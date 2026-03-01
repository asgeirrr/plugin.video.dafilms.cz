# DAFilms.cz Kodi Addons

This repository contains two Kodi addons that share a common codebase:

## Structure

- **shared/** - Contains all shared code (API, playback, search, etc.)
- **addon-junior/** - DAFilms.cz Junior addon (for children's content)
- **Root level files** - Main DAFilms.cz addon

## Addons

### Main Addon (DAFilms.cz)
- **ID**: `plugin.video.dafilms.cz`
- **Base URL**: `https://dafilms.cz`
- **Icon**: `icon.png`
- **Files**: Root level `addon.xml`, `main.py`, and `icon.png`

### Junior Addon (DAFilms.cz Junior)
- **ID**: `plugin.video.dafilms.cz.junior`
- **Base URL**: `https://dafilms.cz/junior`
- **Icon**: `icon_junior.png`
- **Files**: `addon-junior/addon.xml`, `addon-junior/main.py`, and `icon_junior.png`

## Testing Locally

To test both addons in your local Kodi installation:

```bash
# Main addon (already set up)
ln -sf /home/oskar/Projekty/plugin.video.dafilms.cz ~/.kodi/addons/plugin.video.dafilms.cz

# Junior addon
ln -sf /home/oskar/Projekty/plugin.video.dafilms.cz/addon-junior ~/.kodi/addons/plugin.video.dafilms.cz.junior
```

## Development

All shared code is in the `shared/` directory. Changes to shared code will affect both addons.

Each addon's `main.py` sets the `BASE_URL` before importing shared code:
- Main addon: `https://dafilms.cz`
- Junior addon: `https://dafilms.cz/junior`

## Running Tests

```bash
pytest tests/
```

Tests cover the shared codebase functionality.
