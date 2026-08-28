# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

app = FastAPI(title="API Inovação Metrô")

# Configuração de CORS para permitir que o React (localhost:5173) consuma a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Na PoC usamos "*", em prod defina o domínio correto
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    conn = sqlite3.connect('oportunidades.db')
    conn.row_factory = sqlite3.Row # Retorna os resultados como dicionários
    return conn

@app.get("/oportunidades")
def listar_oportunidades():
    conn = get_db_connection()
    oportunidades = conn.execute('SELECT * FROM oportunidades ORDER BY data_coleta DESC').fetchall()
    conn.close()
    return [dict(ix) for ix in oportunidades]