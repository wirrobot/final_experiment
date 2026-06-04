"""
crop_and_stitch.py
Batch crop images using a user-selected rectangle on the first image,
then stitch cropped images into grids.

Subcommands:
    select_region <folder>      打开首张图框选裁剪区域，保存坐标
    process <folder> <cols>*<rows> [last_cols>*<last_rows>]
                                用已保存的区域裁剪拼接，[last] 为最后一页尺寸

Format: 宽*高  (小数在前, 大数在后)

Examples:
    python crop_and_stitch.py select_region try
    python crop_and_stitch.py process try 3*8
    python crop_and_stitch.py process try 3*8 2*5
"""
import os, sys, json, math
from PIL import Image
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector


CROPPED_DIR = os.path.join("pic", "cropped")
STITCHED_DIR = os.path.join("pic", "stitched")


# ---- 框选裁剪区域 ----

def select_region(image_path):
    img = Image.open(image_path)
    img_array = np.array(img)

    fig, ax = plt.subplots(figsize=(14, 9))
    ax.imshow(img_array)
    ax.set_title(
        f"{os.path.basename(image_path)}  |  "
        "Click-drag to select crop region, then close window",
        fontsize=10,
    )

    region = [None]
    selector = [None]  # keep reference alive to prevent GC

    def on_select(eclick, erelease):
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)
        region[0] = [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]
        w, h = region[0][2] - region[0][0], region[0][3] - region[0][1]
        print(f"Selected: ({region[0][0]}, {region[0][1]}) -> "
              f"({region[0][2]}, {region[0][3]})  {w}x{h}")

    selector[0] = RectangleSelector(
        ax, on_select,
        useblit=False,
        button=[1],
        minspanx=5, minspany=5,
        spancoords="pixels",
        interactive=True,
        props=dict(facecolor="none", edgecolor="lime", linewidth=2, alpha=1),
    )

    fig.canvas.manager.set_window_title("Select crop region - close window when done")
    plt.tight_layout()
    plt.show()
    plt.close("all")

    if selector[0] is not None:
        selector[0].disconnect_events()
    return region[0]


def cmd_select_region(folder):
    """框选并保存裁剪坐标到 pic/cropped/<folder>/region.json"""
    input_dir = os.path.join("pic", folder)
    files = sorted([f for f in os.listdir(input_dir)
                   if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])
    if not files:
        print(f"No images in {input_dir}")
        sys.exit(1)

    first_img = os.path.join(input_dir, files[0])
    print(f"Opening: {first_img}")
    region = select_region(first_img)
    if region is None:
        print("No region selected. Exiting.")
        sys.exit(1)

    out_dir = os.path.join(CROPPED_DIR, folder)
    os.makedirs(out_dir, exist_ok=True)
    cfg_path = os.path.join(out_dir, "region.json")
    with open(cfg_path, "w") as f:
        json.dump({"region": region}, f)
    print(f"Region saved to {cfg_path}")


# ---- 批量裁剪 ----

def crop_all(input_dir, output_dir, region):
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


# ---- 拼接 ----

MAX_SIZE_MB = 10


def _save_under_limit(img, out_path, max_mb=MAX_SIZE_MB):
    """Save image, compressing further if it exceeds max_mb."""
    max_bytes = max_mb * 1024 * 1024

    # Try optimized PNG first
    img.save(out_path, format="PNG", optimize=True)
    if os.path.getsize(out_path) <= max_bytes:
        return

    # Try palette-mode PNG (works well for LCD displays with few colors)
    if img.mode != "P":
        pal = img.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
        pal.save(out_path, format="PNG", optimize=True)
    if os.path.getsize(out_path) <= max_bytes:
        return

    # Fallback: JPEG with quality reduction
    jpg_path = os.path.splitext(out_path)[0] + ".jpg"
    for q in [85, 70, 50]:
        img.convert("RGB").save(jpg_path, format="JPEG", quality=q, optimize=True)
        if os.path.getsize(jpg_path) <= max_bytes:
            print(f"  (switched to JPEG q={q})")
            # If we saved as jpg, rename to match original extension expectations
            if jpg_path != out_path:
                os.replace(jpg_path, out_path)
            return
    os.replace(jpg_path, out_path)


def stitch_grid(files, crop_dir, out_path, rows, cols):
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

    _save_under_limit(grid_img, out_path)
    mb = os.path.getsize(out_path) / 1024 / 1024
    print(f"  Saved {min(len(files), rows * cols)} images ({rows}x{cols}) -> {out_path} ({mb:.1f} MB)")


# ---- 批量处理 ----

def cmd_process(folder, grid_spec, last_spec=None):
    """加载已保存的裁剪区域，执行裁剪+拼接"""
    input_dir = os.path.join("pic", folder)
    crop_dir = os.path.join(CROPPED_DIR, folder)
    stitch_dir = os.path.join(STITCHED_DIR, folder)
    cfg_path = os.path.join(crop_dir, "region.json")

    if not os.path.exists(cfg_path):
        print(f"Error: region config not found at {cfg_path}. Run 'select_region' first.")
        sys.exit(1)

    with open(cfg_path, "r") as f:
        cfg = json.load(f)
    region = cfg["region"]

    try:
        grid_cols, grid_rows = map(int, grid_spec.split("*"))
    except ValueError:
        print(f"Error: invalid grid spec '{grid_spec}'. Use format like '3*8'")
        sys.exit(1)

    cropped_files = crop_all(input_dir, crop_dir, region)

    total = len(cropped_files)
    per_grid = grid_cols * grid_rows
    full_grids = total // per_grid
    remainder = total % per_grid

    os.makedirs(stitch_dir, exist_ok=True)

    # Full grids
    for g in range(full_grids):
        start = g * per_grid
        end = start + per_grid
        out_path = os.path.join(stitch_dir, f"stitched_{g + 1:02d}.png")
        stitch_grid(cropped_files[start:end], crop_dir, out_path, grid_rows, grid_cols)

    # Remainder
    if remainder > 0:
        remain_files = cropped_files[full_grids * per_grid:]
        if last_spec is not None:
            try:
                lc, lr = map(int, last_spec.split("*"))
            except ValueError:
                print(f"Error: invalid last-grid spec '{last_spec}'")
                sys.exit(1)
        else:
            msg = f"\nRemaining {remainder} image(s).\n" \
                  f"Enter last-grid size (e.g. '2*5') or press Enter to skip: "
            while True:
                sys.stdout.write(msg)
                sys.stdout.flush()
                last_spec = sys.stdin.readline().strip()
                if not last_spec:
                    print("Skipped last grid.")
                    return
                try:
                    lc, lr = map(int, last_spec.split("*"))
                except ValueError:
                    print("Invalid format, use e.g. '2*5'")
                    continue
                if lc * lr < remainder:
                    print(f"Grid {lc}*{lr} ({lc*lr}) is too small for "
                          f"{remainder} images. Try again.")
                    continue
                break

        if lc * lr < remainder:
            print(f"Error: last-grid {lc}*{lr} ({lc*lr}) too small for {remainder} images")
            sys.exit(1)
        out_path = os.path.join(stitch_dir, "stitched_last.png")
        stitch_grid(remain_files, crop_dir, out_path, lr, lc)

    print(f"\nDone: {folder}")


# ---- 入口 ----

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python crop_and_stitch.py select_region <folder>")
        print("  python crop_and_stitch.py process <folder> <cols>*<rows> [last_cols>*<last_rows>]")
        sys.exit(1)

    cmd = sys.argv[1]
    folder = sys.argv[2]

    if cmd == "select_region":
        cmd_select_region(folder)
    elif cmd == "process":
        if len(sys.argv) < 4:
            print("Error: 'process' needs grid spec, e.g. '3*8'")
            sys.exit(1)
        grid_spec = sys.argv[3]
        last_spec = sys.argv[4] if len(sys.argv) >= 5 else None
        cmd_process(folder, grid_spec, last_spec)
    else:
        print(f"Unknown command: {cmd}")
        print("Use 'select_region' or 'process'")
        sys.exit(1)


if __name__ == "__main__":
    main()
