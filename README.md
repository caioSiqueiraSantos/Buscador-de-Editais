# 🔍 Buscador de Oportunidades para Inovação

Aplicação web e pipeline de dados para busca, triagem e estruturação automatizada de editais, chamadas públicas e oportunidades de fomento à inovação (com foco em mobilidade urbana e tecnologias estratégicas).

---

## 🎯 Utilidade

O sistema automatiza o monitoramento de fontes de fomento e parcerias tecnológicas:

1. **Coleta de dados:** Consulta diretamente a API REST pública da FINEP (com suporte arquitetural para futuras integrações como FAPESP e SENAI).
2. **Triagem temática:** Filtra chamadas com base em temas de interesse cadastrados (ex.: mobilidade sobre trilhos, hidrogênio verde, IA, MaaS), descartando itens irrelevantes antes do envio à IA para economizar requisições.
3. **Análise com IA (Google Gemini):** Estrutura e classifica oportunidades aderentes, extraindo resumos executivos, prazos e nível de aderência (*Alto*, *Médio*, *Baixo*).
4. **Armazenamento centralizado:** Persiste editais e temas em banco de dados PostgreSQL com controle de duplicidade.
5. **Painel de visualização:** Interface web interativa em React para pesquisa, filtros rápidos, visualização do edital bruto e gerenciamento do CRUD de temas em tempo real.

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

## 🚀 Deploy

A arquitetura desacoplada permite o deploy independente de cada componente:

| Componente | Hospedagem Recomendada | Variáveis de Ambiente Necessárias |
|---|---|---|
| **Frontend** | **Vercel** | `VITE_API_URL` (URL pública da API no backend) |
| **Backend (API)** | **Render** / Railway / Fly.io | `DATABASE_URL`, `GEMINI_API_KEY`, `FRONTEND_URL` (URL da Vercel) |
| **Banco de Dados** | **Neon** / Supabase / Render PG | PostgreSQL gerenciado com conexão SSL |
| **Scraper** | Terminal local, GitHub Actions ou Cron Job | `DATABASE_URL`, `GEMINI_API_KEY` |

- **Ambiente de produção:** Deploy configurado via Vercel (frontend) e nuvem gerenciada (backend e banco de dados).
- Mais detalhes sobre a arquitetura e o fluxo de processamento podem ser encontrados na pasta [`doc/`](doc/).
