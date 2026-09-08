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
            link TEXT UNIQUE,
            data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Garantir compatibilidade caso a tabela já tenha sido criada sem a coluna data_coleta
    cursor.execute("PRAGMA table_info(oportunidades)")
    colunas = [info[1] for info in cursor.fetchall()]
    if 'data_coleta' not in colunas:
        cursor.execute("ALTER TABLE oportunidades ADD COLUMN data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

    # Garantir índice único para deduplicação mesmo em bancos criados anteriormente
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_oportunidades_link ON oportunidades(link)")
    
    conn.commit()
    conn.close()
    print("Banco de dados 'oportunidades.db' inicializado com sucesso!")

if __name__ == "__main__":
    init_db()