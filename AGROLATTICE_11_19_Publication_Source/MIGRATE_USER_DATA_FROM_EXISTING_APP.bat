@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Migrate AGROLATTICE User Data - Release 11.19

echo AGROLATTICE 11.19 - BACKUP-FIRST USER-DATA MIGRATION
echo.
echo Use this after extracting Release 11.19 when your real research data live in an older working AGROLATTICE folder.
echo The folder selected below becomes the source of truth for compatible user-owned research databases:
echo   - Field Operations
echo   - Experiments / Maize Pollination Lab
echo   - Persistent Twin
echo   - Research Evidence
echo   - Crop Profile Registry
echo   - Reporting Registry
echo.
echo Before replacement, AGROLATTICE creates timestamped backups and verifies SQLite integrity.
echo Schema upgrades, where needed by a future source database, remain additive/non-destructive at normal startup.
echo.
set /p "SOURCE=Enter the full path of the existing working app folder: "
set "SOURCE=%SOURCE:"=%"

if not exist "%SOURCE%" (
  echo ERROR: The source folder does not exist.
  pause
  exit /b 1
)
if /I "%SOURCE%"=="%CD%" (
  echo ERROR: Source and destination are the same folder. Nothing was changed.
  pause
  exit /b 1
)

echo.
echo IMPORTANT: compatible user-owned SQLite databases from:
echo   %SOURCE%
echo will replace the packaged/current Release 11.19 copies only AFTER validation and backups are created.
echo Use this only when the selected folder is your authoritative working installation.
echo.
set /p "CONFIRM=Type MIGRATE to continue: "
if /I not "%CONFIRM%"=="MIGRATE" (
  echo Migration cancelled. Nothing was changed.
  pause
  exit /b 0
)

set "PYTHON_EXE="
if defined CONDA_PREFIX if exist "%CONDA_PREFIX%\python.exe" set "PYTHON_EXE=%CONDA_PREFIX%\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\anaconda3\envs\ML_AGRICULTURE\python.exe" set "PYTHON_EXE=%USERPROFILE%\anaconda3\envs\ML_AGRICULTURE\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\anaconda3\python.exe" set "PYTHON_EXE=%USERPROFILE%\anaconda3\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\miniconda3\envs\ML_AGRICULTURE\python.exe" set "PYTHON_EXE=%USERPROFILE%\miniconda3\envs\ML_AGRICULTURE\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\miniconda3\python.exe" set "PYTHON_EXE=%USERPROFILE%\miniconda3\python.exe"
if not defined PYTHON_EXE for /f "delims=" %%P in ('where python 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%P"

if not defined PYTHON_EXE (
  echo ERROR: Python was not found. Activate the ML_AGRICULTURE environment and try again.
  pause
  exit /b 1
)

"%PYTHON_EXE%" "%~dp0safe_data_migration.py" "%SOURCE%" --destination "%~dp0" --confirmed
if errorlevel 1 (
  echo.
  echo Migration stopped safely. Review the error above. Existing backups were not intentionally deleted.
  pause
  exit /b 1
)

echo.
echo Migration complete. Run RUN_APP.bat; Release 11.19 will verify its runtime modules and database schemas before launch.
pause
endlocal
