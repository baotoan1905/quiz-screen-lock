"""
admin_panel.py — Admin settings dialog for QuizLock.
Password-protected dialog that lets a parent/admin configure
grade band, time budget, rewards, and other options.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from config import Config, GRADE_BANDS


def prompt_admin_password(config: Config, parent: Optional[QWidget] = None) -> bool:
    """Show a password dialog. Returns True if the entered password is correct."""
    pw, ok = QInputDialog.getText(
        parent,
        "Admin Access",
        "Enter admin password:",
        QLineEdit.EchoMode.Password,
    )
    if not ok:
        return False
    if pw == config.admin_password:
        return True
    QMessageBox.warning(parent, "Wrong Password", "Incorrect admin password.")
    return False


class AdminPanel(QDialog):
    """Settings dialog; only shown after successful password check."""

    def __init__(self, config: Config, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._config = config
        self._lock_now_requested = False
        self.setWindowTitle("QuizLock — Admin Settings")
        self.setMinimumWidth(460)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._build_ui()
        self._load_values()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(16)

        # --- Grade / Questions -------------------------------------------
        grp_quiz = QGroupBox("Quiz Settings")
        form_quiz = QFormLayout(grp_quiz)

        self._grade_combo = QComboBox()
        for key, label in GRADE_BANDS:
            self._grade_combo.addItem(label, key)
        form_quiz.addRow("Grade Band:", self._grade_combo)

        self._req_spin = QSpinBox()
        self._req_spin.setRange(1, 20)
        self._req_spin.setSuffix(" correct answer(s) to unlock")
        form_quiz.addRow("Required to Unlock:", self._req_spin)

        root.addWidget(grp_quiz)

        # --- Time Budget -------------------------------------------------
        grp_time = QGroupBox("Screen-Time Budget")
        form_time = QFormLayout(grp_time)

        self._daily_spin = QSpinBox()
        self._daily_spin.setRange(5, 480)
        self._daily_spin.setSuffix(" minutes / day")
        form_time.addRow("Daily Budget:", self._daily_spin)

        self._easy_reward_spin = QSpinBox()
        self._easy_reward_spin.setRange(1, 120)
        self._easy_reward_spin.setSuffix(" min")
        form_time.addRow("Easy Question Reward:", self._easy_reward_spin)

        self._moderate_reward_spin = QSpinBox()
        self._moderate_reward_spin.setRange(1, 120)
        self._moderate_reward_spin.setSuffix(" min")
        form_time.addRow("Moderate Question Reward:", self._moderate_reward_spin)

        self._difficult_reward_spin = QSpinBox()
        self._difficult_reward_spin.setRange(1, 120)
        self._difficult_reward_spin.setSuffix(" min")
        form_time.addRow("Difficult Question Reward:", self._difficult_reward_spin)

        root.addWidget(grp_time)

        # --- Startup & Behaviour ----------------------------------------
        grp_misc = QGroupBox("Behaviour")
        form_misc = QFormLayout(grp_misc)

        self._lock_startup_cb = QCheckBox("Lock screen on application startup")
        form_misc.addRow(self._lock_startup_cb)

        self._start_windows_cb = QCheckBox("Start QuizLock when Windows starts")
        form_misc.addRow(self._start_windows_cb)

        self._lock_now_btn = QPushButton("Lock Screen Now")
        self._lock_now_btn.clicked.connect(self._request_lock_now)
        form_misc.addRow(self._lock_now_btn)

        root.addWidget(grp_misc)

        # --- Change password --------------------------------------------
        grp_pw = QGroupBox("Security")
        form_pw = QFormLayout(grp_pw)
        self._change_pw_btn = QPushButton("Change Admin Password…")
        self._change_pw_btn.clicked.connect(self._change_password)
        form_pw.addRow(self._change_pw_btn)
        root.addWidget(grp_pw)

        # --- Buttons -----------------------------------------------------
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.setLayout(root)

    # ------------------------------------------------------------------
    def _load_values(self) -> None:
        # Grade band
        for i in range(self._grade_combo.count()):
            if self._grade_combo.itemData(i) == self._config.grade_band:
                self._grade_combo.setCurrentIndex(i)
                break
        self._req_spin.setValue(self._config.questions_required_to_unlock)
        self._daily_spin.setValue(self._config.daily_screen_minutes)
        rewards = self._config.minutes_per_difficulty
        self._easy_reward_spin.setValue(rewards["easy"])
        self._moderate_reward_spin.setValue(rewards["moderate"])
        self._difficult_reward_spin.setValue(rewards["difficult"])
        self._lock_startup_cb.setChecked(self._config.lock_on_startup)
        self._start_windows_cb.setChecked(self._config.start_with_windows)

    def _save_and_accept(self) -> None:
        self._config.grade_band = self._grade_combo.currentData()
        self._config.questions_required_to_unlock = self._req_spin.value()
        self._config.daily_screen_minutes = self._daily_spin.value()
        self._config.minutes_per_difficulty = {
            "easy": self._easy_reward_spin.value(),
            "moderate": self._moderate_reward_spin.value(),
            "difficult": self._difficult_reward_spin.value(),
        }
        self._config.lock_on_startup = self._lock_startup_cb.isChecked()
        self._config.start_with_windows = self._start_windows_cb.isChecked()
        self._config.save()
        self.accept()

    @property
    def lock_now_requested(self) -> bool:
        return self._lock_now_requested

    def _request_lock_now(self) -> None:
        self._save_and_accept()
        self._lock_now_requested = True

    def _change_password(self) -> None:
        old_pw, ok = QInputDialog.getText(
            self,
            "Change Password",
            "Enter current password:",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return
        if old_pw != self._config.admin_password:
            QMessageBox.warning(self, "Wrong Password", "Current password is incorrect.")
            return
        new_pw, ok = QInputDialog.getText(
            self,
            "Change Password",
            "Enter new password:",
            QLineEdit.EchoMode.Password,
        )
        if not ok or not new_pw.strip():
            return
        confirm, ok = QInputDialog.getText(
            self,
            "Change Password",
            "Confirm new password:",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return
        if new_pw != confirm:
            QMessageBox.warning(self, "Mismatch", "Passwords do not match.")
            return
        self._config.admin_password = new_pw
        self._config.save()
        QMessageBox.information(self, "Success", "Admin password changed successfully.")
