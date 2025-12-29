import sys

import xbmc
import xbmcgui
import xbmcplugin

try:
    from urlparse import parse_qsl, urlencode  # type: ignore
except ImportError:
    from urllib.parse import parse_qsl, urlencode  # type: ignore


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
