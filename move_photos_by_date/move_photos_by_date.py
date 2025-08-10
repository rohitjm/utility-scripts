#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import json
import hashlib
import csv
from datetime import datetime
from pathlib import Path

def get_exiftool_data(file_path: Path) -> dict:
    """Extract metadata using exiftool, return dict or empty."""
    try:
        result = subprocess.run(
            ["exiftool", "-j", str(file_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        if data and isinstance(data, list):
            return data[0]
    except subprocess.CalledProcessError as e:
        print(f"[EXIFTOOL ERROR] Could not read EXIF for {file_path}: {e.stderr.strip()}")
    except Exception as e:
        print(f"[EXIF ERROR] Unexpected error reading EXIF from {file_path}: {e}")
    return {}

def parse_date(date_str):
    """Parse EXIF date string 'YYYY:MM:DD HH:MM:SS' to datetime.date."""
    try:
        return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S").date()
    except Exception:
        return None

def safe_folder_name(name):
    """Sanitize folder name to remove problematic characters."""
    return "".join(c if c.isalnum() or c in " _-" else "_" for c in str(name)).strip() or "Unknown"

def file_hash(path: Path, blocksize=65536):
    """Compute SHA256 hash of a file, with error handling."""
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            for block in iter(lambda: f.read(blocksize), b""):
                h.update(block)
        return h.hexdigest()
    except Exception as e:
        print(f"[HASH ERROR] Could not hash file {path}: {e}")
        return None

def get_unique_path(dest_path: Path, src_file: Path, log_writer):
    """Get unique destination path, avoiding overwrites or duplicates."""
    if not dest_path.exists():
        return dest_path
    try:
        if file_hash(dest_path) == file_hash(src_file):
            print(f"Skipping duplicate: {src_file}")
            log_writer.writerow(["Skipped Duplicate", str(src_file), ""])
            return None
    except Exception as e:
        print(f"[HASH ERROR] Could not compare files for duplicates {src_file} and {dest_path}: {e}")
        # To be safe, don't skip here
    base, ext = dest_path.stem, dest_path.suffix
    counter = 1
    while True:
        new_path = dest_path.with_name(f"{base}_{counter}{ext}")
        if not new_path.exists():
            print(f"Renaming {src_file.name} to avoid conflict: {new_path.name}")
            log_writer.writerow(["Renamed", str(src_file), str(new_path)])
            return new_path
        try:
            if file_hash(new_path) == file_hash(src_file):
                print(f"Skipping duplicate (after rename check): {src_file}")
                log_writer.writerow(["Skipped Duplicate", str(src_file), ""])
                return None
        except Exception as e:
            print(f"[HASH ERROR] Could not compare files for duplicates {src_file} and {new_path}: {e}")
        counter += 1

def is_skippable_file(file_path: Path) -> bool:
    # Skip hidden macOS resource fork files and dotfiles
    return file_path.name.startswith("._") or file_path.name.startswith(".")

def process_file(file_path: Path, base_folder: Path, move_files: bool, seen_hashes: set, log_writer):
    if is_skippable_file(file_path):
        print(f"Skipping hidden/system file: {file_path}")
        return

    try:
        meta = get_exiftool_data(file_path)
        date_taken_str = meta.get("DateTimeOriginal") or meta.get("CreateDate") or meta.get("MediaCreateDate")
        date_taken = parse_date(date_taken_str) if date_taken_str else None
        if not date_taken:
            # fallback to file modification date
            date_taken = datetime.fromtimestamp(file_path.stat().st_mtime).date()
    except FileNotFoundError:
        print(f"[METADATA ERROR] File not found (likely moved): {file_path}, skipping.")
        return
    except Exception as e:
        print(f"[METADATA ERROR] Could not get date for {file_path}: {e}")
        date_taken = datetime.fromtimestamp(file_path.stat().st_mtime).date()

    try:
        lens_raw = meta.get("LensModel") or meta.get("LensID") or meta.get("LensMake") or "Unknown_Lens"
        lens_name = safe_folder_name(lens_raw)
    except Exception as e:
        print(f"[METADATA ERROR] Could not get lens info for {file_path}: {e}")
        lens_name = "Unknown_Lens"

    date_folder = date_taken.strftime("%Y-%m-%d")
    try:
        target_folder = base_folder / date_folder / lens_name
        target_folder.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[FILE ERROR] Could not create directory {target_folder}: {e}")
        return

    dest_path = target_folder / file_path.name

    current_hash = file_hash(file_path)
    if current_hash is None:
        print(f"[HASH ERROR] Skipping file due to hash failure: {file_path}")
        return

    if current_hash in seen_hashes:
        print(f"Skipping duplicate by hash: {file_path}")
        log_writer.writerow(["Skipped Duplicate", str(file_path), ""])
        return

    unique_dest_path = get_unique_path(dest_path, file_path, log_writer)
    if unique_dest_path is None:
        # duplicate skip
        return

    action = "Moved" if move_files else "Reorganized"
    try:
        shutil.move(str(file_path), str(unique_dest_path))
        print(f"{action}: {file_path} -> {unique_dest_path}")
        log_writer.writerow([action, str(file_path), str(unique_dest_path)])
        seen_hashes.add(current_hash)
    except FileNotFoundError:
        print(f"[FILE ERROR] File not found during move (likely moved already): {file_path}")
    except Exception as e:
        print(f"[FILE ERROR] Could not move {file_path} to {unique_dest_path}: {e}")

def walk_and_process(src_dir: Path, base_folder: Path, move_files: bool, log_writer):
    seen_hashes = set()
    for root, _, files in os.walk(src_dir):
        for fname in files:
            file_path = Path(root) / fname
            if is_skippable_file(file_path):
                print(f"Skipping hidden/system file: {file_path}")
                continue
            try:
                if not file_path.is_file():
                    print(f"Skipping non-regular file: {file_path}")
                    continue
                process_file(file_path, base_folder, move_files, seen_hashes, log_writer)
            except FileNotFoundError:
                print(f"File disappeared during processing, skipping: {file_path}")
            except Exception as e:
                print(f"[ERROR] Unexpected error processing {file_path}: {e}")

def main():
    print("Photo Organizer")
    print("1: Move files from source to destination")
    print("2: Reorganize files in place")
    choice = input("Enter 1 or 2: ").strip()
    if choice not in {"1", "2"}:
        print("Invalid choice, exiting.")
        sys.exit(1)

    src = Path(input("Enter source directory path: ").strip())
    if not src.is_dir():
        print(f"Source directory does not exist: {src}")
        sys.exit(1)

    if choice == "1":
        dest = Path(input("Enter destination directory path: ").strip())
        try:
            dest.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Could not create destination directory {dest}: {e}")
            sys.exit(1)
        base_folder = dest
        move_files = True
    else:
        base_folder = src
        move_files = False

    log_file = Path(f"photo_organizer_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    try:
        with log_file.open("w", newline="", encoding="utf-8") as csvfile:
            log_writer = csv.writer(csvfile)
            log_writer.writerow(["Action", "Source Path", "Destination Path"])
            walk_and_process(src, base_folder, move_files, log_writer)
    except Exception as e:
        print(f"[LOG ERROR] Could not write to log file {log_file}: {e}")
        sys.exit(1)

    print(f"\nDone! Log saved to {log_file}")

if __name__ == "__main__":
    main()
