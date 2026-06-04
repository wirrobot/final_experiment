#!/bin/bash
# run.sh - 一键处理流水线：抽帧 → 旋转 → 裁剪 → 拼接

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ====== Step 1: 指定视频 + 抽帧 ======
echo "============================================"
echo "  Step 1: 指定视频 + 抽帧"
echo "============================================"
echo ""
echo "videos/ 下的视频文件:"
ls "$SCRIPT_DIR/videos/" 2>/dev/null || echo "  (空)"
echo ""
read -p "请输入视频文件名 (如 try.mp4): " VIDEO
if [ ! -f "$SCRIPT_DIR/videos/$VIDEO" ]; then
    echo "错误: videos/$VIDEO 不存在"
    exit 1
fi

FOLDER="$(basename "$VIDEO" | sed 's/\.[^.]*$//')"

echo ""
echo "抽帧中..."
python3 "$SCRIPT_DIR/extract_frames.py" "$VIDEO"
echo ""

# ====== Step 2: 旋转 ======
echo "============================================"
echo "  Step 2: 旋转"
echo "============================================"
echo ""
echo "每次按 Enter 逆时针旋转 90°，按 d + Enter 结束"
echo "（不旋转则直接按 d 跳过）"
echo ""

while true; do
    echo -n "操作?  Enter=旋转一次  d=结束: "
    read -r KEY
    if [ "$KEY" = "d" ]; then
        break
    fi
    python3 "$SCRIPT_DIR/rotate_images.py" "$FOLDER"
done

# ====== Step 3 & 4: 裁剪 + 拼接 ======
echo ""
echo "============================================"
echo "  Step 3 & 4: 裁剪 + 拼接"
echo "============================================"
echo ""
read -p "拼接网格尺寸 宽*高 (如 3*8): " GRID

python3 "$SCRIPT_DIR/crop_and_stitch.py" "$FOLDER" "$GRID"

echo ""
echo "全部完成!"
