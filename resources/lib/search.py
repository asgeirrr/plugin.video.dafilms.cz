import sys

import xbmc
import xbmcgui
import xbmcplugin

from resources.lib.api import DAFilmsAPI, FilmDetails
from resources.lib.session import get_session
from resources.lib.utils import fetch_film_details_parallel, get_film_details_cache, get_url

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])


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
        xbmcplugin.setPluginCategory(_handle, f"Výsledky hledání: {query}")

        try:
            api = session.get_api()
            results = api.search_films(query)

            if results:
                cache = get_film_details_cache()
                # Fetch details in parallel for all films (with timeout)
                film_ids = [f.id for f in results[:20] if f.id not in cache]  # Limit to 20 results

                if film_ids:
                    new_details = fetch_film_details_parallel(api, film_ids)
                    cache.update(new_details)

                for film in results[:20]:
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
