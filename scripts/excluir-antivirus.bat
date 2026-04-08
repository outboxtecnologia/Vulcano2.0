@echo off
echo Adicionando C:\projetos ao Windows Defender (requer Admin)...
PowerShell -Command "Add-MpPreference -ExclusionPath 'C:\projetos'"
echo.
echo Verificando exclusoes ativas:
PowerShell -Command "(Get-MpPreference).ExclusionPath"
echo.
pause
