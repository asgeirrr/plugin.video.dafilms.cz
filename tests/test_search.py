"""Tests for search history functionality"""
import sys


def test_search_history_management(tmp_path, monkeypatch):
    """Test search history add/dedupe/limit logic"""
    import json
    
    # Mock sys.argv to avoid the _handle assignment in search.py
    monkeypatch.setattr(sys, "argv", ["script.py", "0"])
    
    from resources.lib.search import add_to_search_history, load_search_history

    # Patch the history file location
    history_file = tmp_path / "search_history.json"
    monkeypatch.setattr(
        "resources.lib.search.get_search_history_file",
        lambda: str(history_file)
    )

    # Test adding entries
    add_to_search_history("film1")
    add_to_search_history("film2")
    add_to_search_history("film3")

    history = load_search_history()
    assert history == ["film3", "film2", "film1"]

    # Test deduplication - should move to front
    add_to_search_history("film1")
    history = load_search_history()
    assert history == ["film1", "film3", "film2"]

    # Test 20-item limit
    # First clear history by adding 20+ unique items
    for i in range(25):
        add_to_search_history(f"item{i}")
    # Now add one more - should push out the oldest (item0)
    add_to_search_history("new")
    history = load_search_history()
    assert len(history) == 20
    assert history[0] == "new"
    assert "item0" not in history  # Oldest should be gone
    assert "item24" in history  # Most recent before "new" should still be there


def test_empty_history(tmp_path, monkeypatch):
    """Test loading empty/missing history file"""
    # Mock sys.argv to avoid the _handle assignment in search.py
    monkeypatch.setattr(sys, "argv", ["script.py", "0"])
    
    from resources.lib.search import load_search_history

    # Patch to non-existent file
    history_file = tmp_path / "nonexistent.json"
    monkeypatch.setattr(
        "resources.lib.search.get_search_history_file",
        lambda: str(history_file)
    )

    history = load_search_history()
    assert history == []


def test_history_file_persistence(tmp_path, monkeypatch):
    """Test that history is saved to and loaded from file correctly"""
    import json
    
    # Mock sys.argv to avoid the _handle assignment in search.py
    monkeypatch.setattr(sys, "argv", ["script.py", "0"])
    
    from resources.lib.search import add_to_search_history, load_search_history

    history_file = tmp_path / "search_history.json"
    monkeypatch.setattr(
        "resources.lib.search.get_search_history_file",
        lambda: str(history_file)
    )

    add_to_search_history("test1")
    add_to_search_history("test2")

    # Verify file was created and contains correct data
    assert history_file.exists()
    with open(history_file, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
    assert saved_data == ["test2", "test1"]

    # Verify loading returns the same data
    loaded = load_search_history()
    assert loaded == ["test2", "test1"]
