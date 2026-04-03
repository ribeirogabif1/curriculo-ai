import streamlit as st 
import fitz
import os
from openai import OpenAI 
from dotenv import load_dotenv

load_dotenv ()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

#le o exto em pdf
def ler_pdf(arquivo):

    doc = fitz.open(stream=arquivo.read(), filetype="pdf")
    texto = ""
    for pagina in doc:
        texto += pagina.get_text()

    return texto    

#envia o curriculo e a vaga para o chatgpt

def analisar_curriculo(curriculo_texto, vaga_texto):
    resposta = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content":"""Você é especialistas em RH e redação de curriclos. 4
                Sua tarefa é adaptar o curriculo do candidato para a vaga descria, destacando as experiências e habilidades mais relevantes. Matenha todas as informações verdadeira - apenas reorganizer e reescreva para destacar o que é mais relevante para a vaga. 
                Retorne apenas o curriculo adaptado, sem comentários extras."""

            },
            {
            "role": "user",
            "content": f"""
            CURRÍCULO ATUAL:
            {curriculo_texto}

            DESCRIÇÃO DA VAGA:
            {descricao_vaga}

            """Adapte o currículo para essa vaga."""
            }
        ]
    )
    return resposta.choices[0].message.content

st.title("Adaptador de currículo com IA")