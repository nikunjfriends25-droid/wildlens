@echo off
title WildLens Validator
cd /d C:\wildlife-news-map
echo Starting WildLens validation GUI...
echo Open http://localhost:8501 in your browser
echo Close this window to stop the server.
echo.
streamlit run v2/tools/validate.py
pause
