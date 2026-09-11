# backend/main.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import psycopg
from psycopg.rows import dict_row
from psycopg.errors import UniqueViolation
from typing import Optional
from database import get_db_url

app = FastAPI(title="API Inovação Metrô")

# Configuração de CORS para permitir que o React consuma a API
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins = [frontend_url]
else:
    # Fallback para desenvolvimento local
    origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    url = get_db_url()
    return psycopg.connect(url, row_factory=dict_row)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API está no ar."}

# Schemas Pydantic para Temas
class TemaSchema(BaseModel):
    nome: str = Field(..., min_length=1, description="Nome ou palavra-chave do tema de interesse")

@app.get("/oportunidades")
def listar_oportunidades():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM oportunidades ORDER BY data_coleta DESC')
        oportunidades = cursor.fetchall()
        return oportunidades
    finally:
        conn.close()

# Endpoints CRUD para Temas / Palavras-chave
@app.get("/temas")
def listar_temas():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM temas ORDER BY id ASC')
        temas = cursor.fetchall()
        return temas
    finally:
        conn.close()

@app.post("/temas", status_code=201)
def criar_tema(tema: TemaSchema):
    nome_limpo = tema.nome.strip()
    if not nome_limpo:
        raise HTTPException(status_code=400, detail="O nome do tema não pode ser vazio.")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO temas (nome) VALUES (%s) RETURNING id, nome, data_criacao", (nome_limpo,))
        novo_tema = cursor.fetchone()
        conn.commit()
        return novo_tema
    except UniqueViolation:
        conn.rollback()
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
        cursor.execute("SELECT * FROM temas WHERE id = %s", (tema_id,))
        existente = cursor.fetchone()
        if not existente:
            raise HTTPException(status_code=404, detail="Tema não encontrado.")
        
        cursor.execute("UPDATE temas SET nome = %s WHERE id = %s RETURNING id, nome, data_criacao", (nome_limpo, tema_id))
        atualizado = cursor.fetchone()
        conn.commit()
        return atualizado
    except UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Já existe outro tema com o nome '{nome_limpo}'.")
    finally:
        conn.close()

@app.delete("/temas/{tema_id}")
def remover_tema(tema_id: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM temas WHERE id = %s", (tema_id,))
        existente = cursor.fetchone()
        if not existente:
            raise HTTPException(status_code=404, detail="Tema não encontrado.")
        
        cursor.execute("DELETE FROM temas WHERE id = %s", (tema_id,))
        conn.commit()
        return {"message": "Tema removido com sucesso", "id": tema_id}
    finally:
        conn.close()