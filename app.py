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
    """
    Streams the video from GCS with FFmpeg processing applied in real-time.
    """
    def generate():
        # Properly format the text arguments
        creation_time_formatted = blob.time_created.strftime("%I:%M %p %Z")
        title_text = creation_time_formatted
        watermark_text = "fogcat5"

        # Use a pipe to stream data between FFmpeg and the HTTP response
        process = subprocess.Popen(
            [
                "ffmpeg",
                "-i", "pipe:0",  # Input from stdin
                "-vf",
                f"drawtext=text='{title_text}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:fontsize=24:fontcolor=white:x=10:y=10," \
                f"drawtext=text='{watermark_text}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:fontsize=24:fontcolor=white:x=w-tw-10:y=10",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-movflags", "+faststart",
                "-f", "mp4",
                "pipe:1"  # Output to stdout
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=10**6
        )

        try:
            # Stream the blob content into FFmpeg
            with blob.open("rb") as blob_stream:
                while chunk := blob_stream.read(1024 * 1024):  # Read in chunks
                    process.stdin.write(chunk)
                process.stdin.close()

            # Stream FFmpeg's output to the HTTP response
            for chunk in iter(lambda: process.stdout.read(1024 * 1024), b""):
                yield chunk
        except Exception as e:
            logging.error(f"Error streaming video: {e}")
        finally:
            process.terminate()
            process.wait()
        # Use a pipe to stream data between FFmpeg and the HTTP response
        process = subprocess.Popen(
            [
                "ffmpeg",
                "-i", "pipe:0",  # Input from stdin
                "-vf", f"drawtext=text='Created at {blob.time_created.strftime('%I:%M %p %Z')}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:fontsize=24:fontcolor=white:x=10:y=10,"
                       f"drawtext=text='fogcat5':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:fontsize=24:fontcolor=white:x=w-tw-10:y=10",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-movflags", "+faststart",
                "-f", "mp4",
                "pipe:1"  # Output to stdout
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=10**6
        )

        try:
            # Stream the blob content into FFmpeg
            with blob.open("rb") as blob_stream:
                while chunk := blob_stream.read(1024 * 1024):  # Read in chunks
                    process.stdin.write(chunk)
                process.stdin.close()

            # Stream FFmpeg's output to the HTTP response
            for chunk in iter(lambda: process.stdout.read(1024 * 1024), b""):
                yield chunk
        except Exception as e:
            logging.error(f"Error streaming video: {e}")
        finally:
            process.terminate()
            process.wait()

    return Response(generate(), content_type="video/mp4")


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
