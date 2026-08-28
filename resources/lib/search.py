import json
import os
import sys

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

try:
    from xbmcvfs import translatePath
except ImportError:
    # Fallback for older Kodi versions (pre-Matrix)
    translatePath = xbmc.translatePath

from resources.lib.api import DAFilmsAPI, FilmDetails
from resources.lib.session import get_session
from resources.lib.utils import fetch_film_details_parallel, get_film_details_cache, get_url

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])


def get_search_history_file():
    """Get the appropriate search history file path based on the current addon"""
    # Get the addon's profile directory
    addon = xbmcaddon.Addon()
    profile_dir = translatePath(addon.getAddonInfo("profile"))
    return os.path.join(profile_dir, "search_history.json")


def load_search_history():
    """Load search history from file"""
    try:
        history_file = get_search_history_file()
        # Ensure directory exists
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        if os.path.exists(history_file):
            with open(history_file, encoding="utf-8") as f:
                return json.load(f)
    except (OSError, json.JSONDecodeError):
        pass
    return []


def save_search_history(history):
    """Save search history to file"""
    try:
        history_file = get_search_history_file()
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def add_to_search_history(query):
    """Add a query to search history, keeping only the last 20 unique queries"""
    history = load_search_history()
    # Remove the query if it already exists to move it to the front
    if query in history:
        history.remove(query)
    # Add to the beginning
    history.insert(0, query)
    # Keep only last 20
    history = history[:20]
    save_search_history(history)


def show_search_history(label):
    """Display search history page with 'Nové hledání' at the top"""
    xbmcplugin.setPluginCategory(_handle, label)

    # Add "Nové hledání" as the first item
    list_item = xbmcgui.ListItem(label="Nové hledání")
    url = get_url(action="search", label="Hledání")
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    # Load and display search history
    history = load_search_history()
    for query in history:
        list_item = xbmcgui.ListItem(label=query)
        # Pass the query directly to search action
        url = get_url(action="search", query=query, label=f"Hledání: {query}")
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    xbmcplugin.endOfDirectory(_handle, cacheToDisc=True)


def perform_search(query, label):
    """Perform film search"""
    session = get_session()

    # If no query provided, show search dialog
    if not query:
        keyboard = xbmc.Keyboard("", "Hledat filmy na DAFilms.cz")
        keyboard.doModal()
        if keyboard.isConfirmed():
            query = keyboard.getText()
        else:
            # User cancelled
            xbmcplugin.setPluginCategory(_handle, "Hledání zrušeno")
            list_item = xbmcgui.ListItem(label="Hledání zrušeno")
            xbmcplugin.addDirectoryItem(_handle, "", list_item, False)
            xbmcplugin.endOfDirectory(_handle, cacheToDisc=True)
            return

    # If we have a query (either from direct call or from keyboard), perform search
    if query:
        # Save to search history
        add_to_search_history(query)
        xbmcplugin.setPluginCategory(_handle, f"Výsledky hledání: {query}")

        try:
            api = session.get_api()
            results = api.search_films(query)

            if results:
                cache = get_film_details_cache()
                # Only fetch details for films missing plot/director
                film_ids_needing_fetch = []
                for film in results[:20]:  # Limit to 20 results
                    if film.id in cache:
                        continue
                    if not film.plot or not film.thumb:
                        film_ids_needing_fetch.append(film.id)

                if film_ids_needing_fetch:
                    new_details = fetch_film_details_parallel(api, film_ids_needing_fetch)
                    cache.update(new_details)

                for film in results[:20]:
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
            else:
                # No results found
                list_item = xbmcgui.ListItem(label="Nenalezeny žádné filmy")
                xbmcplugin.addDirectoryItem(_handle, "", list_item, False)

            xbmcplugin.endOfDirectory(_handle, cacheToDisc=True)

        except Exception as e:
            # Show error to user
            xbmcplugin.setPluginCategory(_handle, "Chyba při hledání")
            list_item = xbmcgui.ListItem(label=f"Chyba: {str(e)}")
            xbmcplugin.addDirectoryItem(_handle, "", list_item, False)
            xbmcplugin.endOfDirectory(_handle, cacheToDisc=True)
