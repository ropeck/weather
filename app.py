#!/usr/local/bin/python

from flask import Flask, render_template, Response, send_from_directory, jsonify
from cachetools import cached, TTLCache
from google.cloud import storage
from typing import List
import os
import logging
import subprocess
from datetime import datetime

app = Flask(__name__)
storage_client: storage.Client = storage.Client()
BUCKET_NAME: str = os.environ.get('BUCKET_NAME', "fogcat-webcam")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


@app.route('/favicon.ico')
def favicon() -> Response:
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200


@app.route('/')
def index() -> str:
    # Replace with actual GCS logic
    videos = get_video_list()
    return render_template('index.html', videos=videos)


@app.route('/video/<path:subpath>')
def video(subpath: str) -> Response:
    blob = storage_client.bucket(BUCKET_NAME).get_blob(subpath)
    return send_video(blob)


@cached(cache=TTLCache(maxsize=100, ttl=600))
def get_video_list() -> List[storage.Blob]:
    # Access the GCS bucket
    bucket = storage_client.get_bucket(BUCKET_NAME)
    blobs: List[storage.Blob] = [x for x in list(bucket.list_blobs()) if "frames" not in x.name]
    if not blobs:
        raise ValueError("No videos found in the bucket.")
    return blobs


@cached(cache=TTLCache(maxsize=20, ttl=60))
def send_video(blob: storage.Blob) -> Response:
    """
    Downloads the blob to local disk, processes it with FFmpeg, and serves the processed file.
    """
    local_path = f"/tmp/{blob.name.replace('/', '_')}"
    processed_path = f"/tmp/processed_{blob.name.replace('/', '_')}"
    try:
        # Download blob to local file
        blob.download_to_filename(local_path)

        # Properly format the text arguments
        from pytz import timezone
        pst = timezone('America/Los_Angeles')
        creation_time_formatted = blob.time_created.astimezone(pst).strftime("%b %-d, %Y %-I:%M %p %Z")
        title_text = creation_time_formatted.replace(":", "\\:")
        watermark_text = "fogcat5"

        # Use FFmpeg to process the video and save to a file
        subprocess.run(
            [
                "ffmpeg",
                "-i", local_path,  # Input file
                "-vf",
                f"drawtext=text='{title_text}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:fontsize=24:fontcolor=white:x=10:y=10," \
                f"drawtext=text='{watermark_text}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:fontsize=24:fontcolor=white:x=w-tw-10:y=10",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-movflags", "+faststart",
                "-y", processed_path
            ],
            check=True
        )

        # Serve the processed video file
        with open(processed_path, "rb") as video_file:
            return Response(video_file.read(), content_type="video/mp4")
    except Exception as e:
        logging.error(f"Error processing video: {e}")
        return Response(f"Error: {e}", status=500)
    finally:
        # Cleanup local files
        if os.path.exists(local_path):
            os.remove(local_path)
        if os.path.exists(processed_path):
            os.remove(processed_path)


@app.route('/video_latest')
def video_latest() -> Response:
    try:
        blob = latest_blob()
        return send_video(blob)
    except ValueError as e:
        logging.error(f"Error fetching latest video: {e}")
        return Response(f"Error: {str(e)}", status=404)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return Response(f"Error: {str(e)}", status=500)


def latest_blob() -> storage.Blob:
    blobs = get_video_list()
    if not blobs:
        raise ValueError("No blobs found in the bucket.")
    latest = max(blobs, key=lambda b: b.updated)
    logging.info(f"Latest blob: {latest.name}, size: {latest.size}, created at: {latest.time_created}")
    return latest


@app.route('/latest')
def latest() -> str:
    return render_template("latest.html",
                           video_url="video_latest",
                           latest_blob=str(latest_blob()))


if __name__ == '__main__':
    app.run(debug=True)
