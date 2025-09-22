#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo prático de uso da API JSON da LeIA
"""

import requests
import json
import time

def testar_api_json():
    """Testa a API JSON da LeIA"""
    
    # URL da API (ajuste conforme necessário)
    base_url = "http://localhost:5000"
    
    print("🚀 TESTANDO API JSON DA LEIA")
    print("=" * 50)
    
    # 1. Verificar se a API está rodando
    print("\n1️⃣ Verificando status da API...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API está rodando!")
            print(f"   Status: {response.json()}")
        else:
            print(f"❌ API retornou status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao conectar com a API: {e}")
        print("   Certifique-se de que a API está rodando: python api_json.py")
        return False
    
    # 2. Obter exemplos
    print("\n2️⃣ Obtendo exemplos de perguntas...")
    try:
        response = requests.get(f"{base_url}/exemplos", timeout=5)
        if response.status_code == 200:
            exemplos = response.json()
            print("✅ Exemplos obtidos!")
            print(f"   Categorias disponíveis: {len(exemplos['exemplos'])}")
        else:
            print(f"❌ Erro ao obter exemplos: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao obter exemplos: {e}")
    
    # 3. Testar perguntas
    perguntas_teste = [
        "Qual o fornecedor com maior custo em janeiro de 2024?",
        "Quantas linhas ativas tem o cliente Safra?",
        "Qual usuário teve maior custo no mês atual?"
    ]
    
    print(f"\n3️⃣ Testando {len(perguntas_teste)} perguntas...")
    
    sucessos = 0
    for i, pergunta in enumerate(perguntas_teste, 1):
        print(f"\n   📝 Pergunta {i}: {pergunta}")
        
        # Preparar JSON de entrada
        entrada = {"pergunta": pergunta}
        
        try:
            # Enviar pergunta
            response = requests.post(
                f"{base_url}/pergunta",
                json=entrada,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                resposta = response.json()
                print(f"   ✅ Sucesso: {resposta.get('sucesso', False)}")
                print(f"   📤 Resposta: {resposta.get('resposta', 'N/A')[:100]}...")
                print(f"   🕐 Timestamp: {resposta.get('timestamp', 'N/A')}")
                sucessos += 1
            else:
                print(f"   ❌ Erro HTTP: {response.status_code}")
                print(f"   📄 Resposta: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Erro de requisição: {e}")
        except json.JSONDecodeError as e:
            print(f"   ❌ Erro ao decodificar JSON: {e}")
        
        # Pequena pausa entre requisições
        time.sleep(1)
    
    # 4. Resumo dos testes
    print(f"\n4️⃣ RESUMO DOS TESTES")
    print("=" * 50)
    print(f"✅ Sucessos: {sucessos}/{len(perguntas_teste)}")
    print(f"❌ Falhas: {len(perguntas_teste) - sucessos}/{len(perguntas_teste)}")
    print(f"📈 Taxa de sucesso: {(sucessos/len(perguntas_teste))*100:.1f}%")
    
    if sucessos == len(perguntas_teste):
        print("🎉 TODOS OS TESTES PASSARAM!")
    else:
        print("⚠️ ALGUNS TESTES FALHARAM!")
    
    return sucessos == len(perguntas_teste)

def exemplo_uso_programatico():
    """Exemplo de como usar a API programaticamente"""
    
    print("\n" + "=" * 50)
    print("📚 EXEMPLO DE USO PROGRAMÁTICO")
    print("=" * 50)
    
    # URL da API
    base_url = "http://localhost:5000"
    
    # Pergunta
    pergunta = "Quantas linhas ociosas tem o cliente Safra?"
    
    # Preparar dados
    dados = {"pergunta": pergunta}
    
    print(f"📝 Pergunta: {pergunta}")
    print(f"🌐 URL: {base_url}/pergunta")
    print(f"📤 Dados enviados: {json.dumps(dados, ensure_ascii=False, indent=2)}")
    
    try:
        # Fazer requisição
        response = requests.post(
            f"{base_url}/pergunta",
            json=dados,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            resposta = response.json()
            print(f"\n✅ Resposta recebida:")
            print(json.dumps(resposta, ensure_ascii=False, indent=2))
            
            # Extrair informações
            if resposta.get('sucesso'):
                print(f"\n🎯 Resposta da LeIA: {resposta.get('resposta')}")
            else:
                print(f"\n❌ Erro: {resposta.get('resposta')}")
        else:
            print(f"\n❌ Erro HTTP: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Erro de conexão: {e}")
        print("   Certifique-se de que a API está rodando!")

if __name__ == "__main__":
    print("LeIA API - Exemplo de Uso")
    print("Certifique-se de que a API está rodando: python api_json.py")
    print()
    
    # Testar API
    if testar_api_json():
        # Se os testes passaram, mostrar exemplo programático
        exemplo_uso_programatico()
    
    print("\n" + "=" * 50)
    print("✨ Teste concluído!")
    print("=" * 50)
