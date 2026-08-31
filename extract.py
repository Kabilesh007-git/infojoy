import requests
from bs4 import BeautifulSoup
import re
import time


class ExtractBG:

    def __init__(self, movie_name, years):

        self.movie_name = movie_name.strip()
        self.years = str(years).strip()

        self.base_url = "https://www.themoviedb.org"

        # =====================================================
        # SESSION
        # =====================================================

        self.session = requests.Session()

        self.session.headers.update({

            "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/142.0.0.0 Safari/537.36",

            "Accept":
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,"
                "*/*;q=0.8",

            "Accept-Language":
                "en-US,en;q=0.9",

            "Connection":
                "keep-alive"
        })

        # =====================================================
        # DATA
        # =====================================================

        self.name = None
        self.url = None
        self.date = None
        self.poster = None
        self.bg_poster = None

    # =========================================================
    # NORMALIZE
    # =========================================================

    def normalize(self, text):

        text = text.lower().strip()

        # Remove (...) part
        text = re.sub(
            r"\([^)]*\)",
            "",
            text
        )

        # Remove extra spaces
        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()

    # =========================================================
    # REQUEST
    # =========================================================

    def get_page(self, url, params=None):

        for attempt in range(1, 4):

            try:

                """print(
                    f"[{attempt}/3] GET:",
                    url,
                    params
                )"""

                response = self.session.get(
                    url,
                    params=params,
                    timeout=10
                )

                """print(
                    "Status:",
                    response.status_code
                )"""

                if response.status_code == 200:

                    return response

                print(
                    "Unexpected status:",
                    response.status_code
                )

            except requests.exceptions.Timeout:

                print(
                    "Request timeout"
                )

            except requests.exceptions.ConnectionError as e:

                """print(
                    "Connection error:",
                    e
                )"""

            except requests.exceptions.RequestException as e:

                """print(
                    "Request error:",
                    e
                )"""

            if attempt < 3:

                time.sleep(1)

        return None

    # =========================================================
    # FIRST STAGE
    # SEARCH MOVIE
    # =========================================================

    def first_stage(self):

        search_url = (
            f"{self.base_url}/search/movie"
        )

        # IMPORTANT:
        # Send query through params
        #
        # This creates:
        #
        # https://www.themoviedb.org/search/movie?query=karuppu

        response = self.get_page(
            search_url,
            params={
                "query": self.movie_name
            }
        )

        if response is None:

            print(
                "TMDB search failed."
            )

            return False

        # =====================================================
        # PARSE
        # =====================================================

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # =====================================================
        # MOVIE CARDS
        # =====================================================

        movies = soup.select(
            "div.comp\\:media-card"
        )

        """print(
            "Movie cards found:",
            len(movies)
        )"""

        if not movies:

            print(
                "No movie cards found."
            )

            return False

        # =====================================================
        # LOOP
        # =====================================================

        for movie in movies:

            # -------------------------------------------------
            # TITLE
            # -------------------------------------------------

            title_tag = movie.select_one(
                "h2"
            )

            if not title_tag:

                continue

            # Get first span
            #
            # Kattradhu Thamizh
            #
            # instead of:
            #
            # Kattradhu Thamizh (கற்றது தமிழ்)

            first_span = title_tag.select_one(
                "span"
            )

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

            # -------------------------------------------------
            # DATE
            # -------------------------------------------------

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

            # -------------------------------------------------
            # DEBUG
            # -------------------------------------------------

            """print(
                "Checking:",
                name,
                "|",
                date
            )"""

            # -------------------------------------------------
            # YEAR
            # -------------------------------------------------

            if self.years not in date:

                continue

            # -------------------------------------------------
            # NAME
            # -------------------------------------------------

            if (
                self.normalize(name)
                !=
                self.normalize(
                    self.movie_name
                )
            ):

                continue

            # -------------------------------------------------
            # URL
            # -------------------------------------------------

            link = movie.select_one(
                "a[href^='/movie/']"
            )

            if not link:

                continue

            movie_url = link.get(
                "href"
            )

            if not movie_url:

                continue

            # =================================================
            # SAVE
            # =================================================

            self.name = name
            self.url = movie_url
            self.date = date

            """print()
            print(
                "MOVIE FOUND"
            )

            print(
                "Name:",
                self.name
            )

            print(
                "URL:",
                self.url
            )

            print(
                "Date:",
                self.date
            )"""

            # =================================================
            # SECOND STAGE
            # =================================================

            return self.second_stage(
                movie_url
            )

        print()
        print(
            "Matching movie not found."
        )

        return False

    # =========================================================
    # SECOND STAGE
    # POSTER + BACKGROUND
    # =========================================================

    def second_stage(self, url):

        # -----------------------------------------------------
        # FULL URL
        # -----------------------------------------------------

        if url.startswith("http"):

            full_url = url

        else:

            full_url = (
                self.base_url +
                url
            )

        """print()
        print(
            "Movie page:",
            full_url
        )"""

        # -----------------------------------------------------
        # REQUEST
        # -----------------------------------------------------

        response = self.get_page(
            full_url
        )

        if response is None:

            print(
                "Movie page failed."
            )

            return False

        # =====================================================
        # SAVE HTML
        # =====================================================

        

        # =====================================================
        # PARSE
        # =====================================================

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

        # =====================================================
        # BACKGROUND
        # =====================================================

        styles = soup.find_all(
            "style"
        )

        for style in styles:

            css = style.get_text()

            # We specifically look for:
            #
            # div.header.large.first {
            #
            #     background-image: url('...');
            #
            # }

            if "div.header.large.first" not in css:

                continue

            match = re.search(
                r"div\.header\.large\.first\s*\{"
                r".*?"
                r"background-image\s*:"
                r"\s*url\(['\"]?"
                r"([^'\")]+)"
                r"['\"]?\)",
                css,
                re.IGNORECASE |
                re.DOTALL
            )

            if match:

                self.bg_poster = (
                    match.group(1).strip()
                )

                break

        # =====================================================
        # RESULT
        # =====================================================

        """print()
        print(
            "=" * 60
        )

        print(
            "EXTRACTION RESULT"
        )

        print(
            "=" * 60
        )

        print(
            "Movie      :",
            self.name
        )

        print(
            "URL        :",
            self.url
        )

        print(
            "Poster 2x  :",
            self.poster
        )

        print(
            "Background :",
            self.bg_poster
        )

        print(
            "=" * 60
        )"""

        return True


# =============================================================
# TEST
# =============================================================



obj = ExtractBG

"""(
        "karuppu",
        2026
    )

    obj.first_stage()
    print(obj.poster)
    print(obj.bg_poster)"""

"""if result:

        print()
        print(
            "SUCCESS"
        )

        print(
            "POSTER:",
            obj.poster
        )

        print(
            "BACKGROUND:",
            obj.bg_poster
        )

    else:

        print()
        print(
            "Extraction failed."
        )"""



