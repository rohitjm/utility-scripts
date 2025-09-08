import os
import shutil
import time
from datetime import datetime

# Set your source and destination directories
SOURCE_DIR = "/Users/rohitmathew/Dev/AI_ML/ComfyUI/output"
DEST_DIR = "/Volumes/Rohit/AI_ML/ComfyUI/output"
INTERVAL_SECONDS = 300  # 5 minutes

def get_unique_filename(dest_dir, filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename

    while os.path.exists(os.path.join(dest_dir, new_filename)):
        new_filename = f"{base}_{counter}{ext}"
        counter += 1

    return new_filename

def move_files_by_date():
    print("Checking for files to move...")
    for filename in os.listdir(SOURCE_DIR):
        source_path = os.path.join(SOURCE_DIR, filename)

        # Skip directories
        if not os.path.isfile(source_path):
            continue

        try:
            # Get last modified date
            mod_time = os.path.getmtime(source_path)
            date_str = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d")
            date_dir = os.path.join(DEST_DIR, date_str)

            # Create dated subdirectory if it doesn't exist
            os.makedirs(date_dir, exist_ok=True)

            # Resolve filename conflict
            unique_filename = get_unique_filename(date_dir, filename)
            dest_path = os.path.join(date_dir, unique_filename)

            # Move the file
            shutil.move(source_path, dest_path)
            print(f"Moved: {filename} → {dest_path}")
        except Exception as e:
            print(f"Failed to move {filename}: {e}")

if __name__ == "__main__":
    while True:
        move_files_by_date()
        print(f"Waiting {INTERVAL_SECONDS // 60} minutes...\n")
        time.sleep(INTERVAL_SECONDS)

