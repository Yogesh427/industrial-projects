from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

try:
    import cv2
except ImportError:
    print("OpenCV is missing. Install dependencies with: python -m pip install -r requirements.txt")
    raise SystemExit(1)

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".wmv", ".m4v", ".mpeg", ".mpg"}
DEFAULT_MAX_IMAGES = 10_000


def clean_label(value: str) -> str:
    label = re.sub(r"[^A-Za-z0-9_-]+", "", value.strip())
    if not label:
        raise ValueError("The label must contain at least one letter or number.")
    return label


def collect_videos(input_dir: Path) -> list[Path]:
    return sorted(
        path for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    )


def choose_videos(videos: list[Path]) -> list[Path] | None:
    print("\nAvailable videos:")
    for index, video in enumerate(videos, 1):
        print(f"  {index}. {video.name}")

    selection = input("Select videos by number (example: 1,3) or A for all: ").strip().lower()
    if selection in {"end", "exit", "q"}:
        return None
    if selection in {"a", "all"}:
        return videos
    if not selection:
        raise ValueError("No videos selected.")

    try:
        indexes = sorted({int(item.strip()) for item in selection.split(",")})
    except ValueError as error:
        raise ValueError("Use video numbers separated by commas, or enter A for all.") from error

    if any(index < 1 or index > len(videos) for index in indexes):
        raise ValueError(f"Choose numbers from 1 to {len(videos)}.")
    return [videos[index - 1] for index in indexes]


def extract_frames(
    videos: list[Path],
    output_dir: Path,
    label: str,
    target_fps: float,
    duration_seconds: float,
    max_images: int,
) -> int:
    if not videos:
        raise ValueError(
            "No video files were found. Put one or more videos in the input folder; "
            "single image files are not accepted."
        )

    output_dir = output_dir / label
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.csv"
    saved = 0

    with manifest_path.open("w", newline="", encoding="utf-8") as manifest_file:
        writer = csv.writer(manifest_file)
        writer.writerow(["label", "source_video", "frame_number", "timestamp_seconds", "output_file"])

        for video_path in videos:
            if saved >= max_images:
                break

            capture = cv2.VideoCapture(str(video_path))
            if not capture.isOpened():
                print(f"Skipped unreadable video: {video_path.name}")
                capture.release()
                continue

            fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
            frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            frame_step = max(1, round(fps / target_fps))
            max_frames_for_video = max(1, round(fps * duration_seconds))
            frame_index = 0

            while saved < max_images and frame_index < max_frames_for_video:
                success, frame = capture.read()
                if not success:
                    break

                if frame_index % frame_step == 0:
                    saved += 1
                    filename = f"#{saved}{label}.jpg"
                    destination = output_dir / filename
                    if not cv2.imwrite(str(destination), frame):
                        raise RuntimeError(f"Could not write image: {destination}")
                    timestamp = frame_index / fps
                    writer.writerow([label, video_path.name, frame_index, f"{timestamp:.3f}", filename])
                    print(f"[{saved}] {filename} <- {video_path.name} ({timestamp:.2f}s)")

                frame_index += 1

            capture.release()
            print(f"Finished {video_path.name}: {frame_count or frame_index} source frames")

    return saved


def parse_args() -> argparse.Namespace:
    tool_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Bulk-extract labeled frames from a folder of videos. Images are not accepted as input."
    )
    parser.add_argument("--input", type=Path, default=tool_dir / "videos", help="Folder containing videos")
    parser.add_argument("--output", type=Path, default=tool_dir / "extracted_images", help="Folder for extracted images")
    parser.add_argument("--frames-per-second", type=float, default=60.0, help="Target extraction rate; default 60 FPS")
    parser.add_argument("--duration-seconds", type=float, default=5.0, help="Seconds to extract from the start of each selected video; default 5")
    parser.add_argument("--every-seconds", type=float, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--max-images", type=int, default=DEFAULT_MAX_IMAGES, help="Maximum total images, default 10000")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.frames_per_second <= 0 or args.duration_seconds <= 0 or args.max_images <= 0:
        print("frames-per-second, duration-seconds, and max-images must be greater than zero.")
        return 2

    if not 3 <= args.duration_seconds <= 5:
        print("duration-seconds must be between 3 and 5.")
        return 2

    target_fps = args.frames_per_second
    if args.every_seconds is not None:
        if args.every_seconds <= 0:
            print("every-seconds must be greater than zero.")
            return 2
        target_fps = 1 / args.every_seconds

    if not args.input.exists() or not args.input.is_dir():
        print(f"Input folder does not exist: {args.input.resolve()}")
        print("Create it, put one or more video files inside it, and run again.")
        return 2

    videos = collect_videos(args.input)
    default_input = Path(__file__).resolve().parent / "videos"
    if not videos and args.input.resolve() == default_input.resolve():
        root_videos = collect_videos(Path(__file__).resolve().parent)
        if root_videos:
            args.input = Path(__file__).resolve().parent
            videos = root_videos
            print(f"Using videos found beside extractor.py: {args.input.resolve()}")

    print(f"Found {len(videos)} video file(s) in {args.input.resolve()}")
    print("This tool processes videos in bulk. It does not extract from a single image.")
    print("Type END at the video selection prompt whenever you want to close the extractor.")
    while True:
        try:
            selected_videos = choose_videos(videos)
        except ValueError as error:
            print(error)
            continue
        if selected_videos is None:
            print("Extractor ended by user.")
            return 0

        try:
            label = clean_label(input("Enter the name after each #number (example: furina): "))
        except (ValueError, EOFError) as error:
            print(error)
            continue

        print(f"All extracted files will use the label '{label}'. The name will not be requested again for this batch.")
        try:
            saved = extract_frames(selected_videos, args.output, label, target_fps, args.duration_seconds, args.max_images)
        except (ValueError, RuntimeError) as error:
            print(error)
            continue

        batch_output = args.output / label
        print(f"Done. Extracted {saved} image(s) into {batch_output.resolve()}")
        print(f"Naming format: #1{label}.jpg, #2{label}.jpg, ...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
