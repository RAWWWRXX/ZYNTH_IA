import streamlit as st
import pandas as pd
from openai import OpenAI
import fitz  # PyMuPDF
from io import BytesIO
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ZYNTH Enterprise IA", page_icon="💎", layout="wide")

# --- CSS ESTILO ZYNTH NEÓN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto:wght@300;400&display=swap');
    .main { background-color: #050505; color: #00FF00; font-family: 'Roboto', sans-serif; }
    h1 { font-family: 'Orbitron', sans-serif; color: #00FF00 !important; text-shadow: 0 0 20px #00FF00; text-align: center; font-size: 50px;}
    .stButton>button { 
        background: #00FF00; color: black; font-family: 'Orbitron'; width: 100%; height: 50px;
        border: none; box-shadow: 0 0 15px #00FF00;
    }
    .stTextInput>div>div>input { background-color: #111; color: #00FF00; border: 1px solid #00FF00; }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE CONTRASEÑA ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h1>ZYNTH ACCESS</h1>", unsafe_allow_html=True)
    clave = st.text_input("INGRESE CÓDIGO DE ACCESO:", type="password")
    if clave == "ZYNTH2026":
        st.session_state.autenticado = True
        st.rerun()
    st.stop()

# --- INTERFAZ PRINCIPAL ---
st.markdown("<h1>ZYNTH ENTERPRISE</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#555;'>ULTRA-FAST TALENT SCANNER v5.0</p>", unsafe_allow_html=True)

# Motor IA
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def analizar_cv(file, reqs):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        texto = " ".join([p.get_text() for p in doc])[:7000]
        prompt = f"Analiza este CV: {texto}\nBusco: {reqs}\nResponde: Nombre: [N] | Score: [0-100] | Veredicto: [V] | Motivo: [M] | Email: [E]"
        
        envio = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        r = envio.choices[0].message.content.split(" | ")
        return {
            "NOMBRE": r[0].split(": ")[1],
            "PUNTAJE": int(''.join(filter(str.isdigit, r[1]))),
            "VEREDICTO": r[2].split(": ")[1],
            "MOTIVO": r[3].split(": ")[1],
            "EMAIL": r[4].split(": ")[1]
        }
    except: return None

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### ⚙️ CONFIG")
    perfil = st.text_area("Perfil:", placeholder="Ej: Ingeniero Software...")
    archivos = st.file_uploader("Subir PDFs", accept_multiple_files=True, type=['pdf'])
    btn = st.button("🔥 ESCANEO MASIVO")

with col2:
    if archivos and perfil and btn:
        resultados = []
        barra = st.progress(0)
        
        # Multithreading para que 1000 CVs carguen rápido
        with ThreadPoolExecutor(max_workers=10) as exe:
            futuros = [exe.submit(analizar_cv, f, perfil) for f in archivos]
            for i, f in enumerate(futuros):
                res = f.result()
                if res: resultados.append(res)
                barra.progress((i + 1) / len(archivos))

        if resultados:
            df = pd.DataFrame(resultados).sort_values("PUNTAJE", ascending=False)
            
            # Gráfica Horizontal arreglada
            fig = px.bar(df.head(15), x='PUNTAJE', y='NOMBRE', orientation='h', 
                         color='PUNTAJE', color_continuous_scale='Greens', template="plotly_dark")
            fig.update_layout(yaxis={'autorange': "reversed"}, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df, use_container_width=True)

            # --- ARREGLO DE EXCEL (COLUMNAS ANCHAS) ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='ZYNTH_DATA')
                workbook = writer.book
                worksheet = writer.sheets['ZYNTH_DATA']
                
                # Formato para que se vea profesional
                header_format = workbook.add_format({'bold': True, 'bg_color': '#00FF00', 'border': 1})
                
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    # Ajuste automático del ancho (30 unidades por columna)
                    worksheet.set_column(col_num, col_num, 30)
            
            st.download_button("📥 DESCARGAR EXCEL ARREGLADO", output.getvalue(), "Zynth_Report_v5.xlsx")
