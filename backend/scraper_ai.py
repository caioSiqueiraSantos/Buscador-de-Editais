# backend/scraper_ai.py
import os
import sys
import json
import requests
import urllib.parse
from typing import Optional, List, Dict, Any, Tuple

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

from database import init_db, obter_temas_db, get_db_connection, obter_exemplos_aprendizado

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 1. Pydantic Schema estruturado para o Gemini
class Oportunidade(BaseModel):
    titulo: str = Field(description="O título do edital ou chamada")
    instituicao: str = Field(description="Órgão responsável, ex: FINEP, FAPESP")
    categoria: str = Field(description="Deve ser: Edital, Evento, Curso ou Parceria")
    resumo: str = Field(description="Resumo de no máximo 3 linhas sobre o que se trata")
    tematica: str = Field(description="Tema principal do edital")
    prazo: str = Field(description="Prazo limite. Use 'Não informado' se não achar")
    aderencia: str = Field(description="Aderência aos temas do Metrô: Alto, Médio, Baixo")
    justificativa_ia: Optional[str] = Field(default="", description="Justificativa concisa de 1 a 2 linhas explicando por que essa aderência foi atribuída com base nos temas e histórico de calibragem humana")
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
        
        # 2. Correspondência por subtermos significativos
        subtermos = re.split(r'[,;()\/]|\be\b|\bou\b', tema_norm)
        for sub in subtermos:
            sub_limpo = sub.strip()
            if len(sub_limpo) >= 3 and sub_limpo in texto_normalizado:
                return True, f"{tema} (termo: {sub_limpo})"
            
            # 3. Correspondência por palavras individuais relevantes do tema
            for palavra in sub_limpo.split():
                if len(palavra) >= 4 and palavra not in stop_words and palavra in texto_normalizado:
                    return True, f"{tema} (palavra: {palavra})"
                
    return False, ""

def oportunidade_ja_existe(link: str, titulo: str = "") -> bool:
    """Verifica no banco se uma oportunidade já foi cadastrada e já possui descricaoRawText retido na íntegra."""
    if not link and not titulo:
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    if titulo:
        cursor.execute('''
            SELECT 1 FROM oportunidades 
            WHERE (link = %s OR titulo = %s) 
              AND descricaoRawText IS NOT NULL 
              AND descricaoRawText != ''
        ''', (link, titulo))
    else:
        cursor.execute('''
            SELECT 1 FROM oportunidades 
            WHERE link = %s 
              AND descricaoRawText IS NOT NULL 
              AND descricaoRawText != ''
        ''', (link,))
    existe = cursor.fetchone() is not None
    conn.close()
    return existe

def consumir_api_oculta(url: str):
    """Consome o endpoint REST da API da FINEP para extrair os dados brutos."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        dados_json = response.json()
        return dados_json.get('items', [])
    except Exception as e:
        print(f"Erro ao acessar a API: {e}")
        return []

ANO_MINIMO_RELEVANTE = 2025 # Ignora editais históricos antigos para economizar tokens

def edital_eh_muito_antigo(item: dict, ano_minimo: int = ANO_MINIMO_RELEVANTE) -> tuple[bool, str]:
    """Verifica se o edital é muito antigo com base na data de publicação ou vigência."""
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

def montar_secao_memoria_aprendizado(positivos: list, negativos: list) -> str:
    """Formata os feedbacks humanos para serem injetados dinamicamente no prompt do Gemini."""
    linhas = []
    if not positivos and not negativos:
        linhas.append("- Padrão Base: Dê prioridade a oportunidades voltadas a mobilidade urbana sobre trilhos, operação de metrô/trens, bilhetagem eletrônica, MaaS e infraestrutura sustentável de transporte público.")
        return "\n".join(linhas)

    if positivos:
        linhas.append("### EXEMPLOS DE EDITAIS VALIDADOS/AJUSTADOS POR ESPECIALISTAS DO METRÔ (REFERÊNCIA DE ADERÊNCIA ALTA/MÉDIA):")
        for p in positivos:
            tit = p.get('titulo') or p['titulo']
            ad = p.get('aderencia_final') or p['aderencia_final']
            mot = p.get('motivo_feedback') or "Aprovado pela equipe de inovação"
            linhas.append(f"• Edital: '{tit}' -> Aderência Humana: {ad} | Justificativa: {mot}")

    if negativos:
        linhas.append("\n### EXEMPLOS DE EDITAIS DESCARTADOS PELO HUMANO COMO FALSOS POSITIVOS (NÃO PRIORIZAR SEMELHANTES):")
        for n in negativos:
            tit = n.get('titulo') or n['titulo']
            mot = n.get('motivo_feedback') or "Fora do escopo do Metrô"
            linhas.append(f"• Edital Descartado: '{tit}' -> MOTIVO DO DESCARTE: {mot} (Atribua 'Baixo' ou desconsidere editais similares)")

    return "\n".join(linhas)

def analisar_com_ia(
    bloco_enriquecido: dict,
    url_publica: str,
    temas_lista: list[str],
    exemplos_positivos: list = None,
    exemplos_negativos: list = None
) -> Oportunidade:
    """Envia o bloco enriquecido de dados para o Gemini com Dynamic Few-Shot In-Context Learning."""
    temas_str = ", ".join(temas_lista) if temas_lista else "Mobilidade urbana, inovação tecnológica, transporte sobre trilhos"
    secao_memoria = montar_secao_memoria_aprendizado(exemplos_positivos or [], exemplos_negativos or [])
    
    prompt = f"""
    Você é um analista sênior de inovação de uma companhia de Metrô (Companhia do Metropolitano).
    Analise os dados do edital enriquecido e extraia as informações estruturadas com base nos preceitos básicos e na memória de aprendizado contínuo.
    
    Preceitos Fundamentais da Companhia:
    - Foco Institucional: Mobilidade urbana sobre trilhos, operação metroferroviária, passageiros de alta capacidade, bilhetagem/MaaS, manutenção preventiva de vias e transição energética.
    - Temas de Interesse Cadastrados no Banco: {temas_str}.
    
    MEMÓRIA DE CALIBRAÇÃO HUMANA (Decisões reais da equipe técnica para orientar seu julgamento):
    {secao_memoria}
    
    Regras de Negócio e Classificação:
    1. Aderência: Deve ser estritamente 'Alto', 'Médio' ou 'Baixo'.
       - Atribua 'Alto' quando houver sinergia direta com metrô, trens, mobilidade de passageiros ou temas estratégicos similares aos exemplos positivos validados.
       - Atribua 'Médio' para tecnologias com aplicação indireta (ex.: eficiência energética predial, ferramentas de software de gestão geral).
       - Atribua 'Baixo' quando o edital tratar de modais não correlatos (ex.: frete rodoviário de soja, caminhões de agronegócio, navios de carga) mesmo que mencione palavras como 'transporte' ou 'veículos'.
    2. Justificativa IA: Escreva de 1 a 2 linhas claras explicando a razão da nota atribuída, contrastando com os temas e o aprendizado humano.
    3. Categoria: Deve ser estritamente: Edital, Evento, Curso ou Parceria.
    4. Resumo: No máximo 3 linhas claras e objetivas.
    5. Prazo: Extraia a data limite de submissão baseando-se no Prazo Proposto ({bloco_enriquecido.get('prazoProposto')}), Vigência Fim ({bloco_enriquecido.get('vigenciaFim')}) ou texto do edital. Use 'Não informado' se não identificar.
    6. Link: Utilize a URL pública fornecida ({url_publica}).
    
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
            temperature=0.1
        ),
    )
    
    oportunidade = Oportunidade.model_validate_json(response.text)
    oportunidade.link = url_publica
    oportunidade.descricaoRawText = bloco_enriquecido.get('descricaoRawText', '')
    return oportunidade

# Alias para compatibilidade
analisar_item_com_ia = analisar_com_ia

def salvar_no_banco(oportunidade: Oportunidade):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    texto_completo = oportunidade.descricaoRawText or ""
    
    try:
        # Verifica se já existe por link ou título
        cursor.execute('SELECT id, status_revisao, aderencia_humana FROM oportunidades WHERE link = %s OR titulo = %s', (oportunidade.link, oportunidade.titulo))
        existente = cursor.fetchone()
        
        if existente:
            # Preserva a soberania humana: se o usuário já revisou, não sobrescreve a aderência humana!
            status_rev = existente.get('status_revisao') if isinstance(existente, dict) else existente[1]
            if status_rev in ['aprovado', 'ajustado']:
                cursor.execute('''
                    UPDATE oportunidades 
                    SET link = %s, descricaoRawText = %s, resumo = %s, prazo = %s, justificativa_ia = %s
                    WHERE id = %s
                ''', (
                    oportunidade.link, texto_completo,
                    oportunidade.resumo, oportunidade.prazo, oportunidade.justificativa_ia, existente['id'] if isinstance(existente, dict) else existente[0]
                ))
                print(f"🔄 Oportunidade atualizada preservando revisão humana: {oportunidade.titulo[:50]}...")
            else:
                cursor.execute('''
                    UPDATE oportunidades 
                    SET link = %s, descricaoRawText = %s, resumo = %s, prazo = %s, aderencia = %s, justificativa_ia = %s
                    WHERE id = %s
                ''', (
                    oportunidade.link, texto_completo,
                    oportunidade.resumo, oportunidade.prazo, oportunidade.aderencia, oportunidade.justificativa_ia, existente['id'] if isinstance(existente, dict) else existente[0]
                ))
                print(f"🔄 Oportunidade atualizada: {oportunidade.titulo[:50]}...")
        else:
            cursor.execute('''
                INSERT INTO oportunidades (
                    titulo, instituicao, categoria, resumo, tematica, prazo, aderencia, justificativa_ia, link, descricaoRawText
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                oportunidade.titulo, oportunidade.instituicao, oportunidade.categoria,
                oportunidade.resumo, oportunidade.tematica, oportunidade.prazo,
                oportunidade.aderencia, oportunidade.justificativa_ia, oportunidade.link, texto_completo
            ))
            print(f"✅ Nova oportunidade salva (Classificada com Memória de IA): {oportunidade.titulo[:50]}...")
            
        conn.commit()
    except Exception as e:
        print(f"Erro ao salvar no banco: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    
    # 1. Carregar temas dinâmicos
    temas_ativos = obter_temas_db()
    print(f"📌 Temas cadastrados no banco ({len(temas_ativos)}):")
    for t in temas_ativos:
        print(f"   • {t}")
    
    # 2. Carregar memória de aprendizado (feedbacks humanos de calibragem e falsos positivos)
    exemplos_pos, exemplos_neg = obter_exemplos_aprendizado(limite=4)
    print(f"\n🧠 Memória de Aprendizado Ativo carregada:")
    print(f"   • {len(exemplos_pos)} exemplos positivos de calibração humana")
    print(f"   • {len(exemplos_neg)} exemplos de falsos positivos descartados")
    
    # Endpoint REST da FINEP ordenado pelas chamadas mais recentes
    url_alvo = "https://www.finep.gov.br/o/c/chamadapublicas?sort=dataDePublicacao:desc"
    
    print(f"\nIniciando raspagem via API: {url_alvo} ...")
    itens = consumir_api_oculta(url_alvo)
    
    if itens:
        print(f"Encontrados {len(itens)} itens na API. Analisando...")
        for item in itens:
            try:
                titulo_preview = (item.get('titulo') or 'Item sem título').strip()
                item_id = item.get('id', '')
                url_publica = f"https://www.finep.gov.br/e/chamada-publica/222684/{item_id}"

                # Filtro Temporal
                eh_antigo, motivo_antigo = edital_eh_muito_antigo(item)
                if eh_antigo:
                    print(f"⏭️ Edital '{titulo_preview[:45]}' ignorado: {motivo_antigo}.")
                    continue

                # Filtro de Situação
                situacao = item.get('situacao') or {}
                situacao_key = str(situacao.get('key', '')).lower().strip()
                if situacao_key in ['encerrado', 'encerrada'] or situacao_key.startswith('encerrad'):
                    print(f"⏭️ Edital '{titulo_preview[:45]}' está '{situacao_key}'. Pulando...")
                    continue

                # Deduplicação Pré-IA
                if oportunidade_ja_existe(url_publica, titulo_preview):
                    print(f"⏭️ Oportunidade já existente ({titulo_preview[:45]}). Pulando...")
                    continue

                # Extração de Categorias
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

                categorias_str = "; ".join(categorias_lista) if categorias_lista else "Não informado"
                vigencia_inicio = item.get('vigenciaInicio')
                vigencia_fim = item.get('vigenciaFim')
                prazo_proposto = item.get('prazoProposto')
                descricao_limpa = (item.get('descricaoRawText') or item.get('descricao') or '').strip()

                bloco_enriquecido = {
                    "titulo": titulo_preview,
                    "descricaoRawText": descricao_limpa,
                    "categorias": categorias_str,
                    "vigenciaInicio": vigencia_inicio or "Não informada",
                    "vigenciaFim": vigencia_fim or "Não informada",
                    "prazoProposto": prazo_proposto or "Não informado",
                    "url_publica": url_publica
                }

                # Filtro prévio por palavras-chave / temas
                corresponde, tema_detectado = contem_palavra_chave(bloco_enriquecido, temas_ativos)
                if not corresponde:
                    print(f"⏭️ Sem palavra-chave no edital: '{titulo_preview[:45]}'. Pulando.")
                    continue
                
                print(f"\n🎯 Palavra-chave detectada: '{tema_detectado}' no edital: '{titulo_preview[:45]}'")
                print("Enviando para o Gemini com injeção de Few-Shot da memória de aprendizado...")
                
                resultado_pydantic = analisar_com_ia(
                    bloco_enriquecido,
                    url_publica,
                    temas_ativos,
                    exemplos_pos,
                    exemplos_neg
                )
                
                salvar_no_banco(resultado_pydantic)
            except Exception as e:
                print(f"Erro ao processar item: {e}")
    else:
        print("Falha ao extrair itens da API ou a lista está vazia.")