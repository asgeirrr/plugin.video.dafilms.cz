import sys

import xbmc
import xbmcgui
import xbmcplugin

from resources.lib.api import DAFilmsAPIError
from resources.lib.session import get_session
from resources.lib.utils import show_notification

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])


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
        xbmc.log("DAFilms: Configuring HLS stream", xbmc.LOGINFO)
        play_item.setProperty("inputstream", "inputstream.adaptive")
        play_item.setProperty("inputstream.adaptive.manifest_type", "hls")
        play_item.setProperty("inputstream.adaptive.manifest_update_parameter", "full")
        play_item.setProperty(
            "inputstream.adaptive.stream_headers", "User-Agent=Kodi/DAFilms Addon"
        )
    elif ".mp4" in stream_url:
        # MP4 stream - this is what we typically get from DAFilms
        xbmc.log("DAFilms: Configuring MP4 stream", xbmc.LOGINFO)
        play_item.setProperty("inputstream", "")
        play_item.setMimeType("video/mp4")
        # For CloudFront URLs, we might need additional headers
        if "cloudfront.net" in stream_url:
            xbmc.log("DAFilms: CloudFront URL detected, setting headers", xbmc.LOGINFO)
            play_item.setProperty(
                "inputstream.adaptive.stream_headers", "User-Agent=Kodi/DAFilms Addon"
            )
    else:
        # Unknown stream type - try adaptive
        xbmc.log("DAFilms: Unknown stream type, trying adaptive", xbmc.LOGINFO)
        play_item.setProperty("inputstream", "inputstream.adaptive")
        play_item.setProperty("inputstream.adaptive.manifest_type", "hls")

    # Set content lookup to false to avoid Kodi scraping
    play_item.setContentLookup(False)

    # Debug: Log the final play item properties
    xbmc.log(f"DAFilms: Play item path: {play_item.getPath()}", xbmc.LOGINFO)
    xbmc.log(f"DAFilms: Play item properties: {play_item.getProperty('inputstream')}", xbmc.LOGINFO)

    # Start playback using the original working method
    try:
        xbmc.log("DAFilms: Starting playback", xbmc.LOGINFO)

        # Create player instance first
        player = xbmc.Player()
        # Fallback to direct player if setResolvedUrl didn't work
        xbmc.log("DAFilms: Trying direct player method", xbmc.LOGINFO)
        player.play(stream_url, play_item)

        # Give it time to start
        xbmc.sleep(1000)

        # Check if playback started
        if player.isPlaying():
            xbmc.log("DAFilms: Playback started successfully with direct player", xbmc.LOGINFO)
        else:
            xbmc.log("DAFilms: Playback failed to start", xbmc.LOGERROR)
            show_notification("Chyba při spouštění přehrávání", icon=xbmcgui.NOTIFICATION_ERROR)
    except Exception as e:
        xbmc.log(f"DAFilms: Playback error: {str(e)}", xbmc.LOGERROR)
        show_notification(f"Chyba při přehrávání: {str(e)}", icon=xbmcgui.NOTIFICATION_ERROR)
