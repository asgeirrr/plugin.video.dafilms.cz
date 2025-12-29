# DAFilms.cz Kodi Addon

An unofficial Kodi video add-on for watching documentaries and films from [DAFilms.cz](https://dafilms.cz).

## Features

- ✅ **Comprehensive Film Database**: Access 200+ documentaries and films
- ✅ **Newest Films**: Browse recently added content
- ✅ **Search**: Find specific films with autocomplete
- ✅ **Rich Metadata**: Film details, thumbnails, and descriptions
- ✅ **Modern Playback**: HLS and MP4 stream support with inputstream.adaptive

## Installation

### From ZIP File

1. Download the latest release ZIP file
2. In Kodi: **Settings** → **Add-ons** → **Install from zip file**
3. Select the downloaded ZIP file
4. Wait for "Add-on installed" notification

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/plugin.video.dafilms.cz.git
cd plugin.video.dafilms.cz

# Install development dependencies
pip install ruff

# Run code quality checks
ruff check resources/lib/
ruff format resources/lib/
```

## Code Quality

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

- **Linting**: `ruff check resources/lib/`
- **Formatting**: `ruff format resources/lib/`
- **Auto-fix**: `ruff check --fix resources/lib/`

Configuration is in `pyproject.toml` and `.ruff.toml`.

## Project Structure

```
plugin.video.dafilms.cz/
├── addon.xml              # Addon metadata
├── icon.png               # Addon icon
├── main.py                # Main entry point
├── resources/
│   └── lib/
│       ├── api.py         # DAFilms.cz API client
│       ├── films.py       # Film listing functionality
│       ├── playback.py    # Video playback
│       ├── search.py      # Search functionality
│       └── utils.py       # Utility functions
├── .ruff.toml             # Ruff configuration
├── pyproject.toml         # Python project configuration
└── README.md              # This file
```

## Dependencies

- **Kodi Python**: 3.0.0+
- **script.module.requests**: 2.31.0+
- **script.module.beautifulsoup4**: 4.9.3+
- **inputstream.adaptive**: Any version (for HLS playback)

## Development Notes

### HTML Scraping Approach

Since DAFilms.cz doesn't provide a public API, this addon uses HTML scraping with BeautifulSoup to:
- Extract film listings from `/film?o=r&oa=1`
- Parse film details from JSON-LD metadata
- Find video streams from Video.js player configuration

### Stream URL Detection

The addon attempts multiple methods to find stream URLs:
1. Direct `<source>` tags in Video.js player
2. JavaScript configuration parsing
3. Common URL patterns
4. Debug output for manual inspection

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Run `ruff check --fix` before committing
4. Submit a pull request

## License

This project is licensed under the AGPL 3.0

## Support

For issues or questions, please open a GitHub issue.

---

**Note**: This is an unofficial addon and is not affiliated with DAFilms.cz.
