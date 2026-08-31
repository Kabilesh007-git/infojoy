import asyncio
import aiohttp
import datetime
import time
from bs4 import BeautifulSoup


class RequestGenerator:

    def __init__(self, movie_name, url):

        self.movie_name = str(movie_name).lower().replace(" ", "-")
        self.search_name = str(movie_name).lower()
        self.url = url

        self.result = None
        self.year = None


    async def check_url(self, session, url, year, semaphore):

        async with semaphore:

            try:

                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=4)
                ) as response:

                    if response.status != 200:
                        return None

                    html = await response.text()

                    soup = BeautifulSoup(html, "lxml")

                    title = soup.select_one("title")

                    if title:

                        title = title.get_text(
                            " ",
                            strip=True
                        ).lower()

                        if self.search_name in title:

                            # Return BOTH URL and year
                            return url, year

            except Exception:

                return None

        return None


    async def search(self):

        tails = [
            "-tamil-movie/",
            "-movie/",
            "-tamil-movie-moviesda/"
        ]

        current_year = datetime.datetime.now().year


        # Store URL and year together
        urls = [

            (
                f"{self.url}"
                f"{self.movie_name}-{year}{tail}",
                year
            )

            for year in range(current_year, 1999, -1)

            for tail in tails
        ]


        semaphore = asyncio.Semaphore(20)


        connector = aiohttp.TCPConnector(
            limit=20,
            limit_per_host=20
        )


        headers = {
            "User-Agent": "Mozilla/5.0"
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

                result = await task


                if result:

                    # result = (url, year)
                    url, year = result

                    #print("FOUND:")
                    #print("URL :", url)
                    #print("YEAR:", year)


                    # Cancel remaining requests
                    for t in tasks:

                        if not t.done():
                            t.cancel()


                    return result


        return None


    def start(self):

        start_time = time.time()


        self.result = asyncio.run(
            self.search()
        )


        if self.result:

            # Get URL and year
            self.result_url, self.year = self.result



        else:

            print("Movie not found")


        #print(f"Time: {time.time() - start_time:.2f} seconds")


        return self.result


# ---------------------------------------------------
# TEST
# ---------------------------------------------------

down = RequestGenerator




        