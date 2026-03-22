import streamlit as st
import pandas as pd
from openai import OpenAI
import fitz  # PyMuPDF
from io import BytesIO
import plotly.express as px

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ZYNTH Enterprise IA", page_icon="💎", layout="wide")

# Estilo Neón
st.markdown("<style>.main { background-color: #0E1117; color: #00FF00; }</style>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; color: #00FF00;'>ZYNTH ENTERPRISE</h1>", unsafe_allow_html=True)

# --- SEGURIDAD ---
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    pwd = st.text_input("PASSWORD:", type="password")
    if pwd == "ZYNTH2026":
        st.session_state.auth = True
        st.rerun()
    st.stop()

# --- LÓGICA ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def procesar_cv(file, reqs):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = "".join([page.get_text() for page in doc])
    
    prompt = f"Analiza este CV: {text[:4000]}. Requisitos: {reqs}. Responde solo: Nombre: [N] | Puntaje: [0-100] | Veredicto: [V] | Motivo: [M]"
    
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content

# --- INTERFAZ ---
reqs = st.text_input("¿Qué buscas?", "Ingeniero con ganas de trabajar")
files = st.file_uploader("Subir PDFs", accept_multiple_files=True, type=['pdf'])

if files and st.button("ANALIZAR"):
    data = []
    for f in files:
        res = procesar_cv(f, reqs)
        p = res.split(" | ")
        data.append({
            "NOMBRE": p[0].split(": ")[1],
            "PUNTAJE": int(p[1].split(": ")[1]),
            "VEREDICTO": p[2].split(": ")[1],
            "MOTIVO": p[3].split(": ")[1]
        })
    
    df = pd.DataFrame(data)
    st.plotly_chart(px.bar(df, x='NOMBRE', y='PUNTAJE', color='PUNTAJE', template="plotly_dark"))
    st.dataframe(df)
    
    # Excel
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as w:
        df.to_excel(w, index=False)
    st.download_button("Descargar Excel", out.getvalue(), "ZYNTH_Report.xlsx")
