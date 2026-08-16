#!/usr/bin/env python3
import sys, os, subprocess, tempfile
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QScrollArea, QFileDialog, QMessageBox, QSizePolicy
)
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt, Signal, QProcess
from functools import partial

# -------------------------------
# Clickable thumbnail label
# -------------------------------
class ClickableLabel(QLabel):
    clicked = Signal()
    def mousePressEvent(self, event):
        self.clicked.emit()

# -------------------------------
# Chapter Thumbnail Widget
# -------------------------------
class ChapterThumbnail(QWidget):
    def __init__(self, chap_num, timestamp, image_path):
        super().__init__()
        self.chap_num = chap_num
        self.timestamp = timestamp
        self.selected = False  # split before this chapter
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        self.label = ClickableLabel()
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            self.label.setPixmap(pixmap.scaledToWidth(160, Qt.SmoothTransformation))
        else:
            self.label.setText("No Thumbnail")
            self.label.setAlignment(Qt.AlignCenter)
            self.label.setFixedHeight(100)

        self.text_label = QLabel(f"Chapter {chap_num} – {timestamp}")
        self.text_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.label)
        layout.addWidget(self.text_label)
        self.setLayout(layout)
        self.update_style()

    def toggle_selected(self):
        self.selected = not self.selected
        self.update_style()

    def update_style(self):
        if self.selected:
            self.setStyleSheet("border: 2px solid red; background-color: #ffdede;")
        else:
            self.setStyleSheet("border: 1px solid gray; background-color: none;")

# -------------------------------
# Main GUI
# -------------------------------
class MKVSplitter(QWidget):
    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.temp_dir = tempfile.mkdtemp(prefix="mkv_split_")
        self.thumb_dir = os.path.join(self.temp_dir, "thumbs")
        self.chapter_file = os.path.join(self.temp_dir, "chapters.txt")

        # Extract chapters
        self.extract_chapters()
        # Parse chapters
        self.chapters = self.parse_chapters()
        # Generate thumbnails
        self.generate_thumbnails()

        self.init_ui()

    # -------------------------------
    def extract_chapters(self):
        subprocess.run(
            ["mkvextract", "chapters", self.video_path, "-s"],
            stdout=open(self.chapter_file, "w")
        )

    def parse_chapters(self):
        chapters = []
        with open(self.chapter_file, "r") as f:
            for line in f:
                if line.startswith("CHAPTER") and "=" in line and "NAME" not in line:
                    chap_num = int(line[7:9])
                    start_time = line.strip().split("=")[1]
                    chapters.append((chap_num, start_time))
        return chapters

    def generate_thumbnails(self):
        os.makedirs(self.thumb_dir, exist_ok=True)
        for i, (chap_num, start_time) in enumerate(self.chapters):
            if i + 1 < len(self.chapters):
                end_time = self.chapters[i + 1][1]
            else:
                end_time = start_time
            h, m, s = map(float, start_time.split(":"))
            start_sec = h*3600 + m*60 + s
            h, m, s = map(float, end_time.split(":"))
            end_sec = h*3600 + m*60 + s
            midpoint = start_sec + (end_sec - start_sec)/2
            out_file = os.path.join(self.thumb_dir, f"Chapter_{chap_num:02}.jpg")
            if not os.path.exists(out_file):
                subprocess.run([
                    "ffmpeg", "-y", "-ss", str(midpoint), "-i", self.video_path,
                    "-frames:v", "1", out_file
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # -------------------------------
    def init_ui(self):
        self.setWindowTitle("MKV Splitter – Select Chapters to Split Before")
        layout = QVBoxLayout()

        instr_label = QLabel(
            "Instructions:\n"
            "- Click a chapter thumbnail to toggle splitting before this chapter.\n"
            "- Chapter 1 (0s) is ignored automatically.\n"
            "- Selected chapters are highlighted in red.\n"
            "- Click 'Split MKV' to perform the split."
        )
        instr_label.setWordWrap(True)
        instr_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(instr_label)

        # Scrollable thumbnails
        self.scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        self.thumb_widgets = {}

        for chap_num, ts in self.chapters:
            thumb_path = os.path.join(self.thumb_dir, f"Chapter_{chap_num:02}.jpg")
            chap_widget = ChapterThumbnail(chap_num, ts, thumb_path)
            if chap_num != 1:  # chapter 1 cannot be split
                chap_widget.label.clicked.connect(partial(self.toggle_chapter, chap_widget))
            scroll_layout.addWidget(chap_widget)
            self.thumb_widgets[chap_num] = chap_widget

        scroll_widget.setLayout(scroll_layout)
        self.scroll_area.setWidget(scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.scroll_area)

        # Split button
        self.btn_split = QPushButton("Split MKV")
        self.btn_split.clicked.connect(self.split_mkv)

        # Split button always at bottom
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_split)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.resize(800, 700)

    # -------------------------------
    def toggle_chapter(self, chap_widget):
        chap_widget.toggle_selected()

    # -------------------------------
    def split_mkv(self):
        selected_chaps = [
            str(chap_num)
            for chap_num, widget in self.thumb_widgets.items()
            if widget.selected
        ]

        if not selected_chaps:
            QMessageBox.warning(self, "Error", "No chapters selected for splitting!")
            return

        video = Path(self.video_path)

        # Output alongside the source video
        out_file = video.parent / f"{video.stem}-%03d.mkv"

        self.btn_split.setEnabled(False)
        self.btn_split.setText("Splitting...")

        self.process = QProcess(self)
        self.process.finished.connect(
            partial(self.split_finished, str(out_file))
        )

        self.process.start(
            "mkvmerge",
            [
                "-o",
                str(out_file),
                "--split",
                f"chapters:{','.join(selected_chaps)}",
                str(video),
            ],
        )

# -------------------------------
# Entry point
# -------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path, _ = QFileDialog.getOpenFileName(None, "Select MKV Video", "", "MKV Files (*.mkv)")
    if not video_path:
        sys.exit(0)
    splitter = MKVSplitter(video_path)
    splitter.show()
    sys.exit(app.exec())
