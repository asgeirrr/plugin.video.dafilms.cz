import sys

import xbmcgui
import xbmcplugin

from resources.lib.api import DAFilmsAPI, FilmDetails
from resources.lib.session import get_session
from resources.lib.utils import add_directory_item, get_url

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])


def list_newest_films(label):
    """List newest films"""
    xbmcplugin.setPluginCategory(_handle, label)

    # Get session and API instance
    session = get_session()
    api = session.get_api()

    # Check if we need to login
    if not session.is_logged_in():
        # Show notification and open settings
        session.prompt_for_login()
        # Show empty listing since we can't get data without login
        xbmcplugin.endOfDirectory(_handle, cacheToDisc=True)
        return

    films = api.get_newest_films(limit=20)

    if films:
        for film in films:
            list_item = xbmcgui.ListItem(label=film.title)
            list_item.setArt({"thumb": film.thumb})

            # Set rich metadata (film object only has basic fields)
            video_info = {
                "title": film.title,
                "plot": "DAFilms.cz dokumentární film",
                "genre": "Documentary",
                "mediatype": "movie",
            }
            list_item.setInfo("video", video_info)

            url = get_url(action="play_film", film_id=film.id, title=film.title)
            xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    xbmcplugin.endOfDirectory(_handle, cacheToDisc=True)


def list_all_films(label):
    """List all films from comprehensive listing"""
    xbmcplugin.setPluginCategory(_handle, label)

    # Get session and API instance
    session = get_session()
    api = session.get_api()

    # Check if we need to login
    if not session.is_logged_in():
        # Show notification and open settings
        session.prompt_for_login()
        # Show empty listing since we can't get data without login
        xbmcplugin.endOfDirectory(_handle, cacheToDisc=True)
        return

    films = api.get_all_films(limit=50)

    if films:
        for film in films:
            list_item = xbmcgui.ListItem(label=film.title)
            list_item.setArt({"thumb": film.thumb})
            # Set rich metadata (film object only has basic fields)
            video_info = {
                "title": film.title,
                "plot": "DAFilms.cz dokumentární film",
                "genre": "Documentary",
                "mediatype": "movie",
            }
            list_item.setInfo("video", video_info)

            url = get_url(action="play_film", film_id=film.id, title=film.title)
            xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    xbmcplugin.endOfDirectory(_handle, cacheToDisc=True)


def list_subscription_films(label):
    """List films available for subscribers"""
    xbmcplugin.setPluginCategory(_handle, label)

    # Get session and API instance
    session = get_session()
    api = session.get_api()

    # Check if we need to login
    if not session.is_logged_in():
        # Show notification and open settings
        session.prompt_for_login()
        # Show empty listing since we can't get data without login
        xbmcplugin.endOfDirectory(_handle, cacheToDisc=True)
        return

    films = api.get_subscription_films(limit=50)

    if films:
        for film in films:
            list_item = xbmcgui.ListItem(label=film.title)
            list_item.setArt({"thumb": film.thumb})
            # Set rich metadata (film object only has basic fields)
            video_info = {
                "title": film.title,
                "plot": "DAFilms.cz dokumentární film pro předplatitele",
                "genre": "Documentary",
                "mediatype": "movie",
            }
            list_item.setInfo("video", video_info)

            url = get_url(action="play_film", film_id=film.id, title=film.title)
            xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    xbmcplugin.endOfDirectory(_handle, cacheToDisc=True)


def list_purchased_films(label):
    """List films that the user has purchased"""
    xbmcplugin.setPluginCategory(_handle, label)

    # Get session and API instance
    session = get_session()
    api = session.get_api()

    # Check if we need to login
    if not session.is_logged_in():
        # Show notification and open settings
        session.prompt_for_login()
        # Show empty listing since we can't get data without login
        xbmcplugin.endOfDirectory(_handle, cacheToDisc=True)
        return

    try:
        films = api.get_purchased_films()

        if films:
            for film in films:
                list_item = xbmcgui.ListItem(label=film.title)
                # Try to fetch film details to get thumbnail
                try:
                    film_details = api.get_film_details(film.id)
                    if film_details.get("thumb"):
                        list_item.setArt({"thumb": film_details["thumb"]})
                except Exception:
                    # If we can't get details, proceed without thumbnail
                    pass

                # Set rich metadata
                video_info = {
                    "title": film.title,
                    "plot": "DAFilms.cz zakoupený film",
                    "genre": "Documentary",
                    "mediatype": "movie",
                }
                list_item.setInfo("video", video_info)

                url = get_url(action="play_film", film_id=film.id, title=film.title)
                xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
        else:
            # No purchased films found
            list_item = xbmcgui.ListItem(label="Žádné zakoupené filmy")
            xbmcplugin.addDirectoryItem(_handle, "", list_item, False)

    except Exception as e:
        # Show error to user
        list_item = xbmcgui.ListItem(label=f"Chyba při načítání zakoupených filmů: {str(e)}")
        xbmcplugin.addDirectoryItem(_handle, "", list_item, False)

    xbmcplugin.endOfDirectory(_handle, cacheToDisc=True)
