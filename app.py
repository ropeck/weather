from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route('/')
def index():
    # Replace with actual GCS logic
    videos = [
        {"name": "sample_video.mp4", "url": "/static/sample_video.mp4"}
    ]
    return render_template('index.html', videos=videos)

if __name__ == '__main__':
    app.run(debug=True)
