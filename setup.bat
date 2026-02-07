@echo off
echo Installing claude-docs-sync...

:: Copy fetch script
copy /Y "%~dp0fetch-docs.py" "%USERPROFILE%\.claude\fetch-docs.py" >nul
copy /Y "%~dp0check-docs.bat" "%USERPROFILE%\.claude\check-docs.bat" >nul

:: Initial download
echo.
echo Running initial docs download...
python "%USERPROFILE%\.claude\fetch-docs.py"

:: Schedule daily check
echo.
echo Setting up daily scheduled task (9:00 AM)...
powershell -Command "Register-ScheduledTask -TaskName 'ClaudeDocsUpdate' -Description 'Daily check for Claude Code documentation updates' -Action (New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c \"%USERPROFILE%\.claude\check-docs.bat\"') -Trigger (New-ScheduledTaskTrigger -Daily -At '9:00AM') -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries) -Force"

echo.
echo Done! Docs saved to %USERPROFILE%\.claude\docs\claude-code\
echo Daily update check scheduled at 9:00 AM.
echo.
echo Manual commands:
echo   python ~/.claude/fetch-docs.py           Full download
echo   python ~/.claude/fetch-docs.py --check   Check for updates
echo   python ~/.claude/fetch-docs.py --update  Download only changes
pause
