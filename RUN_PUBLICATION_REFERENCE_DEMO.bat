@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title AGROLATTICE 11.19 - Publication Reference Demo
set "PYTHON_EXE="
if defined CONDA_PREFIX if exist "%CONDA_PREFIX%\python.exe" set "PYTHON_EXE=%CONDA_PREFIX%\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\anaconda3\envs\ML_AGRICULTURE\python.exe" set "PYTHON_EXE=%USERPROFILE%\anaconda3\envs\ML_AGRICULTURE\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\anaconda3\python.exe" set "PYTHON_EXE=%USERPROFILE%\anaconda3\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\miniconda3\envs\ML_AGRICULTURE\python.exe" set "PYTHON_EXE=%USERPROFILE%\miniconda3\envs\ML_AGRICULTURE\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\miniconda3\python.exe" set "PYTHON_EXE=%USERPROFILE%\miniconda3\python.exe"
if not defined PYTHON_EXE for /f "delims=" %%P in ('where python 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%P"
if not defined PYTHON_EXE (
  echo ERROR: Python was not found.
  pause
  exit /b 1
)
"%PYTHON_EXE%" publication_reference.py --output publication_reference
if errorlevel 1 (
  echo ERROR: publication-reference demo verification failed.
  pause
  exit /b 1
)
echo Demo project, figures and example outputs regenerated deterministically.
pause
endlocal
