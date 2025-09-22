#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API JSON para LeIA - Assistente Virtual (Versão Standalone)
Endpoint para receber perguntas em formato JSON e retornar respostas em JSON
"""

import os
import sys
import json
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar apenas as funções necessárias sem executar o loop principal
try:
    # Importar funções específicas
    from main import (
        conectar_postgres, extrair_palavras_chave, pesquisar_tabela_especifica,
        executar_query_direta, extrair_cliente_pergunta, extrair_mes_ano,
        formatar_moeda, formatar_dataframe_moeda, formatar_valores_monetarios_no_texto,
        formatar_inteiro_ptbr, construir_filtro_mes, detectar_tabela_e_campos,
        pesquisar_linhas, pesquisar_custos_usuarios, pesquisar_linhas_ociosas,
        pesquisar_termos_linhas, pesquisar_no_banco, _cosine_similarity, construir_rag_prompt,
        preparar_llm_e_embeddings, responder_com_rag
    )
    print("✅ Funções importadas com sucesso!")
except Exception as e:
    print(f"❌ Erro ao importar funções: {e}")
    sys.exit(1)

# Configurar Flask
app = Flask(__name__)
CORS(app)

# Variáveis globais
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

def processar_entrada_json(entrada_json):
    """Processa entrada JSON e extrai a pergunta"""
    try:
        if isinstance(entrada_json, str):
            dados = json.loads(entrada_json)
        else:
            dados = entrada_json
        
        # Extrair pergunta do JSON
        pergunta = dados.get('pergunta', dados.get('question', dados.get('query', '')))
        
        if not pergunta:
            return None, {"erro": "Campo 'pergunta' não encontrado no JSON"}
        
        return pergunta, None
    
    except json.JSONDecodeError as e:
        return None, {"erro": f"JSON inválido: {str(e)}"}
    except Exception as e:
        return None, {"erro": f"Erro ao processar entrada: {str(e)}"}

def formatar_resposta_json(resposta_texto, pergunta, sucesso=True, dados_extras=None):
    """Formata resposta em JSON"""
    try:
        resposta_json = {
            "sucesso": sucesso,
            "pergunta": pergunta,
            "resposta": resposta_texto,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "versao": "1.0"
        }
        
        if dados_extras:
            resposta_json["dados_extras"] = dados_extras
        
        return json.dumps(resposta_json, ensure_ascii=False, indent=2)
    
    except Exception as e:
        erro_json = {
            "sucesso": False,
            "pergunta": pergunta if pergunta else "N/A",
            "resposta": f"Erro ao formatar resposta JSON: {str(e)}",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "versao": "1.0"
        }
        return json.dumps(erro_json, ensure_ascii=False, indent=2)

def processar_pergunta_json_api(entrada_json):
    """Processa pergunta em formato JSON e retorna resposta em JSON"""
    try:
        # Processar entrada JSON
        pergunta, erro = processar_entrada_json(entrada_json)
        if erro:
            return formatar_resposta_json("", "", False, erro)
        
        if not pergunta.strip():
            return formatar_resposta_json("Por favor, digite uma pergunta válida.", pergunta, False)
        
        # Pesquisar no banco de dados
        dados_banco = pesquisar_no_banco(pergunta)
        
        # Verificar se é uma resposta já formatada (custos por usuários, linhas ociosas, termos)
        if (dados_banco.startswith("O Usuário") or 
            dados_banco.startswith("Nos últimos") or 
            dados_banco.startswith("No último mês") or
            dados_banco.startswith("Não foram encontrados dados de custos") or 
            dados_banco.startswith("--- INFORMAÇÕES EXTRAÍDAS DA PERGUNTA ---")):
            return formatar_resposta_json(dados_banco, pergunta, True)
        
        # Verificar se é uma resposta de linhas ociosas (já formatada)
        elif (dados_banco.startswith("O Cliente") and 
            ("linhas ociosas" in dados_banco or "linha ociosa" in dados_banco or 
             "possui atualmente" in dados_banco or "possuiu em" in dados_banco or 
             "possuiu nos últimos" in dados_banco)):
            return formatar_resposta_json(dados_banco, pergunta, True)
        
        # Verificar se é uma resposta sobre termos de linhas (já formatada)
        elif (dados_banco.startswith("O Cliente") and 
            ("linhas sem termos" in dados_banco or "linha sem termo" in dados_banco or 
             "são do tipo" in dados_banco or "estão Ativas são do tipo" in dados_banco)):
            return formatar_resposta_json(dados_banco, pergunta, True)
        
        # Verificar se é uma resposta de linhas normais (deve passar pelo RAG)
        elif ("--- LINHAS POR FORNECEDOR" in dados_banco or 
              "--- TOTAL POR FORNECEDOR" in dados_banco or
              "--- DADOS BRUTOS" in dados_banco or
              "--- DEBUG:" in dados_banco):
            # Passar pelo RAG para formatar a resposta
            if llm_global and embeddings_global:
                try:
                    resposta = responder_com_rag(pergunta, dados_banco, llm_global, embeddings_global, top_k=6)
                    return formatar_resposta_json(resposta, pergunta, True)
                except Exception as e:
                    return formatar_resposta_json(f"Dados do banco (sem processamento IA):\n\n{dados_banco}", pergunta, True, {"erro_ia": str(e)})
            else:
                return formatar_resposta_json(f"Dados do banco de dados:\n\n{dados_banco}", pergunta, True)
        else:
            if llm_global and embeddings_global:
                try:
                    resposta = responder_com_rag(pergunta, dados_banco, llm_global, embeddings_global, top_k=6)
                    return formatar_resposta_json(resposta, pergunta, True)
                except Exception as e:
                    return formatar_resposta_json(f"Dados do banco (sem processamento IA):\n\n{dados_banco}", pergunta, True, {"erro_ia": str(e)})
            else:
                return formatar_resposta_json(f"Dados do banco de dados:\n\n{dados_banco}", pergunta, True)
    
    except Exception as e:
        return formatar_resposta_json(f"Erro interno: {str(e)}", pergunta if 'pergunta' in locals() else "", False)

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
        resposta_json = processar_pergunta_json_api(dados_json)
        
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
    print("🚀 Inicializando LeIA API (Standalone)...")
    
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
