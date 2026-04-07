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

return json.loads(resposta.choices[0].message.content)

def gerar_pdf(dados):
    buffer = io.BytesIO()
    doc = SimplesDocTemplate(buffer, pagesize=A4, 
                             rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    estilos = getSampleStyleSheet()

    estilo_nome = ParaphaStyle("nome", fontsize=18, fontName="Helvetica-bold", textColor=colors.HexColor("#1e3a5f"), spaceAfter=12)
    estilo_contato = ParagraphStyle("contato", fontsize=10, textColor=grey, SpaceAfter=12)
    estilo_secao = ParagraphStyle("secao", fontsize=13, fontName="Helvetica-bold", textColor=colors.HexColor("#1e3a5f"), spaceBefore=14, spaceAfter=6, borderPad=4)
    
    estilo_cargo = ParagraphStyle("cargo", fontsize=11, fontName="Helvetica-bold", spaceAfter=2)
    
    estilo_normal = ParagraphStyle("normal", fontsize=10, spaceAfter=4, leading=4)

    conteudo[]

    conteudo.append(Paragraph(dados["nome"], estilo_nome))
    conteudo.append(Paragraph(dados["contato"], estilo_contato))
    conteudo.append(Paragraph("OBJETIVO", estilo_secao))
    conteudo.append(Paragraph(dados["objetivo"], estilo_normal))
    conteudo.append(Spacer(1, 12))
   
    conteudo.append(Paragraph("EXPERÊNCIA PROFISSIONAL", estilo_secao))
    for exp in dados["experiencia"]:
        conteudo.append(Paragraph(f"{exp['cargo']} - {exp['empresa']}, estilo_cargo))
        conteudo.append(Paragraph(exp["periodo"], estilo_normal))
        conteudo.append(Paragraph(exp["descricao"], estilo_normal))
        conteudo.append(Spacer(1, 6))   
        
        conteudo.append(Paragraph("EDUCAÇÃO", estilo_secao))
        for edu in dados["educacao"]:
            conteudo.append(Paragraph(f"{edu['curso']} - {edu['instituicao']}", estilo_normal))
            conteudo.append(Spacer(1, 8))

        conteudo.append(Paragraph("HABILIDADES", estilo_secao))
        habilidades_texto = ", ".join(dados["habilidades"])
        conteudo.append(Paragraph(habilidades_texto, estilo_normal))

        doc.build(conteudo)
    return buffer

st.set_page_config(page_title="Adaptador de Currículo", page_icon=":briefcase:a", layout="wide")
st.title("Adaptador de Currículo com IA)")
st.markdown("Faça upload do seu currículo em PDF e cole a descriçãp da vaga")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Upload do Currículo")
    arquivo.pdf = st.file_uploader("Upload o currículo em PDF", type=["pdf"])

with col2: 
    st.subheader("Descrição da vaga")
    descricao_vaga = st.text_area("Cole a descrição da vaga aqui")

if st.button("Adaptar Currículo", user_container_width=True):
    if not arquivo_pdf:
        st.error("Por favor, faça upload do currículo em PDF")
    elif not descricao_vaga:
    st.error("Por favor, cole a descrição da vaga")

    else:
        with st.spinner("Adaptando currículo..."):
            curriculo_texto = ler_pdf(arquivo_pdf)
            dados_adaptados = adaptar_curriculo(curriculo_texto, descricao_vaga)
            pdf_buffer = gerar_pdf(dados)
            
    score = dados.get("score", 0)
    st.subheader("Score de compatibilidade")
    st.progress(score/100)

    if score >= 75:
        st.success(f" {score} Currículo compatível com a vaga!")
    elif score>= 50:
        st.warning:(f"{score} Currículo com compatibilidade média")
    else:
        st.error(f"{score} Currículo com baixa compatibilidade")    

    st.success("Currículo adaptado com sucesso!")
    st.download_button(
            label="Baixar Currículo Adaptado",
            data=pdf_buffer,
            file_name="GabrielaRibeiro_CV.pdf",
            mime="application/pdf"
            user_container_width=True
        )

