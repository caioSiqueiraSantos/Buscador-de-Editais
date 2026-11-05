# backend/scrapers/base.py
import re
import unicodedata
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Dict, Any
import requests
import urllib3
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MESES_PT = {
    'janeiro': '01', 'fevereiro': '02', 'marco': '03', 'março': '03',
    'abril': '04', 'maio': '05', 'junho': '06', 'julho': '07',
    'agosto': '08', 'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12',
    'jan': '01', 'fev': '02', 'mar': '03', 'abr': '04', 'mai': '05', 'jun': '06',
    'jul': '07', 'ago': '08', 'set': '09', 'out': '10', 'nov': '11', 'dez': '12'
}


def _sem_acentos(txt: str) -> str:
    if not txt:
        return ""
    nfkd = unicodedata.normalize('NFKD', str(txt))
    return "".join(c for c in nfkd if unicodedata.category(c) != 'Mn').lower()


def normalizar_data_br(texto_data: str) -> str:
    """Padroniza datas extraídas (ISO, DD-MM-YYYY, por extenso) para DD/MM/YYYY."""
    if not texto_data:
        return "Não informado"
    t = texto_data.strip()
    if not t or t.lower() in ['não informado', 'nao informado', 'n/a', 'não informada']:
        return "Não informado"

    if 'fluxo cont' in t.lower():
        return "Fluxo Contínuo"

    # Formato ISO YYYY-MM-DD
    m_iso = re.search(r'(\d{4})[-/](\d{2})[-/](\d{2})', t)
    if m_iso:
        ano, mes, dia = m_iso.groups()
        return f"{dia}/{mes}/{ano}"

    # Formato DD/MM/YYYY, DD-MM-YYYY ou DD.MM.YYYY
    m_dmy = re.search(r'(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})', t)
    if m_dmy:
        dia, mes, ano = m_dmy.groups()
        if len(ano) == 2:
            ano = f"20{ano}"
        return f"{int(dia):02d}/{int(mes):02d}/{ano}"

    # Formato por extenso ("15 de dezembro de 2026")
    m_ext = re.search(
        r'(\d{1,2})(?:º|o)?\s+de\s+([a-zç]+)\s+de\s+(202\d)',
        t.lower()
    )
    if m_ext:
        dia, nome_mes, ano = m_ext.groups()
        mes = MESES_PT.get(_sem_acentos(nome_mes))
        if mes:
            return f"{int(dia):02d}/{mes}/{ano}"

    return t


def extrair_prazo_universal(texto: str) -> str:
    """
    Extrai a data limite de submissão/inscrição a partir de textos ou cronogramas em português,
    retornando no formato padronizado DD/MM/YYYY ou 'Fluxo Contínuo'.
    """
    if not texto:
        return "Não informado"

    # 1. Intervalo de datas ("de DD/MM/YYYY a DD/MM/YYYY" ou "DD/MM/YYYY até DD/MM/YYYY")
    m_range = re.search(
        r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]202\d\s*(?:a|até|ate|-|–)\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]202[5-9])',
        texto,
        re.IGNORECASE
    )
    if m_range:
        return normalizar_data_br(m_range.group(1))

    # 2. Data numérica próxima a termos de prazo/submissão/inscrição/encerramento
    m_num = re.search(
        r'(?:prazo(?:\s+final|\s+limite)?|submiss[aã]o(?:\s+de\s+propostas)?|inscri[cç][oõ]es|encerramento|data\s+limite|propostas\s+at[eé]|at[eé]\s+o\s+dia|at[eé]|vig[eê]ncia)\s*[^0-9\n]{0,35}?(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]202[5-9])',
        texto,
        re.IGNORECASE
    )
    if m_num:
        return normalizar_data_br(m_num.group(1))

    # 3. Data por extenso próxima a termos de prazo/submissão/inscrição
    m_ext = re.search(
        r'(?:prazo|submiss[aã]o|inscri[cç][oõ]es|encerramento|propostas|at[eé])[^.\n]{0,45}?(\d{1,2}(?:º|o)?\s+de\s+(?:janeiro|fevereiro|mar[cç]o|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\s+de\s+202[5-9])',
        texto,
        re.IGNORECASE
    )
    if m_ext:
        return normalizar_data_br(m_ext.group(1))

    # 4. Qualquer data por extenso de 2026/2027 no texto
    m_ext_any = re.search(
        r'(\d{1,2}(?:º|o)?\s+de\s+(?:janeiro|fevereiro|mar[cç]o|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\s+de\s+202[6-9])',
        texto,
        re.IGNORECASE
    )
    if m_ext_any:
        return normalizar_data_br(m_ext_any.group(1))

    # 5. Fluxo contínuo explícito
    if re.search(r'\bfluxo\s+cont[ií]nuo\b', texto, re.IGNORECASE):
        return "Fluxo Contínuo"

    return "Não informado"


def eh_item_ruido_ou_encerrado(titulo: str, link: str = "", descricao: str = "") -> bool:
    """
    Filtra ruídos que não são oportunidades abertas:
    - Resultados preliminares/finais, atas, homologações, comissões de julgamento, erratas isoladas
    - Notícias esportivas (Vôlei, Judô, Rugby, Basquete, NBB, Superliga)
    - Chamadas antigas explícitas (<= 2024) sem menção a 2025/2026+ ou fluxo contínuo
    """
    if not titulo or len(titulo.strip()) < 12:
        return True

    t_norm = _sem_acentos(titulo).strip()
    link_norm = _sem_acentos(link).strip()
    desc_norm = _sem_acentos(descricao).strip()

    # Títulos genéricos de interface / imagens
    if t_norm in [
        'logotipo do evento', 'saiba mais', 'leia mais', 'ver documentos',
        'clique aqui', 'acesse', 'baixar', 'chamadas de propostas',
        'como submeter propostas', 'execucao de processos', 'normas'
    ]:
        return True

    # 1. Resultados de editais já encerrados, homologações, comissões e recursos
    padroes_fase_encerrada = [
        r'\bresultado\s+(preliminar|final|parcial|de\s+merito|do\s+julgamento|da\s+etapa|do\s+processo|do\s+programa|do\s+edital|da\s+chamada)',
        r'\bresultados\s+(preliminares|finais)',
        r'^resultado[\s\-_]',
        r'\bextrato\s+d[eo]\s+resultado\b',
        r'\b(divulga|divulgado|anuncia|confira\s+o)\s+resultado\b',
        r'\bhomologacao\s+(do\s+resultado|das\s+inscri|final|preliminar)',
        r'\bcomissao\s+de\s+(selecao|julgamento|avaliacao|enquadramento)',
        r'\bautodeclaracao\s+d[oa]\s+candidat',
        r'\bformulario\s+de\s+recurso\b',
        r'\blista\s+(preliminar|final)\s+de\s+(inscritos|aprovados|habilitados)',
        r'\bpropostas\s+(homologadas|inabilitadas|aprovadas)\b',
    ]
    for pat in padroes_fase_encerrada:
        if re.search(pat, t_norm):
            return True

    # 2. Notícias esportivas ou homenagens corporativas (ex.: SESI Esporte / SENAI)
    padroes_esporte = [
        r'\bsuperliga\b', r'\bvolei\b', r'\bjudo\b', r'\brugby\b',
        r'\bbasquete\b', r'\bnbb\b', r'\bgrand\s+slam\b',
        r'\bselecao\s+brasileira\s+sub\b', r'\bopen\s+pan-americano\b',
        r'\be\s+homenagead[oa]\b', r'\bindustria\s+homenageia\b',
        r'\brelatorio\s+de\s+auditoria\b'
    ]
    for pat in padroes_esporte:
        if re.search(pat, t_norm):
            return True

    # 3. Verificação de recência: descarta editais explicitamente antigos (<= 2024)
    combinado = f"{t_norm} {link_norm} {desc_norm}"
    tem_ano_recente = re.search(r'\b202[5-9]\b', combinado) is not None
    tem_fluxo_continuo = 'fluxo continuo' in combinado

    if not tem_ano_recente and not tem_fluxo_continuo:
        # Se o título ou o slug da URL menciona explicitamente anos de 2015 a 2024
        if re.search(r'(?:^|[\s\/\-_nº°])20(?:1\d|2[0-4])(?:$|[\s\/\-_\.\)])', f"{t_norm} {link_norm}"):
            return True

    return False


def enriquecer_itens_via_html(
    itens: List["ItemBrutoEdital"],
    headers: Optional[Dict[str, str]] = None,
    max_workers: int = 6,
    max_itens: int = 25
) -> List["ItemBrutoEdital"]:
    """
    Scraping em 2 Etapas (Detail Page Enrichment):
    Visita em paralelo as páginas HTML internas dos itens que ainda não possuem prazo
    ou cuja descrição na listagem é apenas o título curto, extraindo o corpo completo
    do edital e o prazo de submissão padronizado (DD/MM/YYYY).
    """
    if not itens:
        return itens

    req_headers = headers or {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
    }

    extensoes_binarias = ('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar', '.odt', '.jpg', '.png')

    candidatos = [
        item for item in itens
        if item.link.startswith('http')
        and not item.link.lower().split('?')[0].endswith(extensoes_binarias)
        and (
            not item.prazo_proposto
            or item.prazo_proposto in ['Não informado', 'Não informada']
            or len(item.descricao or '') < 220
        )
    ][:max_itens]

    if not candidatos:
        return itens

    def _enriquecer_um(item: "ItemBrutoEdital"):
        try:
            resp = requests.get(item.link, headers=req_headers, timeout=8, verify=False)
            if resp.status_code != 200:
                return
            ctype = (resp.headers.get('Content-Type') or '').lower()
            if 'pdf' in ctype or 'octet-stream' in ctype:
                return

            html_str = resp.content.decode('utf-8', errors='replace')
            soup = BeautifulSoup(html_str, 'html.parser')

            # Remove elementos de navegação, rodapé, scripts e menus laterais
            for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
                tag.decompose()

            container = (
                soup.find(id='content-core')
                or soup.find('article')
                or soup.find('main')
                or soup.find(id='main-content')
                or soup.find(id='content')
                or soup.find(class_=re.compile(r'(entry-content|post-content|node-content|article-body|conteudo|materia)', re.I))
                or soup.body
            )
            if not container:
                return

            texto_pagina = container.get_text(separator=' ', strip=True)
            texto_pagina = re.sub(r'\s+', ' ', texto_pagina).strip()

            if len(texto_pagina) > len(item.descricao or '') and len(texto_pagina) >= 120:
                item.descricao = f"{item.titulo} — {texto_pagina}"[:2500]

            if not item.prazo_proposto or item.prazo_proposto in ['Não informado', 'Não informada']:
                prazo_extraido = extrair_prazo_universal(texto_pagina)
                if prazo_extraido != "Não informado":
                    item.prazo_proposto = prazo_extraido
        except Exception:
            pass

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        list(executor.map(_enriquecer_um, candidatos))

    # Filtra itens cujo conteúdo enriquecido revelou ser de ano encerrado (<= 2024) ou ruído
    itens_filtrados = [
        it for it in itens
        if not eh_item_ruido_ou_encerrado(it.titulo, it.link, it.descricao)
    ]
    return itens_filtrados


class ItemBrutoEdital(BaseModel):
    """
    Contrato Universal: Qualquer fonte (API, HTML scraping, RSS, Playwright, etc.)
    deve transformar os dados brutos capturados nesta estrutura padronizada
    antes de enviar para a esteira de filtros e IA.
    """
    titulo: str = Field(description="Título da chamada pública, edital ou oportunidade")
    descricao: str = Field(description="Descrição bruta, escopo ou resumo textual extraído da fonte")
    instituicao: str = Field(description="Nome do órgão/instituição de fomento (ex: FINEP, FAPESP, SENAI, CNPq)")
    link: str = Field(description="URL pública do edital na íntegra")
    prazo_proposto: Optional[str] = Field(default="Não informado", description="Prazo ou vigência final de submissão")
    vigencia_inicio: Optional[str] = Field(default="Não informada", description="Data de publicação ou início de vigência")
    vigencia_fim: Optional[str] = Field(default="Não informada", description="Data de encerramento da vigência")
    categorias: Optional[str] = Field(default="Não informado", description="Categorias, áreas temáticas ou taxonomia da fonte")
    dados_adicionais: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadados específicos da fonte")

class BaseScraper(ABC):
    """
    Classe Abstrata que define o contrato obrigatório para todos os Scrapers/Crawlers.
    Para adicionar uma nova fonte (ex: SENAI, CNPq), basta herdar desta classe
    e implementar as propriedades e o método `coletar()`.
    """

    @property
    @abstractmethod
    def nome_fonte(self) -> str:
        """Identificador textual único do scraper (ex: 'FINEP', 'FAPESP')."""
        pass

    @property
    def habilitado(self) -> bool:
        """Indica se este scraper deve ser executado na rotina geral."""
        return True

    @abstractmethod
    def coletar(self) -> List[ItemBrutoEdital]:
        """
        Executa a extração da fonte (seja via requests API, BeautifulSoup, Playwright, etc.)
        e retorna uma lista de itens normalizados no formato ItemBrutoEdital.
        """
        pass
