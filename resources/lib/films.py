from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import xbmcgui
import xbmcplugin

from resources.lib.api import Category, DAFilmsAPI, FilmDetails
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


def list_categories(label):
    """List program categories from the first page"""
    xbmcplugin.setPluginCategory(_handle, label)

    # Get session and API instance
    session = get_session()
    api = session.get_api()

    # Get categories from the first page only (featured/current categories)
    categories = api.get_categories()

    for category in categories:
        list_item = xbmcgui.ListItem(label=category.title)
        if category.thumb:
            list_item.setArt({"thumb": category.thumb})
        if category.plot:
            list_item.setInfo("video", {"plot": category.plot})
        url = get_url(action="list_category_films", category_id=category.id, label=category.title)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    xbmcplugin.endOfDirectory(_handle, cacheToDisc=True)


def list_category_films(label, category_id: str):
    """List films from a specific category"""
    xbmcplugin.setPluginCategory(_handle, label)

    # Get session and API instance
    session = get_session()
    api = session.get_api()

    films = api.get_category_films(category_id)
    _populate_directory(api, films)


def _populate_directory(api: DAFilmsAPI, films: list[FilmDetails]) -> None:
    cache = get_film_details_cache()
    # Only fetch details for films missing plot/director (extracted from listing page)
    film_ids_needing_fetch = []
    for film in films:
        if film.id in cache:
            continue
        if not film.plot or not film.thumb:
            film_ids_needing_fetch.append(film.id)

    if film_ids_needing_fetch:
        new_details = fetch_film_details_parallel(api, film_ids_needing_fetch)
        cache.update(new_details)

    for film in films:
        list_item = xbmcgui.ListItem(label=film.title)

        # Use cached details if available
        film_details = cache.get(film.id, {})

        # Build info from FilmDetails (has plot, director from listing) + cache
        info = {
            "title": film.title,
            "plot": film.plot or film_details.get("plot", ""),
            "director": film.director or film_details.get("director"),
            "genre": "Documentary",
            "mediatype": "movie",
        }
        info = {k: v for k, v in info.items() if v is not None}

        # Use thumb from FilmDetails first, then cached, then None
        thumb = film.thumb or film_details.get("thumb")
        list_item.setArt({"thumb": thumb})

        list_item.setInfo("video", info)
        list_item.setProperty("IsPlayable", "true")

        url = get_url(action="play_film", film_id=film.id, title=film.title)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    xbmcplugin.endOfDirectory(_handle, cacheToDisc=True)
