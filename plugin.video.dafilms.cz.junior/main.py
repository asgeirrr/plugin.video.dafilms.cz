import sys

import xbmcaddon
import xbmcgui
import xbmcplugin

try:
    from urlparse import parse_qsl  # type: ignore
except ImportError:
    from urllib.parse import parse_qsl  # type: ignore

# Set the BASE_URL for Junior before importing shared code
import resources.lib.api as api_module

api_module.DAFilmsAPI.BASE_URL = "https://dafilms.cz/junior"

from resources.lib.utils import get_url
from resources.lib.films import list_newest_junior_films
from resources.lib.search import perform_search, show_search_history
from resources.lib.playback import play_film

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])


def list_menu():
    """Main menu listing for Junior"""
    # Purchased films
    list_item = xbmcgui.ListItem(label="Nejnovější filmy pro 3-6")
    url = get_url(action="list_preschool", label="Nejnovější filmy pro 3-6")
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    # Subscription films
    list_item = xbmcgui.ListItem(label="Nejnovější filmy pro 7-11")
    url = get_url(action="list_elementary_school", label="Nejnovější filmy pro 7-11")
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    # Featured content
    list_item = xbmcgui.ListItem(label="Nejnovější filmy 12+")
    url = get_url(action="list_middle_school", label="Nejnovější filmy 12+")
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    # Search
    list_item = xbmcgui.ListItem(label="Hledat")
    url = get_url(action="search_history", label="Hledání")
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    xbmcplugin.endOfDirectory(_handle, cacheToDisc=True)


def router(paramstring):
    """Route plugin calls to appropriate functions"""
    params = dict(parse_qsl(paramstring))

    if not params:
        list_menu()
    elif params["action"] == "list_preschool":
        list_newest_junior_films(params["label"], category="3-6")
    elif params["action"] == "list_elementary_school":
        list_newest_junior_films(params["label"], category="7-11")
    elif params["action"] == "list_middle_school":
        list_newest_junior_films(params["label"], category="12+")
    elif params["action"] == "search_history":
        show_search_history(params["label"])
    elif params["action"] == "search":
        perform_search(params.get("query", ""), params["label"])
    elif params["action"] == "play_film":
        play_film(params["film_id"], params["title"])
    else:
        raise ValueError(f"Unknown parameter: {paramstring}!")


if __name__ == "__main__":
    router(sys.argv[2][1:])
