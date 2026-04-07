import streamlit as st
import fitz  # pymupdf
import os
import json
import io
import google.generativeai as genai  # Biblioteca do Google
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors


load_dotenv()
# Certifique-se de ter GEMINI_API_KEY no seu arquivo .env
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def ler_pdf(arquivo):
    """Lê o texto do currículo mantendo a estrutura por blocos."""
    doc = fitz.open(stream=arquivo.read(), filetype="pdf")
    texto = ""
    for pagina in doc:
        blocos = pagina.get_text("blocks")
        for bloco in blocos:
            texto += bloco[4] + "\n"
    return texto

def adaptar_curriculo(curriculo_texto, descricao_vaga):
    """Envia o currículo e a vaga para o Gemini e retorna JSON estruturado."""
    
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={"response_mime_type": "application/json"}
    )
    
    prompt = f"""
    Você é um especialista em RH. Adapte o currículo para a vaga, destacando experiências relevantes.
    Mantenha apenas informações VERDADEIRAS do original.
    
    Retorne este formato JSON exato:
    {{
        "nome": "Nome completo",
        "contato": "email | telefone | linkedin",
        "objetivo": "Objetivo adaptado",
        "experiencias": [
            {{"cargo": "Cargo", "empresa": "Empresa", "periodo": "Jan/2022 - Atual", "descricao": "Descrição"}}
        ],
        "educacao": [
            {{"curso": "Curso", "instituicao": "Instituição", "periodo": "2018 - 2022"}}
        ],
        "habilidades": ["habilidade1", "habilidade2"],
        "score": 85
    }}

    CURRÍCULO: {curriculo_texto}
    VAGA: {descricao_vaga}
    """

    try:
        resposta = model.generate_content(prompt)
        return json.loads(resposta.text)
    except Exception as e:
        st.error(f"Erro ao processar com IA: {e}")
        return None

def gerar_pdf(dados):
    """Gera o PDF do currículo adaptado usando ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    
    estilo_nome = ParagraphStyle("nome", fontSize=20, fontName="Helvetica-Bold",
                                  textColor=colors.HexColor("#1E3A5F"), spaceAfter=6)
    estilo_contato = ParagraphStyle("contato", fontSize=10, textColor=colors.grey, spaceAfter=12)
    estilo_secao = ParagraphStyle("secao", fontSize=13, fontName="Helvetica-Bold",
                                   textColor=colors.HexColor("#1E3A5F"),
                                   spaceBefore=14, spaceAfter=6)
    estilo_cargo = ParagraphStyle("cargo", fontSize=11, fontName="Helvetica-Bold", spaceAfter=2)
    estilo_normal = ParagraphStyle("normal", fontSize=10, spaceAfter=4, leading=14)

    conteudo = []
    conteudo.append(Paragraph(dados["nome"], estilo_nome))
    conteudo.append(Paragraph(dados["contato"], estilo_contato))
    
    conteudo.append(Paragraph("OBJETIVO", estilo_secao))
    conteudo.append(Paragraph(dados["objetivo"], estilo_normal))

    conteudo.append(Paragraph("EXPERIÊNCIA PROFISSIONAL", estilo_secao))
    for exp in dados["experiencias"]:
        conteudo.append(Paragraph(f"{exp['cargo']} — {exp['empresa']}", estilo_cargo))
        conteudo.append(Paragraph(exp["periodo"], estilo_normal))
        conteudo.append(Paragraph(exp["descricao"], estilo_normal))
        conteudo.append(Spacer(1, 8))

    conteudo.append(Paragraph("EDUCAÇÃO", estilo_secao))
    for edu in dados["educacao"]:
        conteudo.append(Paragraph(f"{edu['curso']} — {edu['instituicao']}", estilo_cargo))
        conteudo.append(Paragraph(edu["periodo"], estilo_normal))

    conteudo.append(Paragraph("HABILIDADES", estilo_secao))
    conteudo.append(Paragraph(" • ".join(dados["habilidades"]), estilo_normal))

    doc.build(conteudo)
    buffer.seek(0)
    return buffer

# 2. Interface Streamlit
st.set_page_config(page_title="IA Adaptador de CV", layout="wide")
st.title("📄 Personalizador de Currículos (Grátis)")

col1, col2 = st.columns(2)
with col1:
    arquivo_pdf = st.file_uploader("Seu currículo (PDF)", type=["pdf"])
with col2:
    descricao_vaga = st.text_area("Descrição da vaga", height=200)

if st.button("Gerar Currículo Adaptado"):
    if arquivo_pdf and descricao_vaga:
        with st.spinner("O Gemini está analisando seu perfil..."):
            texto_original = ler_pdf(arquivo_pdf)
            dados_adaptados = adaptar_curriculo(texto_original, descricao_vaga)
            
            if dados_adaptados:
                pdf_gerado = gerar_pdf(dados_adaptados)
                st.success(f"Score de aderência: {dados_adaptados['score']}%")
                st.download_button("Baixar Novo PDF", data=pdf_gerado, file_name="cv_ia.pdf", mime="application/pdf")
    else:
        st.warning("Preencha todos os campos!")

