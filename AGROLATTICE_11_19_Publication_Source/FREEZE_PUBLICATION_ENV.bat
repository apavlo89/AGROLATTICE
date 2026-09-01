@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title AGROLATTICE 11.19 - Freeze Publication Environment
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
if not exist "publication_reference\environment" mkdir "publication_reference\environment"
"%PYTHON_EXE%" --version > "publication_reference\environment\python_runtime_11_19.txt" 2>&1
"%PYTHON_EXE%" -c "import sys,platform; print(sys.executable); print(sys.version); print(platform.platform())" >> "publication_reference\environment\python_runtime_11_19.txt" 2>&1
"%PYTHON_EXE%" -m pip freeze --all > "publication_reference\environment\pip_freeze_11_19.txt"
"%PYTHON_EXE%" -c "import hashlib,pathlib; p=pathlib.Path(r'publication_reference\environment\pip_freeze_11_19.txt'); print(hashlib.sha256(p.read_bytes()).hexdigest())" > "publication_reference\environment\pip_freeze_11_19.sha256.txt"
echo Exact target-environment snapshot written to publication_reference\environment\
pause
endlocal
