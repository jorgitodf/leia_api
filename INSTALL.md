# 🚀 Instalação Rápida - LeIA Gemini

## ⚡ Instalação em 5 passos

### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd LeIA_Gemini
```

### 2. Crie e ative o ambiente virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure o arquivo .env
Crie o arquivo `.env` na raiz do projeto:

```env
# Configurações do PostgreSQL
DB_HOST=localhost
DB_PORT=5441
DB_NAME=LeIA
DB_USER=postgres
DB_PASSWORD=postgres

# Configurações da API do Google Gemini
GOOGLE_API_KEY=sua_chave_api_aqui
```

### 5. Execute o sistema
```bash
python main.py
```

## 🔧 Comandos Úteis

### Instalar dependências de desenvolvimento
```bash
pip install -r requirements-dev.txt
```

### Verificar instalação
```bash
python -c "import main; print('✅ Instalação OK!')"
```

### Atualizar dependências
```bash
pip install -r requirements.txt --upgrade
```

## ❗ Problemas Comuns

### Erro de conexão com PostgreSQL
- Verifique se o PostgreSQL está rodando
- Confirme as credenciais no arquivo `.env`
- Teste a conexão: `psql -h localhost -p 5441 -U postgres -d LeIA`

### Erro da API do Google Gemini
- Verifique se a `GOOGLE_API_KEY` está correta no `.env`
- Confirme se a API está habilitada no Google Cloud Console

### Erro de dependências
- Atualize o pip: `python -m pip install --upgrade pip`
- Reinstale as dependências: `pip install -r requirements.txt --force-reinstall`

## 📞 Suporte
Se encontrar problemas, verifique:
1. Versão do Python (3.8+)
2. Arquivo `.env` configurado
3. PostgreSQL rodando
4. Chave da API válida
