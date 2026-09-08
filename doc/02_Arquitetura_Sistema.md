# Arquitetura do Sistema (PoC)

Este documento detalha a stack tecnológica, a organização estrutural do projeto e as decisões arquiteturais da Prova de Conceito (PoC).

## 1. Stack Tecnológica
*   **Ingestão de Dados:** Python com `requests` para consumo direto de APIs REST públicas/ocultas (JSON). *Nota: `beautifulsoup4` permanece instalado como ferramenta de fallback para páginas que não oferecem endpoints de dados estruturados.*
*   **Motor de IA:** Google Gemini API via novo SDK oficial (`google-genai`), modelo **`gemini-3.5-flash-lite`**, com validação estrita de esquema estruturado via **`Pydantic`** (`types.GenerateContentConfig(response_schema=Oportunidade)`).
*   **Backend (API):** Python com `FastAPI` e servidor ASGI `Uvicorn` para servir os dados na porta `8000`.
*   **Banco de Dados:** `SQLite` (arquivo local `oportunidades.db`) com operações SQL diretas via `sqlite3`.
*   **Frontend:** Single Page Application (SPA) com `React`, empacotada via `Vite` (porta `5173`).
*   **Estilização:** `Tailwind CSS` (via PostCSS) com tema escuro e elementos visuais no padrão do Metrô.

## 2. Estrutura de Diretórios
```text
Buscador-de-Editais/
├── .gitignore                   
├── backend/
│   ├── .env                     # Chaves de API (ex: GEMINI_API_KEY)
│   ├── database.py              # Inicialização e migração do SQLite (schema centralizado)
│   ├── scraper_ai.py            # Script de ingestão, análise via Gemini e persistência
│   ├── main.py                  # API REST FastAPI (endpoints para o frontend)
│   ├── oportunidades.db         # Banco de dados SQLite local
│   ├── requirements.txt         # Dependências do backend Python
│   └── venv/                    # Ambiente virtual Python
├── doc/
│   ├── 01_Visao_Geral_PoC.md
│   ├── 02_Arquitetura_Sistema.md
│   └── 03_Fluxo_de_Dados.md
└── frontend/
    ├── package.json             
    ├── tailwind.config.js       
    ├── postcss.config.js        
    ├── index.html               
    ├── vite.config.js
    └── src/
        ├── App.jsx              # Interface principal com busca e filtros dinâmicos
        ├── App.css
        └── index.css            
```

## 3. Decisões Arquiteturais e Boas Práticas

*   **Separação entre Ingestão (Batch) e API (Serving):**
    *   `scraper_ai.py` funciona como um processo de coleta e processamento em lote (*batch*), executado sob demanda ou agendamento via terminal (`python scraper_ai.py`).
    *   `main.py` atua exclusivamente como servidor de leitura (`SELECT`) para o frontend, mantendo alta performance e isolamento de falhas.
*   **Deduplicação em Duas Camadas:**
    1.  *Camada de Negócio / Aplicação:* Verificação prévia no SQLite do link estimado da chamada antes de acionar a IA, economizando 100% dos tokens de chamadas repetidas.
    2.  *Camada de Persistência:* Restrição `link TEXT UNIQUE` e uso de `INSERT OR IGNORE` para integridade transacional contra concorrência ou links equivalentes.
*   **Ambiente e Protocolo de Execução Local:**
    *   O Uvicorn executa em **HTTP puro** (`http://127.0.0.1:8000`). Não há certificado SSL configurado localmente; portanto, tentativas de acesso com `https://` resultarão em falha de conexão (`ERR_SSL_PROTOCOL_ERROR`).
    *   A documentação interativa da API está disponível via Swagger UI em `http://127.0.0.1:8000/docs`.
*   **CORS (Cross-Origin Resource Sharing):** Habilitado no FastAPI com `allow_origins=["*"]` para permitir que o Vite (`http://localhost:5173`) consuma a API sem bloqueios no navegador.

---
*Nota para IAs auxiliares: Ao sugerir códigos, respeite a stack atual. Mantenha a simplicidade da PoC, priorizando o SQLite e evitando ORMs pesados.*
