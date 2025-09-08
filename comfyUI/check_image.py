from PIL import Image
import os

directory = "/Volumes/Rohit/AI_ML/ComfyUI/output/2025-06-03/"

for filename in os.listdir(directory):
    path = os.path.join(directory, filename)
    try:
        with Image.open(path) as img:
            img.verify()
        print(f"✅ {filename} is a valid image.")
    except Exception as e:
        print(f"❌ {filename} is invalid: {e}")
