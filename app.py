import streamlit as st
import fitz
import os
import json
import io
from openai import OpenAI
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import geSampleStyleSheet, ParagraStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


#ler o texto em pdf
def ler_pdf(arquivo):
    doc = fitz.open(stream=arquivo.read(), filetype= "pdf")
    texto = ""
    for pagina in doc:
        blocos = pagina.get_text("blocks")
        for bloco in blocos:
            texto += bloco[4] + "\n"
    return texto    

#envia o curriculo e a vaga pro GPT e retorna o JSON 
def adaptar_curriculo(curriculo_texto, descricao_vaga):
    resposta = client.chat.completions.create(
        model="gtp-4o",
        messages=[
            {
                "role": "system",
                "content": """Você é um especialista em RH e redação de curriculos.
                Adapte o curriculo para a vaga descrita, destacando experiencia relevantes. 
                Mantenha apenas informações verdadeiras do curriculo original.
                Todos os periodos de data devem estar no formato MM/AAAA (ex: 01/2020 - 12/2020)
                Se o cargo for atual use "MM/AAAA - Atual"
                Retorne APENAS em um JSON válido, sem texto extra, neste formato: 
                {
                "nome": "Nome completo"
                "contato": "email | telefone | linkedin"
                "objetivo": "Objetivo profissional adaptado para a vaga"
                "experiencia": [
                    {
                        "cargo": "Cargo",
                        "empresa": "Empresa",
                        "periodo": "Periodo",
                        "descricao": "Descrição das responsabilidades e conquistas, adaptada para destacar relevância para a vaga"
                    }
                ],
                "educacao": [
                    {
                        "curso": "nome do curso"
                        "instituicao": "nome da instituição"
                    }
                ],

                "habilidades": ["habilidades1", "habilidades2"], 
                "score": 85
            O campo score é de 0 a 100 indicando o quanto o candidato atende a vaga"""  
                },
            {
                "role": "user",
                "content": f"""
                CURRICULO ATUAL:
                {curriculo_texto}

                DESCRIÇÃO DA VAGA:
                {descricao_vaga}

                ADAPTE O CURRICULO PARA A VAGA E RETORNE O JSON."""
                
            }
        ]
    )
