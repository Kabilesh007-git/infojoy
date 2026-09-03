import asyncio
import aiohttp
import datetime
import time
import re

from bs4 import BeautifulSoup


class RequestGenerator:

    def __init__(self, movie_name, url):

        self.movie_name = (
            str(movie_name)
            .lower()
            .strip()
            .replace(" ", "-")
        )

        self.search_name = (
            str(movie_name)
            .lower()
            .strip()
        )

        self.url = url

        self.result = None
        self.result_url = None
        self.result_url1 = None
        self.result_url2 = None
        self.result_url3 = None

        self.year = None

        self.results = []


    # ==================================================
    # EXTRACT LAST UPDATED DATE
    # ==================================================

    def get_last_updated(self, html):

        soup = BeautifulSoup(
            html,
            "lxml"
        )

        text = soup.get_text(
            " ",
            strip=True
        )

        # ----------------------------------------------
        # Try common "Last Updated" formats
        # ----------------------------------------------

        patterns = [

            r"last\s*updated\s*[:\-]?\s*"
            r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",

            r"last\s*updated\s*[:\-]?\s*"
            r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})",

            r"last\s*updated\s*[:\-]?\s*"
            r"([A-Za-z]+\s+\d{1,2},\s*\d{4})",

            r"updated\s*[:\-]?\s*"
            r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",

            r"updated\s*[:\-]?\s*"
            r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                date_text = match.group(1)

                formats = [
                    "%d-%m-%Y",
                    "%d/%m/%Y",
                    "%d-%m-%y",
                    "%d/%m/%y",
                    "%d %B %Y",
                    "%d %b %Y",
                    "%B %d, %Y",
                    "%b %d, %Y",
                ]

                for fmt in formats:

                    try:

                        return datetime.datetime.strptime(
                            date_text,
                            fmt
                        )

                    except ValueError:
                        pass

        return None


    # ==================================================
    # CHECK URL
    # ==================================================

    async def check_url(
        self,
        session,
        url,
        year,
        semaphore
    ):

        async with semaphore:

            try:

                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(
                        total=4
                    ),
                    allow_redirects=True
                ) as response:

                    if response.status != 200:
                        return None

                    html = await response.text(
                        errors="ignore"
                    )

                    soup = BeautifulSoup(
                        html,
                        "lxml"
                    )

                    title = soup.select_one(
                        "title"
                    )

                    if not title:
                        return None

                    title = title.get_text(
                        " ",
                        strip=True
                    ).lower()

                    if self.search_name not in title:
                        return None

                    # ----------------------------------
                    # GET LAST UPDATED
                    # ----------------------------------

                    last_updated = (
                        self.get_last_updated(
                            html
                        )
                    )

                    print()
                    print(
                        f"FOUND [{year}]"
                    )
                    print(
                        "URL     :", url
                    )
                    print(
                        "UPDATED :",
                        last_updated
                    )

                    return {
                        "url": url,
                        "year": year,
                        "updated": last_updated
                    }

            except asyncio.CancelledError:
                raise

            except (
                asyncio.TimeoutError,
                aiohttp.ClientError
            ):
                return None

            except Exception as e:

                print(
                    "ERROR:",
                    url,
                    e
                )

                return None

        return None


    # ==================================================
    # SEARCH
    # ==================================================

    async def search(self):

        start_time = time.perf_counter()

        tails = [
            "-movie/",
            "-tamil-movie/",
            "-tamil-movie-moviesda/"
        ]

        current_year = datetime.datetime.now().year

        urls = [
            (
                f"{self.url}"
                f"{self.movie_name}-"
                f"{year}"
                f"{tail}",
                year
            )

            for year in range(
                current_year,
                1999,
                -1
            )

            for tail in tails
        ]

        print(
            "TOTAL URLS:",
            len(urls)
        )

        semaphore = asyncio.Semaphore(20)

        connector = aiohttp.TCPConnector(
            limit=20,
            limit_per_host=20
        )

        headers = {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/140.0 Safari/537.36"
            )
        }

        async with aiohttp.ClientSession(
            connector=connector,
            headers=headers
        ) as session:

            tasks = [
                asyncio.create_task(
                    self.check_url(
                        session,
                        url,
                        year,
                        semaphore
                    )
                )

                for url, year in urls
            ]

            for task in asyncio.as_completed(tasks):

                try:

                    result = await task

                    if result:

                        self.results.append(
                            result
                        )

                except asyncio.CancelledError:

                    continue

                except Exception:

                    continue

            await asyncio.gather(
                *tasks,
                return_exceptions=True
            )

        # ==================================================
        # NO RESULTS
        # ==================================================

        if not self.results:

            print(
                "\nMOVIE NOT FOUND"
            )

            return None

        # ==================================================
        # SHOW ALL RESULTS
        # ==================================================

        print()
        print("=" * 60)
        print("FOUND PAGES")
        print("=" * 60)

        for item in self.results:

            print(
                "URL     :",
                item["url"]
            )

            print(
                "YEAR    :",
                item["year"]
            )

            print(
                "UPDATED :",
                item["updated"]
            )

            print("-" * 60)

        # ==================================================
        # SORT BY LAST UPDATED
        # ==================================================

        valid_dates = [
            item
            for item in self.results
            if item["updated"] is not None
        ]

        if valid_dates:

            valid_dates.sort(
                key=lambda x: x["updated"],
                reverse=True
            )

            selected = valid_dates[0]

        else:

            # If no update date exists,
            # fall back to newest movie year.

            self.results.sort(
                key=lambda x: x["year"],
                reverse=True
            )

            selected = self.results[0]

        # ==================================================
        # STORE URL VARIABLES
        # ==================================================

        sorted_results = valid_dates

        if not sorted_results:

            sorted_results = self.results

        self.result_url1 = (
            sorted_results[0]["url"]
            if len(sorted_results) >= 1
            else None
        )

        self.result_url2 = (
            sorted_results[1]["url"]
            if len(sorted_results) >= 2
            else None
        )

        self.result_url3 = (
            sorted_results[2]["url"]
            if len(sorted_results) >= 3
            else None
        )

        # ==================================================
        # FINAL RESULT = LATEST UPDATED PAGE
        # ==================================================

        self.result_url = selected["url"]

        self.year = selected["year"]

        self.result = self.result_url

        # ==================================================
        # PRINT FINAL RESULT
        # ==================================================

        print()
        print("=" * 60)
        print("LATEST UPDATED RESULT")
        print("=" * 60)

        print(
            "RESULT URL:",
            self.result_url
        )

        print(
            "YEAR:",
            self.year
        )

        print(
            "UPDATED:",
            selected["updated"]
        )

        print()
        print("RESULT URL 1:", self.result_url1)
        print("RESULT URL 2:", self.result_url2)
        print("RESULT URL 3:", self.result_url3)

        elapsed = (
            time.perf_counter()
            - start_time
        )

        print(
            f"\nSEARCH TIME: {elapsed:.2f} seconds"
        )

        return self.result


    # ==================================================
    # START
    # ==================================================

    def start(self):

        self.result = asyncio.run(
            self.search()
        )

        return self.result


# ======================================================
# ALIASES
# ======================================================

down = RequestGenerator
rg = RequestGenerator