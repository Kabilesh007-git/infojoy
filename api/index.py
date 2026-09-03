import os
import sys
import traceback

# ============================================================
# PROJECT ROOT
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# Allow Python to find packages.py, processing_unit.py, etc.
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# ============================================================
# IMPORTS
# ============================================================

from flask import Flask, render_template, request, jsonify

from processing_unit import rg
from downloader import MovieDownloader

from threading import Thread, Lock


# ============================================================
# FLASK APP
# ============================================================

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)


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

        download_status.update({

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
        })


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

    with data_lock:

        current_data = None
        base_data.clear()

    reset_download_status()

    thread = Thread(
        target=downdload_process,
        args=(movie,),
        daemon=True
    )

    thread.start()

    thread.join()

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

    with data_lock:

        data = current_data

    if data is None:

        return jsonify({
            "success": False,
            "error": "Movie processing data not found"
        }), 404

    reset_download_status()

    try:

        data.quality = quality

        print(
            "Selected quality:",
            data.quality
        )

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

    if not final_link:

        return jsonify({
            "success": False,
            "error": "Final download link was not generated"
        }), 500

    with data_lock:

        current_data = data

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
# MOVIE DETAILS
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

        with data_lock:

            data = current_data

        if data is None:

            raise Exception(
                "Movie data not found"
            )

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

        downloader = MovieDownloader(
            data
        )

        downloader.download(
            download_status,
            download_lock
        )

        with download_lock:

            if download_status["cancel_requested"]:

                download_status.update({

                    "status": "cancelled",

                    "running": False,

                    "completed": False,

                    "cancelled": True,

                    "error": None,

                    "message": "Download cancelled",

                    "eta": "00:00"
                })

                print("DOWNLOAD CANCELLED")

                return

            download_status.update({

                "status": "completed",

                "running": False,

                "completed": True,

                "cancelled": False,

                "error": None,

                "percentage": 100,

                "eta": "00:00",

                "message": "Download completed"
            })

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

                download_status.update({

                    "status": "cancelled",

                    "completed": False,

                    "cancelled": True,

                    "error": None,

                    "message": "Download cancelled",

                    "eta": "00:00"
                })

            else:

                download_status.update({

                    "status": "error",

                    "completed": False,

                    "cancelled": False,

                    "error": str(e),

                    "message": "Download failed"
                })


# ============================================================
# START DOWNLOAD
# ============================================================

@app.route("/start_download", methods=["POST"])
def start_download():

    with data_lock:

        data = current_data

    if data is None:

        return jsonify({
            "success": False,
            "error": "Movie data not found"
        }), 404

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

    with download_lock:

        if download_status["running"]:

            return jsonify({
                "success": False,
                "error": "Download already running"
            }), 409

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
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":

    app.run(
    host="0.0.0.0",
    port=5000,
    debug=True
)
#
# this is the main application 