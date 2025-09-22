#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples da API JSON da LeIA
"""

import requests
import json
import time

def testar_api():
    """Testa se a API está funcionando"""
    
    print("🧪 TESTANDO API JSON DA LEIA")
    print("=" * 40)
    
    # Aguardar um pouco para a API inicializar
    print("⏳ Aguardando API inicializar...")
    time.sleep(3)
    
    # URL da API
    base_url = "http://127.0.0.1:5000"
    
    # 1. Testar health check
    print("\n1️⃣ Testando health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API está funcionando!")
            print(f"   Resposta: {response.json()}")
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        print("   Certifique-se de que a API está rodando!")
        return False
    
    # 2. Testar pergunta simples
    print("\n2️⃣ Testando pergunta...")
    try:
        pergunta = {"pergunta": "Qual o fornecedor com maior custo em janeiro de 2024?"}
        
        response = requests.post(
            f"{base_url}/pergunta",
            json=pergunta,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            resposta = response.json()
            print("✅ Pergunta processada com sucesso!")
            print(f"   Sucesso: {resposta.get('sucesso', False)}")
            print(f"   Resposta: {resposta.get('resposta', 'N/A')[:100]}...")
            return True
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de requisição: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao decodificar JSON: {e}")
        return False

if __name__ == "__main__":
    if testar_api():
        print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("A API JSON da LeIA está funcionando perfeitamente!")
    else:
        print("\n❌ TESTE FALHOU!")
        print("Verifique se a API está rodando: python api_json.py")
