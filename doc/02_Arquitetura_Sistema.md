# Arquitetura do Sistema (MVP)

## 1. Visão da Solução

```text
Equipe / Usuário Corporativo
   |
   v
Frontend React/Vite (Planejado: Azure Static Web Apps com Entra ID)
   |
   | HTTPS / JSON (CORS restrito)
   v
API FastAPI (Planejado: Azure Container Apps / App Service)
   |
   | Conexão segura / SSL (Planejado: VNet / Private Endpoint)
   v
PostgreSQL (Planejado: Azure Database for PostgreSQL)
   ^
   | Gravação unificada das oportunidades
   |
Pipeline de Coleta e IA (backend/pipeline.py)
   ^
   | Acionamento Semanal / Webhook
   |
Orquestrador n8n (Disparo semanal + Notificação de Alta Aderência)
   |
   +---> Fontes Ativas: [FINEP (REST API), FAPESP (Scraper HTML)]
   +---> Disparo de Alerta: [Teams / E-mail com Link Pré-filtrado]
```

---

## 2. Stack Tecnológica do MVP

- **Fontes e Coleta:** Python, `requests`, `beautifulsoup4`, com arquitetura modular de scrapers (`backend/scrapers/`).
- **IA Semântica:** Google Gemini por meio do SDK `google-genai`, com validação estruturada via Pydantic.
- **Backend:** FastAPI assíncrono executado por Uvicorn.
- **Banco de Dados:** PostgreSQL relacional com controle de unicidade por link.
- **Frontend:** Single Page Application (SPA) em React com Vite e Tailwind CSS.
- **Automação e Notificações:** **n8n** gerenciando cron semanal e envio de alertas com links pré-filtrados.

---

## 3. Organização do Projeto

```text
Buscador-de-Editais/
├── backend/
│   ├── database.py              # Conexão e inicialização do PostgreSQL
│   ├── pipeline.py              # Pipeline unificada (filtro temático + Gemini + deduplicação)
│   ├── scraper_ai.py            # Ponto de entrada CLI para coletas
│   ├── scrapers/                # Módulos especializados por órgão
│   │   ├── base.py              # Classe base abstrata para scrapers
│   │   ├── finep.py             # Integração FINEP (API REST)
│   │   └── fapesp.py            # Integração FAPESP (Web Scraping)
│   ├── main.py                  # API REST FastAPI e CRUD de temas
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
            ├── GerenciadorTemas.jsx
            ├── ModalDescarte.jsx
            └── PainelAprendizadoIA.jsx
```

---

## 4. Responsabilidades dos Módulos

### Módulos de Scrapers (`scrapers/`)
Cada fonte de fomento possui seu próprio coletor herdado de `BaseScraper`. Ele sabe como consultar a fonte (seja via REST API como a FINEP ou via parser HTML como a FAPESP) e retorna uma lista padronizada de editais brutos.

### Pipeline Central (`pipeline.py`)
Centraliza as regras de negócio:
1. Normalização de datas e termos;
2. Pré-filtro baseado nos temas ativos do banco;
3. Chamada estruturada ao Gemini apenas para itens aderentes;
4. Gravação idempotente no PostgreSQL.

### Automação n8n
- **Gatilho de Execução:** Executa periodicamente a cada semana chamando o backend.
- **Notificação:** Analisa as saídas, filtra por aderência `Alta`, enumera as oportunidades e envia alerta aos responsáveis contendo o link da aplicação já filtrado por alta relevância.

---

## 5. Planejamento de Integração Azure Corporativa

O MVP foi projetado respeitando padrões corporativos de nuvem para transição suave à infraestrutura Azure:

| Componente | Implementação MVP | Alvo Corporativo Azure |
|---|---|---|
| **API Backend** | FastAPI / Container | **Azure App Service** ou **Azure Container Apps** |
| **Banco de Dados** | PostgreSQL gerenciado | **Azure Database for PostgreSQL (Flexible Server)** com VNet e Private Link |
| **Frontend** | React / SPA | **Azure Static Web Apps** com Single Sign-On (**Microsoft Entra ID**) |
| **Agendamento** | n8n | **Azure Logic Apps** ou n8n corporativo |
| **Segurança e Chaves** | Variáveis de ambiente | **Azure Key Vault** para chaves de API e segredos de banco |
