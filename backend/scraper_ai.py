# backend/scraper_ai.py
"""
Ponto de Entrada Principal para Coleta e Triagem de Editais.
Orquestra os scrapers modulares (FINEP, FAPESP, etc.) através da pipeline central de IA.

Uso:
  python scraper_ai.py               # Executa todas as fontes registradas
  python scraper_ai.py --fonte finep # Executa apenas a fonte especificada
  python scraper_ai.py --listar      # Lista todas as fontes disponíveis
"""

import sys
import argparse
from typing import List

# Importa a esteira central unificada
from pipeline import (
    init_db,
    obter_temas_db,
    obter_exemplos_aprendizado,
    expurgar_editais_divergentes_banco,
    executar_scraper,
    executar_pipeline_completa,
    # Re-exportações para manter compatibilidade retroativa
    Oportunidade,
    analisar_com_ia,
    analisar_item_com_ia,
    salvar_no_banco,
    salvar_recusado_prefiltro,
    verificar_divergencia_sumaria,
    contem_palavra_chave,
    oportunidade_ja_existe
)

# Importa os scrapers modulares
from scrapers import (
    SCRAPERS_REGISTRY,
    listar_scrapers,
    obter_scraper
)

def executar_coleta_geral(fontes_selecionadas: List[str] = None):
    """Executa a rotina de auditoria e coleta das fontes registradas."""
    resultado = executar_pipeline_completa(fontes_selecionadas=fontes_selecionadas)
    print("\n🏁 Processo de coleta e triagem finalizado para todas as fontes.")
    print(f"📊 Total de itens de Alta Aderência encontrados nesta rodada: {resultado['total_alta_aderencia']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orquestrador Modular de Coleta e Triagem de Editais com IA")
    parser.add_argument("--fonte", type=str, help="Executa apenas a fonte especificada (ex: finep, fapesp, cnpq)")
    parser.add_argument("--listar", action="store_true", help="Lista todas as fontes cadastradas no catálogo")
    parser.add_argument(
        "--testar-coleta",
        action="store_true",
        help="Executa apenas a coleta bruta (dry-run) para validar retorno, sem gravar no banco e sem chamar a API do Gemini"
    )
    args = parser.parse_args()

    if args.listar:
        print("\n📚 Fontes registradas no catálogo de scrapers:")
        for chave, s in SCRAPERS_REGISTRY.items():
            status = "Ativo" if s.habilitado else "Desabilitado"
            print(f"  • {chave.upper():<15} -> {s.__class__.__name__:<22} [{status}]")
        sys.exit(0)

    if args.testar_coleta:
        alvos = [obter_scraper(args.fonte)] if args.fonte else list(SCRAPERS_REGISTRY.values())
        alvos = [a for a in alvos if a is not None]
        if not alvos:
            print(f"⚠️ Fonte '{args.fonte}' não encontrada no catálogo.")
            sys.exit(1)

        print("\n🧪 MODO TESTE DE COLETA (DRY-RUN: Sem escrita no DB e sem chamadas ao Gemini)")
        for s in alvos:
            print(f"\n--------------------------------------------------------")
            print(f"🔍 Testando Fonte: {s.nome_fonte} ({s.__class__.__name__}) | Habilitado={s.habilitado}")
            itens = s.coletar()
            print(f"✅ Total capturado: {len(itens)} itens")
            for idx, it in enumerate(itens[:3], 1):
                print(f"   [{idx}] Título: {it.titulo[:90]}")
                print(f"       Link:   {it.link}")
                print(f"       Prazo:  {it.prazo_proposto} | Categoria: {it.categorias}")
        sys.exit(0)

    fontes = [args.fonte] if args.fonte else None
    executar_coleta_geral(fontes)
