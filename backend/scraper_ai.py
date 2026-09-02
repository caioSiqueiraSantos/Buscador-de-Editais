import os
import json
import sqlite3
import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

TEMAS = "Mobilidade, transporte sobre trilhos, MaaS, hidrogênio verde, blockchain, materiais avançados, energias renováveis, Indústria 4.0, inteligência artificial."

# 1. Pydantic Schema para Gemini e SQLite
class Oportunidade(BaseModel):
    titulo: str = Field(description="O título do edital ou chamada")
    instituicao: str = Field(description="Órgão responsável, ex: FINEP, FAPESP")
    categoria: str = Field(description="Deve ser: Edital, Evento, Curso ou Parceria")
    resumo: str = Field(description="Resumo de no máximo 3 linhas sobre o que se trata")
    tematica: str = Field(description="Tema principal do edital")
    prazo: str = Field(description="Prazo limite. Use 'Não informado' se não achar")
    aderencia: str = Field(description="Aderência aos temas do Metrô: Alto, Médio, Baixo")
    link: str = Field(description="Link para acesso à chamada")

def init_db():
    """Inicializa o banco de dados com restrição UNIQUE no link para evitar duplicatas."""
    conn = sqlite3.connect('oportunidades.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS oportunidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            instituicao TEXT,
            categoria TEXT,
            resumo TEXT,
            tematica TEXT,
            prazo TEXT,
            aderencia TEXT,
            link TEXT UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

def consumir_api_oculta(url):
    """Consome o endpoint REST da API oculta para extrair os dados brutos."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        dados_json = response.json()
        
        # O endpoint da FINEP retorna os resultados na chave 'items'
        itens = dados_json.get('items', [])
        return itens
    except Exception as e:
        print(f"Erro ao acessar a API: {e}")
        return []

def analisar_item_com_ia(item_json, link_base):
    """Envia o objeto JSON bruto para o Gemini e retorna um objeto Pydantic validado."""
    prompt = f"""
    Você é um analista de inovação de uma companhia de Metrô.
    Analise os dados brutos JSON retornados por uma API de fomento e extraia as informações essenciais.
    
    Regras de Negócio:
    - Avalie a aderência (Alto, Médio, Baixo) aos seguintes temas do Metrô: {TEMAS}.
    - Categoria deve ser: Edital, Evento, Curso ou Parceria.
    - O resumo deve ter no máximo 3 linhas.
    
    Dados brutos da API (JSON da chamada):
    {json.dumps(item_json, ensure_ascii=False)}
    
    Note: Utilize a URL base abaixo e concatene com o id/referência da chamada para formar o link da oportunidade, ou extraia diretamente do JSON caso seja claro.
    URL Base sugerida: {link_base}
    """
    
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Oportunidade,
            temperature=0.2
        ),
    )
    
    # O pydantic valida e já cria a classe python estruturada
    return Oportunidade.model_validate_json(response.text)

def salvar_no_banco(oportunidade: Oportunidade):
    conn = sqlite3.connect('oportunidades.db')
    cursor = conn.cursor()
    
    try:
        # INSERT OR IGNORE garante a deduplicação silenciosa baseada no link UNIQUE
        cursor.execute('''
            INSERT OR IGNORE INTO oportunidades (titulo, instituicao, categoria, resumo, tematica, prazo, aderencia, link)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            oportunidade.titulo, oportunidade.instituicao, oportunidade.categoria,
            oportunidade.resumo, oportunidade.tematica, oportunidade.prazo,
            oportunidade.aderencia, oportunidade.link
        ))
        
        if cursor.rowcount > 0:
            print(f"✅ Nova oportunidade salva: {oportunidade.titulo[:50]}...")
        else:
            print(f"⚠️ Oportunidade já existe no banco (Duplicata ignorada): {oportunidade.titulo[:50]}...")
            
        conn.commit()
    except Exception as e:
        print(f"Erro ao salvar no banco: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    
    # Endpoint da FINEP fornecido para o GET
    url_alvo = "https://www.finep.gov.br/o/c/chamadapublicas?sort=dataDePublicacao:desc&search=&page=1&pageSize=5"
    link_base_finep = "https://www.finep.gov.br/chamadas-publicas/chamadapublica/"
    
    print(f"Iniciando raspagem via API: {url_alvo} ...")
    itens = consumir_api_oculta(url_alvo)
    
    if itens:
        print(f"Encontrados {len(itens)} itens na API. Analisando os primeiros para a PoC...")
        # Processando os primeiros itens para demonstração
        for item in itens:
            try:
                print("\nEnviando item para análise da IA (Gemini)...")
                resultado_pydantic = analisar_item_com_ia(item, link_base_finep)
                salvar_no_banco(resultado_pydantic)
            except Exception as e:
                print(f"Erro ao processar item: {e}")
    else:
        print("Falha ao extrair itens da API ou a lista está vazia.")