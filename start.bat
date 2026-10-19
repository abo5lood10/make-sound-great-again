@echo off
cd /d "%~dp0"
where python >nul 2>nul || (echo Python 3.8+ is required: https://www.python.org/downloads/ & pause & exit /b 1)
python -m pip install --quiet --disable-pip-version-check -r requirements.txt || (echo Could not install the requirements. & pause & exit /b 1)
python run.py %*
