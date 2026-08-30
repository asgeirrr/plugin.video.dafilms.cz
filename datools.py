#!/usr/bin/env python3
"""
Development tools for DAFilms.cz Kodi addon
Run with: python3 datools.py [command]
"""

import sys
import os
import subprocess
import shutil
import zipfile
import requests
import re
import traceback
from pathlib import Path


# ruff: noqa: T201


def build_addon(version="1.0.0"):
    """Build both Kodi addon ZIP files"""
    print(f"Building DAFilms.cz Kodi addons version {version}...")

    # Create temporary directory structure
    build_dir = Path("/tmp/dafilms-build")

    # Clean up any existing build
    if build_dir.exists():
        shutil.rmtree(build_dir)

    # Build main addon
    print("\n=== Building Main Addon (DAFilms.cz) ===")
    build_addon_from_config(
        build_dir=build_dir,
        version=version,
        addon_id="plugin.video.dafilms.cz",
        addon_xml_path="addon.xml",
        icon_path="icon.png",
        main_py_path="main.py",
    )

    # Build junior addon
    print("\n=== Building Junior Addon (DAFilms.cz Junior) ===")
    build_addon_from_config(
        build_dir=build_dir,
        version=version,
        addon_id="plugin.video.dafilms.cz.junior",
        addon_xml_path="plugin.video.dafilms.cz.junior/addon.xml",
        icon_path="plugin.video.dafilms.cz.junior/icon.png",
        main_py_path="plugin.video.dafilms.cz.junior/main.py",
    )

    print(f"\n✅ Both addons built successfully!")


def build_addon_from_config(build_dir, version, addon_id, addon_xml_path, icon_path, main_py_path):
    """Build a Kodi addon ZIP file with the given configuration"""
    addon_build_dir = build_dir / addon_id
    addon_build_dir.mkdir(parents=True)
    resources_dir = addon_build_dir / "resources"
    lib_dir = resources_dir / "lib"
    lib_dir.mkdir(parents=True)

    print("Copying files...")

    # Main files
    shutil.copy(addon_xml_path, addon_build_dir)
    shutil.copy(icon_path, addon_build_dir)
    shutil.copy(main_py_path, addon_build_dir)

    # Resources
    shutil.copy("resources/settings.xml", resources_dir)

    # Copy Python library files
    for file in Path("resources/lib").glob("*.py"):
        if file.name != "__pycache__":
            shutil.copy(file, lib_dir)

    # Create ZIP with proper structure
    print("Creating ZIP file...")
    zip_path = Path(f"../{addon_id}-{version}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in addon_build_dir.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(build_dir)
                zipf.write(file, arcname)

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


def run_tests():
    """Run tests using pytest"""
    print("Running tests...")

    # Run pytest and stream output in real-time with color support
    process = subprocess.Popen(
        ["python", "-m", "pytest", "tests", "-vv", "--color=yes"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        universal_newlines=True,
    )

    # Stream stdout with color preservation
    for line in process.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()

    # Stream stderr with color preservation
    for line in process.stderr:
        sys.stderr.write(line)
        sys.stderr.flush()


def main():
    if len(sys.argv) < 2:
        print("DAFilms.cz Development Tools")
        print("Usage: python3 datools.py [command]")
        print("Commands:")
        print("  install       - Install via symlink")
        print("  test          - Run tests")
        print("  deps          - Check dependencies")
        print("  logs          - Show Kodi logs")
        print("  build         - Build the Kodi addon ZIP file")
        print("  clean         - Clean build artifacts")

        return

    command = sys.argv[1]

    if command == "install":
        install_symlink()
    elif command == "test":
        run_tests()
    elif command == "deps":
        check_dependencies()
    elif command == "logs":
        show_logs()
    elif command == "build":
        version = sys.argv[2] if len(sys.argv) > 2 else "1.0.0"
        build_addon(version)
    elif command == "clean":
        clean_build()
    else:
        print(f"Unknown command: {command}")


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

    # Filter for our addon with context to capture full tracebacks
    print("\nFiltering for DAFilms (with error context):")
    result = subprocess.run(
        ["grep", "-E", "-A", "3", "-B", "1", "dafilms|DAFilms|Error|Traceback|Exception|AttributeError", str(log_file)],
        capture_output=True,
        text=True
    )
    if result.stdout:
        print(result.stdout)
    else:
        print("No matching entries found")


if __name__ == "__main__":
    main()
