#!/usr/local/bin/python

import os
import logging
from datetime import datetime, timedelta
from app import VIDEO_WORKING_DIR

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

def delete_old_files(directory: str, hours: int = 24):
    """
    Deletes files older than the specified number of hours from the given directory.

    Args:
        directory (str): Directory to scan for old files.
        hours (int): Age threshold in hours for deleting files.
    """
    threshold_time = datetime.now() - timedelta(hours=hours)

    if not os.path.exists(directory):
        logging.warning(f"Directory {directory} does not exist.")
        return

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_mtime < threshold_time:
                    os.remove(file_path)
                    logging.info(f"Deleted old file: {file_path}")
            except Exception as e:
                logging.error(f"Failed to delete file {file_path}: {e}")


if __name__ == "__main__":
    delete_old_files(VIDEO_WORKING_DIR)
