# backend/database.py
import os
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

def get_db_url() -> str:
    load_dotenv(override=True)
    return os.getenv('DATABASE_URL', '')

def is_postgres() -> bool:
    url = get_db_url()
    return url.startswith('postgres://') or url.startswith('postgresql://')

class DBConnection:
    """
    Abstração resiliente que suporta tanto PostgreSQL (psycopg em produção/cloud)
    quanto SQLite (desenvolvimento local com zero-config).
    """
    def __init__(self):
        self.is_pg = is_postgres()
        if self.is_pg:
            import psycopg
            from psycopg.rows import dict_row
            self.conn = psycopg.connect(get_db_url(), row_factory=dict_row)
        else:
            db_path = os.path.join(os.path.dirname(__file__), 'editais.db')
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row

    def cursor(self):
        return DBCursor(self.conn.cursor(), self.is_pg)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

class DBCursor:
    """
    Cursor unificado que adapta consultas parametrizadas (%s -> ?) quando usando SQLite
    e padroniza o retorno como dicionários legíveis.
    """
    def __init__(self, cursor, is_pg: bool):
        self.cursor = cursor
        self.is_pg = is_pg

    def execute(self, query: str, params=None):
        if not self.is_pg:
            adapted_query = query.replace('%s', '?')
            if params is None:
                return self.cursor.execute(adapted_query)
            return self.cursor.execute(adapted_query, params)
        else:
            if params is None:
                return self.cursor.execute(query)
            return self.cursor.execute(query, params)

    def executemany(self, query: str, seq_of_params):
        if not self.is_pg:
            adapted_query = query.replace('%s', '?')
            return self.cursor.executemany(adapted_query, seq_of_params)
        else:
            return self.cursor.executemany(query, seq_of_params)

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        if not self.is_pg and isinstance(row, sqlite3.Row):
            return dict(row)
        if isinstance(row, dict):
            return row
        return row

    def fetchall(self):
        rows = self.cursor.fetchall()
        if not self.is_pg:
            return [dict(r) if isinstance(r, sqlite3.Row) else r for r in rows]
        return rows

def get_db_connection() -> DBConnection:
    return DBConnection()

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if is_postgres():
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
                justificativa_ia TEXT,
                aderencia_humana TEXT,
                status_revisao TEXT DEFAULT 'pendente',
                motivo_feedback TEXT,
                excluido BOOLEAN DEFAULT FALSE,
                data_feedback TIMESTAMP,
                link TEXT UNIQUE,
                data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                descricaoRawText TEXT
            )
        ''')
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_oportunidades_link ON oportunidades(link)")
        
        # Migração idempotente para tabelas criadas em versões anteriores
        colunas_migracao = [
            ("justificativa_ia", "TEXT"),
            ("aderencia_humana", "TEXT"),
            ("status_revisao", "TEXT DEFAULT 'pendente'"),
            ("motivo_feedback", "TEXT"),
            ("excluido", "BOOLEAN DEFAULT FALSE"),
            ("data_feedback", "TIMESTAMP")
        ]
        for col, tipo in colunas_migracao:
            cursor.execute(f"ALTER TABLE oportunidades ADD COLUMN IF NOT EXISTS {col} {tipo}")
            
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS temas (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL UNIQUE,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        # SQLite
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
                justificativa_ia TEXT,
                aderencia_humana TEXT,
                status_revisao TEXT DEFAULT 'pendente',
                motivo_feedback TEXT,
                excluido BOOLEAN DEFAULT 0,
                data_feedback TIMESTAMP,
                link TEXT UNIQUE,
                data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                descricaoRawText TEXT
            )
        ''')
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_oportunidades_link ON oportunidades(link)")
        
        # Migração idempotente no SQLite via inspeção de colunas existentes
        cursor.execute("PRAGMA table_info(oportunidades)")
        colunas_existentes = {row['name'] if isinstance(row, dict) else row[1] for row in cursor.fetchall()}
        colunas_migracao = [
            ("justificativa_ia", "TEXT"),
            ("aderencia_humana", "TEXT"),
            ("status_revisao", "TEXT DEFAULT 'pendente'"),
            ("motivo_feedback", "TEXT"),
            ("excluido", "BOOLEAN DEFAULT 0"),
            ("data_feedback", "TIMESTAMP")
        ]
        for col, tipo in colunas_migracao:
            if col not in colunas_existentes:
                cursor.execute(f"ALTER TABLE oportunidades ADD COLUMN {col} {tipo}")
                
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS temas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

    # Seed inicial de temas padrão caso esteja vazio
    cursor.execute("SELECT COUNT(*) as count FROM temas")
    res = cursor.fetchone()
    count_temas = res['count'] if isinstance(res, dict) else res[0]
    
    if count_temas == 0:
        temas_iniciais = [
            "Mobilidade urbana e transporte sobre trilhos",
            "MaaS (Mobility as a Service)",
            "Hidrogênio verde e Energias renováveis",
            "Blockchain e Materiais avançados",
            "Indústria 4.0 e Inteligência Artificial"
        ]
        if is_postgres():
            cursor.executemany("INSERT INTO temas (nome) VALUES (%s) ON CONFLICT (nome) DO NOTHING", [(t,) for t in temas_iniciais])
        else:
            cursor.executemany("INSERT INTO temas (nome) VALUES (%s)", [(t,) for t in temas_iniciais])
        print("Temas iniciais cadastrados com sucesso!")

    # Seed de demonstração para o protótipo caso a tabela de oportunidades esteja vazia
    cursor.execute("SELECT COUNT(*) as count FROM oportunidades")
    res_op = cursor.fetchone()
    count_ops = res_op['count'] if isinstance(res_op, dict) else res_op[0]
    
    if count_ops == 0:
        seed_editais = [
            (
                "Finep Mais Inovação - Mobilidade Sustentável e Sistemas Ferroviários",
                "FINEP",
                "Edital",
                "Apoio a projetos de inovação voltados à eletrificação, sinalização inteligente e materiais avançados para malha sobre trilhos.",
                "Mobilidade urbana e transporte sobre trilhos",
                "15/12/2026",
                "Alto",
                "Foco direto em sistemas de tração e infraestrutura metroviária de alta capacidade.",
                None,
                "pendente",
                None,
                False,
                "https://www.finep.gov.br/chamadas-publicas/chamadapublica/mobilidade-trilhos-2026",
                "Texto completo da chamada pública da Finep com foco em infraestrutura ferroviária e metroviária..."
            ),
            (
                "Chamada Pública Finep/MCTI - Inteligência Artificial para Cidades Inteligentes e MaaS",
                "FINEP",
                "Edital",
                "Desenvolvimento de plataformas integradas de bilhetagem unificada, roteirização multimodal e gestão de fluxo de passageiros.",
                "MaaS (Mobility as a Service)",
                "30/11/2026",
                "Alto",
                "Convergência com bilhetagem digital e integração intermodal do sistema metroviário.",
                "Alto",
                "aprovado",
                "Tema estratégico para a bilhetagem e experiência do passageiro no Metrô.",
                False,
                "https://www.finep.gov.br/chamadas-publicas/chamadapublica/ia-maas-cidades-2026",
                "Edital voltado para mobilidade como serviço e conectividade urbana..."
            ),
            (
                "Edital FINEP - Biocombustíveis e Descarbonização no Transporte Rodoviário de Cargas",
                "FINEP",
                "Edital",
                "Subvenção para motores a biodiesel e logística para carretas de grãos no agronegócio.",
                "Divergente / Não aderente",
                "20/10/2026",
                "Baixo",
                "Recusado pela IA: Foco em frotas rodoviárias para transporte de grãos no agronegócio, sem aderência ao escopo do Metrô/NIT.",
                None,
                "descartado",
                "Recusado pela IA: Foco em agronegócio e frete rodoviário de grãos.",
                True,
                "https://www.finep.gov.br/chamadas-publicas/chamadapublica/agro-cargas-2026",
                "Edital voltado exclusivamente a frotas pesadas rodoviárias e transporte de soja no Centro-Oeste..."
            )
        ]
        
        insert_query = '''
            INSERT INTO oportunidades (
                titulo, instituicao, categoria, resumo, tematica, prazo,
                aderencia, justificativa_ia, aderencia_humana, status_revisao,
                motivo_feedback, excluido, link, descricaoRawText
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        for edital in seed_editais:
            try:
                cursor.execute(insert_query, edital)
            except Exception as e:
                pass
        print("Seed de demonstração de oportunidades aplicado com sucesso!")

    conn.commit()
    conn.close()
    db_tipo = "PostgreSQL" if is_postgres() else "SQLite local"
    print(f"Banco de dados ({db_tipo}) inicializado com sucesso!")

def obter_temas_db() -> List[str]:
    """Retorna a lista de nomes de temas cadastrados no banco."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM temas ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [row['nome'] if isinstance(row, dict) else row[0] for row in rows]

def obter_exemplos_aprendizado(limite: int = 4) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Recupera os feedbacks humanos mais recentes para calibrar o prompt da IA:
    - Exemplos Positivos/Ajustados: editais que o usuário validou ou subiu aderência.
    - Exemplos Negativos/Falsos Positivos: editais que o usuário descartou/excluiu com motivo.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Editais aprovados ou com aderência ajustada pelo humano (Exemplos Positivos)
    cursor.execute('''
        SELECT id, titulo, tematica, COALESCE(aderencia_humana, aderencia) as aderencia_final, motivo_feedback, resumo
        FROM oportunidades
        WHERE status_revisao IN ('aprovado', 'ajustado') AND excluido IS NOT TRUE
        ORDER BY data_feedback DESC
        LIMIT %s
    ''', (limite,))
    positivos = cursor.fetchall()
    
    # 2. Editais descartados / excluídos como falsos positivos (Exemplos Negativos)
    cursor.execute('''
        SELECT id, titulo, tematica, motivo_feedback, resumo
        FROM oportunidades
        WHERE status_revisao = 'descartado' OR excluido IS TRUE
        ORDER BY data_feedback DESC
        LIMIT %s
    ''', (limite,))
    negativos = cursor.fetchall()
    
    conn.close()
    return positivos, negativos

if __name__ == "__main__":
    init_db()