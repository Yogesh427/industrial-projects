# Bulk Video To Image Extractor

This tool extracts frames from multiple videos and labels them with one name chosen at the start of the run.

## Folder setup

Create this structure:

```text
vedio/
  extractor.py
  requirements.txt
  videos/
    video-one.mp4
    video-two.mp4
```

Input must be a folder containing one or more video files. Image files are ignored and a folder with no videos is rejected. The tool is designed for bulk frame extraction from video, not single-image input.

## Install

From the `vedio` folder:

```powershell
python -m pip install -r requirements.txt
```

The extractor also works when launched from the project root. Its default folders are always `vedio/videos` and `vedio/extracted_images`.

## Run

```powershell
python extractor.py --input videos --output extracted_images
```

Or from the project root:

```powershell
python vedio\extractor.py
```

The tool asks for the label once:

```text
Enter the name after each #number (example: furina): furina
```

It then creates:

```text
extracted_images/
  #1furina.jpg
  #2furina.jpg
  #3furina.jpg
  ...
  manifest.csv
```

Numbering continues across all videos and stops at `#10000`. The name is never requested again during the same extraction run.

By default, the extractor targets 250 frames per second, which means it extracts every available source frame for normal videos. A video recorded at 30 FPS cannot provide 250 unique frames per second; the tool will not invent duplicate frames.

Set another target rate like this:

```powershell
python extractor.py --input videos --output extracted_images --frames-per-second 60
```

You can also set a lower safety limit while testing:

```powershell
python extractor.py --input videos --output extracted_images --max-images 100
```

`manifest.csv` records the generated label, source video, source frame number, timestamp, and output filename.
