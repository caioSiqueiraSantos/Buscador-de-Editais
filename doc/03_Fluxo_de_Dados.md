# Fluxo de Dados e Processamento

Este documento descreve o ciclo de vida da informação, desde a origem (sites de fomento) até a tela do usuário.

## 1. Ingestão (Web Scraping)
1.  O script `scraper_ai.py` é executado.
2.  A biblioteca `requests` faz chamadas HTTP GET para os sites-alvo (ex: páginas específicas de editais da FAPESP ou FINEP).
3.  O `BeautifulSoup` limpa o HTML, extraindo apenas o texto visível da página (limitado a ~4000 caracteres para otimizar tokens).

## 2. Processamento Semântico (IA)
1.  O texto bruto extraído, junto com o link original e um *System Prompt* rigoroso contendo as regras de negócio do Metrô, é enviado para a API do Google Gemini.
2.  A API processa o conteúdo, cruza com os critérios de "Temas de Interesse" e devolve uma resposta estritamente estruturada em JSON (usando `response_mime_type="application/json"`).

## 3. Persistência (Banco de Dados)
1.  O Python intercepta o JSON gerado pelo Gemini.
2.  Os dados são mapeados e inseridos via comando `INSERT INTO` na tabela `oportunidades` do `oportunidades.db` (SQLite).
3.  Um *timestamp* (`data_coleta`) é gerado automaticamente pelo banco para controle cronológico.

## 4. Distribuição (API REST)
1.  O servidor `FastAPI` (rodando via `main.py`) fica escutando requisições na porta 8000.
2.  Quando a rota `GET /oportunidades` é acionada, o sistema executa um `SELECT * FROM oportunidades ORDER BY data_coleta DESC`.
3.  Os dados são serializados em um array de objetos JSON e devolvidos ao cliente.

## 5. Consumo e Visualização (Frontend React)
1.  O usuário abre a aplicação React no navegador (`localhost:5173`).
2.  O hook `useEffect` no componente `App.jsx` faz um `fetch` para a API local.
3.  O estado `oportunidades` é populado com os dados.
4.  O sistema renderiza os "Cards" dinâmicos com estilização condicional (ex: cores diferentes para níveis de aderência).
5.  O usuário pode usar o *input* de busca para filtrar instantaneamente (Client-side filtering) os dados carregados usando JavaScript nativo.

## Diagrama Lógico Simplificado
`Sites de Fomento` -> `BeautifulSoup (Texto Bruto)` -> `Gemini API (JSON Estruturado)` -> `SQLite (Persistência)` -> `FastAPI (Endpoint)` -> `React (Visualização)`
