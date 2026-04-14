"""
timer_widget.py — Floating countdown timer widget for QuizLock.
Shows remaining screen-time budget as a small always-on-top overlay
in the corner of the primary screen.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QPoint, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class TimerWidget(QWidget):
    """
    Small floating widget showing HH:MM:SS of remaining screen time.

    Signals:
        time_expired()  — emitted when the budget reaches zero
        tick(int)       — emitted every second with remaining_seconds
    """

    time_expired = pyqtSignal()
    tick = pyqtSignal(int)

    _MARGIN = 16    # px from screen edge
    _WIDTH  = 198
    _HEIGHT = 50

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._remaining_seconds: int = 0
        self._total_budget_seconds: int = 0
        self._current_question_minutes: int = 0
        self._current_difficulty: str = "moderate"
        self._running: bool = False
        self._setup_window()
        self._setup_ui()
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

    # ------------------------------------------------------------------
    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(self._WIDTH, self._HEIGHT)
        self._reposition()

    def _reposition(self) -> None:
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.right() - self._WIDTH - self._MARGIN
        y = screen.bottom() - self._HEIGHT - self._MARGIN
        self.move(QPoint(x, y))

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(1)

        row1 = QHBoxLayout()
        row1.setSpacing(4)
        self._total_lbl = QLabel("TOT 00:00:00")
        self._used_lbl = QLabel("USED 00:00:00")
        row1.addWidget(self._total_lbl)
        row1.addStretch()
        row1.addWidget(self._used_lbl)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(4)
        self._left_lbl = QLabel("LEFT 00:00:00")
        self._question_reward_lbl = QLabel("Q +0M MOD")
        row2.addWidget(self._left_lbl)
        row2.addStretch()
        row2.addWidget(self._question_reward_lbl)
        layout.addLayout(row2)

        for lbl in [self._total_lbl, self._used_lbl, self._left_lbl, self._question_reward_lbl]:
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet("color: white; font-size: 10px;")

        font = QFont("Courier New", 10, QFont.Weight.Bold)
        for lbl in [self._total_lbl, self._used_lbl, self._left_lbl]:
            lbl.setFont(font)

        self._question_reward_lbl.setStyleSheet("color: #CBE2FF; font-size: 10px; font-weight: bold;")

        self._refresh_label()

        self.setLayout(layout)

    # ------------------------------------------------------------------
    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(20, 25, 50, 200))
        painter.setPen(QPen(QColor(80, 120, 200, 160), 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 10, 10)

    # ------------------------------------------------------------------
    def set_remaining(self, seconds: int) -> None:
        self._remaining_seconds = max(0, seconds)
        self._refresh_label()

    def set_budget(self, seconds: int) -> None:
        self._total_budget_seconds = max(0, seconds)
        self._refresh_label()

    def set_current_question_reward(self, minutes: int, difficulty: str) -> None:
        self._current_question_minutes = max(0, minutes)
        self._current_difficulty = difficulty.strip().capitalize() if difficulty else "Moderate"
        self._refresh_label()

    def add_time(self, seconds: int) -> None:
        self._remaining_seconds = max(0, self._remaining_seconds + seconds)
        self._refresh_label()

    @property
    def remaining_seconds(self) -> int:
        return self._remaining_seconds

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._timer.start()
            self.show()

    def stop(self) -> None:
        self._running = False
        self._timer.stop()

    def pause(self) -> None:
        self._timer.stop()

    def resume(self) -> None:
        if self._running:
            self._timer.start()

    # ------------------------------------------------------------------
    def _tick(self) -> None:
        if self._remaining_seconds > 0:
            self._remaining_seconds -= 1
            self._refresh_label()
            self.tick.emit(self._remaining_seconds)
            if self._remaining_seconds == 0:
                self._timer.stop()
                self.time_expired.emit()
        else:
            self._timer.stop()
            self.time_expired.emit()

    def _refresh_label(self) -> None:
        def fmt(total: int) -> str:
            h, rem = divmod(max(0, total), 3600)
            m, sec = divmod(rem, 60)
            return f"{h:02d}:{m:02d}:{sec:02d}"

        def diff_short(name: str) -> str:
            lowered = name.strip().lower()
            if lowered.startswith("easy"):
                return "EZY"
            if lowered.startswith("diff") or lowered.startswith("hard"):
                return "HARD"
            return "MOD"

        left = self._remaining_seconds
        total = self._total_budget_seconds
        used = min(total, max(0, total - left))

        self._total_lbl.setText(f"Total {fmt(total)}")
        self._used_lbl.setText(f"Used {fmt(used)}")
        self._left_lbl.setText(f"Left {fmt(left)}")
        self._question_reward_lbl.setText(
            f"Q +{self._current_question_minutes}M {diff_short(self._current_difficulty)}"
        )

        # Turn left label red when under 5 minutes.
        if left < 300:
            self._left_lbl.setStyleSheet("color: #FF6060; font-size: 10px; font-weight: bold;")
        elif left < 900:
            self._left_lbl.setStyleSheet("color: #FFAA44; font-size: 10px; font-weight: bold;")
        else:
            self._left_lbl.setStyleSheet("color: #66FFB5; font-size: 10px; font-weight: bold;")
