# 🔍 Buscador de Oportunidades para Inovação (MVP)

Aplicação web e pipeline de dados para busca, triagem e estruturação automatizada de editais, chamadas públicas e oportunidades de fomento à inovação (com foco em mobilidade urbana e tecnologias estratégicas).

> **Status do Projeto:** Atualmente em estágio de **MVP (Mínimo Produto Viável)**, concebido com arquitetura modular para migração e integração futura à **infraestrutura corporativa em nuvem da Microsoft Azure**.

---

## 🎯 Utilidade e Fontes Integradas

O sistema automatiza o monitoramento de fontes de fomento e parcerias tecnológicas:

1. **Coleta de dados multi-fonte em 2 etapas:** Coleta estruturada com catálogo modular (`backend/scrapers/`) cobrindo **27 instituições** mapeadas (20 fontes ativas com dados recentes de 2025/2026+ enriquecidos com prazo e texto completo, 1 fonte com portal defasado de 2021–2022 desabilitada por redundância com a FAPAC, e 6 mapeadas com diagnóstico de bloqueio WAF/autenticação).
2. **Triagem temática e anti-ruído:** Filtra chamadas com base em temas de interesse cadastrados (ex.: mobilidade sobre trilhos, hidrogênio verde, IA, MaaS), descartando automaticamente resultados de editais encerrados, pautas esportivas, editais antigos (`<= 2024`) e itens divergentes antes do envio à IA para economizar requisições.
3. **Análise com IA (Google Gemini):** Estrutura e classifica oportunidades aderentes, extraindo resumos executivos, prazos e nível de aderência (*Alto*, *Médio*, *Baixo*).
4. **Armazenamento centralizado:** Persiste editais e temas em banco de dados PostgreSQL com controle de duplicidade.
5. **Painel de visualização:** Interface web interativa em React para pesquisa, filtros rápidos, visualização do edital bruto e gerenciamento do CRUD de temas em tempo real.

---

## 📊 Status de Mapeamento, Qualidade e Coleta das Fontes (27 Instituições)

Abaixo está o status consolidado da implementação, enriquecimento em 2 etapas (listagem + página interna do edital) e validação de qualidade/recência (em modo *dry-run*, sem escrita no banco ou consumo da API Gemini) de todas as 27 instituições da planilha de mapeamento:

| # | Órgão / Instituição | Chave CLI (`--fonte`) | Capturado? | Itens Válidos (2025/2026+) | Com Prazo (`DD/MM/AAAA`) | Com Texto Rico (`>=150 chars`) | Método de Extração Implementado | Observações Técnicas / Pontos de Atenção |
| :-: | :--- | :--- | :-: | :-: | :-: | :-: | :--- | :--- |
| 1 | **FINEP** | `finep` | ✅ Sim | 18 | 100% | 100% | API REST JSON (`/o/c/chamadapublicas`) | Filtra chamadas abertas e vigentes a partir de 2025 com prazos ISO e texto integral. |
| 2 | **FAPESP** | `fapesp` | ✅ Sim | 24 | 91,7% | 100% | Web Scraping HTML 2 Etapas (`fapesp.br/chamadas` + detalhe) | Filtra manuais fixos (IDs antigos) e visita cada chamada aberta para extrair cronograma e texto integral. |
| 3 | **CNPq** | `cnpq` | ✅ Sim | 12 | 75,0% | 100% | Web Scraping HTML 2 Etapas (`gov.br/cnpq/.../abertas-para-submissao`) | Migrado do legado `memoria2.cnpq.br` (403) para `gov.br/cnpq`, filtrando resultados encerrados. |
| 4 | **CAPES** | `capes` | ✅ Sim | 32 | 81,2% | 87,5% | Web Scraping HTML 2 Etapas (`gov.br/capes/.../editais-e-resultados-capes`) | Visita as páginas internas dos programas estratégicos para extrair escopo completo e prazos vigentes. |
| 5 | **MCTI** | `mcti` | ✅ Sim | 7 | — | 100% | Web Scraping HTML 2 Etapas (`gov.br/mcti/.../noticias` e FNDCT) | Filtra estritamente notícias de chamadas, seleções, prêmios e FNDCT (descartando curiosidades científicas gerais). |
| 6 | **EMBRAPII** | `embrapii` | ✅ Sim | 15 | 66,7% | 100% | Híbrido: API WP-JSON + HTML 2 Etapas (`/transparencia/`) | Filtra chamadas históricas encerradas (2016–2024) e retém apenas chamadas abertas/recentes (2025/2026+). |
| 7 | **ANPEI** | `anpei` | ✅ Sim | 6 | — | 66,7% | API REST WordPress (`/wp-json/wp/v2/posts`) | Extrai `content.rendered` completo das publicações de PD&I e fomento empresarial. |
| 8 | **ANPROTEC** | `anprotec` | ✅ Sim | 22 | 100% | 100% | Híbrido: HTML 2 Etapas (`/site/oportunidades/`) + WP-JSON | Visita cada oportunidade publicada para extrair o corpo completo e datas limite. |
| 9 | **FACEPE** | `facepe` | ✅ Sim | 57 | 70,2% | 15,8%* | Híbrido: API WP-JSON (`www2.facepe.br`) + HTML (`/editais/todos/`) | Filtra resultados preliminares/finais e editais `<= 2024`. *(Itens da tabela HTML apontam direto para PDF).* |
| 10 | **FAPAC** | `fapac` | ✅ Sim | 30 | 3,3%* | 100% | Web Scraping HTML (`fapac.ac.gov.br/98-2/`) | Domínio atualizado de `fapac.acre.gov.br` para `fapac.ac.gov.br`; filtra atas, comissões e resultados encerrados. |
| 11 | **FAPDF** | `fapdf` | ✅ Sim | 16 | —* | 100% | Web Scraping HTML 2 Etapas (`fap.df.gov.br/chamadas-internacionais-20261`) | Filtra extratos de resultados encerrados e anos `<= 2024` (links diretos para PDFs no SEI/DODF). |
| 12 | **FAPEAM** | `fapeam` | ✅ Sim | 4 | 100% | 100% | API Interna AJAX (`POST /wp-admin/admin-ajax.php?action=get-editais`) + HTML | Consome as abas `editais-abertos` e `fluxo-continuo` com vigência exata e enriquece o texto na página do edital. |
| 13 | **FAPEMAT** | `fapemat` | ✅ Sim | 3 | 66,7% | 100% | Web Scraping HTML 2 Etapas (`fapemat.mt.gov.br` e `/editais`) | Filtra resultados finais/preliminares e enriquece o corpo completo das chamadas vigentes. |
| 14 | **FAPEMIG** | `fapemig` | ✅ Sim | 4 | —* | 100% | Híbrido: Payload SSR (`__NUXT_DATA__`) + HTML 2 Etapas | Deduplica chamadas entre SSR e HTML e extrai o escopo completo das oportunidades abertas. |
| 15 | **FAPERGS** | `fapergs` | ✅ Sim | 6 | —* | 100% | Web Scraping HTML 2 Etapas (`fapergs.rs.gov.br/abertos` e `/inicial`) | Remove resultados preliminares e imagens de banner, enriquecendo o texto dos editais abertos. |
| 16 | **FAPERJ** | `faperj` | ✅ Sim | 56 | 98,2% | 100% | Web Scraping HTML (`faperj.br/?id=28.5.7`) | Extrai títulos reais e prazos por extenso diretamente da Lista Oficial de Editais 2025/2026. |
| 17 | **FAPESC** | `fapesc` | ✅ Sim | 10 | 50,0% | 90,0% | Híbrido: HTML 2 Etapas (`/chamadas-abertas/`) + API WP-JSON | Filtra resultados de mérito/admissibilidade e retém apenas chamadas abertas vigentes. |
| 18 | **FUNDECT** | `fundect` | ✅ Sim | 16 | 25,0% | 100% | Web Scraping HTML (`fundect.ms.gov.br/informativos/consultas/`) | Filtra chamadas antigas (`<= 2024`) e anexos secundários, retendo os editais principais do MS. |
| 19 | **SENAI** | `senai` | ✅ Sim | 6 | 16,7% | 100% | Web Scraping HTML 2 Etapas (`sp.senai.br/noticias`) | Filtra homenagens institucionais e enriquece o texto completo de hackathons, cursos e chamadas tecnológicas. |
| 20 | **SESI** | `sesi` | ✅ Sim | 1 | 100% | 100% | Web Scraping HTML 2 Etapas (`sesisp.org.br/noticias`) | Filtra 100% das pautas esportivas (Vôlei, Judô, Rugby, Basquete), retendo apenas educação/robótica. |
| 21 | **FUNTAC** | `funtac` | ⚠️ Histórico | 0 *(6 de 2021–22)* | — | — | Web Scraping HTML (`funtac.ac.gov.br/editais/`) | **Desabilitado por padrão:** O portal da FUNTAC contém apenas PDFs antigos (2021–2022); os editais atuais do Acre (2025/2026) estão centralizados na **FAPAC**. |
| 22 | **BNDES** | `bndes` | ❌ Não | 0 | — | — | API CKAN (`dadosabertos.bndes.gov.br`) | **Ponto de Atenção:** Conexões automatizadas sofrem *Read Timeout* na porta 443 (firewall/anti-bot nos domínios `bndes.gov.br`). Desabilitado por padrão. |
| 23 | **DESENVOLVE SP** | `desenvolve_sp` | ❌ Não | 0 | — | — | Web Scraping / WP-JSON (`desenvolvesp.com.br`) | **Ponto de Atenção:** Bloqueado por WAF/Cloudflare (**HTTP 403 Forbidden**) em todas as rotas. Requer navegador headless ou liberação de IP. |
| 24 | **BID** | `bid` | ❌ Não | 0 | — | — | Web Scraping (`projectprocurement.iadb.org`) | **Ponto de Atenção:** Bloqueado por proteção anti-bot Akamai/Cloudflare (**HTTP 403 Forbidden**). Requer automação via navegador real (Playwright Stealth). |
| 25 | **CAF** | `caf` | ❌ Não | 0 | — | — | Web Scraping (`caf.com/pt/sobre-a-caf/licitacoes/`) | **Ponto de Atenção:** Bloqueado por WAF/Cloudflare (**HTTP 403 Forbidden**). Requer navegador headless com resolução de desafio JS. |
| 26 | **FIGROUP** | `figroup` | ❌ Não | 0 | — | — | Web Scraping (`financiamentodainovacao.com.br/editais/`) | **Ponto de Atenção:** O antigo blog agregador redireciona (301) para página institucional (`fi-groupbr.com`); os editais migraram para o portal fechado **FI Connect** (`connect.fi-group.com`), que exige login. |
| 27 | **FUNDEP** | `fundep` | ❌ Não | 0 | — | — | Web Scraping (`portaldecompras.fundep.ufmg.br`) | **Ponto de Atenção:** O portal institucional não lista editais de fomento abertos no HTML, e o Portal de Compras utiliza ASP.NET WebForms (`__doPostBack`) com controle de sessão. |

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

# Listar todas as 27 fontes cadastradas no catálogo e seus status:
python scraper_ai.py --listar

# Testar apenas a coleta bruta (Dry-Run: sem gravar no banco e sem chamar a API do Gemini):
python scraper_ai.py --testar-coleta
python scraper_ai.py --fonte cnpq --testar-coleta
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

### 3. Execução e Orquestração do n8n

Para rodar o orquestrador n8n e automatizar as coletas semanais e alertas:

`ash
# Iniciar o container do n8n via Docker Compose
docker compose -f docker-compose.n8n.yml up -d
`
1. Acesse o n8n no navegador em http://localhost:5678.
2. Em **Workflows**, clique em **Import from File...** e selecione 
8n/workflow_buscador_editais.json.
3. O workflow já vem configurado com agendamento semanal (segundas às 08:00), chamada autenticada ao backend (POST /pipeline/executar), formatação executiva e disparo para Microsoft Teams / E-mail com links pré-filtrados.
4. Consulte o guia detalhado em [doc/04_Guia_Integracao_N8N.md](doc/04_Guia_Integracao_N8N.md).

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
