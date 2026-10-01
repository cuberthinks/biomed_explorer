@echo off
title BioMed Explorer
cd /d "%USERPROFILE%\Documents\biom.med"
if errorlevel 1 (
  echo Could not find the folder %USERPROFILE%\Documents\biom.med
  echo Clone it first: git clone https://github.com/cuberthinks/biom.med.git
  pause
  exit /b 1
)

if not exist node_modules (
  echo Installing for the first time, this takes a few minutes...
  call npm.cmd install
  if errorlevel 1 (
    echo.
    echo npm install failed. Copy the red text above and send it to Claude.
    pause
    exit /b 1
  )
)

echo Starting BioMed Explorer... your browser will open in a few seconds.
start "" cmd /c "timeout /t 8 >nul & start http://localhost:3000"
call npm.cmd run dev
pause
