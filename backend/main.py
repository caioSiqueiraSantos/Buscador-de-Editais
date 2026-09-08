# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import sqlite3
from typing import Optional

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

# Schemas Pydantic para Temas
class TemaSchema(BaseModel):
    nome: str = Field(..., min_length=1, description="Nome ou palavra-chave do tema de interesse")

@app.get("/oportunidades")
def listar_oportunidades():
    conn = get_db_connection()
    oportunidades = conn.execute('SELECT * FROM oportunidades ORDER BY data_coleta DESC').fetchall()
    conn.close()
    return [dict(ix) for ix in oportunidades]

# Endpoints CRUD para Temas / Palavras-chave
@app.get("/temas")
def listar_temas():
    conn = get_db_connection()
    temas = conn.execute('SELECT * FROM temas ORDER BY id ASC').fetchall()
    conn.close()
    return [dict(t) for t in temas]

@app.post("/temas", status_code=201)
def criar_tema(tema: TemaSchema):
    nome_limpo = tema.nome.strip()
    if not nome_limpo:
        raise HTTPException(status_code=400, detail="O nome do tema não pode ser vazio.")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO temas (nome) VALUES (?)", (nome_limpo,))
        novo_id = cursor.lastrowid
        conn.commit()
        novo_tema = conn.execute("SELECT * FROM temas WHERE id = ?", (novo_id,)).fetchone()
        return dict(novo_tema)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail=f"O tema '{nome_limpo}' já está cadastrado.")
    finally:
        conn.close()

@app.put("/temas/{tema_id}")
def atualizar_tema(tema_id: int, tema: TemaSchema):
    nome_limpo = tema.nome.strip()
    if not nome_limpo:
        raise HTTPException(status_code=400, detail="O nome do tema não pode ser vazio.")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        existente = cursor.execute("SELECT * FROM temas WHERE id = ?", (tema_id,)).fetchone()
        if not existente:
            raise HTTPException(status_code=404, detail="Tema não encontrado.")
        
        cursor.execute("UPDATE temas SET nome = ? WHERE id = ?", (nome_limpo, tema_id))
        conn.commit()
        atualizado = conn.execute("SELECT * FROM temas WHERE id = ?", (tema_id,)).fetchone()
        return dict(atualizado)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail=f"Já existe outro tema com o nome '{nome_limpo}'.")
    finally:
        conn.close()

@app.delete("/temas/{tema_id}")
def remover_tema(tema_id: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        existente = cursor.execute("SELECT * FROM temas WHERE id = ?", (tema_id,)).fetchone()
        if not existente:
            raise HTTPException(status_code=404, detail="Tema não encontrado.")
        
        cursor.execute("DELETE FROM temas WHERE id = ?", (tema_id,))
        conn.commit()
        return {"message": "Tema removido com sucesso", "id": tema_id}
    finally:
        conn.close()