from flask import Flask, render_template, Response, send_from_directory
from cachetools import cached, TTLCache
from google.cloud import storage
import os

app = Flask(__name__)
storage_client = storage.Client()
BUCKET_NAME = os.environ.get('BUCKET_NAME', "fogcat-webcam")


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )


@app.route('/')
def index():
    # Replace with actual GCS logic
    videos = get_video_list()
    return render_template('index.html', videos=videos)

@app.route('/video/<path:subpath>')
def video(subpath):
    print(subpath)
    blob = storage_client.bucket(BUCKET_NAME).blob(subpath)
    return send_video(blob)

@cached(cache=TTLCache(maxsize=100, ttl=600))
def get_video_list():
    # Access the GCS bucket
    bucket = storage_client.get_bucket(BUCKET_NAME)

    # Get all blobs in the bucket and sort by updated timestamp (most recent first)
    blobs = [x for x in list(bucket.list_blobs()) if "frames" not in x.name]
    if not blobs:
        return "No videos found in the bucket.", 404

    print(f"Found {len(blobs)} videos.")
    return blobs


@app.route('/video_latest')
def video_latest():
    try:
        blobs = get_video_list()
        most_recent_blob = max(blobs, key=lambda b: b.updated)
        print(f"Most recent blob: {most_recent_blob.name}")
        return send_video(most_recent_blob)

    except Exception as e:
        return f"An error occurred: {e}", 500


def send_video(blob):
    # Stream the blob content as bytes
    def generate():
        with blob.open("rb") as blob_stream:
            while True:
                chunk = blob_stream.read(1024 * 1024)  # Read in 1 MB chunks
                if not chunk:
                    break
                yield chunk

    return Response(generate(), content_type="video/mp4")


@app.route('/latest')
def latest():
    # Embed the video player with autoloop in the HTML
    return render_template("latest.html", video_url="/video_latest")

if __name__ == '__main__':
    app.run(debug=True)
