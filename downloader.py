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
            self.url = str(
                self.url
            ).strip()

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
        # VERCEL
        # =====================================================

        self.is_vercel = (
            os.getenv("VERCEL") == "1"
            or os.getenv("VERCEL_ENV") is not None
        )

        # =====================================================
        # DOWNLOAD FOLDER
        # =====================================================

        if self.is_vercel:

            self.folder = "/tmp/Infojoy"

        else:

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

        self.filepath = os.path.join(
            self.folder,
            filename + ".mp4"
        )

    # =========================================================
    # FORMAT TIME
    # =========================================================

    @staticmethod
    def format_time(seconds):

        try:

            seconds = max(
                0,
                int(seconds)
            )

        except (
            TypeError,
            ValueError
        ):

            seconds = 0

        hours = seconds // 3600

        minutes = (
            seconds % 3600
        ) // 60

        seconds = seconds % 60

        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{seconds:02d}"
        )

    # =========================================================
    # FORMAT SIZE
    # =========================================================

    @staticmethod
    def format_size(bytes_value):

        try:

            bytes_value = float(
                bytes_value
            )

        except (
            TypeError,
            ValueError
        ):

            return "0 B"

        if bytes_value < 1024:

            return (
                f"{bytes_value:.0f} B"
            )

        if bytes_value < 1024 ** 2:

            return (
                f"{bytes_value / 1024:.2f} KB"
            )

        if bytes_value < 1024 ** 3:

            return (
                f"{bytes_value / 1024 ** 2:.2f} MB"
            )

        return (
            f"{bytes_value / 1024 ** 3:.2f} GB"
        )

    # =========================================================
    # HEADERS
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

            "Accept": "*/*",

            "Accept-Encoding": "identity",

            "Connection": "keep-alive"
        }

    # =========================================================
    # UPDATE STATUS
    # =========================================================

    def update_status(
        self,
        status_data,
        lock,
        **values
    ):

        with lock:

            status_data.update(
                values
            )

    # =========================================================
    # CHECK CANCEL
    # =========================================================

    def is_cancelled(
        self,
        status_data,
        lock
    ):

        with lock:

            return bool(
                status_data.get(
                    "cancel_requested",
                    False
                )
            )

    # =========================================================
    # SET ERROR
    # =========================================================

    def set_error(
        self,
        status_data,
        lock,
        message
    ):

        self.update_status(

            status_data,
            lock,

            status="error",

            running=False,

            completed=False,

            cancelled=False,

            error=message,

            message=message
        )

    # =========================================================
    # DOWNLOAD
    # =========================================================

    def download(
        self,
        status_data,
        lock
    ):

        # =====================================================
        # CHECK URL
        # =====================================================

        if not self.url:

            self.set_error(
                status_data,
                lock,
                "Final download link not found"
            )

            return

        print()
        print("=" * 60)
        print("DOWNLOAD START")
        print("=" * 60)

        print(
            "Movie :",
            self.movie_name
        )

        print(
            "URL   :",
            self.url
        )

        print(
            "File  :",
            self.filepath
        )

        print(
            "Mode  :",
            "VERCEL"
            if self.is_vercel
            else "LOCAL"
        )

        print("=" * 60)

        response = None

        downloaded = 0

        total_size = 0

        start_time = time.time()

        # =====================================================
        # INITIAL STATUS
        # =====================================================

        self.update_status(

            status_data,
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

            eta="00:00:00",

            elapsed="00:00:00",

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
            print(
                "Connecting to server..."
            )

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

            print(
                "CONTENT RANGE:",
                response.headers.get(
                    "Content-Range"
                )
            )

            response.raise_for_status()

        except requests.exceptions.Timeout as e:

            message = (
                "Download connection timed out: "
                f"{e}"
            )

            self.set_error(
                status_data,
                lock,
                message
            )

            return

        except requests.exceptions.ConnectionError as e:

            message = (
                "Could not connect to download server: "
                f"{e}"
            )

            self.set_error(
                status_data,
                lock,
                message
            )

            return

        except requests.exceptions.HTTPError as e:

            status_code = (
                response.status_code
                if response is not None
                else "unknown"
            )

            message = (
                "Download server returned HTTP "
                f"{status_code}: {e}"
            )

            self.set_error(
                status_data,
                lock,
                message
            )

            return

        except requests.RequestException as e:

            message = (
                "Download connection error: "
                f"{e}"
            )

            self.set_error(
                status_data,
                lock,
                message
            )

            return

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

        # =====================================================
        # CONTENT RANGE FALLBACK
        # =====================================================

        if total_size <= 0:

            content_range = response.headers.get(
                "Content-Range"
            )

            if (
                content_range
                and "/" in content_range
            ):

                try:

                    total_part = (
                        content_range
                        .split("/")[-1]
                        .strip()
                    )

                    if total_part.isdigit():

                        total_size = int(
                            total_part
                        )

                except Exception:

                    total_size = 0

        # =====================================================
        # TOTAL MB
        # =====================================================

        total_mb = (
            total_size
            / 1024
            / 1024
        )

        print()
        print(
            "TOTAL SIZE:",
            total_size,
            "bytes"
        )

        print(
            "TOTAL SIZE:",
            round(
                total_mb,
                2
            ),
            "MB"
        )

        # =====================================================
        # START STATUS
        # =====================================================

        self.update_status(

            status_data,
            lock,

            status="starting",

            running=True,

            completed=False,

            cancelled=False,

            movie_name=self.movie_name,

            total=total_size,

            percentage=0,

            downloaded=0,

            speed=0,

            eta="00:00:00",

            elapsed=self.format_time(
                time.time() - start_time
            ),

            filename=self.filepath,

            error=None,

            message=(
                f"Starting download "
                f"{self.movie_name}..."
            )
        )

        # =====================================================
        # CHUNK SIZE
        #
        # 1 MB makes progress updates and cancellation
        # more responsive than 8 MB chunks.
        # =====================================================

        chunk_size = 1024 * 1024

        # =====================================================
        # DOWNLOAD
        # =====================================================

        try:

            with open(
                self.filepath,
                "wb"
            ) as file:

                for chunk in response.iter_content(
                    chunk_size=chunk_size
                ):

                    # =========================================
                    # CHECK CANCEL BEFORE WRITE
                    # =========================================

                    if self.is_cancelled(
                        status_data,
                        lock
                    ):

                        print(
                            "Stopping download..."
                        )

                        break

                    if not chunk:

                        continue

                    # =========================================
                    # WRITE
                    # =========================================

                    file.write(
                        chunk
                    )

                    file.flush()

                    downloaded += len(
                        chunk
                    )

                    # =========================================
                    # CHECK CANCEL AFTER WRITE
                    # =========================================

                    if self.is_cancelled(
                        status_data,
                        lock
                    ):

                        print(
                            "Cancellation detected."
                        )

                        break

                    # =========================================
                    # ELAPSED
                    # =========================================

                    elapsed_seconds = (
                        time.time()
                        - start_time
                    )

                    elapsed_seconds = max(
                        elapsed_seconds,
                        0.001
                    )

                    # =========================================
                    # SPEED
                    # =========================================

                    speed_bytes = (
                        downloaded
                        / elapsed_seconds
                    )

                    speed_mb = (
                        speed_bytes
                        / 1024
                        / 1024
                    )

                    # =========================================
                    # PERCENTAGE
                    # =========================================

                    if total_size > 0:

                        percentage = (
                            downloaded
                            / total_size
                        ) * 100

                        percentage = max(
                            0,
                            min(
                                100,
                                percentage
                            )
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

                        remaining = max(
                            0,
                            total_size - downloaded
                        )

                        eta_seconds = (
                            remaining
                            / speed_bytes
                        )

                    else:

                        eta_seconds = 0

                    # =========================================
                    # UPDATE STATUS
                    #
                    # IMPORTANT:
                    # downloaded and total are BYTES.
                    # The frontend converts them to MB/GB.
                    # =========================================

                    self.update_status(

                        status_data,
                        lock,

                        status="downloading",

                        running=True,

                        completed=False,

                        cancelled=False,

                        movie_name=self.movie_name,

                        percentage=round(
                            percentage,
                            2
                        ),

                        downloaded=downloaded,

                        total=total_size,

                        speed=speed_bytes,

                        eta=self.format_time(
                            eta_seconds
                        ),

                        elapsed=self.format_time(
                            elapsed_seconds
                        ),

                        filename=self.filepath,

                        error=None,

                        message=(
                            f"Downloading "
                            f"{self.movie_name}..."
                        )
                    )

            # =================================================
            # CHECK CANCELLATION
            # =================================================

            cancelled = self.is_cancelled(
                status_data,
                lock
            )

            if cancelled:

                print(
                    "Download cancelled."
                )

                # =============================================
                # DELETE PARTIAL FILE
                # =============================================

                try:

                    if os.path.exists(
                        self.filepath
                    ):

                        os.remove(
                            self.filepath
                        )

                        print(
                            "Partial file deleted."
                        )

                except OSError as e:

                    print(
                        "Could not delete partial file:",
                        e
                    )

                # =============================================
                # CANCELLED STATUS
                #
                # IMPORTANT:
                # cancel_requested stays TRUE.
                # =============================================

                self.update_status(

                    status_data,
                    lock,

                    status="cancelled",

                    running=False,

                    completed=False,

                    cancelled=True,

                    cancel_requested=True,

                    error=None,

                    percentage=0,

                    downloaded=0,

                    speed=0,

                    eta="00:00:00",

                    elapsed="00:00:00",

                    filename=self.filepath,

                    message=(
                        f"{self.movie_name} "
                        "download cancelled"
                    )
                )

                return

        except OSError as e:

            message = (
                f"File error: {e}"
            )

            self.set_error(
                status_data,
                lock,
                message
            )

            return

        except Exception as e:

            # =============================================
            # If cancellation caused the exception,
            # don't turn it into an error.
            # =============================================

            if self.is_cancelled(
                status_data,
                lock
            ):

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

                    status_data,
                    lock,

                    status="cancelled",

                    running=False,

                    completed=False,

                    cancelled=True,

                    cancel_requested=True,

                    error=None,

                    percentage=0,

                    downloaded=0,

                    speed=0,

                    eta="00:00:00",

                    elapsed="00:00:00",

                    message="Download cancelled"
                )

                return

            message = (
                f"Download failed: {e}"
            )

            self.set_error(
                status_data,
                lock,
                message
            )

            return

        finally:

            if response is not None:

                try:

                    response.close()

                except Exception:

                    pass

        # =====================================================
        # FINAL CANCEL CHECK
        # =====================================================

        if self.is_cancelled(
            status_data,
            lock
        ):

            print(
                "Final cancellation detected."
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

                status_data,
                lock,

                status="cancelled",

                running=False,

                completed=False,

                cancelled=True,

                cancel_requested=True,

                error=None,

                percentage=0,

                downloaded=0,

                speed=0,

                eta="00:00:00",

                elapsed="00:00:00",

                filename=self.filepath,

                message="Download cancelled"
            )

            return

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
            downloaded
            / 1024
            / 1024
        )

        # =====================================================
        # AVERAGE SPEED
        # =====================================================

        average_speed = (
            downloaded
            / duration
        )

        average_speed_mb = (
            average_speed
            / 1024
            / 1024
        )

        # =====================================================
        # VERIFY DOWNLOAD
        # =====================================================

        if downloaded <= 0:

            message = (
                "Download finished with "
                "0 bytes received."
            )

            self.set_error(
                status_data,
                lock,
                message
            )

            return

        # =====================================================
        # OPTIONAL SIZE CHECK
        # =====================================================

        if (
            total_size > 0
            and downloaded < total_size
        ):

            print()
            print(
                "WARNING:"
            )

            print(
                "Expected:",
                self.format_size(
                    total_size
                )
            )

            print(
                "Received:",
                self.format_size(
                    downloaded
                )
            )

            print(
                "Download ended before "
                "Content-Length was reached."
            )

        # =====================================================
        # COMPLETED
        # =====================================================

        self.update_status(

            status_data,
            lock,

            status="completed",

            running=False,

            completed=True,

            cancelled=False,

            cancel_requested=False,

            error=None,

            movie_name=self.movie_name,

            percentage=100,

            downloaded=downloaded,

            total=total_size,

            speed=average_speed,

            eta="00:00:00",

            elapsed=self.format_time(
                duration
            ),

            filename=self.filepath,

            message=(
                f"{self.movie_name} "
                "download completed"
            )
        )

        # =====================================================
        # PRINT FINAL INFORMATION
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
                average_speed_mb,
                2
            ),
            "MB/s"
        )

        print(
            "Elapsed:",
            self.format_time(
                duration
            )
        )

        print(
            "Environment:",
            "Vercel"
            if self.is_vercel
            else "Local"
        )

        print("=" * 60)