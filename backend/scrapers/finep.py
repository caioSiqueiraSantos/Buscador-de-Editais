# backend/scrapers/finep.py
import requests
from typing import List, Tuple
from scrapers.base import BaseScraper, ItemBrutoEdital

ANO_MINIMO_RELEVANTE = 2025  # Ignora editais históricos antigos para economizar tokens

class FinepScraper(BaseScraper):
    """
    Scraper específico para a API REST pública da FINEP.
    Extrai oportunidades abertas e normaliza para o contrato ItemBrutoEdital.
    """

    @property
    def nome_fonte(self) -> str:
        return "FINEP"

    def _edital_eh_muito_antigo(self, item: dict, ano_minimo: int = ANO_MINIMO_RELEVANTE) -> Tuple[bool, str]:
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

    def _consumir_api_finep(self, url: str) -> list:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            dados_json = response.json()
            return dados_json.get('items', [])
        except Exception as e:
            print(f"[{self.nome_fonte}] Erro ao acessar a API: {e}")
            return []

    def coletar(self) -> List[ItemBrutoEdital]:
        url_alvo = "https://www.finep.gov.br/o/c/chamadapublicas?sort=dataDePublicacao:desc"
        print(f"[{self.nome_fonte}] Consultando API REST: {url_alvo} ...")
        
        itens_brutos = self._consumir_api_finep(url_alvo)
        if not itens_brutos:
            print(f"[{self.nome_fonte}] Nenhum item retornado pela API da FINEP.")
            return []

        print(f"[{self.nome_fonte}] {len(itens_brutos)} itens obtidos. Filtrando pré-requisitos temporais e de situação...")
        itens_normalizados: List[ItemBrutoEdital] = []

        for item in itens_brutos:
            titulo = (item.get('titulo') or 'Item sem título').strip()
            item_id = item.get('id', '')
            url_publica = f"https://www.finep.gov.br/e/chamada-publica/222684/{item_id}"

            # 1. Filtro Temporal da fonte
            eh_antigo, motivo_antigo = self._edital_eh_muito_antigo(item)
            if eh_antigo:
                # Opcional: log verbose
                continue

            # 2. Filtro de Situação (exclui encerrados)
            situacao = item.get('situacao') or {}
            situacao_key = str(situacao.get('key', '')).lower().strip()
            if situacao_key in ['encerrado', 'encerrada'] or situacao_key.startswith('encerrad'):
                continue

            # 3. Categorias e taxonomias da FINEP
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
            vigencia_inicio = item.get('vigenciaInicio') or "Não informada"
            vigencia_fim = item.get('vigenciaFim') or "Não informada"
            prazo_proposto = item.get('prazoProposto') or "Não informado"
            descricao_limpa = (item.get('descricaoRawText') or item.get('descricao') or '').strip()

            itens_normalizados.append(ItemBrutoEdital(
                titulo=titulo,
                descricao=descricao_limpa,
                instituicao=self.nome_fonte,
                link=url_publica,
                prazo_proposto=prazo_proposto,
                vigencia_inicio=vigencia_inicio,
                vigencia_fim=vigencia_fim,
                categorias=categorias_str,
                dados_adicionais={"item_id": item_id, "situacao": situacao_key}
            ))

        print(f"[{self.nome_fonte}] Coleta concluída com sucesso: {len(itens_normalizados)} itens válidos para processamento.")
        return itens_normalizados
