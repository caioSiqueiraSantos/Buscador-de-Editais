# backend/scrapers/base.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

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
