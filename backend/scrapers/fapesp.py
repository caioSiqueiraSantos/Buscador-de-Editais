# backend/scrapers/fapesp.py
import re
import requests
from typing import List
from bs4 import BeautifulSoup
from scrapers.base import (
    BaseScraper,
    ItemBrutoEdital,
    eh_item_ruido_ou_encerrado,
    extrair_prazo_universal,
    enriquecer_itens_via_html,
)

class FapespScraper(BaseScraper):
    """
    Scraper baseado em Web Scraping (HTML) em 2 etapas para o portal de Chamadas de Propostas da FAPESP.
    Filtra manuais institucionais fixos e enriquece o prazo e o texto completo visitando as páginas das chamadas.
    """

    @property
    def nome_fonte(self) -> str:
        return "FAPESP"

    def coletar(self) -> List[ItemBrutoEdital]:
        url_alvo = "https://fapesp.br/chamadas"
        print(f"[{self.nome_fonte}] Acessando portal de chamadas via Web Scraping: {url_alvo} ...")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        try:
            resp = requests.get(url_alvo, headers=headers, timeout=20)
            resp.raise_for_status()
            html_content = resp.content.decode('utf-8', errors='replace')
        except Exception as e:
            print(f"[{self.nome_fonte}] Erro ao carregar página da FAPESP: {e}")
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        itens_normalizados: List[ItemBrutoEdital] = []
        links_vistos = set()

        # Encontra todos os links de chamadas recentes no portal (IDs >= 16500 correspondem a chamadas de 2025/2026+)
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            titulo = a.get_text(separator=' ', strip=True)

            if not href.startswith('http'):
                if href.startswith('/'):
                    href = f"https://fapesp.br{href}"
                else:
                    href = f"https://fapesp.br/{href}"

            m_id = re.search(r'fapesp\.br/(\d+)', href)
            if m_id:
                num_id = int(m_id.group(1))
                # IDs antigos (< 16500) são páginas institucionais fixas ("Como Submeter Propostas", manuais de bolsas)
                if num_id < 16500 and not any(w in titulo.lower() for w in ['chamada', 'edital', '2025', '2026', '2027']):
                    continue
            elif 'chamada' not in href.lower():
                continue

            if len(titulo) < 15 or eh_item_ruido_ou_encerrado(titulo, href):
                continue
            if any(p in titulo.lower() for p in [
                'jovem pesquisador - fase 2', 'ciência para todos', 'codigo de etica',
                'código de ética', 'assessoria científica', 'assessoria cientifica'
            ]):
                continue

            if href in links_vistos:
                continue
            links_vistos.add(href)

            container = a.find_parent('li') or a.find_parent('p') or a.find_parent('div')
            texto_contexto = container.get_text(separator='\n', strip=True) if container else titulo

            prazo = extrair_prazo_universal(texto_contexto)

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

        # Etapa 2: Enriquece texto completo e prazo de submissão nas páginas internas das chamadas
        itens_normalizados = enriquecer_itens_via_html(itens_normalizados, headers=headers, max_itens=45)

        print(f"[{self.nome_fonte}] Scraping concluído com sucesso: {len(itens_normalizados)} chamadas abertas e enriquecidas.")
        return itens_normalizados
