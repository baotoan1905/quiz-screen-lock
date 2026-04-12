"""
config.py — QuizLock settings management.
Reads/writes ~/.quizlock/config.json.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".quizlock"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS: dict[str, Any] = {
    "admin_password": "quizlock123",
    "grade_band": "grade_5_6",          # which question pool to draw from
    "daily_screen_minutes": 60,         # total screen-time budget per day
    "minutes_per_correct": 5,           # screen time awarded per correct answer
    "questions_required_to_unlock": 1,  # correct answers needed to unlock once
    "lock_on_startup": False,
    "start_with_windows": False,
    "tray_icon_visible": True,
}

GRADE_BANDS = [
    ("grade_1_2",   "Grades 1–2"),
    ("grade_3_4",   "Grades 3–4"),
    ("grade_5_6",   "Grades 5–6"),
    ("grade_7_9",   "Grades 7–9"),
    ("grade_10_plus", "Grades 10–12"),
]


class Config:
    def __init__(self) -> None:
        self._data: dict[str, Any] = dict(DEFAULTS)
        self.load()

    # ------------------------------------------------------------------
    def load(self) -> None:
        if CONFIG_FILE.exists():
            try:
                with CONFIG_FILE.open("r", encoding="utf-8") as fh:
                    stored = json.load(fh)
                self._data.update(stored)
            except (json.JSONDecodeError, OSError):
                pass  # keep defaults

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with CONFIG_FILE.open("w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2)

    # ------------------------------------------------------------------
    # Typed accessors
    # ------------------------------------------------------------------
    @property
    def admin_password(self) -> str:
        return str(self._data["admin_password"])

    @admin_password.setter
    def admin_password(self, v: str) -> None:
        self._data["admin_password"] = v

    @property
    def grade_band(self) -> str:
        return str(self._data["grade_band"])

    @grade_band.setter
    def grade_band(self, v: str) -> None:
        self._data["grade_band"] = v

    @property
    def daily_screen_minutes(self) -> int:
        return int(self._data["daily_screen_minutes"])

    @daily_screen_minutes.setter
    def daily_screen_minutes(self, v: int) -> None:
        self._data["daily_screen_minutes"] = max(1, v)

    @property
    def minutes_per_correct(self) -> int:
        return int(self._data["minutes_per_correct"])

    @minutes_per_correct.setter
    def minutes_per_correct(self, v: int) -> None:
        self._data["minutes_per_correct"] = max(1, v)

    @property
    def questions_required_to_unlock(self) -> int:
        return int(self._data["questions_required_to_unlock"])

    @questions_required_to_unlock.setter
    def questions_required_to_unlock(self, v: int) -> None:
        self._data["questions_required_to_unlock"] = max(1, v)

    @property
    def lock_on_startup(self) -> bool:
        return bool(self._data["lock_on_startup"])

    @lock_on_startup.setter
    def lock_on_startup(self, v: bool) -> None:
        self._data["lock_on_startup"] = v

    @property
    def start_with_windows(self) -> bool:
        return bool(self._data["start_with_windows"])

    @start_with_windows.setter
    def start_with_windows(self, v: bool) -> None:
        self._data["start_with_windows"] = v

    @property
    def tray_icon_visible(self) -> bool:
        return bool(self._data["tray_icon_visible"])

    @tray_icon_visible.setter
    def tray_icon_visible(self, v: bool) -> None:
        self._data["tray_icon_visible"] = v

    # ------------------------------------------------------------------
    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value
