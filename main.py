import sys
import os

from PySide6.QtCore import Qt, QUrl, QPoint
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtMultimedia import (
    QMediaPlayer,
    QAudioOutput,
    QMediaMetaData
)
from PySide6.QtMultimediaWidgets import QVideoWidget


class AnimatedDesktop(QWidget):

    BORDER = 8

    def __init__(self):
        super().__init__()

        # -----------------------------
        # Window
        # -----------------------------
        self.setWindowTitle("Animated Desktop")

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )

        self.setMinimumSize(200, 120)

        # -----------------------------
        # Video widget
        # -----------------------------
        self.video = QVideoWidget(self)

        self.video.setAspectRatioMode(
            Qt.AspectRatioMode.IgnoreAspectRatio
        )

        self.video.setStyleSheet(
            "background-color: transparent;"
        )

        self.video.setGeometry(self.rect())

        # -----------------------------
        # Player
        # -----------------------------
        self.player = QMediaPlayer(self)

        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)

        self.player.setVideoOutput(self.video)

        # -----------------------------
        # Find video
        # -----------------------------
        if getattr(sys, "frozen", False):
    # Running as EXE
            base_path = os.path.dirname(sys.executable)
        else:
    # Running normally with Python
            base_path = os.path.dirname(os.path.abspath(__file__))

        video_path = os.path.join(
            base_path,
            "wallpaper.mp4"
        )

        print("Video:", video_path)

        if not os.path.exists(video_path):
            print("ERROR: wallpaper.mp4 not found")
            return

        # -----------------------------
        # Load video
        # -----------------------------
        self.player.setSource(
            QUrl.fromLocalFile(video_path)
        )

        self.player.mediaStatusChanged.connect(
            self.media_status_changed
        )

        # -----------------------------
        # Dragging / resizing
        # -----------------------------
        self.dragging = False
        self.resizing = False
        self.resize_edges = 0
        self.drag_position = QPoint()

        self.video.installEventFilter(self)

        self.player.play()

    # =================================
    # VIDEO
    # =================================

    def media_status_changed(self, status):

        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.player.play()
            
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:

            self.player.setPosition(0)
            self.player.play()

    # =================================
    # RESIZE
    # =================================

    def resizeEvent(self, event):

        self.video.setGeometry(self.rect())

        super().resizeEvent(event)

    def get_resize_edges(self, pos):

        edges = 0

        if pos.x() <= self.BORDER:
            edges |= 1

        if pos.x() >= self.width() - self.BORDER:
            edges |= 2

        if pos.y() <= self.BORDER:
            edges |= 4

        if pos.y() >= self.height() - self.BORDER:
            edges |= 8

        return edges

    def update_cursor(self, edges):

        if edges in (1, 2):
            self.setCursor(Qt.CursorShape.SizeHorCursor)

        elif edges in (4, 8):
            self.setCursor(Qt.CursorShape.SizeVerCursor)

        elif edges in (5, 10):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)

        elif edges in (6, 9):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)

        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    # =================================
    # MOUSE
    # =================================

    def eventFilter(self, obj, event):

        if obj == self.video:

            if event.type() == event.Type.MouseButtonPress:

                if event.button() == Qt.MouseButton.LeftButton:

                    pos = event.position().toPoint()

                    self.resize_edges = self.get_resize_edges(pos)

                    if self.resize_edges:
                        self.resizing = True
                        self.drag_position = event.globalPosition().toPoint()

                    else:
                        self.dragging = True
                        self.drag_position = (
                            event.globalPosition().toPoint()
                            - self.frameGeometry().topLeft()
                        )

                    return True

            elif event.type() == event.Type.MouseMove:

                pos = event.position().toPoint()

                if self.resizing:

                    self.resize_window(
                        event.globalPosition().toPoint()
                    )

                    return True

                elif self.dragging:

                    self.move(
                        event.globalPosition().toPoint()
                        - self.drag_position
                    )

                    return True

                else:

                    edges = self.get_resize_edges(pos)
                    self.update_cursor(edges)

            elif event.type() == event.Type.MouseButtonRelease:

                self.dragging = False
                self.resizing = False
                self.resize_edges = 0

                return True

        return super().eventFilter(obj, event)

    # =================================
    # ACTUAL RESIZING
    # =================================

    def resize_window(self, global_pos):

        rect = self.geometry()

        dx = global_pos.x() - self.drag_position.x()
        dy = global_pos.y() - self.drag_position.y()

        if self.resize_edges & 1:
            new_width = rect.width() - dx

            if new_width >= self.minimumWidth():

                rect.setLeft(rect.left() + dx)

        if self.resize_edges & 2:
            new_width = rect.width() + dx

            if new_width >= self.minimumWidth():

                rect.setRight(rect.right() + dx)

        if self.resize_edges & 4:
            new_height = rect.height() - dy

            if new_height >= self.minimumHeight():

                rect.setTop(rect.top() + dy)

        if self.resize_edges & 8:
            new_height = rect.height() + dy

            if new_height >= self.minimumHeight():

                rect.setBottom(rect.bottom() + dy)

        self.setGeometry(rect)

        self.drag_position = global_pos


# =====================================
# START APPLICATION
# =====================================

app = QApplication(sys.argv)

window = AnimatedDesktop()
window.show()

sys.exit(app.exec())