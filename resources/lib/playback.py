import sys
import traceback

import xbmc
import xbmcgui
import xbmcplugin

from resources.lib.api import DAFilmsAPIError
from resources.lib.session import get_session
from resources.lib.utils import show_notification

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])


def _start_watch_time_monitor(api, film_id):
    """Start a background thread to monitor and update watch time"""
    import threading
    import time

    def watch_time_monitor():
        """Monitor playback position and update watch time periodically"""
        try:
            xbmc.log(f"DAFilms: Watch time monitor started for film {film_id}", xbmc.LOGDEBUG)

            # Get Kodi player instance
            player = xbmc.Player()
            time.sleep(5)

            # Monitor playback for up to 4 hours (14400 seconds)
            start_time = time.time()
            last_position = 0

            while time.time() - start_time < 14400:  # 4 hours max
                monitor_iteration = int((time.time() - start_time) / 30) + 1

                # Check if player is playing
                if player.isPlaying():
                    # Get current position
                    current_position = player.getTime()  # in seconds
                    xbmc.log(
                        f"DAFilms: Monitor iteration {monitor_iteration}: Player is playing, position = {current_position}s",
                        xbmc.LOGDEBUG,
                    )

                    # Convert to milliseconds for the API
                    position_ms = int(current_position * 1000)

                    # Only update if position changed significantly (more than 5 seconds)
                    if abs(position_ms - last_position) > 5000:
                        xbmc.log(
                            f"DAFilms: Position changed significantly: {last_position}ms -> {position_ms}ms",
                            xbmc.LOGDEBUG,
                        )

                        # Update watch time
                        api.update_watch_time(film_id, position_ms)

                        last_position = position_ms

                    else:
                        xbmc.log(
                            f"DAFilms: Position change too small: {position_ms}ms (last was {last_position}ms)",
                            xbmc.LOGDEBUG,
                        )

                # Sleep for 30 seconds between checks
                xbmc.log(
                    f"DAFilms: Sleeping for 30 seconds before next check (iteration {monitor_iteration})",
                    xbmc.LOGDEBUG,
                )
                time.sleep(30)

        except Exception as e:
            xbmc.log(
                f"DAFilms: Watch time monitor error: {str(e)}\n{traceback.format_exc()}",
                xbmc.LOGERROR,
            )

    # Start monitor thread
    xbmc.log("DAFilms: Starting watch time monitor thread", xbmc.LOGDEBUG)
    monitor_thread = threading.Thread(target=watch_time_monitor, daemon=True)
    monitor_thread.start()


def play_film(film_id, title):
    """Play a film from DAFilms.cz - simplified version"""
    # Get the session manager
    session = get_session()
    api = session.get_api()

    # Check if we need to prompt for login
    if not session.is_logged_in():
        session.prompt_for_login()
        show_notification(
            "Přihlášení je vyžadováno pro přehrávání", icon=xbmcgui.NOTIFICATION_ERROR
        )
        return

    # Get stream URL with better error handling
    try:
        xbmc.log(f"DAFilms: Getting stream URL for film {film_id}", xbmc.LOGINFO)
        stream_url = api.get_stream_url(film_id)
        xbmc.log(f"DAFilms: Retrieved stream URL: {stream_url}", xbmc.LOGINFO)

        # Check if stream requires purchase
        if stream_url == "REQUIRES_PURCHASE":
            xbmc.log(f"DAFilms: Film {film_id} requires purchase", xbmc.LOGWARNING)
            show_notification(
                "Film vyžaduje zakoupení nebo předplatné", icon=xbmcgui.NOTIFICATION_WARNING
            )
            return

        # Validate that we got a proper URL
        if (
            not stream_url
            or not isinstance(stream_url, str)
            or not stream_url.startswith(("http://", "https://"))
        ):
            xbmc.log(f"DAFilms: Invalid stream URL received: {stream_url}", xbmc.LOGERROR)
            show_notification("Neplatná URL streamu filmu", icon=xbmcgui.NOTIFICATION_ERROR)
            return

    except DAFilmsAPIError as e:
        xbmc.log(f"DAFilms: API error getting stream URL: {str(e)}", xbmc.LOGERROR)
        show_notification(f"Chyba při získávání streamu: {str(e)}", icon=xbmcgui.NOTIFICATION_ERROR)
        return
    except Exception as e:
        xbmc.log(f"DAFilms: Unexpected error getting stream URL: {str(e)}", xbmc.LOGERROR)
        show_notification(f"Neočekávaná chyba: {str(e)}", icon=xbmcgui.NOTIFICATION_ERROR)
        return

    # Create a playable item
    xbmc.log(f"DAFilms: Creating playable item for: {title}", xbmc.LOGINFO)
    xbmc.log(f"DAFilms: Stream URL: {stream_url}", xbmc.LOGINFO)

    play_item = xbmcgui.ListItem(label=title, path=stream_url)

    # Set basic video info
    video_info = {
        "title": title,
        "genre": "Documentary",
        "mediatype": "movie",
    }
    play_item.setInfo("video", video_info)

    # Set stream type properties with debugging
    if stream_url.endswith(".m3u8"):
        # HLS stream
        xbmc.log("DAFilms: Configuring HLS stream", xbmc.LOGDEBUG)
        play_item.setProperty("inputstream", "inputstream.adaptive")
        play_item.setProperty("inputstream.adaptive.manifest_type", "hls")
        play_item.setProperty("inputstream.adaptive.manifest_update_parameter", "full")
        play_item.setProperty(
            "inputstream.adaptive.stream_headers", "User-Agent=Kodi/DAFilms Addon"
        )
    elif ".mp4" in stream_url:
        # MP4 stream - this is what we typically get from DAFilms
        xbmc.log("DAFilms: Configuring MP4 stream", xbmc.LOGDEBUG)
        play_item.setProperty("inputstream", "")
        play_item.setMimeType("video/mp4")
    else:
        # Unknown stream type - try adaptive
        xbmc.log("DAFilms: Unknown stream type, trying adaptive", xbmc.LOGDEBUG)
        play_item.setProperty("inputstream", "inputstream.adaptive")
        play_item.setProperty("inputstream.adaptive.manifest_type", "hls")

    # Set content lookup to false to avoid Kodi scraping
    play_item.setContentLookup(False)

    # Debug: Log the final play item properties
    xbmc.log(f"DAFilms: Play item path: {play_item.getPath()}", xbmc.LOGDEBUG)
    xbmc.log(
        f"DAFilms: Play item properties: {play_item.getProperty('inputstream')}", xbmc.LOGDEBUG
    )

    # Start playback using the appropriate method for the stream type
    try:
        xbmc.log("DAFilms: Starting playback", xbmc.LOGINFO)
        xbmc.log(f"DAFilms: Is CloudFront URL: {'cloudfront.net' in stream_url}", xbmc.LOGDEBUG)

        # For CloudFront URLs, enhance the play item with better configuration
        if "cloudfront.net" in stream_url:
            # Set MIME type explicitly
            play_item.setMimeType("video/mp4")

            # Enable HTTP debugging to see range requests
            play_item.setProperty("inputstream.http.debug", "true")
            play_item.setProperty("inputstream.http.log_level", "verbose")

            headers = (
                "Host=d144orpukbkwri.cloudfront.net|"
                "User-Agent=Mozilla/5.0 (X11; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0|"
                "Accept=video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5|"
                "Accept-Language=cs,sk;q=0.9,en-US;q=0.8,en;q=0.7|"
                "Range=bytes=0-|"  # Will be overridden by actual range
                "Sec-Fetch-Dest=video|"
                "Sec-Fetch-Mode=no-cors|"
                "Sec-Fetch-Site=cross-site|"
                "Sec-Fetch-Storage-Access=none|"
                "Sec-GPC=1|"
                "Connection=keep-alive|"
                "Referer=https://dafilms.cz/|"
                "Accept-Encoding=identity|"
                "Priority=u=6|"
                "TE=trailers"
            )
            play_item.setProperty("inputstream.http.headers", headers)

        # Start playback with the configured item
        xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=play_item)
        # Start watch time monitor to allow seeking
        if session.is_logged_in() and "cloudfront.net" in stream_url:
            _start_watch_time_monitor(api, film_id)

    except Exception as e:
        xbmc.log(f"DAFilms: Playback error: {str(e)}", xbmc.LOGERROR)
        show_notification(f"Chyba při přehrávání: {str(e)}", icon=xbmcgui.NOTIFICATION_ERROR)
