REM change to current directory
%~d0
pushd %~dp0

set RELEASE_FILE=DEUMeldeformularKonverter.zip

REM delete old files
rd /Q /S dist
del %RELEASE_FILE%

REM package user interface into an executable
REM make sure to install all python requirements (see ../install_requirements.bat)
pyinstaller --onefile DEUMeldeformularKonverter.py --path ..

REM copy additional files
robocopy ..\masterData dist\masterData /S
robocopy . dist\ *.md
robocopy .. dist\ LICENSE

REM create zip archive
powershell -NoProfile -ExecutionPolicy Bypass -Command Compress-Archive dist/* %RELEASE_FILE%
popd
