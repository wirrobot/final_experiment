import cv2
import os
import sys


def extract_frames(video_name, interval=0.1):
    video_dir = "videos"
    pic_dir = "pic"

    video_path = os.path.join(video_dir, video_name)
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found!")
        return

    video_base = os.path.splitext(video_name)[0]
    output_dir = os.path.join(pic_dir, video_base)
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Cannot open video '{video_path}'")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * interval)
    print(f"Video FPS: {fps}, Extracting every {frame_interval} frames (interval: {interval}s)")

    frame_count = 0
    saved_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            frame_path = os.path.join(output_dir, f"frame_{saved_count:06d}.jpg")
            cv2.imwrite(frame_path, frame)
            saved_count += 1

        frame_count += 1

    cap.release()
    print(f"Done! Extracted {saved_count} frames to '{output_dir}'")
    return output_dir


if __name__ == "__main__":
    if len(sys.argv) < 2:
        video_name = input("Enter video name (e.g., try.mp4): ").strip()
    else:
        video_name = sys.argv[1]

    interval = float(sys.argv[2]) if len(sys.argv) > 2 else 0.2
    extract_frames(video_name, interval)
