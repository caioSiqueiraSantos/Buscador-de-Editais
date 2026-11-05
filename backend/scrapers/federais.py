# backend/scrapers/federais.py
"""
Scrapers para órgãos e agências de fomento federais / nacionais:
- CNPq (Conselho Nacional de Desenvolvimento Científico e Tecnológico)
- CAPES (Coordenação de Aperfeiçoamento de Pessoal de Nível Superior)
- MCTI (Ministério da Ciência, Tecnologia e Inovação)
- EMBRAPII (Empresa Brasileira de Pesquisa e Inovação Industrial)
- BNDES (Banco Nacional de Desenvolvimento Econômico e Social)
"""

import re
import requests
import urllib3
from typing import List
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper, ItemBrutoEdital

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


def _extrair_prazo_texto(texto: str) -> str:
    if not texto:
        return "Não informado"
    m = re.search(
        r'(?:inscri[cç][oõ]es\s*(?:v[aã]o\s*)?at[eé]|prazo|submiss[aã]o|at[eé])\s*:?\s*(\d{1,2}[\/\-\.]\d{1,2}(?:[\/\-\.]\d{2,4})?)',
        texto,
        re.IGNORECASE
    )
    if m:
        return m.group(1)
    return "Não informado"


class CnpqScraper(BaseScraper):
    """
    Scraper para o portal oficial do CNPq (gov.br/cnpq).
    Coleta chamadas abertas para submissão e chamadas destacadas na página principal.
    """

    @property
    def nome_fonte(self) -> str:
        return "CNPq"

    def coletar(self) -> List[ItemBrutoEdital]:
        urls = [
            "https://www.gov.br/cnpq/pt-br/chamadas/abertas-para-submissao",
            "https://www.gov.br/cnpq/pt-br"
        ]
        itens: List[ItemBrutoEdital] = []
        links_vistos = set()

        for url in urls:
            print(f"[{self.nome_fonte}] Consultando página de chamadas: {url} ...")
            try:
                resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15, verify=False)
                resp.raise_for_status()
            except Exception as e:
                print(f"[{self.nome_fonte}] Erro ao acessar {url}: {e}")
                continue

            soup = BeautifulSoup(resp.text, 'html.parser')
            container_principal = soup.find(id='content-core') or soup.find('main') or soup

            for a in container_principal.find_all('a', href=True):
                href = a['href'].strip()
                titulo = a.get_text(" ", strip=True)

                if not href.startswith('http'):
                    href = f"https://www.gov.br{href}" if href.startswith('/') else f"https://www.gov.br/cnpq/pt-br/{href}"

                # Ignora links de compartilhamento social, anexos isolados ou navegação
                if any(s in href.lower() for s in ['facebook.com', 'twitter.com', 'linkedin.com', 'whatsapp.com', 'search?', 'resolveuid']):
                    continue
                if any(titulo.lower().startswith(p) for p in ['compartilhe', 'link para copiar', 'anexo ', 'territórios priorizados', 'busca de chamadas', 'chamadas abertas', 'chamadas em análise', 'resultados', 'normas']):
                    continue
                if titulo.lower() == 'chamada' and href.lower().endswith('.pdf'):
                    continue

                eh_chamada = (
                    '/chamadas/todas-as-chamadas/' in href.lower()
                    or ('/noticias/' in href.lower() and ('chamada' in titulo.lower() or 'edital' in titulo.lower() or 'bolsa' in titulo.lower()))
                )
                if not eh_chamada or len(titulo) < 20:
                    continue

                # Remove prefixo "Saiba mais sobre " se presente
                titulo_limpo = re.sub(r'^Saiba mais sobre\s+', '', titulo, flags=re.IGNORECASE).strip()

                if href in links_vistos:
                    continue
                links_vistos.add(href)

                bloco_pai = a.find_parent(['div', 'li', 'article'])
                contexto = bloco_pai.get_text(" ", strip=True) if bloco_pai else titulo_limpo
                prazo = _extrair_prazo_texto(contexto)

                itens.append(ItemBrutoEdital(
                    titulo=titulo_limpo,
                    descricao=contexto[:1500],
                    instituicao=self.nome_fonte,
                    link=href,
                    prazo_proposto=prazo,
                    categorias="CNPq - Chamadas Públicas e Fomento"
                ))

        print(f"[{self.nome_fonte}] Coleta concluída: {len(itens)} chamadas encontradas.")
        return itens


class CapesScraper(BaseScraper):
    """
    Scraper para o portal de Editais e Programas Estratégicos da CAPES (gov.br/capes).
    """

    @property
    def nome_fonte(self) -> str:
        return "CAPES"

    def coletar(self) -> List[ItemBrutoEdital]:
        url = "https://www.gov.br/capes/pt-br/assuntos/editais-e-resultados-capes"
        print(f"[{self.nome_fonte}] Consultando página de editais: {url} ...")
        itens: List[ItemBrutoEdital] = []
        links_vistos = set()

        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15, verify=False)
            resp.raise_for_status()
        except Exception as e:
            print(f"[{self.nome_fonte}] Erro ao acessar {url}: {e}")
            return []

        soup = BeautifulSoup(resp.text, 'html.parser')
        main = soup.find(id='content-core') or soup.find('main') or soup

        for a in main.find_all('a', href=True):
            href = a['href'].strip()
            titulo = a.get_text(" ", strip=True)

            if not href.startswith('http'):
                href = f"https://www.gov.br{href}" if href.startswith('/') else f"https://www.gov.br/capes/pt-br/{href}"

            if len(titulo) < 15:
                continue
            if any(s in href.lower() for s in ['facebook.com', 'twitter.com', 'linkedin.com', 'whatsapp.com', '#']):
                continue

            eh_relevante = any(
                k in (titulo + " " + href).lower()
                for k in ['edital', 'chamada', 'programa', 'bolsa', 'cooperacao', 'pesquisa']
            )
            if not eh_relevante:
                continue

            if href in links_vistos:
                continue
            links_vistos.add(href)

            pai = a.find_parent(['li', 'div', 'p'])
            contexto = pai.get_text(" ", strip=True) if pai else titulo

            itens.append(ItemBrutoEdital(
                titulo=titulo,
                descricao=contexto[:1500],
                instituicao=self.nome_fonte,
                link=href,
                prazo_proposto=_extrair_prazo_texto(contexto),
                categorias="CAPES - Editais e Programas de Pós-Graduação/Pesquisa"
            ))

        print(f"[{self.nome_fonte}] Coleta concluída: {len(itens)} editais/programas encontrados.")
        return itens


class MctiScraper(BaseScraper):
    """
    Scraper para o Ministério da Ciência, Tecnologia e Inovação (MCTI).
    Monitora notícias de chamadas/prêmios/seleções e páginas de fomento do MCTI.
    """

    @property
    def nome_fonte(self) -> str:
        return "MCTI"

    def coletar(self) -> List[ItemBrutoEdital]:
        urls = [
            "https://www.gov.br/mcti/pt-br/acompanhe-o-mcti/noticias",
            "https://www.gov.br/mcti/pt-br"
        ]
        itens: List[ItemBrutoEdital] = []
        links_vistos = set()

        for url in urls:
            print(f"[{self.nome_fonte}] Consultando portal MCTI: {url} ...")
            try:
                resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15, verify=False)
                resp.raise_for_status()
            except Exception as e:
                print(f"[{self.nome_fonte}] Erro ao acessar {url}: {e}")
                continue

            soup = BeautifulSoup(resp.text, 'html.parser')
            main = soup.find(id='content-core') or soup.find('main') or soup
            for a in main.find_all('a', href=True):
                href = a['href'].strip()
                titulo = a.get_text(" ", strip=True)

                if not href.startswith('http'):
                    href = f"https://www.gov.br{href}" if href.startswith('/') else f"https://www.gov.br/mcti/pt-br/{href}"

                if 'gov.br/mcti/' not in href or len(titulo) < 25:
                    continue
                if any(s in href.lower() for s in ['search?', '#', 'facebook.com', 'twitter.com', 'whatsapp.com']):
                    continue
                if href.rstrip('/') == 'https://www.gov.br/mcti/pt-br':
                    continue

                # Filtra publicações datadas e chamadas/editais do MCTI
                eh_oportunidade = (
                    re.search(r'/noticias/202\d/', href.lower()) is not None
                    or any(w in titulo.lower() for w in ['edital', 'chamada', 'selecion', 'prêmio', 'premio', 'subven', 'fndct', 'bolsa'])
                )
                if not eh_oportunidade:
                    continue

                if href in links_vistos:
                    continue
                links_vistos.add(href)

                pai = a.find_parent(['article', 'li', 'div'])
                contexto = pai.get_text(" ", strip=True) if pai else titulo

                itens.append(ItemBrutoEdital(
                    titulo=titulo,
                    descricao=contexto[:1500],
                    instituicao=self.nome_fonte,
                    link=href,
                    prazo_proposto=_extrair_prazo_texto(contexto),
                    categorias="MCTI - Fomento e Políticas de CT&I"
                ))

        print(f"[{self.nome_fonte}] Coleta concluída: {len(itens)} itens encontrados.")
        return itens


class EmbrapiiScraper(BaseScraper):
    """
    Scraper para a EMBRAPII (Empresa Brasileira de Pesquisa e Inovação Industrial).
    Combina a API WP-JSON de publicações/chamadas com a listagem de Chamadas Públicas da página de Transparência.
    """

    @property
    def nome_fonte(self) -> str:
        return "EMBRAPII"

    def coletar(self) -> List[ItemBrutoEdital]:
        itens: List[ItemBrutoEdital] = []
        links_vistos = set()

        # 1. Consulta WP-JSON API para notícias recentes de chamadas e parcerias
        url_api = "https://embrapii.org.br/wp-json/wp/v2/posts?per_page=15"
        print(f"[{self.nome_fonte}] Consultando API WP-JSON: {url_api} ...")
        try:
            resp = requests.get(url_api, headers=DEFAULT_HEADERS, timeout=15, verify=False)
            if resp.status_code == 200:
                posts = resp.json()
                for post in posts:
                    titulo = _limpar_html(post.get('title', {}).get('rendered', ''))
                    link = post.get('link', '').strip()
                    resumo = _limpar_html(post.get('excerpt', {}).get('rendered', '')) or _limpar_html(post.get('content', {}).get('rendered', ''))
                    data_pub = (post.get('date') or '')[:10]

                    if not titulo or not link or link in links_vistos:
                        continue
                    links_vistos.add(link)

                    itens.append(ItemBrutoEdital(
                        titulo=titulo,
                        descricao=resumo[:1500] if resumo else titulo,
                        instituicao=self.nome_fonte,
                        link=link,
                        vigencia_inicio=data_pub or "Não informada",
                        prazo_proposto=_extrair_prazo_texto(resumo),
                        categorias="EMBRAPII - Inovação Industrial"
                    ))
        except Exception as e:
            print(f"[{self.nome_fonte}] Aviso ao consultar WP-JSON: {e}")

        # 2. Consulta listagem de Chamadas Públicas na página inicial e Transparência
        for url_html in ["https://embrapii.org.br/", "https://embrapii.org.br/transparencia/"]:
            print(f"[{self.nome_fonte}] Consultando chamadas públicas em: {url_html} ...")
            try:
                resp = requests.get(url_html, headers=DEFAULT_HEADERS, timeout=15, verify=False)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, 'html.parser')

                for a in soup.find_all('a', href=True):
                    href = a['href'].strip()
                    if '/chamadas-publicas/' not in href or href.rstrip('/').endswith('/chamadas-publicas'):
                        continue
                    if not href.startswith('http'):
                        href = f"https://embrapii.org.br{href}" if href.startswith('/') else f"https://embrapii.org.br/{href}"

                    if href in links_vistos:
                        continue

                    texto_link = a.get_text(" ", strip=True)
                    pai = a.find_parent(['div', 'li', 'tr', 'article'])
                    contexto = pai.get_text(" ", strip=True) if pai else texto_link

                    # Quando o texto do botão é 'Ver documentos', extrai o título do contexto ou do slug da URL
                    if not texto_link or texto_link.lower() in ['ver documentos', 'saiba mais', 'acesse']:
                        titulo_limpo = re.sub(r'\s*Ver documentos.*$', '', contexto, flags=re.IGNORECASE).strip()
                        if len(titulo_limpo) < 10 or len(titulo_limpo) > 180:
                            slug = href.rstrip('/').split('/')[-1]
                            titulo_limpo = slug.replace('-', ' ').upper()
                    else:
                        titulo_limpo = texto_link

                    links_vistos.add(href)
                    itens.append(ItemBrutoEdital(
                        titulo=titulo_limpo,
                        descricao=contexto[:1500] if contexto else titulo_limpo,
                        instituicao=self.nome_fonte,
                        link=href,
                        prazo_proposto=_extrair_prazo_texto(contexto),
                        categorias="EMBRAPII - Chamadas Públicas"
                    ))
            except Exception as e:
                print(f"[{self.nome_fonte}] Erro ao acessar {url_html}: {e}")

        print(f"[{self.nome_fonte}] Coleta concluída: {len(itens)} itens encontrados.")
        return itens


class BndesScraper(BaseScraper):
    """
    Scraper para o BNDES (Portal Dados Abertos CKAN e Portal Institucional).
    Nota Técnica: As conexões automatizadas para dadosabertos.bndes.gov.br e www.bndes.gov.br
    frequentemente sofrem Read Timeout na porta 443 por regras de firewall/anti-bot do BNDES.
    """

    @property
    def nome_fonte(self) -> str:
        return "BNDES"

    @property
    def habilitado(self) -> bool:
        return False

    def coletar(self) -> List[ItemBrutoEdital]:
        url_ckan = "https://dadosabertos.bndes.gov.br/api/3/action/package_search?q=chamada"
        print(f"[{self.nome_fonte}] Consultando API CKAN: {url_ckan} ...")
        itens: List[ItemBrutoEdital] = []

        try:
            resp = requests.get(url_ckan, headers=DEFAULT_HEADERS, timeout=12, verify=False)
            resp.raise_for_status()
            dados = resp.json()
            resultados = dados.get('result', {}).get('results', [])
            for pkg in resultados:
                titulo = pkg.get('title') or pkg.get('name') or 'Conjunto de Dados BNDES'
                notas = pkg.get('notes') or titulo
                name_slug = pkg.get('name', '')
                link = f"https://dadosabertos.bndes.gov.br/dataset/{name_slug}"
                itens.append(ItemBrutoEdital(
                    titulo=titulo,
                    descricao=notas[:1500],
                    instituicao=self.nome_fonte,
                    link=link,
                    categorias="BNDES - Dados Abertos / Chamadas"
                ))
        except Exception as e:
            print(f"[{self.nome_fonte}] Falha/Timeout ao conectar ao portal BNDES: {e}")

        return itens
