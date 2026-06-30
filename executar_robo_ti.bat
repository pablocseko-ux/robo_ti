@echo off
cd /d C:\Users\Pbehrens\Documents\robo_rh\robo_ti

call .venv\Scripts\activate.bat

python main.py >> logs\robo_ti.log 2>&1