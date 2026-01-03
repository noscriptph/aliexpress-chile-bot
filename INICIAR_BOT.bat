@echo off
:: Navega a la carpeta donde está el archivo .bat
cd /d "%~dp0"

echo Verificando Python 3.12...
:: Intentamos llamar a python. Si no funciona, intentamos con 'py' (el lanzador de Windows)
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo Usando comando: python
    python bot.py
) else (
    py -3.12 bot.py
)

pause