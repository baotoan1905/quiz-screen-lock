# Changelog

All notable changes to QuizLock will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-12

### Added
- Fullscreen always-on-top lock screen overlay (`lock_screen.py`)
- Quiz engine with 100+ questions across 5 grade bands (`quiz_engine.py`, `questions.py`)
  - Grades 1–2: arithmetic, basic science, days/months
  - Grades 3–4: multiplication, fractions, world geography, history
  - Grades 5–6: pre-algebra, earth science, world history, literature
  - Grades 7–9: algebra, biology, chemistry, Shakespeare
  - Grades 10–12: calculus, thermodynamics, advanced literature
- Floating countdown timer widget showing remaining screen-time budget (`timer_widget.py`)
- System tray icon with Lock Now / Settings / Quit menu items (`main.py`)
- Password-protected admin settings panel (`admin_panel.py`)
  - Configure grade band, daily budget, reward per correct answer
  - Change admin password
  - Lock-on-startup option
- Windows low-level keyboard hook to suppress Escape / Win keys while locked (`keyboard_hook.py`)
- JSON-based configuration persisted to `~/.quizlock/config.json` (`config.py`)
- `build.bat` for one-step PyInstaller packaging into `QuizLock.exe`
- MIT License
