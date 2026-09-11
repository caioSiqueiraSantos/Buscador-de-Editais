import os
import sys
import json
import sqlite3
import requests
import urllib.parse
from typing import Optional

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import unicodedata
import re

from database import init_db, obter_temas_db

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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
    descricaoRawText: Optional[str] = Field(default="", description="Texto completo bruto da descrição do edital")

def normalizar_texto(texto: str) -> str:
    """Remove acentos e converte para minúsculas para comparação flexível."""
    if not texto:
        return ""
    texto_sem_html = re.sub(r'<[^>]+>', ' ', str(texto))
    nfkd = unicodedata.normalize('NFKD', texto_sem_html)
    return "".join(c for c in nfkd if unicodedata.category(c) != 'Mn').lower()

def extrair_valores_texto(item):
    """Extrai recursivamente todos os valores textuais dos campos de um JSON/dict/list."""
    valores = []
    if isinstance(item, dict):
        for v in item.values():
            valores.extend(extrair_valores_texto(v))
    elif isinstance(item, list):
        for elem in item:
            valores.extend(extrair_valores_texto(elem))
    elif isinstance(item, (str, int, float)):
        valores.append(str(item))
    return valores

def contem_palavra_chave(item_json: dict, temas: list[str]) -> tuple[bool, str]:
    """
    Verifica se o conteúdo do item contém ao menos um dos temas/palavras-chave cadastradas no banco.
    Retorna (True, tema_encontrado) se houver correspondência, ou (False, '') caso contrário.
    """
    if not temas:
        return True, "Todos os temas (banco sem restrições)"
    
    # Concatena todos os campos do JSON e normaliza
    todos_textos = " ".join(extrair_valores_texto(item_json))
    texto_normalizado = normalizar_texto(todos_textos)
    
    stop_words = {'para', 'sobre', 'como', 'com', 'sem', 'dos', 'das', 'uma', 'uns', 'umas', 'que', 'service'}

    for tema in temas:
        tema_norm = normalizar_texto(tema).strip()
        if not tema_norm:
            continue
        
        # 1. Correspondência direta do tema completo
        if tema_norm in texto_normalizado:
            return True, tema
        
        # 2. Correspondência por subtermos significativos (ex: "MaaS", "transporte sobre trilhos")
        subtermos = re.split(r'[,;()\/]|\be\b|\bou\b', tema_norm)
        for sub in subtermos:
            sub_limpo = sub.strip()
            if len(sub_limpo) >= 3 and sub_limpo in texto_normalizado:
                return True, f"{tema} (termo: {sub_limpo})"
            
            # 3. Correspondência por palavras individuais relevantes do tema (ex: "mobilidade", "transporte", "trilhos")
            for palavra in sub_limpo.split():
                if len(palavra) >= 4 and palavra not in stop_words and palavra in texto_normalizado:
                    return True, f"{tema} (palavra: {palavra})"
                
    return False, ""

def oportunidade_ja_existe(link: str, titulo: str = "") -> bool:
    """Verifica no SQLite se uma oportunidade já foi cadastrada e já possui descricaoRawText retido na íntegra."""
    if not link and not titulo:
        return False
    conn = sqlite3.connect('oportunidades.db')
    cursor = conn.cursor()
    if titulo:
        cursor.execute('''
            SELECT 1 FROM oportunidades 
            WHERE (link = ? OR titulo = ?) 
              AND descricaoRawText IS NOT NULL 
              AND descricaoRawText != ''
        ''', (link, titulo))
    else:
        cursor.execute('''
            SELECT 1 FROM oportunidades 
            WHERE link = ? 
              AND descricaoRawText IS NOT NULL 
              AND descricaoRawText != ''
        ''', (link,))
    existe = cursor.fetchone() is not None
    conn.close()
    return existe

def extrair_link_item(item_json: dict, link_base: str):
    """Tenta inferir o link da oportunidade antes da chamada ao Gemini para checagem prévia de duplicidade."""
    candidato = (
        item_json.get('link') or 
        item_json.get('url') or 
        item_json.get('id') or 
        item_json.get('codigo')
    )
    if candidato:
        candidato_str = str(candidato).strip()
        if candidato_str.startswith('http'):
            return candidato_str
        return f"{link_base.rstrip('/')}/{candidato_str.lstrip('/')}"
    return None

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

ANO_MINIMO_RELEVANTE = 2025 # Ignora editais históricos anteriores a 2025 para poupar processamento e tokens

def edital_eh_muito_antigo(item: dict, ano_minimo: int = ANO_MINIMO_RELEVANTE) -> tuple[bool, str]:
    """
    Verifica se o edital é muito antigo com base na data de publicação ou vigência.
    Retorna (True, motivo) se for antigo, ou (False, '') caso contrário.
    """
    data_pub = str(item.get('dataDePublicacao') or '').strip()
    if len(data_pub) >= 4 and data_pub[:4].isdigit():
        ano_pub = int(data_pub[:4])
        if ano_pub < ano_minimo:
            return True, f"publicado em {ano_pub} (anterior a {ano_minimo})"

    vigencia_fim = str(item.get('vigenciaFim') or '').strip()
    if len(vigencia_fim) >= 4 and vigencia_fim[:4].isdigit():
        ano_fim = int(vigencia_fim[:4])
        if ano_fim < ano_minimo:
            return True, f"vigência encerrada em {ano_fim} (anterior a {ano_minimo})"

    return False, ""

def analisar_com_ia(bloco_enriquecido: dict, url_publica: str, temas_lista: list[str]) -> Oportunidade:
    """Envia o bloco enriquecido de dados para o Gemini e retorna um objeto Pydantic validado."""
    temas_str = ", ".join(temas_lista) if temas_lista else "Mobilidade, inovação tecnológica, transporte"
    
    prompt = f"""
    Você é um analista de inovação de uma companhia de Metrô.
    Analise os dados essenciais do edital enriquecido e extraia as informações estruturadas.
    
    Regras de Negócio:
    - Avalie a aderência (Alto, Médio, Baixo) aos seguintes temas de interesse do Metrô: {temas_str}.
    - Categoria deve ser estritamente: Edital, Evento, Curso ou Parceria.
    - O resumo deve ter no máximo 3 linhas claras e objetivas.
    - Prazo: extraia a data limite de submissão baseando-se no Prazo Proposto ({bloco_enriquecido.get('prazoProposto')}), Vigência Fim ({bloco_enriquecido.get('vigenciaFim')}) ou texto do edital. Use 'Não informado' se não identificar.
    - Link: utilize a URL pública fornecida ({url_publica}).
    
    Bloco Enriquecido do Edital:
    Título: {bloco_enriquecido.get('titulo')}
    Descrição: {bloco_enriquecido.get('descricaoRawText')}
    Categorias / Taxonomia: {bloco_enriquecido.get('categorias')}
    Vigência Início: {bloco_enriquecido.get('vigenciaInicio')}
    Vigência Fim: {bloco_enriquecido.get('vigenciaFim')}
    Prazo Proposto (Submissão): {bloco_enriquecido.get('prazoProposto')}
    URL Pública: {url_publica}
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
    
    oportunidade = Oportunidade.model_validate_json(response.text)
    # Garante que o link de saída seja o proxy seguro de busca do Google
    oportunidade.link = url_publica
    # Garante a retenção integral do conteúdo bruto original (descricaoRawText)
    oportunidade.descricaoRawText = bloco_enriquecido.get('descricaoRawText', '')
    return oportunidade

# Alias para compatibilidade
analisar_item_com_ia = analisar_com_ia

def salvar_no_banco(oportunidade: Oportunidade):
    conn = sqlite3.connect('oportunidades.db')
    cursor = conn.cursor()
    
    texto_completo = oportunidade.descricaoRawText or ""
    
    try:
        # Verifica se já existe por link ou título para atualizar ou inserir
        cursor.execute('SELECT id FROM oportunidades WHERE link = ? OR titulo = ?', (oportunidade.link, oportunidade.titulo))
        existente = cursor.fetchone()
        
        if existente:
            cursor.execute('''
                UPDATE oportunidades 
                SET link = ?, descricaoRawText = ?, resumo = ?, prazo = ?, aderencia = ?
                WHERE id = ?
            ''', (
                oportunidade.link, texto_completo,
                oportunidade.resumo, oportunidade.prazo, oportunidade.aderencia, existente[0]
            ))
            print(f"🔄 Oportunidade atualizada (proxy Google + retenção texto): {oportunidade.titulo[:50]}...")
        else:
            cursor.execute('''
                INSERT INTO oportunidades (titulo, instituicao, categoria, resumo, tematica, prazo, aderencia, link, descricaoRawText)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                oportunidade.titulo, oportunidade.instituicao, oportunidade.categoria,
                oportunidade.resumo, oportunidade.tematica, oportunidade.prazo,
                oportunidade.aderencia, oportunidade.link, texto_completo
            ))
            print(f"✅ Nova oportunidade salva: {oportunidade.titulo[:50]}...")
            
        conn.commit()
    except Exception as e:
        print(f"Erro ao salvar no banco: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    
    # Carregar temas dinâmicos do banco SQLite
    temas_ativos = obter_temas_db()
    print(f"📌 Temas/Palavras-chave ativas no banco ({len(temas_ativos)}):")
    for t in temas_ativos:
        print(f"   • {t}")
    
    # Endpoint REST da FINEP ordenado pelas chamadas mais recentes (dispensa BeautifulSoup)
    url_alvo = "https://www.finep.gov.br/o/c/chamadapublicas?sort=dataDePublicacao:desc"
    link_base_finep = "https://www.finep.gov.br/chamadas-publicas/chamadapublica/"
    
    print(f"\nIniciando raspagem via API: {url_alvo} ...")
    itens = consumir_api_oculta(url_alvo)
    
    if itens:
        print(f"Encontrados {len(itens)} itens na API. Analisando os itens para a PoC...")
        for item in itens:
            try:
                titulo_preview = (item.get('titulo') or 'Item sem título').strip()
                
                # 1. Montagem dinâmica da URL pública via proxy seguro de busca do Google (evita erros 404)
                titulo_codificado = urllib.parse.quote(titulo_preview)
                url_publica = f"https://www.google.com/search?q=site:finep.gov.br+{titulo_codificado}"

                # 2. Filtro Temporal: Ignora editais muito antigos (economiza tokens e processamento)
                eh_antigo, motivo_antigo = edital_eh_muito_antigo(item)
                if eh_antigo:
                    print(f"⏭️ Edital '{titulo_preview[:45]}' ignorado: {motivo_antigo}.")
                    continue

                # 3. Filtro de Custo: verifica a chave 'key' de 'situacao'. Se encerrado, pula o processamento
                situacao = item.get('situacao') or {}
                situacao_key = str(situacao.get('key', '')).lower().strip()
                if situacao_key in ['encerrado', 'encerrada'] or situacao_key.startswith('encerrad'):
                    print(f"⏭️ Edital '{titulo_preview[:45]}' está com situação '{situacao_key}'. Pulando...")
                    continue

                # 4. Deduplicação Pré-IA baseada na URL pública e título
                if oportunidade_ja_existe(url_publica, titulo_preview):
                    print(f"⏭️ Oportunidade já existente e retida no banco ({titulo_preview[:45]}). Pulando...")
                    continue

                # 4. Extração segura de Taxonomia (.get())
                categorias_lista = []
                tema_principal = item.get('temaPrincipal') or {}
                if isinstance(tema_principal, dict):
                    nome_tema_p = tema_principal.get('name')
                    if nome_tema_p:
                        categorias_lista.append(nome_tema_p)
                elif isinstance(tema_principal, str) and tema_principal:
                    categorias_lista.append(tema_principal)

                taxonomy_briefs = item.get('taxonomyCategoryBriefs') or []
                if isinstance(taxonomy_briefs, list):
                    for cat in taxonomy_briefs:
                        if isinstance(cat, dict):
                            cat_nome = cat.get('taxonomyCategoryName') or cat.get('name')
                            if cat_nome and cat_nome not in categorias_lista:
                                categorias_lista.append(cat_nome)
                        elif isinstance(cat, str) and cat not in categorias_lista:
                            categorias_lista.append(cat)

                tema_geral = item.get('tema')
                if tema_geral and tema_geral not in categorias_lista:
                    categorias_lista.append(str(tema_geral))

                categorias_str = "; ".join(categorias_lista) if categorias_lista else "Não informado"

                # 5. Extração de Datas
                vigencia_inicio = item.get('vigenciaInicio')
                vigencia_fim = item.get('vigenciaFim')
                prazo_proposto = item.get('prazoProposto')
                descricao_limpa = (item.get('descricaoRawText') or item.get('descricao') or '').strip()

                # 6. Bloco enriquecido com título, descrição limpa, categorias e datas
                bloco_enriquecido = {
                    "titulo": titulo_preview,
                    "descricaoRawText": descricao_limpa,
                    "categorias": categorias_str,
                    "vigenciaInicio": vigencia_inicio or "Não informada",
                    "vigenciaFim": vigencia_fim or "Não informada",
                    "prazoProposto": prazo_proposto or "Não informado",
                    "url_publica": url_publica
                }

                # 7. Filtro prévio por palavras-chave / temas dinâmicos no SQLite
                corresponde, tema_detectado = contem_palavra_chave(bloco_enriquecido, temas_ativos)
                if not corresponde:
                    print(f"⏭️ Nenhuma palavra-chave encontrada no edital: '{titulo_preview[:45]}'. Ignorando conteúdo.")
                    continue
                
                print(f"\n🎯 Palavra-chave detectada: '{tema_detectado}' no edital: '{titulo_preview[:45]}'")
                print("Enviando bloco enriquecido para análise e medição de aderência com a IA (Gemini)...")
                resultado_pydantic = analisar_com_ia(bloco_enriquecido, url_publica, temas_ativos)
                
                # 8. Verificação final de duplicidade e persistência
                if oportunidade_ja_existe(resultado_pydantic.link):
                    print(f"⏭️ Oportunidade com link '{resultado_pydantic.link}' já existe no banco. Pulando inserção.")
                    continue

                salvar_no_banco(resultado_pydantic)
            except Exception as e:
                print(f"Erro ao processar item: {e}")
    else:
        print("Falha ao extrair itens da API ou a lista está vazia.")