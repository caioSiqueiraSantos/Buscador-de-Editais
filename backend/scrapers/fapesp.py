# backend/scrapers/fapesp.py
import re
import requests
from typing import List
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper, ItemBrutoEdital

class FapespScraper(BaseScraper):
    """
    Scraper baseado em Web Scraping (HTML) para o portal de Chamadas de Propostas da FAPESP.
    Demonstra a flexibilidade do padrão Adapter para fontes que não possuem API JSON.
    """

    @property
    def nome_fonte(self) -> str:
        return "FAPESP"

    def coletar(self) -> List[ItemBrutoEdital]:
        url_alvo = "https://fapesp.br/chamadas"
        print(f"[{self.nome_fonte}] Acessando portal de chamadas via Web Scraping: {url_alvo} ...")

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
            }
            resp = requests.get(url_alvo, headers=headers, timeout=20)
            resp.raise_for_status()
            # Força decodificação correta de caracteres em português
            html_content = resp.content.decode('utf-8', errors='replace')
        except Exception as e:
            print(f"[{self.nome_fonte}] Erro ao carregar página da FAPESP: {e}")
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        itens_normalizados: List[ItemBrutoEdital] = []
        links_vistos = set()

        # Encontra todos os links de chamadas no portal (padrão https://fapesp.br/<id_numerico>)
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            titulo = a.get_text(separator=' ', strip=True)

            # Filtra links válidos de chamadas da FAPESP com título substantivo
            if not href.startswith('http'):
                if href.startswith('/'):
                    href = f"https://fapesp.br{href}"
                else:
                    href = f"https://fapesp.br/{href}"

            eh_chamada = re.search(r'fapesp\.br/\d+', href) or ('chamada' in href.lower())
            if not eh_chamada or len(titulo) < 15:
                continue

            # Evita títulos que sejam apenas 'Saiba mais' ou menus genéricos
            if titulo.lower() in ['chamadas de propostas', 'saiba mais', 'leia mais', 'ver todas']:
                continue

            if href in links_vistos:
                continue
            links_vistos.add(href)

            # Tenta extrair metadados ao redor do link (prazo, modalidade, área)
            container = a.find_parent('li') or a.find_parent('p') or a.find_parent('div')
            texto_contexto = container.get_text(separator='\n', strip=True) if container else titulo

            prazo = "Não informado"
            match_prazo = re.search(r'(?:prazo|submiss[aã]o|data limite|at[eé])\s*(?:de submiss[aã]o)?\s*:?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})', texto_contexto, re.IGNORECASE)
            if match_prazo:
                prazo = match_prazo.group(1)

            categoria = "FAPESP - Fomento à Pesquisa"
            match_area = re.search(r'[ÁAáa]rea\s*:\s*([^\n\r]+)', texto_contexto)
            if match_area:
                categoria = match_area.group(1).strip()

            itens_normalizados.append(ItemBrutoEdital(
                titulo=titulo,
                descricao=texto_contexto[:1500],
                instituicao=self.nome_fonte,
                link=href,
                prazo_proposto=prazo,
                categorias=categoria
            ))

        print(f"[{self.nome_fonte}] Scraping concluído com sucesso: {len(itens_normalizados)} chamadas encontradas.")
        return itens_normalizados
