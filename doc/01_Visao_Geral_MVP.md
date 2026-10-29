# Visão Geral do Projeto (MVP)

**Nome:** Buscador Automatizado de Oportunidades para Inovação  
**Fase:** Mínimo Produto Viável (MVP)  
**Área:** Inovação - Companhia de Metrô  
**Planejamento de Infraestrutura:** Transição para nuvem corporativa **Microsoft Azure**

---

## 1. Objetivo

O projeto identifica editais, financiamentos, eventos e parcerias relevantes para inovação tecnológica e mobilidade urbana. A solução:

1. consulta fontes oficiais de fomento (**FINEP** e **FAPESP** já integradas);
2. filtra oportunidades por data, situação e temas de interesse cadastrados;
3. utiliza o Google Gemini para estruturar e classificar os itens aderentes;
4. armazena os resultados em banco de dados PostgreSQL;
5. disponibiliza os dados em uma API FastAPI consumida pelo painel interativo em React;
6. integra-se com **n8n** para agendamento semanal e disparo de alertas de alta aderência.

---

## 2. Fontes de Dados Integradas

- **FINEP:** Coleta estruturada consumindo endpoint REST público de chamadas abertas e vigentes.
- **FAPESP:** Coleta automatizada via Web Scraping com suporte a paginação e extração de detalhes da chamada.
- *(Fontes planejadas para expansão: SENAI, CNPq, BNDES, Embrapii).*

---

## 3. Automação e Notificações (n8n)

Na arquitetura operacional do MVP, a rotina periódica é orquestrada via **n8n**:
- **Disparo Semanal:** O n8n aciona semanalmente a rotina do backend para coletar e processar novidades nas fontes configuradas.
- **Alerta de Alta Aderência:** Ao finalizar o processamento, o workflow identifica oportunidades com aderência **Alta**, compilando uma notificação automática (e-mail, Teams ou Slack) com:
  1. Lista numerada de oportunidades relevantes encontradas na rodada;
  2. Resumo da oportunidade, instituição fomentadora e prazo de submissão;
  3. **Link direto pré-filtrado** para a interface web com o filtro de aderência `Alta` ativo, permitindo acesso imediato aos editais prioritários.

---

## 4. Planejamento de Integração com Azure Corporativa

O MVP foi projetado de forma modular para suportar migração direta aos serviços corporativos da **Microsoft Azure**:
- **Hospedagem da API e Scrapers:** Migração para **Azure App Services** ou **Azure Container Apps**.
- **Persistência Corporativa:** Instância gerenciada no **Azure Database for PostgreSQL** com conexões privadas (Private Link/VNet).
- **Interface e Autenticação:** Hospedagem em **Azure Static Web Apps** integrada com Single Sign-On corporativo via **Microsoft Entra ID (Azure AD)**.
- **Automação Integrada:** Workflows corporativos em **Azure Logic Apps** ou n8n hospedado internamente.

---

## 5. Componentes Atuais do MVP

| Componente | Responsabilidade |
|---|---|
| `backend/scrapers/` | Módulos individuais de coleta por fonte (`finep.py`, `fapesp.py`) |
| `backend/pipeline.py` | Pipeline unificada de filtro temático, análise por IA e deduplicação |
| `backend/scraper_ai.py` | Ponto de entrada CLI para execução de coletas manuais ou via webhook |
| `backend/database.py` | Centraliza conexão e inicialização do PostgreSQL |
| `backend/main.py` | Expõe a API REST e o CRUD de temas |
| `frontend/` | Interface React para visualização, filtros rápidos e gestão de temas |
| PostgreSQL hospedado | Persiste oportunidades e temas |
| n8n (Orquestrador) | Gatilho semanal de busca e disparo de alertas de alta aderência |

---

## 6. Temas e Palavras-Chave

Os temas são armazenados na tabela `temas` e podem ser administrados pelo painel React. Eles possuem duas funções:

1. filtrar o conteúdo retornado pelas fontes antes da chamada ao Gemini (redução de custos e tempo);
2. orientar a classificação de aderência feita pela IA.

Temas de referência inicial:
- Mobilidade urbana e transporte sobre trilhos
- MaaS (Mobility as a Service)
- Hidrogênio verde e Energias renováveis
- Blockchain e Materiais avançados
- Indústria 4.0 e Inteligência Artificial

---

## 7. Dados Persistidos

### `oportunidades`

| Campo | Descrição |
|---|---|
| `id` | Identificador da oportunidade |
| `titulo` | Título do edital ou chamada |
| `instituicao` | Órgão responsável (FINEP, FAPESP, etc.) |
| `categoria` | `Edital`, `Evento`, `Curso` ou `Parceria` |
| `resumo` | Resumo executivo estruturado pela IA |
| `tematica` | Tema principal identificado |
| `prazo` | Prazo limite ou `Não informado` |
| `aderencia` | `Alto`, `Médio` ou `Baixo` |
| `link` | Link público oficial da oportunidade (com unicidade) |
| `data_coleta` | Data de inserção ou atualização |
| `descricaoRawText` | Texto bruto retido para consulta interna |

### `temas`

| Campo | Descrição |
|---|---|
| `id` | Identificador do tema |
| `nome` | Tema ou palavra-chave, com unicidade |
| `data_criacao` | Data de criação |

---

## 8. Regras Principais

- Itens antigos ou com prazos expirados são descartados antes do envio à IA.
- Itens sem correspondência com os temas ativos não consomem tokens do Gemini.
- A deduplicação por link impede redundância entre execuções semanais.
- O texto bruto permanece armazenado para consulta mesmo em caso de indisponibilidade da fonte externa.
