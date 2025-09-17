# Configuração do Arquivo .env

Para configurar as variáveis de ambiente, crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:

```env
# Configurações do PostgreSQL
DB_HOST=localhost
DB_PORT=5441
DB_NAME=LeIA
DB_USER=postgres
DB_PASSWORD=postgres

# Configurações da API do Google Gemini
GOOGLE_API_KEY=your_google_api_key_here
```

## Variáveis de Ambiente

### PostgreSQL
- `DB_HOST`: Endereço do servidor PostgreSQL (padrão: localhost)
- `DB_PORT`: Porta do PostgreSQL (padrão: 5441)
- `DB_NAME`: Nome do banco de dados (padrão: LeIA)
- `DB_USER`: Usuário do PostgreSQL (padrão: postgres)
- `DB_PASSWORD`: Senha do PostgreSQL (padrão: postgres)

### Google Gemini API
- `GOOGLE_API_KEY`: Chave da API do Google Gemini (obrigatório para funcionalidade completa)

## Como Criar o Arquivo .env

1. Na raiz do projeto, crie um arquivo chamado `.env`
2. Copie o conteúdo acima para o arquivo
3. Substitua os valores pelos seus dados reais
4. Salve o arquivo

## Valores Padrão

Se o arquivo `.env` não existir ou alguma variável não estiver definida, o sistema usará os valores padrão mostrados acima.
