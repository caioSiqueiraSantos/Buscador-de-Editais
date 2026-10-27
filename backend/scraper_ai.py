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
    init_db()

    # 1. Higienização retroativa de oportunidades que possam ter sido salvas anteriormente
    print("\n🔍 Executando auditoria e higienização de oportunidades divergentes no banco...")
    expurgar_editais_divergentes_banco()

    # 2. Informações de temas e memória ativa
    temas = obter_temas_db()
    print(f"\n📌 Temas cadastrados no banco ({len(temas)}):")
    for t in temas:
        print(f"   • {t}")

    exemplos_pos, exemplos_neg = obter_exemplos_aprendizado(limite=4)
    print(f"\n🧠 Memória de Aprendizado Ativo carregada:")
    print(f"   • {len(exemplos_pos)} exemplos positivos de calibração humana")
    print(f"   • {len(exemplos_neg)} exemplos de falsos positivos descartados")

    # 3. Determina quais scrapers executar
    if fontes_selecionadas:
        scrapers_alvo = []
        for f in fontes_selecionadas:
            s = obter_scraper(f)
            if s:
                scrapers_alvo.append(s)
            else:
                print(f"⚠️ Fonte '{f}' não encontrada no catálogo de scrapers.")
    else:
        scrapers_alvo = listar_scrapers()

    if not scrapers_alvo:
        print("❌ Nenhum scraper válido para execução.")
        return

    print(f"\n🌐 Fontes ativas para esta rodada: {[s.nome_fonte for s in scrapers_alvo]}")

    for scraper in scrapers_alvo:
        try:
            executar_scraper(scraper)
        except Exception as e:
            print(f"❌ Erro crítico ao executar scraper [{scraper.nome_fonte}]: {e}")

    print("\n🏁 Processo de coleta e triagem finalizado para todas as fontes.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orquestrador Modular de Coleta e Triagem de Editais com IA")
    parser.add_argument("--fonte", type=str, help="Executa apenas a fonte especificada (ex: finep, fapesp)")
    parser.add_argument("--listar", action="store_true", help="Lista todas as fontes cadastradas no catálogo")
    args = parser.parse_args()

    if args.listar:
        print("\n📚 Fontes registradas no catálogo de scrapers:")
        for chave, s in SCRAPERS_REGISTRY.items():
            status = "Ativo" if s.habilitado else "Desabilitado"
            print(f"  • {chave.upper():<10} -> {s.__class__.__name__} [{status}]")
        sys.exit(0)

    fontes = [args.fonte] if args.fonte else None
    executar_coleta_geral(fontes)