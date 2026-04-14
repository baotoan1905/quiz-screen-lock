"""
main.py — QuizLock entry point.

Starts a PyQt6 application with:
  - System tray icon (Lock Now / Settings / Quit)
  - ScreenTimeManager that counts down screen time and triggers lock
  - LockScreen overlay dismissed only by answering quiz questions correctly
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
)

from admin_panel import AdminPanel, prompt_admin_password
from config import Config
from lock_screen import LockScreen
from timer_widget import TimerWidget

APP_STARTUP_NAME = "QuizLock"


def _startup_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    script_path = Path(__file__).resolve()
    return f'"{sys.executable}" "{script_path}"'


def apply_startup_setting(enabled: bool) -> None:
    if sys.platform != "win32":
        return
    import winreg

    run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, APP_STARTUP_NAME, 0, winreg.REG_SZ, _startup_command())
        else:
            try:
                winreg.DeleteValue(key, APP_STARTUP_NAME)
            except FileNotFoundError:
                pass


# ---------------------------------------------------------------------------
# Minimal programmatic icon (no external .ico needed)
# ---------------------------------------------------------------------------
def _make_tray_icon(locked: bool = False) -> QIcon:
    size = 32
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    color = QColor("#FF4444") if locked else QColor("#44AAFF")
    painter.setBrush(color)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(2, 2, size - 4, size - 4)
    painter.setPen(QColor("white"))
    font = QFont("Arial", 14, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "Q")
    painter.end()
    return QIcon(pix)


# ---------------------------------------------------------------------------
class ScreenTimeManager:
    """
    Tracks screen-time budget and triggers lock when it expires.
    Also handles receiving awarded minutes from the quiz.
    """

    def __init__(
        self,
        config: Config,
        lock_screen: LockScreen,
        timer_widget: TimerWidget,
        tray: QSystemTrayIcon,
    ) -> None:
        self._config = config
        self._lock_screen = lock_screen
        self._timer_widget = timer_widget
        self._tray = tray
        self._locked = False

        # Set initial budget
        budget_secs = config.daily_screen_minutes * 60
        self._timer_widget.set_budget(budget_secs)
        self._timer_widget.set_remaining(budget_secs)

        # Wire signals
        self._timer_widget.time_expired.connect(self._on_time_expired)
        self._timer_widget.tick.connect(self._on_tick)
        self._lock_screen.unlocked.connect(self._on_unlocked)
        self._lock_screen.question_reward_changed.connect(self._on_question_reward_changed)

    # ------------------------------------------------------------------
    def start(self) -> None:
        self._timer_widget.start()

    def lock_now(self) -> None:
        if not self._locked:
            self._locked = True
            self._timer_widget.pause()
            self._tray.setIcon(_make_tray_icon(locked=True))
            self._tray.setToolTip("QuizLock — LOCKED")
            self._lock_screen.show_lock()

    @property
    def is_locked(self) -> bool:
        return self._locked

    # ------------------------------------------------------------------
    def _on_time_expired(self) -> None:
        self._tray.showMessage(
            "QuizLock",
            "Screen time is up! Solve a quiz to unlock.",
            QSystemTrayIcon.MessageIcon.Warning,
            3000,
        )
        self.lock_now()

    def _on_tick(self, remaining: int) -> None:
        h, rem = divmod(remaining, 3600)
        m, s = divmod(rem, 60)
        self._tray.setToolTip(f"QuizLock — {h:02d}:{m:02d}:{s:02d} remaining")
        # Warn at 5 min
        if remaining == 300:
            self._tray.showMessage(
                "QuizLock",
                "5 minutes of screen time remaining.",
                QSystemTrayIcon.MessageIcon.Information,
                4000,
            )

    def _on_unlocked(self, minutes: int) -> None:
        self._locked = False
        if minutes > 0:
            # After a successful quiz while locked, allow only the earned window.
            self._timer_widget.set_remaining(minutes * 60)
        elif self._timer_widget.remaining_seconds <= 0:
            # Admin bypass from lock screen should not immediately relock.
            self._timer_widget.set_remaining(self._config.daily_screen_minutes * 60)
        self._timer_widget.resume()
        self._tray.setIcon(_make_tray_icon(locked=False))
        self._tray.setToolTip("QuizLock — running")
        if minutes > 0:
            msg = f"Unlocked! +{minutes} minutes added to your screen-time budget."
        else:
            msg = "Unlocked with admin access."
        self._tray.showMessage(
            "QuizLock",
            msg,
            QSystemTrayIcon.MessageIcon.Information,
            3000,
        )

    def _on_question_reward_changed(self, minutes: int, difficulty: str) -> None:
        self._timer_widget.set_current_question_reward(minutes, difficulty)


# ---------------------------------------------------------------------------
class QuizLockApp:
    def __init__(self, app: QApplication) -> None:
        self._app = app
        self._app.setQuitOnLastWindowClosed(False)
        self._config = Config()

        self._lock_screen = LockScreen(self._config)
        self._timer_widget = TimerWidget()
        self._tray = self._build_tray()

        self._manager = ScreenTimeManager(
            self._config,
            self._lock_screen,
            self._timer_widget,
            self._tray,
        )

        # Keep OS startup registration in sync with saved preference.
        try:
            apply_startup_setting(self._config.start_with_windows)
        except OSError:
            pass

    # ------------------------------------------------------------------
    def _build_tray(self) -> QSystemTrayIcon:
        tray = QSystemTrayIcon(_make_tray_icon(), self._app)
        tray.setToolTip("QuizLock — running")

        menu = QMenu()

        act_lock = menu.addAction("Lock Now")
        act_lock.triggered.connect(self._on_lock_now)

        act_settings = menu.addAction("Settings…")
        act_settings.triggered.connect(self._on_settings)

        menu.addSeparator()

        act_quit = menu.addAction("Quit QuizLock")
        act_quit.triggered.connect(self._on_quit)

        tray.setContextMenu(menu)
        tray.activated.connect(self._on_tray_activated)
        tray.show()
        return tray

    # ------------------------------------------------------------------
    def _on_lock_now(self) -> None:
        self._manager.lock_now()

    def _on_settings(self) -> None:
        if self._manager.is_locked:
            QMessageBox.warning(
                None,
                "QuizLock",
                "Settings are disabled while the screen is locked.",
            )
            return
        if not prompt_admin_password(self._config):
            return
        dlg = AdminPanel(self._config)
        if dlg.exec():
            # Apply new budget if changed
            new_secs = self._config.daily_screen_minutes * 60
            self._timer_widget.set_budget(new_secs)
            self._timer_widget.set_remaining(new_secs)
            try:
                apply_startup_setting(self._config.start_with_windows)
            except OSError as exc:
                QMessageBox.warning(
                    None,
                    "QuizLock",
                    f"Could not update Windows startup setting: {exc}",
                )
            if dlg.lock_now_requested:
                self._manager.lock_now()

    def _on_quit(self) -> None:
        if self._manager.is_locked:
            QMessageBox.warning(
                None,
                "QuizLock",
                "Cannot quit while locked. Solve the quiz to unlock first.",
            )
            return
        if not prompt_admin_password(self._config):
            return
        reply = QMessageBox.question(
            None,
            "Quit QuizLock",
            "Are you sure you want to quit QuizLock?\n"
            "Screen-time enforcement will be disabled.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._app.quit()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._on_settings()

    # ------------------------------------------------------------------
    def run(self) -> int:
        self._tray.showMessage(
            "QuizLock",
            "QuizLock is running in the system tray.",
            QSystemTrayIcon.MessageIcon.Information,
            2500,
        )
        if self._config.lock_on_startup:
            QTimer.singleShot(500, self._manager.lock_now)
        self._manager.start()
        return self._app.exec()


# ---------------------------------------------------------------------------
def main() -> None:
    app = QApplication(sys.argv)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(
            None,
            "QuizLock",
            "No system tray detected. QuizLock requires a system tray.",
        )
        sys.exit(1)
    ql = QuizLockApp(app)
    sys.exit(ql.run())


if __name__ == "__main__":
    main()
