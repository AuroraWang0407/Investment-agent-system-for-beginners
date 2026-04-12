@echo off
title AI Stock Agent Launcher

:: Set your conda environment name here!
set ENV_CMD=conda activate stock_agent

echo =========================================
echo   Starting AI Stock Agent (Conda)...
echo =========================================

:: 1. Start the FastAPI backend
echo Starting FastAPI Backend...
start cmd /k "%ENV_CMD% && uvicorn api:app --reload"

:: Wait for 3 seconds
timeout /t 3 /nobreak > NUL

:: 2. Start the Streamlit frontend
echo Starting Streamlit Frontend...
start cmd /k "%ENV_CMD% && streamlit run app.py"