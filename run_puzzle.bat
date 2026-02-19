@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PORT=%~1"
if "%PORT%"=="" set "PORT=4173"

set "PY_CMD="
where python >nul 2>nul
if %ERRORLEVEL%==0 set "PY_CMD=python"

if "%PY_CMD%"=="" (
  where py >nul 2>nul
  if %ERRORLEVEL%==0 set "PY_CMD=py -3"
)

cd /d "%SCRIPT_DIR%"

if "%PY_CMD%"=="" (
  echo [안내] python/py를 찾지 못해 파일 모드로 실행합니다.
  echo [안내] 브라우저에서 index.html을 직접 엽니다.
  start "" "%SCRIPT_DIR%index.html"
  exit /b 0
)

echo 이미지 퍼즐 서버를 시작합니다...
echo 경로: %SCRIPT_DIR%
echo 주소: http://localhost:%PORT%/index.html
echo 중지하려면 Ctrl+C 를 누르세요.

start "" "http://localhost:%PORT%/index.html"
%PY_CMD% -m http.server %PORT%
