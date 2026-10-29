# 🔍 Buscador de Oportunidades para Inovação (MVP)

Aplicação web e pipeline de dados para busca, triagem e estruturação automatizada de editais, chamadas públicas e oportunidades de fomento à inovação (com foco em mobilidade urbana e tecnologias estratégicas).

> **Status do Projeto:** Atualmente em estágio de **MVP (Mínimo Produto Viável)**, concebido com arquitetura modular para migração e integração futura à **infraestrutura corporativa em nuvem da Microsoft Azure**.

---

## 🎯 Utilidade e Fontes Integradas

O sistema automatiza o monitoramento de fontes de fomento e parcerias tecnológicas:

1. **Coleta de dados multi-fonte:** Coleta estruturada com suporte ativo a:
   - **FINEP:** Consulta via API REST pública de chamadas públicas abertas e vigentes.
   - **FAPESP:** Coleta e parsing automatizado via web scraping com suporte a paginação e extração de detalhes.
   *(Estrutura extensível para novos órgãos como SENAI, CNPq, BNDES, etc.)*
2. **Triagem temática:** Filtra chamadas com base em temas de interesse cadastrados (ex.: mobilidade sobre trilhos, hidrogênio verde, IA, MaaS), descartando itens irrelevantes antes do envio à IA para economizar requisições.
3. **Análise com IA (Google Gemini):** Estrutura e classifica oportunidades aderentes, extraindo resumos executivos, prazos e nível de aderência (*Alto*, *Médio*, *Baixo*).
4. **Armazenamento centralizado:** Persiste editais e temas em banco de dados PostgreSQL com controle de duplicidade.
5. **Painel de visualização:** Interface web interativa em React para pesquisa, filtros rápidos, visualização do edital bruto e gerenciamento do CRUD de temas em tempo real.

---

## 🔄 Automação e Notificações (Fluxo n8n)

Para a operação contínua e automatizada do MVP, o fluxo de agendamento e alerta opera via **n8n**:
- **Disparo Semanal:** O n8n executa semanalmente uma rotina agendada (cron) que aciona o buscador/pipeline no backend para processar as novidades da semana em todas as fontes ativas (FINEP, FAPESP).
- **Notificação de Oportunidades de Alta Aderência:** O workflow filtra as oportunidades identificadas com aderência **Alta** e envia uma notificação automática (e-mail, Teams ou Slack) contendo:
  1. **Lista numerada** das oportunidades com alta aderência identificadas na rodada;
  2. **Resumo executivo, instituição e prazo de submissão** de cada item;
  3. **Link direto pré-filtrado** para a interface web (com o filtro de alta aderência já aplicado), direcionando a equipe técnica diretamente para a análise das oportunidades prioritárias.

---

## ☁️ Planejamento de Integração com Azure Corporativa

O MVP foi projetado de forma desacoplada para facilitar a transição para a infraestrutura corporativa na **Microsoft Azure**:
- **Backend e APIs:** Migração planejada para **Azure App Services** ou **Azure Container Apps** (com suporte a escalabilidade e rede virtual corporativa).
- **Banco de Dados:** Transição para **Azure Database for PostgreSQL** (instância gerenciada com isolamento de rede e conexão via VNet / Private Endpoints).
- **Frontend:** Hospedagem em **Azure Static Web Apps** com controle de acesso corporativo via **Microsoft Entra ID (Azure AD)**.
- **Orquestração e Notificações:** Integração contínua do n8n / **Azure Logic Apps** para disparos periódicos e notificações corporativas via Microsoft Teams.

---

## 💻 Como Rodar na Própria Máquina

### Pré-requisitos
- **Python 3.10+**
- **Node.js 18+** e npm
- Instância do **PostgreSQL** (local ou na nuvem, ex: Neon, Supabase)
- Chave de API do **Google Gemini** ([Google AI Studio](https://aistudio.google.com/))

---

### 1. Configuração do Backend e Scraper

Abra o terminal na pasta `backend`:

```bash
cd backend
```

Crie e ative um ambiente virtual:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

Instale as dependências:
```bash
pip install -r requirements.txt
```

Crie o arquivo `.env` dentro de `backend/`:
```env
DATABASE_URL=postgresql://usuario:senha@host:porta/banco?sslmode=require
GEMINI_API_KEY=sua_chave_gemini_aqui
FRONTEND_URL=http://localhost:5173
```

#### Executar a API (FastAPI):
```bash
uvicorn main:app --reload --port 8000
```
> A API estará disponível em `http://localhost:8000` (documentação Swagger em `http://localhost:8000/docs`). As tabelas do PostgreSQL são inicializadas automaticamente na primeira execução.

#### Executar a Coleta/Scrapers (sob demanda):
Em um novo terminal (com o ambiente virtual ativo na pasta `backend`):
```bash
# Executar todas as fontes ativas (FINEP, FAPESP, etc.):
python scraper_ai.py

# Ou filtrar por uma fonte específica:
python scraper_ai.py --fonte finep
python scraper_ai.py --fonte fapesp

# Listar todas as fontes cadastradas no catálogo:
python scraper_ai.py --listar
```
> Cada scraper busca oportunidades na sua fonte (REST API ou Web Scraping HTML) e envia para a pipeline unificada, que filtra pelos temas cadastrados no banco, classifica via Gemini e salva as novas oportunidades no PostgreSQL.

---

### 2. Configuração do Frontend

Abra outro terminal na pasta `frontend`:

```bash
cd frontend
```

Instale as dependências:
```bash
npm install
```

Crie o arquivo `.env.local` na pasta `frontend/`:
```env
VITE_API_URL=http://localhost:8000
```

Inicie o servidor de desenvolvimento:
```bash
npm run dev
```
> Acesse a aplicação no navegador em `http://localhost:5173`.

---

## 🚀 Deploy e Infraestrutura

A arquitetura desacoplada permite o deploy independente de cada componente:

| Componente | Ambiente Atual (MVP) | Destino Corporativo (Planejado) | Variáveis de Ambiente |
|---|---|---|---|
| **Frontend** | Static Hosting / Vercel | **Azure Static Web Apps** (com Entra ID / SSO) | `VITE_API_URL` |
| **Backend (API)** | Container / Nuvem Gerenciada | **Azure App Services / Container Apps** | `DATABASE_URL`, `GEMINI_API_KEY`, `FRONTEND_URL` |
| **Banco de Dados** | PostgreSQL Gerenciado (Neon/Supabase) | **Azure Database for PostgreSQL** | PostgreSQL com SSL / VNet |
| **Automação / Scraper** | Execução local ou agendada | **n8n / Azure Logic Apps** (disparo semanal e alertas) | `DATABASE_URL`, `GEMINI_API_KEY` |

- **Ambiente atual:** Deploy configurado via Vercel (frontend) e nuvem gerenciada (backend e banco de dados).
- Mais detalhes sobre a arquitetura e o fluxo de processamento podem ser encontrados na pasta [`doc/`](doc/).
