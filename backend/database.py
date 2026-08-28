# backend/database.py
import sqlite3

def init_db():
    conn = sqlite3.connect('oportunidades.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS oportunidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            instituicao TEXT,
            categoria TEXT,
            resumo TEXT,
            tematica TEXT,
            prazo TEXT,
            aderencia TEXT,
            link TEXT,
            data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Banco de dados 'oportunidades.db' inicializado com sucesso!")

if __name__ == "__main__":
    init_db()