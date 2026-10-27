# backend/pipeline.py
"""
Pipeline Central de Inteligência, Triagem e Persistência de Editais.
Recebe itens padronizados (ItemBrutoEdital) de qualquer fonte/scraper e aplica:
1. Deduplicação inteligente
2. Tier 1: Pré-filtro heurístico de divergência (Zero Token Waste)
3. Tier 2: Match de palavras-chave / temas de interesse do Metrô/NIT
4. Tier 3: Análise Cognitiva com IA (Google Gemini) com Active Learning e Structured Outputs
5. Persistência relacional no PostgreSQL/SQLite preservando feedback humano
"""

import os
import sys
import json
import unicodedata
import re
from typing import Optional, List, Dict, Any, Tuple

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from database import init_db, obter_temas_db, get_db_connection, obter_exemplos_aprendizado
from scrapers.base import ItemBrutoEdital, BaseScraper

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ==================== SCHEMAS E ESTRUTURAS ====================

class Oportunidade(BaseModel):
    titulo: str = Field(description="O título do edital ou chamada pública")
    instituicao: str = Field(description="Órgão responsável, ex: FINEP, FAPESP, CNPq")
    categoria: str = Field(description="Deve ser estritamente: Edital, Evento, Curso ou Parceria")
    resumo: str = Field(description="Resumo claro e objetivo de no máximo 3 linhas sobre o escopo do edital")
    tematica: str = Field(description="Tema principal do edital")
    prazo: str = Field(description="Prazo limite de submissão (formato data ou 'Não informado')")
    aderencia: str = Field(description="Aderência estratégica aos temas do Metrô/NIT: Alto, Médio ou Baixo")
    justificativa_ia: Optional[str] = Field(default="", description="Justificativa concisa de 1 a 2 linhas explicando a pontuação ou recusa")
    link: str = Field(description="Link público para acesso à chamada")
    descricaoRawText: Optional[str] = Field(default="", description="Texto completo bruto da descrição do edital")
    recusado: bool = Field(
        default=False,
        description="Defina estritamente como True se o edital for considerado extremamente divergente do foco do Metrô/NIT (ex.: agronegócio, pecuária, lavouras, commodities agrícolas/minerais, etc.) ou se não soar minimamente interessante/aplicável para a companhia. Defina False apenas se for aderente ou com potencial real de interesse para mobilidade, transporte, tecnologia ou mundo digital."
    )
    motivo_recusa: Optional[str] = Field(
        default="",
        description="Explicação concisa do motivo da recusa por divergência temática (preencher obrigatoriamente se recusado=True)."
    )

# ==================== UTILITÁRIOS TEXTUAIS ====================

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

# ==================== CONSTANTES DE FILTRAGEM ====================

TERMOS_RECUSA_DIVERGENCIA = [
    # Agronegócio, Agroindústria e Agropecuária
    'agronegocio', 'agropecuaria', 'agricola', 'agricultura familiar', 'lavoura', 'lavouras',
    'safra', 'safras', 'soja', 'milho', 'cana de acucar', 'cana-de-acucar', 'cafeicultura',
    'suinocultura', 'bovinocultura', 'avicultura', 'pecuaria', 'silagem',
    'fertilizante', 'fertilizantes', 'defensivo agricola', 'defensivos agricolas', 'agrotoxico',
    'pesticida', 'pesticidas', 'adubacao', 'adubo', 'trator agricola', 'tratores agricolas',
    'colheitadeira', 'colheitadeiras', 'semeadora', 'implementos agricolas',
    'piscicultura', 'aquicultura', 'pesca artesanal', 'veterinaria animal', 'manejo de pastagens',
    'cultivo de graos', 'gado de corte', 'gado leiteiro',
    'agroindustria', 'agroindustrial', 'agroindustriais', 'agro', 'bioeconomia e alimentos',
    
    # Commodities Brutas, Frete Pesado de Grãos e Mineração Extrativa
    'commodities agricolas', 'graos agricolas', 'carreta de graos', 'transporte de soja',
    'transporte rodoviario de cargas', 'mineracao de ferro', 'bauxita', 'extracao mineral bruta'
]

TERMOS_SALVAGUARDA_METRO = [
    'metro', 'metropolitano', 'trem', 'trens', 'ferrovi', 'trilho', 'vlt', 'monotrilho',
    'mobilidade urbana', 'transporte publico', 'bilhetag', 'bilhete unico', 'cbtc',
    'material rodante', 'via permanente', 'passageiro', 'passageiros', 'maas',
    'visao computacional', 'digital twin', 'gemeo digital', 'estacao de metro',
    'ciberseguranca industrial', 'telecomunicacao ferroviaria'
]

# ==================== FILTROS E SALVAGUARDAS ====================

def verificar_divergencia_sumaria(bloco_enriquecido: dict) -> Tuple[bool, str]:
    """
    Tier 1 - Heurística de Pré-Filtro (Zero Token Waste):
    Detecta editais com divergência extrema e inequívoca (ex.: agronegócio puro, defensivos, colheita)
    que não contenham nenhuma correlação com sistemas metroferroviários ou mobilidade.
    """
    todos_textos = f"{bloco_enriquecido.get('titulo', '')} {bloco_enriquecido.get('categorias', '')} {bloco_enriquecido.get('descricaoRawText', '')}"
    texto_norm = normalizar_texto(todos_textos)
    
    # Se mencionar explicitamente modais ou tecnologias metroviárias, não recusa sumariamente
    for termo_salvo in TERMOS_SALVAGUARDA_METRO:
        if termo_salvo in texto_norm:
            return False, ""
            
    # Procura termos estritamente divergentes
    for termo_div in TERMOS_RECUSA_DIVERGENCIA:
        padrao = r'\b' + re.escape(termo_div) + r'\b'
        if re.search(padrao, texto_norm):
            return True, f"Foco temático em agronegócio/commodities agrícolas ('{termo_div}'), sem correlação com o ecossistema metroferroviário ou NIT."
            
    return False, ""

def salvar_recusado_prefiltro(titulo: str, link: str, motivo: str, instituicao: str = "FINEP", resumo: str = "", raw_text: str = ""):
    """Registra no banco um edital recusado sumariamente no pré-filtro para deduplicação e memória negativa."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id, status_revisao FROM oportunidades WHERE link = %s OR titulo = %s', (link, titulo))
        existente = cursor.fetchone()
        if existente:
            op_id = existente['id'] if isinstance(existente, dict) else existente[0]
            status_rev_antigo = existente.get('status_revisao') if isinstance(existente, dict) else existente[1]
            if status_rev_antigo not in ['aprovado', 'ajustado']:
                cursor.execute('''
                    UPDATE oportunidades
                    SET status_revisao = 'descartado', excluido = TRUE, aderencia = 'Baixo',
                        motivo_feedback = %s, data_feedback = CURRENT_TIMESTAMP, descricaoRawText = %s
                    WHERE id = %s
                ''', (f"Recusado no Pré-Filtro: {motivo}", raw_text, op_id))
        else:
            cursor.execute('''
                INSERT INTO oportunidades (
                    titulo, instituicao, categoria, resumo, tematica, prazo,
                    aderencia, justificativa_ia, link, descricaoRawText,
                    status_revisao, excluido, motivo_feedback, data_feedback
                ) VALUES (%s, %s, 'Edital', %s, 'Divergente / Não aderente', 'Não informado',
                          'Baixo', %s, %s, %s, 'descartado', TRUE, %s, CURRENT_TIMESTAMP)
            ''', (
                titulo, instituicao, resumo or "Edital descartado no pré-filtro por divergência com o escopo do Metrô/NIT.",
                f"Recusado sumariamente no pré-filtro por divergência temática: {motivo}", link, raw_text,
                f"Recusado pela IA (Pré-Filtro): {motivo}"
            ))
        conn.commit()
    except Exception as e:
        print(f"Erro ao salvar recusa do pré-filtro: {e}")
    finally:
        conn.close()

def contem_palavra_chave(item_json: dict, temas: list[str]) -> Tuple[bool, str]:
    """
    Tier 2: Verifica se o conteúdo do item contém ao menos um dos temas/palavras-chave cadastradas no banco.
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

# ==================== IA E APRENDIZADO ATIVO ====================

def montar_secao_memoria_aprendizado(positivos: list, negativos: list) -> str:
    """Formata os feedbacks humanos para serem injetados dinamicamente no prompt do Gemini."""
    linhas = []
    if not positivos and not negativos:
        linhas.append("- Padrão Base: Dê prioridade máxima a oportunidades voltadas a mobilidade urbana sobre trilhos, operação de metrô/trens, bilhetagem eletrônica, MaaS, tecnologias digitais (IA, IoT, Visão Computacional) e infraestrutura sustentável de transporte público.")
        return "\n".join(linhas)

    if positivos:
        linhas.append("### EXEMPLOS DE EDITAIS VALIDADOS/AJUSTADOS POR ESPECIALISTAS DO METRÔ (REFERÊNCIA DE ADERÊNCIA ALTA/MÉDIA):")
        for p in positivos:
            tit = p.get('titulo') or p['titulo']
            ad = p.get('aderencia_final') or p['aderencia_final']
            mot = p.get('motivo_feedback') or "Aprovado pela equipe de inovação"
            linhas.append(f"• Edital: '{tit}' -> Aderência Humana: {ad} | Justificativa: {mot}")

    if negativos:
        linhas.append("\n### EXEMPLOS DE EDITAIS DESCARTADOS PELO HUMANO COMO FALSOS POSITIVOS / FORA DE ESCOPO (RECUSAR SEMELHANTES):")
        for n in negativos:
            tit = n.get('titulo') or n['titulo']
            mot = n.get('motivo_feedback') or "Fora do escopo do Metrô"
            linhas.append(f"• Edital Descartado: '{tit}' -> MOTIVO DO DESCARTE: {mot} (Obrigatório: Defina 'recusado': true e atribua 'Baixo')")

    return "\n".join(linhas)

def analisar_com_ia(
    bloco_enriquecido: dict,
    url_publica: str,
    temas_lista: list[str],
    exemplos_positivos: list = None,
    exemplos_negativos: list = None
) -> Oportunidade:
    """Tier 3: Envia o bloco enriquecido para o Gemini com Dynamic Few-Shot e triagem de aderência ao Metrô/NIT."""
    temas_str = ", ".join(temas_lista) if temas_lista else "Mobilidade urbana, inovação tecnológica, transporte sobre trilhos"
    secao_memoria = montar_secao_memoria_aprendizado(exemplos_positivos or [], exemplos_negativos or [])
    
    prompt = f"""
    Você é um Engenheiro de Software e Analista de Inovação Sênior do NIT (Núcleo de Inovação Tecnológica) da Companhia do Metrô de São Paulo.
    Sua missão é realizar a triagem técnica e estratégica de oportunidades de fomento e inovação aberta.

    🎯 DIRETRIZ ESTRATÉGICA DE INTERESSE: FOCO NO METRÔ E NO NIT DO METRÔ
    O Metrô de São Paulo opera transporte público metroferroviário de passageiros de alta capacidade em malha urbana densa.
    O NIT (Núcleo de Inovação Tecnológica) busca tecnologias e inovações aplicáveis direta ou indiretamente ao ecossistema do Metrô.

    ÁREAS DE ALTO INTERESSE E PRIORIDADE:
    1. MOBILIDADE URBANA & TRANSPORTE:
       - Transporte sobre trilhos: metrô, trens metropolitanos, VLT, monotrilho.
       - Operação metroferroviária, automação de linhas (GoA4 / trens autônomos), sinalização e controle de trens (CBTC, ATO, ATP).
       - Engenharia de material rodante, truques, via permanente, sistemas de tração, frenagem, portas de plataforma (PSD).
       - Bilhetagem eletrônica/digital, bilhete único, validação NFC/QR Code, sistemas ABT (Account-Based Ticketing).
       - MaaS (Mobility as a Service), intermodalidade (integração metrô + ônibus + micromobilidade), gestão e segurança de fluxo de passageiros, acessibilidade.
    2. TECNOLOGIA & MUNDO DIGITAL (NIT):
       - Inteligência Artificial, Aprendizado de Máquina, Visão Computacional aplicada (detecção de invasão de via, contagem e fluxo de passageiros, inspeção preventiva de ativos).
       - Internet das Coisas (IoT), sensoriamento avançado, telemetria e manutenção preditiva de componentes críticos.
       - Redes de telecomunicação críticas (5G privativo, rádio digital TETRA, redes ópticas), cibersegurança industrial (OT/SCADA) e de TI.
       - Gêmeos Digitais (Digital Twins), modelagem BIM para infraestrutura metroviária, simulação de tráfego e evacuação em estações.
       - Transformação digital corporativa, governança de dados, automação de processos e plataformas em nuvem.
    3. ENERGIA & SUSTENTABILIDADE URBANA:
       - Eletrificação, eficiência energética em tração elétrica e subestações retificadoras, recuperação de energia de frenagem regenerativa.
       - Descarbonização, baterias e hidrogênio verde aplicados ao transporte urbano ou à operação de apoio.
       - Novos materiais compósitos de alta durabilidade, redução de atrito roda-trilho, mitigação de ruído e vibração em áreas urbanas densas.
    - Temas de Interesse Cadastrados no Banco: {temas_str}.

    ⛔ DIRETRIZ MANDATÓRIA DE RECUSA (DESCARTE IMEDIATO):
    Se o edital for considerado extremamente divergente do foco do Metrô/NIT ou não soar minimamente interessante/aplicável para a companhia, VOCÊ DEVE RECUSÁ-LO (definir 'recusado': true e 'aderencia': 'Baixo').
    NÃO se deixe enganar por palavras genéricas como 'tecnologia', 'inovação', 'descarbonização', 'veículos' ou 'transporte' se o objeto fim pertencer a áreas não correlatas.
    
    Exemplos de temas EXTREMAMENTE DIVERGENTES que DEVEM SER RECUSADOS:
    - Agronegócio, Agropecuária e Campo: cultivo de grãos, lavouras, safras, defensivos agrícolas, fertilizantes, adubos, irrigação rural, tratores, colheitadeiras, sementes.
    - Commodities Agrícolas ou Minerais Brutas: soja, milho, cana-de-açúcar, café, gado, carne, celulose, mineração bruta de minério de ferro ou bauxita.
    - Logística de Granéis / Frete Rodoviário de Cargas de Commodities: carretas bi-trem, rodotrens para escoamento de safras, barcaças fluviais exclusivas de grãos.
    - Pecuária de corte/leite, suinocultura, avicultura, piscicultura, pesca e medicina veterinária animal.
    - Saúde clínica geral, hospitais, novos medicamentos ou cirurgias sem conexão com a ergonomia/operação metroviária.
    - Qualquer edital cujo objeto principal não tenha aplicabilidade prática, técnica ou científica para o Metrô ou o NIT.

    MEMÓRIA DE CALIBRAÇÃO HUMANA (Decisões reais da equipe técnica para orientar seu julgamento):
    {secao_memoria}

    REGRAS DE CLASSIFICAÇÃO:
    1. 'recusado': Booleano. Defina como TRUE se o edital divergir do foco do Metrô/NIT (agronegócio, commodities, pecuária, etc.) ou se não for interessante para a companhia. Defina como FALSE apenas se houver aplicabilidade real.
    2. 'motivo_recusa': Se 'recusado' for true, descreva em 1 a 2 linhas a razão técnica da recusa por divergência temática. Se false, deixe em branco.
    3. 'aderencia': Estritamente 'Alto', 'Médio' ou 'Baixo'.
       - Se 'recusado' for true -> OBRIGATORIAMENTE atribua 'Baixo'.
       - 'Alto': Sinergia direta com metrô, trens, mobilidade urbana, bilhetagem/MaaS ou tecnologias digitais prioritárias do NIT.
       - 'Médio': Tecnologias transversais com aplicação indireta ao Metrô (ex.: softwares corporativos gerais, eficiência energética predial geral).
       - 'Baixo': Pouca sinergia ou temas limítrofes.
    4. 'justificativa_ia': Resumo analítico de 1 a 2 linhas fundamentando a decisão de aderência ou recusa.
    5. 'categoria': Estritamente: Edital, Evento, Curso ou Parceria.
    6. 'resumo': No máximo 3 linhas claras e objetivas.
    7. 'prazo': Extraia a data limite de submissão baseando-se no Prazo Proposto ({bloco_enriquecido.get('prazoProposto')}), Vigência Fim ({bloco_enriquecido.get('vigenciaFim')}) ou texto do edital. Use 'Não informado' se não identificar.
    8. 'link': Utilize a URL pública fornecida ({url_publica}).

    Bloco Enriquecido do Edital:
    Título: {bloco_enriquecido.get('titulo')}
    Descrição: {bloco_enriquecido.get('descricaoRawText')}
    Categorias / Taxonomia: {bloco_enriquecido.get('categorias')}
    Vigência Início: {bloco_enriquecido.get('vigenciaInicio')}
    Vigência Fim: {bloco_enriquecido.get('vigenciaFim')}
    Prazo Proposto (Submissão): {bloco_enriquecido.get('prazoProposto')}
    URL Pública: {url_publica}
    """
    
    modelos_candidatos = ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-flash-latest"]
    response = None
    ultimo_erro = None

    for nome_modelo in modelos_candidatos:
        try:
            response = client.models.generate_content(
                model=nome_modelo,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Oportunidade,
                    temperature=0.1
                ),
            )
            break
        except Exception as err:
            ultimo_erro = err
            print(f"⚠️ Modelo '{nome_modelo}' indisponível ou com sobrecarga ({err}). Tentando próximo modelo...")
            continue

    if response is None:
        raise RuntimeError(f"Falha ao chamar a IA em todos os modelos candidatos. Último erro: {ultimo_erro}")
    
    oportunidade = Oportunidade.model_validate_json(response.text)
    oportunidade.link = url_publica
    oportunidade.descricaoRawText = bloco_enriquecido.get('descricaoRawText', '')
    
    if oportunidade.recusado:
        oportunidade.aderencia = "Baixo"
        if not oportunidade.motivo_recusa:
            oportunidade.motivo_recusa = oportunidade.justificativa_ia or "Recusado pela IA por divergência temática com o foco do Metrô/NIT."
            
    return oportunidade

# Alias para compatibilidade retroativa
analisar_item_com_ia = analisar_com_ia

# ==================== PERSISTÊNCIA NO BANCO ====================

def salvar_no_banco(oportunidade: Oportunidade):
    """
    Persiste o resultado da análise no banco de dados.
    Se recusado pela IA, marca como excluido e descartado para alimentar o active learning.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    texto_completo = oportunidade.descricaoRawText or ""
    eh_recusado = bool(getattr(oportunidade, 'recusado', False))
    motivo_recusa = getattr(oportunidade, 'motivo_recusa', '') or oportunidade.justificativa_ia or "Recusado pela IA por divergência temática com o foco do Metrô/NIT."
    
    aderencia_final = 'Baixo' if eh_recusado else oportunidade.aderencia
    status_revisao = 'descartado' if eh_recusado else 'pendente'
    motivo_feedback = f"Recusado pela IA: {motivo_recusa}" if eh_recusado else None
    excluido = True if eh_recusado else False
    
    try:
        cursor.execute('SELECT id, status_revisao, aderencia_humana, excluido FROM oportunidades WHERE link = %s OR titulo = %s', (oportunidade.link, oportunidade.titulo))
        existente = cursor.fetchone()
        
        if existente:
            op_id = existente['id'] if isinstance(existente, dict) else existente[0]
            status_rev_antigo = existente.get('status_revisao') if isinstance(existente, dict) else existente[1]
            
            # Preserva decisão humana prévia
            if status_rev_antigo in ['aprovado', 'ajustado']:
                cursor.execute('''
                    UPDATE oportunidades 
                    SET link = %s, descricaoRawText = %s, resumo = %s, prazo = %s, justificativa_ia = %s
                    WHERE id = %s
                ''', (
                    oportunidade.link, texto_completo,
                    oportunidade.resumo, oportunidade.prazo, oportunidade.justificativa_ia, op_id
                ))
                print(f"🔄 Oportunidade atualizada preservando revisão humana: {oportunidade.titulo[:50]}...")
            else:
                cursor.execute('''
                    UPDATE oportunidades 
                    SET link = %s, descricaoRawText = %s, resumo = %s, prazo = %s, aderencia = %s, 
                        justificativa_ia = %s, status_revisao = %s, excluido = %s, motivo_feedback = %s,
                        data_feedback = CASE WHEN %s = TRUE THEN CURRENT_TIMESTAMP ELSE data_feedback END
                    WHERE id = %s
                ''', (
                    oportunidade.link, texto_completo,
                    oportunidade.resumo, oportunidade.prazo, aderencia_final,
                    oportunidade.justificativa_ia, status_revisao, excluido, motivo_feedback,
                    excluido, op_id
                ))
                if eh_recusado:
                    print(f"🚫 [RECUSADO PELA IA] '{oportunidade.titulo[:50]}' atualizada como DESCARTADA.")
                else:
                    print(f"🔄 Oportunidade atualizada: {oportunidade.titulo[:50]}... (Aderência: {aderencia_final})")
        else:
            cursor.execute('''
                INSERT INTO oportunidades (
                    titulo, instituicao, categoria, resumo, tematica, prazo, 
                    aderencia, justificativa_ia, link, descricaoRawText,
                    status_revisao, excluido, motivo_feedback, data_feedback
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                          CASE WHEN %s = TRUE THEN CURRENT_TIMESTAMP ELSE NULL END)
            ''', (
                oportunidade.titulo, oportunidade.instituicao, oportunidade.categoria,
                oportunidade.resumo, oportunidade.tematica, oportunidade.prazo,
                aderencia_final, oportunidade.justificativa_ia, oportunidade.link, texto_completo,
                status_revisao, excluido, motivo_feedback, excluido
            ))
            if eh_recusado:
                print(f"🚫 [RECUSADO PELA IA] Edital divergente registrado como DESCARTADO: {oportunidade.titulo[:50]}...")
                print(f"   Motivo: {motivo_recusa}")
            else:
                print(f"✅ Nova oportunidade salva (Aderente): {oportunidade.titulo[:50]}... (Aderência: {aderencia_final})")
            
        conn.commit()
    except Exception as e:
        print(f"Erro ao salvar no banco: {e}")
    finally:
        conn.close()

def expurgar_editais_divergentes_banco():
    """
    Higienização Retroativa de Escopo:
    Varre o banco e descarta itens estritamente divergentes salvos no passado.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, titulo, tematica, descricaoRawText, status_revisao, aderencia_humana 
            FROM oportunidades 
            WHERE excluido IS NOT TRUE
        """)
        ativas = cursor.fetchall()
        descartadas_count = 0
        for op in ativas:
            op_id = op['id'] if isinstance(op, dict) else op[0]
            def extrair_campo(obj, *nomes_possiveis):
                if isinstance(obj, dict):
                    for nome in nomes_possiveis:
                        for k, v in obj.items():
                            if k.lower() == nome.lower() and v is not None:
                                return v
                return ""

            status_rev = extrair_campo(op, 'status_revisao')
            if status_rev in ['aprovado', 'ajustado']:
                continue
                
            bloco_fake = {
                'titulo': extrair_campo(op, 'titulo'),
                'categorias': extrair_campo(op, 'tematica', 'categoria'),
                'descricaoRawText': extrair_campo(op, 'descricaorawtext', 'descricao', 'resumo')
            }
            eh_div, motivo_div = verificar_divergencia_sumaria(bloco_fake)
            if eh_div:
                cursor.execute('''
                    UPDATE oportunidades
                    SET status_revisao = 'descartado', excluido = TRUE, aderencia = 'Baixo',
                        motivo_feedback = %s, data_feedback = CURRENT_TIMESTAMP
                    WHERE id = %s
                ''', (f"Recusado pela IA (Higienização de Escopo): {motivo_div}", op_id))
                descartadas_count += 1
                tit = (bloco_fake['titulo'] or 'Sem título')[:50]
                print(f"🧹 [HIGIENIZAÇÃO] Edital ID {op_id} ('{tit}...') marcado como DESCARTADO: {motivo_div}")
        
        conn.commit()
        if descartadas_count > 0:
            print(f"✨ Higienização concluída: {descartadas_count} oportunidades divergentes foram descartadas.")
        else:
            print("✨ Higienização: Nenhuma oportunidade ativa divergente encontrada no banco.")
    except Exception as e:
        print(f"Erro durante a higienização do banco: {e}")
    finally:
        conn.close()

# ==================== ORQUESTRADOR DO PIPELINE ====================

def processar_item_edital(
    item: ItemBrutoEdital,
    temas_ativos: list[str],
    exemplos_pos: list,
    exemplos_neg: list
) -> Tuple[str, Optional[Oportunidade]]:
    """
    Aplica a esteira completa de filtros e IA para um item coletado por qualquer scraper.
    Retornos possíveis: 'existente', 'recusado_prefiltro', 'sem_palavra_chave', 'salvo_ia', 'erro'.
    """
    titulo_preview = item.titulo[:45]

    # 1. Deduplicação Pré-IA
    if oportunidade_ja_existe(item.link, item.titulo):
        print(f"⏭️ Oportunidade já existente ({titulo_preview}). Pulando...")
        return "existente", None

    bloco_enriquecido = {
        "titulo": item.titulo,
        "descricaoRawText": item.descricao,
        "categorias": item.categorias,
        "vigenciaInicio": item.vigencia_inicio,
        "vigenciaFim": item.vigencia_fim,
        "prazoProposto": item.prazo_proposto,
        "url_publica": item.link
    }

    # 2. Tier 1: Pré-filtro de divergência extrema (Zero Token Waste)
    eh_divergente, motivo_div = verificar_divergencia_sumaria(bloco_enriquecido)
    if eh_divergente:
        print(f"\n🚫 [PRÉ-FILTRO] Edital '{titulo_preview}' recusado sumariamente por divergência temática.")
        print(f"   Motivo: {motivo_div}")
        salvar_recusado_prefiltro(
            titulo=item.titulo,
            link=item.link,
            motivo=motivo_div,
            instituicao=item.instituicao,
            resumo=item.descricao[:250],
            raw_text=item.descricao
        )
        return "recusado_prefiltro", None

    # 3. Tier 2: Filtro por palavras-chave cadastradas
    corresponde, tema_detectado = contem_palavra_chave(bloco_enriquecido, temas_ativos)
    if not corresponde:
        print(f"⏭️ Sem palavra-chave no edital: '{titulo_preview}'. Pulando.")
        return "sem_palavra_chave", None

    print(f"\n🎯 Palavra-chave detectada: '{tema_detectado}' no edital: '{titulo_preview}'")
    print(f"   Enviando [{item.instituicao}] para IA com injeção de Few-Shot da memória...")

    # 4. Tier 3: Análise com IA
    try:
        oportunidade = analisar_com_ia(
            bloco_enriquecido,
            item.link,
            temas_ativos,
            exemplos_pos,
            exemplos_neg
        )
        # Garante que a instituição original seja mantida se a IA não especificou
        if not oportunidade.instituicao or oportunidade.instituicao in ['Não informado', '']:
            oportunidade.instituicao = item.instituicao
            
        salvar_no_banco(oportunidade)
        return "salvo_ia", oportunidade
    except Exception as e:
        print(f"❌ Erro ao analisar item com IA: {e}")
        return "erro", None

def executar_scraper(scraper: BaseScraper, limite_itens: Optional[int] = None):
    """Executa a coleta e o processamento de ponta a ponta para um scraper específico."""
    print(f"\n========================================================")
    print(f"🚀 INICIANDO PIPELINE PARA FONTE: [{scraper.nome_fonte}]")
    print(f"========================================================")
    
    # Carrega estado do banco
    temas_ativos = obter_temas_db()
    exemplos_pos, exemplos_neg = obter_exemplos_aprendizado(limite=4)
    
    # 1. Coleta na fonte
    itens = scraper.coletar()
    if not itens:
        print(f"[{scraper.nome_fonte}] Nenhum item novo ou válido retornado pela coleta.")
        return

    if limite_itens:
        itens = itens[:limite_itens]

    print(f"[{scraper.nome_fonte}] {len(itens)} itens prontos para passar pela esteira de filtros e IA...")
    
    metricas = {"existente": 0, "recusado_prefiltro": 0, "sem_palavra_chave": 0, "salvo_ia": 0, "erro": 0}
    for item in itens:
        try:
            status, _ = processar_item_edital(item, temas_ativos, exemplos_pos, exemplos_neg)
            metricas[status] = metricas.get(status, 0) + 1
        except Exception as e:
            print(f"Erro inesperado no item '{item.titulo[:40]}': {e}")
            metricas["erro"] += 1

    print(f"\n📊 RESUMO DA EXECUÇÃO [{scraper.nome_fonte}]:")
    print(f"   • Salvos/Atualizados com IA: {metricas['salvo_ia']}")
    print(f"   • Recusados no Pré-Filtro: {metricas['recusado_prefiltro']}")
    print(f"   • Fora de temas cadastrados: {metricas['sem_palavra_chave']}")
    print(f"   • Já existentes no banco: {metricas['existente']}")
    if metricas['erro'] > 0:
        print(f"   • Erros de processamento: {metricas['erro']}")
