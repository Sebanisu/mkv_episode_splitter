# MKV Episode Splitter

A simple PySide6 GUI for splitting multi-episode MKV files into separate video files based on their chapter markers.

This is useful for Blu-ray or other releases where multiple episodes are stored in a single large MKV with each episode represented as a chapter.

I used AI to help make this.

## Features

- Opens an MKV file through a file picker or command-line argument.
- Reads chapter information using `mkvextract`.
- Generates a thumbnail for each chapter using `ffmpeg`.
- Displays chapters in a scrollable GUI.
- Click a chapter thumbnail to select a split point.
- Selected split points are highlighted in red.
- Chapter 1 cannot be selected as a split point.
- Splits the video using `mkvmerge`.
- Output files are created alongside the original MKV.
- Output files use the original filename with a numbered suffix.

For example:

```text
My Show.mkv
My Show-001.mkv
My Show-002.mkv
My Show-003.mkv
```

## Requirements

This application is intended for Linux and currently uses:

- Python 3
- PySide6
- MKVToolNix
  - `mkvextract`
  - `mkvmerge`
- FFmpeg

### Arch Linux

Install the required packages with:

```bash
sudo pacman -S python ffmpeg mkvtoolnix
```

Install PySide6 with:

```bash
sudo pacman -S python-pyside6
```

If `python-pyside6` is not available in your configured repositories, install PySide6 through another Python package source appropriate for your system.

## Running

From the project directory:

```bash
python mkv_episode_splitter.py
```

The application will open a file picker if no MKV is supplied.

You can also provide an MKV directly:

```bash
python mkv_episode_splitter.py "/path/to/video.mkv"
```

## Using the Splitter

1. Open the application.
2. Select an MKV file.
3. The application reads the chapter markers.
4. Thumbnails are generated for the chapters.
5. Click the chapters where a new episode should begin.
6. Selected chapters are highlighted in red.
7. Click **Split MKV**.
8. The resulting MKV files are written to the same directory as the source file.

Chapter 1 is automatically ignored because it represents the beginning of the original video.

## Desktop Launcher

The application can also be launched from the Linux application menu using a `.desktop` file.

Example:

```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=MKV Episode Splitter
Comment=Split multi-episode MKV files into individual episodes
Exec=python /home/sebanisu/dev/mkv_episode_splitter/mkv_episode_splitter.py
Path=/mnt/media/pool/Videos
Terminal=false
Categories=AudioVideo;Video;
Icon=video-x-generic
StartupNotify=true
```

The launcher uses `/mnt/media/pool/Videos` as its working directory while the Python application itself resides in:

```text
~/dev/mkv_episode_splitter/
```

## Project Structure

```text
mkv_episode_splitter/
├── LICENSE
├── README.md
└── mkv_episode_splitter.py
```

## How It Works

The application uses the MKV's chapter metadata to determine potential episode boundaries.

For each chapter:

1. `mkvextract` extracts the chapter timestamps.
2. The application calculates a midpoint between the current chapter and the next chapter.
3. `ffmpeg` extracts a single frame at that midpoint for use as a thumbnail.
4. The user selects the desired chapter boundaries.
5. `mkvmerge` splits the original MKV at the selected chapter numbers.

The original source file is not modified.

## License

This project is released into the public domain under the Unlicense. See the [LICENSE](LICENSE) file for full details.