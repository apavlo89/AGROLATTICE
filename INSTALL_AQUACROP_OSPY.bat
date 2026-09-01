@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Install AquaCrop-OSPy Backend
set "PYTHON_EXE="
if defined CONDA_PREFIX if exist "%CONDA_PREFIX%\python.exe" set "PYTHON_EXE=%CONDA_PREFIX%\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\anaconda3\envs\ML_AGRICULTURE\python.exe" set "PYTHON_EXE=%USERPROFILE%\anaconda3\envs\ML_AGRICULTURE\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\anaconda3\python.exe" set "PYTHON_EXE=%USERPROFILE%\anaconda3\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\miniconda3\python.exe" set "PYTHON_EXE=%USERPROFILE%\miniconda3\python.exe"
if not defined PYTHON_EXE for /f "delims=" %%P in ('where python 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%P"
if not defined PYTHON_EXE (
  echo ERROR: Python was not found.
  pause
  exit /b 1
)
echo Installing AquaCrop-OSPy into:
echo %PYTHON_EXE%
"%PYTHON_EXE%" -m pip install --upgrade "aquacrop>=3.1.0"
if errorlevel 1 (
  echo.
  echo AquaCrop-OSPy installation failed. Review Python-version and package errors above.
  pause
  exit /b 1
)
echo.
echo Installation complete. Restart Streamlit.
pause
endlocal
