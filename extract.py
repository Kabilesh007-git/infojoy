import requests
from bs4 import BeautifulSoup
import re


class ExtractBG:

    def __init__(self, movie_name, year):

        self.movie_name = movie_name.strip()
        self.year = str(year).strip()

        self.base_url = "https://www.themoviedb.org"

        # Stage 1
        self.name = None
        self.href = None
        self.date = None

        # Stage 2
        self.poster = None
        self.bg_poster = None

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/142.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.themoviedb.org/"
        })

    # =========================================================
    # NORMALIZE NAME
    # =========================================================

    def normalize(self, text):

        if not text:
            return ""

        text = text.lower().strip()

        # Replace dashes with spaces
        text = text.replace("-", " ")
        text = text.replace("–", " ")
        text = text.replace("—", " ")

        # Remove (...) 
        text = re.sub(r"\([^)]*\)", "", text)

        # Remove [...]
        text = re.sub(r"\[[^\]]*\]", "", text)

        # Keep English letters and numbers
        text = re.sub(r"[^a-z0-9\s]", " ", text)

        # Remove extra spaces
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    # =========================================================
    # REQUEST
    # =========================================================

    def get_page(self, url, params=None):

        try:

            print("GET:", url)

            response = self.session.get(
                url,
                params=params,
                timeout=15,
                allow_redirects=True
            )

            print("STATUS:", response.status_code)

            if response.status_code == 200:
                return response

            print(
                "Unexpected status:",
                response.status_code
            )

        except requests.exceptions.ConnectionError as e:

            print(
                "Connection error:",
                e
            )

        except requests.exceptions.Timeout:

            print("Request timeout")

        except requests.exceptions.RequestException as e:

            print(
                "Request error:",
                e
            )

        return None

    # =========================================================
    # STAGE 1
    # SEARCH MOVIE
    # =========================================================

    def stage_one(self):

        print()
        print("=" * 60)
        print("STAGE 1 - SEARCH MOVIE")
        print("=" * 60)

        search_url = (
            f"{self.base_url}/search/movie"
        )

        response = self.get_page(
            search_url,
            params={
                "query": self.movie_name
            }
        )

        if response is None:

            print("TMDB search failed.")

            return False

        # -----------------------------------------------------
        # Save search HTML
        # -----------------------------------------------------

        with open(
            "search.html",
            "w",
            encoding="utf-8"
        ) as file:

            file.write(response.text)

        print("Search HTML saved.")

        # -----------------------------------------------------
        # Parse
        # -----------------------------------------------------

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # TMDB current movie cards
        movies = soup.select(
            "div.comp\\:media-card"
        )

        print(
            "Movie cards found:",
            len(movies)
        )

        if not movies:

            print("No movie cards found.")

            return False

        # -----------------------------------------------------
        # Search name
        # -----------------------------------------------------

        searched_name = self.normalize(
            self.movie_name
        )

        # -----------------------------------------------------
        # Check every movie
        # -----------------------------------------------------

        for movie in movies:

            # ================================================
            # TITLE
            # ================================================

            title_tag = movie.select_one("h2")

            if not title_tag:
                continue

            # First span contains English title.
            #
            # Example:
            #
            # <h2>
            #     <span>Dhurandhar: The Revenge</span>
            #     <span> (धुरंधर: द रिवेंज)</span>
            # </h2>

            first_span = title_tag.select_one("span")

            if first_span:

                name = first_span.get_text(
                    " ",
                    strip=True
                )

            else:

                name = title_tag.get_text(
                    " ",
                    strip=True
                )

            # ================================================
            # DATE
            # ================================================

            date_tag = movie.select_one(
                ".release_date"
            )

            if date_tag:

                date = date_tag.get_text(
                    " ",
                    strip=True
                )

            else:

                date = ""

            # ================================================
            # HREF
            # ================================================

            link = movie.select_one(
                "a[href^='/movie/']"
            )

            if not link:
                continue

            href = link.get("href")

            if not href:
                continue

            # ================================================
            # PRINT
            # ================================================

            print()
            print("--------------------------------")
            print("NAME :", name)
            print("DATE :", date)
            print("HREF :", href)
            print("--------------------------------")

            # ================================================
            # YEAR CHECK
            # ================================================

            if self.year not in date:

                print("YEAR : NOT MATCHED")

                continue

            print("YEAR : MATCHED")

            # ================================================
            # NAME CHECK
            # ================================================

            found_name = self.normalize(
                name
            )

            print(
                "SEARCH NAME:",
                searched_name
            )

            print(
                "FOUND NAME :",
                found_name
            )

            if searched_name != found_name:

                print("NAME : NOT MATCHED")

                continue

            print("NAME : MATCHED")

            # ================================================
            # MOVIE FOUND
            # ================================================

            self.name = name
            self.href = href
            self.date = date

            print()
            print("=" * 60)
            print("MOVIE FOUND")
            print("=" * 60)

            print("NAME :", self.name)
            print("YEAR :", self.year)
            print("DATE :", self.date)
            print("HREF :", self.href)

            print("=" * 60)

            # ================================================
            # SEND HREF TO STAGE 2
            # ================================================

            return self.stage_two(
                self.href
            )

        # -----------------------------------------------------
        # Not found
        # -----------------------------------------------------

        print()
        print("No matching movie found.")

        return False

    # =========================================================
    # STAGE 2
    # GET POSTER + BACKGROUND
    # =========================================================

    def stage_two(self, href):

        print()
        print("=" * 60)
        print("STAGE 2 - MOVIE PAGE")
        print("=" * 60)

        # -----------------------------------------------------
        # Create full URL
        # -----------------------------------------------------

        if href.startswith("http"):

            movie_url = href

        else:

            movie_url = (
                self.base_url
                + href
            )

        print(
            "MOVIE URL:",
            movie_url
        )

        # -----------------------------------------------------
        # Request movie page
        # -----------------------------------------------------

        response = self.get_page(
            movie_url
        )

        if response is None:

            print(
                "Movie page request failed."
            )

            return False

        # -----------------------------------------------------
        # Save movie HTML
        # -----------------------------------------------------

        with open(
            "movie.html",
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                response.text
            )

        print(
            "Movie HTML saved: movie.html"
        )

        # -----------------------------------------------------
        # Parse
        # -----------------------------------------------------

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # =====================================================
        # POSTER
        # =====================================================

        poster_tag = soup.select_one(
            "img.poster"
        )

        if poster_tag:

            srcset = poster_tag.get(
                "srcset",
                ""
            )

            print()
            print("POSTER SRCSET:")
            print(srcset)

            # Example:
            #
            # URL 1x,
            # URL 2x

            for item in srcset.split(","):

                parts = item.strip().split()

                if len(parts) != 2:
                    continue

                image_url = parts[0]
                size = parts[1]

                if size == "2x":

                    self.poster = image_url

                    break

            # Fallback
            if not self.poster:

                self.poster = poster_tag.get(
                    "src"
                )

        # =====================================================
        # BACKGROUND
        # =====================================================

        for style in soup.find_all("style"):

            css = style.get_text()

            if "div.header.large.first" not in css:
                continue

            # Find:
            #
            # background-image: url('IMAGE_URL');

            match = re.search(
                r"div\.header\.large\.first"
                r"\s*\{.*?"
                r"background-image\s*:\s*url\(\s*"
                r"['\"]?"
                r"([^'\")]+)"
                r"['\"]?"
                r"\s*\)",
                css,
                re.IGNORECASE | re.DOTALL
            )

            if match:

                self.bg_poster = (
                    match.group(1).strip()
                )

                break

        # =====================================================
        # BACKGROUND FALLBACK
        # =====================================================

        if not self.bg_poster:

            header = soup.select_one(
                "div.header.large.first"
            )

            if header:

                style = header.get(
                    "style",
                    ""
                )

                match = re.search(
                    r"background-image\s*:\s*url\(\s*"
                    r"['\"]?"
                    r"([^'\")]+)"
                    r"['\"]?"
                    r"\s*\)",
                    style,
                    re.IGNORECASE
                )

                if match:

                    self.bg_poster = (
                        match.group(1).strip()
                    )

        # =====================================================
        # CLEAN URL
        # =====================================================

        if self.poster:

            self.poster = self.poster.replace(
                "\\/",
                "/"
            )

        if self.bg_poster:

            self.bg_poster = self.bg_poster.replace(
                "\\/",
                "/"
            )

        # =====================================================
        # RESULT
        # =====================================================

        print()
        print("=" * 60)
        print("FINAL RESULT")
        print("=" * 60)

        print(
            "MOVIE      :",
            self.name
        )

        print(
            "HREF       :",
            self.href
        )

        print(
            "DATE       :",
            self.date
        )

        print()

        print(
            "POSTER 2x  :",
            self.poster
        )

        print()

        print(
            "BACKGROUND :",
            self.bg_poster
        )

        print("=" * 60)

        return True


# =============================================================
# TEST
# =============================================================

if __name__ == "__main__":

    obj = ExtractBG
    """(
        "Dhurandhar-The-Revenge",
        2026
    )

    result = obj.stage_one()

    if result:

        print()
        print("=" * 60)
        print("SUCCESS")
        print("=" * 60)

        print(
            "poster =",
            obj.poster
        )

        print(
            "bg_poster =",
            obj.bg_poster
        )

    else:

        print()
        print("=" * 60)
        print("FAILED")
        print("=" * 60)"""
    





    #