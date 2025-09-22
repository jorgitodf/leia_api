#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API JSON para LeIA - Assistente Virtual (Versão Corrigida)
Endpoint para receber perguntas em formato JSON e retornar respostas em JSON
"""

import os
import sys
import json
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

# Adicionar o diretório atual ao path para importar main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar apenas as funções necessárias do main.py
from main import (
    processar_pergunta_json, 
    preparar_llm_e_embeddings,
    formatar_resposta_json,
    conectar_postgres,
    pesquisar_no_banco,
    responder_com_rag
)

# Configurar Flask
app = Flask(__name__)
CORS(app)  # Permitir CORS para requisições de diferentes origens

# Variáveis globais para LLM
llm_global = None
embeddings_global = None
llm_initialized = False

def inicializar_llm():
    """Inicializa o LLM e embeddings globalmente"""
    global llm_global, embeddings_global, llm_initialized
    
    if not llm_initialized:
        try:
            llm_global, embeddings_global = preparar_llm_e_embeddings()
            llm_initialized = True
            print("✅ LLM e embeddings inicializados com sucesso!")
        except Exception as e:
            print(f"⚠️ Aviso: {e}")
            print("Operando sem LLM. Apenas dados brutos serão retornados.")
            llm_global, embeddings_global = None, None
            llm_initialized = True

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de verificação de saúde da API"""
    return jsonify({
        "status": "ok",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "versao": "1.0",
        "llm_disponivel": llm_global is not None
    })

@app.route('/pergunta', methods=['POST'])
def processar_pergunta():
    """Endpoint principal para processar perguntas em JSON"""
    try:
        # Verificar se o conteúdo é JSON
        if not request.is_json:
            return jsonify({
                "sucesso": False,
                "erro": "Content-Type deve ser application/json",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }), 400
        
        # Obter dados JSON
        dados_json = request.get_json()
        
        if not dados_json:
            return jsonify({
                "sucesso": False,
                "erro": "JSON vazio ou inválido",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }), 400
        
        # Processar pergunta
        resposta_json = processar_pergunta_json(dados_json, llm_global, embeddings_global)
        
        # Converter resposta JSON string para dict
        resposta_dict = json.loads(resposta_json)
        
        # Retornar resposta
        return jsonify(resposta_dict)
    
    except Exception as e:
        return jsonify({
            "sucesso": False,
            "erro": f"Erro interno do servidor: {str(e)}",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 500

@app.route('/exemplos', methods=['GET'])
def obter_exemplos():
    """Endpoint para obter exemplos de perguntas"""
    exemplos = {
        "exemplos": [
            {
                "categoria": "Custos por Fornecedor",
                "perguntas": [
                    "Qual o fornecedor com maior custo em janeiro de 2024?",
                    "Quais são os custos do cliente Safra em dezembro de 2023?"
                ]
            },
            {
                "categoria": "Linhas Telefônicas",
                "perguntas": [
                    "Quantas linhas ativas tem o cliente Safra?",
                    "Quantas linhas bloqueadas tem o cliente Sonda?"
                ]
            },
            {
                "categoria": "Custos por Usuário",
                "perguntas": [
                    "Qual usuário teve maior custo no mês atual?",
                    "Quem foi o usuário com maior custo em agosto de 2024?"
                ]
            },
            {
                "categoria": "Linhas Ociosas",
                "perguntas": [
                    "Quantas linhas ociosas tem o cliente Safra?",
                    "Quantas linhas ociosas por operadora tem o Sotreq?"
                ]
            },
            {
                "categoria": "Termos de Linhas",
                "perguntas": [
                    "Quantas linhas no Cliente Safra não possuem termo?",
                    "Do total de linhas sem termos no Cliente Safra, me mostre o total por tipo de linha"
                ]
            }
        ],
        "formato_entrada": {
            "pergunta": "Sua pergunta aqui",
            "exemplo": {
                "pergunta": "Qual o fornecedor com maior custo em janeiro de 2024?"
            }
        },
        "formato_saida": {
            "sucesso": True,
            "pergunta": "Pergunta original",
            "resposta": "Resposta da LeIA",
            "timestamp": "2024-01-01 12:00:00",
            "versao": "1.0"
        }
    }
    
    return jsonify(exemplos)

@app.route('/', methods=['GET'])
def home():
    """Página inicial da API"""
    return jsonify({
        "mensagem": "LeIA API - Assistente Virtual",
        "versao": "1.0",
        "endpoints": {
            "POST /pergunta": "Processar pergunta em JSON",
            "GET /exemplos": "Obter exemplos de perguntas",
            "GET /health": "Verificar status da API",
            "GET /": "Esta página"
        },
        "exemplo_uso": {
            "url": "/pergunta",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json"
            },
            "body": {
                "pergunta": "Qual o fornecedor com maior custo em janeiro de 2024?"
            }
        }
    })

if __name__ == '__main__':
    print("🚀 Inicializando LeIA API...")
    
    # Inicializar LLM
    inicializar_llm()
    
    # Configurações do servidor
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', 5000))
    debug = os.getenv('API_DEBUG', 'False').lower() == 'true'
    
    print(f"🌐 Servidor rodando em http://{host}:{port}")
    print(f"📚 Documentação disponível em http://{host}:{port}/")
    print(f"🔍 Exemplos disponíveis em http://{host}:{port}/exemplos")
    print(f"❤️ Health check em http://{host}:{port}/health")
    
    # Iniciar servidor
    app.run(host=host, port=port, debug=debug)
