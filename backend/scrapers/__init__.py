# backend/scrapers/__init__.py
from typing import Dict, List, Optional
from scrapers.base import BaseScraper, ItemBrutoEdital
from scrapers.finep import FinepScraper
from scrapers.fapesp import FapespScraper

# Catálogo centralizado de scrapers registrados
SCRAPERS_REGISTRY: Dict[str, BaseScraper] = {
    "finep": FinepScraper(),
    "fapesp": FapespScraper()
}

def obter_scraper(nome: str) -> Optional[BaseScraper]:
    """Retorna a instância do scraper pelo identificador (case-insensitive)."""
    return SCRAPERS_REGISTRY.get(nome.lower().strip())

def listar_scrapers() -> List[BaseScraper]:
    """Retorna a lista de todos os scrapers ativos registrados."""
    return [s for s in SCRAPERS_REGISTRY.values() if s.habilitado]

__all__ = [
    "BaseScraper",
    "ItemBrutoEdital",
    "FinepScraper",
    "FapespScraper",
    "SCRAPERS_REGISTRY",
    "obter_scraper",
    "listar_scrapers"
]
