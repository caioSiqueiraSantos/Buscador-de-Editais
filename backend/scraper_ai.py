from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import json
import sqlite3
import requests
from bs4 import BeautifulSoup
 
load_dotenv()
# A configuração agora é feita instanciando um Client:
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Temas de interesse do Metrô
TEMAS = "Mobilidade, transporte sobre trilhos, MaaS, hidrogênio verde, blockchain, materiais avançados, energias renováveis, Indústria 4.0, inteligência artificial."

def extrair_texto_pagina(url):
    """Realiza o scraping de uma página de edital, isolando o conteúdo principal."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove tags indesejadas que sujam o prompt (menus, rodapés, scripts)
        for tag in soup(['header', 'footer', 'nav', 'script', 'style', 'aside']):
            tag.decompose()
            
        # Tenta focar no conteúdo principal (tag main, article ou div com classes comuns de conteúdo)
        main_content = soup.find('main') or soup.find('article') or soup.find('div', id='content') or soup.body
        
        if not main_content:
            return ""
            
        texto_limpo = main_content.get_text(separator=' ', strip=True)
        return texto_limpo[:4000] # Limite para não estourar o limite de tokens da API
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
    
    # Modelo atualizado e ativo na API Google GenAI
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    
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
    # Exemplo prático usando um link real de chamadas da FINEP
    url_alvo = "http://www.finep.gov.br/chamadas-publicas/chamadaspublicas" 
    
    print(f"Extraindo texto de: {url_alvo} ...")
    texto_extraido = extrair_texto_pagina(url_alvo)
    
    if texto_extraido:
        print("Analisando oportunidade com IA...")
        resultado_json = analisar_com_ia(texto_extraido, url_alvo)
        
        salvar_no_banco(resultado_json)
        print("Oportunidade salva com sucesso!")
        print(json.dumps(resultado_json, indent=2, ensure_ascii=False))
    else:
        print("Falha ao extrair texto da página.")