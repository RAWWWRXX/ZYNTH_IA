import streamlit as st
import pandas as pd
from openai import OpenAI
import fitz  # PyMuPDF
from io import BytesIO
import plotly.express as px  # Para las gráficas profesionales

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ZYNTH Enterprise IA", page_icon="💎", layout="wide")

# --- ESTILO NEÓN ZYNTH v2.0 ---
st.markdown("""
    <style>
    .main { background-color: #0E1117; color: #00FF00; }
    .stButton>button { 
        background-color: #00FF00; color: black; border-radius: 5px; 
        font-weight: bold; width: 100%; border: none; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #00CC00; transform: scale(1.02); }
    .stTextInput>div>div>input { background-color: #1A1C24; color: white; border: 1px solid #333; }
    h1 { color: #00FF00 !important; font-family: 'Orbitron', sans-serif; letter-spacing: 5px; text-align: center; }
    h3 { color: #888 !important; text-align: center; }
    .stProgress > div > div > div > div { background-color: #00FF00; }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER DE MARCA ---
st.markdown("<h1>ZYNTH ENTERPRISE</h1>", unsafe_allow_html=True)
st.markdown("<h3>NEXUS TALENT PROCESSOR • AI EDITION</h3>", unsafe_allow_html=True)
st.divider()

# --- SEGURIDAD ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        password = st.text_input("SISTEMA ENCRIPTADO - INGRESE ACCESS KEY:", type="password")
        if password == "ZYNTH2026":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.info("Esperando credenciales de administrador...")
            st.stop()

# --- CONFIGURACIÓN DE IA ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

def analyze_cv(text, user_requirements):
    prompt = f"""
    Eres el motor de IA de ZYNTH Enterprise. Analiza este CV basándote en estos REQUISITOS DEL CLIENTE: "{user_requirements}".
    Extrae:
    1. Nombre del candidato.
    2. Puntaje (1-100) según qué tanto cumple con los requisitos.
    3. Correo.
    4. Teléfono.
    5. Análisis: Una frase técnica del perfil.
    6. Veredicto: (CONTRATAR, ENTREVISTAR o RECHAZAR).
    7. Motivo: Justificación breve.

    CV: {text}
    Responde en este formato:
    Nombre: [N] | Puntaje: [P] | Correo: [C] | Telefono: [T] | Analisis: [A] | Veredicto: [V] | Motivo: [M]
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# --- PANEL DE CONTROL ---
col_left, col_right = st.columns([1, 2])

with col_left:
    st.markdown("#### ⚙️ CONFIGURACIÓN")
    reqs = st.text_area("¿Qué perfil buscas hoy?", placeholder="Ej: Ingeniero de Software con experiencia en Python y bots...")
    uploaded_files = st.file_uploader("CARGAR CVS (PDF)", accept_multiple_files=True, type=['pdf'])

with col_right:
    if uploaded_files and reqs:
        if st.button("🚀 INICIAR ESCANEO ZYNTH"):
            results = []
            progress_bar = st.progress(0)
            
            for i, file in enumerate(uploaded_files):
                text = extract_text_from_pdf(file)
                analysis = analyze_cv(text, reqs)
                parts = analysis.split(" | ")
                
                try:
                    res_dict = {
                        "NOMBRE": parts[0].split(": ")[1],
                        "PUNTAJE": int(parts[1].split(": ")[1]),
                        "VEREDICTO": parts[5].split(": ")[1],
                        "MOTIVO": parts[6].split(": ")[1],
                        "CORREO": parts[2].split(": ")[1],
                        "TELÉFONO": parts[3].split(": ")[1],
                        "ANÁLISIS": parts[4].split(": ")[1],
                        "ARCHIVO": file.name
                    }
                    results.append(res_dict)
                except:
                    continue
                progress_bar.progress((i + 1) / len(uploaded_files))

            df = pd.DataFrame(results)
            
            # --- VISUALIZACIÓN DE DATOS ---
            st.markdown("#### 📊 RANKING DE TALENTO")
            df_sorted = df.sort_values(by="PUNTAJE", ascending=False)
            fig = px.bar(df_sorted.head(5), x='NOMBRE', y='PUNTAJE', 
                         color='PUNTAJE', color_continuous_scale='Greens',
                         template="plotly_dark", title="TOP 5 CANDIDATOS")
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(df_sorted)

            # --- EXCEL PREMIUM ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='ZYNTH_DATA')
                workbook, worksheet = writer.book, writer.sheets['ZYNTH_DATA']
                header_fmt = workbook.add_format({'bold': True, 'bg_color': '#000000', 'font_color': '#00FF00', 'border': 1})
                cell_fmt = workbook.add_format({'border': 1})
                for i, col in enumerate(df.columns):
                    worksheet.set_column(i, i, max(df[col].astype(str).map(len).max(), len(col)) + 5, cell_fmt)
                    worksheet.write(0, i, col, header_fmt)
            
            st.download_button("📥 DESCARGAR REPORTE ZYNTH", output.getvalue(), "Reporte_ZYNTH.xlsx")

    else:
        st.info("Esperando archivos y descripción del puesto...")
