
from packages import *



app = Flask(__name__)


# ============================================================
# GLOBAL DATA
# ============================================================

current_data = None
base_data = []

data_lock = Lock()
download_lock = Lock()


# ============================================================
# DOWNLOAD STATUS
# ============================================================

download_status = {
    "status": "idle",
    "running": False,
    "completed": False,
    "cancelled": False,
    "cancel_requested": False,
    "error": None,

    "percentage": 0,

    "downloaded": 0,
    "total": 0,

    "speed": 0,

    "eta": "00:00",
    "elapsed": "00:00",

    "filename": "",
    "message": ""
}


# ============================================================
# RESET DOWNLOAD STATUS
# ============================================================

def reset_download_status():

    with download_lock:

        download_status["status"] = "idle"
        download_status["running"] = False
        download_status["completed"] = False
        download_status["cancelled"] = False
        download_status["cancel_requested"] = False
        download_status["error"] = None

        download_status["percentage"] = 0

        download_status["downloaded"] = 0
        download_status["total"] = 0

        download_status["speed"] = 0

        download_status["eta"] = "00:00"
        download_status["elapsed"] = "00:00"

        download_status["filename"] = ""
        download_status["message"] = ""


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template("index.html")


# ============================================================
# MOVIE PROCESSING
# ============================================================

def downdload_process(movie):

    global current_data

    try:

        print()
        print("=" * 60)
        print("MOVIE PROCESSING")
        print("=" * 60)

        print("Movie:", movie)

        data = rg(movie, 360)

        data.stage1()

        with data_lock:

            current_data = data

            if hasattr(data, "count") and data.count:

                base_data[:] = [
                    item
                    for item in data.count
                    if item
                ]

            else:

                base_data.clear()

        print("QUALITIES:")
        print(base_data)

        print("Movie processing completed")

        print("=" * 60)

    except Exception as e:

        print()
        print("=" * 60)
        print("MOVIE PROCESSING ERROR")
        print("=" * 60)

        print("Movie:", movie)
        print("Error:", e)

        traceback.print_exc()

        print("=" * 60)

        with data_lock:

            current_data = None
            base_data.clear()


# ============================================================
# SEARCH MOVIE
# ============================================================

@app.route("/downdload", methods=["POST"])
def download():

    global current_data

    movie = request.form.get(
        "movie",
        ""
    ).strip()

    if not movie:

        return """
        <h2>Enter movie name</h2>
        <a href="/">Go Back</a>
        """

    print()
    print("=" * 60)
    print("SEARCH REQUEST")
    print("=" * 60)

    print("Movie:", movie)

    # --------------------------------------------------------
    # CLEAR OLD MOVIE DATA
    # --------------------------------------------------------

    with data_lock:

        current_data = None
        base_data.clear()

    # --------------------------------------------------------
    # RESET OLD DOWNLOAD STATE
    # --------------------------------------------------------

    reset_download_status()

    # --------------------------------------------------------
    # PROCESS MOVIE
    # --------------------------------------------------------

    thread = Thread(
        target=downdload_process,
        args=(movie,),
        daemon=True
    )

    thread.start()

    thread.join()

    # --------------------------------------------------------
    # GET RESULT
    # --------------------------------------------------------

    with data_lock:

        data = current_data
        counts = list(base_data)

    if data is None:

        return """
        <h2>Movie processing failed</h2>
        <a href="/">Go Back</a>
        """

    print("AVAILABLE QUALITIES:")
    print(counts)

    print("=" * 60)

    return render_template(
        "index1.html",
        movie=movie,
        counts=counts
    )


# ============================================================
# SELECT QUALITY
# ============================================================

@app.route("/select_quality", methods=["POST"])
def select_quality():

    global current_data

    movie = request.form.get(
        "movie",
        ""
    ).strip()

    quality = request.form.get(
        "quality",
        ""
    ).strip()

    print()
    print("=" * 60)
    print("QUALITY SELECTION")
    print("=" * 60)

    print("Movie:", movie)
    print("Quality:", quality)

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not movie:

        return jsonify({
            "success": False,
            "error": "Movie name missing"
        }), 400

    if not quality:

        return jsonify({
            "success": False,
            "error": "Quality missing"
        }), 400

    # --------------------------------------------------------
    # GET MOVIE DATA
    # --------------------------------------------------------

    with data_lock:

        data = current_data

    if data is None:

        return jsonify({
            "success": False,
            "error": "Movie processing data not found"
        }), 404

    # --------------------------------------------------------
    # RESET DOWNLOAD STATE
    #
    # IMPORTANT:
    # This removes "Download already running"
    # from the previous selection.
    # --------------------------------------------------------

    reset_download_status()

    # --------------------------------------------------------
    # SET QUALITY
    # --------------------------------------------------------

    try:

        data.quality = quality

        print(
            "Selected quality:",
            data.quality
        )

        # ----------------------------------------------------
        # CONTINUE PROCESS
        # ----------------------------------------------------

        data.continue_process()

        print(
            "Continue process completed"
        )

    except Exception as e:

        print()
        print("=" * 60)
        print("CONTINUE PROCESS ERROR")
        print("=" * 60)

        print("Error:", e)

        traceback.print_exc()

        print("=" * 60)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    # --------------------------------------------------------
    # GET DATA
    # --------------------------------------------------------

    poster = getattr(
        data,
        "poster",
        None
    )

    bg_poster = getattr(
        data,
        "bg_poster",
        None
    )

    details = getattr(
        data,
        "details",
        {}
    )

    final_link = getattr(
        data,
        "f_link",
        None
    )

    print()
    print("--------------------------------")
    print("Final Link:", final_link)
    print("Poster:", poster)
    print("Background:", bg_poster)
    print("Details:", details)
    print("--------------------------------")

    # --------------------------------------------------------
    # CHECK LINK
    # --------------------------------------------------------

    if not final_link:

        return jsonify({
            "success": False,
            "error": "Final download link was not generated"
        }), 500

    # --------------------------------------------------------
    # SAVE DATA
    # --------------------------------------------------------

    with data_lock:

        current_data = data

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Return JSON because JavaScript uses response.json()
    # --------------------------------------------------------

    return jsonify({

        "success": True,

        "movie": movie,

        "quality": quality,

        "poster": poster,

        "bg_poster": bg_poster,

        "details": details,

        "link": final_link,

        "next": "/movie_details"

    })


# ============================================================
# MOVIE DETAILS PAGE
# ============================================================

@app.route("/movie_details")
def movie_details():

    with data_lock:

        data = current_data

    if data is None:

        return """
        <h2>Movie data not found</h2>
        <a href="/">Go Back</a>
        """

    poster = getattr(
        data,
        "poster",
        None
    )

    bg_poster = getattr(
        data,
        "bg_poster",
        None
    )

    details = getattr(
        data,
        "details",
        {}
    )

    quality = getattr(
        data,
        "quality",
        ""
    )

    final_link = getattr(
        data,
        "f_link",
        None
    )

    return render_template(
        "movie_details.html",

        movie=details.get(
            "Movie",
            ""
        ),

        poster=poster,

        bg_poster=bg_poster,

        details=details,

        quality=quality,

        link=final_link
    )


# ============================================================
# RUN DOWNLOAD
# ============================================================

def run_download():

    global current_data

    try:

        print()
        print("=" * 60)
        print("DOWNLOAD STARTED")
        print("=" * 60)

        # ----------------------------------------------------
        # GET DATA
        # ----------------------------------------------------

        with data_lock:

            data = current_data

        if data is None:

            raise Exception(
                "Movie data not found"
            )

        # ----------------------------------------------------
        # GET LINK
        # ----------------------------------------------------

        final_link = getattr(
            data,
            "f_link",
            None
        )

        if not final_link:

            raise Exception(
                "Final download link not found"
            )

        print("Final link:")
        print(final_link)

        # ----------------------------------------------------
        # CREATE DOWNLOADER
        # ----------------------------------------------------

        downloader = MovieDownloader(
            data
        )

        # ----------------------------------------------------
        # START DOWNLOAD
        # ----------------------------------------------------

        downloader.download(
            download_status,
            download_lock
        )

        # ----------------------------------------------------
        # FINISHED
        # ----------------------------------------------------

        with download_lock:

            if download_status["cancel_requested"]:

                download_status["status"] = "cancelled"
                download_status["running"] = False
                download_status["completed"] = False
                download_status["cancelled"] = True
                download_status["error"] = None
                download_status["message"] = "Download cancelled"
                download_status["eta"] = "00:00"

                print("DOWNLOAD CANCELLED")

                return

            download_status["status"] = "completed"
            download_status["running"] = False
            download_status["completed"] = True
            download_status["cancelled"] = False
            download_status["error"] = None
            download_status["percentage"] = 100
            download_status["eta"] = "00:00"
            download_status["message"] = "Download completed"

        print()
        print("=" * 60)
        print("DOWNLOAD COMPLETED")
        print("=" * 60)

    except Exception as e:

        print()
        print("=" * 60)
        print("DOWNLOAD ERROR")
        print("=" * 60)

        print("Error:", e)

        traceback.print_exc()

        print("=" * 60)

        with download_lock:

            download_status["running"] = False

            if download_status["cancel_requested"]:

                download_status["status"] = "cancelled"
                download_status["completed"] = False
                download_status["cancelled"] = True
                download_status["error"] = None
                download_status["message"] = "Download cancelled"
                download_status["eta"] = "00:00"

            else:

                download_status["status"] = "error"
                download_status["completed"] = False
                download_status["cancelled"] = False
                download_status["error"] = str(e)
                download_status["message"] = "Download failed"


# ============================================================
# START DOWNLOAD
# ============================================================

@app.route("/start_download", methods=["POST"])
def start_download():

    with data_lock:

        data = current_data

    # --------------------------------------------------------
    # CHECK DATA
    # --------------------------------------------------------

    if data is None:

        return jsonify({
            "success": False,
            "error": "Movie data not found"
        }), 404

    # --------------------------------------------------------
    # CHECK LINK
    # --------------------------------------------------------

    final_link = getattr(
        data,
        "f_link",
        None
    )

    if not final_link:

        return jsonify({
            "success": False,
            "error": "Final download link not found"
        }), 400

    # --------------------------------------------------------
    # START DOWNLOAD
    # --------------------------------------------------------

    with download_lock:

        # ----------------------------------------------------
        # ONLY BLOCK IF ACTUALLY RUNNING
        # ----------------------------------------------------

        if download_status["running"]:

            return jsonify({
                "success": False,
                "error": "Download already running"
            }), 409

        # ----------------------------------------------------
        # RESET EVERYTHING
        # ----------------------------------------------------

        download_status.update({

            "status": "starting",

            "running": True,

            "completed": False,

            "cancelled": False,

            "cancel_requested": False,

            "error": None,

            "percentage": 0,

            "downloaded": 0,

            "total": 0,

            "speed": 0,

            "eta": "00:00",

            "elapsed": "00:00",

            "filename": "",

            "message": "Starting download..."
        })

    print()
    print("=" * 60)
    print("START DOWNLOAD REQUEST")
    print("=" * 60)

    # --------------------------------------------------------
    # THREAD
    # --------------------------------------------------------

    thread = Thread(
        target=run_download,
        daemon=True
    )

    thread.start()

    return jsonify({

        "success": True,

        "message": "Download started"

    })


# ============================================================
# CANCEL DOWNLOAD
# ============================================================

@app.route("/cancel_download", methods=["POST"])
def cancel_download():

    with download_lock:

        if not download_status["running"]:

            return jsonify({
                "success": False,
                "error": "No download is running"
            }), 400

        download_status["cancel_requested"] = True

        download_status["status"] = "cancelling"

        download_status["message"] = (
            "Cancelling download..."
        )

    print()
    print("=" * 60)
    print("CANCEL REQUESTED")
    print("=" * 60)

    return jsonify({

        "success": True,

        "message": "Cancel requested"

    })


# ============================================================
# DOWNLOAD STATUS
# ============================================================

@app.route("/download_status")
def get_download_status():

    with download_lock:

        status = download_status.copy()

    return jsonify(status)


# ============================================================
# OLD STATUS ROUTE
# ============================================================

@app.route("/status")
def status():

    with download_lock:

        current_status = download_status.copy()

    with data_lock:

        qualities = list(base_data)

    return jsonify({

        "qualities": qualities,

        "download": current_status

    })


# ============================================================
# RUN FLASK
# ============================================================

