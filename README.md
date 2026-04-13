# QuizLock

**A Windows screen-lock app that rewards screen time for solving educational quizzes.**

QuizLock sits in the system tray and counts down the child's daily screen-time budget. When time runs out the screen is locked with a fullscreen overlay. The child must answer quiz questions correctly to earn more minutes and return to the desktop.

---

## Features

- **Fullscreen lock screen** — always on top, suppresses Win key / Escape / Alt+F4
- **100+ curated questions** across five grade bands (Grades 1–12)
- **Earn screen time** — each correct answer adds configurable minutes back
- **Floating countdown timer** — small transparent overlay shows remaining budget
- **System tray icon** — quick access to Lock Now, Settings, and Quit
- **Password-protected admin panel** — parents configure grade, budget, and rewards
- **Persistent config** — settings saved to `~/.quizlock/config.json`
- **Single-file executable** — build to `QuizLock.exe` with one command

---

## Grade Bands & Question Topics

| Band | Grades | Subjects |
|------|--------|---------|
| `grade_1_2` | 1–2 | Basic arithmetic, shapes, days/seasons, animals |
| `grade_3_4` | 3–4 | Multiplication, fractions, world geography, US history |
| `grade_5_6` | 5–6 | Pre-algebra, earth science, world history, literature |
| `grade_7_9` | 7–9 | Algebra, biology, chemistry, Shakespeare |
| `grade_10_plus` | 10–12 | Calculus, thermodynamics, advanced literature, world events |

---

## Default Settings

| Setting | Default |
|---------|---------|
| Daily screen budget | 60 minutes |
| Minutes per correct answer | 5 minutes |
| Correct answers to unlock | 1 |
| Grade band | Grades 5–6 |
| Admin password | `quizlock123` |

**Change the admin password immediately after first run.**

---

## Installation & Running from Source

### Requirements

- Windows 10 or 11
- Python 3.10+

### Steps

```bat
git clone https://github.com/baotoan1905/quiz-screen-lock.git
cd quiz-screen-lock
python -m pip install -r requirements.txt
python src/main.py
```

QuizLock runs in the **system tray** (no main window opens). If you do not see it right away, click the Windows hidden-icons arrow near the clock and look for the **Q** icon, then right-click it for settings.

---

## Building a Standalone Executable

```bat
build.bat
```

This installs dependencies and runs PyInstaller. The output `QuizLock.exe` will be in the `dist\` folder.

---

## Usage

1. **Start QuizLock** — it runs in the system tray.
2. **Tray icon** — right-click to open the menu:
   - **Lock Now** — immediately show the lock screen
   - **Settings…** — open admin panel (requires password)
   - **Quit QuizLock** — exit (requires confirmation)
3. **Lock screen** — the child sees a quiz. Answer correctly to earn screen time.
4. **Admin panel** — parents set the grade band, daily budget, and reward per correct answer.

---

## Project Structure

```
quiz-screen-lock/
├── src/
│   ├── main.py          # Entry point, tray icon, ScreenTimeManager
│   ├── lock_screen.py   # Fullscreen overlay
│   ├── timer_widget.py  # Floating countdown timer
│   ├── admin_panel.py   # Admin settings dialog
│   ├── quiz_engine.py   # Quiz widget and scoring
│   ├── keyboard_hook.py # Win/Escape key suppression
│   ├── config.py        # Config read/write
│   └── questions.py     # 100+ question bank
├── requirements.txt
├── build.bat
├── CHANGELOG.md
├── LICENSE
└── README.md
```

---

## License

MIT © 2026 [baotoan1905](https://github.com/baotoan1905)
