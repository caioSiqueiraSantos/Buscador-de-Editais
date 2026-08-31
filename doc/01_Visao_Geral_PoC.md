# Visão Geral do Projeto
**Nome do Projeto:** Buscador Automatizado de Oportunidades para Inovação
**Fase Atual:** Prova de Conceito (PoC)
**Setor:** Inovação - Companhia de Metrô

## 1. Objetivo
Desenvolver uma ferramenta automatizada capaz de prospectar editais, financiamentos, eventos e parcerias em sites governamentais e de fomento (ex: FAPESP, SENAI, FINEP). A solução utiliza Inteligência Artificial para ler textos brutos, classificar o nível de aderência aos interesses estratégicos da companhia e disponibilizar essas oportunidades em um painel interativo.

## 2. Natureza de "Prova de Conceito" (PoC)
Este projeto foi desenhado estritamente como uma PoC local. O foco é **validar a viabilidade técnica** (se a IA consegue extrair e classificar os dados corretamente) e **gerar valor imediato** para os usuários do setor.
*   **Restrições Atuais:** Execução apenas em máquina local (`localhost`), sem infraestrutura em nuvem, sem CI/CD ou DevOps complexo no momento.
*   **Próximos Passos (Pós-PoC):** Migração para ambiente corporativo (ex: Google Cloud / Vertex AI), implementação de webhooks/notificações (email/Teams), e raspagem em larga escala.

## 3. Temas de Interesse (Critérios de Aderência)
A IA foi instruída a classificar as oportunidades com base nos seguintes temas estratégicos:
*   Mobilidade urbana e transporte sobre trilhos
*   MaaS (Mobility as a Service)
*   Hidrogênio verde e Energias renováveis
*   Blockchain e Materiais avançados
*   Indústria 4.0 e Inteligência Artificial

## 4. Estrutura de Dados Extraída
Para cada oportunidade, o sistema deve garantir a extração/geração dos seguintes campos em formato estruturado (JSON):
`titulo`, `instituicao`, `categoria` (Edital/Evento/Curso/Parceria), `resumo` (máx. 3 linhas), `tematica`, `prazo`, `aderencia` (Alto/Médio/Baixo) e `link`.

---
*Nota para IAs auxiliares: Este documento define o escopo de negócios. Limite as sugestões de novas features àquelas que respeitem as restrições da PoC.*
