@echo off
title SISTEMA DE OFERTAS ALIEXPRESS - CHILE
color 0B

echo ======================================================
echo   INICIANDO ECOSISTEMA DE OFERTAS (IA + BOT + AUTO)
echo ======================================================

:: 1. Iniciar Ollama (asegura que el servidor de IA esté arriba)
echo [1/3] Levantando Servidor Ollama...
start "Servidor Ollama" cmd /k "ollama serve"
timeout /t 5

:: 2. Iniciar el Bot de Respuestas (Telegram Interactivo)
echo [2/3] Iniciando Bot de Telegram (Respuestas a links)...
start "Bot Telegram" cmd /k "python bot.py"

:: 3. Iniciar el Cazador Automatico (Tareas Programadas y CSV)
echo [3/3] Iniciando Cazador de Tendencias (Auto-Publicador)...
start "Cazador Auto" cmd /k "python cazador_auto.py"

echo.
echo ======================================================
echo   SISTEMA ACTIVO - NO CIERRES LAS VENTANAS NEGRAS
echo ======================================================
pause