import os, sys
import streamlit as st
import time
from datetime import datetime

# Silenciar logs do gRPC/ALTS via env e ocultar stderr apenas durante import Google
os.environ.setdefault("GRPC_VERBOSITY", "ERROR")
os.environ.setdefault("GLOG_minloglevel", "3")
# Reduzir verbosidade de bibliotecas nativas relacionadas
os.environ.setdefault("ABSL_LOG_LEVEL", "3")  # 0=INFO,1=WARNING,2=ERROR,3=FATAL
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

# Supressão global de stderr (Python e C) para eliminar WARNINGS nativos precoces
_SILENCE_ACTIVE = False
_SAVED_FD2 = None
_DEVNULL_FD = None
_DEVNULL_PY = None

def _silence_stderr_start():
    global _SILENCE_ACTIVE, _SAVED_FD2, _DEVNULL_FD, _DEVNULL_PY
    if _SILENCE_ACTIVE:
        return
    _SILENCE_ACTIVE = True
    _DEVNULL_PY = open(os.devnull, 'w')
    sys.stderr = _DEVNULL_PY
    _SAVED_FD2 = os.dup(2)
    _DEVNULL_FD = os.open(os.devnull, os.O_WRONLY)
    os.dup2(_DEVNULL_FD, 2)

def _silence_stderr_stop():
    global _SILENCE_ACTIVE, _SAVED_FD2, _DEVNULL_FD, _DEVNULL_PY
    if not _SILENCE_ACTIVE:
        return
    try:
        os.dup2(_SAVED_FD2, 2)
    finally:
        try:
            os.close(_SAVED_FD2)
        except Exception:
            pass
        try:
            os.close(_DEVNULL_FD)
        except Exception:
            pass
        try:
            _DEVNULL_PY.close()
        except Exception:
            pass
        sys.stderr = sys.__stderr__
        _SILENCE_ACTIVE = False

# Inicia supressão cedo (antes de imports que podem disparar logs nativos)
_silence_stderr_start()

from contextlib import contextmanager

@contextmanager
def _suppress_stderr_during_imports():
    """Suprime stderr Python e também o stderr de nível C (fd 2) temporariamente."""
    original_stderr = sys.stderr
    devnull_py = open(os.devnull, 'w')
    # Redireciona stderr Python
    sys.stderr = devnull_py
    # Redireciona fd 2 (C-level)
    saved_fd = os.dup(2)
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull_fd, 2)
    try:
        yield
    finally:
        try:
            os.dup2(saved_fd, 2)
        finally:
            try:
                os.close(saved_fd)
            except Exception:
                pass
            try:
                os.close(devnull_fd)
            except Exception:
                pass
            sys.stderr = original_stderr
            try:
                devnull_py.close()
            except Exception:
                pass

from langchain.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
with _suppress_stderr_during_imports():
    import google.generativeai as genai
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
import numpy as np
from dotenv import load_dotenv, find_dotenv

# Carrega variáveis do .env de forma robusta (ordem: pasta do script, detectado via find_dotenv, diretório atual)
_env_loaded = False
try:
    # 1) .env ao lado do script
    _env_loaded = load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env")) or _env_loaded
    # 2) .env mais próximo subindo diretórios
    _found = find_dotenv(usecwd=True)
    if _found:
        _env_loaded = load_dotenv(_found) or _env_loaded
    # 3) .env no CWD atual
    _env_loaded = load_dotenv() or _env_loaded
except Exception:
    pass

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql
import pandas as pd
import re

load_dotenv()

# Configurações de conexão com o PostgreSQL (importadas do .env)
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5441'),
    'database': os.getenv('DB_NAME', 'LeIA'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

# Importar todas as funções do main.py
from main import (
    conectar_postgres, extrair_palavras_chave, pesquisar_tabela_especifica,
    executar_query_direta, extrair_cliente_pergunta, extrair_mes_ano,
    formatar_moeda, formatar_dataframe_moeda, formatar_valores_monetarios_no_texto,
    formatar_inteiro_ptbr, construir_filtro_mes, detectar_tabela_e_campos,
    pesquisar_linhas, pesquisar_custos_usuarios, pesquisar_linhas_ociosas,
    pesquisar_no_banco, _cosine_similarity, construir_rag_prompt,
    preparar_llm_e_embeddings, responder_com_rag
)

# Configuração da página Streamlit
st.set_page_config(
    page_title="LeIA - Assistente Virtual",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para melhorar a aparência
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    .user-message {
        background-color: #f0f2f6;
        border-left-color: #667eea;
    }
    .assistant-message {
        background-color: #e8f4fd;
        border-left-color: #764ba2;
    }
    .welcome-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        text-align: center;
        font-size: 1.1em;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        border: none;
    }
    .stTextInput > div > div > input {
        border-radius: 25px;
        border: 2px solid #e0e0e0;
        padding: 12px 20px;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        outline: none;
    }
    .stButton > button {
        border-radius: 25px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    .chat-input-container {
        background: white;
        padding: 1rem;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar o estado da sessão
if 'messages' not in st.session_state:
    st.session_state.messages = []
    # Adicionar mensagem de boas-vindas inicial
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Olá, sou a sua assistente virtual LeIA, como posso te ajudar hoje?"
    })
if 'llm_initialized' not in st.session_state:
    st.session_state.llm_initialized = False
if 'llm' not in st.session_state:
    st.session_state.llm = None
if 'embeddings' not in st.session_state:
    st.session_state.embeddings = None
if 'modo_sem_llm' not in st.session_state:
    st.session_state.modo_sem_llm = False

def inicializar_llm():
    """Inicializa o LLM e embeddings se ainda não foram inicializados"""
    if not st.session_state.llm_initialized:
        try:
            with st.spinner("Inicializando assistente virtual..."):
                st.session_state.llm, st.session_state.embeddings = preparar_llm_e_embeddings()
                st.session_state.modo_sem_llm = False
                st.session_state.llm_initialized = True
                st.success("✅ Assistente virtual inicializado com sucesso!")
        except Exception as e:
            st.warning(f"⚠️ Aviso: {e}")
            st.info("Operando sem LLM. Somente exibindo os resultados da base.")
            st.session_state.llm, st.session_state.embeddings = None, None
            st.session_state.modo_sem_llm = True
            st.session_state.llm_initialized = True

def processar_pergunta(pergunta):
    """Processa a pergunta e retorna a resposta"""
    if not pergunta.strip():
        return "Por favor, digite uma pergunta."
    
    # Pesquisar no banco de dados
    with st.spinner("🔍 Analisando sua pergunta..."):
        dados_banco = pesquisar_no_banco(pergunta)
    
    # Verificar se é uma resposta de custos por usuários (já formatada)
    if (dados_banco.startswith("O Usuário") or dados_banco.startswith("Nos últimos 3 meses") or 
        dados_banco.startswith("Não foram encontrados dados de custos") or 
        dados_banco.startswith("--- INFORMAÇÕES EXTRAÍDAS DA PERGUNTA ---")):
        return dados_banco
    
    # Verificar se é uma resposta de linhas ociosas (já formatada)
    elif (dados_banco.startswith("O Cliente") and 
        ("linhas ociosas" in dados_banco or "linha ociosa" in dados_banco or 
         "possui atualmente" in dados_banco or "possuiu em" in dados_banco or 
         "possuiu nos últimos" in dados_banco)):
        return dados_banco
    
    # Verificar se é uma resposta de linhas normais (deve passar pelo RAG)
    elif ("--- LINHAS POR FORNECEDOR" in dados_banco or 
          "--- TOTAL POR FORNECEDOR" in dados_banco or
          "--- DADOS BRUTOS" in dados_banco or
          "--- DEBUG:" in dados_banco):
        # Passar pelo RAG para formatar a resposta
        if not st.session_state.modo_sem_llm:
            try:
                with st.spinner("🤖 Processando resposta com IA..."):
                    resposta = responder_com_rag(pergunta, dados_banco, st.session_state.llm, st.session_state.embeddings, top_k=6)
                return resposta
            except Exception as e:
                st.error(f"Erro ao gerar resposta: {e}")
                return f"Dados do banco (sem processamento IA):\n\n{dados_banco}"
        else:
            return f"Dados do banco de dados:\n\n{dados_banco}"
    else:
        if st.session_state.modo_sem_llm:
            return f"Dados do banco de dados:\n\n{dados_banco}"
        else:
            try:
                with st.spinner("🤖 Processando resposta com IA..."):
                    resposta = responder_com_rag(pergunta, dados_banco, st.session_state.llm, st.session_state.embeddings, top_k=6)
                return resposta
            except Exception as e:
                st.error(f"Erro ao gerar resposta: {e}")
                return f"Dados do banco (sem processamento IA):\n\n{dados_banco}"

def main():
    # Cabeçalho principal
    st.markdown("""
    <div class="main-header">
        <h1>🤖 LeIA - Assistente Virtual</h1>
        <p>Sistema Inteligente de Análise de Dados</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar com informações
    with st.sidebar:
        st.header("ℹ️ Sobre a LeIA")
        st.markdown("""
        **LeIA** é sua assistente virtual especializada em análise de dados empresariais.
        
        ### 🎯 O que posso fazer:
        - 📊 Análise de custos por fornecedor
        - 📱 Consulta de linhas telefônicas
        - 👥 Análise de custos por usuário
        - 📈 Relatórios de linhas ociosas
        - 🔍 Pesquisas inteligentes no banco de dados
        
        ### 💡 Exemplos de perguntas:
        - "Qual o fornecedor com maior custo no mês de janeiro de 2024?"
        - "Quantas linhas ativas tem o cliente Safra?"
        - "Quem foi o usuário com maior custo no mês atual?"
        - "Quantas linhas ociosas tem o cliente Sotreq?"
        """)
        
        st.header("⚙️ Status do Sistema")
        if st.session_state.llm_initialized:
            if st.session_state.modo_sem_llm:
                st.warning("🔧 Modo: Apenas Banco de Dados")
                st.info("LLM não disponível. Apenas dados brutos serão exibidos.")
            else:
                st.success("✅ Modo: IA Completa")
                st.info("LLM e RAG funcionando normalmente.")
        else:
            st.info("🔄 Inicializando sistema...")
        
        # Botão para limpar histórico
        if st.button("🗑️ Limpar Histórico"):
            st.session_state.messages = []
            st.rerun()
    
    # Inicializar LLM se necessário
    if not st.session_state.llm_initialized:
        inicializar_llm()
    
    # Container principal do chat
    chat_container = st.container()
    
    # Exibir histórico de mensagens
    with chat_container:
        for i, message in enumerate(st.session_state.messages):
            # Destacar a mensagem de boas-vindas inicial
            if i == 0 and message["role"] == "assistant" and "Olá, sou a sua assistente virtual LeIA" in message["content"]:
                st.markdown(f"""
                <div class="welcome-message">
                    <strong>🤖 {message["content"]}</strong>
                </div>
                """, unsafe_allow_html=True)
            else:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
    
    # Seção de exemplos de perguntas (apenas se não há mensagens além da inicial)
    if len(st.session_state.messages) <= 1:
        st.markdown("### 💡 Exemplos de perguntas que posso responder:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **📊 Custos por Fornecedor:**
            - Qual o fornecedor com maior custo em janeiro de 2024?
            - Quais são os custos do cliente Safra em dezembro de 2023?
            
            **📱 Linhas Telefônicas:**
            - Quantas linhas ativas tem o cliente Safra?
            - Quantas linhas bloqueadas tem o cliente Sonda?
            """)
        
        with col2:
            st.markdown("""
            **👥 Custos por Usuário:**
            - Qual usuário teve maior custo no mês atual?
            - Quem foi o usuário com maior custo em agosto de 2024?
            
            **📈 Linhas Ociosas:**
            - Quantas linhas ociosas tem o cliente Safra?
            - Quantas linhas ociosas por operadora tem o Sotreq?
            """)
        
        st.markdown("---")
    
    # Container para input de pergunta
    st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
    
    # Input para nova pergunta com placeholder mais descritivo
    prompt = st.chat_input(
        "💬 Digite sua pergunta aqui... (ex: Qual o fornecedor com maior custo em janeiro de 2024?)",
        key="chat_input"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if prompt:
        # Adicionar mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Exibir mensagem do usuário
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Processar pergunta e gerar resposta
        with st.chat_message("assistant"):
            resposta = processar_pergunta(prompt)
            st.markdown(resposta)
        
        # Adicionar resposta ao histórico
        st.session_state.messages.append({"role": "assistant", "content": resposta})
        
        # Limpar o input após enviar
        st.rerun()
    
    # Rodapé
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8em;">
        <p>LeIA - Assistente Virtual | Powered by Gemini 2.5 Flash + RAG</p>
        <p>Para encerrar, feche esta aba do navegador</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
