# Arquitetura do Sistema (PoC)

Este documento detalha a stack tecnológica e a organização estrutural do projeto. A arquitetura foi pensada para ser modular, facilitando a substituição de componentes no futuro (ex: trocar SQLite por PostgreSQL).

## 1. Stack Tecnológica
*   **Web Scraping:** Python (`requests`, `BeautifulSoup4`).
*   **Motor de IA:** Google Gemini API (modelo `gemini-1.5-flash`), com forçamento de saída em JSON.
*   **Backend (API):** Python com `FastAPI` e `Uvicorn` para servir os dados.
*   **Banco de Dados:** `SQLite` (arquivo local `.db`) interagindo via raw SQL/`sqlite3`.
*   **Frontend:** Single Page Application (SPA) com `React`, empacotada via `Vite`.
*   **Estilização:** `Tailwind CSS` (via PostCSS).

## 2. Estrutura de Diretórios
```text
Buscador-de-Editais/
├── .gitignore                   
├── backend/
│   ├── .env                     
│   ├── database.py              
│   ├── scraper_ai.py            
│   ├── main.py                  
│   └── oportunidades.db         
└── frontend/
    ├── package.json             
    ├── tailwind.config.js       
    ├── postcss.config.js        
    ├── index.html               
    └── src/
        ├── App.jsx              
        └── index.css            
```

## 3. Decisões Arquiteturais
*   **Desacoplamento:** Backend e Frontend rodam em portas separadas (`8000` e `5173`). O backend apenas serve JSON via API REST, permitindo que o frontend seja totalmente independente.
*   **CORS (Cross-Origin Resource Sharing):** Habilitado no FastAPI com `allow_origins=["*"]` para garantir fluidez no ambiente local de desenvolvimento.

---
*Nota para IAs auxiliares: Ao sugerir códigos, respeite a stack atual. Não introduza bibliotecas como SQLAlchemy, Next.js ou Redux sem requisição explícita, mantendo a simplicidade da PoC.*
