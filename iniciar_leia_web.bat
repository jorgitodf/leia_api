@echo off
echo ========================================
echo    LeIA - Assistente Virtual Web
echo ========================================
echo.
echo Iniciando interface web da LeIA...
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Por favor, instale o Python 3.8 ou superior.
    pause
    exit /b 1
)

REM Executar o script de inicialização
python start_web.py

pause
