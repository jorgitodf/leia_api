# LeIA - Funcionalidade JSON

## 📋 Visão Geral

A LeIA agora suporta entrada e saída em formato JSON, permitindo integração com sistemas externos e APIs.

## 🚀 Como Usar

### 1. Interface Streamlit

1. Acesse a interface Streamlit da LeIA
2. Na sidebar, ative o checkbox "🔧 Modo JSON"
3. Digite sua pergunta no formato JSON
4. Clique em "🚀 Processar JSON"

### 2. API REST

A LeIA agora inclui uma API REST para processamento JSON:

```bash
# Iniciar a API
python api_json.py
```

A API estará disponível em `http://localhost:5000`

## 📝 Formato de Entrada

### JSON de Entrada

```json
{
  "pergunta": "Qual o fornecedor com maior custo em janeiro de 2024?"
}
```

### Campos Aceitos

- `pergunta` (obrigatório): A pergunta a ser processada
- `question` (alternativo): Alias para `pergunta`
- `query` (alternativo): Alias para `pergunta`

## 📤 Formato de Saída

### JSON de Resposta

```json
{
  "sucesso": true,
  "pergunta": "Qual o fornecedor com maior custo em janeiro de 2024?",
  "resposta": "O Cliente Safra, o fornecedor com o maior custo no mês de janeiro de 2024 é Vivo, com um custo total de R$ 1.234.567,89, tipo de contrato Pós-pago.",
  "timestamp": "2024-01-15 14:30:25",
  "versao": "1.0"
}
```

### Campos de Resposta

- `sucesso` (boolean): Indica se a operação foi bem-sucedida
- `pergunta` (string): A pergunta original
- `resposta` (string): A resposta da LeIA
- `timestamp` (string): Data e hora da resposta
- `versao` (string): Versão da API
- `dados_extras` (object, opcional): Informações adicionais em caso de erro

## 🔗 Endpoints da API

### POST /pergunta
Processa uma pergunta em formato JSON.

**Exemplo de requisição:**
```bash
curl -X POST http://localhost:5000/pergunta \
  -H "Content-Type: application/json" \
  -d '{"pergunta": "Qual o fornecedor com maior custo em janeiro de 2024?"}'
```

### GET /exemplos
Retorna exemplos de perguntas e formatos.

**Exemplo:**
```bash
curl http://localhost:5000/exemplos
```

### GET /health
Verifica o status da API.

**Exemplo:**
```bash
curl http://localhost:5000/health
```

### GET /
Página inicial com documentação da API.

## 🧪 Testando a Funcionalidade

Execute o script de teste:

```bash
python teste_json.py
```

Este script testará várias perguntas e verificará se as respostas estão no formato JSON correto.

## 📚 Exemplos de Perguntas

### Custos por Fornecedor
```json
{
  "pergunta": "Qual o fornecedor com maior custo em janeiro de 2024?"
}
```

### Linhas Telefônicas
```json
{
  "pergunta": "Quantas linhas ativas tem o cliente Safra?"
}
```

### Custos por Usuário
```json
{
  "pergunta": "Qual usuário teve maior custo no mês atual?"
}
```

### Linhas Ociosas
```json
{
  "pergunta": "Quantas linhas ociosas tem o cliente Safra?"
}
```

### Termos de Linhas
```json
{
  "pergunta": "Quantas linhas no Cliente Safra não possuem termo?"
}
```

## ⚙️ Configuração

### Variáveis de Ambiente

```bash
# API
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=False

# Banco de Dados
DB_HOST=localhost
DB_PORT=5441
DB_NAME=LeIA
DB_USER=postgres
DB_PASSWORD=postgres
DB_SSLMODE=require

# Google AI
GOOGLE_API_KEY=sua_chave_aqui
```

## 🔧 Tratamento de Erros

### Erro de JSON Inválido
```json
{
  "sucesso": false,
  "pergunta": "N/A",
  "resposta": "JSON inválido: Expecting ',' delimiter: line 1 column 15 (char 14)",
  "timestamp": "2024-01-15 14:30:25",
  "versao": "1.0"
}
```

### Erro de Campo Obrigatório
```json
{
  "sucesso": false,
  "pergunta": "N/A",
  "resposta": "Campo 'pergunta' não encontrado no JSON",
  "timestamp": "2024-01-15 14:30:25",
  "versao": "1.0"
}
```

### Erro Interno
```json
{
  "sucesso": false,
  "pergunta": "Qual o fornecedor com maior custo?",
  "resposta": "Erro interno: Connection timeout",
  "timestamp": "2024-01-15 14:30:25",
  "versao": "1.0"
}
```

## 🚀 Iniciando os Serviços

### Interface Streamlit
```bash
streamlit run app.py
```

### API REST
```bash
python api_json.py
```

### Teste
```bash
python teste_json.py
```

## 📞 Suporte

Para dúvidas ou problemas com a funcionalidade JSON, verifique:

1. Se o JSON de entrada está no formato correto
2. Se a API está rodando na porta correta
3. Se as variáveis de ambiente estão configuradas
4. Se o banco de dados está acessível

## 🔄 Versões

- **v1.0**: Implementação inicial da funcionalidade JSON
  - Suporte a entrada JSON
  - Resposta em formato JSON
  - API REST
  - Interface Streamlit com modo JSON
  - Tratamento de erros
  - Script de teste
