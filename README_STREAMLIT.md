# LeIA - Interface Web com Streamlit

## 🚀 Como Executar a Interface Web

### 1. Instalar Dependências

Primeiro, certifique-se de que todas as dependências estão instaladas:

```bash
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

Certifique-se de que o arquivo `.env` está configurado com:

```env
# Banco de Dados PostgreSQL
DB_HOST=localhost
DB_PORT=5441
DB_NAME=LeIA
DB_USER=postgres
DB_PASSWORD=postgres

# Google Gemini AI
GOOGLE_API_KEY=sua_chave_api_aqui
```

### 3. Executar a Aplicação Web

Para iniciar a interface web, execute:

```bash
streamlit run app.py
```

### 4. Acessar no Navegador

Após executar o comando acima, o Streamlit irá:

1. Iniciar o servidor local
2. Abrir automaticamente o navegador
3. Exibir a interface da LeIA

Se não abrir automaticamente, acesse: **http://localhost:8501**

## 🎯 Funcionalidades da Interface Web

### ✨ Interface Amigável
- **Chat interativo** com histórico de conversas
- **Design moderno** com gradientes e animações
- **Sidebar informativa** com exemplos de perguntas
- **Status do sistema** em tempo real

### 🔧 Recursos Avançados
- **Processamento em tempo real** com indicadores de progresso
- **Modo sem LLM** quando a API não está disponível
- **Limpeza de histórico** com um clique
- **Responsivo** para diferentes tamanhos de tela

### 📊 Tipos de Consultas Suportadas
- **Custos por fornecedor**: "Qual o fornecedor com maior custo em janeiro de 2024?"
- **Linhas telefônicas**: "Quantas linhas ativas tem o cliente Safra?"
- **Custos por usuário**: "Quem foi o usuário com maior custo no mês atual?"
- **Linhas ociosas**: "Quantas linhas ociosas tem o cliente Sotreq?"

## 🆚 Diferenças entre Interface Web e Terminal

| Recurso | Terminal (main.py) | Web (app.py) |
|---------|-------------------|--------------|
| **Interface** | Linha de comando | Navegador web |
| **Histórico** | Não salvo | Salvo na sessão |
| **Visual** | Texto simples | Design moderno |
| **Usabilidade** | Para desenvolvedores | Para usuários finais |
| **Acesso** | Local | Pode ser compartilhado |

## 🔧 Solução de Problemas

### Erro: "ModuleNotFoundError: No module named 'streamlit'"
```bash
pip install streamlit>=1.28.0
```

### Erro: "Port 8501 is already in use"
```bash
streamlit run app.py --server.port 8502
```

### Erro de conexão com banco de dados
- Verifique se o PostgreSQL está rodando
- Confirme as credenciais no arquivo `.env`
- Teste a conexão com o banco

### Erro de API do Google Gemini
- Verifique se a `GOOGLE_API_KEY` está correta
- Confirme se a API está ativa
- A aplicação funcionará em modo "apenas banco de dados" se a API falhar

## 📱 Acesso Remoto

Para acessar a aplicação de outros dispositivos na rede:

```bash
streamlit run app.py --server.address 0.0.0.0
```

Depois acesse: `http://SEU_IP:8501`

## 🎨 Personalização

A interface pode ser personalizada editando o arquivo `app.py`:

- **Cores**: Modifique o CSS no início do arquivo
- **Logo**: Adicione uma imagem na seção de cabeçalho
- **Exemplos**: Altere os exemplos de perguntas na sidebar
- **Layout**: Ajuste o `st.set_page_config()`

## 🔄 Atualizações

Para atualizar a aplicação:

1. Pare o servidor (Ctrl+C)
2. Atualize o código se necessário
3. Execute novamente: `streamlit run app.py`

---

**🎉 Pronto! Agora você tem uma interface web moderna para interagir com a LeIA!**
