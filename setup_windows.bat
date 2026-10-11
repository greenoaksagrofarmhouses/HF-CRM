@echo off
setlocal
where py >nul 2>nul || (echo Python launcher not found. Install Python 3.12+ first. & pause & exit /b 1)
if not exist .venv\Scripts\python.exe py -3.12 -m venv .venv
if errorlevel 1 (echo Could not create virtual environment. Ensure Python 3.12+ is installed. & pause & exit /b 1)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 (echo pip upgrade failed. Check network and try again. & pause & exit /b 1)
pip install -r requirements.txt
if errorlevel 1 (echo Dependency installation failed. Check internet access and requirements.txt. & pause & exit /b 1)
python manage.py check
if errorlevel 1 (echo Django system check failed. & pause & exit /b 1)
python manage.py makemigrations crm
if errorlevel 1 (echo Migration generation failed. & pause & exit /b 1)
python manage.py migrate
if errorlevel 1 (echo Database migration failed. & pause & exit /b 1)
echo.
echo Setup complete. Create a login with: python manage.py createsuperuser
echo Then start with: python manage.py runserver
pause
