#!/usr/bin/env python3
import os
import re
import sys
from imdb import IMDb
from datetime import datetime

def smart_clean_query(filename):
    """
    Extracts a clean movie title + optional year from messy filenames.
    """
    name, _ = os.path.splitext(filename)

    # Remove bracketed parts [ ... ] or ( ... )
    name = re.sub(r"[\[\(].*?[\]\)]", " ", name)

    # Replace dots, underscores, and dashes with spaces
    name = re.sub(r"[._\-]+", " ", name)

    # Remove common quality/resolution keywords
    quality_keywords = [
        "1080p", "720p", "480p", "2160p", "4k", "hdrip", "brrip", "webrip", "bluray",
        "dvdrip", "hdtv", "x264", "x265", "hevc", "webdl", "web dl", "dvdscr", "cam"
    ]
    pattern = r"\b(?:{})\b".format("|".join(quality_keywords))
    name = re.sub(pattern, " ", name, flags=re.IGNORECASE)

    # Keep only alphanumeric and spaces
    name = re.sub(r"[^a-zA-Z0-9 ]", " ", name)

    # Collapse multiple spaces
    name = re.sub(r"\s+", " ", name).strip()

    # If year exists, cut off after year
    match = re.search(r"\b(19\d{2}|20\d{2})\b", name)
    if match:
        year_pos = match.end()
        name = name[:year_pos]

    return name.strip()

def rename_movies(folder_path):
    ia = IMDb()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_path = os.path.join(folder_path, f"rename_log_{timestamp}.txt")

    renamed_log = []
    not_found_log = []

    for fname in os.listdir(folder_path):
        full_path = os.path.join(folder_path, fname)
        if not os.path.isfile(full_path):
            continue

        query = smart_clean_query(fname)
        if not query:
            print(f"⚠ Could not extract a valid query from: {fname}")
            not_found_log.append(fname)
            continue

        print(f"Searching IMDb for '{query}'...")

        try:
            results = ia.search_movie(query, results=1)
        except Exception as e:
            print(f"  ⏳ Error searching IMDb: {e}")
            not_found_log.append(fname)
            continue

        if not results:
            print("  ⚠ No results found.")
            not_found_log.append(fname)
            continue

        movie = results[0]
        title = movie.get('title')
        year = movie.get('year', None)

        if not (title and year):
            print("  ⚠ Missing details, skipping.")
            not_found_log.append(fname)
            continue

        _, ext = os.path.splitext(fname)
        new_name = f"{title} ({year}){ext}"
        new_path = os.path.join(folder_path, new_name)

        if os.path.exists(new_path):
            print(f"  ℹ Destination already exists: '{new_name}' — skipping.")
            continue

        try:
            os.rename(full_path, new_path)
            print(f"  ✅ Renamed to: '{new_name}'")
            renamed_log.append(f"{fname} -> {new_name}")
        except Exception as e:
            print(f"  ❌ Rename failed: {e}")
            not_found_log.append(fname)

    # Write the log file
    with open(log_file_path, "w", encoding="utf-8") as logf:
        logf.write("Movie Rename Log\n")
        logf.write(f"Run Date: {datetime.now()}\n\n")
        logf.write("Renamed Files:\n")
        logf.write("----------------\n")
        if renamed_log:
            logf.write("\n".join(renamed_log))
            logf.write("\n")
        else:
            logf.write("None\n")

        logf.write("\nFiles with No Match:\n")
        logf.write("--------------------\n")
        if not_found_log:
            logf.write("\n".join(not_found_log))
            logf.write("\n")
        else:
            logf.write("None\n")

    print(f"\n📄 Log saved to: {log_file_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} /path/to/movie_folder")
        sys.exit(1)

    folder = sys.argv[1]
    if not os.path.isdir(folder):
        print(f"Error: '{folder}' is not a valid directory.")
        sys.exit(1)

    rename_movies(folder)
