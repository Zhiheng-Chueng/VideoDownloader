# VideoDownloader

Simple multi-platform video downloader with a GUI, format selection, and HLS support.

## Features
- GUI with format selection
- HLS segment download with concurrency
- Header/cookie injection for protected streams
- Optional ffmpeg remux/re-encode stage

## Requirements
- Python 3.10+
- ffmpeg and yt-dlp binaries in `bin/`

## Setup
```bash
pip install -r requirements.txt
```

## Run
```bash
python main.py
```

## Notes
- Downloads are saved to `downloads/`.
- HLS download timing is reported before ffmpeg processing starts.
