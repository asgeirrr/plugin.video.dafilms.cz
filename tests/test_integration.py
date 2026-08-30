import pytest
from resources.lib.api import DAFilmsAPI, FilmDetails
import os
import json
from bs4 import BeautifulSoup


@pytest.fixture(scope="module")
def api():
    """Fixture that provides an authenticated DAFilmsAPI instance"""
    email = os.environ.get("DAFILMS_EMAIL")
    password = os.environ.get("DAFILMS_PASSWORD")

    api = DAFilmsAPI()
    api.login(email, password)
    return api


def test_stream_extraction(api):
    """Test stream URL extraction for a specific film"""
    film_id = "18800"

    stream_url = api.get_stream_url(film_id)
    # Stream URL should either be a valid URL or None
    assert stream_url.startswith(
        "https://d144orpukbkwri.cloudfront.net/films/DreamScenario/DreamScenario-720p.mp4"
    )


def test_search(api):
    """Test search functionality"""
    api = DAFilmsAPI()
    results = api.search_films("Karel")
    # Verify the expected film is in results with data from listing page
    film_ids = [r.id for r in results]
    assert "10919-karel-ja-a-ty" in film_ids
    film = next(r for r in results if r.id == "10919-karel-ja-a-ty")
    assert film.title == "Karel, já a ty"
    assert (
        film.thumb == "https://dafilms.cz/media/_cache/small/gallery/2021/01/22/Karel_ja_a_ty_1.jpg"
    )
    # With optimization, plot and director should be extracted from listing
    assert film.plot is not None
    assert film.director is not None


def test_search_junior(api):
    """Test search functionality"""
    api = DAFilmsAPI()
    api.BASE_URL = "https://dafilms.cz/junior"

    results = api.search_films("Karel")

    # Verify expected film is in results with data from listing page
    film_ids = [r.id for r in results]
    assert "9955-filmovy-dobrodruh-karel-zeman" in film_ids
    film = next(r for r in results if r.id == "9955-filmovy-dobrodruh-karel-zeman")
    assert film.title == "Filmový dobrodruh Karel Zeman"
    assert (
        film.thumb
        == "https://dafilms.cz/media/_cache/small/gallery/2016/02/17/Karel_Zeman_young.jpg"
    )
    # Director should be extracted from listing (plot may or may not be present)
    assert film.director is not None

    # Verify main site films are not in junior results
    assert "10919-karel-ja-a-ty" not in film_ids


def test_film_details(api):
    """Test film details extraction for a specific film"""
    details = api.get_film_details(18800)
    assert details == {
        "title": "To se mi snad zd\xe1",
        "plot": "Nen\xe1padn\xfd vysoko\u0161kolsk\xfd profesor Paul (Nicolas Cage) se ze dne na den za\u010dne objevovat ve snech milion\u016f lid\xed po cel\xe9m sv\u011bt\u011b a stane se tak glob\xe1ln\xed celebritou.",
        "director": "Kristoffer Borgli",
        "cast": [
            "Nicolas Cage",
            "Julianne Nicholson",
            "Michael Cera",
            "Tim Meadows",
            "Dylan Gelula",
            "Dylan Baker",
            "Jessica Clement",
            "Lily Bird",
            "Star Slade",
            "Kaleb Horn",
            "Liz Adjei",
        ],
        "thumb": "https://dafilms.cz/media/gallery/2025/11/26/To_se_mi_snad_zda_1.jpeg",
    }


def test_purchased_films(api):
    """Test purchased films listing functionality"""
    purchased_films = api.get_purchased_films()
    assert all(isinstance(f, FilmDetails) for f in purchased_films)


def test_most_watched_films():
    """Test most watched films listing functionality"""
    api = DAFilmsAPI()
    most_watched_films = api.get_most_watched_films()
    # Verify we get a list of FilmDetails objects
    assert len(most_watched_films) > 2
    # Verify each film has required attributes
    for film in most_watched_films:
        assert isinstance(film, FilmDetails)
        assert film.id
        assert film.title
        assert film.url
        # URL should be an absolute URL
        assert film.url.startswith("http")
