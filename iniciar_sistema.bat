@echo off
title SISTEMA DE OFERTAS ALIEXPRESS - CHILE
color 0B

echo ======================================================
echo   INICIANDO ECOSISTEMA DE OFERTAS (IA + BOT + AUTO)
echo ======================================================

:: 1. Verificar e Iniciar Ollama
echo [1/3] Verificando Servidor Ollama...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [!] Ollama ya esta en ejecucion.
) else (
    echo [!] Iniciando Ollama desde cero...
    start "Servidor Ollama" /min "ollama serve"
    timeout /t 5
)

:: 2. Iniciar el Bot de Respuestas (Telegram Interactivo)
echo [2/3] Iniciando Bot de Telegram...
start "Bot Telegram" cmd /k "python bot.py"

:: 3. Iniciar el Cazador Automatico (Menu y Tareas)
echo [3/3] Iniciando Centro de Control (Cazador Auto)...
start "Cazador Auto" cmd /k "python cazador_auto.py"

echo.
echo ======================================================
echo   SISTEMA ACTIVO - REVISA LAS VENTANAS EMERGENTES
echo ======================================================
echo Pulsa cualquier tecla para cerrar este lanzador...
pause > nul