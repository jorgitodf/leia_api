#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API JSON para LeIA - Assistente Virtual (Versão Final)
"""

import os
import sys
import json
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações do banco de dados da API (sobrescreve as do main.py)
API_DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'aws-1-us-east-2.pooler.supabase.com'),
    'port': os.getenv('DB_PORT', '6543'),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres.pfznodcjdxcuwmpcmupg'),
    'password': os.getenv('DB_PASSWORD', '!LeIA@2025'),
    'sslmode': os.getenv('DB_SSLMODE', 'require')
}

# Verificar configurações do banco de dados
def verificar_configuracao_banco():
    """Verifica se as configurações do banco estão corretas"""
    print(f"🔧 Configurações do Banco de Dados:")
    print(f"   Host: {API_DB_CONFIG['host']}")
    print(f"   Port: {API_DB_CONFIG['port']}")
    print(f"   Database: {API_DB_CONFIG['database']}")
    print(f"   User: {API_DB_CONFIG['user']}")
    print(f"   Password: {'***' if API_DB_CONFIG['password'] else 'NÃO DEFINIDA'}")
    print(f"   SSL Mode: {API_DB_CONFIG['sslmode']}")
    
    return API_DB_CONFIG

def conectar_postgres_api():
    """Conecta ao banco de dados PostgreSQL usando configurações da API"""
    try:
        import psycopg2
        conn = psycopg2.connect(**API_DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Erro ao conectar com o PostgreSQL: {e}")
        return None

def pesquisar_no_banco_api(pergunta):
    """Pesquisa inteligente no banco de dados usando configurações da API"""
    pergunta_lower = pergunta.lower()
    
    # Verificar PRIMEIRO se a pergunta é sobre termos de linhas (prioridade)
    termos_termos = ['termo', 'termos', 'possui termo', 'não possuem termo', 'nao possuem termo', 'sem termo']
    if any(termo in pergunta_lower for termo in termos_termos):
        return pesquisar_termos_linhas_api(pergunta)
    
    # Verificar se a pergunta é sobre custos por usuários
    padroes_custos_usuarios = [
        'usuário.*maior.*custo', 'usuario.*maior.*custo', 
        'maior.*custo.*usuário', 'maior.*custo.*usuario',
        'custo.*usuário', 'custo.*usuario', 'usuário.*custo', 'usuario.*custo'
    ]
    
    import re
    for padrao in padroes_custos_usuarios:
        if re.search(padrao, pergunta_lower):
            return pesquisar_custos_usuarios_api(pergunta)
    
    # Verificar também termos simples
    termos_custos_usuarios = ['usuário', 'usuario']
    if any(termo in pergunta_lower for termo in termos_custos_usuarios) and 'custo' in pergunta_lower:
        return pesquisar_custos_usuarios_api(pergunta)
    
    # Verificar se a pergunta é sobre linhas ociosas
    termos_ociosas = ['ociosa', 'ociosas', 'ocioso', 'ociosos']
    for termo in termos_ociosas:
        if termo in pergunta_lower:
            return pesquisar_linhas_ociosas_api(pergunta)
    
    # Verificar se a pergunta é sobre linhas normais
    if any(termo in pergunta_lower for termo in ['linha', 'licenca', 'status', 'ativa', 'bloqueada', 'cancelada', 'total_linhas']):
        return pesquisar_linhas_api(pergunta)
    
    # Se não for sobre linhas, usa a lógica de custos
    return pesquisar_custos_fornecedor_api(pergunta)

def pesquisar_termos_linhas_api(pergunta):
    """Pesquisa específica para a tabela ia_termos_numeros usando configurações da API"""
    try:
        conn = conectar_postgres_api()
        if not conn:
            return "Não foi possível conectar ao banco de dados."
        
        # Importar funções necessárias
        from main import (
            extrair_cliente_pergunta, formatar_inteiro_ptbr, executar_query_direta
        )
        
        resultados = []
        tempo_inicio = time.time()
        
        with conn.cursor() as cursor:
            # Verificar se a tabela ia_termos_numeros existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'ia_termos_numeros'
            """)
            tabela_existe = cursor.fetchone()[0]
            
            if tabela_existe == 0:
                return "A tabela 'ia_termos_numeros' não existe no banco de dados."
            
            # Descobrir a estrutura real da tabela
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'ia_termos_numeros'
                ORDER BY ordinal_position
            """)
            colunas_tabela = cursor.fetchall()
        
        # Encontrar nomes reais das colunas
        coluna_cliente = None
        coluna_possui_termo = None
        coluna_tipo_linha = None
        coluna_status_linha = None
        
        for coluna, tipo in colunas_tabela:
            coluna_lower = coluna.lower()
            if 'cliente' in coluna_lower:
                coluna_cliente = coluna
            elif 'possui_termo' in coluna_lower:
                coluna_possui_termo = coluna
            elif 'tipo_linha' in coluna_lower:
                coluna_tipo_linha = coluna
            elif 'status_linha' in coluna_lower:
                coluna_status_linha = coluna
        
        # Extrair informações da pergunta
        cliente_extraido = extrair_cliente_pergunta(pergunta)
        pergunta_lower = pergunta.lower()
        
        # Configurar filtros
        cliente_capitalizado = cliente_extraido.capitalize() if cliente_extraido else None
        filtro_cliente = f"{coluna_cliente} = '{cliente_capitalizado}'" if cliente_capitalizado else f"{coluna_cliente} IS NOT NULL"
        nome_cliente_filtro = cliente_capitalizado if cliente_capitalizado else "todos os clientes"
        
        # Pergunta 1: Quantas linhas não possuem termo
        if 'não possuem termo' in pergunta_lower or 'nao possuem termo' in pergunta_lower or 'sem termo' in pergunta_lower:
            query_linhas_sem_termo = f"""
            SELECT COUNT(*) as total_sem_termo
            FROM ia_termos_numeros
            WHERE {filtro_cliente}
            AND ({coluna_possui_termo} = 'N' OR {coluna_possui_termo} = 'Não' OR {coluna_possui_termo} = 'NAO' OR {coluna_possui_termo} = 'NÃO' OR {coluna_possui_termo} IS NULL OR {coluna_possui_termo} = '')
            """
            
            resultado_sem_termo = executar_query_direta(conn, query_linhas_sem_termo)
            if resultado_sem_termo is not None and not resultado_sem_termo.empty:
                total_sem_termo = resultado_sem_termo.iloc[0]['total_sem_termo'] or 0
                return f"O Cliente {nome_cliente_filtro} possui {formatar_inteiro_ptbr(total_sem_termo)} linhas sem termos."
            else:
                return f"O Cliente {nome_cliente_filtro} possui 0 linhas sem termos."
        
        return f"Não foi possível processar a pergunta sobre termos para o Cliente {nome_cliente_filtro}."
                    
    except Exception as e:
        return f"Erro durante a pesquisa de termos: {e}"
    finally:
        if 'conn' in locals():
            conn.close()

def pesquisar_custos_usuarios_api(pergunta):
    """Pesquisa específica para a tabela ia_custo_usuarios_linhas usando configurações da API"""
    try:
        conn = conectar_postgres_api()
        if not conn:
            return "Não foi possível conectar ao banco de dados."
        
        # Importar funções necessárias
        from main import (
            extrair_mes_ano, extrair_cliente_pergunta, formatar_moeda,
            construir_filtro_mes, executar_query_direta, extrair_quantidade_meses
        )
        
        resultados = []
        tempo_inicio = time.time()
        
        with conn.cursor() as cursor:
            # Verificar se a tabela existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'ia_custo_usuarios_linhas'
            """)
            tabela_existe = cursor.fetchone()[0]
            
            if tabela_existe == 0:
                return "A tabela 'ia_custo_usuarios_linhas' não existe no banco de dados."
            
            # Descobrir a estrutura real da tabela
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'ia_custo_usuarios_linhas'
                ORDER BY ordinal_position
            """)
            colunas_tabela = cursor.fetchall()
        
        # Encontrar nomes reais das colunas
        coluna_cliente = None
        coluna_nome_usuario = None
        coluna_total = None
        coluna_mes_referencia = None
        tipo_mes_referencia = None
        
        for coluna, tipo in colunas_tabela:
            coluna_lower = coluna.lower()
            if 'cliente' in coluna_lower:
                coluna_cliente = coluna
            elif 'nome_usuario' in coluna_lower or 'usuario' in coluna_lower:
                coluna_nome_usuario = coluna
            elif 'total' in coluna_lower or 'custo' in coluna_lower or 'valor' in coluna_lower:
                coluna_total = coluna
            elif 'mes' in coluna_lower or 'referencia' in coluna_lower or 'data' in coluna_lower:
                coluna_mes_referencia = coluna
                tipo_mes_referencia = tipo
        
        # Extrair informações da pergunta
        ano, mes_numero, mes_nome = extrair_mes_ano(pergunta)
        cliente_extraido = extrair_cliente_pergunta(pergunta)
        pergunta_lower = pergunta.lower()
        
        # Configurar filtros
        cliente_capitalizado = cliente_extraido.capitalize() if cliente_extraido else None
        filtro_cliente = f"{coluna_cliente} = '{cliente_capitalizado}'" if cliente_capitalizado else f"{coluna_cliente} IS NOT NULL"
        nome_cliente_filtro = cliente_capitalizado if cliente_capitalizado else "todos os clientes"
        
        # Detectar tipo de pergunta
        if 'atualmente' in pergunta_lower or 'mês atual' in pergunta_lower:
            # Maior custo no mês atual
            from datetime import datetime
            hoje = datetime.now()
            ano_atual = str(hoje.year)
            mes_atual = str(hoje.month).zfill(2)
            filtro_mes = construir_filtro_mes(coluna_mes_referencia, tipo_mes_referencia, ano_atual, mes_atual)
            
            query_maior_custo_atual = f"""
            SELECT 
                {coluna_nome_usuario} as nome_usuario,
                {coluna_total} as total,
                {coluna_mes_referencia} as mes_referencia
            FROM ia_custo_usuarios_linhas
            WHERE {filtro_cliente}
            {filtro_mes}
            ORDER BY {coluna_total} DESC
            LIMIT 1
            """
            
            resultado_atual = executar_query_direta(conn, query_maior_custo_atual)
            if resultado_atual is not None and not resultado_atual.empty:
                usuario = resultado_atual.iloc[0]['nome_usuario']
                total = resultado_atual.iloc[0]['total']
                total_formatado = formatar_moeda(total)
                mes_formatado = f"{mes_atual}/{ano_atual}"
                return f"O Usuário {usuario} possui o custo no valor de {total_formatado} no mês atual ({mes_formatado})."
            else:
                return f"Não foram encontrados dados de custos para o Cliente {nome_cliente_filtro} no mês atual."
        
        return f"Não foi possível processar a pergunta sobre custos por usuários para o Cliente {nome_cliente_filtro}."
                    
    except Exception as e:
        return f"Erro durante a pesquisa de custos por usuários: {e}"
    finally:
        if 'conn' in locals():
            conn.close()

def pesquisar_linhas_ociosas_api(pergunta):
    """Pesquisa específica para a tabela ia_linhas_ociosas usando configurações da API"""
    try:
        conn = conectar_postgres_api()
        if not conn:
            return "Não foi possível conectar ao banco de dados."
        
        # Importar funções necessárias
        from main import (
            extrair_mes_ano, extrair_cliente_pergunta, formatar_inteiro_ptbr,
            construir_filtro_mes, executar_query_direta, extrair_quantidade_meses
        )
        
        resultados = []
        tempo_inicio = time.time()
        
        with conn.cursor() as cursor:
            # Verificar se a tabela existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'ia_linhas_ociosas'
            """)
            tabela_existe = cursor.fetchone()[0]
            
            if tabela_existe == 0:
                return "A tabela 'ia_linhas_ociosas' não existe no banco de dados."
            
            # Descobrir a estrutura real da tabela
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'ia_linhas_ociosas'
                ORDER BY ordinal_position
            """)
            colunas_tabela = cursor.fetchall()
        
        # Encontrar nomes reais das colunas
        coluna_cliente = None
        coluna_operadora = None
        coluna_mes_referencia = None
        coluna_quantidade = None
        tipo_mes_referencia = None
        
        for coluna, tipo in colunas_tabela:
            coluna_lower = coluna.lower()
            if 'cliente' in coluna_lower:
                coluna_cliente = coluna
            elif 'operadora' in coluna_lower or 'fornecedor' in coluna_lower:
                coluna_operadora = coluna
            elif 'mes' in coluna_lower or 'referencia' in coluna_lower or 'data' in coluna_lower:
                coluna_mes_referencia = coluna
                tipo_mes_referencia = tipo
            elif 'quantidade' in coluna_lower or 'total' in coluna_lower or 'qtd' in coluna_lower:
                coluna_quantidade = coluna
        
        # Extrair informações da pergunta
        ano, mes_numero, mes_nome = extrair_mes_ano(pergunta)
        cliente_extraido = extrair_cliente_pergunta(pergunta)
        pergunta_lower = pergunta.lower()
        
        # Configurar filtros
        cliente_capitalizado = cliente_extraido.capitalize() if cliente_extraido else None
        filtro_cliente = f"{coluna_cliente} = '{cliente_capitalizado}'" if cliente_capitalizado else f"{coluna_cliente} IS NOT NULL"
        nome_cliente_filtro = cliente_capitalizado if cliente_capitalizado else "todos os clientes"
        
        # Detectar tipo de pergunta
        if 'atualmente' in pergunta_lower or 'mês atual' in pergunta_lower:
            # Mês atual
            from datetime import datetime
            hoje = datetime.now()
            ano_atual = str(hoje.year)
            mes_atual = str(hoje.month).zfill(2)
            filtro_mes = construir_filtro_mes(coluna_mes_referencia, tipo_mes_referencia, ano_atual, mes_atual)
            
            query_total_atual = f"""
            SELECT COUNT(*) as total_ociosas
            FROM ia_linhas_ociosas
            WHERE {filtro_cliente}
            {filtro_mes}
            """
            
            resultado_atual = executar_query_direta(conn, query_total_atual)
            if resultado_atual is not None and not resultado_atual.empty:
                total = resultado_atual.iloc[0]['total_ociosas'] or 0
                if total == 1:
                    return f"O Cliente {nome_cliente_filtro} possui atualmente {total} linha ociosa."
                else:
                    return f"O Cliente {nome_cliente_filtro} possui atualmente {total} linhas ociosas."
            else:
                return f"O Cliente {nome_cliente_filtro} possui atualmente 0 linhas ociosas."
        
        return f"Não foi possível processar a pergunta sobre linhas ociosas para o Cliente {nome_cliente_filtro}."
                    
    except Exception as e:
        return f"Erro durante a pesquisa de linhas ociosas: {e}"
    finally:
        if 'conn' in locals():
            conn.close()

def pesquisar_linhas_api(pergunta):
    """Pesquisa específica para a tabela ia_linhas usando configurações da API"""
    try:
        conn = conectar_postgres_api()
        if not conn:
            return "Não foi possível conectar ao banco de dados."
        
        # Importar funções necessárias
        from main import (
            extrair_mes_ano, extrair_cliente_pergunta, formatar_inteiro_ptbr,
            construir_filtro_mes, executar_query_direta
        )
        
        resultados = []
        tempo_inicio = time.time()
        
        with conn.cursor() as cursor:
            # Verificar se a tabela existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'ia_linhas'
            """)
            tabela_existe = cursor.fetchone()[0]
            
            if tabela_existe == 0:
                return "A tabela 'ia_linhas' não existe no banco de dados."
            
            # Descobrir a estrutura real da tabela
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'ia_linhas'
                ORDER BY ordinal_position
            """)
            colunas_tabela = cursor.fetchall()
        
        # Encontrar nomes reais das colunas
        coluna_cliente = None
        coluna_status_licenca = None
        coluna_fornecedor = None
        coluna_total_linhas = None
        coluna_mes_referencia = None
        tipo_mes_referencia = None
        coluna_tipo_contrato = None
        
        for coluna, tipo in colunas_tabela:
            coluna_lower = coluna.lower()
            if 'cliente' in coluna_lower:
                coluna_cliente = coluna
            elif 'status' in coluna_lower and 'licenca' in coluna_lower:
                coluna_status_licenca = coluna
            elif 'fornecedor' in coluna_lower:
                coluna_fornecedor = coluna
            elif 'total_linhas' in coluna_lower or ('total' in coluna_lower and 'linha' in coluna_lower):
                coluna_total_linhas = coluna
            elif 'mes' in coluna_lower or 'referencia' in coluna_lower or 'data' in coluna_lower:
                coluna_mes_referencia = coluna
                tipo_mes_referencia = tipo
            elif 'tipo' in coluna_lower and 'contrato' in coluna_lower:
                coluna_tipo_contrato = coluna
        
        # Extrair informações da pergunta
        ano, mes_numero, mes_nome = extrair_mes_ano(pergunta)
        cliente_extraido = extrair_cliente_pergunta(pergunta)
        
        # Extrair status da licença da pergunta
        status_extraido = None
        status_opcoes = ['ativa', 'bloqueada', 'cancelada']
        pergunta_lower = pergunta.lower()
        
        for status in status_opcoes:
            if status in pergunta_lower:
                status_extraido = status
                break
        
        # Configurar filtros
        filtro_cliente = f"{coluna_cliente} ILIKE '%{cliente_extraido}%'" if cliente_extraido else f"{coluna_cliente} IS NOT NULL"
        filtro_status = f"AND {coluna_status_licenca} ILIKE '%{status_extraido}%'" if status_extraido else ""
        filtro_mes = construir_filtro_mes(coluna_mes_referencia, tipo_mes_referencia, ano, mes_numero) if (mes_numero and ano) else ""
        
        nome_cliente_filtro = cliente_extraido if cliente_extraido else "todos os clientes"
        
        # CONSULTA: Dados brutos para análise
        query_dados_brutos = f"""
        SELECT 
            {coluna_cliente} as cliente,
            {coluna_fornecedor} as fornecedor,
            {coluna_status_licenca} as status_licenca,
            {coluna_mes_referencia} as mes_referencia,
            {coluna_total_linhas} as total_linhas
        FROM ia_linhas
        WHERE {filtro_cliente}
        {filtro_status}
        {filtro_mes}
        ORDER BY {coluna_total_linhas} DESC
        LIMIT 20
        """
        
        resultado_bruto = executar_query_direta(conn, query_dados_brutos)
        if resultado_bruto is not None and not resultado_bruto.empty:
            # Calcular total manualmente
            if coluna_total_linhas in resultado_bruto.columns:
                total_calculado = resultado_bruto[coluna_total_linhas].sum()
                return f"O Cliente {nome_cliente_filtro} possui {formatar_inteiro_ptbr(total_calculado)} linhas."
        
        return f"Não foram encontrados dados de linhas para o Cliente {nome_cliente_filtro}."
                    
    except Exception as e:
        return f"Erro durante a pesquisa de linhas: {e}"
    finally:
        if 'conn' in locals():
            conn.close()

def pesquisar_custos_fornecedor_api(pergunta):
    """Pesquisa específica para a tabela ia_custo_fornecedor usando configurações da API"""
    try:
        conn = conectar_postgres_api()
        if not conn:
            return "Não foi possível conectar ao banco de dados."
        
        # Importar funções necessárias
        from main import (
            extrair_mes_ano, extrair_cliente_pergunta, formatar_moeda,
            construir_filtro_mes, executar_query_direta
        )
        
        resultados = []
        tempo_inicio = time.time()
        
        with conn.cursor() as cursor:
            # Verificar se a tabela existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'ia_custo_fornecedor'
            """)
            tabela_existe = cursor.fetchone()[0]
            
            if tabela_existe == 0:
                return "A tabela 'ia_custo_fornecedor' não existe no banco de dados."
            
            # Descobrir a estrutura real da tabela
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'ia_custo_fornecedor'
                ORDER BY ordinal_position
            """)
            colunas_tabela = cursor.fetchall()
        
        # Encontrar nomes reais das colunas
        coluna_cliente = None
        coluna_fornecedor = None
        coluna_custo = None
        coluna_mes_referencia = None
        coluna_tipo_contrato = None
        
        for coluna, tipo in colunas_tabela:
            coluna_lower = coluna.lower()
            if 'cliente' in coluna_lower:
                coluna_cliente = coluna
            elif 'fornecedor' in coluna_lower:
                coluna_fornecedor = coluna
            elif coluna_lower == 'total' or 'custo' in coluna_lower or 'valor' in coluna_lower or tipo in ['numeric', 'decimal', 'money', 'double precision']:
                coluna_custo = coluna
            elif 'mes' in coluna_lower or 'referencia' in coluna_lower or 'data' in coluna_lower or tipo in ['date', 'timestamp', 'varchar', 'text']:
                coluna_mes_referencia = coluna
            elif 'tipo' in coluna_lower and 'contrato' in coluna_lower:
                coluna_tipo_contrato = coluna
        
        # Extrair informações da pergunta
        ano, mes_numero, mes_nome = extrair_mes_ano(pergunta)
        cliente_extraido = extrair_cliente_pergunta(pergunta)
        
        # Se não extraiu cliente, usar 'safra' como padrão ou buscar todos
        filtro_cliente = f"{coluna_cliente} ILIKE '%{cliente_extraido}%'" if cliente_extraido else f"{coluna_cliente} IS NOT NULL"
        nome_cliente_filtro = cliente_extraido if cliente_extraido else "todos os clientes"
        
        # CONSULTA PRINCIPAL: Para o mês específico solicitado
        if mes_numero and ano and coluna_mes_referencia and coluna_cliente and coluna_fornecedor and coluna_custo:
            filtro_mes = construir_filtro_mes(coluna_mes_referencia, None, ano, mes_numero)
            
            # Incluir tipo_contrato se a coluna existir
            campos_select = f"""
                {coluna_cliente} as cliente,
                {coluna_fornecedor} as fornecedor,
                {coluna_mes_referencia} as mes_referencia,
                {coluna_custo} as custo"""
            
            if coluna_tipo_contrato:
                campos_select += f",\n                {coluna_tipo_contrato} as tipo_contrato"
            
            query_mes_exato = f"""
            SELECT 
                {campos_select}
            FROM ia_custo_fornecedor 
            WHERE {filtro_cliente}
            {filtro_mes}
            ORDER BY {coluna_custo} DESC
            LIMIT 1
            """
            
            resultado_mes_exato = executar_query_direta(conn, query_mes_exato)
            if resultado_mes_exato is not None and not resultado_mes_exato.empty:
                fornecedor = resultado_mes_exato.iloc[0]['fornecedor']
                custo = resultado_mes_exato.iloc[0]['custo']
                tipo_contrato = resultado_mes_exato.iloc[0].get('tipo_contrato', 'N/A')
                
                custo_formatado = formatar_moeda(custo)
                return f"O Cliente {nome_cliente_filtro}, o fornecedor com o maior custo no mês de {mes_nome} de {ano} é {fornecedor}, com um custo total de {custo_formatado}, tipo de contrato {tipo_contrato}."
        
        return f"Não foram encontrados dados de custos para o Cliente {nome_cliente_filtro}."
                    
    except Exception as e:
        return f"Erro durante a pesquisa de custos: {e}"
    finally:
        if 'conn' in locals():
            conn.close()

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
            # Importar apenas quando necessário
            from main import preparar_llm_e_embeddings
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
        
        # Importar funções necessárias
        from main import (
            extrair_palavras_chave, pesquisar_tabela_especifica,
            executar_query_direta, extrair_cliente_pergunta, extrair_mes_ano,
            formatar_moeda, formatar_dataframe_moeda, formatar_valores_monetarios_no_texto,
            formatar_inteiro_ptbr, construir_filtro_mes, detectar_tabela_e_campos,
            pesquisar_linhas, pesquisar_custos_usuarios, pesquisar_linhas_ociosas,
            pesquisar_termos_linhas, _cosine_similarity, construir_rag_prompt,
            responder_com_rag
        )
        
        # Pesquisar no banco de dados usando configurações da API
        dados_banco = pesquisar_no_banco_api(pergunta)
        
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

@app.route('/config', methods=['GET'])
def verificar_config():
    """Endpoint para verificar configurações do banco de dados"""
    config = verificar_configuracao_banco()
    return jsonify({
        "configuracao_banco": {
            "host": config['host'],
            "port": config['port'],
            "database": config['database'],
            "user": config['user'],
            "password": "***" if config['password'] else "NÃO DEFINIDA",
            "sslmode": config['sslmode']
        },
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
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
            "GET /config": "Verificar configurações do banco de dados",
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
    print("🚀 Inicializando LeIA API (Versão Final)...")
    
    # Verificar configurações do banco de dados
    verificar_configuracao_banco()
    
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
    print(f"🔧 Configurações do banco em http://{host}:{port}/config")
    
    # Iniciar servidor
    app.run(host=host, port=port, debug=debug)
