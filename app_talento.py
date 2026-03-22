import streamlit as st
import pandas as pd
from openai import OpenAI
import fitz  # PyMuPDF
from io import BytesIO
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor # Para velocidad masiva

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ZYNTH Enterprise IA", page_icon="💎", layout="wide")

# --- CSS ESTILO "ZYNTH NEÓN" ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto:wght@300;400&display=swap');
    .main { background-color: #050505; color: #00FF00; font-family: 'Roboto', sans-serif; }
    h1 { font-family: 'Orbitron', sans-serif; color: #00FF00 !important; text-shadow: 0 0 20px #00FF00; text-align: center; }
    .stButton>button { 
        background: #00FF00; color: black; font-family: 'Orbitron'; width: 100%; 
        border: none; box-shadow: 0 0 15px #00FF00;
    }
    .stProgress > div > div > div > div { background-color: #00FF00; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1>ZYNTH ENTERPRISE</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#888;'>HIGH-SPEED TALENT PROCESSOR v4.0</p>", unsafe_allow_html=True)

# --- SEGURIDAD ---
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    pwd = st.text_input("ACCESS KEY:", type="password")
    if pwd == "ZYNTH2026":
        st.session_state.auth = True
        st.rerun()
    st.stop()

# --- MOTOR DE IA ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def procesar_un_solo_pdf(file, reqs):
    """Función que procesa un PDF individual para el ThreadPool"""
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = " ".join([page.get_text() for page in doc])[:8000]
        
        prompt = f"Analiza este CV: {text}. Requisitos: {reqs}. Responde solo: Nombre: [N] | Puntaje: [0-100] | Veredicto: [V] | Motivo: [M] | Email: [E]"
        
        response = client.chat.completions.create(
            model="gpt-4o-mini", # El más rápido y barato para volumen
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        res = response.choices[0].message.content
        p = res.split(" | ")
        return {
            "NOMBRE": p[0].split(": ")[1],
            "PUNTAJE": int(''.join(filter(str.isdigit, p[1]))),
            "VEREDICTO": p[2].split(": ")[1],
            "MOTIVO": p[3].split(": ")[1],
            "EMAIL": p[4].split(": ")[1]
        }
    except:
        return None

# --- INTERFAZ ---
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### ⚙️ FILTRO")
    reqs = st.text_area("Perfil buscado:", placeholder="Ej: Dev Jr con Python...", height=100)
    files = st.file_uploader("Subir CVs (Máximo 1000)", accept_multiple_files=True, type=['pdf'])
    start = st.button("🚀 INICIAR ESCANEO MASIVO")

with col2:
    if files and reqs and start:
        results = []
        progress = st.progress(0)
        status = st.empty()
        
        # --- PROCESAMIENTO PARALELO (AQUÍ ESTÁ LA MAGIA) ---
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(procesar_un_solo_pdf, f, reqs) for f in files]
            
            for i, future in enumerate(futures):
                res = future.result()
                if res: results.append(res)
                progress.progress((i + 1) / len(files))
                status.text(f"Procesados: {i+1} de {len(files)}")

        if results:
            df = pd.DataFrame(results).sort_values(by="PUNTAJE", ascending=False)
            
            # Gráfica Horizontal Limpia
            fig = px.bar(df.head(20), x='PUNTAJE', y='NOMBRE', orientation='h',
                         color='PUNTAJE', color_continuous_scale='Greens',
                         template="plotly_dark", title="TOP 20 CANDIDATOS")
            fig.update_layout(yaxis={'autorange': "reversed"}, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df, use_container_width=True)

            # Excel de alta calidad
            out = BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as w:
                df.to_excel(w, index=False, sheet_name='ZYNTH_REPORT')
                # Auto-ajuste de columnas
                worksheet = w.sheets['ZYNTH_REPORT']
                for i, col in enumerate(df.columns):
                    worksheet.set_column(i, i, 25)
            
            st.download_button("📥 DESCARGAR EXCEL", out.getvalue(), "ZYNTH_Report.xlsx")
