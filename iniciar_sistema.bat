@echo off
title = Studio Andressa Mariano - Sistema de Agendamento
color 0D
echo ==================================================
echo    STUDIO ANDRESSA MARIANO HAIR
echo    Sistema de Agendamento
echo ==================================================
echo.
echo 🟢 Iniciando servidor...
echo.

REM Entrar na pasta correta onde está o main.py
cd /d "%~dp0backend\api"

start "Backend" python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

timeout /t 5 /nobreak > nul

echo 🟢 Abrindo o sistema no navegador...
start http://localhost:8000/docs
start "" "%~dp0frontend\index.html"

echo.
echo ==================================================
echo ✅ Sistema rodando!
echo 📌 Deixe esta janela aberta
echo 🔴 Feche esta janela para desligar o sistema
echo ==================================================
echo.
pause