@echo off
title Sistema AliExpress IA - Control Global
color 0B

:: 1. MATAR PROCESOS PREVIOS (Limpieza)
echo [1/4] Limpiando procesos antiguos...
taskkill /f /im ollama.exe >nul 2>&1
taskkill /f /im "ollama serve" >nul 2>&1

:: 2. INICIAR OLLAMA SERVE
echo [2/4] Despertando a Gemma 3 (Ollama)...
:: Iniciamos el servidor en una ventana separada minimizada
start "Servidor IA" /min ollama serve

:: 3. ESPERA CRÍTICA
:: Ollama tarda unos segundos en levantar el puerto 11434. 
:: Si el bot arranca antes, dirá "Offline".
echo Esperando 10 segundos a que la IA este lista...
timeout /t 10 /nobreak > nul

:: 4. INICIAR BOT
echo [3/4] Iniciando Bot de Telegram...
echo --------------------------------------------------
echo NOTA: Si ves 'IA Offline', cierra esta ventana 
echo y vuelve a abrirla (Ollama puede tardar en cargar).
echo --------------------------------------------------
python bot.py

:: 5. APAGADO AUTOMÁTICO AL CERRAR
:shutdown
echo [4/4] Apagando IA y liberando memoria RAM...
taskkill /f /im ollama.exe >nul 2>&1
echo [OK] Sistema cerrado.
pause