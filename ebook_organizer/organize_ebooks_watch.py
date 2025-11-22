#!/usr/bin/env python3
import os
import shutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from loguru import logger

# Configure these paths
SOURCE_DIR = Path("/mnt/rmhome-qnap-rohit/EBooks")   # Your existing ebooks folder
DEST_DIR = Path("/mnt/rmhome-qnap-rohit/calibre_library") # New Calibre-style library

# Supported ebook extensions
EXTENSIONS = {".epub", ".mobi", ".azw3", ".pdf"}

logger.add("ebook_organizer.log", rotation="1 MB")

def organize_file(file_path):
    file_path = Path(file_path)
    if file_path.suffix.lower() not in EXTENSIONS:
        return

    # Try to read author and title from filename: "Author - Title.ext"
    parts = file_path.stem.split(" - ", 1)
    if len(parts) == 2:
        author, title = parts
    else:
        author = "Unknown Author"
        title = file_path.stem

    # Destination: /Calibre/Author/Title.ext
    author_dir = DEST_DIR / author
    author_dir.mkdir(parents=True, exist_ok=True)

    dest_file = author_dir / file_path.name

    if not dest_file.exists():
        shutil.copy2(file_path, dest_file)
        logger.info(f"Copied {file_path} -> {dest_file}")
    else:
        logger.info(f"File already exists, skipping: {dest_file}")

class EBookHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            organize_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            organize_file(event.src_path)

if __name__ == "__main__":
    logger.info("Starting ebook organizer...")
    event_handler = EBookHandler()
    observer = Observer()
    observer.schedule(event_handler, str(SOURCE_DIR), recursive=True)
    observer.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

