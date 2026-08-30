"""Pytest configuration and mocks for testing"""

import sys
from unittest.mock import MagicMock

# Mock xbmc modules before any imports
sys.modules["xbmc"] = MagicMock()
sys.modules["xbmcaddon"] = MagicMock()
sys.modules["xbmcgui"] = MagicMock()
sys.modules["xbmcplugin"] = MagicMock()
sys.modules["xbmcvfs"] = MagicMock()
