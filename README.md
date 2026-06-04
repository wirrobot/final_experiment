# 电子秤示数提取流水线

## 工作流概览

```
videos/  →  抽帧  →  旋转  →  裁剪  →  拼接  →  千问 
```

## 项目结构

```
final_experiment/
├── videos/                  # 原始视频（在此放入 .mp4 文件）
├── pic/                     # 图片中间产物
│   ├── {name}/              # 抽帧后的原始帧
│   ├── {name}_cropped/      # 裁剪后的帧
│   └── {name}_stitched/     # 拼接后的网格图
├── run.sh                   # 一键流水线脚本
├── extract_frames.py        # 视频抽帧
├── rotate_images.py         # 批量逆时针旋转 90°
├── crop_and_stitch.py       # 鼠标框选裁剪 + 网格拼接
├── requirements.txt         # Python 依赖
└── README.md
```

## 环境配置

```bash
pip install -r requirements.txt
```

## 使用步骤

### 1. 放入视频

把所有待处理 `.mp4` 视频文件放入 `videos/` 目录。

### 2. 一键运行

```bash
./run.sh
```

### 3. 按提示操作

```
Step 1: 输入视频文件名（如 try.mp4），自动抽帧到 pic/try/
Step 2: 按 Enter 旋转 90°，可多次按累积角度，按 d 结束
Step 3: 在首张图上拖拽框选裁剪区域，关闭窗口
Step 4: 输入拼接网格尺寸（宽*高，如 4*11）
        如有余数，再输入最后一页尺寸（如 4*10）
```

### 4. 得到结果

将 `pic/{name}_stitched/` 里的拼接图上传给千问（注意上传顺序），提示词：

> 每张图从左到右、从上到下，依次提取所有的示数

千问返回每张图中所有网格的数字读数列表。

## 单独使用各脚本

```bash
# 仅抽帧
python extract_frames.py try.mp4 0.1

# 仅旋转
python rotate_images.py try

# 仅裁剪+拼接
python crop_and_stitch.py try 3*8
```
