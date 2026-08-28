from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import xbmcgui
import xbmcplugin

from resources.lib.api import DAFilmsAPI, FilmDetails
from resources.lib.session import get_session
from resources.lib.utils import (
    add_directory_item,
    fetch_film_details_parallel,
    get_film_details_cache,
    get_url,
)

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

    films = api.list_films(order_by="date_added", order="desc", limit=None)
    _populate_directory(api, films)


def list_subscription_films(label):
    """List films available for subscribers"""
    xbmcplugin.setPluginCategory(_handle, label)

    # Get session and API instance
    session = get_session()
    api = session.get_api()

    films = api.get_subscription_films(limit=None)
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

    films = api.list_films(
        order_by="date_added", order="desc", junior_category=category, limit=None
    )
    _populate_directory(api, films)


def _populate_directory(api: DAFilmsAPI, films: list[FilmDetails]) -> None:
    cache = get_film_details_cache()
    # Fetch details in parallel for all films (with timeout)
    film_ids = [f.id for f in films if f.id not in cache]

    if film_ids:
        new_details = fetch_film_details_parallel(api, film_ids)
        cache.update(new_details)

    for film in films:
        list_item = xbmcgui.ListItem(label=film.title)

        # Use cached details if available
        film_details = cache.get(film.id, {})

        if not film_details:
            film_details = {
                "title": film.title,
                "plot": "",
                "genre": "Documentary",
                "mediatype": "movie",
            }

        # Use thumb from cached details if available, otherwise fall back to film.thumb
        thumb = film_details.get("thumb") or film.thumb
        list_item.setArt({"thumb": thumb})

        list_item.setInfo("video", film_details)
        list_item.setProperty("IsPlayable", "true")

        url = get_url(action="play_film", film_id=film.id, title=film.title)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    xbmcplugin.endOfDirectory(_handle, cacheToDisc=True)
