# Use a lightweight Python base image
FROM python:3.9-slim-bullseye

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    procps \
    inetutils-syslogd \
    curl \
    ffmpeg \
    cron \
    at \
    tzdata && \
    pip install --no-cache-dir \
    yt-dlp \
    google-cloud-storage \
    gunicorn \
    astral \
    pytz \
    flask \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


# Set the working directory
WORKDIR /app

# Create and use a non-root user
RUN useradd -m appuser
USER appuser

# Download and install Google Cloud SDK
RUN curl https://sdk.cloud.google.com | bash && \
    echo "installed"
ENV PATH="$PATH:/home/appuser/google-cloud-sdk/bin"


# Expose the port the app runs on
EXPOSE 5000

# Add a healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:5000/health || exit 1

USER root
# Copy the rest of the application files
COPY app.py endpoint.sh templates static /app
RUN chown -R appuser:appuser /app
RUN chmod +x /app/*.sh /app/*.py

USER appuser

USER root
# Start the container with the endpoint script
CMD ["bash", "/app/endpoint.sh"]