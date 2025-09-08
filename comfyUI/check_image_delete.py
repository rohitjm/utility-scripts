import os
from PIL import Image

def remove_invalid_images(directory):
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory.")
        return

    files = os.listdir(directory)
    removed = 0

    for filename in files:
        filepath = os.path.join(directory, filename)

        # Skip if not a file
        if not os.path.isfile(filepath):
            continue

        try:
            with Image.open(filepath) as img:
                img.verify()  # Verify integrity
        except Exception as e:
            print(f"❌ Deleting invalid image: {filename} ({e})")
            os.remove(filepath)
            removed += 1

    print(f"✅ Done. Removed {removed} invalid image(s).")

if __name__ == "__main__":
    # Change this to your directory
    target_dir = "/Volumes/Rohit/AI_ML/ComfyUI/output/2025-06-03/"
    remove_invalid_images(target_dir)
