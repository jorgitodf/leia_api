#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste básico da API Flask
"""

from flask import Flask, request, jsonify
import json
import time

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de verificação de saúde da API"""
    return jsonify({
        "status": "ok",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "versao": "1.0"
    })

@app.route('/teste', methods=['POST'])
def teste():
    """Endpoint de teste"""
    try:
        dados = request.get_json()
        return jsonify({
            "sucesso": True,
            "mensagem": "API funcionando!",
            "dados_recebidos": dados,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        return jsonify({
            "sucesso": False,
            "erro": str(e),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 500

@app.route('/', methods=['GET'])
def home():
    """Página inicial"""
    return jsonify({
        "mensagem": "API de Teste LeIA",
        "endpoints": {
            "GET /health": "Verificar status",
            "POST /teste": "Teste básico"
        }
    })

if __name__ == '__main__':
    print("🚀 Iniciando API de Teste...")
    print("🌐 Servidor rodando em http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=False)
