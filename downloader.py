import os
import time
import requests


class MovieDownloader:

    def __init__(self, movie_data):

        self.data = movie_data

        # =====================================================
        # FINAL DOWNLOAD URL
        # =====================================================

        self.url = getattr(
            movie_data,
            "f_link",
            None
        )

        if self.url:
            self.url = str(self.url).strip()

        # =====================================================
        # MOVIE NAME
        # =====================================================

        self.movie_name = str(
            getattr(
                movie_data,
                "movie_name",
                "movie"
            )
        ).strip()

        if not self.movie_name:
            self.movie_name = "movie"

        # =====================================================
        # DETECT VERCEL / SERVERLESS
        # =====================================================

        self.is_vercel = (
            os.getenv("VERCEL") == "1"
            or os.getenv("VERCEL_ENV") is not None
        )

        # =====================================================
        # DOWNLOAD FOLDER
        # =====================================================

        if self.is_vercel:

            # Vercel's writable temporary directory
            self.folder = "/tmp/Infojoy"

        else:

            # Windows / local machine
            self.folder = os.path.join(
                os.path.expanduser("~"),
                "Downloads",
                "Infojoy"
            )

        os.makedirs(
            self.folder,
            exist_ok=True
        )

        # =====================================================
        # SAFE FILE NAME
        # =====================================================

        filename = self.movie_name

        invalid_chars = '<>:"/\\|?*'

        for char in invalid_chars:
            filename = filename.replace(
                char,
                "_"
            )

        filename = filename.strip()

        if not filename:
            filename = "movie"

        # =====================================================
        # FILE PATH
        # =====================================================

        self.filepath = os.path.join(
            self.folder,
            filename + ".mp4"
        )

    # =========================================================
    # FORMAT TIME
    # =========================================================

    def format_time(self, seconds):

        try:
            seconds = max(
                0,
                int(seconds)
            )
        except (TypeError, ValueError):
            seconds = 0

        hours = seconds // 3600

        minutes = (
            seconds % 3600
        ) // 60

        seconds = seconds % 60

        if hours:

            return (
                f"{hours:02d}:"
                f"{minutes:02d}:"
                f"{seconds:02d}"
            )

        return (
            f"{minutes:02d}:"
            f"{seconds:02d}"
        )

    # =========================================================
    # CREATE HEADERS
    # =========================================================

    def get_headers(self):

        return {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/142.0.0.0 "
                "Safari/537.36"
            ),

            "Accept": (
                "video/mp4,"
                "video/*,"
                "*/*"
            ),

            "Accept-Encoding": "identity",

            "Connection": "keep-alive"
        }

    # =========================================================
    # UPDATE STATUS
    # =========================================================

    def update_status(
        self,
        status,
        lock,
        **values
    ):

        with lock:

            for key, value in values.items():
                status[key] = value

    # =========================================================
    # DOWNLOAD
    # =========================================================

    def download(
        self,
        status,
        lock
    ):

        # =====================================================
        # CHECK URL
        # =====================================================

        if not self.url:

            self.update_status(
                status,
                lock,

                status="failed",
                running=False,
                completed=False,
                cancelled=False,

                error="Final download link not found",

                message=(
                    "Final download link not found"
                ),

                percentage=0,
                downloaded=0,
                total=0,
                speed=0,
                eta="00:00",
                elapsed="00:00"
            )

            raise Exception(
                "Final download link not found"
            )

        print()
        print("=" * 60)
        print("DOWNLOAD START")
        print("=" * 60)
        print("Movie :", self.movie_name)
        print("URL   :", self.url)
        print("File  :", self.filepath)
        print("Vercel:", self.is_vercel)
        print("=" * 60)

        response = None

        downloaded = 0
        total_size = 0

        start_time = time.time()

        # =====================================================
        # INITIAL STATUS
        # =====================================================

        self.update_status(
            status,
            lock,

            status="connecting",
            running=True,
            completed=False,
            cancelled=False,
            cancel_requested=False,

            movie_name=self.movie_name,

            percentage=0,
            downloaded=0,
            total=0,

            speed=0,
            eta="00:00",
            elapsed="00:00",

            filename=self.filepath,

            error=None,

            message=(
                f"Connecting to "
                f"{self.movie_name}..."
            )
        )

        # =====================================================
        # CONNECT
        # =====================================================

        try:

            print()
            print("Connecting to server...")

            response = requests.get(

                self.url,

                headers=self.get_headers(),

                stream=True,

                timeout=(
                    20,
                    120
                ),

                allow_redirects=True
            )

            print(
                "HTTP STATUS:",
                response.status_code
            )

            print(
                "FINAL URL:",
                response.url
            )

            print(
                "CONTENT TYPE:",
                response.headers.get(
                    "Content-Type"
                )
            )

            print(
                "CONTENT LENGTH:",
                response.headers.get(
                    "Content-Length"
                )
            )

            # =================================================
            # HTTP ERROR
            # =================================================

            response.raise_for_status()

        except requests.exceptions.Timeout as e:

            error = (
                "Download connection timed out: "
                f"{e}"
            )

            print()
            print("ERROR:", error)

            self.update_status(
                status,
                lock,

                status="failed",
                running=False,
                completed=False,
                error=error,

                message=error,

                percentage=0,
                downloaded=0,
                total=0,

                speed=0,
                eta="00:00"
            )

            raise Exception(error)

        except requests.exceptions.ConnectionError as e:

            error = (
                "Could not connect to download server: "
                f"{e}"
            )

            print()
            print("ERROR:", error)

            self.update_status(
                status,
                lock,

                status="failed",
                running=False,
                completed=False,
                error=error,

                message=error,

                percentage=0,
                downloaded=0,
                total=0,

                speed=0,
                eta="00:00"
            )

            raise Exception(error)

        except requests.exceptions.HTTPError as e:

            error = (
                "Download server returned HTTP "
                f"{response.status_code}: {e}"
            )

            print()
            print("ERROR:", error)

            self.update_status(
                status,
                lock,

                status="failed",
                running=False,
                completed=False,
                error=error,

                message=error,

                percentage=0,
                downloaded=0,
                total=0,

                speed=0,
                eta="00:00"
            )

            raise Exception(error)

        except requests.RequestException as e:

            error = (
                "Download connection error: "
                f"{repr(e)}"
            )

            print()
            print("ERROR:", error)

            self.update_status(
                status,
                lock,

                status="failed",
                running=False,
                completed=False,
                error=error,

                message=error,

                percentage=0,
                downloaded=0,
                total=0,

                speed=0,
                eta="00:00"
            )

            raise Exception(error)

        # =====================================================
        # CONTENT LENGTH
        # =====================================================

        content_length = response.headers.get(
            "Content-Length"
        )

        if content_length:

            try:

                total_size = int(
                    content_length
                )

            except (
                ValueError,
                TypeError
            ):

                total_size = 0

        else:

            total_size = 0

        # =====================================================
        # CONTENT RANGE FALLBACK
        # =====================================================

        if total_size == 0:

            content_range = response.headers.get(
                "Content-Range"
            )

            if content_range:

                try:

                    # Example:
                    # bytes 0-1023/1632

                    total_part = (
                        content_range
                        .split("/")[-1]
                    )

                    if total_part.isdigit():

                        total_size = int(
                            total_part
                        )

                except Exception:

                    total_size = 0

        print()
        print(
            "TOTAL SIZE:",
            total_size
        )

        # =====================================================
        # START STATUS
        # =====================================================

        self.update_status(
            status,
            lock,

            status="starting",
            running=True,
            completed=False,
            cancelled=False,

            movie_name=self.movie_name,

            total=round(
                total_size /
                1024 /
                1024,
                2
            ),

            percentage=0,
            downloaded=0,
            speed=0,

            eta="00:00",
            elapsed="00:00",

            filename=self.filepath,

            error=None,

            message=(
                f"Starting download "
                f"{self.movie_name}..."
            )
        )

        # =====================================================
        # CHUNK SIZE
        # =====================================================

        chunk_size = (
            8 * 1024 * 1024
        )

        # =====================================================
        # DOWNLOAD FILE
        # =====================================================

        try:

            with open(
                self.filepath,
                "wb"
            ) as file:

                for chunk in response.iter_content(
                    chunk_size=chunk_size
                ):

                    if not chunk:
                        continue

                    # =========================================
                    # CANCEL CHECK
                    # =========================================

                    with lock:

                        cancelled = bool(
                            status.get(
                                "cancel_requested",
                                False
                            )
                        )

                    if cancelled:

                        print(
                            "Stopping download..."
                        )

                        break

                    # =========================================
                    # WRITE
                    # =========================================

                    file.write(chunk)

                    downloaded += len(chunk)

                    # =========================================
                    # TIME
                    # =========================================

                    elapsed = (
                        time.time()
                        - start_time
                    )

                    elapsed = max(
                        elapsed,
                        0.001
                    )

                    # =========================================
                    # SPEED
                    # =========================================

                    speed_bytes = (
                        downloaded /
                        elapsed
                    )

                    speed_mb = (
                        speed_bytes /
                        1024 /
                        1024
                    )

                    # =========================================
                    # DOWNLOADED MB
                    # =========================================

                    downloaded_mb = (
                        downloaded /
                        1024 /
                        1024
                    )

                    # =========================================
                    # TOTAL MB
                    # =========================================

                    total_mb = (
                        total_size /
                        1024 /
                        1024
                    )

                    # =========================================
                    # PERCENTAGE
                    # =========================================

                    if total_size > 0:

                        percentage = (
                            downloaded /
                            total_size
                        ) * 100

                        percentage = min(
                            percentage,
                            100
                        )

                    else:

                        percentage = 0

                    # =========================================
                    # ETA
                    # =========================================

                    if (
                        total_size > 0
                        and speed_bytes > 0
                    ):

                        remaining = (
                            total_size
                            - downloaded
                        )

                        eta_seconds = (
                            remaining /
                            speed_bytes
                        )

                    else:

                        eta_seconds = 0

                    # =========================================
                    # UPDATE STATUS
                    # =========================================

                    self.update_status(
                        status,
                        lock,

                        status="downloading",

                        running=True,

                        completed=False,

                        cancelled=False,

                        movie_name=(
                            self.movie_name
                        ),

                        percentage=round(
                            percentage,
                            2
                        ),

                        downloaded=round(
                            downloaded_mb,
                            2
                        ),

                        total=round(
                            total_mb,
                            2
                        ),

                        speed=round(
                            speed_mb,
                            2
                        ),

                        eta=(
                            self.format_time(
                                eta_seconds
                            )
                        ),

                        elapsed=(
                            self.format_time(
                                elapsed
                            )
                        ),

                        filename=(
                            self.filepath
                        ),

                        error=None,

                        message=(
                            f"Downloading "
                            f"{self.movie_name}..."
                        )
                    )

            # =================================================
            # CHECK CANCELLED
            # =================================================

            with lock:

                cancelled = bool(
                    status.get(
                        "cancel_requested",
                        False
                    )
                )

            if cancelled:

                print(
                    "Download cancelled."
                )

                try:

                    if os.path.exists(
                        self.filepath
                    ):

                        os.remove(
                            self.filepath
                        )

                except OSError:
                    pass

                self.update_status(
                    status,
                    lock,

                    status="cancelled",

                    running=False,

                    completed=False,

                    cancelled=True,

                    cancel_requested=False,

                    error=None,

                    percentage=0,

                    downloaded=0,

                    speed=0,

                    eta="00:00",

                    message=(
                        f"{self.movie_name} "
                        f"download cancelled"
                    )
                )

                return

        except OSError as e:

            error = (
                "File error: "
                f"{e}"
            )

            print()
            print(
                "FILE ERROR:",
                error
            )

            self.update_status(
                status,
                lock,

                status="failed",

                running=False,

                completed=False,

                cancelled=False,

                error=error,

                message=error
            )

            raise Exception(error)

        except Exception as e:

            error = (
                "Download failed: "
                f"{repr(e)}"
            )

            print()
            print(
                "DOWNLOAD ERROR:",
                error
            )

            self.update_status(
                status,
                lock,

                status="failed",

                running=False,

                completed=False,

                cancelled=False,

                error=error,

                message=error
            )

            raise Exception(error)

        finally:

            if response is not None:

                response.close()

        # =====================================================
        # FINAL TIME
        # =====================================================

        duration = (
            time.time()
            - start_time
        )

        duration = max(
            duration,
            0.001
        )

        # =====================================================
        # FINAL SIZE
        # =====================================================

        final_mb = (
            downloaded /
            1024 /
            1024
        )

        # =====================================================
        # AVERAGE SPEED
        # =====================================================

        average_speed = (
            downloaded /
            duration /
            1024 /
            1024
        )

        # =====================================================
        # VERIFY DOWNLOAD
        # =====================================================

        if downloaded <= 0:

            error = (
                "Download finished with "
                "0 bytes received."
            )

            self.update_status(
                status,
                lock,

                status="failed",

                running=False,

                completed=False,

                cancelled=False,

                error=error,

                message=error,

                percentage=0,

                downloaded=0,

                total=round(
                    total_size /
                    1024 /
                    1024,
                    2
                ),

                speed=0,

                eta="00:00",

                elapsed=(
                    self.format_time(
                        duration
                    )
                )
            )

            raise Exception(error)

        # =====================================================
        # COMPLETED
        # =====================================================

        self.update_status(
            status,
            lock,

            status="completed",

            running=False,

            completed=True,

            cancelled=False,

            cancel_requested=False,

            error=None,

            movie_name=self.movie_name,

            percentage=100,

            downloaded=round(
                final_mb,
                2
            ),

            total=round(
                total_size /
                1024 /
                1024,
                2
            ),

            speed=round(
                average_speed,
                2
            ),

            eta="00:00",

            elapsed=(
                self.format_time(
                    duration
                )
            ),

            filename=self.filepath,

            message=(
                f"{self.movie_name} "
                f"download completed"
            )
        )

        # =====================================================
        # PRINT RESULT
        # =====================================================

        print()
        print("=" * 60)
        print("DOWNLOAD FINISHED")
        print("=" * 60)
        print(
            "Movie:",
            self.movie_name
        )
        print(
            "File:",
            self.filepath
        )
        print(
            "Size:",
            round(
                final_mb,
                2
            ),
            "MB"
        )
        print(
            "Average speed:",
            round(
                average_speed,
                2
            ),
            "MB/s"
        )
        print(
            "Environment:",
            "Vercel"
            if self.is_vercel
            else "Local"
        )
        print("=" * 60)