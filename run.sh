#!/bin/bash
# run.sh - 批量处理 videos/ 中的所有视频
# 阶段 1: 批量抽帧
# 阶段 2: 统一参数（网格尺寸 + 余数最后一页）
# 阶段 3: 逐个框选裁剪区域（只选不裁）
# 阶段 4: 批量裁剪 + 拼接（无需交互）

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 收集所有视频文件
VIDEOS=()
while IFS= read -r -d '' f; do
    VIDEOS+=("$(basename "$f")")
done < <(find "$SCRIPT_DIR/videos" -maxdepth 1 -type f \( -iname "*.mp4" -o -iname "*.mov" -o -iname "*.avi" -o -iname "*.mkv" \) -print0 | sort -z)

if [ ${#VIDEOS[@]} -eq 0 ]; then
    echo "错误: videos/ 中没有视频文件"
    exit 1
fi

echo "============================================"
echo "  发现 ${#VIDEOS[@]} 个视频:"
for v in "${VIDEOS[@]}"; do echo "    $v"; done
echo "============================================"
echo ""

# ====== 阶段 1: 批量抽帧 ======
echo "============================================"
echo "  阶段 1/5: 批量抽帧"
echo "============================================"
echo ""

for VIDEO in "${VIDEOS[@]}"; do
    FOLDER="$(basename "$VIDEO" | sed 's/\.[^.]*$//')"
    echo "  >>> $VIDEO -> pic/$FOLDER/"
    python3 "$SCRIPT_DIR/extract_frames.py" "$VIDEO"
done

echo ""
echo "  抽帧完成!"
echo ""

# ====== 阶段 2: 统一参数 ======
echo "============================================"
echo "  阶段 2/5: 统一参数"
echo "============================================"
echo ""

read -p "  拼接网格尺寸 宽*高 (如 3*8): " GRID_SPEC
GRID_COLS=$(echo "$GRID_SPEC" | cut -d'*' -f1)
GRID_ROWS=$(echo "$GRID_SPEC" | cut -d'*' -f2)
PER_GRID=$((GRID_COLS * GRID_ROWS))
echo "  每页 $GRID_COLS x $GRID_ROWS = $PER_GRID 张"
echo ""

declare -A REMAINDERS
for VIDEO in "${VIDEOS[@]}"; do
    FOLDER="$(basename "$VIDEO" | sed 's/\.[^.]*$//')"
    FRAME_DIR="$SCRIPT_DIR/pic/$FOLDER"
    COUNT=$(find "$FRAME_DIR" -maxdepth 1 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) 2>/dev/null | wc -l)
    REM=$((COUNT % PER_GRID))
    if [ "$REM" -gt 0 ]; then
        REMAINDERS["$FOLDER"]="$REM"
    fi
done

declare -A LAST_GRIDS
if [ ${#REMAINDERS[@]} -gt 0 ]; then
    echo "  以下文件夹有余数，请逐个输入最后一页尺寸 (宽*高):"
    echo ""
    for FOLDER in "${!REMAINDERS[@]}"; do
        REM=${REMAINDERS[$FOLDER]}
        read -p "    $FOLDER (剩余 $REM 张): " LAST
        LAST_GRIDS["$FOLDER"]="$LAST"
    done
    echo ""
fi

# ====== 阶段 3: 逐个框选裁剪区域 ======
echo "============================================"
echo "  阶段 3/5: 框选裁剪区域"
echo "============================================"
echo "  (依次弹窗框选，关闭窗口后继续下一个)"
echo ""

for VIDEO in "${VIDEOS[@]}"; do
    FOLDER="$(basename "$VIDEO" | sed 's/\.[^.]*$//')"
    echo "  >>> 框选: $FOLDER"
    python3 "$SCRIPT_DIR/crop_and_stitch.py" select_region "$FOLDER"
    echo ""
done

echo "  框选完成!"
echo ""

# ====== 阶段 4: 批量裁剪 + 拼接 ======
echo "============================================"
echo "  阶段 4/5: 批量裁剪 + 拼接"
echo "============================================"
echo ""

TOTAL=${#VIDEOS[@]}
CURRENT=0

for VIDEO in "${VIDEOS[@]}"; do
    CURRENT=$((CURRENT + 1))
    FOLDER="$(basename "$VIDEO" | sed 's/\.[^.]*$//')"

    echo "  [$CURRENT/$TOTAL] 处理: $FOLDER"

    LAST="${LAST_GRIDS[$FOLDER]}"
    if [ -n "$LAST" ]; then
        python3 "$SCRIPT_DIR/crop_and_stitch.py" process "$FOLDER" "$GRID_SPEC" "$LAST"
    else
        python3 "$SCRIPT_DIR/crop_and_stitch.py" process "$FOLDER" "$GRID_SPEC"
    fi
    echo ""
done

echo "============================================"
echo "  全部完成! 共处理 $TOTAL 个视频"
echo "  拼接结果: pic/stitched/"
echo "============================================"
echo ""

# ====== 阶段 5: 清理中间文件 ======
echo "============================================"
echo "  阶段 5/5: 清理中间文件"
echo "============================================"
echo ""

for VIDEO in "${VIDEOS[@]}"; do
    FOLDER="$(basename "$VIDEO" | sed 's/\.[^.]*$//')"

    echo "  >>> 清理: $FOLDER"

    # 删除抽帧图片
    rm -rf "$SCRIPT_DIR/pic/$FOLDER"

    # 删除裁剪图片，保留 region.json
    CROP_DIR="$SCRIPT_DIR/pic/cropped/$FOLDER"
    if [ -d "$CROP_DIR" ]; then
        find "$CROP_DIR" -type f ! -name 'region.json' -delete
    fi

    echo "      完成"
done

echo ""
echo "  清理完成!"
