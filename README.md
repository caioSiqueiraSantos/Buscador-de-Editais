# 🔍 Buscador de Oportunidades para Inovação (MVP)

Aplicação web e pipeline de dados para busca, triagem e estruturação automatizada de editais, chamadas públicas e oportunidades de fomento à inovação (com foco em mobilidade urbana e tecnologias estratégicas).

> **Status do Projeto:** Atualmente em estágio de **MVP (Mínimo Produto Viável)**, concebido com arquitetura modular para migração e integração futura à **infraestrutura corporativa em nuvem da Microsoft Azure**.

---

## 🎯 Utilidade e Fontes Integradas

O sistema automatiza o monitoramento de fontes de fomento e parcerias tecnológicas:

1. **Coleta de dados multi-fonte:** Coleta estruturada com catálogo modular (`backend/scrapers/`) cobrindo **27 instituições** mapeadas (21 fontes ativas e capturadas com sucesso em testes dry-run, e 6 mapeadas com diagnóstico de bloqueio WAF/autenticação).
2. **Triagem temática:** Filtra chamadas com base em temas de interesse cadastrados (ex.: mobilidade sobre trilhos, hidrogênio verde, IA, MaaS), descartando itens irrelevantes antes do envio à IA para economizar requisições.
3. **Análise com IA (Google Gemini):** Estrutura e classifica oportunidades aderentes, extraindo resumos executivos, prazos e nível de aderência (*Alto*, *Médio*, *Baixo*).
4. **Armazenamento centralizado:** Persiste editais e temas em banco de dados PostgreSQL com controle de duplicidade.
5. **Painel de visualização:** Interface web interativa em React para pesquisa, filtros rápidos, visualização do edital bruto e gerenciamento do CRUD de temas em tempo real.

---

## 📊 Status de Mapeamento e Coleta das Fontes (27 Instituições)

Abaixo está o status consolidado da implementação e validação (em modo *dry-run*, sem escrita no banco ou consumo da API Gemini) de todas as 27 instituições da planilha de mapeamento:

| # | Órgão / Instituição | Chave CLI (`--fonte`) | Capturado? | Itens no Teste | Método de Extração Implementado | Observações Técnicas / Pontos de Atenção |
| :-: | :--- | :--- | :-: | :-: | :--- | :--- |
| 1 | **FINEP** | `finep` | ✅ Sim | 18 | API REST JSON (`/o/c/chamadapublicas`) | Filtra chamadas abertas e vigentes a partir de 2025. |
| 2 | **FAPESP** | `fapesp` | ✅ Sim | 74 | Web Scraping HTML (`fapesp.br/chamadas`) | Extrai chamadas abertas, prazos e áreas temáticas. |
| 3 | **CNPq** | `cnpq` | ✅ Sim | 14 | Web Scraping HTML (`gov.br/cnpq/.../abertas-para-submissao`) | O legado `memoria2.cnpq.br` retorna 403; extração migrada com sucesso para o portal `gov.br/cnpq`. |
| 4 | **CAPES** | `capes` | ✅ Sim | 32 | Web Scraping HTML (`gov.br/capes/.../editais-e-resultados-capes`) | Captura editais abertos, chamadas conjuntas e programas estratégicos. |
| 5 | **MCTI** | `mcti` | ✅ Sim | 10 | Web Scraping HTML (`gov.br/mcti/.../noticias` e FNDCT) | A rota antiga `/chamadas-publicas` retorna 404; captura direcionada às publicações de chamadas/prêmios e FNDCT. |
| 6 | **EMBRAPII** | `embrapii` | ✅ Sim | 47 | Híbrido: API WP-JSON + HTML (`/transparencia/#chamadas`) | Combina posts recentes de chamadas públicas com a tabela oficial de chamadas da área de Transparência. |
| 7 | **ANPEI** | `anpei` | ✅ Sim | 7 | API REST WordPress (`/wp-json/wp/v2/posts`) | Retorna publicações institucionais e oportunidades de PD&I/fomento. |
| 8 | **ANPROTEC** | `anprotec` | ✅ Sim | 22 | Híbrido: HTML (`/site/oportunidades/`) + WP-JSON | Excelente aderência: aba `/oportunidades/` concentra editais externos e chamadas para startups/ICTs. |
| 9 | **FACEPE** | `facepe` | ✅ Sim | 75 | Híbrido: API WP-JSON (`www2.facepe.br`) + HTML (`/editais/todos/`) | O domínio `www.facepe.br` redireciona para `www2.facepe.br`, onde a API WP-JSON e a listagem estão abertas. |
| 10 | **FAPAC** | `fapac` | ✅ Sim | 48 | Web Scraping HTML (`fapac.ac.gov.br/98-2/`) | **Atenção:** O domínio da planilha (`fapac.acre.gov.br`) foi desativado pelo governo; atualizado para `fapac.ac.gov.br`. |
| 11 | **FAPDF** | `fapdf` | ✅ Sim | 24 | Web Scraping HTML (`fap.df.gov.br/chamadas-internacionais-20261` e home) | A rota genérica `/editais/` retorna 404 no Liferay; extração apontada para as páginas ativas de chamadas e documentos SEI/DODF. |
| 12 | **FAPEAM** | `fapeam` | ✅ Sim | 4 | API Interna AJAX (`POST /wp-admin/admin-ajax.php?action=get-editais`) | A página usa Vue.js; mapeamos o endpoint POST interno consumindo as abas `editais-abertos` e `fluxo-continuo` com vigência exata. |
| 13 | **FAPEMAT** | `fapemat` | ✅ Sim | 6 | Web Scraping HTML (`fapemat.mt.gov.br` e `/editais`) | Extrai chamadas de subvenção econômica e editais estaduais vigentes no Liferay. |
| 14 | **FAPEMIG** | `fapemig` | ✅ Sim | 5 | Híbrido: Payload SSR (`__NUXT_DATA__`) + HTML (`/oportunidades/chamadas-e-editais`) | Novo portal em Nuxt 3; extração lê tanto os cards renderizados quanto o estado JSON SSR embutido na página. |
| 15 | **FAPERGS** | `fapergs` | ✅ Sim | 7 | Web Scraping HTML (`fapergs.rs.gov.br/abertos` e `/inicial`) | Captura editais abertos e chamadas em destaque na página inicial. |
| 16 | **FAPERJ** | `faperj` | ✅ Sim | 56 | Web Scraping HTML (`faperj.br/?id=28.5.7`) | Captura diretamente da Lista Oficial de Editais / Chamadas lançados em 2026 (links diretos para os PDFs dos editais). |
| 17 | **FAPESC** | `fapesc` | ✅ Sim | 14 | Híbrido: HTML (`/chamadas-abertas/`) + API WP-JSON | Captura todas as chamadas abertas de subvenção/pesquisa em SC e publicações recentes de editais. |
| 18 | **FUNDECT** | `fundect` | ✅ Sim | 16 | Web Scraping HTML (`fundect.ms.gov.br/informativos/consultas/`) | Extrai os editais e chamadas públicas do MS (filtrando anexos secundários). |
| 19 | **FUNTAC** | `funtac` | ✅ Sim | 6 | Web Scraping HTML (`funtac.ac.gov.br/editais/`) | **Atenção:** Domínio corrigido de `funtac.acre.gov.br` para `funtac.ac.gov.br`. A página pública contém apenas editais históricos (2021–2022). |
| 20 | **SENAI** | `senai` | ✅ Sim | 8 | Web Scraping HTML (`sp.senai.br/noticias`) | A rota `/inovacao` retorna 404; captura realizada via feed de notícias do SENAI-SP (hackathons, chamadas e cursos). |
| 21 | **SESI** | `sesi` | ✅ Sim | 10 | Web Scraping HTML (`sesisp.org.br/noticias`) | Captura notícias institucionais e projetos educacionais/tecnológicos (ex.: robótica); inclui pautas esportivas que são filtradas pela pipeline. |
| 22 | **BNDES** | `bndes` | ❌ Não | 0 | API CKAN (`dadosabertos.bndes.gov.br`) | **Ponto de Atenção:** Conexões automatizadas sofrem *Read Timeout* na porta 443 (firewall/anti-bot nos domínios `bndes.gov.br`). Desabilitado por padrão. |
| 23 | **DESENVOLVE SP** | `desenvolve_sp` | ❌ Não | 0 | Web Scraping / WP-JSON (`desenvolvesp.com.br`) | **Ponto de Atenção:** Bloqueado por WAF/Cloudflare (**HTTP 403 Forbidden**) em todas as rotas (HTML, `/feed/` e `/wp-json/`). Requer navegador headless ou liberação de IP. |
| 24 | **BID** | `bid` | ❌ Não | 0 | Web Scraping (`projectprocurement.iadb.org`) | **Ponto de Atenção:** Bloqueado por proteção anti-bot Akamai/Cloudflare (**HTTP 403 Forbidden**). Requer automação via navegador real (Playwright Stealth) ou API autenticada. |
| 25 | **CAF** | `caf` | ❌ Não | 0 | Web Scraping (`caf.com/pt/sobre-a-caf/licitacoes/`) | **Ponto de Atenção:** Bloqueado por WAF/Cloudflare (**HTTP 403 Forbidden**). Requer navegador headless com resolução de desafio JS. |
| 26 | **FIGROUP** | `figroup` | ❌ Não | 0 | Web Scraping (`financiamentodainovacao.com.br/editais/`) | **Ponto de Atenção:** O antigo blog agregador foi descontinuado e redireciona (301) para página institucional (`fi-groupbr.com`); os editais migraram para o portal fechado **FI Connect** (`connect.fi-group.com`), que exige login. |
| 27 | **FUNDEP** | `fundep` | ❌ Não | 0 | Web Scraping (`portaldecompras.fundep.ufmg.br`) | **Ponto de Atenção:** O portal institucional não lista editais de fomento abertos no HTML, e o Portal de Compras utiliza ASP.NET WebForms (`__doPostBack`) com controle de sessão/cookies. |

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
