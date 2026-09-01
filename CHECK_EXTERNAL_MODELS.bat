@echo off
setlocal
cd /d "%~dp0"
echo Searching for DSSAT and APSIM executables...
echo.
for %%F in ("C:\DSSAT48\DSCSM048.EXE" "C:\DSSAT485\DSCSM048.EXE") do if exist %%F echo DSSAT found: %%~F
for /d %%D in ("C:\Program Files\APSIM*") do if exist "%%~D\bin\Models.exe" echo APSIM found: %%~D\bin\Models.exe
echo.
echo You can enter a different executable path inside the app.
pause
endlocal
