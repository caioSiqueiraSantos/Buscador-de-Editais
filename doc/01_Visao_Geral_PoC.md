# Visão Geral do Projeto
**Nome do Projeto:** Buscador Automatizado de Oportunidades para Inovação
**Fase Atual:** Prova de Conceito (PoC)
**Setor:** Inovação - Companhia de Metrô

## 1. Objetivo
Desenvolver uma ferramenta automatizada capaz de prospectar editais, financiamentos, eventos e parcerias em fontes governamentais e de fomento. A solução utiliza Inteligência Artificial generativa para interpretar dados brutos de chamadas públicas, classificar o nível de aderência aos interesses estratégicos da companhia e disponibilizar essas oportunidades em um painel interativo.

*   **Fontes na PoC:**
    *   **FINEP (Ativa):** Coleta via endpoint REST público de chamadas abertas/recentes.
    *   **FAPESP e SENAI (Backlog/Próximos Passos):** Mapeadas para expansão futura após validação da PoC.

## 2. Natureza de "Prova de Conceito" (PoC)
Este projeto foi desenhado estritamente como uma PoC local. O foco é **validar a viabilidade técnica** (se a IA consegue extrair e classificar os dados corretamente) e **gerar valor imediato** para os usuários do setor.
*   **Restrições Atuais:** Execução apenas em máquina local (`localhost`), protocolo HTTP simples (sem TLS/HTTPS), sem infraestrutura em nuvem, sem CI/CD ou DevOps complexo no momento.
*   **Próximos Passos (Pós-PoC):** Migração para ambiente corporativo (ex: Google Cloud / Vertex AI), orquestração periódica de coleta (Airflow/Cloud Functions), implementação de webhooks/notificações (email/Teams), e raspagem em larga escala.

## 3. Temas de Interesse e Palavras-chave Dinâmicas
Diferente de listas estáticas no código, os temas estratégicos agora são **armazenados e gerenciados dinamicamente no banco de dados SQLite** (tabela `temas`) através de um CRUD no painel React. 
Eles desempenham duplo papel no ciclo de vida da informação:
1. **Filtro de Palavras-Chave:** O coletor analisa os campos brutos do edital antes de qualquer chamada externa. Caso nenhuma das palavras-chave ativas seja identificada, o conteúdo é descartado de imediato, economizando custos e tempo.
2. **Critérios de Aderência para IA:** Havendo correspondência, os temas ativos são injetados dinamicamente no prompt do Google Gemini para avaliar o nível de alinhamento (`Alto`, `Médio` ou `Baixo`).

A base é inicializada automaticamente (*seed*) com os seguintes temas estratégicos de referência:
*   Mobilidade urbana e transporte sobre trilhos
*   MaaS (Mobility as a Service)
*   Hidrogênio verde e Energias renováveis
*   Blockchain e Materiais avançados
*   Indústria 4.0 e Inteligência Artificial

## 4. Estrutura de Dados e Integridade
O sistema gerencia duas tabelas relacionais locais no SQLite:

### Tabela `oportunidades`
Armazena as oportunidades validadas e classificadas pela IA:

| Campo | Tipo / Regra | Descrição |
| :--- | :--- | :--- |
| `titulo` | `TEXT NOT NULL` | Título do edital ou chamada pública |
| `instituicao` | `TEXT` | Órgão responsável (ex: FINEP) |
| `categoria` | `TEXT` | Classificação estrita: `Edital`, `Evento`, `Curso` ou `Parceria` |
| `resumo` | `TEXT` | Síntese concisa de no máximo 3 linhas sobre a oportunidade |
| `tematica` | `TEXT` | Tema principal identificado na chamada |
| `prazo` | `TEXT` | Prazo limite de submissão (ou "Não informado") |
| `aderencia` | `TEXT` | Nível de alinhamento com os temas do Metrô: `Alto`, `Médio` ou `Baixo` |
| `link` | `TEXT UNIQUE` | URL de acesso à chamada pública (**chave de deduplicação**) |
| `data_coleta` | `TIMESTAMP` | Registro temporal gerado automaticamente pelo banco para ordenação |

### Tabela `temas`
Armazena os temas e palavras-chave gerenciáveis pelo usuário via CRUD:

| Campo | Tipo / Regra | Descrição |
| :--- | :--- | :--- |
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | Identificador único do tema |
| `nome` | `TEXT NOT NULL UNIQUE` | Nome ou palavra-chave de interesse estratégico |
| `data_criacao` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | Data e hora de inclusão do tema |

### Política de Deduplicação e Economia de Tokens
Para otimizar custos de consumo de API de IA e evitar redundâncias:
1. **Deduplicação Pré-IA:** O sistema verifica se o edital já existe no banco antes de solicitar o processamento semântico à IA.
2. **Pré-filtro de Palavras-Chave:** Descarta chamadas que não guardam correspondência lexical com nenhum tema ativo no banco.
3. **Deduplicação no Banco:** O campo `link` possui restrição `UNIQUE` e as inserções utilizam `INSERT OR IGNORE` como garantia de integridade transacional.

---
*Nota para IAs auxiliares: Este documento define o escopo de negócios. Limite as sugestões de novas features àquelas que respeitem as restrições da PoC.*
