from flask import Flask, render_template, Response, send_from_directory, jsonify
from cachetools import cached, TTLCache
from google.cloud import storage
from typing import List, Dict, Tuple, Union
import os

app = Flask(__name__)
storage_client: storage.Client = storage.Client()
BUCKET_NAME: str = os.environ.get('BUCKET_NAME', "fogcat-webcam")


@app.route('/favicon.ico')
def favicon() -> Response:
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )


@app.route('/')
def index() -> str:
    # Replace with actual GCS logic
    videos = get_video_list()
    return render_template('index.html', videos=videos)


@app.route('/video/<path:subpath>')
def video(subpath: str) -> Response:
    print(subpath)
    blob = storage_client.bucket(BUCKET_NAME).blob(subpath)
    return send_video(blob)


@cached(cache=TTLCache(maxsize=100, ttl=600))
def get_video_list() -> List[storage.Blob]:
    # Access the GCS bucket
    bucket = storage_client.get_bucket(BUCKET_NAME)

    # Get all blobs in the bucket and filter out "frames"
    blobs: List[storage.Blob] = [x for x in list(bucket.list_blobs()) if "frames" not in x.name]
    if not blobs:
        raise ValueError("No videos found in the bucket.")  # Raise an exception for an error

    print(f"Found {len(blobs)} videos.")
    return blobs


@app.route('/video_latest')
def video_latest() -> Union[Response, Tuple[str, int]]:
    try:
        blobs = get_video_list()
        if isinstance(blobs, tuple):  # Handle case where no videos are found
            return blobs

        most_recent_blob = max(blobs, key=lambda b: b.updated)
        print(f"Most recent blob: {most_recent_blob.name}")
        return send_video(most_recent_blob)

    except Exception as e:
        return f"An error occurred: {e}", 500


def send_video(blob: storage.Blob) -> Response:
    # Stream the blob content as bytes
    def generate() -> bytes:
        with blob.open("rb") as blob_stream:
            while True:
                chunk = blob_stream.read(1024 * 1024)  # Read in 1 MB chunks
                if not chunk:
                    break
                yield chunk

    return Response(generate(), content_type="video/mp4")


@app.route('/latest')
def latest() -> str:
    # Embed the video player with autoloop in the HTML
    return render_template("latest.html", video_url="/video_latest")


if __name__ == '__main__':
    app.run(debug=True)
