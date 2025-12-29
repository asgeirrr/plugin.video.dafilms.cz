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
    success = api.login(email, password)
    if not success:
        pytest.fail("Login failed, check DAFILMS_EMAIL and DAFILMS_PASSWORD env vars.")
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
    expected_details = FilmDetails(
        id="10919-karel-ja-a-ty",
        title="Karel, já a ty",
        url="https://dafilms.cz/film/10919-karel-ja-a-ty",
        thumb="https://dafilms.cz/media/_cache/small/gallery/2021/01/22/Karel_ja_a_ty_1.jpg",
    )
    assert expected_details in results


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
