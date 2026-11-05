# backend/scrapers/faps_estaduais.py
"""
Scrapers para as Fundações Estaduais de Amparo à Pesquisa (FAPs) e Fundações Tecnológicas:
- FACEPE (PE)
- FAPAC (AC)
- FAPDF (DF)
- FAPEAM (AM)
- FAPEMAT (MT)
- FAPEMIG (MG)
- FAPERGS (RS)
- FAPERJ (RJ)
- FAPESC (SC)
- FUNDECT (MS)
- FUNTAC (AC)
"""

import json
import re
import requests
import urllib3
from typing import List
from bs4 import BeautifulSoup
from scrapers.base import (
    BaseScraper,
    ItemBrutoEdital,
    _sem_acentos,
    normalizar_data_br,
    extrair_prazo_universal,
    eh_item_ruido_ou_encerrado,
    enriquecer_itens_via_html,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
}


def _limpar_html(texto_html: str) -> str:
    if not texto_html:
        return ""
    soup = BeautifulSoup(texto_html, 'html.parser')
    return soup.get_text(separator=' ', strip=True)


def _extrair_prazo(texto: str) -> str:
    return extrair_prazo_universal(texto)


class FacepeScraper(BaseScraper):
    """
    Scraper para a FACEPE (Fundação de Amparo à Ciência e Tecnologia de Pernambuco).
    Utiliza a API WP-JSON (www2.facepe.br) e a página de listagem de editais, filtrando resultados encerrados.
    """

    @property
    def nome_fonte(self) -> str:
        return "FACEPE"

    def coletar(self) -> List[ItemBrutoEdital]:
        itens: List[ItemBrutoEdital] = []
        links_vistos = set()

        # 1. API WP-JSON (usa content.rendered completo para descrição rica e extração de prazo)
        url_api = "https://www2.facepe.br/wp-json/wp/v2/posts?per_page=20"
        print(f"[{self.nome_fonte}] Consultando API WP-JSON: {url_api} ...")
        try:
            resp = requests.get(url_api, headers=DEFAULT_HEADERS, timeout=15, verify=False)
            if resp.status_code == 200:
                for post in resp.json():
                    titulo = _limpar_html(post.get('title', {}).get('rendered', ''))
                    link = (post.get('link') or '').strip()
                    corpo = _limpar_html(post.get('content', {}).get('rendered', ''))
                    resumo = _limpar_html(post.get('excerpt', {}).get('rendered', ''))
                    texto_desc = corpo if len(corpo) > len(resumo) else resumo
                    data_pub = (post.get('date') or '')[:10]

                    if not titulo or not link or link in links_vistos:
                        continue
                    if eh_item_ruido_ou_encerrado(titulo, link, texto_desc):
                        continue

                    links_vistos.add(link)
                    itens.append(ItemBrutoEdital(
                        titulo=titulo,
                        descricao=texto_desc[:2000] if texto_desc else titulo,
                        instituicao=self.nome_fonte,
                        link=link,
                        vigencia_inicio=data_pub or "Não informada",
                        prazo_proposto=_extrair_prazo(texto_desc),
                        categorias="FACEPE - Editais e Fomento PE"
                    ))
        except Exception as e:
            print(f"[{self.nome_fonte}] Aviso WP-JSON: {e}")

        # 2. Página de Editais (filtra apenas editais recentes 2025/2026+)
        url_editais = "https://www2.facepe.br/editais/todos/"
        print(f"[{self.nome_fonte}] Consultando listagem de editais: {url_editais} ...")
        try:
            resp = requests.get(url_editais, headers=DEFAULT_HEADERS, timeout=15, verify=False)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for h in soup.find_all(['h2', 'h3', 'h4']):
                    txt = h.get_text(" ", strip=True)
                    if 'edital' not in txt.lower() and not re.search(r'\d{2}/202[5-9]', txt):
                        continue
                    container = h.find_parent(['div', 'article', 'li', 'tr'])
                    contexto = container.get_text(" ", strip=True) if container else txt
                    a = h.find('a', href=True) or (h.find_parent('a', href=True))
                    if not a and container:
                        a = container.find('a', href=True)
                    href = a['href'].strip() if a else url_editais

                    if eh_item_ruido_ou_encerrado(txt, href, contexto):
                        continue
                    if href in links_vistos and href != url_editais:
                        continue
                    links_vistos.add(href)

                    desc_final = contexto if len(contexto) > len(txt) else f"Edital Público FACEPE-PE: {txt}"
                    itens.append(ItemBrutoEdital(
                        titulo=txt,
                        descricao=desc_final[:1500],
                        instituicao=self.nome_fonte,
                        link=href,
                        prazo_proposto=_extrair_prazo(contexto),
                        categorias="FACEPE - Editais"
                    ))
        except Exception as e:
            print(f"[{self.nome_fonte}] Aviso HTML editais: {e}")

        itens = enriquecer_itens_via_html(itens, headers=DEFAULT_HEADERS, max_itens=15)
        print(f"[{self.nome_fonte}] Coleta concluída: {len(itens)} itens encontrados.")
        return itens


class FapacScraper(BaseScraper):
    """
    Scraper para a FAPAC (Fundação de Amparo à Pesquisa do Estado do Acre).
    Nota: O domínio legado fapac.acre.gov.br migrou para https://fapac.ac.gov.br.
    Filtra apenas os editais principais vigentes (2025/2026+), descartando atas, comissões e resultados.
    """

    @property
    def nome_fonte(self) -> str:
        return "FAPAC"

    def coletar(self) -> List[ItemBrutoEdital]:
        url = "https://fapac.ac.gov.br/98-2/"
        print(f"[{self.nome_fonte}] Consultando página de editais em {url} ...")
        itens: List[ItemBrutoEdital] = []
        links_vistos = set()

        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15, verify=False)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            main = soup.find('main') or soup.find(id='content') or soup

            for a in main.find_all('a', href=True):
                href = a['href'].strip()
                titulo = a.get_text(" ", strip=True)

                if len(titulo) < 15:
                    continue
                if any(s in href.lower() for s in ['facebook.com', 'twitter.com', 'whatsapp.com']):
                    continue
                # Ignora anexos de formulário, declarações ou modelos isolados
                if any(titulo.lower().startswith(p) for p in [
                    'anexo ', 'formulário', 'formulario', 'modelo de ', 'termo de ',
                    'declaração', 'declaracao', 'portaria', 'retificação', 'retificacao'
                ]):
                    continue

                bloco = a.find_parent(['div', 'li', 'p', 'section'])
                contexto = bloco.get_text(" ", strip=True) if bloco else titulo

                if eh_item_ruido_ou_encerrado(titulo, href, contexto):
                    continue

                if href in links_vistos:
                    continue
                links_vistos.add(href)

                desc_rica = (
                    f"Edital de Chamamento Público FAPAC (Fundação de Amparo à Pesquisa do Estado do Acre): {titulo}. "
                    f"Contexto da publicação: {contexto}"
                )
                itens.append(ItemBrutoEdital(
                    titulo=titulo,
                    descricao=desc_rica[:1500],
                    instituicao=self.nome_fonte,
                    link=href,
                    prazo_proposto=_extrair_prazo(contexto),
                    categorias="FAPAC - Editais Acre"
                ))
        except Exception as e:
            print(f"[{self.nome_fonte}] Erro ao coletar de {url}: {e}")

        itens = enriquecer_itens_via_html(itens, headers=DEFAULT_HEADERS, max_itens=15)
        print(f"[{self.nome_fonte}] Coleta concluída: {len(itens)} itens encontrados.")
        return itens


class FapdfScraper(BaseScraper):
    """
    Scraper para a FAPDF (Fundação de Apoio à Pesquisa do Distrito Federal).
    Coleta chamadas internacionais, editais PPSUS e destaques do portal fap.df.gov.br.
    """

    @property
    def nome_fonte(self) -> str:
        return "FAPDF"

    def coletar(self) -> List[ItemBrutoEdital]:
        urls = [
            "https://www.fap.df.gov.br/chamadas-internacionais-20261",
            "https://www.fap.df.gov.br/edital-ppsus",
            "https://www.fap.df.gov.br/"
        ]
        itens: List[ItemBrutoEdital] = []
        links_vistos = set()

        for url in urls:
            print(f"[{self.nome_fonte}] Consultando {url} ...")
            try:
                resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15, verify=False)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, 'html.parser')
                main = soup.find(id='main-content') or soup

                for a in main.find_all('a', href=True):
                    href = a['href'].strip()
                    titulo = a.get_text(" ", strip=True)

                    if not href.startswith('http'):
                        href = f"https://www.fap.df.gov.br{href}" if href.startswith('/') else f"https://www.fap.df.gov.br/{href}"

                    if len(titulo) < 12:
                        continue
                    if any(s in href.lower() for s in ['loginportlet', 'df.gov.br/category', 'sinj.df.gov.br', 'youtube.com', 'instagram.com', '#']):
                        continue
                    if any(s in href.lower() for s in ['organograma', 'planejamento-estrategico']):
                        continue

                    eh_chamada = any(
                        w in (titulo + " " + href).lower()
                        for w in ['chamada', 'edital', 'ppsus', 'confap', 'fomento', 'selecao', 'subvencao']
                    )
                    if not eh_chamada:
                        continue

                    if any(yr in href for yr in ['2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024']):
                        continue

                    pai = a.find_parent(['div', 'article', 'li', 'p'])
                    if pai and len(pai.get_text(strip=True)) < 120 and pai.parent:
                        pai = pai.parent
                    contexto = pai.get_text(" ", strip=True) if pai else titulo

                    if eh_item_ruido_ou_encerrado(titulo, href, contexto):
                        continue

                    if href in links_vistos:
                        continue
                    links_vistos.add(href)

                    desc_rica = contexto if len(contexto) >= 150 else f"Chamada Pública FAPDF (Distrito Federal): {titulo}. {contexto}"
                    itens.append(ItemBrutoEdital(
                        titulo=titulo,
                        descricao=desc_rica[:1500],
                        instituicao=self.nome_fonte,
                        link=href,
                        prazo_proposto=_extrair_prazo(contexto),
                        categorias="FAPDF - Chamadas e Editais DF"
                    ))
            except Exception as e:
                print(f"[{self.nome_fonte}] Erro ao acessar {url}: {e}")

        itens = enriquecer_itens_via_html(itens, headers=DEFAULT_HEADERS, max_itens=15)
        print(f"[{self.nome_fonte}] Coleta concluída: {len(itens)} itens encontrados.")
        return itens


class FapeamScraper(BaseScraper):
    """
    Scraper para a FAPEAM (Fundação de Amparo à Pesquisa do Estado do Amazonas).
    Consome diretamente o endpoint interno AJAX (admin-ajax.php?action=get-editais)
    e enriquece a descrição visitando a página individual de cada edital vigente.
    """

    @property
    def nome_fonte(self) -> str:
        return "FAPEAM"

    def coletar(self) -> List[ItemBrutoEdital]:
        ajax_url = "https://www.fapeam.am.gov.br/wp-admin/admin-ajax.php?action=get-editais"
        abas = ["editais-abertos", "fluxo-continuo"]
        itens: List[ItemBrutoEdital] = []
        links_vistos = set()

        headers_ajax = {
            **DEFAULT_HEADERS,
            'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'
        }

        for aba in abas:
            print(f"[{self.nome_fonte}] Consultando API AJAX interna (aba={aba}) ...")
            try:
                resp = requests.post(
                    ajax_url,
                    headers=headers_ajax,
                    data={'tipo': aba, 'p': '1', 'paginacao': '1'},
                    timeout=15,
                    verify=False
                )
                resp.raise_for_status()
                dados = resp.json()
                lista = dados.get('editais_formatted') or []

                for item in lista:
                    titulo = (item.get('post_title') or '').strip()
                    link = (item.get('permalink') or '').strip()
                    vigencia = (item.get('vigencia') or 'Não informada').strip()

                    if not titulo or not link or link in links_vistos:
                        continue
                    links_vistos.add(link)

                    partes_vig = vigencia.split('até')
                    vig_ini = normalizar_data_br(partes_vig[0].strip()) if len(partes_vig) > 0 else vigencia
                    vig_fim_raw = partes_vig[1].strip() if len(partes_vig) > 1 else vigencia
                    prazo_norm = "Fluxo Contínuo" if aba == "fluxo-continuo" and "fluxo" in vig_fim_raw.lower() else normalizar_data_br(vig_fim_raw)

                    itens.append(ItemBrutoEdital(
                        titulo=titulo,
                        descricao=f"Edital Vigente FAPEAM ({aba.replace('-', ' ').title()}): {titulo} | Vigência: {vigencia}",
                        instituicao=self.nome_fonte,
                        link=link,
                        prazo_proposto=prazo_norm,
                        vigencia_inicio=vig_ini,
                        vigencia_fim=prazo_norm,
                        categorias=f"FAPEAM - {aba.replace('-', ' ').title()}"
                    ))
            except Exception as e:
                print(f"[{self.nome_fonte}] Erro na aba {aba}: {e}")

        itens = enriquecer_itens_via_html(itens, headers=DEFAULT_HEADERS, max_itens=10)
        print(f"[{self.nome_fonte}] Coleta concluída: {len(itens)} editais vigentes encontrados.")
        return itens


class FapematScraper(BaseScraper):
    """
    Scraper para a FAPEMAT (Fundação de Amparo à Pesquisa do Estado de Mato Grosso).
    Extrai editais e chamadas abertas publicados no portal fapemat.mt.gov.br.
    """

    @property
    def nome_fonte(self) -> str:
        return "FAPEMAT"

    def coletar(self) -> List[ItemBrutoEdital]:
        urls = [
            "https://www.fapemat.mt.gov.br/",
            "https://www.fapemat.mt.gov.br/editais"
        ]
        itens: List[ItemBrutoEdital] = []
        links_vistos = set()

        for url in urls:
            print(f"[{self.nome_fonte}] Consultando {url} ...")
            try:
                resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15, verify=False)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, 'html.parser')

                for a in soup.find_all('a', href=True):
                    href = a['href'].strip()
                    titulo = a.get_text(" ", strip=True)

                    if not href.startswith('http'):
                        href = f"https://www.fapemat.mt.gov.br{href}" if href.startswith('/') else f"https://www.fapemat.mt.gov.br/{href}"

                    if len(titulo) < 18 or href.endswith('/editais_1') or href.endswith('/editais'):
                        continue
                    if not any(w in (titulo + " " + href).lower() for w in ['edital', 'chamada', '/w/', '/pt/-/']):
                        continue

                    pai = a.find_parent(['div', 'li', 'article'])
                    contexto = pai.get_text(" ", strip=True) if pai else titulo

                    if eh_item_ruido_ou_encerrado(titulo, href, contexto):
                        continue

                    if href in links_vistos:
                        continue
                    links_vistos.add(href)

                    itens.append(ItemBrutoEdital(
                        titulo=titulo,
                        descricao=contexto[:1500],
                        instituicao=self.nome_fonte,
                        link=href,
                        prazo_proposto=_extrair_prazo(contexto),
                        categorias="FAPEMAT - Editais e Chamadas MT"
                    ))
            except Exception as e:
                print(f"[{self.nome_fonte}] Erro ao acessar {url}: {e}")

        itens = enriquecer_itens_via_html(itens, headers=DEFAULT_HEADERS, max_itens=10)
        print(f"[{self.nome_fonte}] Coleta concluída: {len(itens)} itens encontrados.")
        return itens


class FapemigScraper(BaseScraper):
    """
    Scraper para a FAPEMIG (Fundação de Amparo à Pesquisa do Estado de Minas Gerais).
    Extrai chamadas abertas a partir da renderização SSR Nuxt (__NUXT_DATA__) e links de oportunidades.
    """

    @property
    def nome_fonte(self) -> str:
        return "FAPEMIG"

    def coletar(self) -> List[ItemBrutoEdital]:
        urls = [
            "https://fapemig.br/",
            "https://fapemig.br/oportunidades/chamadas-e-editais"
        ]
        itens: List[ItemBrutoEdital] = []
        links_vistos = set()
        titulos_norm_vistos = set()

        for url in urls:
            print(f"[{self.nome_fonte}] Consultando {url} ...")
            try:
                resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15, verify=False)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, 'html.parser')

                # 1. Links diretos de chamadas no HTML
                for a in soup.find_all('a', href=True):
                    href = a['href'].strip()
                    if '/oportunidades/chamadas-e-editais/' not in href:
                        continue
                    if not href.startswith('http'):
                        href = f"https://fapemig.br{href}" if href.startswith('/') else f"https://fapemig.br/{href}"

                    if href in links_vistos:
                        continue

                    pai = a.find_parent(['article', 'li']) or a.find_parent('div')
                    if pai and len(pai.get_text(strip=True)) < 25 and pai.parent:
                        pai = pai.parent
                    contexto = pai.get_text(" ", strip=True) if pai else ""
                    slug = href.rstrip('/').split('/')[-1]
                    titulo = re.sub(r'\s*Saiba Mais.*$', '', contexto, flags=re.IGNORECASE).strip()
                    if len(titulo) < 10 or len(titulo) > 180:
                        titulo = slug.replace('-', ' ').upper()
                    descricao_final = contexto if (contexto and contexto.lower() != 'saiba mais' and len(contexto) > 15) else f"Chamada Pública FAPEMIG: {titulo}"

                    chave_norm = re.sub(r'[^a-z0-9]', '', _sem_acentos(titulo))[:45]
                    if chave_norm in titulos_norm_vistos or eh_item_ruido_ou_encerrado(titulo, href, descricao_final):
                        continue

                    links_vistos.add(href)
                    titulos_norm_vistos.add(chave_norm)
                    itens.append(ItemBrutoEdital(
                        titulo=titulo,
                        descricao=descricao_final[:1500],
                        instituicao=self.nome_fonte,
                        link=href,
                        prazo_proposto=_extrair_prazo(descricao_final),
                        categorias="FAPEMIG - Chamadas e Editais MG"
                    ))

                # 2. Extração complementar do payload SSR __NUXT_DATA__
                nuxt_tag = soup.find('script', id='__NUXT_DATA__')
                if nuxt_tag:
                    try:
                        nuxt_arr = json.loads(nuxt_tag.get_text())
                        for idx, val in enumerate(nuxt_arr):
                            if isinstance(val, str) and re.match(r'^\d{3}/202\d\s*-', val.strip()):
                                titulo_call = val.strip()
                                chave_norm = re.sub(r'[^a-z0-9]', '', _sem_acentos(titulo_call))[:45]
                                if chave_norm in titulos_norm_vistos:
                                    continue
                                slug_call = nuxt_arr[idx + 1] if (idx + 1 < len(nuxt_arr) and isinstance(nuxt_arr[idx + 1], str)) else ""
                                link_call = f"https://fapemig.br/oportunidades/chamadas-e-editais/{slug_call}" if slug_call and not slug_call.startswith('http') else url
                                if link_call not in links_vistos and not eh_item_ruido_ou_encerrado(titulo_call, link_call):
                                    links_vistos.add(link_call)
                                    titulos_norm_vistos.add(chave_norm)
                                    itens.append(ItemBrutoEdital(
                                        titulo=titulo_call,
                                        descricao=f"Chamada Pública FAPEMIG: {titulo_call}",
                                        instituicao=self.nome_fonte,
                                        link=link_call,
                                        categorias="FAPEMIG - Chamadas Abertas (SSR)"
                                    ))
                    except Exception:
                        pass
            except Exception as e:
                print(f"[{self.nome_fonte}] Erro ao acessar {url}: {e}")

        itens = enriquecer_itens_via_html(itens, headers=DEFAULT_HEADERS, max_itens=15)
        print(f"[{self.nome_fonte}] Coleta concluída: {len(itens)} chamadas encontradas.")
        return itens


class FapergsScraper(BaseScraper):
    """
    Scraper para a FAPERGS (Fundação de Amparo à Pesquisa do Estado do Rio Grande do Sul).
    Monitora a página de editais abertos e os avisos/editais da página inicial.
    """

    @property
    def nome_fonte(self) -> str:
        return "FAPERGS"

    def coletar(self) -> List[ItemBrutoEdital]:
        urls = [
            "https://fapergs.rs.gov.br/abertos",
            "https://fapergs.rs.gov.br/inicial"
        ]
        itens: List[ItemBrutoEdital] = []
        links_vistos = set()

        for url in urls:
            print(f"[{self.nome_fonte}] Consultando {url} ...")
            try:
                resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15, verify=False)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, 'html.parser')

                for a in soup.find_all('a', href=True):
                    href = a['href'].strip()
                    titulo = a.get_text(" ", strip=True)

                    if href.startswith('javascript') or href.startswith('#'):
                        continue
                    if not href.startswith('http'):
                        href = f"https://fapergs.rs.gov.br{href}" if href.startswith('/') else f"https://fapergs.rs.gov.br/{href}"

                    if len(titulo) < 15:
                        continue
                    if any(href.endswith(s) for s in ['/abertos', '/em-julgamento', '/encerrados', '/chamadas-e-editais', '/selecao-2025']):
                        continue

                    eh_edital = any(
                        w in (titulo + " " + href).lower()
                        for w in ['edital', 'chamada', 'profix', 'fomento', 'selecao', 'prêmio', 'premio']
                    )
                    if not eh_edital:
                        continue

                    pai = a.find_parent(['li', 'div', 'article'])
                    contexto = pai.get_text(" ", strip=True) if pai else titulo

                    if eh_item_ruido_ou_encerrado(titulo, href, contexto):
                        continue

                    if href in links_vistos:
                        continue
                    links_vistos.add(href)

                    itens.append(ItemBrutoEdital(
                        titulo=titulo,
                        descricao=contexto[:1500],
                        instituicao=self.nome_fonte,
                        link=href,
                        prazo_proposto=_extrair_prazo(contexto),
                        categorias="FAPERGS - Editais e Chamadas RS"
                    ))
            except Exception as e:
                print(f"[{self.nome_fonte}] Erro ao acessar {url}: {e}")

        itens = enriquecer_itens_via_html(itens, headers=DEFAULT_HEADERS, max_itens=10)
        print(f"[{self.nome_fonte}] Coleta concluída: {len(itens)} itens encontrados.")
        return itens


class FaperjScraper(BaseScraper):
    """
    Scraper para a FAPERJ (Fundação Carlos Chagas Filho de Amparo à Pesquisa do Estado do Rio de Janeiro).
    Extrai os editais lançados na Lista Oficial de Editais / Chamadas (/?id=28.5.7).
    """

    @property
    def nome_fonte(self) -> str:
        return "FAPERJ"

    def coletar(self) -> List[ItemBrutoEdital]:
        url = "https://www.faperj.br/?id=28.5.7"
        print(f"[{self.nome_fonte}] Consultando Lista de Editais: {url} ...")
        itens: List[ItemBrutoEdital] = []
        links_vistos = set()

        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15, verify=False)
            resp.raise_for_status()
            html_str = resp.content.decode('utf-8', errors='replace')
            soup = BeautifulSoup(html_str, 'html.parser')

            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                titulo = a.get_text(" ", strip=True)

                if href.startswith('javascript') or href.startswith('#'):
                    continue
                if not href.startswith('http'):
                    href = f"https://www.faperj.br/{href.lstrip('/')}"

                # Ignora links secundários de resultados ("confira a lista...", "veja a lista...")
                if any(titulo.lower().startswith(p) for p in ['confira ', 'veja ', 'lista de ', 'quem ', 'resultado']):
                    continue
                if not ('edital' in titulo.lower() or 'chamada' in titulo.lower()):
                    continue
                if len(titulo) < 15:
                    continue

                pai = a.find_parent(['p', 'li', 'div'])
                contexto = pai.get_text(" ", strip=True) if pai else titulo

                # Se o texto da âncora for uma URL crua (ex.: chamadas conjuntas CONFAP), extrai o título real do parágrafo pai
                if titulo.lower().startswith('http'):
                    antes_url = contexto.split('http')[0].strip(' -–:;')
                    if len(antes_url) >= 15:
                        titulo = antes_url[:180]
                    else:
                        slug = href.rstrip('/').split('/')[-1]
                        titulo = f"Chamada Conjunta FAPERJ/CONFAP: {slug.replace('-', ' ').title()}"

                if eh_item_ruido_ou_encerrado(titulo, href, contexto):
                    continue

                if href in links_vistos:
                    continue
                links_vistos.add(href)

                itens.append(ItemBrutoEdital(
                    titulo=titulo,
                    descricao=contexto[:1500],
                    instituicao=self.nome_fonte,
                    link=href,
                    prazo_proposto=_extrair_prazo(contexto),
                    categorias="FAPERJ - Editais e Chamadas RJ"
                ))
        except Exception as e:
            print(f"[{self.nome_fonte}] Erro ao acessar {url}: {e}")

        itens = enriquecer_itens_via_html(itens, headers=DEFAULT_HEADERS, max_itens=20)
        print(f"[{self.nome_fonte}] Coleta concluída: {len(itens)} editais encontrados.")
        return itens


class FapescScraper(BaseScraper):
    """
    Scraper para a FAPESC (Fundação de Amparo à Pesquisa e Inovação do Estado de Santa Catarina).
    Coleta chamadas abertas diretamente de /chamadas-abertas/ e da API WP-JSON, filtrando resultados de mérito.
    """

    @property
    def nome_fonte(self) -> str:
        return "FAPESC"

    def coletar(self) -> List[ItemBrutoEdital]:
        itens: List[ItemBrutoEdital] = []
        links_vistos = set()

        # 1. Página de Chamadas Abertas
        url_abertas = "https://fapesc.sc.gov.br/chamadas-abertas/"
        print(f"[{self.nome_fonte}] Consultando Chamadas Abertas: {url_abertas} ...")
        try:
            resp = requests.get(url_abertas, headers=DEFAULT_HEADERS, timeout=15, verify=False)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            for h in soup.find_all(['h2', 'h3', 'h4']):
                titulo = h.get_text(" ", strip=True)
                if not any(w in titulo.lower() for w in ['edital', 'chamada']):
                    continue
                if titulo.upper() == 'CHAMADAS ABERTAS':
                    continue

                bloco = h.find_parent(['div', 'article', 'section'])
                contexto = bloco.get_text(" ", strip=True) if bloco else titulo

                a = h.find('a', href=True) or h.find_parent('a', href=True)
                if not a and bloco:
                    a = bloco.find('a', href=True)

                href = a['href'].strip() if a else f"{url_abertas}#{re.sub(r'[^a-z0-9]+', '-', titulo.lower())[:40]}"

                if eh_item_ruido_ou_encerrado(titulo, href, contexto):
                    continue
                if href in links_vistos:
                    continue
                links_vistos.add(href)

                desc_rica = contexto if len(contexto) >= 150 else f"Chamada Pública Aberta FAPESC (Santa Catarina): {titulo}. {contexto}"
                itens.append(ItemBrutoEdital(
                    titulo=titulo,
                    descricao=desc_rica[:1500],
                    instituicao=self.nome_fonte,
                    link=href,
                    prazo_proposto=_extrair_prazo(contexto),
                    categorias="FAPESC - Chamadas Abertas SC"
                ))
        except Exception as e:
            print(f"[{self.nome_fonte}] Erro em chamadas abertas: {e}")

        # 2. API WP-JSON complementar (apenas chamadas abertas, descartando resultados preliminares/finais)
        url_api = "https://fapesc.sc.gov.br/wp-json/wp/v2/posts?per_page=15"
        try:
            resp = requests.get(url_api, headers=DEFAULT_HEADERS, timeout=15, verify=False)
            if resp.status_code == 200:
                for post in resp.json():
                    titulo = _limpar_html(post.get('title', {}).get('rendered', ''))
                    link = (post.get('link') or '').strip()
                    corpo = _limpar_html(post.get('content', {}).get('rendered', ''))
                    resumo = _limpar_html(post.get('excerpt', {}).get('rendered', ''))
                    texto_desc = corpo if len(corpo) > len(resumo) else resumo

                    if not titulo or not link or link in links_vistos:
                        continue
                    if not any(w in titulo.lower() for w in ['edital', 'chamada', 'seleção', 'selecao', 'fomento']):
                        continue
                    if eh_item_ruido_ou_encerrado(titulo, link, texto_desc):
                        continue

                    links_vistos.add(link)
                    itens.append(ItemBrutoEdital(
                        titulo=titulo,
                        descricao=texto_desc[:2000] if texto_desc else titulo,
                        instituicao=self.nome_fonte,
                        link=link,
                        vigencia_inicio=(post.get('date') or '')[:10],
                        prazo_proposto=_extrair_prazo(texto_desc),
                        categorias="FAPESC - Publicações de Editais"
                    ))
        except Exception as e:
            print(f"[{self.nome_fonte}] Aviso WP-JSON: {e}")

        itens = enriquecer_itens_via_html(itens, headers=DEFAULT_HEADERS, max_itens=15)
        print(f"[{self.nome_fonte}] Coleta concluída: {len(itens)} chamadas encontradas.")
        return itens


class FundectScraper(BaseScraper):
    """
    Scraper para a FUNDECT (Fundação de Apoio ao Desenvolvimento do Ensino, Ciência e Tecnologia do MS).
    Coleta chamadas na página de Consulta de Editais (/informativos/consultas/) e via API WP-JSON.
    """

    @property
    def nome_fonte(self) -> str:
        return "FUNDECT"

    def coletar(self) -> List[ItemBrutoEdital]:
        url = "https://www.fundect.ms.gov.br/informativos/consultas/"
        print(f"[{self.nome_fonte}] Consultando página de Editais: {url} ...")
        itens: List[ItemBrutoEdital] = []
        links_vistos = set()

        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15, verify=False)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                titulo = a.get_text(" ", strip=True)

                if href.startswith('#') or len(titulo) < 20:
                    continue
                if any(titulo.lower().startswith(p) for p in [
                    'anexo ', 'acessar proposta', 'lista preliminar', 'listas preliminares',
                    'resultado ', 'ficha de ', 'declaração', 'declaracao', 'projeto de pesquisa'
                ]):
                    continue
                if not any(w in titulo.lower() for w in ['chamada', 'edital']):
                    continue

                bloco = a.find_parent(['div', 'section', 'article', 'li'])
                contexto = bloco.get_text(" ", strip=True) if bloco else titulo

                if eh_item_ruido_ou_encerrado(titulo, href, contexto):
                    continue

                if href in links_vistos:
                    continue
                links_vistos.add(href)

                desc_rica = (
                    f"Chamada Pública FUNDECT-MS (Mato Grosso do Sul): {titulo}. "
                    f"Detalhes e documentos da chamada: {contexto}"
                )
                itens.append(ItemBrutoEdital(
                    titulo=titulo,
                    descricao=desc_rica[:1500],
                    instituicao=self.nome_fonte,
                    link=href,
                    prazo_proposto=_extrair_prazo(contexto),
                    categorias="FUNDECT - Chamadas Públicas MS"
                ))
        except Exception as e:
            print(f"[{self.nome_fonte}] Erro ao acessar {url}: {e}")

        print(f"[{self.nome_fonte}] Coleta concluída: {len(itens)} chamadas encontradas.")
        return itens


class FuntacScraper(BaseScraper):
    """
    Scraper para a FUNTAC (Fundação de Tecnologia do Estado do Acre).
    Nota Técnica: O portal https://funtac.ac.gov.br/editais/ mantém apenas arquivos históricos de 2021 e 2022,
    enquanto os editais vigentes de CT&I do Acre (2025/2026+) foram centralizados na FAPAC (https://fapac.ac.gov.br/98-2/).
    """

    @property
    def nome_fonte(self) -> str:
        return "FUNTAC"

    @property
    def habilitado(self) -> bool:
        return False

    def coletar(self) -> List[ItemBrutoEdital]:
        url = "https://funtac.ac.gov.br/editais/"
        print(f"[{self.nome_fonte}] Consultando página de editais: {url} ...")
        itens: List[ItemBrutoEdital] = []
        links_vistos = set()

        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15, verify=False)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            main = soup.find('main') or soup.find(id='content') or soup

            for a in main.find_all('a', href=True):
                href = a['href'].strip()
                titulo = a.get_text(" ", strip=True)

                if not href.startswith('http') or any(s in href.lower() for s in ['facebook.com', 'twitter.com', 'whatsapp.com']):
                    continue
                if len(titulo) < 12 or titulo.lower() in ['baixar', 'acesse']:
                    continue
                if any(w in titulo.lower() for w in ['instruções', 'instrucoes', 'resumo expandido', 'modelo pôster', 'formulário de recurso']):
                    continue
                if not any(w in (titulo + " " + href).lower() for w in ['edital', 'chamada']):
                    continue

                if titulo.startswith('http'):
                    titulo = titulo.rstrip('/').split('/')[-1].replace('.pdf', '').replace('-', ' ')

                if eh_item_ruido_ou_encerrado(titulo, href):
                    continue

                if href in links_vistos:
                    continue
                links_vistos.add(href)

                itens.append(ItemBrutoEdital(
                    titulo=titulo,
                    descricao=f"Publicação FUNTAC/AC: {titulo}",
                    instituicao=self.nome_fonte,
                    link=href,
                    categorias="FUNTAC - Editais e Chamadas Acre"
                ))
        except Exception as e:
            print(f"[{self.nome_fonte}] Erro ao acessar {url}: {e}")

        print(f"[{self.nome_fonte}] Coleta concluída: {len(itens)} itens recentes encontrados.")
        return itens
