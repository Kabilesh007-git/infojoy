import requests
from bs4 import BeautifulSoup
import time
import lxml

from dow_process import *
from extract import *


class request_generator:

    def __init__(self, movie_name, movie_quality):

        self.movie_name = movie_name
        self.quality = str(movie_quality)

        self.base_url = "https://moviesdatamil.me/"
        self.session = requests.Session()

        # Default values
        self.link1 = None
        self.link2 = None
        self.link3 = None
        self.link4 = None
        self.f_link = None

        self.poster = None
        self.bg_poster = None

        self.details = {}
        self.links = []
        self.count = []

    # --------------------------------------------------
    # STAGE 1
    # --------------------------------------------------

    def stage1(self):

        self.start_time = time.time()

        self.dow_pc = down(
            self.movie_name,
            self.base_url
        )

        self.dow_pc.start()

        if not self.dow_pc.result_url:
            return

        data = self.session.get(
            self.dow_pc.result_url,
            timeout=15
        )

        data.raise_for_status()

        soup = BeautifulSoup(
            data.content,
            "lxml"
        )

        # ----------------------------------------------
        # Get first movie link
        # ----------------------------------------------

        extract = soup.select_one(
            "div.f a[href]"
        )

        if not extract:

            extract = soup.select_one(
                "div.folder div.left a[href]"
            )

        if not extract:
            return

        self.link1 = extract.get("href")

        # ----------------------------------------------
        # Movie details
        # ----------------------------------------------

        items = soup.select(
            "ul.movie-info li"
        )

        for item in items:

            key = item.select_one("strong")
            value = item.select_one("span")

            if key and value:

                key_text = key.get_text(
                    " ",
                    strip=True
                ).strip(":")

                value_text = value.get_text(
                    " ",
                    strip=True
                )

                self.details[key_text] = value_text

        # ----------------------------------------------
        # Go to stage 2
        # ----------------------------------------------

        self.stage2(self.link1)

    # --------------------------------------------------
    # STAGE 2
    # Get available qualities
    # --------------------------------------------------

    def stage2(self, link1):

        # Prevent duplicate https://
        if link1.startswith("http"):

            url = link1

        else:

            url = self.base_url + link1.lstrip("/")

        data = self.session.get(
            url,
            timeout=15
        )

        data.raise_for_status()

        soup = BeautifulSoup(
            data.text,
            "lxml"
        )

        # ----------------------------------------------
        # Find quality links
        # ----------------------------------------------

        self.links = soup.select(
            "div.f a[href]"
        )

        if not self.links:

            self.links = soup.select(
                "div.folder div.left a[href]"
            )

        # ----------------------------------------------
        # Save quality names
        # ----------------------------------------------

        self.count = []

        for item in self.links:

            text = item.get_text(
                " ",
                strip=True
            )

            if text:
                self.count.append(text)

    # --------------------------------------------------
    # CONTINUE PROCESS
    # --------------------------------------------------

    def continue_process(self):

        self.link2 = None

        wanted_quality = str(
            self.quality
        ).lower().strip()

        # ----------------------------------------------
        # Make sure links exist
        # ----------------------------------------------

        if not self.links:

            return

        # ----------------------------------------------
        # Find selected quality
        # ----------------------------------------------

        for div in self.links:

            href = div.get(
                "href",
                ""
            )

            text = div.get_text(
                " ",
                strip=True
            ).lower()

            if (
                wanted_quality in text
                or
                wanted_quality in href.lower()
            ):

                self.link2 = href
                break

        # ----------------------------------------------
        # Quality not found
        # ----------------------------------------------

        if self.link2 is None:

            return

        # ----------------------------------------------
        # Get poster + background
        # ----------------------------------------------

        process_bg = obj(
            self.movie_name,
            self.dow_pc.year
        )

        process_bg.first_stage()

        self.poster = getattr(
            process_bg,
            "poster",
            None
        )

        self.bg_poster = getattr(
            process_bg,
            "bg_poster",
            None
        )

        # ----------------------------------------------
        # Stage 3
        # ----------------------------------------------

        self.stage3(
            self.link2
        )

        # ----------------------------------------------
        # ONLY FINAL OUTPUT
        # ----------------------------------------------

        print("--------------------------------")
        print("Final Link:", self.f_link)
        print("Poster:", self.poster)
        print("Background:", self.bg_poster)
        print("Details:", self.details)
        print("--------------------------------")

    # --------------------------------------------------
    # STAGE 3
    # --------------------------------------------------

    def stage3(self, link2):

        if link2.startswith("http"):

            url = link2

        else:

            url = self.base_url + link2.lstrip("/")

        data = self.session.get(
            url,
            timeout=15
        )

        data.raise_for_status()

        soup = BeautifulSoup(
            data.text,
            "lxml"
        )

        # ----------------------------------------------
        # Find download link
        # ----------------------------------------------

        dd_link = soup.select_one(
            "div.left a[href]"
        )

        if not dd_link:

            dd_link = soup.select_one(
                "div.dlink a[href]"
            )

        if not dd_link:
            return

        self.link3 = dd_link.get(
            "href"
        )

        # ----------------------------------------------
        # Extra details
        # ----------------------------------------------

        items = soup.select(
            "div.left li"
        )

        for item in items:

            text = item.get_text(
                " ",
                strip=True
            )

            if ":" in text and "-" not in text:

                key, value = text.split(
                    ":",
                    1
                )

                self.details[
                    key.strip()
                ] = value.strip()

        # ----------------------------------------------
        # Decide next stage
        # ----------------------------------------------

        if self.link3.startswith("http"):

            self.link3 = (
                self.link3
                .replace(
                    "/download.moviespage.xyz/",
                    "/movies.downloadpage.xyz/"
                )
                .replace(
                    "/file/",
                    "/page/"
                )
            )

            self.stage5(
                self.link3
            )

        else:

            self.stage4(
                self.link3
            )

    # --------------------------------------------------
    # STAGE 4
    # --------------------------------------------------

    def stage4(self, link3):

        # Handle relative URL correctly
        if link3.startswith("http"):

            url = link3

        else:

            url = (
                self.base_url
                + link3.lstrip("/")
            )

        data = self.session.get(
            url,
            timeout=15
        )

        data.raise_for_status()

        soup = BeautifulSoup(
            data.text,
            "lxml"
        )

        # ----------------------------------------------
        # Get details
        # ----------------------------------------------

        items = soup.select(
            "div.details"
        )

        for item in items:

            strong = item.select_one(
                "strong"
            )

            if strong:

                key = strong.get_text(
                    strip=True
                ).rstrip(":")

                # Get text after <strong>
                value = strong.next_sibling

                if value:

                    value = str(
                        value
                    ).strip()

                    self.details[key] = value

        # ----------------------------------------------
        # Download link
        # ----------------------------------------------

        dlink = soup.select_one(
            "div.download a[href]"
        )

        if not dlink:

            dlink = soup.select_one(
                "div.dlink a[href]"
            )

        if not dlink:
            return

        self.link4 = dlink.get(
            "href"
        )

        # ----------------------------------------------
        # Convert download URL
        # ----------------------------------------------

        self.link4 = (
            self.link4
            .replace(
                "/download.moviespage.xyz/",
                "/movies.downloadpage.xyz/"
            )
            .replace(
                "/file/",
                "/page/"
            )
        )

        self.stage5(
            self.link4
        )

    # --------------------------------------------------
    # STAGE 5
    # --------------------------------------------------

    def stage5(self, link4):

        data = self.session.get(
            link4,
            timeout=15
        )

        data.raise_for_status()

        soup = BeautifulSoup(
            data.text,
            "lxml"
        )

        d_link2 = soup.select_one(
            "div.dlink a[href]"
        )

        if not d_link2:

            d_link2 = soup.select_one(
                "div.download a[href]"
            )

        if not d_link2:
            return

        self.f_link = d_link2.get(
            "href"
        )

    # --------------------------------------------------
    # DOWNLOAD PROCESS
    # --------------------------------------------------

    def downdload_process(self, link5):

        url = link5

        # Your download code here
        pass


# ======================================================
# TEST
# ======================================================



rg = request_generator


"""(
        "kaththi",
        "360"
    )

    rg.stage1()

    rg.continue_process()"""