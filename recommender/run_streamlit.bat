@echo off
title Doctor Portal Streamlit App
cd /d "%~dp0"
echo ===================================================
echo     LAUNCHING STREAMLIT DOCTOR & MONGODB PORTAL
echo ===================================================
echo.
echo Opening http://localhost:8501 in your browser...
python -m streamlit run app.py
pause
