@echo off
echo ========================================
echo    LeIA - Assistente Virtual JSON
echo ========================================
echo.
echo Escolha uma opcao:
echo.
echo 1. Interface Streamlit (com modo JSON)
echo 2. API REST JSON
echo 3. Teste da funcionalidade JSON
echo 4. Sair
echo.
set /p opcao="Digite sua opcao (1-4): "

if "%opcao%"=="1" (
    echo.
    echo Iniciando Interface Streamlit...
    echo Acesse: http://localhost:8501
    echo Ative o modo JSON na sidebar
    echo.
    streamlit run app.py
) else if "%opcao%"=="2" (
    echo.
    echo Iniciando API REST JSON...
    echo API disponivel em: http://127.0.0.1:5000
    echo Documentacao: http://127.0.0.1:5000/
    echo.
    python api_json_final.py
) else if "%opcao%"=="3" (
    echo.
    echo Executando testes da funcionalidade JSON...
    echo.
    python teste_json.py
    echo.
    pause
) else if "%opcao%"=="4" (
    echo.
    echo Saindo...
    exit
) else (
    echo.
    echo Opcao invalida!
    pause
    goto :eof
)

pause
