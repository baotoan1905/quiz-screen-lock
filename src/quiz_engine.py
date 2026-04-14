"""
quiz_engine.py — Quiz logic widget for QuizLock.
Displays a random question from the configured grade band.
Emits quiz_passed(minutes_awarded) when the user answers correctly
enough times; emits quiz_failed on wrong answer.
"""
from __future__ import annotations

import random
from typing import Optional

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config import Config
from questions import QUESTIONS


class QuizEngine(QWidget):
    """
    Self-contained quiz widget.
    Signals:
        quiz_passed(int)  — emitted with minutes_awarded when enough correct answers
        quiz_failed()     — emitted after a wrong answer (caller may choose to re-show)
        question_reward_changed(int, str) — emitted when current question/reward changes
    """

    quiz_passed = pyqtSignal(int)   # minutes to award
    quiz_failed = pyqtSignal()
    question_reward_changed = pyqtSignal(int, str)

    _LEVELS = ("easy", "moderate", "difficult")

    def __init__(self, config: Config, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._config = config
        self._correct_streak = 0
        self._round_earned_minutes = 0
        self._current_answer: str = ""
        self._current_difficulty = "moderate"
        self._current_question_minutes = self._config.minutes_for_difficulty(self._current_difficulty)
        self._current_question_key = ""
        self._difficulty_subject_cycles: dict[str, list[str]] = {k: [] for k in self._LEVELS}
        self._difficulty_pools: dict[str, list[dict]] = {k: [] for k in self._LEVELS}
        self._pool_band: str = ""
        self._setup_ui()
        self._load_question()

    # ------------------------------------------------------------------
    def _setup_ui(self) -> None:
        self.setObjectName("QuizEngine")
        self.setStyleSheet("""
            QWidget#QuizEngine {
                background: transparent;
            }
            QLabel#question_label {
                color: #FFFFFF;
                font-size: 22px;
                font-weight: bold;
            }
            QLabel#subject_label {
                color: #AADDFF;
                font-size: 13px;
                letter-spacing: 1px;
            }
            QLabel#feedback_label {
                font-size: 16px;
                font-weight: bold;
                min-height: 24px;
            }
            QLabel#difficulty_label {
                color: #FFE9A9;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton.choice_btn {
                background: rgba(255,255,255,0.12);
                color: #FFFFFF;
                border: 2px solid rgba(255,255,255,0.25);
                border-radius: 10px;
                padding: 12px 20px;
                font-size: 16px;
                text-align: left;
            }
            QPushButton.choice_btn:hover {
                background: rgba(100,160,255,0.35);
                border-color: #64A0FF;
            }
            QPushButton.choice_btn:pressed {
                background: rgba(100,160,255,0.55);
            }
            QPushButton.diff_btn {
                background: rgba(255,255,255,0.09);
                color: #E6F0FF;
                border: 1px solid rgba(255,255,255,0.28);
                border-radius: 9px;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton.diff_btn:checked {
                background: rgba(255,210,90,0.35);
                border: 2px solid rgba(255,230,140,0.95);
                color: #FFFFFF;
            }
            QPushButton.change_btn {
                background: rgba(255,255,255,0.09);
                color: #E6F0FF;
                border: 1px solid rgba(255,255,255,0.28);
                border-radius: 9px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QPushButton.change_btn:hover,
            QPushButton.diff_btn:hover {
                background: rgba(120,170,255,0.30);
                border-color: #7AA4FF;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(40, 30, 40, 30)

        self._subject_label = QLabel()
        self._subject_label.setObjectName("subject_label")
        self._subject_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._subject_label)

        self._question_label = QLabel()
        self._question_label.setObjectName("question_label")
        self._question_label.setWordWrap(True)
        self._question_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._question_label)

        self._difficulty_label = QLabel()
        self._difficulty_label.setObjectName("difficulty_label")
        self._difficulty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._difficulty_label)

        diff_row = QHBoxLayout()
        diff_row.setSpacing(8)
        self._easy_btn = self._make_difficulty_btn("easy", "Easy")
        self._moderate_btn = self._make_difficulty_btn("moderate", "Moderate")
        self._difficult_btn = self._make_difficulty_btn("difficult", "Difficult")
        self._change_question_btn = QPushButton("Change Question")
        self._change_question_btn.setProperty("class", "change_btn")
        self._change_question_btn.clicked.connect(self._on_change_question)
        diff_row.addWidget(self._easy_btn)
        diff_row.addWidget(self._moderate_btn)
        diff_row.addWidget(self._difficult_btn)
        diff_row.addWidget(self._change_question_btn)
        layout.addLayout(diff_row)

        layout.addSpacing(8)

        # 4 answer buttons
        self._btn_a = self._make_choice_btn("A")
        self._btn_b = self._make_choice_btn("B")
        self._btn_c = self._make_choice_btn("C")
        self._btn_d = self._make_choice_btn("D")

        row1 = QHBoxLayout()
        row1.addWidget(self._btn_a)
        row1.addWidget(self._btn_b)
        row2 = QHBoxLayout()
        row2.addWidget(self._btn_c)
        row2.addWidget(self._btn_d)
        layout.addLayout(row1)
        layout.addLayout(row2)

        layout.addSpacing(6)

        self._feedback_label = QLabel("")
        self._feedback_label.setObjectName("feedback_label")
        self._feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._feedback_label)

        self._progress_label = QLabel()
        self._progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._progress_label.setStyleSheet("color: #BBBBBB; font-size: 13px;")
        layout.addWidget(self._progress_label)

        self.setLayout(layout)

    def _make_choice_btn(self, letter: str) -> QPushButton:
        btn = QPushButton()
        btn.setProperty("class", "choice_btn")
        btn.setMinimumHeight(52)
        btn.clicked.connect(lambda _, l=letter: self._on_answer(l))
        return btn

    def _make_difficulty_btn(self, level: str, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setProperty("class", "diff_btn")
        btn.setCheckable(True)
        btn.clicked.connect(lambda _: self._set_difficulty(level))
        return btn

    def _normalized_subject(self, raw_subject: str) -> str:
        subject = raw_subject.strip()
        lowered = subject.lower()
        if lowered in {"language", "literature", "reading", "grammar", "vocabulary", "english"}:
            return "English"
        return subject

    def _normalize_difficulty(self, raw: str) -> str:
        lowered = raw.strip().lower()
        if lowered in self._LEVELS:
            return lowered
        if lowered in {"hard", "harder", "advanced"}:
            return "difficult"
        if lowered in {"medium", "normal", "intermediate"}:
            return "moderate"
        return "easy"

    def _difficulty_score(self, item: dict, band: str) -> int:
        text = str(item.get("question", "")).lower()
        subject = self._normalized_subject(str(item.get("subject", "General"))).lower()
        grade_weight = {
            "grade_1_2": 1,
            "grade_3_4": 2,
            "grade_5_6": 3,
            "grade_7_9": 4,
            "grade_10_plus": 5,
        }.get(band, 3)

        score = grade_weight
        if subject == "iq":
            score += 1
        if any(op in text for op in ["×", "÷", "%", "^", "fraction", "equation", "probability", "hypotenuse"]):
            score += 2
        elif any(op in text for op in ["+", "-", "*", "/", "decimal", "percent"]):
            score += 1
        if len(text) > 70:
            score += 1
        if len(text) > 110:
            score += 1
        return score

    def _rebuild_difficulty_pools(self, band: str, pool: list[dict]) -> None:
        self._difficulty_pools = {k: [] for k in self._LEVELS}
        explicit_items: list[tuple[str, dict]] = []
        inferred_items: list[tuple[int, dict]] = []

        for item in pool:
            raw_diff = item.get("difficulty")
            if isinstance(raw_diff, str) and raw_diff.strip():
                explicit_items.append((self._normalize_difficulty(raw_diff), item))
            else:
                inferred_items.append((self._difficulty_score(item, band), item))

        for level, item in explicit_items:
            self._difficulty_pools[level].append(item)

        inferred_items.sort(key=lambda x: x[0])
        count = len(inferred_items)
        if count > 0:
            for idx, (_, item) in enumerate(inferred_items):
                if idx < count / 3:
                    self._difficulty_pools["easy"].append(item)
                elif idx < (2 * count) / 3:
                    self._difficulty_pools["moderate"].append(item)
                else:
                    self._difficulty_pools["difficult"].append(item)

        # If a bucket is empty, reuse from moderate/easy so the UI always works.
        if not self._difficulty_pools["moderate"] and self._difficulty_pools["easy"]:
            self._difficulty_pools["moderate"] = self._difficulty_pools["easy"][:]
        if not self._difficulty_pools["easy"] and self._difficulty_pools["moderate"]:
            self._difficulty_pools["easy"] = self._difficulty_pools["moderate"][:]
        if not self._difficulty_pools["difficult"]:
            source = self._difficulty_pools["moderate"] or self._difficulty_pools["easy"]
            self._difficulty_pools["difficult"] = source[:]

    def _set_difficulty(self, level: str) -> None:
        normalized = self._normalize_difficulty(level)
        if normalized == self._current_difficulty:
            return
        self._current_difficulty = normalized
        self._load_question(force_change=True)

    def _active_difficulty_button_state(self) -> None:
        self._easy_btn.setChecked(self._current_difficulty == "easy")
        self._moderate_btn.setChecked(self._current_difficulty == "moderate")
        self._difficult_btn.setChecked(self._current_difficulty == "difficult")

    def _difficulty_display(self, level: str) -> str:
        return {
            "easy": "Easy",
            "moderate": "Moderate",
            "difficult": "Difficult",
        }.get(level, "Moderate")

    def _question_key(self, item: dict) -> str:
        return str(item.get("question", ""))

    def _on_change_question(self) -> None:
        self._feedback_label.setStyleSheet("color: #AADDFF;")
        self._feedback_label.setText("Changed to another question.")
        self._load_question(force_change=True)

    # ------------------------------------------------------------------
    def _load_question(self, force_change: bool = False) -> None:
        """Pick a random question from the configured grade band.

        Selection is balanced by subject so Math/Science do not dominate
        when a band also contains English questions. Questions are also
        separated by difficulty to support reward-by-level.
        """
        band = self._config.grade_band
        pool = QUESTIONS.get(band, QUESTIONS["grade_5_6"])

        if self._pool_band != band:
            self._difficulty_subject_cycles = {k: [] for k in self._LEVELS}
            self._pool_band = band
            self._rebuild_difficulty_pools(band, pool)

        current_pool = self._difficulty_pools.get(self._current_difficulty, [])
        if not current_pool:
            current_pool = pool

        by_subject: dict[str, list[dict]] = {}
        for item in current_pool:
            subject = self._normalized_subject(str(item.get("subject", "General")))
            by_subject.setdefault(subject, []).append(item)

        available_subjects = list(by_subject.keys())
        if not self._difficulty_subject_cycles[self._current_difficulty] or any(
            s not in available_subjects for s in self._difficulty_subject_cycles[self._current_difficulty]
        ):
            self._difficulty_subject_cycles[self._current_difficulty] = available_subjects[:]
            random.shuffle(self._difficulty_subject_cycles[self._current_difficulty])

        chosen_subject = self._difficulty_subject_cycles[self._current_difficulty].pop()
        candidates = by_subject[chosen_subject][:]
        if force_change and len(candidates) > 1:
            candidates = [q for q in candidates if self._question_key(q) != self._current_question_key] or candidates
        q = random.choice(candidates)

        self._current_answer = q["answer"]
        self._current_question_key = self._question_key(q)
        self._current_question_minutes = self._config.minutes_for_difficulty(self._current_difficulty)

        self._active_difficulty_button_state()
        self._subject_label.setText(chosen_subject.upper())
        self._difficulty_label.setText(
            f"Difficulty: {self._difficulty_display(self._current_difficulty)}  |  "
            f"Current Question Reward: +{self._current_question_minutes} min"
        )
        self._question_label.setText(q["question"])

        for btn, choice in zip(
            [self._btn_a, self._btn_b, self._btn_c, self._btn_d],
            q["choices"],
        ):
            btn.setText(choice)
            btn.setEnabled(True)

        self._change_question_btn.setEnabled(True)
        self.question_reward_changed.emit(self._current_question_minutes, self._current_difficulty)
        self._update_progress()

    def _update_progress(self) -> None:
        needed = self._config.questions_required_to_unlock
        self._progress_label.setText(
            f"Correct answers: {self._correct_streak} / {needed} needed to unlock  |  "
            f"Round earned: +{self._round_earned_minutes} min"
        )

    # ------------------------------------------------------------------
    def _on_answer(self, letter: str) -> None:
        if letter == self._current_answer:
            self._correct_streak += 1
            self._round_earned_minutes += self._current_question_minutes
            self._feedback_label.setStyleSheet("color: #55FF55;")
            self._feedback_label.setText(f"Correct! +{self._current_question_minutes} min ✓")
            needed = self._config.questions_required_to_unlock
            if self._correct_streak >= needed:
                minutes = self._round_earned_minutes
                self._correct_streak = 0
                self._round_earned_minutes = 0
                self.quiz_passed.emit(minutes)
            else:
                # Load next question after short display
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(800, lambda: self._load_question(force_change=True))
        else:
            self._feedback_label.setStyleSheet("color: #FF5555;")
            correct_text = ""
            for btn in [self._btn_a, self._btn_b, self._btn_c, self._btn_d]:
                if btn.text().startswith(self._current_answer + "."):
                    correct_text = btn.text()
            self._feedback_label.setText(f"Wrong! Answer: {correct_text}")
            # Reset streak
            self._correct_streak = 0
            self._round_earned_minutes = 0
            self._update_progress()
            # Disable all buttons briefly then reload
            for btn in [self._btn_a, self._btn_b, self._btn_c, self._btn_d]:
                btn.setEnabled(False)
            self._change_question_btn.setEnabled(False)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1500, lambda: self._load_question(force_change=True))
            self.quiz_failed.emit()

    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Reset state and load a fresh question (call before showing lock screen)."""
        self._correct_streak = 0
        self._round_earned_minutes = 0
        self._load_question()
