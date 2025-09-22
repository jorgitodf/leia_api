#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar configurações do banco de dados
"""

import os
import sys
from dotenv import load_dotenv

def testar_configuracao_banco():
    """Testa as configurações do banco de dados"""
    
    print("🔧 TESTANDO CONFIGURAÇÕES DO BANCO DE DADOS")
    print("=" * 50)
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Verificar se o arquivo .env existe
    if not os.path.exists('.env'):
        print("❌ Arquivo .env não encontrado!")
        print("   Crie um arquivo .env com as configurações do banco de dados")
        return False
    
    # Obter configurações
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5441')
    db_name = os.getenv('DB_NAME', 'LeIA')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'postgres')
    db_sslmode = os.getenv('DB_SSLMODE', 'require')
    
    print(f"📋 Configurações encontradas:")
    print(f"   Host: {db_host}")
    print(f"   Port: {db_port}")
    print(f"   Database: {db_name}")
    print(f"   User: {db_user}")
    print(f"   Password: {'***' if db_password else 'NÃO DEFINIDA'}")
    print(f"   SSL Mode: {db_sslmode}")
    
    # Verificar se as configurações não são as padrão
    if db_host == 'localhost' and db_port == '5441':
        print("\n⚠️ ATENÇÃO: Usando configurações padrão (localhost)")
        print("   Certifique-se de que estas são as configurações corretas para produção")
    
    # Testar conexão
    print(f"\n🔌 Testando conexão com o banco...")
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
            sslmode=db_sslmode
        )
        
        print("✅ Conexão com o banco de dados bem-sucedida!")
        
        # Testar uma query simples
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"📊 Versão do PostgreSQL: {version}")
        
        conn.close()
        return True
        
    except ImportError:
        print("❌ psycopg2 não instalado!")
        print("   Execute: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ Erro ao conectar com o banco: {e}")
        print("\n🔧 Verificações:")
        print("   1. O host está correto?")
        print("   2. A porta está correta?")
        print("   3. O banco de dados existe?")
        print("   4. O usuário e senha estão corretos?")
        print("   5. O servidor está rodando?")
        print("   6. O firewall permite conexões?")
        return False

def mostrar_exemplo_env():
    """Mostra exemplo de arquivo .env"""
    print("\n📝 EXEMPLO DE ARQUIVO .env:")
    print("=" * 50)
    print("""
# Configurações do Banco de Dados PostgreSQL
DB_HOST=seu_host_do_banco_aqui
DB_PORT=5432
DB_NAME=seu_nome_do_banco_aqui
DB_USER=seu_usuario_do_banco_aqui
DB_PASSWORD=sua_senha_do_banco_aqui
DB_SSLMODE=require

# Configurações da API
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=False

# Google AI API Key
GOOGLE_API_KEY=sua_chave_do_google_ai_aqui
""")

if __name__ == "__main__":
    print("LeIA - Teste de Configuração do Banco de Dados")
    print("=" * 50)
    
    if testar_configuracao_banco():
        print("\n🎉 CONFIGURAÇÃO OK!")
        print("A API deve funcionar corretamente com estas configurações.")
    else:
        print("\n❌ CONFIGURAÇÃO COM PROBLEMAS!")
        print("Corrija as configurações antes de iniciar a API.")
        mostrar_exemplo_env()
