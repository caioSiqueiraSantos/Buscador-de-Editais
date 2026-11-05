# backend/scrapers/internacionais.py
"""
Scrapers para Bancos e Organismos Multilaterais Internacionais:
- BID (Banco Interamericano de Desenvolvimento - iadb.org)
- CAF (Banco de Desenvolvimento da América Latina e Caribe - caf.com)
"""

import requests
import urllib3
from typing import List
from scrapers.base import BaseScraper, ItemBrutoEdital

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
}


class BidScraper(BaseScraper):
    """
    Scraper para o BID (Banco Interamericano de Desenvolvimento - Procurement).
    Nota Técnica: Os domínios www.iadb.org e projectprocurement.iadb.org possuem proteção
    WAF / Cloudflare / Akamai que retorna HTTP 403 Forbidden para requisições sem desafio JS de navegador.
    """

    @property
    def nome_fonte(self) -> str:
        return "BID"

    @property
    def habilitado(self) -> bool:
        return False

    def coletar(self) -> List[ItemBrutoEdital]:
        url = "https://projectprocurement.iadb.org/en/procurement-notices"
        print(f"[{self.nome_fonte}] Consultando portal de Procurement do BID: {url} ...")
        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15, verify=False)
            if resp.status_code == 403:
                print(f"[{self.nome_fonte}] Bloqueado por WAF/Bot Protection (HTTP 403 Forbidden).")
                return []
            resp.raise_for_status()
        except Exception as e:
            print(f"[{self.nome_fonte}] Erro ao acessar {url}: {e}")
        return []


class CafScraper(BaseScraper):
    """
    Scraper para o CAF (Banco de Desenvolvimento da América Latina e Caribe).
    Nota Técnica: O domínio www.caf.com bloqueia requisições HTTP diretas com HTTP 403 Forbidden (WAF/Cloudflare).
    """

    @property
    def nome_fonte(self) -> str:
        return "CAF"

    @property
    def habilitado(self) -> bool:
        return False

    def coletar(self) -> List[ItemBrutoEdital]:
        url = "https://www.caf.com/pt/sobre-a-caf/licitacoes/"
        print(f"[{self.nome_fonte}] Consultando portal de Licitações/Convocatórias CAF: {url} ...")
        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15, verify=False)
            if resp.status_code == 403:
                print(f"[{self.nome_fonte}] Bloqueado por WAF/Cloudflare (HTTP 403 Forbidden).")
                return []
            resp.raise_for_status()
        except Exception as e:
            print(f"[{self.nome_fonte}] Erro ao acessar {url}: {e}")
        return []

