# backend/scrapers/associacoes_sistema_s.py
"""
Scrapers para Associações de Inovação, Sistema S, Fundações de Apoio e Agências Regionais:
- ANPEI (Associação Nacional de Pesquisa e Desenvolvimento das Empresas Inovadoras)
- ANPROTEC (Associação Nacional de Entidades Promotoras de Empreendimentos Inovadores)
- SENAI-SP (Serviço Nacional de Aprendizagem Industrial)
- SESI-SP (Serviço Social da Indústria)
- FI GROUP (Consultoria de Financiamento à Inovação)
- FUNDEP (Fundação de Desenvolvimento da Pesquisa - UFMG)
- DESENVOLVE SP (Agência de Fomento do Estado de São Paulo)
"""

import re
import requests
import urllib3
from typing import List
from bs4 import BeautifulSoup
from scrapers.base import (
    BaseScraper,
    ItemBrutoEdital,
    eh_item_ruido_ou_encerrado,
    extrair_prazo_universal,
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


class AnpeiScraper(BaseScraper):
    """
    Scraper para a ANPEI.
    Consome a API REST WordPress (/wp-json/wp/v2/posts) extraindo o conteúdo completo das publicações.
    """

    @property
    def nome_fonte(self) -> str:
        return "ANPEI"

    def coletar(self) -> List[ItemBrutoEdital]:
        url_api = "https://anpei.org.br/wp-json/wp/v2/posts?per_page=15"
        print(f"[{self.nome_fonte}] Consultando API WP-JSON: {url_api} ...")
        itens: List[ItemBrutoEdital] = []
        links_vistos = set()

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
                        categorias="ANPEI - PD&I e Fomento Empresarial"
                    ))
        except Exception as e:
            print(f"[{self.nome_fonte}] Erro ao consultar WP-JSON: {e}")

        print(f"[{self.nome_fonte}] Coleta concluída: {len(itens)} publicações encontradas.")
        return itens


class AnprotecScraper(BaseScraper):
    """
    Scraper para a ANPROTEC.
    Coleta diretamente da aba dedicada de Oportunidades (/site/oportunidades/) e da API WP-JSON,
    enriquecendo o corpo completo e os prazos de cada oportunidade em 2 etapas.
    """

    @property
    def nome_fonte(self) -> str:
        return "ANPROTEC"

    def coletar(self) -> List[ItemBrutoEdital]:
        itens: List[ItemBrutoEdital] = []
        links_vistos = set()

        # 1. Página dedicada de Oportunidades (Editais, Chamadas e Programas)
        url_op = "https://anprotec.org.br/site/oportunidades/"
        print(f"[{self.nome_fonte}] Consultando página de Oportunidades: {url_op} ...")
        try:
            resp = requests.get(url_op, headers=DEFAULT_HEADERS, timeout=15, verify=False)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                titulo = a.get_text(" ", strip=True)

                if not re.search(r'anprotec\.org\.br/site/202\d/', href):
                    continue
                if not titulo or titulo.lower() in ['leia mais', 'saiba mais'] or len(titulo) < 15:
                    continue

                pai = a.find_parent(['article', 'div', 'li'])
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
                    categorias="ANPROTEC - Oportunidades e Editais"
                ))
        except Exception as e:
            print(f"[{self.nome_fonte}] Erro em {url_op}: {e}")

        # 2. Complemento via API WP-JSON (usa content.rendered completo)
        url_api = "https://anprotec.org.br/site/wp-json/wp/v2/posts?per_page=10"
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
                        categorias="ANPROTEC - Notícias e Chamadas"
                    ))
        except Exception as e:
            print(f"[{self.nome_fonte}] Aviso WP-JSON: {e}")

        # Etapa 2: Enriquece páginas HTML da aba Oportunidades para obter texto completo e prazo
        itens = enriquecer_itens_via_html(itens, headers=DEFAULT_HEADERS, max_itens=25)
        print(f"[{self.nome_fonte}] Coleta concluída: {len(itens)} oportunidades encontradas.")
        return itens


class SenaiScraper(BaseScraper):
    """
    Scraper para o SENAI-SP (sp.senai.br/noticias).
    Extrai notícias de inovação, hackathons, cursos e chamadas tecnológicas, enriquecendo o corpo completo.
    """

    @property
    def nome_fonte(self) -> str:
        return "SENAI"

    def coletar(self) -> List[ItemBrutoEdital]:
        url = "https://www.sp.senai.br/noticias"
        print(f"[{self.nome_fonte}] Consultando portal SENAI-SP: {url} ...")
        itens: List[ItemBrutoEdital] = []
        links_vistos = set()

        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15, verify=False)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                texto = a.get_text(" ", strip=True)

                if '/noticia/' not in href or len(texto) < 20:
                    continue
                if not href.startswith('http'):
                    href = f"https://www.sp.senai.br{href}" if href.startswith('/') else f"https://www.sp.senai.br/{href}"

                if href in links_vistos:
                    continue

                data_pub = "Não informada"
                m_data = re.match(r'^(\d{2}/\d{2}/\d{4})\s+(.*)', texto)
                if m_data:
                    data_pub = m_data.group(1)
                    resto = m_data.group(2)
                else:
                    resto = texto

                partes = re.split(r'\s*Descri[cç][aã]o\s*', resto)
                titulo = partes[0].strip()
                descricao = partes[1].strip() if (len(partes) > 1 and partes[1].strip()) else titulo

                if eh_item_ruido_ou_encerrado(titulo, href, descricao):
                    continue

                links_vistos.add(href)
                itens.append(ItemBrutoEdital(
                    titulo=titulo[:200],
                    descricao=descricao[:1500],
                    instituicao=self.nome_fonte,
                    link=href,
                    vigencia_inicio=data_pub,
                    prazo_proposto=_extrair_prazo(descricao),
                    categorias="SENAI-SP - Editais, Cursos e Inovação Tecnológica"
                ))
        except Exception as e:
            print(f"[{self.nome_fonte}] Erro ao acessar {url}: {e}")

        itens = enriquecer_itens_via_html(itens, headers=DEFAULT_HEADERS, max_itens=12)
        print(f"[{self.nome_fonte}] Coleta concluída: {len(itens)} itens encontrados.")
        return itens


class SesiScraper(BaseScraper):
    """
    Scraper para o SESI-SP (sesisp.org.br/noticias).
    Extrai chamadas, competições educacionais/robótica e projetos de inovação, filtrando notícias de esporte.
    """

    @property
    def nome_fonte(self) -> str:
        return "SESI"

    def coletar(self) -> List[ItemBrutoEdital]:
        url = "https://www.sesisp.org.br/noticias"
        print(f"[{self.nome_fonte}] Consultando portal SESI-SP: {url} ...")
        itens: List[ItemBrutoEdital] = []
        links_vistos = set()

        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15, verify=False)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                texto = a.get_text(" ", strip=True)

                if '/noticia/' not in href or len(texto) < 20:
                    continue
                if not href.startswith('http'):
                    href = f"https://www.sesisp.org.br{href}" if href.startswith('/') else f"https://www.sesisp.org.br/{href}"

                if href in links_vistos:
                    continue

                data_pub = "Não informada"
                m_data = re.match(r'^(\d{2}/\d{2}/\d{4})\s+(.*)', texto)
                if m_data:
                    data_pub = m_data.group(1)
                    resto = m_data.group(2)
                else:
                    resto = texto

                partes = re.split(r'\s*Descri[cç][aã]o\s*', resto)
                titulo = partes[0].strip()
                descricao = partes[1].strip() if (len(partes) > 1 and partes[1].strip()) else titulo

                if eh_item_ruido_ou_encerrado(titulo, href, descricao):
                    continue

                links_vistos.add(href)
                itens.append(ItemBrutoEdital(
                    titulo=titulo[:200],
                    descricao=descricao[:1500],
                    instituicao=self.nome_fonte,
                    link=href,
                    vigencia_inicio=data_pub,
                    prazo_proposto=_extrair_prazo(descricao),
                    categorias="SESI-SP - Educação, Robótica e Inovação"
                ))
        except Exception as e:
            print(f"[{self.nome_fonte}] Erro ao acessar {url}: {e}")

        itens = enriquecer_itens_via_html(itens, headers=DEFAULT_HEADERS, max_itens=10)
        print(f"[{self.nome_fonte}] Coleta concluída: {len(itens)} itens encontrados.")
        return itens


class FiGroupScraper(BaseScraper):
    """
    Scraper para o FI Group (antigo financiamentodainovacao.com.br/editais/).
    Nota Técnica: O domínio antigo redireciona (301) para https://www.fi-groupbr.com/pt/servico/financiamentos,
    que é uma landing page corporativa estática, enquanto os editais detalhados foram migrados para a plataforma
    fechada FI Connect (https://connect.fi-group.com/), que exige login corporativo.
    """

    @property
    def nome_fonte(self) -> str:
        return "FIGROUP"

    @property
    def habilitado(self) -> bool:
        return False

    def coletar(self) -> List[ItemBrutoEdital]:
        url = "https://www.financiamentodainovacao.com.br/editais/"
        print(f"[{self.nome_fonte}] Consultando {url} ...")
        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15, verify=False)
            print(f"[{self.nome_fonte}] Redirecionado para {resp.url} (status {resp.status_code}).")
            print(f"[{self.nome_fonte}] Aviso: O agregador público foi substituído pelo portal autenticado FI Connect (https://connect.fi-group.com/).")
        except Exception as e:
            print(f"[{self.nome_fonte}] Erro ao acessar {url}: {e}")
        return []


class FundepScraper(BaseScraper):
    """
    Scraper para a FUNDEP (UFMG).
    Nota Técnica: O portal principal (fundep.ufmg.br) não lista editais diretamente no HTML (direciona para Gupy/Concursos),
    e o Portal de Compras (portaldecompras.fundep.ufmg.br) utiliza controles ASP.NET WebForms (__doPostBack) com sessão.
    """

    @property
    def nome_fonte(self) -> str:
        return "FUNDEP"

    @property
    def habilitado(self) -> bool:
        return False

    def coletar(self) -> List[ItemBrutoEdital]:
        url = "https://portaldecompras.fundep.ufmg.br/Publico/ConsultarGruposAtivos.aspx"
        print(f"[{self.nome_fonte}] Consultando Portal de Compras FUNDEP: {url} ...")
        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15, verify=False)
            resp.raise_for_status()
            print(f"[{self.nome_fonte}] Aviso: Página utiliza ASP.NET WebForms (__doPostBack) sem listagem direta de editais de fomento em GET simples.")
        except Exception as e:
            print(f"[{self.nome_fonte}] Erro ao acessar {url}: {e}")
        return []


class DesenvolveSpScraper(BaseScraper):
    """
    Scraper para a Desenvolve SP (desenvolvesp.com.br).
    Nota Técnica: O servidor bloqueia requisições automatizadas com HTTP 403 Forbidden (WAF / Cloudflare).
    """

    @property
    def nome_fonte(self) -> str:
        return "DESENVOLVE SP"

    @property
    def habilitado(self) -> bool:
        return False

    def coletar(self) -> List[ItemBrutoEdital]:
        url = "https://www.desenvolvesp.com.br/"
        print(f"[{self.nome_fonte}] Consultando {url} ...")
        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15, verify=False)
            if resp.status_code == 403:
                print(f"[{self.nome_fonte}] Bloqueado por WAF/Cloudflare (HTTP 403 Forbidden).")
                return []
            resp.raise_for_status()
        except Exception as e:
            print(f"[{self.nome_fonte}] Erro ao acessar {url}: {e}")
        return []
