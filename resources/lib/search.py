import sys

import xbmc
import xbmcgui
import xbmcplugin

from resources.lib.api import DAFilmsAPI
from resources.lib.session import get_session
from resources.lib.utils import get_url

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])


def perform_search(query, label):
    """Perform film search"""
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
            api = DAFilmsAPI()
            results = api.search_films(query)

            if results:
                for film in results[:20]:  # Limit to 20 results for performance
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
