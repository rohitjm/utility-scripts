# Photo Organizer Script

A Python tool to help organize large numbers of photo and RAW files by their capture date and camera lens metadata, using **ExifTool** for reliable metadata extraction.

---

## Features

- **Organizes photos by date and lens model** into folders: `YYYY-MM-DD/LensName/filename.ext`  
- Supports **JPEG, RAW, and many other image formats**  
- Handles **duplicate detection** via SHA256 file hashing (skips duplicates)  
- Automatically **renames files to avoid name collisions**  
- Supports two modes:  
  - **Move:** Move files from a source folder into a new organized destination folder  
  - **Reorganize:** Reorganize files *in place* within the same folder  
- Skips macOS hidden/system files (e.g., `._*` files)  
- Detailed **logging** of all actions to a timestamped CSV file  
- Robust error handling to continue processing on read/move errors  

---

## Requirements

- Python 3.6+  
- [ExifTool](https://exiftool.org) installed and available in your system PATH  

### Installing ExifTool

- **macOS:**  
  ```bash
  brew install exiftool
