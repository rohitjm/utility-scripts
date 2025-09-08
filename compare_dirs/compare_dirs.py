#!/usr/bin/env python3
import os
import sys

def usage():
    print(f"Usage: {sys.argv[0]} <dir1> <dir2>")
    sys.exit(1)

if len(sys.argv) != 3:
    usage()

dir1, dir2 = sys.argv[1], sys.argv[2]

if not os.path.isdir(dir1):
    print(f"Error: '{dir1}' is not a directory.")
    sys.exit(1)

if not os.path.isdir(dir2):
    print(f"Error: '{dir2}' is not a directory.")
    sys.exit(1)

files1 = set(os.listdir(dir1))
files2 = set(os.listdir(dir2))

missing_in_dir2 = files1 - files2

if missing_in_dir2:
    print("Files in first directory but not in second:")
    for f in sorted(missing_in_dir2):
        print(f)
else:
    print("All files in the first directory are present in the second.")
