# Visão Geral do Projeto

**Nome:** Buscador Automatizado de Oportunidades para Inovação
**Fase:** Prova de Conceito (PoC)
**Área:** Inovação - Companhia de Metrô

## 1. Objetivo

O projeto identifica editais, financiamentos, eventos e parcerias relevantes para inovação. A solução:

1. consulta a API pública da FINEP;
2. filtra oportunidades por data, situação e temas de interesse;
3. utiliza o Google Gemini para estruturar e classificar os itens aderentes;
4. armazena os resultados em PostgreSQL;
5. disponibiliza os dados em uma API FastAPI consumida pelo painel React.

Na PoC, a FINEP é a fonte ativa. FAPESP, SENAI e outras fontes permanecem como possibilidades futuras.

## 2. Componentes

| Componente | Responsabilidade |
|---|---|
| `backend/scraper_ai.py` | Executa a coleta e o processamento em lote pelo terminal |
| `backend/database.py` | Centraliza conexão e inicialização do PostgreSQL |
| `backend/main.py` | Expõe a API REST e o CRUD de temas |
| `frontend/` | Exibe oportunidades e permite gerenciar temas |
| PostgreSQL hospedado | Persiste oportunidades e temas |

O scraper continua sendo executado manualmente. Ele e a API utilizam o mesmo banco PostgreSQL hospedado, permitindo que os dados inseridos pelo terminal apareçam na interface publicada.

## 3. Temas e palavras-chave

Os temas são armazenados na tabela `temas` e podem ser administrados pelo painel React. Eles possuem duas funções:

1. filtrar o conteúdo retornado pela FINEP antes da chamada ao Gemini;
2. orientar a classificação de aderência feita pela IA.

Quando a tabela é inicializada sem registros, são cadastrados estes temas de referência:

- Mobilidade urbana e transporte sobre trilhos
- MaaS (Mobility as a Service)
- Hidrogênio verde e Energias renováveis
- Blockchain e Materiais avançados
- Indústria 4.0 e Inteligência Artificial

## 4. Dados persistidos

### `oportunidades`

| Campo | Descrição |
|---|---|
| `id` | Identificador da oportunidade |
| `titulo` | Título do edital ou chamada |
| `instituicao` | Órgão responsável |
| `categoria` | `Edital`, `Evento`, `Curso` ou `Parceria` |
| `resumo` | Resumo de até três linhas |
| `tematica` | Tema principal identificado |
| `prazo` | Prazo limite ou `Não informado` |
| `aderencia` | `Alto`, `Médio` ou `Baixo` |
| `link` | Link público da oportunidade, com unicidade |
| `data_coleta` | Data de inserção ou atualização |
| `descricaoRawText` | Texto bruto retido para consulta interna |

### `temas`

| Campo | Descrição |
|---|---|
| `id` | Identificador do tema |
| `nome` | Tema ou palavra-chave, com unicidade |
| `data_criacao` | Data de criação |

## 5. Regras principais

- Itens antigos ou encerrados são descartados antes do processamento com IA.
- Itens sem correspondência com os temas ativos não são enviados ao Gemini.
- O link e o título são usados na deduplicação.
- O texto bruto é mantido para que a interface não dependa da disponibilidade futura da página de origem.
- A unicidade do link no PostgreSQL protege a integridade dos dados.

## 6. Limites atuais da PoC

- A coleta continua sob demanda, pelo terminal.
- Apenas a FINEP está integrada.
- Não há autenticação de usuários ou controle de permissões.
- O envio de notificações e a execução automática periódica ficam para uma etapa futura.
