@echo off
cd /d "%~dp0"
echo ========================================================
echo Running ApplyUs CRM Active Clients Scraper Pipeline
echo ========================================================
python run_crm_pipeline.py
pause
