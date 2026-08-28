# backend/scraper_ai.py
import os
import sqlite3
import json
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Temas de interesse do Metrô
TEMAS = "Mobilidade, transporte sobre trilhos, MaaS, hidrogênio verde, blockchain, materiais avançados, energias renováveis, Indústria 4.0, inteligência artificial."

def extrair_texto_pagina(url):
    """Simula o scraping de uma página genérica de edital."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Pega o texto principal (em uma PoC real, você ajustaria as tags div/main de cada site)
        return soup.get_text(separator=' ', strip=True)[:4000] # Limita a 4000 caracteres para a API
    except Exception as e:
        print(f"Erro ao raspar {url}: {e}")
        return ""

def analisar_com_ia(texto_bruto, link_original):
    """Envia o texto para o Gemini forçando a saída em JSON."""
    
    prompt = f"""
    Você é um analista de inovação de uma companhia de Metrô.
    Analise o texto extraído de uma página de fomento/eventos e extraia as informações em formato JSON.
    
    Regras de Negócio:
    - Avalie a aderência (Alto, Médio, Baixo) aos seguintes temas do Metrô: {TEMAS}.
    - Categoria deve ser: Edital, Evento, Curso ou Parceria.
    - O resumo deve ter no máximo 3 linhas.
    
    O JSON de saída deve ter EXATAMENTE as seguintes chaves:
    "titulo", "instituicao", "categoria", "resumo", "tematica", "prazo" (use "Não informado" se não achar), "aderencia", "link".
    
    Texto bruto:
    {texto_bruto}
    
    Link original para incluir no JSON: {link_original}
    """
    
    # O modelo 1.5 Flash é rápido, barato e suporta JSON mode
    model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
    response = model.generate_content(prompt)
    
    return json.loads(response.text)

def salvar_no_banco(dados_json):
    conn = sqlite3.connect('oportunidades.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO oportunidades (titulo, instituicao, categoria, resumo, tematica, prazo, aderencia, link)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        dados_json.get('titulo'), dados_json.get('instituicao'), dados_json.get('categoria'),
        dados_json.get('resumo'), dados_json.get('tematica'), dados_json.get('prazo'),
        dados_json.get('aderencia'), dados_json.get('link')
    ))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Exemplo prático simulando um link da FAPESP ou FINEP
    url_alvo = "https://example.com/edital-simulado" 
    
    # Para testar sem raspar, podemos usar um texto mockado:
    texto_mock = "A FINEP anuncia edital de R$ 5 milhões para projetos de Hidrogênio Verde focados em mobilidade urbana e trens. Prazo até 30 de Outubro de 2026. Voltado para empresas e startups."
    
    print("Analisando oportunidade com IA...")
    resultado_json = analisar_com_ia(texto_mock, url_alvo)
    
    salvar_no_banco(resultado_json)
    print("Oportunidade salva com sucesso!")
    print(json.dumps(resultado_json, indent=2, ensure_ascii=False))