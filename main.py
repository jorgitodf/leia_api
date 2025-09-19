import os, sys
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
import time
import sys

load_dotenv()

# Configurações de conexão com o PostgreSQL (importadas do .env)
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5441'),
    'database': os.getenv('DB_NAME', 'LeIA'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

def conectar_postgres():
    """Conecta ao banco de dados PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Erro ao conectar com o PostgreSQL: {e}")
        return None

def extrair_palavras_chave(pergunta):
    """Extrai palavras-chave relevantes da pergunta"""
    # Remover palavras comuns e manter termos importantes
    stop_words = ['qual', 'é', 'o', 'a', 'os', 'as', 'do', 'da', 'dos', 'das', 'de', 'com', 'para', 'no', 'na', 'em', 'por', 'que']
    palavras = re.findall(r'\b\w+\b', pergunta.lower())
    palavras_chave = [p for p in palavras if p not in stop_words and len(p) > 2]
    return palavras_chave

def imprimir_digitando(texto, delay_segundos=0.02):
    """Imprime o texto simulando digitação, caractere por caractere."""
    try:
        for caractere in str(texto):
            sys.stdout.write(caractere)
            sys.stdout.flush()
            time.sleep(delay_segundos)
    finally:
        if not str(texto).endswith("\n"):
            sys.stdout.write("\n")
            sys.stdout.flush()

def pesquisar_tabela_especifica(conn, tabela, palavras_chave):
    """Pesquisa em uma tabela específica com palavras-chave"""
    try:
        with conn.cursor() as cursor:
            # Obter colunas da tabela
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{tabela}'
            """)
            colunas = [row[0] for row in cursor.fetchall()]
            
            if not colunas:
                return None
            
            # Construir query de pesquisa mais inteligente
            conditions = []
            params = []
            
            for coluna in colunas:
                for palavra in palavras_chave:
                    conditions.append(f"{coluna}::text ILIKE %s")
                    params.append(f"%{palavra}%")
            
            if conditions:
                where_clause = " OR ".join(conditions)
                query = f"SELECT * FROM {tabela} WHERE {where_clause} LIMIT 20"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                if rows:
                    col_names = [desc[0] for desc in cursor.description]
                    df = pd.DataFrame(rows, columns=col_names)
                    return df
                    
    except Exception as e:
        print(f"Erro ao pesquisar na tabela {tabela}: {e}")
    
    return None

def executar_query_direta(conn, query):
    """Executa uma query SQL diretamente"""
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            if rows:
                col_names = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(rows, columns=col_names)
                return df
    except Exception as e:
        print(f"Erro ao executar query: {e}")
    return None

def extrair_cliente_pergunta(pergunta):
    """Extrai o nome do cliente da pergunta do usuário"""
    # Lista de clientes conhecidos (pode ser expandida)
    clientes_conhecidos = ['safra', 'sotreq', 'verzani', 'sonda', 'direcional', 'mdr']
    
    pergunta_lower = pergunta.lower()
    
    # Procurar por clientes conhecidos na pergunta
    for cliente in clientes_conhecidos:
        if cliente in pergunta_lower:
            return cliente
    
    # Se não encontrou cliente específico, procurar padrões comuns
    padroes_cliente = [
        r'cliente\s+(\w+)',
        r'do\s+cliente\s+(\w+)',
        r'no\s+cliente\s+(\w+)',
        r'para\s+o\s+cliente\s+(\w+)',
        r'customer\s+(\w+)',
        r'client\s+(\w+)'
    ]
    
    for padrao in padroes_cliente:
        match = re.search(padrao, pergunta_lower)
        if match:
            cliente_extraido = match.group(1)
            # Remover palavras comuns que podem vir junto
            palavras_remover = ['o', 'a', 'os', 'as', 'do', 'da', 'dos', 'das', 'de', 'com']
            if cliente_extraido not in palavras_remover:
                return cliente_extraido
    
    # Se não encontrou nenhum cliente específico, retorna None
    return None    

def extrair_mes_ano(pergunta):
    """Extrai mês e ano da pergunta de forma mais precisa"""
    pergunta_lower = pergunta.lower()
    
    meses = {
        'janeiro': '01', 'fevereiro': '02', 'março': '03', 'marco': '03',
        'abril': '04', 'maio': '05', 'junho': '06', 'julho': '07',
        'agosto': '08', 'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
    }
    
    ano = None
    mes_numero = None
    mes_nome = None
    
    # Extrair ano primeiro
    ano_match = re.search(r'20\d{2}', pergunta)
    if ano_match:
        ano = ano_match.group()
    
    # Extrair mês de forma mais precisa - procurando palavras inteiras
    palavras = re.findall(r'\b\w+\b', pergunta_lower)
    
    for palavra in palavras:
        if palavra in meses:
            mes_numero = meses[palavra]
            mes_nome = palavra.capitalize()
            break
    
    # Se não encontrou por palavra inteira, tentar por substring (mais conservador)
    if mes_numero is None:
        for mes, num in meses.items():
            # Usar regex para encontrar a palavra do mês como palavra inteira
            if re.search(r'\b' + mes + r'\b', pergunta_lower):
                mes_numero = num
                mes_nome = mes.capitalize()
                break
    
    return ano, mes_numero, mes_nome

def formatar_moeda(valor):
    """Formata valores para o padrão monetário brasileiro R$ 1.234.567,89"""
    try:
        if valor is None:
            return "R$ 0,00"
        
        # Converter para float se for string
        if isinstance(valor, str):
            # Remover possíveis formatações existentes
            valor = valor.replace('R$', '').replace('.', '').replace(',', '.').strip()
            valor = float(valor)
        
        # Formatar para o padrão brasileiro
        valor_formatado = f"R$ {valor:,.2f}"
        valor_formatado = valor_formatado.replace(',', 'X').replace('.', ',').replace('X', '.')
        return valor_formatado
    except (ValueError, TypeError):
        return f"R$ {valor}"

def formatar_dataframe_moeda(df, coluna_custo):
    """Formata a coluna de custo de um DataFrame para moeda brasileira"""
    if coluna_custo in df.columns:
        df[coluna_custo] = df[coluna_custo].apply(formatar_moeda)
    return df    

def formatar_valores_monetarios_no_texto(texto):
    """Encontra números monetários no texto e aplica formato BR (R$ 1.234.567,89)."""
    if not isinstance(texto, str) or not texto:
        return texto
    # Captura valores com 2 casas decimais, tolerando separadores de milhar (.,) em qualquer ordem
    padrao = re.compile(r"\b\d{1,3}(?:[\.,]\d{3})*[\.,]\d{2}\b|\b\d+[\.,]\d{2}\b")
    def _sub(m):
        raw = m.group(0)
        s = raw.strip().replace('R$', '').strip()
        try:
            if ',' in s and '.' in s:
                # Define o separador decimal como o último entre '.' e ','
                last_dot = s.rfind('.')
                last_comma = s.rfind(',')
                if last_comma > last_dot:
                    decimal_sep, thousand_sep = ',', '.'
                else:
                    decimal_sep, thousand_sep = '.', ','
                s_std = s.replace(thousand_sep, '').replace(decimal_sep, '.')
            elif ',' in s:
                parte_int, parte_frac = s.rsplit(',', 1)
                if len(parte_frac) == 2:
                    s_std = parte_int.replace('.', '').replace(' ', '') + '.' + parte_frac
                else:
                    s_std = s.replace(',', '')
            elif '.' in s:
                parte_int, parte_frac = s.rsplit('.', 1)
                if len(parte_frac) == 2:
                    s_std = parte_int.replace(',', '').replace(' ', '') + '.' + parte_frac
                else:
                    s_std = s.replace('.', '')
            else:
                s_std = s
            valor = float(s_std)
            return formatar_moeda(valor)
        except Exception:
            return raw
    return padrao.sub(_sub, texto)

def formatar_inteiro_ptbr(valor):
    """Formata inteiros com separador de milhar em ponto (ex: 1.234.567)."""
    try:
        if valor is None:
            return "0"
        # Garante inteiro e aplica formatação US, depois troca vírgulas por pontos
        return f"{int(round(valor)):,}".replace(',', '.')
    except Exception:
        return str(valor)

def construir_filtro_mes(coluna_mes, tipo_mes, ano, mes_numero):
    """Constroi filtro de mês eficiente. Usa faixa de datas quando a coluna é date/timestamp."""
    if not (coluna_mes and ano and mes_numero):
        return ""
    tipo_normalizado = (tipo_mes or "").lower()
    # Calcular primeiro dia do mês e primeiro dia do próximo mês
    try:
        ano_i = int(ano)
        mes_i = int(mes_numero)
        prox_ano = ano_i + 1 if mes_i == 12 else ano_i
        prox_mes = 1 if mes_i == 12 else mes_i + 1
        inicio = f"{ano_i:04d}-{mes_i:02d}-01"
        prox_inicio = f"{prox_ano:04d}-{prox_mes:02d}-01"
    except Exception:
        inicio = f"{ano}-{mes_numero}-01"
        # fallback mais permissivo
        return f"AND {coluna_mes}::text ILIKE '%{ano}-{mes_numero}%'"

    if any(t in tipo_normalizado for t in ["date", "timestamp"]):
        return f"AND {coluna_mes} >= DATE '{inicio}' AND {coluna_mes} < DATE '{prox_inicio}'"
    else:
        return f"AND {coluna_mes}::text ILIKE '%{ano}-{mes_numero}%'"

def detectar_tabela_e_campos(pergunta):
    """Detecta automaticamente qual tabela e campos pesquisar baseado na pergunta"""
    pergunta_lower = pergunta.lower()
    
    # Detectar se a pergunta é sobre linhas (status_licenca, total_linhas, etc.)
    if any(termo in pergunta_lower for termo in ['linha', 'licenca', 'status', 'ativa', 'bloqueada', 'cancelada', 'total_linhas']):
        return 'ia_linhas', ['cliente', 'status_licenca', 'fornecedor', 'total_linhas', 'mes_referencia', 'tipo_contrato']
    
    # Padrão: se não detectar nada específico, usa a tabela de custos
    return 'ia_custo_fornecedor', ['cliente', 'fornecedor', 'custo', 'mes_referencia', 'total']    
    
def pesquisar_linhas(pergunta):
    """Pesquisa específica para a tabela ia_linhas"""
    conn = conectar_postgres()
    if not conn:
        return "Não foi possível conectar ao banco de dados."
    
    resultados = []
    tempo_inicio = time.time()
    
    try:
        with conn.cursor() as cursor:
            # Evita queries demoradas
            try:
                cursor.execute("SET statement_timeout TO '15000ms'")
            except Exception:
                pass
            
            # Verificar se a tabela ia_linhas existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'ia_linhas'
            """)
            tabela_existe = cursor.fetchone()[0]
            
            if tabela_existe == 0:
                resultados.append(f"\n--- ERRO: TABELA NÃO ENCONTRADA ---")
                resultados.append(f"A tabela 'ia_linhas' não existe no banco de dados.")
                resultados.append(f"Verifique se:")
                resultados.append(f"- O banco de dados está correto")
                resultados.append(f"- A tabela foi criada")
                resultados.append(f"- O nome da tabela está correto")
                return "\n".join(resultados)
            
            # Descobrir a estrutura real da tabela ia_linhas
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
            
            # CONSULTA 1: Dados brutos para análise
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
                resultados.append(f"\n--- DADOS BRUTOS - CLIENTE {nome_cliente_filtro.upper()} ---")
                resultados.append(resultado_bruto.to_string(index=False))
                
                # Calcular total manualmente
                if coluna_total_linhas in resultado_bruto.columns:
                    total_calculado = resultado_bruto[coluna_total_linhas].sum()
                    resultados.append(f"\n--- TOTAL CALCULADO: {formatar_inteiro_ptbr(total_calculado)} linhas ---")
            
            # CONSULTA 2: Total por fornecedor (sem SUM, assumindo que já é total)
            # Incluir tipo_contrato se a coluna existir
            campos_select_fornecedor = f"""
                {coluna_cliente} as cliente,
                {coluna_fornecedor} as fornecedor,
                {coluna_status_licenca} as status_licenca,
                {coluna_mes_referencia} as mes_referencia,
                {coluna_total_linhas} as total_linhas"""
            
            if coluna_tipo_contrato:
                campos_select_fornecedor += f",\n                {coluna_tipo_contrato} as tipo_contrato"
            
            query_por_fornecedor = f"""
            SELECT 
                {campos_select_fornecedor}
            FROM ia_linhas
            WHERE {filtro_cliente}
            {filtro_status}
            {filtro_mes}
            ORDER BY {coluna_total_linhas} DESC
            LIMIT 10
            """
            
            resultado_fornecedor = executar_query_direta(conn, query_por_fornecedor)
            if resultado_fornecedor is not None and not resultado_fornecedor.empty:
                titulo = f"\n--- LINHAS POR FORNECEDOR - CLIENTE {nome_cliente_filtro.upper()} ---"
                if status_extraido:
                    titulo += f" STATUS {status_extraido.upper()}"
                if mes_nome and ano:
                    titulo += f" MÊS {mes_nome} {ano}"
                
                resultados.append(titulo)
                resultados.append(resultado_fornecedor.to_string(index=False))
            
            # CONSULTA 3: Tentar SUM apenas para verificar
            query_soma = f"""
            SELECT 
                SUM({coluna_total_linhas}) as total_geral
            FROM ia_linhas
            WHERE {filtro_cliente}
            {filtro_status}
            {filtro_mes}
            """
            
            resultado_soma = executar_query_direta(conn, query_soma)
            if resultado_soma is not None and not resultado_soma.empty:
                total_geral = resultado_soma.iloc[0]['total_geral']
                if total_geral is not None:
                    resultados.append(f"\n--- TOTAL GERAL (USANDO SUM): {formatar_inteiro_ptbr(total_geral)} linhas ---")
            
            
            # CONSULTA 3.1: Total de linhas por fornecedor (dados diretos da tabela)
            if coluna_fornecedor and coluna_total_linhas:
                # Usar filtros dinâmicos baseados na pergunta
                if 'atualmente' in pergunta_lower or 'atual' in pergunta_lower:
                    # Para "atualmente", usar o mês mais recente disponível
                    query_linhas_por_fornecedor = f"""
                    SELECT 
                        {coluna_fornecedor} AS fornecedor,
                        {coluna_total_linhas} AS total_linhas,
                        {coluna_tipo_contrato} AS tipo_contrato
                    FROM ia_linhas
                    WHERE {coluna_cliente} = 'Safra'
                    AND {coluna_status_licenca} = 'ATIVA'
                    AND {coluna_mes_referencia} = (
                        SELECT MAX({coluna_mes_referencia}) 
                        FROM ia_linhas 
                        WHERE {coluna_cliente} = 'Safra' 
                        AND {coluna_status_licenca} = 'ATIVA'
                    )
                    ORDER BY {coluna_total_linhas} DESC
                    """
                else:
                    # Para mês específico, usar os filtros extraídos
                    query_linhas_por_fornecedor = f"""
                    SELECT 
                        {coluna_fornecedor} AS fornecedor,
                        {coluna_total_linhas} AS total_linhas,
                        {coluna_tipo_contrato} AS tipo_contrato
                    FROM ia_linhas
                    WHERE {filtro_cliente}
                    {filtro_status}
                    {filtro_mes}
                    AND {coluna_total_linhas} > 0
                    ORDER BY {coluna_total_linhas} DESC
                    """
                
                resultado_linhas = executar_query_direta(conn, query_linhas_por_fornecedor)
                if resultado_linhas is not None and not resultado_linhas.empty:
                    titulo_agregado = "\n--- LINHAS POR FORNECEDOR E TIPO DE CONTRATO ---"
                    resultados.append(titulo_agregado)
                    
                    # Mostrar dados diretos da tabela
                    resultados.append(resultado_linhas.to_string(index=False))
            
            # CONSULTA 4: Ver estrutura dos dados
            query_amostra = f"""
            SELECT *
            FROM ia_linhas
            WHERE {filtro_cliente}
            {filtro_status}
            {filtro_mes}
            LIMIT 5
            """
            
            resultado_amostra = executar_query_direta(conn, query_amostra)
            if resultado_amostra is not None and not resultado_amostra.empty:
                resultados.append(f"\n--- AMOSTRA DOS DADOS (PRIMEIRAS 5 LINHAS) ---")
                resultados.append(resultado_amostra.to_string(index=False))
                    
    except Exception as e:
        return f"Erro durante a pesquisa: {e}"
    finally:
        conn.close()
    
    tempo_total = time.time() - tempo_inicio
    resultados.append(f"\n--- TEMPO DE EXECUÇÃO: {tempo_total:.2f} segundos ---")
    
    if len(resultados) <= 5:  # Apenas headers e tempo
        return "Nenhum resultado encontrado na tabela ia_linhas para a pesquisa."
    
    return "\n".join(resultados)

def pesquisar_custos_usuarios(pergunta):
    """Pesquisa específica para a tabela ia_custo_usuarios_linhas"""
    try:
        conn = conectar_postgres()
        if not conn:
            return "Não foi possível conectar ao banco de dados."
        
        resultados = []
        tempo_inicio = time.time()
        
        with conn.cursor() as cursor:
            # Evita queries demoradas
            try:
                cursor.execute("SET statement_timeout TO '15000ms'")
            except Exception:
                pass
            
            # Verificar se a tabela ia_custo_usuarios_linhas existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'ia_custo_usuarios_linhas'
            """)
            tabela_existe = cursor.fetchone()[0]
            
            if tabela_existe == 0:
                resultados.append(f"\n--- ERRO: TABELA NÃO ENCONTRADA ---")
                resultados.append(f"A tabela 'ia_custo_usuarios_linhas' não existe no banco de dados.")
                resultados.append(f"Verifique se:")
                resultados.append(f"- O banco de dados está correto")
                resultados.append(f"- A tabela foi criada")
                resultados.append(f"- O nome da tabela está correto")
                return "\n".join(resultados)
            
            # Descobrir a estrutura real da tabela ia_custo_usuarios_linhas
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
        coluna_operadora = None
        coluna_total = None
        coluna_mes_referencia = None
        tipo_mes_referencia = None
        
        for coluna, tipo in colunas_tabela:
            coluna_lower = coluna.lower()
            if 'cliente' in coluna_lower:
                coluna_cliente = coluna
            elif 'nome_usuario' in coluna_lower or 'usuario' in coluna_lower:
                coluna_nome_usuario = coluna
            elif 'operadora' in coluna_lower:
                coluna_operadora = coluna
            elif 'total' in coluna_lower or 'custo' in coluna_lower or 'valor' in coluna_lower:
                coluna_total = coluna
            elif 'mes' in coluna_lower or 'referencia' in coluna_lower or 'data' in coluna_lower:
                coluna_mes_referencia = coluna
                tipo_mes_referencia = tipo
        
        # Extrair informações da pergunta
        ano, mes_numero, mes_nome = extrair_mes_ano(pergunta)
        cliente_extraido = extrair_cliente_pergunta(pergunta)
        pergunta_lower = pergunta.lower()
        
        # DEBUG: Mostrar o que foi extraído
        resultados.append(f"\n--- INFORMAÇÕES EXTRAÍDAS DA PERGUNTA ---")
        resultados.append(f"Pergunta: {pergunta}")
        resultados.append(f"Ano extraído: {ano}")
        resultados.append(f"Mês extraído: {mes_nome} ({mes_numero})")
        resultados.append(f"Cliente extraído: {cliente_extraido}")
        
        # Configurar filtros - capitalizar primeira letra do cliente
        cliente_capitalizado = cliente_extraido.capitalize() if cliente_extraido else None
        filtro_cliente = f"{coluna_cliente} = '{cliente_capitalizado}'" if cliente_capitalizado else f"{coluna_cliente} IS NOT NULL"
        nome_cliente_filtro = cliente_capitalizado if cliente_capitalizado else "todos os clientes"
        
        # DEBUG: Mostrar filtros aplicados
        resultados.append(f"Cliente capitalizado: {cliente_capitalizado}")
        resultados.append(f"Filtro cliente: {filtro_cliente}")
        resultados.append(f"Coluna mes_referencia: {coluna_mes_referencia}")
        resultados.append(f"Tipo mes_referencia: {tipo_mes_referencia}")
        resultados.append(f"Coluna cliente: {coluna_cliente}")
        resultados.append(f"Coluna nome_usuario: {coluna_nome_usuario}")
        resultados.append(f"Coluna total: {coluna_total}")
        
        # Detectar tipo de pergunta
        if 'atualmente' in pergunta_lower or 'mês atual' in pergunta_lower or 'mês vigente' in pergunta_lower:
            # Pergunta 1: Maior custo no mês atual
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
                mes_ref = resultado_atual.iloc[0]['mes_referencia']
                
                # Formatar resposta
                total_formatado = formatar_moeda(total)
                mes_formatado = f"{mes_atual}/{ano_atual}"
                return f"O Usuário {usuario} possui o custo no valor de {total_formatado} no mês atual ({mes_formatado})."
            else:
                return f"Não foram encontrados dados de custos para o Cliente {nome_cliente_filtro} no mês atual."
        
        elif mes_numero and ano:
            # Pergunta 2: Maior custo em mês específico
            filtro_mes = construir_filtro_mes(coluna_mes_referencia, tipo_mes_referencia, ano, mes_numero)
            resultados.append(f"Filtro mês aplicado: {filtro_mes}")
            
            query_maior_custo_mes = f"""
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
            
            resultado_mes = executar_query_direta(conn, query_maior_custo_mes)
            if resultado_mes is not None and not resultado_mes.empty:
                usuario = resultado_mes.iloc[0]['nome_usuario']
                total = resultado_mes.iloc[0]['total']
                
                # Formatar resposta
                total_formatado = formatar_moeda(total)
                mes_formatado = f"{mes_numero}/{ano}"
                return f"O Usuário {usuario} teve o custo no valor de {total_formatado} no mês {mes_formatado}."
            else:
                # DEBUG: Verificar se existem dados para o cliente em qualquer mês
                query_verificar_dados = f"""
                SELECT DISTINCT {coluna_mes_referencia}
                FROM ia_custo_usuarios_linhas
                WHERE {filtro_cliente}
                ORDER BY {coluna_mes_referencia} DESC
                LIMIT 10
                """
                
                resultado_verificar = executar_query_direta(conn, query_verificar_dados)
                if resultado_verificar is not None and not resultado_verificar.empty:
                    resultados.append(f"\n--- DATAS DISPONÍVEIS PARA {nome_cliente_filtro.upper()} ---")
                    resultados.append(resultado_verificar.to_string(index=False))
                
                # Verificar se o cliente existe na tabela
                query_verificar_cliente = f"""
                SELECT COUNT(*) as total_registros
                FROM ia_custo_usuarios_linhas
                WHERE {filtro_cliente}
                """
                
                resultado_cliente = executar_query_direta(conn, query_verificar_cliente)
                if resultado_cliente is not None and not resultado_cliente.empty:
                    total_registros = resultado_cliente.iloc[0]['total_registros'] or 0
                    resultados.append(f"\n--- TOTAL DE REGISTROS PARA {nome_cliente_filtro.upper()} (TODOS OS MESES) ---")
                    resultados.append(f"Total: {formatar_inteiro_ptbr(total_registros)} registros")
                
                # Mostrar amostra dos dados para debug
                query_amostra = f"""
                SELECT *
                FROM ia_custo_usuarios_linhas
                WHERE {filtro_cliente}
                LIMIT 5
                """
                
                resultado_amostra = executar_query_direta(conn, query_amostra)
                if resultado_amostra is not None and not resultado_amostra.empty:
                    resultados.append(f"\n--- AMOSTRA DOS DADOS PARA {nome_cliente_filtro.upper()} ---")
                    resultados.append(resultado_amostra.to_string(index=False))
                
                # Se não há dados de debug, retornar mensagem simples
                if len(resultados) <= 2:  # Apenas headers de debug
                    return f"Não foram encontrados dados de custos para o Cliente {nome_cliente_filtro} no mês {mes_nome} de {ano}."
                else:
                    # Retornar dados de debug para análise
                    return "\n".join(resultados)
        
        elif 'último' in pergunta_lower and '3' in pergunta_lower and ('mês' in pergunta_lower or 'mes' in pergunta_lower):
            # Pergunta 3: Maiores custos nos últimos 3 meses
            from datetime import datetime, timedelta
            hoje = datetime.now()
            
            # Calcular data de início (3 meses atrás do mês atual)
            if hoje.month <= 3:
                ano_inicio = hoje.year - 1
                mes_inicio = hoje.month + 9
            else:
                ano_inicio = hoje.year
                mes_inicio = hoje.month - 3
            
            # Data de início (primeiro dia do mês de 3 meses atrás)
            data_inicio = datetime(ano_inicio, mes_inicio, 1)
            
            # Data fim (primeiro dia do mês atual)
            data_fim = datetime(hoje.year, hoje.month, 1)
            
            query_3_meses = f"""
            SELECT 
                {coluna_nome_usuario} as nome_usuario,
                {coluna_total} as total,
                {coluna_mes_referencia} as mes_referencia
            FROM ia_custo_usuarios_linhas
            WHERE {filtro_cliente}
            AND {coluna_mes_referencia} >= DATE '{data_inicio.strftime('%Y-%m-%d')}'
            AND {coluna_mes_referencia} < DATE '{data_fim.strftime('%Y-%m-%d')}'
            ORDER BY {coluna_total} DESC
            LIMIT 3
            """
            
            resultado_3_meses = executar_query_direta(conn, query_3_meses)
            if resultado_3_meses is not None and not resultado_3_meses.empty:
                usuarios_info = []
                for _, row in resultado_3_meses.iterrows():
                    usuario = row['nome_usuario']
                    total = row['total']
                    mes_ref = row['mes_referencia']
                    
                    # Formatar mês de referência
                    if isinstance(mes_ref, str):
                        try:
                            # Se for formato YYYY-MM-DD, extrair mês e ano
                            if '-' in mes_ref:
                                # Extrair ano e mês do formato YYYY-MM-DD
                                partes = mes_ref.split('-')
                                if len(partes) >= 2:
                                    ano = partes[0]
                                    mes = partes[1]
                                    mes_formatado = f"{mes}/{ano}"
                                else:
                                    mes_formatado = mes_ref
                            else:
                                mes_formatado = mes_ref
                        except:
                            mes_formatado = str(mes_ref)
                    else:
                        # Se for um objeto datetime ou date
                        try:
                            if hasattr(mes_ref, 'year') and hasattr(mes_ref, 'month'):
                                mes_formatado = f"{mes_ref.month:02d}/{mes_ref.year}"
                            else:
                                mes_formatado = str(mes_ref)
                        except:
                            mes_formatado = str(mes_ref)
                    
                    total_formatado = formatar_moeda(total)
                    usuarios_info.append(f"{usuario} {total_formatado} no mês {mes_formatado}")
                
                if usuarios_info:
                    return f"Nos últimos 3 meses os usuários que tiveram os maiores custos foram: {'; '.join(usuarios_info)}."
                else:
                    return f"Não foram encontrados dados de custos para o Cliente {nome_cliente_filtro} nos últimos 3 meses."
            else:
                return f"Não foram encontrados dados de custos para o Cliente {nome_cliente_filtro} nos últimos 3 meses."
        
        # Se não conseguiu identificar o tipo de pergunta, retornar dados gerais
        query_geral = f"""
        SELECT 
            {coluna_nome_usuario} as nome_usuario,
            {coluna_total} as total,
            {coluna_mes_referencia} as mes_referencia
        FROM ia_custo_usuarios_linhas
        WHERE {filtro_cliente}
        ORDER BY {coluna_total} DESC
        LIMIT 10
        """
        
        resultado_geral = executar_query_direta(conn, query_geral)
        if resultado_geral is not None and not resultado_geral.empty:
            resultados.append(f"\n--- CUSTOS POR USUÁRIOS - CLIENTE {nome_cliente_filtro.upper()} ---")
            resultados.append(resultado_geral.to_string(index=False))
        else:
            return f"Não foram encontrados dados de custos por usuários para o Cliente {nome_cliente_filtro}."
                    
    except Exception as e:
        return f"Erro durante a pesquisa de custos por usuários: {e}"
    finally:
        if 'conn' in locals():
            conn.close()
    
    tempo_total = time.time() - tempo_inicio
    resultados.append(f"\n--- TEMPO DE EXECUÇÃO: {tempo_total:.2f} segundos ---")
    
    if len(resultados) <= 1:  # Apenas tempo
        return "Nenhum resultado encontrado na tabela ia_custo_usuarios_linhas para a pesquisa."
    
    return "\n".join(resultados)

def pesquisar_termos_linhas(pergunta):
    """Pesquisa específica para a tabela ia_termos_numeros"""
    try:
        conn = conectar_postgres()
        if not conn:
            return "Não foi possível conectar ao banco de dados."
        
        resultados = []
        tempo_inicio = time.time()
        
        with conn.cursor() as cursor:
            # Evita queries demoradas
            try:
                cursor.execute("SET statement_timeout TO '15000ms'")
            except Exception:
                pass
            
            # Verificar se a tabela ia_termos_numeros existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'ia_termos_numeros'
            """)
            tabela_existe = cursor.fetchone()[0]
            
            if tabela_existe == 0:
                resultados.append(f"\n--- ERRO: TABELA NÃO ENCONTRADA ---")
                resultados.append(f"A tabela 'ia_termos_numeros' não existe no banco de dados.")
                resultados.append(f"Verifique se:")
                resultados.append(f"- O banco de dados está correto")
                resultados.append(f"- A tabela foi criada")
                resultados.append(f"- O nome da tabela está correto")
                return "\n".join(resultados)
            
            # Descobrir a estrutura real da tabela ia_termos_numeros
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'ia_termos_numeros'
                ORDER BY ordinal_position
            """)
            colunas_tabela = cursor.fetchall()
        
        # Encontrar nomes reais das colunas
        coluna_cliente = None
        coluna_numero_linha = None
        coluna_status_linha = None
        coluna_conta_linha = None
        coluna_tipo_numero = None
        coluna_tipo_linha = None
        coluna_possui_termo = None
        coluna_status_termo = None
        coluna_tipo_termo = None
        coluna_nome_usuario = None
        
        for coluna, tipo in colunas_tabela:
            coluna_lower = coluna.lower()
            if 'cliente' in coluna_lower:
                coluna_cliente = coluna
            elif 'numero_linha' in coluna_lower or 'numero' in coluna_lower:
                coluna_numero_linha = coluna
            elif 'status_linha' in coluna_lower:
                coluna_status_linha = coluna
            elif 'conta_linha' in coluna_lower:
                coluna_conta_linha = coluna
            elif 'tipo_numero' in coluna_lower:
                coluna_tipo_numero = coluna
            elif 'tipo_linha' in coluna_lower:
                coluna_tipo_linha = coluna
            elif 'possui_termo' in coluna_lower:
                coluna_possui_termo = coluna
            elif 'status_termo' in coluna_lower:
                coluna_status_termo = coluna
            elif 'tipo_termo' in coluna_lower:
                coluna_tipo_termo = coluna
            elif 'nome_usuario' in coluna_lower:
                coluna_nome_usuario = coluna
        
        # Extrair informações da pergunta
        cliente_extraido = extrair_cliente_pergunta(pergunta)
        pergunta_lower = pergunta.lower()
        
        # Configurar filtros - capitalizar primeira letra do cliente
        cliente_capitalizado = cliente_extraido.capitalize() if cliente_extraido else None
        filtro_cliente = f"{coluna_cliente} = '{cliente_capitalizado}'" if cliente_capitalizado else f"{coluna_cliente} IS NOT NULL"
        nome_cliente_filtro = cliente_capitalizado if cliente_capitalizado else "todos os clientes"
        
        # Detectar tipo de pergunta - PRIORIDADE para pergunta 3 (linhas ativas por tipo)
        if ('linhas sem termos' in pergunta_lower and 'tipo de linha' in pergunta_lower and 'linhas ativas' in pergunta_lower) or ('estão ativas' in pergunta_lower and 'tipo' in pergunta_lower):
            # Pergunta 3: Total de linhas sem termos ativas por tipo de linha
            # Primeiro, contar total de linhas sem termos
            query_total_sem_termo = f"""
            SELECT COUNT(*) as total_sem_termo
            FROM ia_termos_numeros
            WHERE {filtro_cliente}
            AND ({coluna_possui_termo} = 'N' OR {coluna_possui_termo} = 'Não' OR {coluna_possui_termo} = 'NAO' OR {coluna_possui_termo} = 'NÃO' OR {coluna_possui_termo} IS NULL OR {coluna_possui_termo} = '')
            """
            
            resultado_total = executar_query_direta(conn, query_total_sem_termo)
            total_sem_termo = resultado_total.iloc[0]['total_sem_termo'] or 0 if resultado_total is not None and not resultado_total.empty else 0
            
            # Agora, contar linhas sem termos ativas por tipo
            query_ativas_por_tipo = f"""
            SELECT 
                {coluna_tipo_linha} as tipo_linha,
                {coluna_status_linha} as status_linha,
                COUNT(*) as total_ativas
            FROM ia_termos_numeros
            WHERE {filtro_cliente}
            AND ({coluna_possui_termo} = 'N' OR {coluna_possui_termo} = 'Não' OR {coluna_possui_termo} = 'NAO' OR {coluna_possui_termo} = 'NÃO' OR {coluna_possui_termo} IS NULL OR {coluna_possui_termo} = '')
            AND ({coluna_status_linha} ILIKE '%ATIVA%' OR {coluna_status_linha} ILIKE '%ATIVO%')
            GROUP BY {coluna_tipo_linha}, {coluna_status_linha}
            ORDER BY total_ativas DESC
            """
            
            resultado_ativas = executar_query_direta(conn, query_ativas_por_tipo)
            if resultado_ativas is not None and not resultado_ativas.empty:
                # Construir resposta detalhada - agrupar por tipo_linha
                tipos_agrupados = {}
                for _, row in resultado_ativas.iterrows():
                    tipo_linha = row['tipo_linha'] if row['tipo_linha'] else 'N/A'
                    total_ativas = row['total_ativas']
                    
                    if tipo_linha not in tipos_agrupados:
                        tipos_agrupados[tipo_linha] = 0
                    tipos_agrupados[tipo_linha] += total_ativas
                
                # Construir detalhes agrupados por tipo
                detalhes_ativas = []
                for tipo_linha, total in tipos_agrupados.items():
                    detalhes_ativas.append(f"{formatar_inteiro_ptbr(total)} linhas que estão Ativas são do tipo {tipo_linha}")
                
                resposta = f"O Cliente {nome_cliente_filtro} possui {formatar_inteiro_ptbr(total_sem_termo)} linhas sem termos e {', '.join(detalhes_ativas)}."
                return resposta
            else:
                return f"O Cliente {nome_cliente_filtro} possui {formatar_inteiro_ptbr(total_sem_termo)} linhas sem termos, mas nenhuma está ativa."
        
        # Detectar tipo de pergunta - PRIORIDADE para pergunta 2 (total por tipo)
        elif ('total de linhas sem termos' in pergunta_lower and 'tipo de linha' in pergunta_lower) or ('me mostre o total por tipo' in pergunta_lower) or ('por tipo de linha' in pergunta_lower):
            # Pergunta 2: Total por tipo de linha das linhas sem termos
            query_por_tipo_linha = f"""
            SELECT 
                {coluna_tipo_linha} as tipo_linha,
                COUNT(*) as total_sem_termo
            FROM ia_termos_numeros
            WHERE {filtro_cliente}
            AND ({coluna_possui_termo} = 'N' OR {coluna_possui_termo} = 'Não' OR {coluna_possui_termo} = 'NAO' OR {coluna_possui_termo} = 'NÃO' OR {coluna_possui_termo} IS NULL OR {coluna_possui_termo} = '')
            GROUP BY {coluna_tipo_linha}
            ORDER BY total_sem_termo DESC
            """
            
            resultado_por_tipo = executar_query_direta(conn, query_por_tipo_linha)
            if resultado_por_tipo is not None and not resultado_por_tipo.empty:
                # Calcular total geral
                total_geral = resultado_por_tipo['total_sem_termo'].sum()
                
                # Construir resposta detalhada
                detalhes_tipo = []
                for _, row in resultado_por_tipo.iterrows():
                    tipo_linha = row['tipo_linha'] if row['tipo_linha'] else 'N/A'
                    total_tipo = row['total_sem_termo']
                    detalhes_tipo.append(f"{formatar_inteiro_ptbr(total_tipo)} linhas são do tipo {tipo_linha}")
                
                resposta = f"O Cliente {nome_cliente_filtro} possui {formatar_inteiro_ptbr(total_geral)} linhas sem termos, sendo que {', '.join(detalhes_tipo)}."
                return resposta
            else:
                return f"O Cliente {nome_cliente_filtro} possui 0 linhas sem termos."
        
        elif 'não possuem termo' in pergunta_lower or 'nao possuem termo' in pergunta_lower or 'sem termo' in pergunta_lower:
            # Pergunta 1: Quantas linhas não possuem termo
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
        
        # Se não conseguiu identificar o tipo de pergunta, retornar dados gerais
        query_geral = f"""
        SELECT 
            {coluna_cliente} as cliente,
            {coluna_numero_linha} as numero_linha,
            {coluna_tipo_linha} as tipo_linha,
            {coluna_possui_termo} as possui_termo,
            {coluna_status_termo} as status_termo,
            {coluna_tipo_termo} as tipo_termo
        FROM ia_termos_numeros
        WHERE {filtro_cliente}
        LIMIT 10
        """
        
        resultado_geral = executar_query_direta(conn, query_geral)
        if resultado_geral is not None and not resultado_geral.empty:
            resultados.append(f"\n--- DADOS DE TERMOS - CLIENTE {nome_cliente_filtro.upper()} ---")
            resultados.append(resultado_geral.to_string(index=False))
        else:
            return f"Não foram encontrados dados de termos para o Cliente {nome_cliente_filtro}."
                    
    except Exception as e:
        return f"Erro durante a pesquisa de termos: {e}"
    finally:
        if 'conn' in locals():
            conn.close()
    
    tempo_total = time.time() - tempo_inicio
    resultados.append(f"\n--- TEMPO DE EXECUÇÃO: {tempo_total:.2f} segundos ---")
    
    if len(resultados) <= 1:  # Apenas tempo
        return "Nenhum resultado encontrado na tabela ia_termos_numeros para a pesquisa."
    
    return "\n".join(resultados)

def pesquisar_linhas_ociosas(pergunta):
    """Pesquisa específica para a tabela ia_linhas_ociosas"""
    try:
        conn = conectar_postgres()
        if not conn:
            return "Não foi possível conectar ao banco de dados."
        
        resultados = []
        tempo_inicio = time.time()
        
        with conn.cursor() as cursor:
            # Evita queries demoradas
            try:
                cursor.execute("SET statement_timeout TO '15000ms'")
            except Exception:
                pass
            
            # Verificar se a tabela ia_linhas_ociosas existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'ia_linhas_ociosas'
            """)
            tabela_existe = cursor.fetchone()[0]
            
            if tabela_existe == 0:
                resultados.append(f"\n--- ERRO: TABELA NÃO ENCONTRADA ---")
                resultados.append(f"A tabela 'ia_linhas_ociosas' não existe no banco de dados.")
                resultados.append(f"Verifique se:")
                resultados.append(f"- O banco de dados está correto")
                resultados.append(f"- A tabela foi criada")
                resultados.append(f"- O nome da tabela está correto")
                return "\n".join(resultados)
            
            # Descobrir a estrutura real da tabela ia_linhas_ociosas
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
        # Capitalizar a primeira letra do nome do cliente para corresponder ao banco
        cliente_capitalizado = cliente_extraido.capitalize() if cliente_extraido else None
        filtro_cliente = f"{coluna_cliente} = '{cliente_capitalizado}'" if cliente_capitalizado else f"{coluna_cliente} IS NOT NULL"
        nome_cliente_filtro = cliente_capitalizado if cliente_capitalizado else "todos os clientes"
        
        # Detectar tipo de pergunta (prioridade para operadora)
        if 'operadora' in pergunta_lower:
            # Pergunta 4: Por operadora (mês atual)
            from datetime import datetime
            hoje = datetime.now()
            ano_atual = str(hoje.year)
            mes_atual = str(hoje.month).zfill(2)
            # Usar a mesma lógica de filtro que funciona em pesquisar_linhas
            filtro_mes = construir_filtro_mes(coluna_mes_referencia, tipo_mes_referencia, ano_atual, mes_atual)
            
            query_por_operadora = f"""
            SELECT 
                {coluna_operadora} as operadora,
                COUNT(*) as total_ociosas
            FROM ia_linhas_ociosas
            WHERE {filtro_cliente}
            {filtro_mes}
            GROUP BY {coluna_operadora}
            ORDER BY total_ociosas DESC
            """
            
            resultado_operadoras = executar_query_direta(conn, query_por_operadora)
            if resultado_operadoras is not None and not resultado_operadoras.empty:
                # Formatar resposta diretamente
                respostas_operadoras = []
                for _, row in resultado_operadoras.iterrows():
                    operadora = str(row['operadora']) if 'operadora' in row else 'N/A'
                    total = row['total_ociosas'] if 'total_ociosas' in row else 0
                    if total == 1:
                        respostas_operadoras.append(f"{total} linha ociosa, Operadora {operadora}")
                    else:
                        respostas_operadoras.append(f"{total} linhas ociosas, Operadora {operadora}")
                
                if respostas_operadoras:
                    return f"O Cliente {nome_cliente_filtro} possui atualmente {', '.join(respostas_operadoras)}."
                else:
                    return f"O Cliente {nome_cliente_filtro} não possui linhas ociosas atualmente."
            else:
                return f"O Cliente {nome_cliente_filtro} não possui linhas ociosas atualmente."
        
        elif 'atualmente' in pergunta_lower or 'mês atual' in pergunta_lower or 'mês vigente' in pergunta_lower:
            # Pergunta 1: Mês atual
            from datetime import datetime
            hoje = datetime.now()
            ano_atual = str(hoje.year)
            mes_atual = str(hoje.month).zfill(2)
            # Usar a mesma lógica de filtro que funciona em pesquisar_linhas
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
                resultados.append(f"\n--- LINHAS OCIOSAS ATUAIS - CLIENTE {nome_cliente_filtro.upper()} ---")
                resultados.append(f"Total de linhas ociosas em {mes_atual}/{ano_atual}: {formatar_inteiro_ptbr(total)}")
            else:
                resultados.append(f"\n--- LINHAS OCIOSAS ATUAIS - CLIENTE {nome_cliente_filtro.upper()} ---")
                resultados.append(f"Total de linhas ociosas em {mes_atual}/{ano_atual}: 0")
            
            # Verificar se existem dados para o cliente em qualquer mês
            query_verificar_dados = f"""
            SELECT DISTINCT {coluna_mes_referencia}
            FROM ia_linhas_ociosas
            WHERE {filtro_cliente}
            ORDER BY {coluna_mes_referencia} DESC
            LIMIT 5
            """
            
            resultado_verificar = executar_query_direta(conn, query_verificar_dados)
            if resultado_verificar is not None and not resultado_verificar.empty:
                resultados.append(f"\n--- DATAS DISPONÍVEIS PARA {nome_cliente_filtro.upper()} ---")
                resultados.append(resultado_verificar.to_string(index=False))
            else:
                resultados.append(f"\n--- NENHUMA DATA ENCONTRADA PARA {nome_cliente_filtro.upper()} ---")
            
            # Verificar se o cliente existe na tabela
            query_verificar_cliente = f"""
            SELECT COUNT(*) as total_registros
            FROM ia_linhas_ociosas
            WHERE {filtro_cliente}
            """
            
            resultado_cliente = executar_query_direta(conn, query_verificar_cliente)
            if resultado_cliente is not None and not resultado_cliente.empty:
                total_registros = resultado_cliente.iloc[0]['total_registros'] or 0
                resultados.append(f"\n--- TOTAL DE REGISTROS PARA {nome_cliente_filtro.upper()} (TODOS OS MESES) ---")
                resultados.append(f"Total: {formatar_inteiro_ptbr(total_registros)} registros")
        
        elif mes_numero and ano:
            # Pergunta 2: Mês específico
            # Usar a mesma lógica de filtro que funciona em pesquisar_linhas
            filtro_mes = construir_filtro_mes(coluna_mes_referencia, tipo_mes_referencia, ano, mes_numero)
            
            query_mes_especifico = f"""
            SELECT COUNT(*) as total_ociosas
            FROM ia_linhas_ociosas
            WHERE {filtro_cliente}
            {filtro_mes}
            """
            
            resultado_mes = executar_query_direta(conn, query_mes_especifico)
            if resultado_mes is not None and not resultado_mes.empty:
                total = resultado_mes.iloc[0]['total_ociosas'] or 0
                # Formatar resposta diretamente
                if total == 1:
                    return f"O Cliente {nome_cliente_filtro} possuiu em {mes_nome} de {ano} {total} linha ociosa."
                else:
                    return f"O Cliente {nome_cliente_filtro} possuiu em {mes_nome} de {ano} {total} linhas ociosas."
            else:
                return f"O Cliente {nome_cliente_filtro} possuiu em {mes_nome} de {ano} 0 linhas ociosas."
        
        elif 'último' in pergunta_lower and '3' in pergunta_lower and ('mês' in pergunta_lower or 'mes' in pergunta_lower):
            # Pergunta 3: Últimos 3 meses - Query simplificada com range de datas
            from datetime import datetime, timedelta
            hoje = datetime.now()
            
            # Calcular data de início (3 meses atrás do mês atual)
            if hoje.month <= 3:
                # Se estamos nos primeiros 3 meses do ano, pegar do ano anterior
                ano_inicio = hoje.year - 1
                mes_inicio = hoje.month + 9  # 12 - 3 + hoje.month
            else:
                ano_inicio = hoje.year
                mes_inicio = hoje.month - 3
            
            # Data de início (primeiro dia do mês de 3 meses atrás)
            data_inicio = datetime(ano_inicio, mes_inicio, 1)
            
            # Data fim (primeiro dia do mês atual)
            data_fim = datetime(hoje.year, hoje.month, 1)
            
            # Query simplificada com range de datas
            query_3_meses = f"""
            SELECT COUNT(*) as total_ociosas
            FROM ia_linhas_ociosas
            WHERE {filtro_cliente}
            AND {coluna_mes_referencia} >= DATE '{data_inicio.strftime('%Y-%m-%d')}'
            AND {coluna_mes_referencia} < DATE '{data_fim.strftime('%Y-%m-%d')}'
            """
            
            resultado_3_meses = executar_query_direta(conn, query_3_meses)
            if resultado_3_meses is not None and not resultado_3_meses.empty:
                total_3_meses = resultado_3_meses.iloc[0]['total_ociosas'] or 0
                resultados.append(f"\n--- LINHAS OCIOSAS ÚLTIMOS 3 MESES - CLIENTE {nome_cliente_filtro.upper()} ---")
                resultados.append(f"Período: {data_inicio.strftime('%m/%Y')} a {(data_fim - timedelta(days=1)).strftime('%m/%Y')}")
                resultados.append(f"TOTAL DOS 3 MESES: {formatar_inteiro_ptbr(total_3_meses)} linhas")
            else:
                resultados.append(f"\n--- LINHAS OCIOSAS ÚLTIMOS 3 MESES - CLIENTE {nome_cliente_filtro.upper()} ---")
                resultados.append(f"TOTAL DOS 3 MESES: 0 linhas")
        
        
        # Consulta de amostra para verificar estrutura
        query_amostra = f"""
        SELECT *
        FROM ia_linhas_ociosas
        WHERE {filtro_cliente}
        LIMIT 5
        """
        
        resultado_amostra = executar_query_direta(conn, query_amostra)
        if resultado_amostra is not None and not resultado_amostra.empty:
            resultados.append(f"\n--- AMOSTRA DOS DADOS (PRIMEIRAS 5 LINHAS) ---")
            resultados.append(resultado_amostra.to_string(index=False))
                    
    except Exception as e:
        return f"Erro durante a pesquisa de linhas ociosas: {e}"
    finally:
        if 'conn' in locals():
            conn.close()
    
    tempo_total = time.time() - tempo_inicio
    resultados.append(f"\n--- TEMPO DE EXECUÇÃO: {tempo_total:.2f} segundos ---")
    
    if len(resultados) <= 5:  # Apenas headers e tempo
        return "Nenhum resultado encontrado na tabela ia_linhas_ociosas para a pesquisa."
    
    # Retornar resposta formatada diretamente para linhas ociosas
    resultado_final = "\n".join(resultados)
    
    # Extrair informações para resposta direta
    if 'atualmente' in pergunta_lower or 'mês atual' in pergunta_lower or 'mês vigente' in pergunta_lower:
        # Resposta para mês atual
        if 'Total de linhas ociosas em' in resultado_final:
            linha_resultado = [linha for linha in resultados if 'Total de linhas ociosas em' in linha][0]
            total = linha_resultado.split(': ')[1]
            # Adicionar "linha ociosa" ou "linhas ociosas" baseado no número
            if total == "1":
                return f"O Cliente {nome_cliente_filtro} possui atualmente {total} linha ociosa."
            else:
                return f"O Cliente {nome_cliente_filtro} possui atualmente {total} linhas ociosas."
        else:
            return f"O Cliente {nome_cliente_filtro} possui atualmente 0 linhas ociosas."
    
    elif mes_numero and ano:
        # Resposta para mês específico
        if 'Total de linhas ociosas:' in resultado_final:
            linha_resultado = [linha for linha in resultados if 'Total de linhas ociosas:' in linha][0]
            return f"O Cliente {nome_cliente_filtro} possuiu em {mes_nome} de {ano} {linha_resultado.split(': ')[1]}."
        else:
            return f"O Cliente {nome_cliente_filtro} possuiu em {mes_nome} de {ano} 0 linhas ociosas."
    
    elif 'último' in pergunta_lower and '3' in pergunta_lower and 'mês' in pergunta_lower:
        # Resposta para últimos 3 meses
        if 'TOTAL DOS 3 MESES:' in resultado_final:
            linha_total = [linha for linha in resultados if 'TOTAL DOS 3 MESES:' in linha][0]
            total_3_meses = linha_total.split(': ')[1]
            return f"O Cliente {nome_cliente_filtro} possuiu nos últimos 3 meses {total_3_meses}."
        else:
            return f"O Cliente {nome_cliente_filtro} possuiu nos últimos 3 meses 0 linhas ociosas."
    
    elif 'operadora' in pergunta_lower and ('atualmente' in pergunta_lower or 'atual' in pergunta_lower):
        # Resposta para por operadora
        if 'LINHAS OCIOSAS POR OPERADORA' in resultado_final:
            operadoras = []
            for linha in resultados:
                if ':' in linha and 'linhas' in linha and 'LINHAS OCIOSAS POR OPERADORA' not in linha:
                    operadoras.append(linha)
            
            if operadoras:
                # Processar cada operadora individualmente
                respostas_operadoras = []
                for operadora_info in operadoras:
                    if ':' in operadora_info:
                        operadora, total = operadora_info.split(': ')
                        total_limpo = total.replace(' linhas', '').strip()
                        if total_limpo == "1":
                            respostas_operadoras.append(f"{total_limpo} linha ociosa, Operadora {operadora}")
                        else:
                            respostas_operadoras.append(f"{total_limpo} linhas ociosas, Operadora {operadora}")
                
                if respostas_operadoras:
                    return f"O Cliente {nome_cliente_filtro} possui atualmente {', '.join(respostas_operadoras)}."
                else:
                    return f"O Cliente {nome_cliente_filtro} não possui linhas ociosas atualmente."
            else:
                return f"O Cliente {nome_cliente_filtro} não possui linhas ociosas atualmente."
        else:
            return f"O Cliente {nome_cliente_filtro} não possui linhas ociosas atualmente."
    
    # Se não conseguir extrair resposta específica, retornar dados completos
    return resultado_final

def pesquisar_no_banco(pergunta):
    """Pesquisa inteligente no banco de dados - Mantida a versão original"""
    pergunta_lower = pergunta.lower()
    
    # Verificar PRIMEIRO se a pergunta é sobre termos de linhas (prioridade)
    termos_termos = ['termo', 'termos', 'possui termo', 'não possuem termo', 'nao possuem termo', 'sem termo']
    if any(termo in pergunta_lower for termo in termos_termos):
        return pesquisar_termos_linhas(pergunta)
    
    # Verificar se a pergunta é sobre custos por usuários
    # Detectar padrões específicos de perguntas sobre custos por usuários
    padroes_custos_usuarios = [
        'usuário.*maior.*custo',
        'usuario.*maior.*custo', 
        'maior.*custo.*usuário',
        'maior.*custo.*usuario',
        'custo.*usuário',
        'custo.*usuario',
        'usuário.*custo',
        'usuario.*custo'
    ]
    
    for padrao in padroes_custos_usuarios:
        if re.search(padrao, pergunta_lower):
            return pesquisar_custos_usuarios(pergunta)
    
    # Verificar também termos simples
    termos_custos_usuarios = ['usuário', 'usuario']
    if any(termo in pergunta_lower for termo in termos_custos_usuarios) and 'custo' in pergunta_lower:
        return pesquisar_custos_usuarios(pergunta)
    
    # Verificar se a pergunta é sobre linhas ociosas
    termos_ociosas = ['ociosa', 'ociosas', 'ocioso', 'ociosos']
    for termo in termos_ociosas:
        if termo in pergunta_lower:
            return pesquisar_linhas_ociosas(pergunta)
    
    # Verificar se a pergunta é sobre linhas normais
    termos_linhas = ['linha', 'licenca', 'status', 'ativa', 'bloqueada', 'cancelada', 'total_linhas', 'fornecedor']
    if any(termo in pergunta_lower for termo in termos_linhas):
        return pesquisar_linhas(pergunta)
    
    # Se não for sobre linhas, usa a versão original para custos
    conn = conectar_postgres()
    if not conn:
        return "Não foi possível conectar ao banco de dados."
    
    resultados = []
    tempo_inicio = time.time()
    
    try:
        with conn.cursor() as cursor:
            # Evita queries demoradas
            try:
                cursor.execute("SET statement_timeout TO '15000ms'")
            except Exception:
                pass
            
            # Verificar se a tabela ia_custo_fornecedor existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'ia_custo_fornecedor'
            """)
            tabela_existe = cursor.fetchone()[0]
            
            if tabela_existe == 0:
                resultados.append(f"\n--- ERRO: TABELA NÃO ENCONTRADA ---")
                resultados.append(f"A tabela 'ia_custo_fornecedor' não existe no banco de dados.")
                resultados.append(f"Verifique se:")
                resultados.append(f"- O banco de dados está correto")
                resultados.append(f"- A tabela foi criada")
                resultados.append(f"- O nome da tabela está correto")
                resultados.append(f"\nTabelas disponíveis no banco:")
                
                # Listar tabelas disponíveis
                cursor.execute("""
                    SELECT table_schema, table_name 
                    FROM information_schema.tables 
                    WHERE table_type = 'BASE TABLE'
                    AND table_schema NOT IN ('information_schema', 'pg_catalog', 'pgagent')
                    ORDER BY table_schema, table_name
                """)
                tabelas_disponiveis = cursor.fetchall()
                for schema, tabela in tabelas_disponiveis:
                    resultados.append(f"- {schema}.{tabela}")
                
                return "\n".join(resultados)
            
            # Descobrir a estrutura real da tabela ia_custo_fornecedor
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
                elif 'custo' in coluna_lower or 'valor' in coluna_lower or 'total' in coluna_lower or tipo in ['numeric', 'decimal', 'money', 'double precision']:
                    coluna_custo = coluna
                elif 'mes' in coluna_lower or 'referencia' in coluna_lower or 'data' in coluna_lower or tipo in ['date', 'timestamp', 'varchar', 'text']:
                    coluna_mes_referencia = coluna
                elif 'tipo' in coluna_lower and 'contrato' in coluna_lower:
                    coluna_tipo_contrato = coluna
            
            # Extrair informações da pergunta
            ano, mes_numero, mes_nome = extrair_mes_ano(pergunta)
            cliente_extraido = extrair_cliente_pergunta(pergunta)
            
            # DEBUG: Mostrar o que foi extraído
            resultados.append(f"\n--- INFORMAÇÕES EXTRAÍDAS DA PERGUNTA ---")
            resultados.append(f"Pergunta: {pergunta}")
            resultados.append(f"Ano extraído: {ano}")
            resultados.append(f"Mês extraído: {mes_nome} ({mes_numero})")
            resultados.append(f"Cliente extraído: {cliente_extraido}")
            
            # Se não extraiu cliente, usar 'safra' como padrão ou buscar todos
            filtro_cliente = f"{coluna_cliente} ILIKE '%{cliente_extraido}%'" if cliente_extraido else f"{coluna_cliente} IS NOT NULL"
            nome_cliente_filtro = cliente_extraido if cliente_extraido else "todos os clientes"
            
            # CONSULTA PRINCIPAL: Para o mês específico solicitado (DYNAMIC)
            if mes_numero and ano and coluna_mes_referencia and coluna_cliente and coluna_fornecedor and coluna_custo:
                
                # CONSULTA 1: Buscar dados EXATOS para o mês/ano solicitado
                filtro_mes = construir_filtro_mes(coluna_mes_referencia, None, ano, mes_numero)
                
                # Incluir tipo_contrato se a coluna existir
                campos_select = f"""
                    {coluna_cliente} as cliente,
                    {coluna_fornecedor} as fornecedor,
                    {coluna_mes_referencia} as mes_referencia,
                    {coluna_custo} as custo"""
                
                if coluna_tipo_contrato:
                    campos_select += f",\n                    {coluna_tipo_contrato} as tipo_contrato"
                
                query_mes_exato = f"""
                SELECT 
                    {campos_select}
                FROM ia_custo_fornecedor 
                WHERE {filtro_cliente}
                {filtro_mes}
                ORDER BY {coluna_custo} DESC
                LIMIT 10
                """
                
                resultado_mes_exato = executar_query_direta(conn, query_mes_exato)
                if resultado_mes_exato is not None and not resultado_mes_exato.empty:
                    resultados.append(f"\n--- DADOS EXATOS PARA {mes_nome} {ano} - CLIENTE {nome_cliente_filtro.upper()} ---")
                    resultados.append(resultado_mes_exato.to_string(index=False))
                else:
                    resultados.append(f"\n--- NENHUM DADO ENCONTRADO PARA {mes_nome} {ano} - CLIENTE {nome_cliente_filtro.upper()} ---")
            
            # CONSULTA 2: Verificar se o mês/ano solicitado existe na base
            if mes_numero and ano and coluna_mes_referencia:
                filtro_mes = construir_filtro_mes(coluna_mes_referencia, None, ano, mes_numero)
                query_verificar_mes = f"""
                SELECT DISTINCT {coluna_mes_referencia}
                FROM ia_custo_fornecedor
                WHERE {filtro_cliente}
                {filtro_mes}
                """
                
                resultado_verificar = executar_query_direta(conn, query_verificar_mes)
                if resultado_verificar is not None and not resultado_verificar.empty:
                    resultados.append(f"\n--- VERIFICAÇÃO: DADOS DE {mes_nome} {ano} EXISTEM PARA {nome_cliente_filtro.upper()} ---")
                    resultados.append(resultado_verificar.to_string(index=False))
            
            # CONSULTA 3: Fornecedor com maior custo no mês/ano solicitado (DYNAMIC - SOMA por fornecedor)
            if mes_numero and ano and coluna_mes_referencia and coluna_cliente and coluna_fornecedor and coluna_custo:
                filtro_mes = construir_filtro_mes(coluna_mes_referencia, None, ano, mes_numero)
                
                # Incluir tipo_contrato se a coluna existir
                campos_select_maior = f"""
                    {coluna_cliente} as cliente,
                    {coluna_fornecedor} as fornecedor,
                    {coluna_mes_referencia} as mes_referencia,
                    SUM({coluna_custo}) as custo_total"""
                
                campos_group_by = f"{coluna_cliente}, {coluna_fornecedor}, {coluna_mes_referencia}"
                
                if coluna_tipo_contrato:
                    campos_select_maior += f",\n                    {coluna_tipo_contrato} as tipo_contrato"
                    campos_group_by += f", {coluna_tipo_contrato}"
                
                query_maior_custo_mes = f"""
                SELECT 
                    {campos_select_maior}
                FROM ia_custo_fornecedor 
                WHERE {filtro_cliente}
                {filtro_mes}
                GROUP BY {campos_group_by}
                ORDER BY custo_total DESC
                LIMIT 1
                """
                
                resultado_maior_custo = executar_query_direta(conn, query_maior_custo_mes)
                if resultado_maior_custo is not None and not resultado_maior_custo.empty:
                    resultados.append(f"\n--- FORNECEDOR COM MAIOR CUSTO EM {mes_nome} {ano} - CLIENTE {nome_cliente_filtro.upper()} ---")
                    resultados.append(resultado_maior_custo.to_string(index=False))
            
            # CONSULTA 4: Todos os dados do mês/ano solicitado para análise (DYNAMIC)
            if mes_numero and ano and coluna_cliente and coluna_mes_referencia:
                filtro_mes = construir_filtro_mes(coluna_mes_referencia, None, ano, mes_numero)
                query_todos_mes = f"""
                SELECT *
                FROM ia_custo_fornecedor 
                WHERE {filtro_cliente}
                {filtro_mes}
                ORDER BY {coluna_custo} DESC
                LIMIT 10
                """
                
                resultado_todos_mes = executar_query_direta(conn, query_todos_mes)
                if resultado_todos_mes is not None and not resultado_todos_mes.empty:
                    resultados.append(f"\n--- TODOS OS DADOS DE {mes_nome} {ano} - CLIENTE {nome_cliente_filtro.upper()} ---")
                    resultados.append(resultado_todos_mes.to_string(index=False))
            
            # CONSULTA 5: Datas disponíveis para referência
            if coluna_mes_referencia:
                query_datas = f"""
                SELECT DISTINCT {coluna_mes_referencia}
                FROM ia_custo_fornecedor
                WHERE {filtro_cliente}
                AND {coluna_mes_referencia} IS NOT NULL
                ORDER BY {coluna_mes_referencia} DESC
                LIMIT 12
                """
                
                resultado_datas = executar_query_direta(conn, query_datas)
                if resultado_datas is not None and not resultado_datas.empty:
                    resultados.append(f"\n--- DATAS DISPONÍVEIS PARA {nome_cliente_filtro.upper()} ---")
                    resultados.append(resultado_datas.to_string(index=False))
            
            # CONSULTA 6: Total geral por fornecedor
            if coluna_cliente and coluna_fornecedor and coluna_custo:
                # Incluir tipo_contrato se a coluna existir
                campos_select_total = f"""
                    {coluna_cliente} as cliente,
                    {coluna_fornecedor} as fornecedor,
                    SUM({coluna_custo}) as custo_total"""
                
                campos_group_by_total = f"{coluna_cliente}, {coluna_fornecedor}"
                
                if coluna_tipo_contrato:
                    campos_select_total += f",\n                    {coluna_tipo_contrato} as tipo_contrato"
                    campos_group_by_total += f", {coluna_tipo_contrato}"
                
                query_total_geral = f"""
                SELECT 
                    {campos_select_total}
                FROM ia_custo_fornecedor 
                WHERE {filtro_cliente}
                GROUP BY {campos_group_by_total}
                ORDER BY custo_total DESC
                LIMIT 10
                """
                
                resultado_total = executar_query_direta(conn, query_total_geral)
                if resultado_total is not None and not resultado_total.empty:
                    resultados.append(f"\n--- CUSTO TOTAL POR FORNECEDOR - CLIENTE {nome_cliente_filtro.upper()} ---")
                    resultados.append(resultado_total.to_string(index=False))
            
            # CONSULTA 7: Lista de clientes disponíveis
            if coluna_cliente:
                query_clientes = f"""
                SELECT DISTINCT {coluna_cliente}
                FROM ia_custo_fornecedor
                WHERE {coluna_cliente} IS NOT NULL
                ORDER BY {coluna_cliente}
                LIMIT 20
                """
                
                resultado_clientes = executar_query_direta(conn, query_clientes)
                if resultado_clientes is not None and not resultado_clientes.empty:
                    resultados.append(f"\n--- CLIENTES DISPONÍVEIS NO BANCO ---")
                    resultados.append(resultado_clientes.to_string(index=False))
                    
            # Descobrir a estrutura real da tabela ia_custo_fornecedor
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'ia_custo_fornecedor'
                ORDER BY ordinal_position
            """)
            colunas_tabela = cursor.fetchall()
            
            # ... (todo o resto do código original)
            
    except Exception as e:
        return f"Erro durante a pesquisa: {e}"
    finally:
        conn.close()
    
    tempo_total = time.time() - tempo_inicio
    resultados.append(f"\n--- TEMPO DE EXECUÇÃO: {tempo_total:.2f} segundos ---")
    
    if not resultados:
        return "Nenhum resultado encontrado no banco de dados para a pesquisa."
    
    return "\n".join(resultados)


def _cosine_similarity(a_vec, b_vec):
    """Calcula similaridade do cosseno entre vetores numpy 1D."""
    a_norm = np.linalg.norm(a_vec)
    b_norm = np.linalg.norm(b_vec)
    if a_norm == 0.0 or b_norm == 0.0:
        return 0.0
    return float(np.dot(a_vec, b_vec) / (a_norm * b_norm))

def construir_rag_prompt():
    """Cria o template de prompt para RAG."""
    template = (
        "Você é um assistente analista de dados. Responda APENAS com base no CONTEXTO fornecido.\n"
        "- IMPORTANTE: Use EXATAMENTE os números que aparecem no contexto. NÃO faça cálculos, somas ou multiplicações.\n"
        "- Se a informação não estiver no contexto, diga que não encontrou nos dados.\n"
        "- SEMPRE inclua o tipo de contrato quando disponível nos dados.\n"
        "- Para números grandes (milhares), use ponto como separador de milhar (ex: 1.234.567).\n"
        "- Para perguntas sobre fornecedor com maior custo, use o formato: 'O Cliente [nome], o fornecedor com o maior custo no mês de [mês] de [ano] é [fornecedor], com um custo total de [valor], tipo de contrato [tipo_contrato].'\n"
        "- Para perguntas sobre linhas por fornecedor, use o formato: '* **[Fornecedor]**: [número] linhas, tipo de contrato [tipo_contrato].'\n"
        "- CRÍTICO: Se você vir 'total_linhas: 1.262.790' no contexto, use EXATAMENTE 1.262.790, não faça nenhum cálculo.\n"
        "- CRÍTICO: Se você vir 'total_linhas: 58.643' no contexto, use EXATAMENTE 58.643, não faça nenhum cálculo.\n\n"
        "Pergunta: {pergunta}\n\n"
        "Contexto (trechos relevantes):\n{contexto}\n\n"
        "Resposta objetiva e concisa em PT-BR:"
    )
    return PromptTemplate.from_template(template)

def preparar_llm_e_embeddings():
    """Inicializa LLM Gemini e embeddings do Google. Requer GOOGLE_API_KEY no ambiente."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or not api_key.strip():
        raise RuntimeError("Defina a variável de ambiente GOOGLE_API_KEY para usar o Gemini.")
    with _suppress_stderr_during_imports():
        genai.configure(api_key=api_key)
    # Interrompe a supressão global após inicializações críticas
    _silence_stderr_stop()
    llm_local = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.0,
    )
    # Para embeddings, a API espera o nome completo do recurso "models/<id>"
    with _suppress_stderr_during_imports():
        emb_local = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    return llm_local, emb_local

def responder_com_rag(pergunta, dados_textuais, llm, embeddings, top_k=6):
    """Executa RAG sobre os dados_textuais: chunking, embeddings, recuperação e geração de resposta."""
    if not dados_textuais or not str(dados_textuais).strip():
        return "Não há dados disponíveis no banco para responder à pergunta."

    # 1) Split em chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)
    chunks = splitter.split_text(str(dados_textuais))
    if not chunks:
        return "Não foi possível preparar o contexto para a resposta."

    # 2) Embeddings de chunks e da pergunta
    try:
        with _suppress_stderr_during_imports():
            chunk_embeddings = embeddings.embed_documents(chunks)
            query_embedding = embeddings.embed_query(pergunta)
    except Exception as e:
        return (
            "Não foi possível gerar embeddings para recuperar o contexto. "
            "Verifique sua chave de API e o modelo de embeddings. Detalhe: " + str(e)
        )
    query_vec = np.array(query_embedding, dtype=float)

    # 3) Similaridade e seleção Top-K
    scores = []
    for idx, emb in enumerate(chunk_embeddings):
        vec = np.array(emb, dtype=float)
        score = _cosine_similarity(query_vec, vec)
        scores.append((score, idx))
    scores.sort(key=lambda x: x[0], reverse=True)
    selecionados = [chunks[i] for _, i in scores[:max(1, min(top_k, len(chunks)))] ]
    contexto = "\n\n".join(selecionados)

    # 4) Prompt RAG e geração
    prompt = construir_rag_prompt()
    chain_local = prompt | llm
    with _suppress_stderr_during_imports():
        resposta = chain_local.invoke({
        "pergunta": pergunta,
        "contexto": contexto,
        })
    # Garantir que retornamos apenas o texto da resposta
    try:
        if hasattr(resposta, "content") and isinstance(resposta.content, str):
            return formatar_valores_monetarios_no_texto(resposta.content)
        # Alguns wrappers podem retornar dict-like
        if isinstance(resposta, dict) and "content" in resposta:
            return formatar_valores_monetarios_no_texto(str(resposta["content"]))
        return formatar_valores_monetarios_no_texto(str(resposta))
    except Exception:
        return formatar_valores_monetarios_no_texto(str(resposta))

print("Olá, sou a sua assistente virtual LeIA, como posso te ajudar hoje?")
print("Digite 'sair' quando quiser encerrar a minha assistência!")

# Inicializa LLM e Embeddings uma única vez
try:
    llm, embeddings = preparar_llm_e_embeddings()
    modo_sem_llm = False
except Exception as e:
    print(f"Aviso: {e}")
    print("Operando sem LLM. Somente exibindo os resultados da base.")
    llm, embeddings = None, None
    modo_sem_llm = True

while True:
    pergunta = input("Você: ")
    
    if pergunta.lower() in ['sair', 'exit', 'quit']:
        print("LeIA: Até Logo!")
        break 

    # Pesquisar no banco de dados
    print("LeIA: Aguarde um momento, por gentileza...")
    dados_banco = pesquisar_no_banco(pergunta)
    
    # Verificar se é uma resposta de custos por usuários (já formatada)
    if (dados_banco.startswith("O Usuário") or dados_banco.startswith("Nos últimos 3 meses") or 
        dados_banco.startswith("Não foram encontrados dados de custos") or 
        dados_banco.startswith("--- INFORMAÇÕES EXTRAÍDAS DA PERGUNTA ---")):
        print("LeIA: ", end="")
        imprimir_digitando(dados_banco)
        print("")
    # Verificar se é uma resposta de linhas ociosas (já formatada)
    elif (dados_banco.startswith("O Cliente") and 
        ("linhas ociosas" in dados_banco or "linha ociosa" in dados_banco or 
         "possui atualmente" in dados_banco or "possuiu em" in dados_banco or 
         "possuiu nos últimos" in dados_banco)):
        print("LeIA: ", end="")
        imprimir_digitando(dados_banco)
        print("")
    # Verificar se é uma resposta sobre termos de linhas (já formatada)
    elif (dados_banco.startswith("O Cliente") and 
        ("linhas sem termos" in dados_banco or "linha sem termo" in dados_banco or 
         "são do tipo" in dados_banco or "estão Ativas são do tipo" in dados_banco)):
        print("LeIA: ", end="")
        imprimir_digitando(dados_banco)
        print("")
    # Verificar se é uma resposta de linhas normais (deve passar pelo RAG)
    elif ("--- LINHAS POR FORNECEDOR" in dados_banco or 
          "--- TOTAL POR FORNECEDOR" in dados_banco or
          "--- DADOS BRUTOS" in dados_banco or
          "--- DEBUG:" in dados_banco):
        # Passar pelo RAG para formatar a resposta
        if not modo_sem_llm:
            try:
                resposta = responder_com_rag(pergunta, dados_banco, llm, embeddings, top_k=6)
                print("LeIA: ", end="")
                imprimir_digitando(resposta)
                print("")
            except Exception as e:
                print(f"Erro ao gerar resposta: {e}")
                print("Mostrando apenas resultados do banco:")
                imprimir_digitando(dados_banco)
                print("")
        else:
            print(f"\nResultados do banco de dados:")
            print(dados_banco)
            print("\n")
    elif modo_sem_llm:
        print(f"\nResultados do banco de dados:")
        print(dados_banco)
        print("\n")
    else:
        try:
            resposta = responder_com_rag(pergunta, dados_banco, llm, embeddings, top_k=6)
            print("LeIA: ", end="")
            imprimir_digitando(resposta)
            print("")
        except Exception as e:
            print(f"Erro ao gerar resposta: {e}")
            print("Mostrando apenas resultados do banco:")
            imprimir_digitando(dados_banco)
            print("")
