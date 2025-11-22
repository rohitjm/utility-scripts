import os
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote_plus
import logging
import requests

# === CONFIG ===
SOURCE_DIR = Path("/mnt/rmhome-qnap-rohit/EBooks")   # Your existing ebooks folder
DEST_DIR = Path("/mnt/rmhome-qnap-rohit/calibre_library") # New Calibre-style library
GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes?q=intitle:{query}"
ALL_SUPPORTED_EXTENSIONS = [".epub", ".pdf", ".mobi"]

# === SETUP LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)

# === HELPER FUNCTIONS ===
def extract_title_from_filename(filename):
    title = filename.replace("_", " ").replace("-", " ")
    title = re.sub(r"\.(epub|pdf|mobi)$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*\([^)]*\)", "", title)  # remove (text)
    return title.strip()

def search_google_books_get_author(title):
    logging.info(f"🔍 Searching Google Books for: {title}")
    url = GOOGLE_BOOKS_API.format(query=quote_plus(title))
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.warning(f"❌ Error querying Google Books API: {e}")
        return None

    data = response.json()
    items = data.get("items", [])
    for item in items:
        volume_info = item.get("volumeInfo", {})
        authors = volume_info.get("authors")
        found_title = volume_info.get("title", "")
        if authors:
            logging.info(f"✅ Found: '{found_title}' by {authors[0]}")
            return authors[0]
    return None

def get_or_create_author_folder(dest_root: Path, author: str):
    for folder in dest_root.iterdir():
        if folder.is_dir() and folder.name.lower() == author.lower():
            return folder

    # Folder doesn't exist, create
    safe_author = re.sub(r'[\\/:"*?<>|]+', '_', author)  # sanitize
    new_folder = dest_root / safe_author
    new_folder.mkdir(parents=True, exist_ok=True)
    logging.info(f"📁 Created author folder: {new_folder}")
    return new_folder

def copy_and_organize_file(file_path: Path, dest_root: Path):
    title = extract_title_from_filename(file_path.name)
    author = search_google_books_get_author(title)
    if not author:
        author = "Unknown Author"

    target_folder = get_or_create_author_folder(dest_root, author)
    destination = target_folder / file_path.name

    if destination.exists():
        logging.info(f"⚠️ Skipping {file_path.name}, already exists in {target_folder}")
        return False

    shutil.copy2(str(file_path), str(destination))
    logging.info(f"📦 Copied '{file_path.name}' → '{target_folder}'")
    return True

def move_file_to_author_folder(file_path: Path, dest_root: Path):
    """Move file (used for reorganizing existing library)."""
    title = extract_title_from_filename(file_path.name)
    author = search_google_books_get_author(title)
    if not author:
        author = "Unknown Author"

    target_folder = get_or_create_author_folder(dest_root, author)
    destination = target_folder / file_path.name

    if file_path.resolve() == destination.resolve():
        logging.info(f"⚠️ Already in correct folder: {file_path.name}")
        return False

    if destination.exists():
        logging.info(f"⚠️ Conflict: {destination} already exists, skipping")
        return False

    shutil.move(str(file_path), str(destination))
    logging.info(f"📦 Moved '{file_path.name}' → '{target_folder}'")
    return True

def organize_directory(source_dir: Path, dest_dir: Path, extensions=None):
    extensions = extensions or ALL_SUPPORTED_EXTENSIONS
    copied_count = 0
    skipped_count = 0

    for ext in extensions:
        logging.info(f"📂 Scanning {source_dir} for {ext} files...")
        files = list(source_dir.rglob(f"*{ext}"))
        if not files:
            logging.info(f"⚠️ No {ext} files found in {source_dir}")
            continue

        for file in files:
            if copy_and_organize_file(file, dest_dir):
                copied_count += 1
            else:
                skipped_count += 1

    logging.info(f"✅ Organization complete: Copied={copied_count}, Skipped={skipped_count}")

def reorganize_library(dest_dir: Path, extensions=None):
    extensions = extensions or ALL_SUPPORTED_EXTENSIONS
    moved_count = 0
    skipped_count = 0

    for ext in extensions:
        logging.info(f"📂 Scanning {dest_dir} for {ext} files to reorganize...")
        files = list(dest_dir.rglob(f"*{ext}"))
        for file in files:
            if move_file_to_author_folder(file, dest_dir):
                moved_count += 1
            else:
                skipped_count += 1

    logging.info(f"✅ Reorganization complete: Moved={moved_count}, Skipped={skipped_count}")

# === MAIN ===
def main():
    logging.info("🚀 Starting ebook organizer...")

    if "--reorganize" in sys.argv:
        logging.info("🔄 Reorganizing existing Calibre library...")
        reorganize_library(DEST_DIR)
    else:
        logging.info("📥 Organizing new ebooks from source directory...")
        organize_directory(SOURCE_DIR, DEST_DIR)

    logging.info("🏁 Ebook organizer finished.")

if __name__ == "__main__":
    input_path = sys.argv[1] if len(sys.argv) > 1 else None
    if input_path and not input_path.startswith("--"):
        SOURCE_DIR = Path(input_path).expanduser()
    main()
