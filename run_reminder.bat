@echo off
cd /d "C:\Users\Loc\Desktop\healthmanager"

REM Dùng python trong venv để chạy lệnh send_reminder
"C:\Users\Loc\Desktop\healthmanager\.venv\Scripts\python.exe" manage.py send_reminder
