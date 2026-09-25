@echo off
cd /d "%~dp0"
echo ========================================================
echo Running Active Clients Job Pipeline
echo ========================================================
python run_crm_pipeline.py
pause
