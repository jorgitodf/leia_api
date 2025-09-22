#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para funcionalidade JSON da LeIA
"""

import json
import sys
import os

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import processar_pergunta_json, preparar_llm_e_embeddings

def testar_pergunta_json(pergunta_texto):
    """Testa uma pergunta em formato JSON"""
    print(f"\n{'='*60}")
    print(f"🧪 TESTANDO PERGUNTA: {pergunta_texto}")
    print(f"{'='*60}")
    
    # Criar JSON de entrada
    entrada_json = {
        "pergunta": pergunta_texto
    }
    
    print("📥 ENTRADA JSON:")
    print(json.dumps(entrada_json, ensure_ascii=False, indent=2))
    
    try:
        # Inicializar LLM (opcional)
        try:
            llm, embeddings = preparar_llm_e_embeddings()
            print("✅ LLM inicializado com sucesso!")
        except Exception as e:
            print(f"⚠️ LLM não disponível: {e}")
            llm, embeddings = None, None
        
        # Processar pergunta
        resposta_json = processar_pergunta_json(entrada_json, llm, embeddings)
        
        print("\n📤 RESPOSTA JSON:")
        print(resposta_json)
        
        # Parsear resposta para verificar estrutura
        resposta_dict = json.loads(resposta_json)
        print(f"\n✅ Estrutura da resposta:")
        print(f"   - Sucesso: {resposta_dict.get('sucesso', 'N/A')}")
        print(f"   - Pergunta: {resposta_dict.get('pergunta', 'N/A')}")
        print(f"   - Timestamp: {resposta_dict.get('timestamp', 'N/A')}")
        print(f"   - Versão: {resposta_dict.get('versao', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO: {str(e)}")
        return False

def main():
    """Função principal de teste"""
    print("🚀 INICIANDO TESTES DA FUNCIONALIDADE JSON")
    print("=" * 60)
    
    # Lista de perguntas para testar
    perguntas_teste = [
        "Qual o fornecedor com maior custo em janeiro de 2024?",
        "Quantas linhas ativas tem o cliente Safra?",
        "Qual usuário teve maior custo no mês atual?",
        "Quantas linhas ociosas tem o cliente Safra?",
        "Quantas linhas no Cliente Safra não possuem termo?",
        "Teste de pergunta inválida para verificar tratamento de erro"
    ]
    
    sucessos = 0
    total = len(perguntas_teste)
    
    for pergunta in perguntas_teste:
        if testar_pergunta_json(pergunta):
            sucessos += 1
    
    print(f"\n{'='*60}")
    print(f"📊 RESULTADO DOS TESTES")
    print(f"{'='*60}")
    print(f"✅ Sucessos: {sucessos}/{total}")
    print(f"❌ Falhas: {total - sucessos}/{total}")
    print(f"📈 Taxa de sucesso: {(sucessos/total)*100:.1f}%")
    
    if sucessos == total:
        print("🎉 TODOS OS TESTES PASSARAM!")
    else:
        print("⚠️ ALGUNS TESTES FALHARAM!")

if __name__ == "__main__":
    main()
