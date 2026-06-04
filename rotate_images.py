"""
rotate_images.py
Batch rotate all images in a folder 90 degrees counterclockwise.

Usage:
    python rotate_images.py <folder_name>

Example:
    python rotate_images.py try
    (rotates all images in pic/try/, saves to pic/try_rotated/)
"""
import os, sys
from PIL import Image


def main():
    if len(sys.argv) < 2:
        print("Usage: python rotate_images.py <folder_name>")
        print("  folder_name: subfolder under pic/ (e.g. 'try')")
        sys.exit(1)

    folder = sys.argv[1]
    input_dir = os.path.join("pic", folder)
    if not os.path.isdir(input_dir):
        print(f"Error: folder '{input_dir}' not found")
        sys.exit(1)

    files = sorted([f for f in os.listdir(input_dir)
                   if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])
    if not files:
        print(f"No images in {input_dir}")
        sys.exit(1)

    for fn in files:
        path = os.path.join(input_dir, fn)
        img = Image.open(path)
        rotated = img.transpose(Image.ROTATE_90)  # counterclockwise
        rotated.save(path)

    print(f"Rotated {len(files)} images in-place -> {input_dir}")


if __name__ == "__main__":
    main()
