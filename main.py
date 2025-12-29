import sys

import xbmcaddon
import xbmcgui
import xbmcplugin

try:
    from urlparse import parse_qsl  # type: ignore
except ImportError:
    from urllib.parse import parse_qsl  # type: ignore

from resources.lib.api import DAFilmsAPI
from resources.lib.utils import get_url
from resources.lib.films import list_newest_films, list_subscription_films, list_purchased_films
from resources.lib.search import perform_search
from resources.lib.playback import play_film

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])


def list_menu():
    """Main menu listing"""
    # Purchased films
    list_item = xbmcgui.ListItem(label="Zakoupené filmy")
    url = get_url(action="list_purchased_films", label="Zakoupené filmy")
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    # Subscription films
    list_item = xbmcgui.ListItem(label="Filmy pro předplatitele")
    url = get_url(action="list_subscription_films", label="Filmy pro předplatitele")
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    # Featured content
    list_item = xbmcgui.ListItem(label="Nejnovější filmy")
    url = get_url(action="list_newest", label="Nejnovější filmy")
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    # Search
    list_item = xbmcgui.ListItem(label="Hledat")
    url = get_url(action="search", label="Hledat")
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    xbmcplugin.endOfDirectory(_handle, cacheToDisc=True)


def router(paramstring):
    """Route plugin calls to appropriate functions"""
    params = dict(parse_qsl(paramstring))

    if not params:
        list_menu()
    elif params["action"] == "list_newest":
        list_newest_films(params["label"])
    elif params["action"] == "list_subscription_films":
        list_subscription_films(params["label"])
    elif params["action"] == "list_purchased_films":
        list_purchased_films(params["label"])
    elif params["action"] == "search":
        perform_search(params.get("query", ""), params["label"])
    elif params["action"] == "play_film":
        play_film(params["film_id"], params["title"])
    else:
        raise ValueError(f"Unknown parameter: {paramstring}!")


if __name__ == "__main__":
    router(sys.argv[2][1:])
