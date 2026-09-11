# Arquitetura do Sistema

## 1. Visão da solução

```text
Usuário
   |
   v
Frontend React/Vite publicado
   |
   | HTTPS / JSON
   v
API FastAPI publicada
   |
   | conexão privada por variável de ambiente
   v
PostgreSQL hospedado

Scraper FINEP + Gemini
   | execução manual pelo terminal
   +-----------------------> PostgreSQL hospedado
```

O frontend não acessa o banco diretamente. Toda leitura ou alteração passa pela API FastAPI.

## 2. Stack tecnológica

- **Coleta:** Python e `requests`, consumindo o endpoint REST da FINEP.
- **IA:** Google Gemini por meio do pacote `google-genai`, com resposta estruturada validada por Pydantic.
- **Backend:** FastAPI executado por Uvicorn.
- **Banco:** PostgreSQL, acessado pelo backend e pelo scraper por meio da variável de ambiente de conexão.
- **Frontend:** React em uma SPA empacotada pelo Vite.
- **Estilização:** Tailwind CSS e CSS da aplicação.

## 3. Organização do projeto

```text
Buscador-de-Editais/
├── backend/
│   ├── database.py              # Conexão e inicialização do PostgreSQL
│   ├── scraper_ai.py            # Coleta, filtro, IA e persistência
│   ├── main.py                  # API REST e CRUD de temas
│   └── requirements.txt         # Dependências Python
├── doc/
│   ├── 01_Visao_Geral_PoC.md
│   ├── 02_Arquitetura_Sistema.md
│   └── 03_Fluxo_de_Dados.md
└── frontend/
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx
        └── components/
            └── GerenciadorTemas.jsx
```

Arquivos `.env` são usados apenas no ambiente de execução e não devem ser versionados.

## 4. Responsabilidades

### Scraper

`scraper_ai.py` é um processo batch independente da API. Ele consulta a FINEP, descarta itens irrelevantes, solicita a análise do Gemini para os itens aderentes e grava os resultados no PostgreSQL.

### API

`main.py` fornece:

- `GET /oportunidades`
- `GET /temas`
- `POST /temas`
- `PUT /temas/{tema_id}`
- `DELETE /temas/{tema_id}`
- `GET /health`, quando habilitado no ambiente publicado

### Frontend

`App.jsx` consulta oportunidades e temas e aplica busca e filtros no navegador. `GerenciadorTemas.jsx` executa o CRUD de temas pela API.

## 5. Decisões arquiteturais

- **Batch separado da API:** o scraper não precisa permanecer rodando para que o painel funcione.
- **PostgreSQL compartilhado:** API e scraper consultam a mesma fonte persistente.
- **Filtro antes da IA:** reduz chamadas ao Gemini e evita processar itens sem aderência temática.
- **Deduplicação em duas camadas:** a aplicação verifica registros existentes e o banco mantém unicidade no link.
- **Retenção do texto bruto:** permite consultar o conteúdo armazenado mesmo que a página original seja alterada ou removida.
- **Configuração por ambiente:** URLs, credenciais e chaves não ficam no código.
- **CORS restrito:** a API deve aceitar a origem publicada do frontend e, quando necessário, a origem local de desenvolvimento.

## 6. Evoluções futuras

- Agendamento automático do scraper.
- Integração com novas fontes.
- Autenticação e autorização.
- Notificações por e-mail ou Teams.
- Observabilidade, auditoria e métricas de execução.
