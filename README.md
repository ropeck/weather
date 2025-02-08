# camera_collector_webapp

This is a Flask web application for displaying videos collected by the camera-collector Kubernetes pod.

## Development Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   python app.py
   ```

## Deployment

This app is designed to run as a pod in Kubernetes. Build the Docker image and deploy it to your cluster.
The repository does CI/CD and builds the fogcat5/collector-webapp image from the event trigger.
To make a new version, a small change can be checked in.