#!/usr/bin/env python3
"""
Development tools for DAFilms.cz Kodi addon
Run with: python3 datools.py [command]
"""

import sys
import json
import os
import subprocess
import shutil
import zipfile
import requests
import re
import traceback
from pathlib import Path
from bs4 import BeautifulSoup

# Add resources to path
sys.path.append(str(Path(__file__).parent / "resources" / "lib"))

from api import DAFilmsAPI


def test_login():
    """Test login functionality"""
    print("Testing login...")
    api = DAFilmsAPI()

    # You would replace these with real credentials for testing
    email = os.environ["DAFILMS_EMAIL"]  # Replace with real email
    password = os.environ["DAFILMS_PASSWORD"]  # Replace with real password

    success = api.login(email, password)
    if success:
        print("✅ Login successful!")
    else:
        print("❌ Login failed")


def build_addon(version="1.0.0"):
    """Build the Kodi addon ZIP file"""
    print(f"Building DAFilms.cz Kodi addon version {version}...")

    # Create temporary directory structure
    build_dir = Path("/tmp/dafilms-build")
    addon_build_dir = build_dir / "plugin.video.dafilms.cz"

    # Clean up any existing build
    if build_dir.exists():
        shutil.rmtree(build_dir)

    # Create directories
    addon_build_dir.mkdir(parents=True)
    resources_dir = addon_build_dir / "resources"
    lib_dir = resources_dir / "lib"
    lib_dir.mkdir(parents=True)

    # Copy files
    print("Copying files...")

    # Main files
    shutil.copy("addon.xml", addon_build_dir)
    shutil.copy("icon.png", addon_build_dir)
    shutil.copy("main.py", addon_build_dir)

    # Resources
    shutil.copy("resources/settings.xml", resources_dir)

    # Copy Python library files
    for file in Path("resources/lib").glob("*.py"):
        if file.name != "__pycache__":
            shutil.copy(file, lib_dir)

    # Create ZIP with proper structure
    print("Creating ZIP file...")
    zip_path = Path(f"../plugin.video.dafilms.cz-{version}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in addon_build_dir.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(build_dir)
                zipf.write(file, arcname)

    # Clean up
    shutil.rmtree(build_dir)

    print(f"✅ Addon built: {zip_path.absolute()}")


def clean_build():
    """Clean build artifacts"""
    print("Cleaning build artifacts...")

    # Remove ZIP files
    for zip_file in Path("..").glob("plugin.video.dafilms.cz-*.zip"):
        zip_file.unlink()
        print(f"Removed: {zip_file}")

    # Remove __pycache__ directories
    for cache_dir in Path(".").rglob("__pycache__"):
        shutil.rmtree(cache_dir)
        print(f"Removed: {cache_dir}")

    print("✅ Cleaned up")


def install_symlink():
    """Install addon via symlink for development"""
    addon_dir = Path.home() / ".kodi" / "addons" / "plugin.video.dafilms.cz"
    dev_dir = Path(__file__).parent

    print(f"Setting up symlink from {dev_dir} to {addon_dir}")

    # Remove existing installation
    if addon_dir.exists():
        if addon_dir.is_symlink():
            addon_dir.unlink()
        else:
            print("⚠️  Existing installation found, not removing (back it up first)")
            return

    # Create symlink
    addon_dir.symlink_to(dev_dir)
    print("✅ Symlink created. Restart Kodi to load the addon.")


def main():
    if len(sys.argv) < 2:
        print("DAFilms.cz Development Tools")
        print("Usage: python3 datools.py [command]")
        print("Commands:")
        print("  test-login    - Test login (edit script first)")
        print("  rebuild       - Rebuild the addon")
        print("  install       - Install via symlink")
        print("  deps          - Check dependencies")
        print("  stream        - Test stream extraction")
        print("  search        - Test search functionality")
        print("  purchased     - Test purchased films listing")
        print("  logs          - Show Kodi logs")
        print("  build         - Build the Kodi addon ZIP file")
        print("  clean         - Clean build artifacts")

        return

    command = sys.argv[1]

    if command == "test-login":
        test_login()
    elif command == "install":
        install_symlink()
    elif command == "deps":
        check_dependencies()
    elif command == "stream":
        film_id = (
            sys.argv[2] if len(sys.argv) > 2 else "18800"
        )  # Default to working film, or use provided ID
        test_stream_extraction(film_id)
    elif command == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else "Karel"
        test_search(query)
    elif command == "purchased":
        test_purchased_films()
    elif command == "details":
        film_id = sys.argv[2] if len(sys.argv) > 2 else "18800"
        test_film_details(film_id)
    elif command == "logs":
        show_logs()
    elif command == "build":
        version = sys.argv[2] if len(sys.argv) > 2 else "1.0.0"
        build_addon(version)
    elif command == "clean":
        clean_build()
    else:
        print(f"Unknown command: {command}")


def test_search(query="dokument"):
    """Test search functionality"""
    print(f"Testing search for query: '{query}'")
    print("=" * 60)

    try:
        api = DAFilmsAPI()

        # Perform search
        print("1. Performing search...")
        results = api.search_films(query)

        if results:
            print(f"   ✅ Found {len(results)} results:")
            for i, result in enumerate(results[:5], 1):  # Show first 5 results
                # Handle both FilmDetails objects and dicts
                if hasattr(result, "title"):  # FilmDetails object
                    title = result.title
                    film_id = result.id
                    url = result.url
                    thumb = result.thumb
                else:  # dict
                    title = result.get("title", "No title")
                    film_id = result.get("id", "N/A")
                    url = result.get("url")
                    thumb = result.get("thumb")

                print(f"      {i}. {title} (ID: {film_id})")
                if url:
                    print(f"         URL: {url}")
                if thumb:
                    print(f"         Thumbnail: {thumb}")

            if len(results) > 5:
                print(f"      ... and {len(results) - 5} more results")
        else:
            print("   ❌ No results found")

        # Debug information
        print("\n2. Debug information:")
        print("   - Search endpoint used: /film")
        print("   - Query parameters: q={query}")
        print("   - Response format: HTML with film cards")
        print("   - Film cards parsed: data-film-item='true' elements")
        print("   - Results limited to: 20 items (for Kodi performance)")
        print("   - Data structure: FilmDetails dataclass (id, title, url, thumb)")
        print("   - Consistent usage: All film listing functions now use FilmDetails")

    except Exception as e:
        print(f"   ❌ Error during search: {e}")
        import traceback

        traceback.print_exc()


def test_film_details(film_id="18800"):
    """Test film details extraction for a specific film"""
    film_url = f"https://dafilms.cz/film/{film_id}"

    print(f"Testing film details extraction for: {film_url}")
    print("=" * 60)

    try:
        api = DAFilmsAPI()

        # Check if we need to login
        print("1. Checking authentication...")
        if not api._logged_in:
            print("   ⚠️  Not logged in. Attempting login with environment variables...")

            # Try to login
            import os

            email = os.environ.get("DAFILMS_EMAIL")
            password = os.environ.get("DAFILMS_PASSWORD")

            if email and password:
                if api.login(email, password):
                    print("   ✅ Login successful")
                else:
                    print("   ❌ Login failed")
                    return
            else:
                print("   ❌ No credentials provided")
                return
        else:
            print("   ✅ Already logged in")

        # Test film details extraction
        print("2. Getting film details...")
        details = api.get_film_details(film_id)

        if details:
            print("   ✅ Film details extracted successfully:")
            for key, value in details.items():
                print(f"      {key}: {value}")
        else:
            print("   ❌ Failed to extract film details")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback

        traceback.print_exc()


def test_purchased_films():
    """Test purchased films listing functionality"""
    print("Testing purchased films listing")
    print("=" * 60)

    try:
        api = DAFilmsAPI()

        # Check if we need to login
        print("1. Checking authentication...")
        if not api._logged_in:
            print("   ⚠️  Not logged in. Attempting login with environment variables...")

            # Try to login
            import os

            email = os.environ.get("DAFILMS_EMAIL")
            password = os.environ.get("DAFILMS_PASSWORD")

            if email and password:
                if api.login(email, password):
                    print("   ✅ Login successful")
                else:
                    print("   ❌ Login failed")
                    return
            else:
                print("   ❌ No credentials provided")
                print("   Set environment variables:")
                print("   export DAFILMS_EMAIL='your@email.com'")
                print("   export DAFILMS_PASSWORD='yourpassword'")
                return
        else:
            print("   ✅ Already logged in")

        # Test purchased films extraction
        print("2. Fetching purchased films from payments page...")
        purchased_films = api.get_purchased_films()

        if purchased_films:
            print(f"   ✅ Found {len(purchased_films)} purchased films:")
            for i, film in enumerate(purchased_films, 1):
                print(f"      {i}. {film.title} (ID: {film.id})")
                print(f"         URL: {film.url}")

                # Try to get film details for each film
                try:
                    details = api.get_film_details(film.id)
                    if details:
                        print(f"         Details: {details.get('plot', 'No description')[:100]}...")
                        if details.get("thumb"):
                            print(f"         Thumbnail: {details['thumb']}")
                except Exception as e:
                    print(f"         ❌ Could not get details: {e}")
        else:
            print("   ⚠️  No purchased films found")
            print("   This could mean:")
            print("   - You haven't purchased any films")
            print("   - The payments page structure has changed")
            print("   - You're not logged in properly")

        # Debug information
        print("\n3. Debug information:")
        print("   - Payments page URL: /user/detail/payments")
        print("   - Looking for table with class: table-responsive")
        print("   - Parsing rows for: Stažení filmu entries")
        print("   - Extracting film links from: <a href='...'>Film Title</a>")
        print("   - Film ID extraction: URL.split('/film/')[1].split('/')[0]")
        print("   - Duplicate prevention: Check film IDs")

    except Exception as e:
        print(f"   ❌ Error during purchased films test: {e}")
        import traceback

        traceback.print_exc()


def test_stream_extraction(film_id):
    """Test stream URL extraction for a specific film"""
    film_url = f"https://dafilms.cz/film/{film_id}"

    print(f"Testing stream extraction for: {film_url}")
    print("=" * 60)

    try:
        api = DAFilmsAPI()

        # Check if we need to login
        print("1. Checking authentication...")
        if not api._logged_in:
            print("   ⚠️  Not logged in. Attempting login with environment variables...")

            # Use environment variables for credentials (same as test_login)
            email = os.environ.get("DAFILMS_EMAIL")
            password = os.environ.get("DAFILMS_PASSWORD")

            if email and password:
                if api.login(email, password):
                    print("   ✅ Login successful")
                else:
                    print("   ❌ Login failed")
                    return
            else:
                print("   ❌ Environment variables DAFILMS_EMAIL and DAFILMS_PASSWORD not set")
                print("   Set them and try again:")
                print("   export DAFILMS_EMAIL='your@email.com'")
                print("   export DAFILMS_PASSWORD='yourpassword'")
                return
        else:
            print("   ✅ Already logged in")

        # First, get the film page
        print("2. Fetching film page...")
        response = api.session.get(f"{api.BASE_URL}/film/{film_id}")
        response.raise_for_status()

        # Save page for debugging
        with open("/tmp/dafilms_film_page.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("   ✅ Page saved to /tmp/dafilms_film_page.html")

        # Parse the page
        soup = BeautifulSoup(response.text, "html.parser")

        # Look for script tags that might contain stream info
        print("3. Looking for stream configuration in scripts...")
        script_tags = soup.find_all("script")
        stream_scripts = []

        for i, script in enumerate(script_tags, 1):
            if script.string and (
                "video" in script.string.lower() or "stream" in script.string.lower()
            ):
                stream_scripts.append((i, script.string[:200]))

        if stream_scripts:
            print(f"   ✅ Found {len(stream_scripts)} relevant scripts:")
            for idx, content in stream_scripts[:3]:  # Show first 3
                print(f"      Script {idx}: {content}...")
        else:
            print("   ❌ No relevant scripts found")

        # Look for JSON data
        print("5. Looking for JSON configuration...")
        json_scripts = soup.find_all("script", type="application/json")
        if json_scripts:
            print(f"   ✅ Found {len(json_scripts)} JSON scripts")
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    if "video" in str(data).lower() or "stream" in str(data).lower():
                        print(f"      Relevant JSON: {json.dumps(data, indent=2)[:300]}...")
                except:
                    pass

        # Try the API's stream extraction
        print("6. Testing API stream extraction...")
        stream_url = api.get_stream_url(film_id)
        if stream_url:
            print(f"   ✅ Stream URL found: {stream_url}")
        else:
            print("   ❌ API could not extract stream URL")

        print("\n" + "=" * 60)
        print("Debugging suggestions:")
        print("1. Check /tmp/dafilms_film_page.html")
        print("2. Look for network requests in browser dev tools")
        print("3. Check if authentication is required")
        print("4. Look for JavaScript that sets up the player")

    except Exception as e:
        print(f"❌ Error during stream extraction: {e}")
        import traceback

        traceback.print_exc()


def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")

    # This would need to run within Kodi to work properly
    # For now, provide manual installation instructions

    dependencies = [
        "script.module.requests (2.31.0+)",
        "script.module.beautifulsoup4 (4.9.3+)",
        "inputstream.adaptive (2.0.0+)",
    ]

    print("Required dependencies:")
    for dep in dependencies:
        print(f"  - {dep}")

    print("\nInstallation methods:")
    print("1. Through Kodi GUI:")
    print("   Settings → Add-ons → Install from repository → Kodi Add-on repository")
    print("\n2. Manual installation:")
    print("   Download ZIP files and install via 'Install from zip file'")
    print("\n3. JSON-RPC commands (run in Kodi Python console):")
    for dep in dependencies:
        addon_id = dep.split()[0]
        print(f"   xbmc.executebuiltin('InstallAddon({addon_id})')")


def show_logs():
    """Show Kodi logs"""
    log_file = Path.home() / ".kodi" / "temp" / "kodi.log"
    if not log_file.exists():
        print(f"❌ Log file not found at {log_file}")
        return

    print(f"Showing last 50 lines of {log_file}:")
    result = subprocess.run(["tail", "-50", str(log_file)], capture_output=True, text=True)
    print(result.stdout)

    # Filter for our addon
    print("\nFiltering for DAFilms:")
    result = subprocess.run(
        ["grep", "DAFilms\\|dafilms", str(log_file)], capture_output=True, text=True
    )
    if result.stdout:
        print(result.stdout)
    else:
        print("No matching entries found")


if __name__ == "__main__":
    main()
