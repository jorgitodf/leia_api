# 🚀 Guia de Deploy em Produção - LeIA API JSON

## ✅ **PROBLEMA RESOLVIDO!**

A API agora carrega corretamente as configurações do arquivo `.env` e não tenta conectar com localhost.

## 🔧 **Configurações Corrigidas**

### **1. Carregamento do .env**
- ✅ Adicionado `load_dotenv()` na API
- ✅ Configurações do banco carregadas do arquivo `.env`
- ✅ Verificação das configurações na inicialização

### **2. Novo Endpoint de Configuração**
- ✅ `GET /config` - Verifica configurações do banco
- ✅ Mostra host, porta, database, usuário (senha oculta)

## 📋 **Passos para Deploy em Produção**

### **1. Preparar Arquivo .env**

Crie um arquivo `.env` no servidor com as configurações corretas:

```bash
# Configurações do Banco de Dados PostgreSQL
DB_HOST=seu_host_do_banco_aqui
DB_PORT=5432
DB_NAME=seu_nome_do_banco_aqui
DB_USER=seu_usuario_do_banco_aqui
DB_PASSWORD=sua_senha_do_banco_aqui
DB_SSLMODE=require

# Configurações da API
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=False

# Google AI API Key
GOOGLE_API_KEY=sua_chave_do_google_ai_aqui
```

### **2. Testar Configurações**

Antes de iniciar a API, teste as configurações:

```bash
python teste_configuracao_banco.py
```

**Resultado esperado:**
```
✅ Conexão com o banco de dados bem-sucedida!
🎉 CONFIGURAÇÃO OK!
```

### **3. Iniciar a API**

```bash
python api_json_final.py
```

**Logs esperados:**
```
🚀 Inicializando LeIA API (Versão Final)...
🔧 Configurações do Banco de Dados:
   Host: seu_host_do_banco_aqui
   Port: 5432
   Database: seu_nome_do_banco_aqui
   User: seu_usuario_do_banco_aqui
   Password: ***
✅ LLM e embeddings inicializados com sucesso!
🌐 Servidor rodando em http://0.0.0.0:5000
```

### **4. Verificar Endpoints**

#### **Health Check:**
```bash
curl http://seu_servidor:5000/health
```

#### **Configurações do Banco:**
```bash
curl http://seu_servidor:5000/config
```

#### **Teste de Pergunta:**
```bash
curl -X POST http://seu_servidor:5000/pergunta \
  -H "Content-Type: application/json" \
  -d '{"pergunta": "Qual o fornecedor com maior custo em janeiro de 2024?"}'
```

## 🔍 **Verificação de Problemas**

### **1. Verificar Configurações**
```bash
curl http://seu_servidor:5000/config
```

**Resposta esperada:**
```json
{
  "configuracao_banco": {
    "host": "seu_host_correto",
    "port": "5432",
    "database": "seu_banco_correto",
    "user": "seu_usuario_correto",
    "password": "***",
    "sslmode": "require"
  }
}
```

### **2. Se ainda conectar com localhost:**
- ✅ Verifique se o arquivo `.env` existe
- ✅ Verifique se as variáveis estão corretas
- ✅ Reinicie a API após alterar o `.env`

### **3. Teste de Conexão Manual:**
```bash
python teste_configuracao_banco.py
```

## 📊 **Exemplos de Configuração por Provedor**

### **Heroku:**
```bash
DB_HOST=ec2-xx-xx-xx-xx.compute-1.amazonaws.com
DB_PORT=5432
DB_NAME=d1234567890abc
DB_USER=abcdefghijklmn
DB_PASSWORD=1234567890abcdefghijklmnopqrstuvwxyz
```

### **Railway:**
```bash
DB_HOST=containers-us-west-xxx.railway.app
DB_PORT=5432
DB_NAME=railway
DB_USER=postgres
DB_PASSWORD=seu_password_aqui
```

### **DigitalOcean:**
```bash
DB_HOST=db-postgresql-nyc1-12345-do-user-123456-0.b.db.ondigitalocean.com
DB_PORT=25060
DB_NAME=defaultdb
DB_USER=doadmin
DB_PASSWORD=seu_password_aqui
```

### **Supabase:**
```bash
DB_HOST=aws-1-us-east-2.pooler.supabase.com
DB_PORT=6543
DB_NAME=postgres
DB_USER=postgres.xxxxxxxxxxxxxxxx
DB_PASSWORD=seu_password_aqui
```

## 🎯 **Endpoints Disponíveis**

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/health` | GET | Status da API |
| `/config` | GET | Configurações do banco |
| `/pergunta` | POST | Processar pergunta JSON |
| `/exemplos` | GET | Exemplos de perguntas |
| `/` | GET | Documentação |

## 🚀 **Deploy Automatizado**

### **Script de Deploy:**
```bash
#!/bin/bash
echo "🚀 Iniciando deploy da LeIA API..."

# Testar configurações
echo "🔧 Testando configurações..."
python teste_configuracao_banco.py

if [ $? -eq 0 ]; then
    echo "✅ Configurações OK! Iniciando API..."
    python api_json_final.py
else
    echo "❌ Erro nas configurações!"
    exit 1
fi
```

## 🎉 **Resultado Final**

Após o deploy, a API deve:

1. ✅ **Carregar configurações do .env**
2. ✅ **Conectar com o banco correto**
3. ✅ **Mostrar configurações na inicialização**
4. ✅ **Responder perguntas via JSON**
5. ✅ **Fornecer endpoint de verificação**

**A API está pronta para produção!** 🚀
