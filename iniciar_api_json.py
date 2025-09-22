#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para iniciar a API JSON da LeIA sem executar o loop principal
"""

import os
import sys
import subprocess

def iniciar_api():
    """Inicia a API JSON da LeIA"""
    print("🚀 Iniciando LeIA API JSON...")
    
    # Verificar se o arquivo existe
    if not os.path.exists('api_json_final.py'):
        print("❌ Arquivo api_json_final.py não encontrado!")
        return False
    
    try:
        # Iniciar a API
        print("🌐 Iniciando servidor...")
        subprocess.run([sys.executable, 'api_json_final.py'], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao iniciar API: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 API interrompida pelo usuário")
        return True

if __name__ == "__main__":
    iniciar_api()
