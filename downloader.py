import os
import time
import requests


class MovieDownloader:

    def __init__(self, movie_data):

        self.data = movie_data

        # =====================================================
        # FINAL URL
        # =====================================================

        self.url = getattr(
            movie_data,
            "f_link",
            None
        )

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
        # DOWNLOAD FOLDER
        # =====================================================

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

        seconds = max(
            0,
            int(seconds)
        )

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
    # DOWNLOAD
    # =========================================================

    def download(
        self,
        status,
        lock
    ):

        if not self.url:

            raise Exception(
                "Final download link not found"
            )

        print()
        print("--------------------------------")
        print("DOWNLOAD URL")
        print("--------------------------------")
        print(self.url)
        print("--------------------------------")

        # =====================================================
        # CONNECT
        # =====================================================

        try:

            response = requests.get(

                self.url,

                stream=True,

                timeout=(15, 60),

                allow_redirects=True
            )

            response.raise_for_status()

        except requests.RequestException as e:

            raise Exception(
                f"Download connection error: {e}"
            )

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

            except ValueError:

                total_size = 0

        else:

            total_size = 0

        # =====================================================
        # START
        # =====================================================

        downloaded = 0

        start_time = time.time()

        chunk_size = 8 * 1024 * 1024

        # =====================================================
        # INITIAL STATUS
        # =====================================================

        with lock:

            status["status"] = "starting"

            status["running"] = True

            status["movie_name"] = self.movie_name

            status["message"] = (
                f"Connecting to download "
                f"{self.movie_name}..."
            )

            status["filename"] = self.filepath

            status["total"] = round(
                total_size / 1024 / 1024,
                2
            )

        # =====================================================
        # FILE
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

                        cancelled = (
                            status[
                                "cancel_requested"
                            ]
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
                        downloaded
                        / elapsed
                    )

                    speed_mb = (
                        speed_bytes
                        / 1024
                        / 1024
                    )

                    # =========================================
                    # DOWNLOADED MB
                    # =========================================

                    downloaded_mb = (
                        downloaded
                        / 1024
                        / 1024
                    )

                    # =========================================
                    # TOTAL MB
                    # =========================================

                    total_mb = (
                        total_size
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
                            remaining
                            / speed_bytes
                        )

                    else:

                        eta_seconds = 0

                    # =========================================
                    # UPDATE BACKEND
                    # =========================================

                    with lock:

                        status["status"] = (
                            "downloading"
                        )

                        status["running"] = True

                        status["completed"] = False

                        status["cancelled"] = False

                        status["cancel_requested"] = False

                        status["movie_name"] = (
                            self.movie_name
                        )

                        status["percentage"] = round(
                            percentage,
                            2
                        )

                        status["downloaded"] = round(
                            downloaded_mb,
                            2
                        )

                        status["total"] = round(
                            total_mb,
                            2
                        )

                        status["speed"] = round(
                            speed_mb,
                            2
                        )

                        status["eta"] = (
                            self.format_time(
                                eta_seconds
                            )
                        )

                        status["elapsed"] = (
                            self.format_time(
                                elapsed
                            )
                        )

                        status["filename"] = (
                            self.filepath
                        )

                        status["message"] = (
                            f"Downloading "
                            f"{self.movie_name}..."
                        )

            # =================================================
            # CANCELLED
            # =================================================

            with lock:

                cancelled = (
                    status[
                        "cancel_requested"
                    ]
                )

            if cancelled:

                try:

                    if os.path.exists(
                        self.filepath
                    ):

                        os.remove(
                            self.filepath
                        )

                except OSError:

                    pass

                with lock:

                    status["status"] = (
                        "cancelled"
                    )

                    status["running"] = False

                    status["completed"] = False

                    status["cancelled"] = True

                    status["cancel_requested"] = False

                    status["error"] = None

                    status["message"] = (
                        f"{self.movie_name} "
                        f"download cancelled"
                    )

                    status["eta"] = "00:00"

                return

        except OSError as e:

            raise Exception(
                f"File error: {e}"
            )

        finally:

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
            / 1024
            / 1024
        )

        # =====================================================
        # COMPLETED
        # =====================================================

        with lock:

            status["status"] = (
                "completed"
            )

            status["running"] = False

            status["completed"] = True

            status["cancelled"] = False

            status["cancel_requested"] = False

            status["error"] = None

            status["movie_name"] = (
                self.movie_name
            )

            status["percentage"] = 100

            status["downloaded"] = round(
                final_mb,
                2
            )

            status["total"] = round(
                total_size / 1024 / 1024,
                2
            )

            status["speed"] = round(
                average_speed,
                2
            )

            status["eta"] = "00:00"

            status["elapsed"] = (
                self.format_time(
                    duration
                )
            )

            status["filename"] = (
                self.filepath
            )

            status["message"] = (
                f"{self.movie_name} "
                f"download completed"
            )

        print()
        print("--------------------------------")
        print("DOWNLOAD FINISHED")
        print("--------------------------------")
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
            round(final_mb, 2),
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
        print("--------------------------------")