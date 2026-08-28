import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import xbmc
import xbmcgui
import xbmcplugin

try:
    from urlparse import parse_qsl, urlencode  # type: ignore
except ImportError:
    from urllib.parse import parse_qsl, urlencode  # type: ignore

# Simple in-memory cache for film details
_film_details_cache = {}


def get_url(**kwargs):
    """Create plugin URL with parameters"""
    return f"{sys.argv[0]}?{urlencode(kwargs)}"


def add_directory_item(handle, label, url, is_folder=True, **kwargs):
    """Helper to add directory items"""
    list_item = xbmcgui.ListItem(label=label)

    # Set additional properties if provided
    if "thumb" in kwargs:
        list_item.setArt({"thumb": kwargs["thumb"]})
    if "fanart" in kwargs:
        list_item.setArt({"fanart": kwargs["fanart"]})
    if "info" in kwargs:
        list_item.setInfo("video", kwargs["info"])

    xbmcplugin.addDirectoryItem(handle, url, list_item, is_folder)


def show_notification(message, title="DAFilms.cz", icon=xbmcgui.NOTIFICATION_INFO):
    """Show Kodi notification"""
    xbmc.executebuiltin(f'Notification("{title}", "{message}", 5000, "{icon}")')


def get_addon_setting(setting_id):
    """Get addon setting value"""
    import xbmcaddon

    addon = xbmcaddon.Addon()
    return addon.getSetting(setting_id)


def get_film_details_cache():
    """Get the shared film details cache"""
    return _film_details_cache


def fetch_film_details_parallel(api, film_ids: list[str]) -> dict[str, dict]:
    """Fetch film details in parallel using thread pool

    Args:
        api: DAFilmsAPI instance to fetch details from
        film_ids: List of film IDs to fetch details for

    Returns:
        Dictionary mapping film IDs to their details
    """
    details = {}

    def fetch_details(film_id):
        try:
            return film_id, api.get_film_details(film_id)
        except Exception:
            return film_id, None

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_id = {executor.submit(fetch_details, film_id): film_id for film_id in film_ids}

        for future in as_completed(future_to_id, timeout=10):
            film_id, result = future.result()
            if result:
                details[film_id] = result

    return details
