import sys
import os

if sys.platform == "win32":
    import winreg

from PySide6.QtCore import Qt, QUrl, QPoint, QSettings
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QMenu,
    QDialog,
    QSlider,
    QLabel,
    QVBoxLayout,
    QPushButton
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


class AnimatedDesktop(QWidget):

    BORDER = 8

    def __init__(self):
        super().__init__()

        # =================================
        # WINDOW
        # =================================

        self.setWindowTitle("Animated Desktop")

        # Borderless, but NOT always on top
        self.setWindowFlags(
            Qt.FramelessWindowHint
        )

        self.setMinimumSize(200, 120)

        # =================================
        # LOCK
        # =================================

        self.locked = False

        # =================================
        # SAVED LAYOUT
        # =================================

        self.settings = QSettings(
            "Godxnemesis",
            "AnimatedDesktop"
        )

        self.opacity_value = int(
            self.settings.value("opacity", 100)
        )

        self.opacity_value = max(20, min(100, self.opacity_value))

        saved_geometry = self.settings.value("geometry")
        if saved_geometry:
            self.restoreGeometry(saved_geometry)

        self.setWindowOpacity(
            self.opacity_value / 100
        )

        # =================================
        # VIDEO
        # =================================

        self.video = QVideoWidget(self)

        # Fill the entire frame
        self.video.setAspectRatioMode(
            Qt.AspectRatioMode.IgnoreAspectRatio
        )

        self.video.setStyleSheet(
            "background-color: transparent;"
        )

        self.video.setGeometry(self.rect())

        # Enable right-click menu
        self.video.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )

        self.video.customContextMenuRequested.connect(
            self.show_context_menu
        )

        # =================================
        # MEDIA PLAYER
        # =================================

        self.player = QMediaPlayer(self)

        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)

        self.player.setVideoOutput(self.video)

        # Smooth automatic looping
        self.player.setLoops(
            QMediaPlayer.Loops.Infinite
        )

        # =================================
        # FIND VIDEO
        # =================================

        if getattr(sys, "frozen", False):
            # Running as EXE
            base_path = os.path.dirname(sys.executable)
        else:
            # Running normally with Python
            base_path = os.path.dirname(
                os.path.abspath(__file__)
            )

        video_path = os.path.join(
            base_path,
            "wallpaper.mp4"
        )

        print("Video:", video_path)

        if not os.path.exists(video_path):
            print("ERROR: wallpaper.mp4 not found")
            return

        # =================================
        # LOAD VIDEO
        # =================================

        self.player.setSource(
            QUrl.fromLocalFile(video_path)
        )

        self.player.mediaStatusChanged.connect(
            self.media_status_changed
        )

        # =================================
        # DRAGGING / RESIZING
        # =================================

        self.dragging = False
        self.resizing = False
        self.resize_edges = 0
        self.drag_position = QPoint()

        self.video.installEventFilter(self)

        # Start video
        self.player.play()

    # =====================================
    # VIDEO STATUS
    # =====================================

    def media_status_changed(self, status):

        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.player.play()

    # =====================================
    # RESIZE EVENT
    # =====================================

    def resizeEvent(self, event):

        self.video.setGeometry(self.rect())

        super().resizeEvent(event)

    # =====================================
    # FIND RESIZE EDGES
    # =====================================

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

    # =====================================
    # CURSOR
    # =====================================

    def update_cursor(self, edges):

        # Locked = no resize cursor
        if self.locked:
            self.setCursor(
                Qt.CursorShape.ArrowCursor
            )
            return

        if edges in (1, 2):
            self.setCursor(
                Qt.CursorShape.SizeHorCursor
            )

        elif edges in (4, 8):
            self.setCursor(
                Qt.CursorShape.SizeVerCursor
            )

        elif edges in (5, 10):
            self.setCursor(
                Qt.CursorShape.SizeBDiagCursor
            )

        elif edges in (6, 9):
            self.setCursor(
                Qt.CursorShape.SizeFDiagCursor
            )

        else:
            self.setCursor(
                Qt.CursorShape.ArrowCursor
            )

    # =====================================
    # RIGHT CLICK MENU
    # =====================================

    def show_context_menu(self, position):

        menu = QMenu(self)

        # -----------------------------
        # Lock / Unlock
        # -----------------------------

        if self.locked:
            lock_action = menu.addAction("🔓 Unlock")
        else:
            lock_action = menu.addAction("🔒 Lock")

        lock_action.triggered.connect(
            self.toggle_lock
        )

        # -----------------------------
        # Future options
        # -----------------------------

        menu.addSeparator()

        resize_action = menu.addAction("Resize")
        resize_action.setEnabled(not self.locked)

        recrop_action = menu.addAction("Recrop")
        recrop_action.setEnabled(not self.locked)

        opacity_action = menu.addAction("Opacity")
        opacity_action.setEnabled(not self.locked)
        opacity_action.triggered.connect(self.show_opacity_dialog)

        save_action = menu.addAction("Save Layout")
        save_action.triggered.connect(
            self.save_layout
        )

        # -----------------------------
        # Start with Windows
        # -----------------------------

        autostart_action = menu.addAction("Start with Windows")
        autostart_action.setCheckable(True)
        autostart_action.setChecked(
            self.is_autostart_enabled()
        )
        autostart_action.triggered.connect(
            self.toggle_autostart
        )

        # These are not implemented yet.
        resize_action.setEnabled(False)
        recrop_action.setEnabled(False)

        # -----------------------------
        # Close
        # -----------------------------

        menu.addSeparator()

        close_action = menu.addAction("Close")

        close_action.triggered.connect(
            self.close
        )

        # Show menu
        menu.exec(
            self.video.mapToGlobal(position)
        )

    # =====================================
    # SAVE LAYOUT
    # =====================================

    def save_layout(self):

        self.settings.setValue(
            "geometry",
            self.saveGeometry()
        )

        self.settings.setValue(
            "opacity",
            self.opacity_value
        )

        self.settings.sync()

        print("Layout saved")

    # =====================================
    # OPACITY
    # =====================================

    def show_opacity_dialog(self):

        dialog = QDialog(self)
        dialog.setWindowTitle("Opacity")
        dialog.setFixedWidth(300)

        layout = QVBoxLayout(dialog)

        value_label = QLabel(
            f"Opacity: {self.opacity_value}%"
        )
        layout.addWidget(value_label)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(20, 100)
        slider.setValue(self.opacity_value)
        slider.setSingleStep(5)
        slider.setPageStep(10)

        def update_opacity(value):
            self.opacity_value = value
            self.setWindowOpacity(value / 100)
            value_label.setText(
                f"Opacity: {value}%"
            )

        slider.valueChanged.connect(update_opacity)
        layout.addWidget(slider)

        close_button = QPushButton("Done")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.exec()


    # =====================================
    # START WITH WINDOWS
    # =====================================

    def is_autostart_enabled(self):

        if sys.platform != "win32":
            return False

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                0,
                winreg.KEY_READ
            )

            try:
                winreg.QueryValueEx(
                    key,
                    "AnimatedDesktop"
                )
                return True

            except FileNotFoundError:
                return False

            finally:
                winreg.CloseKey(key)

        except OSError:
            return False

    def toggle_autostart(self, checked):

        if sys.platform != "win32":
            print("Start with Windows is only available on Windows")
            return

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                0,
                winreg.KEY_SET_VALUE
            )

            if checked:

                if getattr(sys, "frozen", False):
                    command = f'"{sys.executable}"'
                else:
                    script_path = os.path.abspath(__file__)
                    command = f'"{sys.executable}" "{script_path}"'

                winreg.SetValueEx(
                    key,
                    "AnimatedDesktop",
                    0,
                    winreg.REG_SZ,
                    command
                )

                print("Start with Windows enabled")

            else:

                try:
                    winreg.DeleteValue(
                        key,
                        "AnimatedDesktop"
                    )
                except FileNotFoundError:
                    pass

                print("Start with Windows disabled")

            winreg.CloseKey(key)

        except OSError as error:
            print("Could not change Start with Windows:", error)

    # =====================================
    # LOCK / UNLOCK
    # =====================================

    def toggle_lock(self):

        self.locked = not self.locked

        # Stop any active movement
        self.dragging = False
        self.resizing = False
        self.resize_edges = 0

        # Reset cursor
        self.setCursor(
            Qt.CursorShape.ArrowCursor
        )

        if self.locked:
            print("Widget locked")
        else:
            print("Widget unlocked")

    # =====================================
    # MOUSE EVENT FILTER
    # =====================================

    def eventFilter(self, obj, event):

        if obj == self.video:

            # -----------------------------
            # LEFT CLICK
            # -----------------------------

            if event.type() == event.Type.MouseButtonPress:

                if event.button() == Qt.MouseButton.LeftButton:

                    # Locked = don't allow movement/resizing
                    if self.locked:
                        return True

                    pos = event.position().toPoint()

                    self.resize_edges = (
                        self.get_resize_edges(pos)
                    )

                    if self.resize_edges:

                        self.resizing = True

                        self.drag_position = (
                            event.globalPosition().toPoint()
                        )

                    else:

                        self.dragging = True

                        self.drag_position = (
                            event.globalPosition().toPoint()
                            - self.frameGeometry().topLeft()
                        )

                    return True

            # -----------------------------
            # MOUSE MOVE
            # -----------------------------

            elif event.type() == event.Type.MouseMove:

                pos = event.position().toPoint()

                # Locked
                if self.locked:
                    self.setCursor(
                        Qt.CursorShape.ArrowCursor
                    )
                    return False

                # Resizing
                if self.resizing:

                    self.resize_window(
                        event.globalPosition().toPoint()
                    )

                    return True

                # Dragging
                elif self.dragging:

                    self.move(
                        event.globalPosition().toPoint()
                        - self.drag_position
                    )

                    return True

                # Normal cursor
                else:

                    edges = self.get_resize_edges(pos)

                    self.update_cursor(edges)

            # -----------------------------
            # LEFT BUTTON RELEASE
            # -----------------------------

            elif event.type() == event.Type.MouseButtonRelease:

                self.dragging = False
                self.resizing = False
                self.resize_edges = 0

                return True

        return super().eventFilter(obj, event)

    # =====================================
    # RESIZE WINDOW
    # =====================================

    def resize_window(self, global_pos):

        # Safety check
        if self.locked:
            return

        rect = self.geometry()

        dx = (
            global_pos.x()
            - self.drag_position.x()
        )

        dy = (
            global_pos.y()
            - self.drag_position.y()
        )

        # Left
        if self.resize_edges & 1:

            new_width = rect.width() - dx

            if new_width >= self.minimumWidth():
                rect.setLeft(
                    rect.left() + dx
                )

        # Right
        if self.resize_edges & 2:

            new_width = rect.width() + dx

            if new_width >= self.minimumWidth():
                rect.setRight(
                    rect.right() + dx
                )

        # Top
        if self.resize_edges & 4:

            new_height = rect.height() - dy

            if new_height >= self.minimumHeight():
                rect.setTop(
                    rect.top() + dy
                )

        # Bottom
        if self.resize_edges & 8:

            new_height = rect.height() + dy

            if new_height >= self.minimumHeight():
                rect.setBottom(
                    rect.bottom() + dy
                )

        self.setGeometry(rect)

        self.drag_position = global_pos


# =========================================
# START APPLICATION
# =========================================

app = QApplication(sys.argv)

window = AnimatedDesktop()
window.show()

sys.exit(app.exec())