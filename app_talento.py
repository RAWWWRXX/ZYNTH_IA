import streamlit as st
import pandas as pd
from openai import OpenAI
import fitz  # PyMuPDF
from io import BytesIO
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ZYNTH Enterprise IA", page_icon="💎", layout="wide")

# --- CSS ESTILO ZYNTH NEÓN v4.0 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto:wght@300;400&display=swap');
    .main { background-color: #050505; color: #00FF00; font-family: 'Roboto', sans-serif; }
    h1 { font-family: 'Orbitron', sans-serif; color: #00FF00 !important; text-shadow: 0 0 20px #00FF00; text-align: center; font-size: 50px; margin-bottom: 0px;}
    .stButton>button { 
        background: #00FF00; color: black; font-family: 'Orbitron'; width: 100%; height: 50px;
        border: none; box-shadow: 0 0 15px #00FF00; transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.02); background: #00CC00; }
    .stProgress > div > div > div > div { background-color: #00FF00; }
    .stDataFrame { border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1>ZYNTH ENTERPRISE</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#555; letter-spacing: 2px;'>NEXUS TALENT PROCESSOR // HIGH-SPEED EDITION</p>", unsafe_allow_html=True)

# --- MOTOR DE IA (VERIFICACIÓN DE LLAVE) ---
if "OPENAI_API_KEY" not in st.secrets:
    st.error("❌ ERROR: No se encontró la 'OPENAI_API_KEY' en los Secrets de Streamlit.")
    st.stop()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def procesar_cv_veloz(file, reqs):
    """Procesamiento optimizado para volumen masivo"""
    try:
        # Extraer texto del PDF
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = " ".join([page.get_text() for page in doc])[:7000]
        
        # Prompt ultra-directo para ahorrar tiempo/tokens
        prompt = f"CV: {text}\nRequisitos: {reqs}\nResponde exacto: Nombre: [N] | Score: [0-100] | Veredicto: [V] | Motivo: [M] | Email: [E]"
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "Eres un reclutador experto de ZYNTH."},
                      {"role": "user", "content": prompt}],
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

# --- INTERFAZ DE USUARIO ---
col_in, col_out = st.columns([1, 2])

with col_in:
    st.markdown("### ⚙️ PARÁMETROS")
    perfil = st.text_area("¿Qué perfil buscas?", placeholder="Ej: Desarrollador Python Senior...", height=120)
    subidos = st.file_uploader("CARGAR CVS (PDF)", accept_multiple_files=True, type=['pdf'])
    boton_analizar = st.button("🚀 INICIAR ESCANEO ZYNTH")

with col_out:
    if subidos and perfil and boton_analizar:
        resultados = []
        barra = st.progress(0)
        status = st.empty()
        
        # MAGIA: Multithreading para procesar 10 CVs a la vez
        with ThreadPoolExecutor(max_workers=10) as executor:
            futuros = [executor.submit(procesar_cv_veloz, f, perfil) for f in subidos]
            for i, f in enumerate(futuros):
                res = f.result()
                if res:
                    resultados.append(res)
                barra.progress((i + 1) / len(subidos))
                status.write(f"PROCESADOS: {i+1} de {len(subidos)}")

        if resultados:
            df = pd.DataFrame(resultados).sort_values(by="PUNTAJE", ascending=False)
            
            # Gráfica Horizontal de Alta Calidad
            fig = px.bar(df.head(15), x='PUNTAJE', y='NOMBRE', orientation='h',
                         color='PUNTAJE', color_continuous_scale=['#003300', '#00FF00'],
                         template="plotly_dark", title="RANKING TOP 15")
            fig.update_layout(yaxis={'autorange': "reversed"}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla de Datos
            st.dataframe(df, use_container_width=True)

            # Excel Profesional
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='ZYNTH_Talento')
                # Formato de columnas
                worksheet = writer.sheets['ZYNTH_Talento']
                for i, col in enumerate(df.columns):
                    worksheet.set_column(i, i, 25)
            
            st.download_button("📥 DESCARGAR REPORTE EXCEL", output.getvalue(), "ZYNTH_Nexus_Report.xlsx")
        else:
            st.error("No se pudo extraer información de los archivos.")

    elif boton_analizar:
        st.warning("⚠️ Asegúrate de escribir el perfil y subir archivos.")
    else:
        st.markdown("<br><br><h3 style='text-align:center; color:#333;'>Esperando archivos para iniciar proceso...</h3>", unsafe_allow_html=True)
