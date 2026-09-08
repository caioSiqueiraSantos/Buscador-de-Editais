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
    
    # Criar tabela de temas de interesse / palavras-chave
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS temas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        cursor.executemany("INSERT OR IGNORE INTO temas (nome) VALUES (?)", [(t,) for t in temas_iniciais])
        print("Temas iniciais cadastrados com sucesso!")

    conn.commit()
    conn.close()
    print("Banco de dados 'oportunidades.db' inicializado com sucesso!")

def obter_temas_db():
    """Retorna a lista de nomes de temas cadastrados no banco."""
    conn = sqlite3.connect('oportunidades.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM temas ORDER BY id ASC")
    temas = [row[0] for row in cursor.fetchall()]
    conn.close()
    return temas

if __name__ == "__main__":
    init_db()