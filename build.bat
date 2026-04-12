@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Building QuizLock.exe...
pyinstaller --onefile --windowed --name QuizLock --icon=assets\icon.ico src\main.py 2>nul || ^
pyinstaller --onefile --windowed --name QuizLock src\main.py

echo.
echo Done! Find QuizLock.exe in the dist\ folder.
pause
