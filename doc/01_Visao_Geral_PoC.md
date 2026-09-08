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

## 3. Temas de Interesse (Critérios de Aderência)
A IA foi instruída a classificar as oportunidades com base nos seguintes temas estratégicos:
*   Mobilidade urbana e transporte sobre trilhos
*   MaaS (Mobility as a Service)
*   Hidrogênio verde e Energias renováveis
*   Blockchain e Materiais avançados
*   Indústria 4.0 e Inteligência Artificial

## 4. Estrutura de Dados e Integridade
Para cada oportunidade, o sistema garante a extração, validação com Pydantic e persistência dos seguintes campos estruturados:

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

### Política de Deduplicação
Para otimizar custos de consumo de API de IA e evitar redundâncias:
1. **Deduplicação Pré-IA:** O sistema verifica se o edital já existe no banco antes de solicitar o processamento semântico à IA.
2. **Deduplicação no Banco:** O campo `link` possui restrição `UNIQUE` e as inserções utilizam `INSERT OR IGNORE` como garantia de integridade transacional.

---
*Nota para IAs auxiliares: Este documento define o escopo de negócios. Limite as sugestões de novas features àquelas que respeitem as restrições da PoC.*
