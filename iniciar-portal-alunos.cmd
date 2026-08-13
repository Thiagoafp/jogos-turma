@echo off
title Portal dos alunos - Jogos da Turma
cd /d "%~dp0"

echo ============================================================
echo   PORTAL DOS ALUNOS - JOGOS DA TURMA
echo ============================================================
echo.
echo Os alunos conectados ao mesmo Wi-Fi devem abrir:
for /f "tokens=2 delims=:" %%I in ('ipconfig ^| findstr /c:"IPv4"') do echo   http:%%I:8081
echo.
echo A lista individual de codigos esta em:
echo   .portal\codigos-iniciais.txt
echo.
echo Deixe esta janela aberta durante os envios.
echo Para encerrar, pressione Ctrl+C.
echo ============================================================
echo.

python ferramentas\portal.py --host 0.0.0.0
pause
