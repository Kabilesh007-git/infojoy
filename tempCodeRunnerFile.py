import asyncio
import aiohttp
import datetime
import time
import re


class RequestGenerator:

    def __init__(self, movie_name, url):

        # ----------------------------------------
        # MOVIE NAME
        # ----------------------------------------

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

        # ----------------------------------------
        # BASE URL
        # ----------------------------------------

        self.url = url

        # ----------------------------------------
        # RESULTS
        # ----------------------------------------

        self.result = None

        self.result_url = None

        self.result_url1 = None
        self.result_url2 = None
        self.result_url3 = None

        self.year = None

        # All matching pages
        self.results = []


    # ==================================================
    # LAST UPDATED
    # ==================================================

    def get_last_updated(self, html):

        # Convert HTML to normal searchable text
        text = re.sub(
            r"<[^>]+>",
            " ",
            html
        )

        # Decode common HTML spaces
        text = text.replace(
            "&nbsp;",
            " "
        )

        # Remove extra spaces
        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        # ----------------------------------------
        # DATE PATTERNS
        # ----------------------------------------

        patterns = [

            # 27/08/2026
            (
                r"last\s*updated\s*[:\-]?\s*"
                r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
            ),

            # 27-08-2026
            (
                r"updated\s*[:\-]?\s*"
                r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
            ),

            # 27 August 2026
            (
                r"last\s*updated\s*[:\-]?\s*"
                r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})"
            ),

            # August 27, 2026
            (
                r"last\s*updated\s*[:\-]?\s*"
                r"([A-Za-z]+\s+\d{1,2},\s*\d{4})"
            ),

            # 27 August 2026
            (
                r"updated\s*[:\-]?\s*"
                r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})"
            ),

            # August 27, 2026
            (
                r"updated\s*[:\-]?\s*"
                r"([A-Za-z]+\s+\d{1,2},\s*\d{4})"
            ),
        ]

        # ----------------------------------------
        # DATE FORMATS
        # ----------------------------------------

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

        # ----------------------------------------
        # SEARCH DATE
        # ----------------------------------------

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if not match:
                continue

            date_text = match.group(1).strip()

            for date_format in formats:

                try:

                    return datetime.datetime.strptime(
                        date_text,
                        date_format
                    )

                except ValueError:
                    pass

        return None


    # ==================================================
    # CHECK ONE URL
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

                # ----------------------------------------
                # TIMEOUT
                # ----------------------------------------

                timeout = aiohttp.ClientTimeout(
                    total=3,
                    connect=1,
                    sock_read=2
                )

                # ----------------------------------------
                # REQUEST
                # ----------------------------------------

                async with session.get(
                    url,
                    timeout=timeout,
                    allow_redirects=True
                ) as response:

                    # ----------------------------------------
                    # STATUS
                    # ----------------------------------------

                    if response.status != 200:
                        return None

                    # ----------------------------------------
                    # HTML
                    # ----------------------------------------

                    html = await response.text(
                        errors="ignore"
                    )

                    # ----------------------------------------
                    # FAST TITLE EXTRACTION
                    # ----------------------------------------

                    title_match = re.search(
                        r"<title[^>]*>(.*?)</title>",
                        html,
                        re.IGNORECASE |
                        re.DOTALL
                    )

                    if not title_match:
                        return None

                    title = title_match.group(1)

                    # Remove HTML tags
                    title = re.sub(
                        r"<[^>]+>",
                        " ",
                        title
                    )

                    # Normalize
                    title = re.sub(
                        r"\s+",
                        " ",
                        title
                    ).strip().lower()

                    # ----------------------------------------
                    # MOVIE NAME CHECK
                    # ----------------------------------------

                    if self.search_name not in title:
                        return None

                    # ----------------------------------------
                    # LAST UPDATED
                    # ----------------------------------------

                    last_updated = (
                        self.get_last_updated(
                            html
                        )
                    )

                    print(
                        f"FOUND [{year}]: {url}"
                    )

                    print(
                        f"UPDATED: {last_updated}"
                    )

                    # ----------------------------------------
                    # RETURN
                    # ----------------------------------------

                    return {
                        "url": url,
                        "year": year,
                        "updated": last_updated
                    }

            # ----------------------------------------
            # REQUEST CANCELLED
            # ----------------------------------------

            except asyncio.CancelledError:

                raise

            # ----------------------------------------
            # TIMEOUT / CONNECTION ERROR
            # ----------------------------------------

            except (
                asyncio.TimeoutError,
                aiohttp.ClientError
            ):

                return None

            # ----------------------------------------
            # OTHER ERROR
            # ----------------------------------------

            except Exception:

                return None

        return None


    # ==================================================
    # SEARCH
    # ==================================================

    async def search(self):

        start_time = time.perf_counter()

        # ----------------------------------------
        # URL PATTERNS
        # ----------------------------------------

        tails = [

            "-movie/",

            "-tamil-movie/",

            "-tamil-movie-moviesda/"
        ]

        # ----------------------------------------
        # CURRENT YEAR
        # ----------------------------------------

        current_year = datetime.datetime.now().year

        # ----------------------------------------
        # CREATE ALL URLS
        # ----------------------------------------

        urls = []

        for year in range(
            current_year,
            1999,
            -1
        ):

            for tail in tails:

                full_url = (
                    f"{self.url}"
                    f"{self.movie_name}-"
                    f"{year}"
                    f"{tail}"
                )

                urls.append(
                    (
                        full_url,
                        year
                    )
                )

        print()
        print(
            "TOTAL URLS:",
            len(urls)
        )

        # ----------------------------------------
        # CONCURRENCY
        # ----------------------------------------

        MAX_CONNECTIONS = 50

        semaphore = asyncio.Semaphore(
            MAX_CONNECTIONS
        )

        connector = aiohttp.TCPConnector(

            limit=MAX_CONNECTIONS,

            limit_per_host=MAX_CONNECTIONS,

            ttl_dns_cache=300,

            enable_cleanup_closed=True
        )

        # ----------------------------------------
        # HEADERS
        # ----------------------------------------

        headers = {

            "User-Agent":
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/140.0 Safari/537.36",

            "Accept":
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8",

            "Accept-Language":
                "en-US,en;q=0.9"
        }

        # ----------------------------------------
        # SESSION
        # ----------------------------------------

        async with aiohttp.ClientSession(

            connector=connector,

            headers=headers

        ) as session:

            # ----------------------------------------
            # CREATE TASKS
            # ----------------------------------------

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

            # ----------------------------------------
            # PROCESS RESULTS
            # ----------------------------------------

            for task in asyncio.as_completed(
                tasks
            ):

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

            # ----------------------------------------
            # WAIT FOR ALL TASKS
            # ----------------------------------------

            await asyncio.gather(

                *tasks,

                return_exceptions=True
            )

        # ==================================================
        # NO RESULTS
        # ==================================================

        if not self.results:

            print()
            print(
                "=" * 60
            )

            print(
                "MOVIE NOT FOUND"
            )

            print(
                "=" * 60
            )

            elapsed = (
                time.perf_counter()
                - start_time
            )

            print(
                f"SEARCH TIME: {elapsed:.2f} seconds"
            )

            return None

        # ==================================================
        # SHOW ALL FOUND RESULTS
        # ==================================================

        print()
        print(
            "=" * 60
        )

        print(
            "ALL MATCHING PAGES"
        )

        print(
            "=" * 60
        )

        for item in self.results:

            print(
                "YEAR    :",
                item["year"]
            )

            print(
                "URL     :",
                item["url"]
            )

            print(
                "UPDATED :",
                item["updated"]
            )

            print(
                "-" * 60
            )

        # ==================================================
        # SORT BY LAST UPDATED
        # ==================================================

        dated_results = [

            item

            for item in self.results

            if item["updated"] is not None
        ]

        # ----------------------------------------
        # IF UPDATE DATE EXISTS
        # ----------------------------------------

        if dated_results:

            dated_results.sort(

                key=lambda item:
                    item["updated"],

                reverse=True
            )

            sorted_results = dated_results

        # ----------------------------------------
        # IF NO UPDATE DATE
        # ----------------------------------------

        else:

            self.results.sort(

                key=lambda item:
                    item["year"],

                reverse=True
            )

            sorted_results = self.results

        # ==================================================
        # STORE RESULT URL 1
        # ==================================================

        if len(sorted_results) >= 1:

            self.result_url1 = (
                sorted_results[0]["url"]
            )

        # ==================================================
        # STORE RESULT URL 2
        # ==================================================

        if len(sorted_results) >= 2:

            self.result_url2 = (
                sorted_results[1]["url"]
            )

        # ==================================================
        # STORE RESULT URL 3
        # ==================================================

        if len(sorted_results) >= 3:

            self.result_url3 = (
                sorted_results[2]["url"]
            )

        # ==================================================
        # NEWEST / LATEST UPDATED RESULT
        # ==================================================

        selected = sorted_results[0]

        self.result_url = (
            selected["url"]
        )

        self.year = (
            selected["year"]
        )

        self.result = (
            self.result_url
        )

        # ==================================================
        # FINAL OUTPUT
        # ==================================================

        print()
        print(
            "=" * 60
        )

        print(
            "FINAL RESULT"
        )

        print(
            "=" * 60
        )

        print(
            "RESULT URL :",
            self.result_url
        )

        print(
            "RESULT URL1:",
            self.result_url1
        )

        print(
            "RESULT URL2:",
            self.result_url2
        )

        print(
            "RESULT URL3:",
            self.result_url3
        )

        print(
            "YEAR       :",
            self.year
        )

        print(
            "UPDATED    :",
            selected["updated"]
        )

        # ==================================================
        # SEARCH TIME
        # ==================================================

        elapsed = (
            time.perf_counter()
            - start_time
        )

        print()
        print(
            f"SEARCH TIME: {elapsed:.2f} seconds"
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


# ======================================================
# TEST
# ======================================================

if __name__ == "__main__":

    process = RequestGenerator(

        "Pudhupettai",

        "https://moviesdatamil.me/"
    )

    process.start()

    print()
    print(
        "=" * 60
    )

    print(
        "FINAL URL :",
        process.result_url
    )

    print(
        "URL 1     :",
        process.result_url1
    )

    print(
        "URL 2     :",
        process.result_url2
    )

    print(
        "URL 3     :",
        process.result_url3
    )

    print(
        "YEAR      :",
        process.year
    )