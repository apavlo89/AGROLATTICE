@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Install Satellite Monitoring Dependencies

set "PYTHON_EXE="
if defined CONDA_PREFIX if exist "%CONDA_PREFIX%\python.exe" set "PYTHON_EXE=%CONDA_PREFIX%\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\anaconda3\envs\ML_AGRICULTURE\python.exe" set "PYTHON_EXE=%USERPROFILE%\anaconda3\envs\ML_AGRICULTURE\python.exe"
if not defined PYTHON_EXE if exist "%USERPROFILE%\anaconda3\python.exe" set "PYTHON_EXE=%USERPROFILE%\anaconda3\python.exe"
if not defined PYTHON_EXE for /f "delims=" %%P in ('where python 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%P"

if not defined PYTHON_EXE (
  echo ERROR: Python was not found.
  pause
  exit /b 1
)

echo Installing rasterio, shapely, pyproj, Pillow and requests into:
echo %PYTHON_EXE%
"%PYTHON_EXE%" -m pip install --upgrade "requests>=2.31" "rasterio>=1.3.9" "shapely>=2.0" "pyproj>=3.6" "Pillow>=10.0"
if errorlevel 1 (
  echo.
  echo Pip installation failed. Activate your Anaconda environment and try:
  echo conda install -c conda-forge rasterio shapely pyproj pillow requests
  pause
  exit /b 1
)

"%PYTHON_EXE%" -c "import rasterio, shapely, pyproj, PIL, requests, satellite_crop_monitoring; print('Satellite dependencies installed successfully')"
if errorlevel 1 (
  echo Installation completed but the import check failed.
  pause
  exit /b 1
)

echo.
echo Satellite monitoring dependencies are ready.
pause
endlocal
