import streamlit as st
import fitz  # pymupdf
import os
import json
import io
from openai import OpenAI
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    """Envia o currículo e a vaga para o GPT-4o e retorna JSON estruturado."""
    resposta = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """Você é um especialista em RH e redação de currículos.
                Adapte o currículo para a vaga descrita, destacando experiências relevantes.
                Mantenha apenas informações verdadeiras do currículo original.
                
                Retorne APENAS um JSON válido, sem texto extra, neste formato:
                {
                    "nome": "Nome completo",
                    "contato": "email | telefone | linkedin",
                    "objetivo": "Objetivo profissional adaptado para a vaga",
                    "experiencias": [
                        {
                            "cargo": "Cargo",
                            "empresa": "Empresa",
                            "periodo": "Jan/2022 - Atual",
                            "descricao": "Descrição adaptada para a vaga"
                        }
                    ],
                    "educacao": [
                        {
                            "curso": "Nome do curso",
                            "instituicao": "Instituição",
                            "periodo": "2018 - 2022"
                        }
                    ],
                    "habilidades": ["habilidade1", "habilidade2"],
                    "score": 85
                }
                
                O campo score é de 0 a 100 indicando quanto o candidato atende à vaga."""
            },
            {
                "role": "user",
                "content": f"""
                CURRÍCULO ATUAL:
                {curriculo_texto}

                DESCRIÇÃO DA VAGA:
                {descricao_vaga}

                Adapte o currículo e retorne o JSON.
                """
            }
        ]
    )
    return json.loads(resposta.choices[0].message.content)


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
                                   spaceBefore=14, spaceAfter=6,
                                   borderPad=4)
    estilo_cargo = ParagraphStyle("cargo", fontSize=11, fontName="Helvetica-Bold", spaceAfter=2)
    estilo_normal = ParagraphStyle("normal", fontSize=10, spaceAfter=4, leading=14)

    conteudo = []


    conteudo.append(Paragraph(dados["nome"], estilo_nome))
    conteudo.append(Paragraph(dados["contato"], estilo_contato))
   
    conteudo.append(Paragraph("OBJETIVO", estilo_secao))
    conteudo.append(Paragraph(dados["objetivo"], estilo_normal))
    conteudo.append(Spacer(1, 12))

    conteudo.append(Paragraph("EXPERIÊNCIA PROFISSIONAL", estilo_secao))
    for exp in dados["experiencias"]:
        conteudo.append(Paragraph(f"{exp['cargo']} — {exp['empresa']}", estilo_cargo))
        conteudo.append(Paragraph(exp["periodo"], estilo_normal))
        conteudo.append(Paragraph(exp["descricao"], estilo_normal))
        conteudo.append(Spacer(1, 12))

    conteudo.append(Paragraph("EDUCAÇÃO", estilo_secao))
    for edu in dados["educacao"]:
        conteudo.append(Paragraph(f"{edu['curso']} — {edu['instituicao']}", estilo_cargo))
        conteudo.append(Paragraph(edu["periodo"], estilo_normal))
        conteudo.append(Spacer(1, 8))

    conteudo.append(Paragraph("HABILIDADES", estilo_secao))
    habilidades_texto = " • ".join(dados["habilidades"])
    conteudo.append(Paragraph(habilidades_texto, estilo_normal))

    doc.build(conteudo)
    buffer.seek(0)
    return buffer

st.set_page_config(page_title="Adaptador de Currículo", page_icon="📄", layout="wide")
st.title("Adaptador de Currículo com IA")
st.markdown("Faça upload do seu currículo e cole a descrição da vaga. A IA adapta e gera um PDF profissional!")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Seu Currículo")
    arquivo_pdf = st.file_uploader("Upload do currículo em PDF", type=["pdf"])

with col2:
    st.subheader("Descrição da Vaga")
    descricao_vaga = st.text_area("Cole a descrição da vaga aqui", height=300)

if st.button("Adaptar Currículo", use_container_width=True):
    if not arquivo_pdf:
        st.error("Por favor, faça upload do seu currículo em PDF!")
    elif not descricao_vaga:
        st.error("Por favor, cole a descrição da vaga!")
    else:
        with st.spinner("A IA está adaptando seu currículo..."):
            curriculo_texto = ler_pdf(arquivo_pdf)
            dados = adaptar_curriculo(curriculo_texto, descricao_vaga)
            pdf_buffer = gerar_pdf(dados)

        # Score de compatibilidade
        score = dados.get("score", 0)
        st.subheader("Score de Compatibilidade")
        st.progress(score / 100)

        if score >= 75:
            st.success(f"{score}/100 — Ótima compatibilidade com a vaga!")
        elif score >= 50:
            st.warning(f"{score}/100 — Compatibilidade média. Vale candidatar!")
        else:
            st.error(f"{score}/100 — Baixa compatibilidade. Considere se qualificar antes.")

        st.success("Currículo adaptado com sucesso!")

        # Download do PDF
        st.download_button(
            label="⬇Baixar Currículo em PDF",
            data=pdf_buffer,
            file_name="curriculo_adaptado.pdf",
            mime="application/pdf",
            use_container_width=True
        )
