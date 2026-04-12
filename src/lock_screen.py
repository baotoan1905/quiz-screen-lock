"""
lock_screen.py — Fullscreen always-on-top overlay for QuizLock.
Uses PyQt6; covers all monitors; cannot be dismissed with Escape or Alt-F4.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QLinearGradient, QGradient
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config import Config
from quiz_engine import QuizEngine
import keyboard_hook


class LockScreen(QWidget):
    """
    Fullscreen lock overlay.

    Signals:
        unlocked(int)  — emitted with minutes_awarded when quiz passed
    """

    unlocked = pyqtSignal(int)

    def __init__(self, config: Config, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._config = config
        self._setup_window()
        self._setup_ui()

    # ------------------------------------------------------------------
    def _setup_window(self) -> None:
        self.setWindowTitle("QuizLock")
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool           # keeps it off Alt-Tab list
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        # Cover the entire virtual desktop (all monitors)
        desktop = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(desktop)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 40, 0, 40)

        # Header
        header = QLabel("🔒  Screen Locked")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet(
            "color: white; font-size: 32px; font-weight: bold; margin-bottom: 4px;"
        )
        layout.addWidget(header)

        sub = QLabel("Answer the question correctly to unlock your screen.")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #CCCCCC; font-size: 15px; margin-bottom: 20px;")
        layout.addWidget(sub)

        # Quiz widget (centred, max 700 px wide)
        self._quiz = QuizEngine(self._config, self)
        self._quiz.setMaximumWidth(720)
        self._quiz.quiz_passed.connect(self._on_quiz_passed)

        # Wrap in a centering layout
        from PyQt6.QtWidgets import QHBoxLayout
        hbox = QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(self._quiz)
        hbox.addStretch()
        layout.addLayout(hbox)
        layout.addStretch()

        self.setLayout(layout)

    # ------------------------------------------------------------------
    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor(15, 20, 40))
        grad.setColorAt(1.0, QColor(30, 10, 60))
        painter.fillRect(self.rect(), grad)

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        # Swallow all key events on the widget level too
        event.accept()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        # Prevent closing via system menus while locked
        event.ignore()

    # ------------------------------------------------------------------
    def show_lock(self) -> None:
        """Display the lock screen and install keyboard hook."""
        self._quiz.reset()
        keyboard_hook.lock()
        # Re-cover all monitors in case resolution changed
        desktop = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(desktop)
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

    def _on_quiz_passed(self, minutes: int) -> None:
        keyboard_hook.unlock()
        self.hide()
        self.unlocked.emit(minutes)
