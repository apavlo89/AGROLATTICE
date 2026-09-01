@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title AGROLATTICE 11.19 - Optional Research Models

set "PYTHON_EXE="
if defined CONDA_PREFIX if exist "%CONDA_PREFIX%\python.exe" set "PYTHON_EXE=%CONDA_PREFIX%\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\anaconda3\envs\ML_AGRICULTURE\python.exe" set "PYTHON_EXE=%USERPROFILE%\anaconda3\envs\ML_AGRICULTURE\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\miniconda3\envs\ML_AGRICULTURE\python.exe" set "PYTHON_EXE=%USERPROFILE%\miniconda3\envs\ML_AGRICULTURE\python.exe"
if not defined PYTHON_EXE for /f "delims=" %%P in ('where python 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%P"

if not defined PYTHON_EXE (
  echo ERROR: Python was not found. Activate the ML_AGRICULTURE environment first.
  pause
  exit /b 1
)

if not exist "requirements_research_optional.txt" (
  echo ERROR: requirements_research_optional.txt is missing.
  pause
  exit /b 1
)

echo Installing OPTIONAL AGROLATTICE research-model packages using:
echo %PYTHON_EXE%
echo.
"%PYTHON_EXE%" -m pip install -r "requirements_research_optional.txt"
if errorlevel 1 (
  echo.
  echo Optional research-model installation failed. Core AGROLATTICE 11.19 can still run without these packages.
  pause
  exit /b 1
)

echo.
echo Optional research-model packages installed. Runtime compatibility is still checked by the app.
pause
endlocal
