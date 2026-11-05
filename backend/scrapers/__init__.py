# backend/scrapers/__init__.py
from typing import Dict, List, Optional
from scrapers.base import BaseScraper, ItemBrutoEdital
from scrapers.finep import FinepScraper
from scrapers.fapesp import FapespScraper
from scrapers.federais import (
    CnpqScraper,
    CapesScraper,
    MctiScraper,
    EmbrapiiScraper,
    BndesScraper,
)
from scrapers.faps_estaduais import (
    FacepeScraper,
    FapacScraper,
    FapdfScraper,
    FapeamScraper,
    FapematScraper,
    FapemigScraper,
    FapergsScraper,
    FaperjScraper,
    FapescScraper,
    FundectScraper,
    FuntacScraper,
)
from scrapers.associacoes_sistema_s import (
    AnpeiScraper,
    AnprotecScraper,
    SenaiScraper,
    SesiScraper,
    FiGroupScraper,
    FundepScraper,
    DesenvolveSpScraper,
)
from scrapers.internacionais import (
    BidScraper,
    CafScraper,
)

# Catálogo centralizado das 27 fontes mapeadas
SCRAPERS_REGISTRY: Dict[str, BaseScraper] = {
    "finep": FinepScraper(),
    "fapesp": FapespScraper(),
    "anpei": AnpeiScraper(),
    "anprotec": AnprotecScraper(),
    "bid": BidScraper(),
    "bndes": BndesScraper(),
    "caf": CafScraper(),
    "capes": CapesScraper(),
    "cnpq": CnpqScraper(),
    "desenvolve_sp": DesenvolveSpScraper(),
    "embrapii": EmbrapiiScraper(),
    "facepe": FacepeScraper(),
    "fapac": FapacScraper(),
    "fapdf": FapdfScraper(),
    "fapeam": FapeamScraper(),
    "fapemat": FapematScraper(),
    "fapemig": FapemigScraper(),
    "fapergs": FapergsScraper(),
    "faperj": FaperjScraper(),
    "fapesc": FapescScraper(),
    "figroup": FiGroupScraper(),
    "fundect": FundectScraper(),
    "fundep": FundepScraper(),
    "funtac": FuntacScraper(),
    "mcti": MctiScraper(),
    "senai": SenaiScraper(),
    "sesi": SesiScraper(),
}

def obter_scraper(nome: str) -> Optional[BaseScraper]:
    """Retorna a instância do scraper pelo identificador (case-insensitive)."""
    chave = nome.lower().strip().replace(" ", "_")
    return SCRAPERS_REGISTRY.get(chave)

def listar_scrapers() -> List[BaseScraper]:
    """Retorna a lista de todos os scrapers ativos registrados."""
    return [s for s in SCRAPERS_REGISTRY.values() if s.habilitado]

__all__ = [
    "BaseScraper",
    "ItemBrutoEdital",
    "FinepScraper",
    "FapespScraper",
    "CnpqScraper",
    "CapesScraper",
    "MctiScraper",
    "EmbrapiiScraper",
    "BndesScraper",
    "FacepeScraper",
    "FapacScraper",
    "FapdfScraper",
    "FapeamScraper",
    "FapematScraper",
    "FapemigScraper",
    "FapergsScraper",
    "FaperjScraper",
    "FapescScraper",
    "FundectScraper",
    "FuntacScraper",
    "AnpeiScraper",
    "AnprotecScraper",
    "SenaiScraper",
    "SesiScraper",
    "FiGroupScraper",
    "FundepScraper",
    "DesenvolveSpScraper",
    "BidScraper",
    "CafScraper",
    "SCRAPERS_REGISTRY",
    "obter_scraper",
    "listar_scrapers"
]
