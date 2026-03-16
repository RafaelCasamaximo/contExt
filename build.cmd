@echo off
setlocal

set "PROJECT_DIR=%~dp0"
set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
set "SPEC_FILE=%PROJECT_DIR%\packaging\pyinstaller\ContExt.spec"
set "RELEASE_DIR=%PROJECT_DIR%\release"
set "WORK_DIR=%RELEASE_DIR%\windows-x64"
set "DIST_DIR=%WORK_DIR%\dist"
set "BUILD_DIR=%WORK_DIR%\build"
set "CONFIG_DIR=%WORK_DIR%\config"
set "ARTIFACT_DIR=%RELEASE_DIR%\ContExt-windows-x64"
set "ARTIFACT_FILE=%RELEASE_DIR%\ContExt-windows-x64.zip"

if exist "%WORK_DIR%" rmdir /s /q "%WORK_DIR%"
if exist "%ARTIFACT_DIR%" rmdir /s /q "%ARTIFACT_DIR%"
if exist "%ARTIFACT_FILE%" del /q "%ARTIFACT_FILE%"

mkdir "%DIST_DIR%"
mkdir "%BUILD_DIR%"
mkdir "%CONFIG_DIR%"
mkdir "%ARTIFACT_DIR%"
set "PYINSTALLER_CONFIG_DIR=%CONFIG_DIR%"

python -m PyInstaller --noconfirm --clean --distpath "%DIST_DIR%" --workpath "%BUILD_DIR%" "%SPEC_FILE%"
copy /y "%DIST_DIR%\ContExt.exe" "%ARTIFACT_DIR%\ContExt.exe" >nul

powershell -NoProfile -Command "Compress-Archive -Path '%ARTIFACT_DIR%' -DestinationPath '%ARTIFACT_FILE%' -Force"

echo Created %ARTIFACT_FILE%
