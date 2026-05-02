@echo off
echo Copiando .venv do projeto original...
robocopy "C:\Users\dirfe\.gemini\antigravity\scratch\questor_explorer\backend\.venv" "C:\projetos\Vulcano2.0\backend\.venv" /E /NFL /NDL /NJH /NJS /nc /ns /np
echo Concluido!
pause
