import os
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote_plus

import requests

EBOOKS_DIR = Path.home() / "Documents" / "EBooks"
GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes?q=intitle:{query}"

ALL_SUPPORTED_EXTENSIONS = [".epub", ".pdf", ".mobi"]

def ask_for_filetypes():
    selected = []
    print("📚 Select which file types to process:")
    for ext in ALL_SUPPORTED_EXTENSIONS:
        choice = input(f"Process {ext} files? [y/N]: ").strip().lower()
        if choice == 'y':
            selected.append(ext)
    return selected

def extract_title_from_filename(filename):
    title = filename.replace("_", " ").replace("-", " ")
    title = re.sub(r"\.(epub|pdf|mobi)$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*\([^)]*\)", "", title)  # remove (text)
    return title.strip()

def search_google_books_get_author(title):
    print(f"🔍 Searching Google Books for: {title}")
    url = GOOGLE_BOOKS_API.format(query=quote_plus(title))
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Error querying Google Books API: {e}")
        return None

    data = response.json()
    items = data.get("items", [])
    for item in items:
        volume_info = item.get("volumeInfo", {})
        authors = volume_info.get("authors")
        found_title = volume_info.get("title", "")
        if authors:
            print(f"✅ Found: '{found_title}' by {authors[0]}")
            return authors[0]  # Return the first listed author
    return None

def get_or_create_author_folder(author):
    folder_names = [f.name for f in EBOOKS_DIR.iterdir() if f.is_dir()]
    match = next((f for f in folder_names if f.lower() == author.lower()), None)

    if match:
        return EBOOKS_DIR / match

    print(f"📁 No folder found for author: '{author}'")
    create = input(f"Create new folder '{author}'? [y/N]: ").strip().lower()
    if create == 'y':
        new_path = EBOOKS_DIR / author
        new_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created folder: {new_path}")
        return new_path
    else:
        print("⏩ Skipping file due to missing folder.")
        return None

def move_file_to_author_folder(file_path, author):
    target_folder = get_or_create_author_folder(author)
    if target_folder:
        destination = target_folder / file_path.name
        print(f"📦 Moving '{file_path.name}' → '{target_folder.name}'")
        shutil.move(str(file_path), str(destination))

def main(input_dir=None):
    source_dir = Path(input_dir).expanduser() if input_dir else Path.home() / "Downloads"

    if not source_dir.exists():
        print(f"❌ Directory {source_dir} does not exist.")
        return

    selected_extensions = ask_for_filetypes()
    if not selected_extensions:
        print("🚫 No file types selected. Exiting.")
        return

    for ext in selected_extensions:
        print(f"\n📂 Scanning for {ext} files in {source_dir}")
        files = list(source_dir.glob(f"*{ext}"))
        if not files:
            print(f"⚠️ No {ext} files found.")
            continue

        for file in files:
            print(f"\n📖 Processing: {file.name}")
            title = extract_title_from_filename(file.name)
            author = search_google_books_get_author(title)

            if not author:
                author = input("❓ Could not determine author. Please enter author name manually: ").strip()

            move_file_to_author_folder(file, author)

if __name__ == "__main__":
    input_path = sys.argv[1] if len(sys.argv) > 1 else None
    main(input_path)
