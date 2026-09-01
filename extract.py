import requests
import re
from bs4 import BeautifulSoup


class ExtractBG:

    def __init__(self, movie_name, year):

        self.movie_name = str(movie_name).strip()
        self.year = str(year).strip()

        self.poster = None
        self.bg_poster = None
        self.movie_url = None

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/142.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,image/avif,image/webp,"
                "*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.themoviedb.org/",
        })


    # ==================================================
    # NORMALIZE
    # ==================================================

    def normalize(self, text):

        if not text:
            return ""

        text = text.lower()

        text = re.sub(
            r"\([^)]*\)",
            " ",
            text
        )

        text = re.sub(
            r"\[[^\]]*\]",
            " ",
            text
        )

        text = re.sub(
            r"[^a-z0-9\s]",
            " ",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()


    # ==================================================
    # REQUEST
    # ==================================================

    def get_page(self, url, params=None):

        for attempt in range(1, 4):

            try:

                print(
                    f"\nREQUEST {attempt}/3"
                )

                print(
                    "URL:",
                    url
                )

                response = self.session.get(
                    url,
                    params=params,
                    timeout=20,
                    allow_redirects=True
                )

                print(
                    "STATUS:",
                    response.status_code
                )

                print(
                    "FINAL URL:",
                    response.url
                )

                if response.status_code == 200:

                    return response

            except requests.RequestException as e:

                print(
                    "REQUEST ERROR:",
                    e
                )

        return None


    # ==================================================
    # STAGE ONE
    # ==================================================

    def stage_one(self):

        print("\n" + "=" * 50)
        print("STAGE 1 - SEARCH MOVIE")
        print("=" * 50)

        search_url = (
            "https://www.themoviedb.org/search/movie"
        )

        params = {
            "query": self.movie_name
        }

        response = self.get_page(
            search_url,
            params=params
        )

        if response is None:

            print(
                "TMDB SEARCH FAILED"
            )

            return False


        # ==================================================
        # PARSE SEARCH PAGE
        # ==================================================

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )


        # ==================================================
        # FIND ALL MOVIE LINKS
        # ==================================================

        links = soup.find_all(
            "a",
            href=True
        )

        print(
            "TOTAL LINKS:",
            len(links)
        )


        target = self.normalize(
            self.movie_name
        )

        found = None


        # ==================================================
        # CHECK LINKS
        # ==================================================

        for link in links:

            href = link.get(
                "href"
            )

            if not href:
                continue


            # Only movie links
            if not href.startswith(
                "/movie/"
            ):
                continue


            text = link.get_text(
                " ",
                strip=True
            )

            if not text:
                continue


            normalized_text = self.normalize(
                text
            )


            # Get parent card text
            parent = link.find_parent(
                class_=lambda x: x and (
                    "card" in str(x).lower()
                )
            )


            if parent:

                card_text = parent.get_text(
                    " ",
                    strip=True
                )

            else:

                card_text = text


            # ==================================================
            # YEAR CHECK
            # ==================================================

            year_found = (
                self.year in card_text
            )


            # ==================================================
            # TITLE CHECK
            # ==================================================

            title_found = (
                target in normalized_text
                or normalized_text in target
            )


            print(
                "CHECK:",
                text,
                "| YEAR:",
                year_found,
                "| HREF:",
                href
            )


            if title_found and year_found:

                found = href

                print(
                    "\nMOVIE FOUND:"
                )

                print(
                    "TITLE:",
                    text
                )

                print(
                    "YEAR:",
                    self.year
                )

                print(
                    "HREF:",
                    href
                )

                break


        # ==================================================
        # FALLBACK SEARCH
        # ==================================================

        if not found:

            print(
                "\nExact match not found."
            )

            print(
                "Trying relaxed movie search..."
            )


            for link in links:

                href = link.get(
                    "href"
                )

                if not href:
                    continue


                if not href.startswith(
                    "/movie/"
                ):
                    continue


                text = link.get_text(
                    " ",
                    strip=True
                )

                normalized_text = self.normalize(
                    text
                )


                if (
                    target in normalized_text
                    or normalized_text in target
                ):

                    found = href

                    print(
                        "RELAXED MATCH:",
                        text
                    )

                    break


        # ==================================================
        # MOVIE NOT FOUND
        # ==================================================

        if not found:

            print(
                "\nMOVIE NOT FOUND"
            )

            return False


        # ==================================================
        # FULL URL
        # ==================================================

        if found.startswith("/"):

            self.movie_url = (
                "https://www.themoviedb.org"
                + found
            )

        else:

            self.movie_url = found


        print(
            "\nMOVIE URL:",
            self.movie_url
        )


        # ==================================================
        # OPEN MOVIE PAGE
        # ==================================================

        movie_response = self.get_page(
            self.movie_url
        )


        if movie_response is None:

            print(
                "MOVIE PAGE FAILED"
            )

            return False


        # ==================================================
        # EXTRACT IMAGES
        # ==================================================

        self.extract_images(
            movie_response.text
        )


        print(
            "\n" + "=" * 50
        )

        print(
            "EXTRACTED"
        )

        print(
            "POSTER:",
            self.poster
        )

        print(
            "BACKGROUND:",
            self.bg_poster
        )

        print(
            "=" * 50
        )


        return bool(
            self.poster or self.bg_poster
        )


    # ==================================================
    # IMAGE EXTRACTION
    # ==================================================

    def extract_images(self, html):

        soup = BeautifulSoup(
            html,
            "html.parser"
        )


        # ==================================================
        # NORMAL POSTER
        # ==================================================

        poster = soup.find(
            "img",
            class_=lambda x: x and (
                "poster" in x
            )
        )


        if poster:

            print(
                "\nPOSTER TAG FOUND"
            )


            srcset = poster.get(
                "srcset"
            )


            if srcset:

                print(
                    "SRCSET FOUND"
                )

                parts = srcset.split(",")


                for part in parts:

                    part = part.strip()

                    print(
                        "SRCSET:",
                        part
                    )


                    if part.endswith(
                        "2x"
                    ):

                        self.poster = (
                            part.rsplit(
                                " ",
                                1
                            )[0]
                        )

                        break


            # ==================================================
            # FALLBACK SRC
            # ==================================================

            if not self.poster:

                src = poster.get(
                    "src"
                )

                if src:

                    self.poster = src


        # ==================================================
        # BACKGROUND IMAGE
        # ==================================================

        print(
            "\nSEARCHING BACKGROUND..."
        )


        # This catches:
        #
        # background-image: url('https://...')
        #

        pattern = re.compile(
            r"""
            background-image
            \s*:\s*
            url
            \s*\(
            \s*
            ['"]?
            (https://media\.themoviedb\.org/t/p/[^'"\)\s]+)
            ['"]?
            \s*
            \)
            """,
            re.IGNORECASE |
            re.VERBOSE
        )


        matches = pattern.findall(
            html
        )


        print(
            "BACKGROUND MATCHES:",
            len(matches)
        )


        # ==================================================
        # SELECT LARGE BACKGROUND
        # ==================================================

        for url in matches:

            print(
                "BG CANDIDATE:",
                url
            )


            if (
                "w1920" in url
                or "w1280" in url
                or "multi_faces" in url
            ):

                self.bg_poster = (
                    url.strip()
                )

                break


        # ==================================================
        # FALLBACK
        # ==================================================

        if not self.bg_poster:

            for url in matches:

                self.bg_poster = (
                    url.strip()
                )

                break


        # ==================================================
        # EXTRA BACKGROUND SEARCH
        # ==================================================

        if not self.bg_poster:

            print(
                "Trying direct TMDB image search..."
            )


            image_urls = re.findall(
                r"https://media\.themoviedb\.org/t/p/[^\"'\s\)]+",
                html,
                re.IGNORECASE
            )


            for url in image_urls:

                url = url.strip()


                if (
                    "w1920" in url
                    or "w1280" in url
                    or "multi_faces" in url
                ):

                    self.bg_poster = url

                    break


    # ==================================================
    # GET POSTER
    # ==================================================

    def get_poster(self):

        return self.poster


    # ==================================================
    # GET BACKGROUND
    # ==================================================

    def get_background(self):

        return self.bg_poster


# ======================================================
# TEST
# ======================================================

if __name__ == "__main__":

    movie = ExtractBG  

    """(
        "with love",
        2026
    )

    result = movie.stage_one()


    print("\n")
    print("=" * 50)
    print("FINAL RESULT")
    print("=" * 50)

    print(
        "SUCCESS:",
        result
    )

    print(
        "POSTER:",
        movie.poster
    )

    print(
        "BACKGROUND:",
        movie.bg_poster
    )

    print(
        "MOVIE URL:",
        movie.movie_url
    )

    print(
        "=" * 50
    )"""