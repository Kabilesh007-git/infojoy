import requests
from bs4 import BeautifulSoup
import time

from dow_process import down
from extract import ExtractBG


class request_generator:

    def __init__(self, movie_name, movie_quality):

        self.movie_name = str(movie_name).strip()
        self.quality = str(movie_quality).strip()

        self.base_url = "https://moviesdatamil.me/"

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/142.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        })

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

        self.dow_pc = None

        self.start_time = None


    # --------------------------------------------------
    # STAGE 1
    # --------------------------------------------------

    def stage1(self):

        print("\n" + "=" * 50)
        print("STAGE 1")
        print("=" * 50)

        self.start_time = time.time()

        try:

            self.dow_pc = down(
                self.movie_name,
                self.base_url
            )

            self.dow_pc.start()

        except Exception as e:

            print("DOWN ERROR:", e)
            return False


        if not self.dow_pc.result_url:

            print("Movie URL not found")
            return False


        print("Movie URL:")
        print(self.dow_pc.result_url)


        try:

            data = self.session.get(
                self.dow_pc.result_url,
                timeout=15
            )

            data.raise_for_status()

        except requests.RequestException as e:

            print("REQUEST ERROR:", e)
            return False


        soup = BeautifulSoup(
            data.content,
            "lxml"
        )


        # Find first quality/folder link
        extract = soup.select_one(
            "div.f a[href]"
        )


        if not extract:

            extract = soup.select_one(
                "div.folder div.left a[href]"
            )


        if not extract:

            print("First link not found")
            return False


        self.link1 = extract.get("href")


        print("LINK 1:")
        print(self.link1)


        # ----------------------------------------------
        # MOVIE DETAILS
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


        return self.stage2(
            self.link1
        )


    # --------------------------------------------------
    # STAGE 2
    # --------------------------------------------------

    def stage2(self, link1):

        print("\n" + "=" * 50)
        print("STAGE 2")
        print("=" * 50)


        if not link1:
            print("LINK 1 is empty")
            return False


        if link1.startswith("http"):

            url = link1

        else:

            url = (
                self.base_url
                + link1.lstrip("/")
            )


        print("URL:")
        print(url)


        try:

            data = self.session.get(
                url,
                timeout=15
            )

            data.raise_for_status()

        except requests.RequestException as e:

            print("REQUEST ERROR:", e)
            return False


        soup = BeautifulSoup(
            data.text,
            "lxml"
        )


        self.links = soup.select(
            "div.f a[href]"
        )


        if not self.links:

            self.links = soup.select(
                "div.folder div.left a[href]"
            )


        self.count = []


        for item in self.links:

            text = item.get_text(
                " ",
                strip=True
            )


            if text:

                self.count.append(text)


        print("\nAVAILABLE QUALITIES:")

        for quality in self.count:

            print(
                " -",
                quality
            )


        return True


    # --------------------------------------------------
    # SELECT QUALITY
    # --------------------------------------------------

    def continue_process(self):

        print("\n" + "=" * 50)
        print("QUALITY SELECTION")
        print("=" * 50)


        wanted_quality = (
            str(self.quality)
            .lower()
            .strip()
        )


        print("Wanted quality:")
        print(wanted_quality)


        if not self.links:

            print("No quality links available")
            return False


        self.link2 = None


        for div in self.links:

            href = div.get(
                "href",
                ""
            )

            text = div.get_text(
                " ",
                strip=True
            ).lower()


            print("\nChecking:")
            print("TEXT :", text)
            print("HREF :", href)


            if (
                wanted_quality in text
                or wanted_quality in href.lower()
            ):

                self.link2 = href

                print(
                    "QUALITY FOUND:",
                    self.link2
                )

                break


        if self.link2 is None:

            print(
                "Quality not found:",
                self.quality
            )

            return False


        # --------------------------------------------------
        # GET POSTER + BACKGROUND
        # --------------------------------------------------

        try:

            if self.dow_pc and self.dow_pc.year:

                process_bg = ExtractBG(
                    self.movie_name,
                    self.dow_pc.year
                )

                result = process_bg.stage_one()


                if result:

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

                else:

                    print(
                        "TMDB poster extraction failed"
                    )

        except Exception as e:

            print(
                "POSTER ERROR:",
                e
            )


        # --------------------------------------------------
        # STAGE 3
        # --------------------------------------------------

        result = self.stage3(
            self.link2
        )


        print("\n" + "=" * 50)
        print("FINAL RESULT")
        print("=" * 50)

        print("Movie       :", self.movie_name)
        print("Quality     :", self.quality)
        print("Year        :", getattr(
            self.dow_pc,
            "year",
            None
        ))

        print("Poster      :", self.poster)
        print("Background  :", self.bg_poster)

        print("Final Link  :", self.f_link)

        print("Details     :", self.details)

        print("=" * 50)


        return result


    # --------------------------------------------------
    # STAGE 3
    # --------------------------------------------------

    def stage3(self, link2):

        print("\n" + "=" * 50)
        print("STAGE 3")
        print("=" * 50)


        if not link2:

            print("LINK 2 is empty")
            return False


        if link2.startswith("http"):

            url = link2

        else:

            url = (
                self.base_url
                + link2.lstrip("/")
            )


        print("URL:")
        print(url)


        try:

            data = self.session.get(
                url,
                timeout=15
            )

            data.raise_for_status()

        except requests.RequestException as e:

            print("REQUEST ERROR:", e)
            return False


        soup = BeautifulSoup(
            data.text,
            "lxml"
        )


        # --------------------------------------------------
        # FIND NEXT DOWNLOAD LINK
        # --------------------------------------------------

        dd_link = soup.select_one(
            "div.left a[href]"
        )


        if not dd_link:

            dd_link = soup.select_one(
                "div.dlink a[href]"
            )


        if not dd_link:

            print("LINK 3 not found")
            return False


        self.link3 = dd_link.get(
            "href"
        )


        print("LINK 3:")
        print(self.link3)


        # --------------------------------------------------
        # EXTRA DETAILS
        # --------------------------------------------------

        items = soup.select(
            "div.left li"
        )


        for item in items:

            text = item.get_text(
                " ",
                strip=True
            )


            if (
                ":" in text
                and "-" not in text
            ):

                key, value = text.split(
                    ":",
                    1
                )


                self.details[
                    key.strip()
                ] = value.strip()


        # --------------------------------------------------
        # NEXT STAGE
        # --------------------------------------------------

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


            return self.stage5(
                self.link3
            )


        return self.stage4(
            self.link3
        )


    # --------------------------------------------------
    # STAGE 4
    # --------------------------------------------------

    def stage4(self, link3):

        print("\n" + "=" * 50)
        print("STAGE 4")
        print("=" * 50)


        if not link3:

            print("LINK 3 is empty")
            return False


        if link3.startswith("http"):

            url = link3

        else:

            url = (
                self.base_url
                + link3.lstrip("/")
            )


        print("URL:")
        print(url)


        try:

            data = self.session.get(
                url,
                timeout=15
            )

            data.raise_for_status()

        except requests.RequestException as e:

            print("REQUEST ERROR:", e)
            return False


        soup = BeautifulSoup(
            data.text,
            "lxml"
        )


        # --------------------------------------------------
        # DETAILS
        # --------------------------------------------------

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


                value = strong.next_sibling


                if value:

                    value = str(
                        value
                    ).strip()


                    self.details[key] = value


        # --------------------------------------------------
        # DOWNLOAD LINK
        # --------------------------------------------------

        dlink = soup.select_one(
            "div.download a[href]"
        )


        if not dlink:

            dlink = soup.select_one(
                "div.dlink a[href]"
            )


        if not dlink:

            print("LINK 4 not found")
            return False


        self.link4 = dlink.get(
            "href"
        )


        print("LINK 4:")
        print(self.link4)


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


        return self.stage5(
            self.link4
        )


    # --------------------------------------------------
    # STAGE 5
    # --------------------------------------------------

    def stage5(self, link4):

        print("\n" + "=" * 50)
        print("STAGE 5")
        print("=" * 50)


        if not link4:

            print("LINK 4 is empty")
            return False


        print("URL:")
        print(link4)


        try:

            data = self.session.get(
                link4,
                timeout=15
            )

            data.raise_for_status()

        except requests.RequestException as e:

            print("REQUEST ERROR:", e)
            return False


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

            print("FINAL LINK NOT FOUND")
            return False


        self.f_link = d_link2.get(
            "href"
        )


        print("\nFINAL LINK:")
        print(self.f_link)


        elapsed = time.time() - self.start_time


        print(
            "\nTime:",
            round(elapsed, 2),
            "seconds"
        )


        return True


    # --------------------------------------------------
    # DOWNLOAD PROCESS
    # --------------------------------------------------

    def downdload_process(self, link5):

        if not link5:

            print("Download URL is empty")
            return False


        print(
            "Download URL:",
            link5
        )


        # Put your MovieDownloader here.
        # Do not download large movie files directly
        # through a Vercel serverless function.


        return True


# Alias
rg = request_generator


#