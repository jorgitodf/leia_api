# LeIA Gemini - Sistema de IA com RAG

Sistema de inteligência artificial que utiliza Google Gemini com RAG (Retrieval-Augmented Generation) para análise de dados PostgreSQL.

## 🚀 Funcionalidades

- **Análise de Custos por Usuários**: Consultas sobre custos de usuários por cliente e período
- **Análise de Linhas**: Consultas sobre status de licenças e linhas ativas
- **Análise de Linhas Ociosas**: Consultas sobre linhas ociosas por cliente
- **Sistema RAG**: Integração com Google Gemini para respostas inteligentes
- **Interface Conversacional**: Chat interativo em português brasileiro
- **🌐 Interface Web**: Aplicação web moderna com Streamlit para uso em navegador

## 📋 Pré-requisitos

- Python 3.8 ou superior
- PostgreSQL
- Chave da API do Google Gemini

## 🛠️ Instalação

### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd LeIA_Gemini
```

### 2. Crie um ambiente virtual
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto:

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

#### Opção 1: Interface Web (Recomendado)
```bash
# Método simples - duplo clique no arquivo
iniciar_leia_web.bat

# Ou via Python
python start_web.py

# Ou diretamente
streamlit run app.py
```

#### Opção 2: Interface Terminal
```bash
python main.py
```

> **💡 Dica**: A interface web oferece uma experiência mais amigável e moderna!

## 🌐 Interface Web

A interface web da LeIA oferece:

- **🎨 Design Moderno**: Interface limpa e intuitiva
- **💬 Chat Interativo**: Histórico de conversas salvo na sessão
- **📊 Status em Tempo Real**: Indicadores de progresso e status do sistema
- **📱 Responsivo**: Funciona em desktop, tablet e mobile
- **🔄 Modo Fallback**: Funciona mesmo sem conexão com a API do Gemini

### Acesso Rápido
- **URL Local**: http://localhost:8501
- **Arquivo de Inicialização**: `iniciar_leia_web.bat` (Windows)
- **Script Python**: `python start_web.py`

Para mais detalhes, consulte o [README_STREAMLIT.md](README_STREAMLIT.md).

## 📊 Estrutura do Banco de Dados

O sistema trabalha com as seguintes tabelas:

- `ia_custo_usuarios_linhas`: Custos por usuário
- `ia_linhas`: Status de linhas e licenças
- `ia_linhas_ociosas`: Linhas ociosas
- `ia_custo_fornecedor`: Custos por fornecedor

## 💬 Exemplos de Perguntas

### Custos por Usuários
- "Qual usuário do Cliente Safra possui o maior custo no mês atual?"
- "Qual usuário do Cliente Sonda teve o maior custo no mês de Agosto/2025?"
- "Quais são os usuários do Cliente Verzani que tiveram os maiores custos nos últimos 3 meses?"

### Linhas
- "Quantas linhas ativas possui o Cliente Safra no mês atual?"
- "Quantas linhas bloqueadas possui o Cliente Sonda em Julho/2025?"

### Linhas Ociosas
- "Quantas linhas ociosas possui o Cliente Safra atualmente?"
- "Quantas linhas ociosas possui o Cliente Sonda por operadora atualmente?"

## 🔧 Desenvolvimento

Para instalar dependências de desenvolvimento:

```bash
pip install -r requirements-dev.txt
```

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📞 Suporte

Para suporte, entre em contato com a equipe de desenvolvimento.
