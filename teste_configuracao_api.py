#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar se a API está usando as configurações corretas do banco
"""

import requests
import json
import time

def testar_configuracao_api():
    """Testa se a API está usando as configurações corretas do banco"""
    
    print("🔧 TESTANDO CONFIGURAÇÕES DA API")
    print("=" * 50)
    
    API_URL = "http://127.0.0.1:5000"
    
    try:
        # Testar endpoint de configuração
        print("1️⃣ Verificando configurações do banco...")
        response = requests.get(f"{API_URL}/config", timeout=10)
        response.raise_for_status()
        
        config_data = response.json()
        config_banco = config_data['configuracao_banco']
        
        print("✅ Configurações obtidas da API:")
        print(f"   Host: {config_banco['host']}")
        print(f"   Port: {config_banco['port']}")
        print(f"   Database: {config_banco['database']}")
        print(f"   User: {config_banco['user']}")
        print(f"   SSL Mode: {config_banco['sslmode']}")
        
        # Verificar se não está usando localhost
        if config_banco['host'] == 'localhost' or config_banco['host'] == '127.0.0.1':
            print("❌ PROBLEMA: API ainda está configurada para localhost!")
            return False
        else:
            print("✅ API está usando configurações corretas (não localhost)")
        
        # Testar uma pergunta para verificar se conecta corretamente
        print("\n2️⃣ Testando conexão com o banco...")
        pergunta_teste = {
            "pergunta": "Qual o fornecedor com maior custo em janeiro de 2024?"
        }
        
        response = requests.post(
            f"{API_URL}/pergunta",
            headers={"Content-Type": "application/json"},
            data=json.dumps(pergunta_teste),
            timeout=30
        )
        response.raise_for_status()
        
        resposta_data = response.json()
        
        if resposta_data.get('sucesso'):
            print("✅ Conexão com o banco funcionando!")
            print(f"   Resposta: {resposta_data.get('resposta', '')[:100]}...")
            return True
        else:
            print("❌ Erro na conexão com o banco:")
            print(f"   {resposta_data.get('resposta', 'Erro desconhecido')}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão: API não está rodando")
        print("   Execute: python api_json_final.py")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def verificar_arquivo_env():
    """Verifica se o arquivo .env existe e tem as configurações corretas"""
    print("\n3️⃣ Verificando arquivo .env...")
    
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        print("✅ Arquivo .env encontrado")
        
        # Verificar se tem as configurações necessárias
        configs_necessarias = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
        configs_encontradas = []
        
        for config in configs_necessarias:
            if config in conteudo:
                configs_encontradas.append(config)
        
        print(f"   Configurações encontradas: {', '.join(configs_encontradas)}")
        
        if len(configs_encontradas) == len(configs_necessarias):
            print("✅ Todas as configurações necessárias estão no .env")
            return True
        else:
            print("⚠️ Algumas configurações podem estar faltando no .env")
            return False
            
    except FileNotFoundError:
        print("❌ Arquivo .env não encontrado!")
        print("   Crie um arquivo .env com as configurações do banco")
        return False
    except Exception as e:
        print(f"❌ Erro ao ler .env: {e}")
        return False

if __name__ == "__main__":
    print("LeIA - Teste de Configuração da API")
    print("=" * 50)
    
    # Verificar arquivo .env
    env_ok = verificar_arquivo_env()
    
    # Testar API
    api_ok = testar_configuracao_api()
    
    print("\n" + "=" * 50)
    if env_ok and api_ok:
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("A API está usando as configurações corretas do banco de dados.")
    else:
        print("❌ TESTE FALHOU!")
        if not env_ok:
            print("   - Problema com arquivo .env")
        if not api_ok:
            print("   - Problema com configurações da API")
        print("\n🔧 Verificações:")
        print("   1. Certifique-se de que o arquivo .env existe")
        print("   2. Verifique se as configurações do banco estão corretas")
        print("   3. Reinicie a API após alterar o .env")
        print("   4. Execute: python api_json_final.py")
