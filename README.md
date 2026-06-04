# 电子秤示数提取流水线

## 工作流概览

```
videos/  →  抽帧  →  框选裁剪区  →  批量裁剪拼接  →  千问 OCR
```

## 项目结构

```
final_experiment/
├── videos/                  # 原始视频（在此放入 .mp4 / .mov 等）
├── pic/                     # 图片中间产物
│   ├── {name}/              # 抽帧后的原始帧
│   ├── cropped/{name}/      # 裁剪后的帧 + region.json
│   └── stitched/{name}/     # 拼接后的网格图
├── run.sh                   # 一键流水线脚本
├── extract_frames.py        # 视频抽帧
├── crop_and_stitch.py       # 框选裁剪 + 网格拼接
├── rotate_images.py         # 批量逆时针旋转 90°（备用）
├── requirements.txt         # Python 依赖
└── README.md
```

## 环境配置

```bash
pip install -r requirements.txt
```

## 使用步骤

### 1. 放入视频

把所有待处理视频文件放入 `videos/` 目录。

### 2. 一键运行

```bash
./run.sh
```

### 3. 按提示操作

```
阶段 1: 所有视频自动批量抽帧（无需交互）
阶段 2: 输入网格尺寸（宽*高，如 3*8）
        如有余数，统一输入每个文件夹的最后一页尺寸
阶段 3: 逐个弹窗框选裁剪区域（关闭窗口继续下一个）
阶段 4: 自动批量裁剪 + 拼接（无需交互）
```

### 4. 喂给千问

将 `pic/stitched/` 里的拼接图上传给千问，提示词：

> 每张图从左到右、从上到下，依次提取所有的示数

### 5. 结果

千问返回每张图中所有网格的数字读数列表。

## 单独使用各脚本

```bash
# 仅抽帧
python extract_frames.py try.mp4 0.2

# 框选裁剪区域
python crop_and_stitch.py select_region try

# 裁剪+拼接（需先完成框选）
python crop_and_stitch.py process try 3*8
python crop_and_stitch.py process try 3*8 2*5
```
