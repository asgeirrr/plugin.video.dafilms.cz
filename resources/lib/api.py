import json
import re
from dataclasses import dataclass
from typing import Any

import requests
from bs4 import BeautifulSoup


@dataclass
class FilmDetails:
    """Dataclass to represent film details"""

    id: str
    title: str
    url: str
    thumb: str | None = None


class DAFilmsAPIError(Exception):
    """Base exception for all DAFilms API errors"""

    pass


class DAFilmsAPI:
    """API client for DAFilms.cz"""

    BASE_URL = "https://dafilms.cz"
    # Based on research, the site uses HTML scraping rather than a public API
    # We'll need to parse HTML content

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Kodi/DAFilms Addon",
                "Accept": "application/json",
            }
        )
        self._logged_in = False
        self._csrf_token = None

    def get_newest_films(self, page: int = 1, limit: int = 20) -> list[FilmDetails]:
        """Get newest films from DAFilms"""
        return self._get_films_from_listing(page=page, limit=limit, sort="newest")

    def get_all_films(self, page: int = 1, limit: int = 50) -> list[FilmDetails]:
        """Get all films from the comprehensive listing"""
        return self._get_films_from_listing(page=page, limit=limit, sort="all")

    def get_subscription_films(self, page: int = 1, limit: int = 50) -> list[FilmDetails]:
        """Get films available for subscribers from the SVOD collection"""
        try:
            # Use the SVOD collection URL
            url = f"{self.BASE_URL}/collection/35-svod-covered"
            response = self.session.get(url)
            response.raise_for_status()

            # Reuse the existing film parsing logic
            return self._parse_films_from_page(response.text, limit)
        except requests.RequestException as e:
            raise DAFilmsAPIError(f"Network error fetching subscription films: {str(e)}") from e

    def get_purchased_films(self) -> list[FilmDetails]:
        """Get films that the user has purchased from the payments page"""
        try:
            # Fetch the user's payments page
            payments_url = f"{self.BASE_URL}/user/detail/payments"
            response = self.session.get(payments_url)
            response.raise_for_status()

            # Parse the payments table to find purchased films
            soup = BeautifulSoup(response.text, "html.parser")

            # Find the payments table
            payments_table = soup.find("table", class_="table-responsive")
            if not payments_table:
                return []

            # Find all rows in the table body
            rows = (
                payments_table.find("tbody").find_all("tr") if payments_table.find("tbody") else []
            )

            purchased_films = []

            # Parse each row to find "Stažení filmu" entries
            for row in rows:
                # Find the purpose column (second column)
                columns = row.find_all("td")
                if len(columns) >= 2:
                    purpose_cell = columns[1]

                    # Check if this is a film purchase
                    if "Stažení filmu" in purpose_cell.get_text():
                        # Find the film link
                        film_link = purpose_cell.find("a", href=True)
                        if film_link and "film/" in film_link["href"]:
                            film_url = film_link["href"]
                            if not film_url.startswith("http"):
                                film_url = f"{self.BASE_URL}{film_url}"

                            # Extract film ID from URL
                            film_id = film_url.split("/film/")[-1].split("/")[0]

                            # Avoid duplicates
                            if film_id not in [f.id for f in purchased_films]:
                                film_details = FilmDetails(
                                    id=film_id,
                                    title=film_link.get_text(strip=True),
                                    url=film_url,
                                    thumb=None,  # Thumbnail will be fetched when needed
                                )
                                purchased_films.append(film_details)

            return purchased_films

        except requests.RequestException as e:
            raise DAFilmsAPIError(f"Network error fetching purchased films: {str(e)}") from e
        except Exception as e:
            raise DAFilmsAPIError(f"Error parsing purchased films: {str(e)}") from e

    def _parse_films_from_page(self, html_content: str, limit: int = 50) -> list[FilmDetails]:
        """Internal method to parse films from HTML page content"""
        soup = BeautifulSoup(html_content, "html.parser")
        films = []

        # Find all film card elements - same structure as other listings
        film_cards = soup.find_all("li", attrs={"data-film-item": "true"})

        for card in film_cards:
            # Find the main link element
            link_element = card.find("a", class_="ui-movie-card__link")
            if not link_element:
                continue

            film_url = link_element["href"]
            if not film_url.startswith("http"):
                film_url = f"{self.BASE_URL}{film_url}"

            film_id = film_url.split("/film/")[-1].split("/")[0]

            # Extract title
            title_element = card.find(class_="ui-movie-card__link--title")
            if not title_element:
                title_element = card.find(class_="ui-movie-card__title")

            title = title_element.get_text(strip=True) if title_element else "Unknown Title"

            # Extract thumbnail
            thumb = None
            if link_element.has_attr("style"):
                style = link_element["style"]
                match = re.search(r"url\(['\"]([^'\"]+)['\"]\)", style)
                if match:
                    thumb = match.group(1)

            if not thumb:
                img_element = card.find("img")
                if img_element and img_element.has_attr("src"):
                    thumb = img_element["src"]

            films.append(FilmDetails(film_id, title, film_url, thumb))

            if len(films) >= limit:
                break

        return films

    def _get_films_from_listing(
        self, page: int = 1, limit: int = 20, sort: str = "newest", order: str = "asc"
    ) -> list[FilmDetails]:
        """Internal method to get films from various listings"""
        try:
            # Use the comprehensive film listing endpoint with sorting parameters
            # o=t orders by title, o=r orders by addition time, oa=1 sets ascending order
            if sort == "title":
                url = f"{self.BASE_URL}/film?o=t&oa={'1' if order == 'asc' else '0'}"
            elif sort == "newest":
                url = f"{self.BASE_URL}/film?o=r&oa=1"  # o=r orders by addition time (newest first)
            elif sort == "oldest":
                url = f"{self.BASE_URL}/film?o=r&oa=0"  # o=r orders by addition time (oldest first)
            else:
                url = f"{self.BASE_URL}/film"

            response = self.session.get(url)
            response.raise_for_status()

            # Reuse the common film parsing logic
            return self._parse_films_from_page(response.text, limit)
        except requests.RequestException as e:
            raise DAFilmsAPIError(f"Network error fetching films: {str(e)}") from e

    def search_films(self, query: str, page: int = 1) -> list[FilmDetails]:
        """Search for films using the film search endpoint"""
        try:
            # Use the film search endpoint with query parameter
            response = self.session.get(f"{self.BASE_URL}/film", params={"q": query})
            response.raise_for_status()

            # Parse the HTML response to extract film results using shared method
            return self._parse_films_from_page(response.text)
        except requests.RequestException as e:
            raise DAFilmsAPIError(f"Network error searching films: {str(e)}") from e

    def get_film_details(self, film_id: str) -> dict[str, Any]:
        """Get details for a specific film by parsing the film page"""
        try:
            response = self.session.get(f"{self.BASE_URL}/film/{film_id}")
            response.raise_for_status()

            # Extract JSON-LD data which contains structured film information
            # Look for Movie type JSON-LD specifically, as there may be multiple JSON-LD scripts
            soup = BeautifulSoup(response.text, "html.parser")
            json_ld_scripts = soup.find_all("script", {"type": "application/ld+json"})
            film_data = None

            for script in json_ld_scripts:
                # Try to clean up the JSON string and parse again
                try:
                    # Remove control characters and fix common issues
                    clean_string = (
                        script.string.replace("\n", "")
                        .replace("\r", "")
                        .replace("\t", "")
                        .replace("\u00a0", " ")  # Replace non-breaking spaces
                        .replace("\u2013", "-")  # Replace en dash
                        .replace("\u201c", '"')  # Replace left double quote
                        .replace("\u201d", '"')  # Replace right double quote
                    )
                    # Remove other control characters
                    clean_string = "".join(
                        ch for ch in clean_string if ch.isprintable() or ch.isspace()
                    )
                    clean_string = " ".join(clean_string.split())  # Normalize whitespace
                    data = json.loads(clean_string)
                    if data.get("@type") == "Movie":
                        film_data = data
                        break
                except Exception:
                    continue

            details = {
                "title": film_data.get("name", ""),
                "plot": film_data.get("description", ""),
                "director": film_data.get("director", [{}])[0].get("name")
                if film_data.get("director")
                else None,
                "cast": [actor.get("name") for actor in film_data.get("actor", [])],
                "thumb": film_data.get("image"),
            }

            return details

        except requests.RequestException as e:
            raise DAFilmsAPIError(f"Network error fetching film {film_id}: {str(e)}") from e
        except Exception as e:
            raise DAFilmsAPIError(f"Unexpected error parsing film {film_id}: {str(e)}") from e

    def check_film_access(self, film_id: str) -> bool:
        """Check if user has access to a film (not requiring purchase)"""
        if not self._ensure_logged_in():
            return False

        try:
            # Test the player endpoint to see if we get 403 (requires purchase) or 200 (has access)
            player_url = f"{self.BASE_URL}/film/{film_id}/player"
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0",
                "Accept": "*/*",
                "X-Requested-With": "XMLHttpRequest",
            }

            response = self.session.get(player_url, headers=headers)

            if response.status_code == 200:
                return True  # User has access
            elif response.status_code == 403:
                return False  # Film requires purchase
            else:
                # Other status codes - assume no access for safety
                return False

        except requests.RequestException:
            return False

    def get_stream_url(self, film_id: str) -> str:
        """Get stream URL for a film by parsing the film page"""
        # Note: Login is handled by the session manager, not here
        # This method assumes the session is already authenticated

        try:
            # DAFilms.cz uses a player endpoint that returns JSON with stream configuration
            # This is the only reliable method we've found that works
            player_url = f"{self.BASE_URL}/film/{film_id}/player"
            try:
                # Use the same headers as the browser
                headers = {
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0",
                    "Accept": "*/*",
                    "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": f"{self.BASE_URL}/film/{film_id}-to-se-mi-snad-zda",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-origin",
                }

                player_response = self.session.get(player_url, headers=headers)

                if player_response.status_code == 200:
                    # Save for debugging
                    with open(f"/tmp/dafilms_player_{film_id}.json", "w", encoding="utf-8") as f:
                        f.write(player_response.text)

                    # Debug logging
                    import logging

                    logging.info(f"DAFilms API: Player response status 200 for film {film_id}")

                    # Try to parse as JSON
                    try:
                        player_data = player_response.json()
                        logging.info(
                            f"DAFilms API: Successfully parsed player data for film {film_id}"
                        )

                        # Extract HTML snippet containing player configuration
                        if (
                            isinstance(player_data, dict)
                            and "snippets" in player_data
                            and "#film-player-container" in player_data["snippets"]
                        ):
                            html = player_data["snippets"]["#film-player-container"]

                            # Extract the sources array using the working approach from extract_streams.py
                            sources_match = re.search(
                                r"sources\s*=\s*\[([^\]]+)\]", html, re.DOTALL
                            )
                            if sources_match:
                                sources_str = sources_match.group(1)

                                # Extract individual source objects - handle escaped quotes
                                source_objects = re.findall(r"\{[^}]+\}", sources_str)

                                streams = []
                                for i, source_obj in enumerate(source_objects):
                                    # Extract URL - handle escaped quotes and backslashes
                                    url_match = re.search(r'"src"\s*:\s*"([^"]+)"', source_obj)
                                    if url_match:
                                        url = url_match.group(1).replace("\\/", "/")

                                        # Extract label
                                        label_match = re.search(
                                            r'"label"\s*:\s*"([^"]+)"', source_obj
                                        )
                                        label = (
                                            label_match.group(1)
                                            if label_match
                                            else f"Quality {i + 1}"
                                        )

                                        streams.append(
                                            {
                                                "url": url,
                                                "label": label,
                                                "quality": "HD" if "720p" in url else "SD",
                                            }
                                        )

                                if streams:
                                    # Return HD stream if available, otherwise the first stream
                                    hd_stream = next(
                                        (s for s in streams if s["quality"] == "HD"), None
                                    )
                                    if hd_stream:
                                        return hd_stream["url"]
                                    else:
                                        return streams[0]["url"]

                        # Fallback: look for common stream URL patterns in JSON
                        if "sources" in player_data:
                            for source in player_data["sources"]:
                                if "src" in source:
                                    return source["src"]
                        if "stream" in player_data:
                            return player_data["stream"]
                        if "url" in player_data:
                            return player_data["url"]

                        # Recursively search for URLs
                        for _key, value in player_data.items():
                            if isinstance(value, str) and ("http" in value or "stream" in value):
                                return value
                            elif isinstance(value, (dict, list)):
                                # Recursive search would go here
                                pass

                    except json.JSONDecodeError:
                        # Not JSON, might be HTML or other format

                        # Look for stream URLs in text - improved pattern
                        sources_match = re.search(
                            r"sources\s*=\s*\[([^\]]+)\]", player_response.text, re.DOTALL
                        )
                        if sources_match:
                            sources_str = sources_match.group(1)

                            # Extract URLs from the sources array - handle escaped characters
                            url_matches = re.findall(r'https[^"\s]+\.mp4', sources_str)
                            if url_matches:
                                # Return the highest quality (first one, or one with 720p)
                                hd_match = next((url for url in url_matches if "720p" in url), None)
                                return hd_match if hd_match else url_matches[0]

                        # Fallback: look for any MP4 URLs
                        url_matches = re.findall(r'https?://[^"\'\s,&]+\.mp4', player_response.text)
                        if url_matches:
                            # Return HD if available
                            hd_match = next((url for url in url_matches if "720p" in url), None)
                            return hd_match if hd_match else url_matches[0]
                elif player_response.status_code == 403:
                    return "REQUIRES_PURCHASE"
                else:
                    pass
            except Exception:
                pass

            # Debug logging
            import logging

            raise DAFilmsAPIError(f"Could not extract stream URL for film {film_id}")
        except requests.RequestException as e:
            raise DAFilmsAPIError(
                f"Network error fetching stream for film {film_id}: {str(e)}"
            ) from e
        except Exception as e:
            raise DAFilmsAPIError(
                f"Unexpected error extracting stream for film {film_id}: {str(e)}"
            ) from e

    def login(self, username: str, password: str) -> bool:
        """Login to DAFilms.cz to access protected content"""
        try:
            # First get the main page or a film page to extract CSRF token
            # The token is likely available on most pages
            main_page = self.session.get(f"{self.BASE_URL}/")
            main_page.raise_for_status()

            soup = BeautifulSoup(main_page.text, "html.parser")
            csrf_token = soup.find("input", {"name": "_csrf_token"})

            # If not found on main page, try a film page
            if not csrf_token:
                film_page = self.session.get(f"{self.BASE_URL}/film")
                film_page.raise_for_status()
                soup = BeautifulSoup(film_page.text, "html.parser")
                csrf_token = soup.find("input", {"name": "_csrf_token"})

            if not csrf_token:
                return False

            self._csrf_token = csrf_token.get("value")

            # Prepare login data - use email instead of _username based on the curl example
            login_data = {
                "email": username,
                "password": password,
                "_csrf_token": self._csrf_token,
                "remember_me": "on",
            }

            # Submit login form with proper headers
            login_response = self.session.post(
                f"{self.BASE_URL}/login_check",
                data=login_data,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "cs,sk;q=0.8,en-US;q=0.5,en;q=0.3",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Origin": self.BASE_URL,
                    "Referer": f"{self.BASE_URL}/",  # Changed from /login to / since login page doesn't exist
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "same-origin",
                },
            )

            # Check if login was successful
            # Successful login typically redirects to homepage or previous page
            if login_response.status_code == 200:
                # Check if we got a redirect or if we're now logged in
                # Look for logout link or user info in the response
                response_text = login_response.text
                if "Odhlásit" in response_text or "logout" in response_text:
                    self._logged_in = True
                    return True
                elif "Přihlásit" in response_text or "login" in response_text:
                    return False
                else:
                    # Check if we can access a protected resource
                    test_response = self.session.get(f"{self.BASE_URL}/film")
                    if test_response.status_code == 200:
                        self._logged_in = True
                        return True

            return False

        except requests.RequestException:
            return False

    def _ensure_logged_in(self) -> bool:
        """Ensure we're logged in before accessing protected content"""
        if not self._logged_in:
            # Try to login using stored credentials
            # In a real Kodi addon, credentials would be stored in addon settings
            # For now, we'll return False to indicate not logged in
            pass
        return self._logged_in

    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict[str, Any]:
        """Make API request with error handling"""
        try:
            response = self.session.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise DAFilmsAPIError(f"API request failed: {str(e)}") from e
