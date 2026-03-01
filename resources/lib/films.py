from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import xbmcgui
import xbmcplugin

from resources.lib.api import DAFilmsAPI, FilmDetails
from resources.lib.session import get_session
from resources.lib.utils import add_directory_item, get_url

if TYPE_CHECKING:
    from typing import Literal
if len(sys.argv) > 1:
    _handle = int(sys.argv[1])


def list_newest_films(label):
    """List newest films"""
    xbmcplugin.setPluginCategory(_handle, label)

    # Get session and API instance
    session = get_session()
    api = session.get_api()

    films = api.list_films(order_by="date_added", order="desc")
    _populate_directory(api, films)


def list_subscription_films(label):
    """List films available for subscribers"""
    xbmcplugin.setPluginCategory(_handle, label)

    # Get session and API instance
    session = get_session()
    api = session.get_api()

    films = api.get_subscription_films(limit=50)
    _populate_directory(api, films)


def list_purchased_films(label):
    """List films that the user has purchased"""
    xbmcplugin.setPluginCategory(_handle, label)

    # Get session and API instance
    session = get_session()
    api = session.get_api()

    films = api.get_purchased_films()
    _populate_directory(api, films)


def list_newest_junior_films(label, category: Literal["3-6", "7-11", "12+"]) -> None:
    """Populate directory with the newest junior films in the given category."""
    xbmcplugin.setPluginCategory(_handle, label)

    # Get session and API instance
    session = get_session()
    api = session.get_api()

    films = api.list_films(order_by="date_added", order="desc", junior_category=category)
    _populate_directory(api, films)


def _populate_directory(api: DAFilmsAPI, films: list[FilmDetails]) -> None:
    for film in films:
        list_item = xbmcgui.ListItem(label=film.title)
        list_item.setArt({"thumb": film.thumb})
        # Set rich metadata (film object only has basic fields)

        # Try to fetch film details to get thumbnail
        try:
            film_details = api.get_film_details(film.id)
            if film_details.get("thumb"):
                list_item.setArt({"thumb": film_details["thumb"]})
        except Exception:
            # If we can't get details, proceed without thumbnail
            film_details = {
                "title": film.title,
                "plot": "",
                "genre": "",
                "mediatype": "movie",
            }

        list_item.setInfo("video", film_details)
        list_item.setProperty("IsPlayable", "true")

        url = get_url(action="play_film", film_id=film.id, title=film.title)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    xbmcplugin.endOfDirectory(_handle, cacheToDisc=True)
