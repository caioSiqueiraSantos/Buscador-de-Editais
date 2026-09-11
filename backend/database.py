# backend/database.py
import psycopg
from psycopg.rows import dict_row
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_url():
    url = os.getenv('DATABASE_URL')
    if not url:
        raise ValueError("Variável de ambiente DATABASE_URL não configurada.")
    return url

def init_db():
    url = get_db_url()
    conn = psycopg.connect(url)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS oportunidades (
            id SERIAL PRIMARY KEY,
            titulo TEXT NOT NULL,
            instituicao TEXT,
            categoria TEXT,
            resumo TEXT,
            tematica TEXT,
            prazo TEXT,
            aderencia TEXT,
            link TEXT UNIQUE,
            data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            descricaoRawText TEXT
        )
    ''')

    # Garantir índice único para deduplicação mesmo em bancos criados anteriormente
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_oportunidades_link ON oportunidades(link)")
    
    # Criar tabela de temas de interesse / palavras-chave
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS temas (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL UNIQUE,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Seed inicial de temas padrão da PoC caso a tabela esteja vazia
    cursor.execute("SELECT COUNT(*) FROM temas")
    if cursor.fetchone()[0] == 0:
        temas_iniciais = [
            "Mobilidade urbana e transporte sobre trilhos",
            "MaaS (Mobility as a Service)",
            "Hidrogênio verde e Energias renováveis",
            "Blockchain e Materiais avançados",
            "Indústria 4.0 e Inteligência Artificial"
        ]
        cursor.executemany("INSERT INTO temas (nome) VALUES (%s) ON CONFLICT (nome) DO NOTHING", [(t,) for t in temas_iniciais])
        print("Temas iniciais cadastrados com sucesso!")

    conn.commit()
    conn.close()
    print("Banco de dados PostgreSQL inicializado com sucesso!")

def obter_temas_db():
    """Retorna a lista de nomes de temas cadastrados no banco."""
    url = get_db_url()
    conn = psycopg.connect(url)
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM temas ORDER BY id ASC")
    temas = [row[0] for row in cursor.fetchall()]
    conn.close()
    return temas

if __name__ == "__main__":
    init_db()