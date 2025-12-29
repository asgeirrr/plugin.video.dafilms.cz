"""
Session management for DAFilms.cz Kodi addon
Handles authentication, credentials storage, and session persistence
"""

import requests
import xbmcaddon
import xbmcgui

from resources.lib.api import DAFilmsAPI


class DAFilmsSession:
    """Singleton session manager for DAFilms.cz API"""

    _instance = None
    _api = None
    _addon = None

    def __new__(cls):
        """Singleton pattern - ensure only one instance exists"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the session manager"""
        try:
            self._addon = xbmcaddon.Addon("plugin.video.dafilms.cz")
        except Exception:
            # This can happen during development/testing
            self._addon = None

        self._api = DAFilmsAPI()
        self._logged_in = False

    def get_api(self) -> DAFilmsAPI:
        """Get the API instance, ensuring we're logged in"""
        self._ensure_logged_in()
        return self._api

    def _ensure_logged_in(self) -> bool:
        """Ensure we're logged in, attempt login if needed"""
        if self._api._logged_in:
            return True

        # Only use stored credentials, never prompt
        if not self._addon:
            return False

        username = self._addon.getSetting("username")
        password = self._addon.getSetting("password")

        if username and password:
            if self._api.login(username, password):
                self._api._logged_in = True
                self._logged_in = True
                return True
            else:
                # Clear credentials if login failed
                self._addon.setSetting("username", "")
                self._addon.setSetting("password", "")
                return False
        else:
            return False

    def prompt_for_login(self) -> bool:
        """Prompt user to configure credentials in settings"""
        if not self._addon:
            return False

        # Show notification to configure settings
        dialog = xbmcgui.Dialog()
        dialog.notification(
            "Přihlášení vyžadováno",
            "Nastavte přihlašovací údaje v nastavení addonu",
            xbmcgui.NOTIFICATION_INFO,
        )

        # Optionally open settings dialog
        try:
            self._addon.openSettings()
            return True
        except Exception:
            return False

    def logout(self):
        """Logout from DAFilms.cz"""
        self._api._logged_in = False
        self._logged_in = False
        # Clear session cookies by creating a new session
        self._api.session = requests.Session()

        # Clear stored credentials if addon is available
        if self._addon:
            try:
                self._addon.setSetting("username", "")
                self._addon.setSetting("password", "")
            except Exception:
                pass

    def is_logged_in(self) -> bool:
        """Check if user is logged in"""
        return self._logged_in and self._api._logged_in


def get_session() -> DAFilmsSession:
    """Get the global session instance"""
    return DAFilmsSession()
