#!/usr/bin/env python3
"""
Script de inicialização para a interface web da LeIA
"""

import subprocess
import sys
import os
from pathlib import Path

def verificar_dependencias():
    """Verifica se as dependências estão instaladas"""
    try:
        import streamlit
        print("✅ Streamlit encontrado")
    except ImportError:
        print("❌ Streamlit não encontrado. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit>=1.28.0"])
        print("✅ Streamlit instalado com sucesso!")
    
    try:
        import google.generativeai
        print("✅ Google Generative AI encontrado")
    except ImportError:
        print("❌ Google Generative AI não encontrado. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai"])
        print("✅ Google Generative AI instalado com sucesso!")

def verificar_arquivo_env():
    """Verifica se o arquivo .env existe"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Arquivo .env não encontrado!")
        print("📝 Criando arquivo .env de exemplo...")
        
        env_content = """# Configurações do Banco de Dados PostgreSQL
DB_HOST=localhost
DB_PORT=5441
DB_NAME=LeIA
DB_USER=postgres
DB_PASSWORD=postgres

# Google Gemini AI - Substitua pela sua chave real
GOOGLE_API_KEY=sua_chave_api_aqui
"""
        
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)
        
        print("✅ Arquivo .env criado!")
        print("🔧 Por favor, edite o arquivo .env com suas configurações reais.")
        return False
    
    print("✅ Arquivo .env encontrado")
    return True

def main():
    """Função principal"""
    print("🚀 Iniciando LeIA - Interface Web")
    print("=" * 50)
    
    # Verificar dependências
    print("🔍 Verificando dependências...")
    verificar_dependencias()
    
    # Verificar arquivo .env
    print("\n🔍 Verificando configurações...")
    env_ok = verificar_arquivo_env()
    
    if not env_ok:
        print("\n⚠️  Configure o arquivo .env antes de continuar!")
        input("Pressione Enter para sair...")
        return
    
    # Verificar se app.py existe
    if not Path("app.py").exists():
        print("❌ Arquivo app.py não encontrado!")
        print("📁 Certifique-se de estar no diretório correto do projeto.")
        input("Pressione Enter para sair...")
        return
    
    print("\n🌐 Iniciando interface web...")
    print("📱 A aplicação será aberta no seu navegador padrão")
    print("🔗 URL: http://localhost:8501")
    print("\n💡 Para parar a aplicação, pressione Ctrl+C")
    print("=" * 50)
    
    try:
        # Executar Streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=True)
    except KeyboardInterrupt:
        print("\n\n👋 LeIA encerrada. Até logo!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro ao executar a aplicação: {e}")
        input("Pressione Enter para sair...")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()
