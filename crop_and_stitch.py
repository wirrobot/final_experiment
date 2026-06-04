"""
crop_and_stitch.py
Batch crop images using a user-selected rectangle on the first image,
then stitch cropped images into grids with configurable dimensions.

Format: 宽*高  (小数在前, 大数在后)

Usage:
    python crop_and_stitch.py <folder_name> <cols>*<rows>

Example:
    python crop_and_stitch.py try 3*8
    (stitches 24 images per grid, then asks for the size of the last grid)
"""
import os, sys, math
from PIL import Image
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector


def select_region(image_path):
    """
    Display the first image and let the user drag a rectangle
    to select the crop region.  Uses matplotlib RectangleSelector.
    """
    img = Image.open(image_path)
    img_array = np.array(img)

    fig, ax = plt.subplots(figsize=(14, 9))
    ax.imshow(img_array)
    ax.set_title(
        f"{os.path.basename(image_path)}  |  "
        "Drag to select crop region, then close window",
        fontsize=10,
    )

    region = [None]

    def on_select(eclick, erelease):
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)
        region[0] = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        w, h = region[0][2] - region[0][0], region[0][3] - region[0][1]
        print(f"Selected: ({region[0][0]}, {region[0][1]}) -> "
              f"({region[0][2]}, {region[0][3]})  {w}x{h}")

    rs = RectangleSelector(
        ax, on_select, useblit=True, button=[1],
        minspanx=5, minspany=5, spancoords="pixels", interactive=True,
    )
    fig.canvas.manager.set_window_title("Select crop region - close window when done")

    plt.tight_layout()
    plt.show()
    plt.close("all")
    return region[0]


def crop_all(input_dir, output_dir, region):
    """Crop every image using the given region (x1, y1, x2, y2)."""
    os.makedirs(output_dir, exist_ok=True)
    x1, y1, x2, y2 = region

    files = sorted([f for f in os.listdir(input_dir)
                   if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])

    for fn in files:
        img = Image.open(os.path.join(input_dir, fn))
        cropped = img.crop((x1, y1, x2, y2))
        cropped.save(os.path.join(output_dir, fn))

    print(f"Cropped {len(files)} images -> {output_dir}")
    return files


def stitch_grid(files, crop_dir, out_path, rows, cols):
    """Stitch a slice of files into a rows x cols grid."""
    if not files:
        return

    first = Image.open(os.path.join(crop_dir, files[0]))
    cell_w, cell_h = first.size

    grid_w = cols * cell_w
    grid_h = rows * cell_h
    grid_img = Image.new("RGB", (grid_w, grid_h), (255, 255, 255))

    for idx, fn in enumerate(files):
        if idx >= rows * cols:
            break
        r = idx // cols
        c = idx % cols
        img = Image.open(os.path.join(crop_dir, fn))
        grid_img.paste(img, (c * cell_w, r * cell_h))

    grid_img.save(out_path)
    print(f"  Saved {min(len(files), rows * cols)} images ({rows}x{cols}) -> {out_path}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python crop_and_stitch.py <folder_name> <rows>*<cols>")
        print("  folder_name : subfolder under pic/ (e.g. 'try')")
        print("  rows*cols   : target grid size (e.g. 3*8)")
        sys.exit(1)

    folder = sys.argv[1]
    grid_spec = sys.argv[2]

    try:
        grid_cols, grid_rows = map(int, grid_spec.split("*"))
    except ValueError:
        print(f"Error: invalid grid spec '{grid_spec}'. Use format like '3*8'")
        sys.exit(1)

    if grid_cols < 1 or grid_rows < 1:
        print("Error: cols and rows must be >= 1")
        sys.exit(1)

    input_dir = os.path.join("pic", folder)
    if not os.path.isdir(input_dir):
        print(f"Error: folder '{input_dir}' not found")
        sys.exit(1)

    image_files = sorted(
        [f for f in os.listdir(input_dir)
         if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
    )
    total = len(image_files)
    if not image_files:
        print(f"No images in {input_dir}")
        sys.exit(1)

    per_grid = grid_rows * grid_cols
    full_grids = total // per_grid
    remainder = total % per_grid

    print(f"Folder:  {folder}")
    print(f"Images:  {total}")
    print(f"Grid:    {grid_cols}*{grid_rows} = {per_grid} per grid")
    print(f"Output:  {full_grids} full grid(s)")
    if remainder > 0:
        print(f"Residue: {remainder} image(s) need a last-grid size")
    print()

    first_img = os.path.join(input_dir, image_files[0])
    region = select_region(first_img)
    if region is None:
        print("No region selected. Exiting.")
        sys.exit(1)

    crop_dir = os.path.join("pic", f"{folder}_cropped")
    cropped_files = crop_all(input_dir, crop_dir, region)

    stitch_dir = os.path.join("pic", f"{folder}_stitched")
    os.makedirs(stitch_dir, exist_ok=True)

    # Full grids
    for g in range(full_grids):
        start = g * per_grid
        end = start + per_grid
        page_files = cropped_files[start:end]
        out_path = os.path.join(stitch_dir, f"stitched_{g + 1:02d}.png")
        stitch_grid(page_files, crop_dir, out_path, grid_rows, grid_cols)

    # Remainder
    if remainder > 0:
        remain_files = cropped_files[full_grids * per_grid:]
        msg = f"\nRemaining {remainder} image(s).\n" \
              f"Enter last-grid size (e.g. '2*5') or press Enter to skip: "
        while True:
            sys.stdout.write(msg)
            sys.stdout.flush()
            last_spec = sys.stdin.readline().strip()
            if not last_spec:
                print("Skipped last grid.")
                break
            try:
                lc, lr = map(int, last_spec.split("*"))
            except ValueError:
                print("Invalid format, use e.g. '2*5'")
                continue
            if lc * lr < remainder:
                print(f"Grid {lc}*{lr} ({lc*lr}) is too small for "
                      f"{remainder} images. Try again.")
                continue
            out_path = os.path.join(stitch_dir, f"stitched_last.png")
            stitch_grid(remain_files, crop_dir, out_path, lr, lc)
            break

    print("\nDone.")


if __name__ == "__main__":
    main()
