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
from PyQt6.QtGui import QFont
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
    """

    quiz_passed = pyqtSignal(int)   # minutes to award
    quiz_failed = pyqtSignal()

    def __init__(self, config: Config, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._config = config
        self._correct_streak = 0
        self._current_answer: str = ""
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

        layout.addSpacing(10)

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

    def _normalized_subject(self, raw_subject: str) -> str:
        subject = raw_subject.strip()
        lowered = subject.lower()
        if lowered in {"language", "literature", "reading", "grammar", "vocabulary", "english"}:
            return "English"
        return subject

    # ------------------------------------------------------------------
    def _load_question(self) -> None:
        """Pick a random question from the configured grade band.

        Selection is balanced by subject so Math/Science do not dominate
        when a band also contains English questions.
        """
        band = self._config.grade_band
        pool = QUESTIONS.get(band, QUESTIONS["grade_5_6"])
        by_subject: dict[str, list[dict]] = {}
        for item in pool:
            subject = self._normalized_subject(str(item.get("subject", "General")))
            by_subject.setdefault(subject, []).append(item)

        chosen_subject = random.choice(list(by_subject.keys()))
        q = random.choice(by_subject[chosen_subject])

        self._current_answer = q["answer"]
        self._subject_label.setText(chosen_subject.upper())
        self._question_label.setText(q["question"])

        for btn, choice in zip(
            [self._btn_a, self._btn_b, self._btn_c, self._btn_d],
            q["choices"],
        ):
            btn.setText(choice)
            btn.setEnabled(True)

        self._feedback_label.setText("")
        self._update_progress()

    def _update_progress(self) -> None:
        needed = self._config.questions_required_to_unlock
        self._progress_label.setText(
            f"Correct answers: {self._correct_streak} / {needed} needed to unlock"
        )

    # ------------------------------------------------------------------
    def _on_answer(self, letter: str) -> None:
        if letter == self._current_answer:
            self._correct_streak += 1
            self._feedback_label.setStyleSheet("color: #55FF55;")
            self._feedback_label.setText("Correct! ✓")
            needed = self._config.questions_required_to_unlock
            if self._correct_streak >= needed:
                minutes = self._config.minutes_per_correct * self._correct_streak
                self._correct_streak = 0
                self.quiz_passed.emit(minutes)
            else:
                # Load next question after short display
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(800, self._load_question)
        else:
            self._feedback_label.setStyleSheet("color: #FF5555;")
            correct_text = ""
            for btn in [self._btn_a, self._btn_b, self._btn_c, self._btn_d]:
                if btn.text().startswith(self._current_answer + "."):
                    correct_text = btn.text()
            self._feedback_label.setText(f"Wrong! Answer: {correct_text}")
            # Reset streak
            self._correct_streak = 0
            self._update_progress()
            # Disable all buttons briefly then reload
            for btn in [self._btn_a, self._btn_b, self._btn_c, self._btn_d]:
                btn.setEnabled(False)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1500, self._load_question)
            self.quiz_failed.emit()

    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Reset state and load a fresh question (call before showing lock screen)."""
        self._correct_streak = 0
        self._load_question()
