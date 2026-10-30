# backend/main.py
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Header, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from database import get_db_connection, is_postgres, obter_exemplos_aprendizado, init_db
from pipeline import executar_pipeline_completa

app = FastAPI(
    title="API Inovação Metrô - Buscador de Editais",
    description="Backend com suporte a Human-in-the-Loop Feedback Engine, Active Learning e Orquestração n8n",
    version="2.1.0"
)

# Inicializa o banco (tabelas e migrações idempotentes)
init_db()

# Configuração de CORS para permitir acesso local e em produção
frontend_url = os.getenv("FRONTEND_URL")
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
if frontend_url and frontend_url not in origins:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite consumo flexível em ambiente de desenvolvimento e produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== SEGURANÇA E AUTENTICAÇÃO ====================

def verificar_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    api_key: Optional[str] = Query(None)
):
    """
    Valida a chave de autenticação para endpoints protegidos (ex: n8n Webhooks).
    Se PIPELINE_API_KEY estiver definida no .env, a requisição deve conter o token correspondente.
    """
    chave_esperada = os.getenv("PIPELINE_API_KEY")
    if chave_esperada:
        token_fornecido = x_api_key or api_key
        if not token_fornecido or token_fornecido.strip() != chave_esperada.strip():
            raise HTTPException(
                status_code=401,
                detail="Acesso não autorizado: chave de API inválida ou ausente no cabeçalho 'X-API-Key'."
            )
    return True

# ==================== SCHEMAS PYDANTIC ====================

class TemaSchema(BaseModel):
    nome: str = Field(..., min_length=1, description="Nome ou palavra-chave do tema de interesse")

class AderenciaUpdateSchema(BaseModel):
    aderencia: str = Field(..., description="Novo nível de aderência calibrado pelo humano: Alto, Médio, Baixo")
    motivo: Optional[str] = Field(None, description="Motivo ou observação da calibração para treinar a IA")

class DescarteSchema(BaseModel):
    motivo: Optional[str] = Field("Fora do escopo do Metrô", description="Motivo do descarte / falso positivo para treinar a IA")

class ExecucaoPipelineSchema(BaseModel):
    fontes: Optional[List[str]] = Field(None, description="Fontes específicas para coletar (ex: ['finep', 'fapesp']). Se omitido, executa todas.")
    limite_por_fonte: Optional[int] = Field(None, description="Limite máximo opcional de itens a processar por fonte.")
    assincrono: Optional[bool] = Field(False, description="Se True, executa em background task e retorna confirmação imediata.")

# ==================== ENDPOINTS DE MONITORAMENTO E SAÚDE ====================

@app.get("/health")
def health_check():
    db_mode = "PostgreSQL" if is_postgres() else "SQLite local"
    tem_auth = bool(os.getenv("PIPELINE_API_KEY"))
    return {
        "status": "ok",
        "message": "API está ativa.",
        "database": db_mode,
        "n8n_auth_enabled": tem_auth
    }

# ==================== ORQUESTRAÇÃO DE PIPELINE (N8N) ====================

@app.post("/pipeline/executar")
def trigger_pipeline(
    payload: Optional[ExecucaoPipelineSchema] = None,
    background_tasks: BackgroundTasks = None,
    auth: bool = Depends(verificar_api_key)
):
    """
    Endpoint principal acionado pelo n8n (Cron Semanal ou Disparo Manual).
    Executa a esteira completa: scrapers, filtros temáticos, análise Gemini e deduplicação.
    Retorna o resumo com as oportunidades de alta aderência prontas para alertas.
    """
    fontes = payload.fontes if payload else None
    limite = payload.limite_por_fonte if payload else None
    assincrono = payload.assincrono if payload else False

    if assincrono and background_tasks is not None:
        background_tasks.add_task(
            executar_pipeline_completa,
            fontes_selecionadas=fontes,
            limite_por_fonte=limite
        )
        return {
            "status": "iniciado_em_segundo_plano",
            "mensagem": "A pipeline de coleta foi iniciada como tarefa em segundo plano.",
            "data_inicio": datetime.now().isoformat()
        }

    # Execução síncrona: aguarda e retorna o relatório consolidado
    resultado = executar_pipeline_completa(
        fontes_selecionadas=fontes,
        limite_por_fonte=limite
    )
    return resultado

@app.get("/pipeline/alta-aderencia")
def listar_oportunidades_alta_aderencia(
    dias: int = Query(7, ge=1, le=90, description="Buscar editais dos últimos X dias"),
    auth: bool = Depends(verificar_api_key)
):
    """
    Permite ao n8n consultar os editais com Alta Aderência mais recentes
    sem a necessidade de disparar uma nova rodada de web scraping.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, titulo, instituicao, categoria, resumo, tematica, prazo, 
                   COALESCE(aderencia_humana, aderencia) as aderencia_efetiva,
                   justificativa_ia, link, data_coleta
            FROM oportunidades
            WHERE excluido IS NOT TRUE
              AND LOWER(COALESCE(aderencia_humana, aderencia, '')) = 'alto'
            ORDER BY id DESC
            LIMIT 50
        """)
        linhas = cursor.fetchall()
        return {
            "total": len(linhas),
            "periodo_dias": dias,
            "oportunidades": [dict(r) for r in linhas]
        }
    finally:
        conn.close()

# ==================== ENDPOINTS DE OPORTUNIDADES ====================

@app.get("/oportunidades")
def listar_oportunidades(
    incluir_descartados: bool = False,
    status_revisao: Optional[str] = None,
    aderencia: Optional[str] = None,
    busca: Optional[str] = None
):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        query_conditions = []
        params = []
        
        if not incluir_descartados:
            query_conditions.append("excluido IS NOT TRUE")
            
        if status_revisao:
            query_conditions.append("status_revisao = %s")
            params.append(status_revisao)

        if aderencia:
            aderencia_normalizada = aderencia.strip().capitalize()
            if aderencia_normalizada in ['Alto', 'Médio', 'Medio', 'Baixo']:
                if aderencia_normalizada == 'Medio':
                    aderencia_normalizada = 'Médio'
                query_conditions.append("LOWER(COALESCE(aderencia_humana, aderencia, '')) = LOWER(%s)")
                params.append(aderencia_normalizada)

        if busca:
            busca_param = f"%{busca.strip()}%"
            query_conditions.append("(titulo ILIKE %s OR resumo ILIKE %s OR tematica ILIKE %s)" if is_postgres() else "(titulo LIKE %s OR resumo LIKE %s OR tematica LIKE %s)")
            params.extend([busca_param, busca_param, busca_param])
            
        where_clause = ""
        if query_conditions:
            where_clause = "WHERE " + " AND ".join(query_conditions)
            
        query = f"SELECT * FROM oportunidades {where_clause} ORDER BY id DESC"
        cursor.execute(query, tuple(params) if params else None)
        oportunidades = cursor.fetchall()
        
        # Enriquecimento de metadados para o frontend
        resultado = []
        for op in oportunidades:
            op_dict = dict(op)
            aderencia_humana = op_dict.get('aderencia_humana')
            aderencia_ia = op_dict.get('aderencia')
            status = op_dict.get('status_revisao') or 'pendente'
            
            op_dict['aderencia_efetiva'] = aderencia_humana or aderencia_ia
            op_dict['revisado_por_humano'] = bool(aderencia_humana or status in ['aprovado', 'ajustado'])
            op_dict['excluido'] = bool(op_dict.get('excluido'))
            resultado.append(op_dict)
            
        return resultado
    finally:
        conn.close()

@app.patch("/oportunidades/{op_id}/aderencia")
def calibrar_aderencia(op_id: int, payload: AderenciaUpdateSchema):
    """
    Endpoint principal de Human-in-the-Loop:
    Permite ao especialista humano alterar ou definir o nível de aderência (Alto, Médio, Baixo)
    e registrar o motivo, alimentando o dataset de calibração ativa da IA.
    """
    nova_aderencia = payload.aderencia.strip().capitalize()
    if nova_aderencia not in ['Alto', 'Médio', 'Medio', 'Baixo']:
        raise HTTPException(status_code=400, detail="Aderência inválida. Escolha entre: Alto, Médio ou Baixo.")
    if nova_aderencia == 'Medio':
        nova_aderencia = 'Médio'

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, titulo, aderencia FROM oportunidades WHERE id = %s", (op_id,))
        existente = cursor.fetchone()
        if not existente:
            raise HTTPException(status_code=404, detail="Oportunidade não encontrada.")

        motivo_final = payload.motivo.strip() if payload.motivo else f"Aderência reclassificada para {nova_aderencia} pelo especialista"

        cursor.execute('''
            UPDATE oportunidades
            SET aderencia_humana = %s,
                status_revisao = 'ajustado',
                motivo_feedback = %s,
                excluido = FALSE,
                data_feedback = CURRENT_TIMESTAMP
            WHERE id = %s
        ''', (nova_aderencia, motivo_final, op_id))
        
        conn.commit()
        
        cursor.execute("SELECT * FROM oportunidades WHERE id = %s", (op_id,))
        atualizado = dict(cursor.fetchone())
        atualizado['aderencia_efetiva'] = atualizado.get('aderencia_humana') or atualizado.get('aderencia')
        atualizado['revisado_por_humano'] = True
        return {
            "message": "Aderência calibrada com sucesso! O feedback foi incorporado à memória de treinamento da IA.",
            "oportunidade": atualizado
        }
    finally:
        conn.close()

@app.post("/oportunidades/{op_id}/aprovar")
def aprovar_aderencia(op_id: int):
    """
    Valida e confirma que a classificação da IA estava correta,
    reforçando os exemplos positivos de aprendizado.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, titulo, aderencia FROM oportunidades WHERE id = %s", (op_id,))
        existente = cursor.fetchone()
        if not existente:
            raise HTTPException(status_code=404, detail="Oportunidade não encontrada.")

        aderencia_ia = existente.get('aderencia') or 'Médio'
        motivo = f"Aprovado pelo especialista: Classificação da IA ({aderencia_ia}) confirmada como adequada."

        cursor.execute('''
            UPDATE oportunidades
            SET aderencia_humana = %s,
                status_revisao = 'aprovado',
                motivo_feedback = %s,
                excluido = FALSE,
                data_feedback = CURRENT_TIMESTAMP
            WHERE id = %s
        ''', (aderencia_ia, motivo, op_id))
        
        conn.commit()
        return {"message": "Classificação da IA confirmada e gravada como referência positiva para futuros editais."}
    finally:
        conn.close()

@app.post("/oportunidades/{op_id}/descartar")
@app.delete("/oportunidades/{op_id}")
def descartar_oportunidade(op_id: int, payload: Optional[DescarteSchema] = None):
    """
    Exclui a oportunidade da listagem ativa (soft-delete) e registra a justificativa
    do descarte para que a IA aprenda a NÃO sugerir editais semelhantes no futuro (Negative Few-Shot).
    """
    motivo = (payload.motivo if payload and payload.motivo else "Falso positivo descartado pelo usuário").strip()

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, titulo FROM oportunidades WHERE id = %s", (op_id,))
        existente = cursor.fetchone()
        if not existente:
            raise HTTPException(status_code=404, detail="Oportunidade não encontrada.")

        cursor.execute('''
            UPDATE oportunidades
            SET excluido = TRUE,
                status_revisao = 'descartado',
                motivo_feedback = %s,
                data_feedback = CURRENT_TIMESTAMP
            WHERE id = %s
        ''', (motivo, op_id))
        
        conn.commit()
        return {
            "message": "Edital descartado da lista e registrado na memória negativa da IA para evitar falsos positivos.",
            "id": op_id,
            "motivo": motivo
        }
    finally:
        conn.close()

@app.post("/oportunidades/{op_id}/restaurar")
def restaurar_oportunidade(op_id: int):
    """Restaura um edital previamente descartado."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM oportunidades WHERE id = %s", (op_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Oportunidade não encontrada.")

        cursor.execute('''
            UPDATE oportunidades
            SET excluido = FALSE,
                status_revisao = 'pendente'
            WHERE id = %s
        ''', (op_id,))
        conn.commit()
        return {"message": "Oportunidade restaurada para a lista ativa com sucesso.", "id": op_id}
    finally:
        conn.close()

# ==================== ENDPOINTS DE APRENDIZADO DA IA ====================

@app.get("/ia/aprendizado")
def obter_metricas_aprendizado():
    """
    Retorna métricas de alinhamento e as amostras ativas que estão
    sendo injetadas no prompt do Gemini para calibrar decisões futuras.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Contagem geral
        cursor.execute("SELECT COUNT(*) as count FROM oportunidades WHERE excluido IS NOT TRUE")
        total_ativas = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM oportunidades WHERE status_revisao IN ('aprovado', 'ajustado')")
        total_calibradas = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM oportunidades WHERE status_revisao = 'descartado' OR excluido IS TRUE")
        total_descartadas = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM oportunidades WHERE status_revisao = 'pendente' AND excluido IS NOT TRUE")
        total_pendentes = cursor.fetchone()['count']
        
        # Taxa de concordância IA vs Humano
        cursor.execute('''
            SELECT COUNT(*) as count FROM oportunidades 
            WHERE status_revisao = 'aprovado' 
               OR (status_revisao = 'ajustado' AND LOWER(COALESCE(aderencia_humana, '')) = LOWER(COALESCE(aderencia, '')))
        ''')
        total_concordancias = cursor.fetchone()['count']
        
        taxa_concordancia = 0.0
        if total_calibradas > 0:
            taxa_concordancia = round((total_concordancias / total_calibradas) * 100, 1)
        
        # Recupera amostras ativas de aprendizado (Few-Shot)
        positivos, negativos = obter_exemplos_aprendizado(limite=4)
        
        return {
            "metricas": {
                "total_ativas": total_ativas,
                "total_calibradas_humano": total_calibradas,
                "total_falsos_positivos_descartados": total_descartadas,
                "total_pendentes_revisao": total_pendentes,
                "taxa_concordancia_ia_humano": f"{taxa_concordancia}%",
                "status_aprendizado": "Ativo com Feedback em Tempo Real"
            },
            "exemplos_ativos_injetados_na_ia": {
                "positivos_referencia": positivos,
                "negativos_falsos_positivos": negativos
            }
        }
    finally:
        conn.close()

# ==================== ENDPOINTS CRUD PARA TEMAS ====================

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
        cursor.execute("SELECT id FROM temas WHERE LOWER(nome) = LOWER(%s)", (nome_limpo,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"O tema '{nome_limpo}' já está cadastrado.")

        cursor.execute("INSERT INTO temas (nome) VALUES (%s) RETURNING id, nome, data_criacao", (nome_limpo,))
        novo_tema = cursor.fetchone()
        conn.commit()
        return novo_tema
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

        cursor.execute("SELECT id FROM temas WHERE LOWER(nome) = LOWER(%s) AND id != %s", (nome_limpo, tema_id))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"Já existe outro tema cadastrado com o nome '{nome_limpo}'.")
        
        cursor.execute("UPDATE temas SET nome = %s WHERE id = %s RETURNING id, nome, data_criacao", (nome_limpo, tema_id))
        atualizado = cursor.fetchone()
        conn.commit()
        return atualizado
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
