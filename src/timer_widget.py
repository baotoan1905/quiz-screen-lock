"""
timer_widget.py — Floating countdown timer widget for QuizLock.
Shows remaining screen-time budget as a small always-on-top overlay
in the corner of the primary screen.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QPoint, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget


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
    _WIDTH  = 160
    _HEIGHT = 70

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._remaining_seconds: int = 0
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
        y = screen.top() + self._MARGIN
        self.move(QPoint(x, y))

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(2)

        self._title_lbl = QLabel("Screen Time Left")
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_lbl.setStyleSheet(
            "color: rgba(200,220,255,0.85); font-size: 10px; font-weight: bold;"
        )
        layout.addWidget(self._title_lbl)

        self._time_lbl = QLabel("00:00:00")
        self._time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Courier New", 18, QFont.Weight.Bold)
        self._time_lbl.setFont(font)
        self._time_lbl.setStyleSheet("color: white;")
        layout.addWidget(self._time_lbl)

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

    def add_time(self, seconds: int) -> None:
        self._remaining_seconds = max(0, self._remaining_seconds + seconds)
        self._refresh_label()

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
        s = self._remaining_seconds
        h, rem = divmod(s, 3600)
        m, sec = divmod(rem, 60)
        self._time_lbl.setText(f"{h:02d}:{m:02d}:{sec:02d}")
        # Turn label red when under 5 minutes
        if s < 300:
            self._time_lbl.setStyleSheet("color: #FF6060;")
        elif s < 900:
            self._time_lbl.setStyleSheet("color: #FFAA44;")
        else:
            self._time_lbl.setStyleSheet("color: white;")
