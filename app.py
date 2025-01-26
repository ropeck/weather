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
    blob = storage_client.bucket(BUCKET_NAME).blob(subpath)
    return send_video(blob)


@cached(cache=TTLCache(maxsize=100, ttl=600))
def get_video_list() -> List[storage.Blob]:
    # Access the GCS bucket
    bucket = storage_client.get_bucket(BUCKET_NAME)
    blobs: List[storage.Blob] = [x for x in list(bucket.list_blobs()) if "frames" not in x.name]
    if not blobs:
        raise ValueError("No videos found in the bucket.")
    return blobs


def send_video(blob: storage.Blob) -> Response:
    def process_video_with_ffmpeg(input_path: str, output_path: str):
        """
        Processes the video using FFmpeg to add a title with the current date and time.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file {input_path} does not exist.")

        blob_creation_time = blob.time_created.strftime("%Y-%m-%d %H:%M:%S")
        title_text = blob_creation_time
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

        logging.info(f"Processing video {input_path} with FFmpeg to add title...")
        command = [
            "ffmpeg",
            "-i", input_path,
            "-vf", f"drawtext=text='{title_text}':fontfile={font_path}:fontsize=24:fontcolor=white:x=(w-text_w)/2:y=30",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-movflags", "+faststart",
            "-y", output_path
        ]

        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if process.returncode != 0:
            logging.error(f"FFmpeg processing failed: {process.stderr.decode()}")
            raise RuntimeError(f"FFmpeg processing failed: {process.stderr.decode()}")

        logging.info(f"Video processed successfully: {output_path}")

    local_path = f"/tmp/{blob.name.replace('/', '_')}"
    processed_path = f"/tmp/processed_{blob.name.replace('/', '_')}"
    try:
        blob.download_to_filename(local_path)
        process_video_with_ffmpeg(local_path, processed_path)
        with open(processed_path, "rb") as video_file:
            return Response(video_file.read(), content_type="video/mp4")
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)
        if os.path.exists(processed_path):
            os.remove(processed_path)


@app.route('/video_latest')
def video_latest() -> Response:
    return send_video(latest_blob())


def latest_blob() -> storage.Blob:
    blobs = get_video_list()
    return max(blobs, key=lambda b: b.updated)


@app.route('/latest')
def latest() -> str:
    return render_template("latest.html",
                           video_url="video_latest",
                           latest_blob=str(latest_blob()))


if __name__ == '__main__':
    app.run(debug=True)
