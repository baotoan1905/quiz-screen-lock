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
from admin_panel import AdminPanel, prompt_admin_password
from quiz_engine import QuizEngine
import keyboard_hook


class LockScreen(QWidget):
    """
    Fullscreen lock overlay.

    Signals:
        unlocked(int)  — emitted with minutes_awarded when quiz passed
        question_reward_changed(int, str) — emitted when current question reward changes
    """

    unlocked = pyqtSignal(int)
    question_reward_changed = pyqtSignal(int, str)

    def __init__(self, config: Config, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._config = config
        self._secondary_blockers: list[QWidget] = []
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
        # Main quiz window is shown on the primary monitor.
        primary = QApplication.primaryScreen()
        if primary is not None:
            self.setGeometry(primary.geometry())

    def _clear_secondary_blockers(self) -> None:
        for blocker in self._secondary_blockers:
            blocker.hide()
            blocker.deleteLater()
        self._secondary_blockers.clear()

    def _show_secondary_blockers(self) -> None:
        self._clear_secondary_blockers()
        primary = QApplication.primaryScreen()
        for screen in QApplication.screens():
            if screen == primary:
                continue
            blocker = QWidget()
            blocker.setWindowTitle("QuizLock")
            blocker.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.Tool
            )
            blocker.setStyleSheet("background-color: rgb(15, 20, 40);")
            blocker.setGeometry(screen.geometry())
            blocker.show()
            blocker.raise_()
            blocker.activateWindow()
            self._secondary_blockers.append(blocker)

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

        admin_btn = QPushButton("Parent/Admin Access")
        admin_btn.setFixedWidth(220)
        admin_btn.setStyleSheet(
            "QPushButton {"
            "background: rgba(255,255,255,0.12); color: #FFFFFF;"
            "border: 1px solid rgba(255,255,255,0.35); border-radius: 8px;"
            "padding: 8px 12px; font-size: 13px;"
            "}"
            "QPushButton:hover { background: rgba(120,170,255,0.35); }"
        )
        admin_btn.clicked.connect(self._on_admin_access)
        layout.addWidget(admin_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(16)

        # Quiz widget (centred, max 700 px wide)
        self._quiz = QuizEngine(self._config, self)
        self._quiz.setMaximumWidth(720)
        self._quiz.quiz_passed.connect(self._on_quiz_passed)
        self._quiz.question_reward_changed.connect(self._on_question_reward_changed)

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
        self._show_secondary_blockers()
        primary = QApplication.primaryScreen()
        if primary is not None:
            self.setGeometry(primary.geometry())
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

    def _on_quiz_passed(self, minutes: int) -> None:
        keyboard_hook.unlock()
        self.hide()
        self._clear_secondary_blockers()
        self.unlocked.emit(minutes)

    def _on_question_reward_changed(self, minutes: int, difficulty: str) -> None:
        self.question_reward_changed.emit(minutes, difficulty)

    def _on_admin_access(self) -> None:
        if not prompt_admin_password(self._config, self):
            return
        dlg = AdminPanel(self._config, self)
        dlg.exec()
        keyboard_hook.unlock()
        self.hide()
        self._clear_secondary_blockers()
        self.unlocked.emit(0)
