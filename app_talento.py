import streamlit as st
import pandas as pd
from openai import OpenAI
import fitz  # PyMuPDF
from io import BytesIO
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ZYNTH Enterprise IA", page_icon="💎", layout="wide")

# --- CSS ESTILO ZYNTH NEÓN v5.2 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto:wght@300;400&display=swap');
    .main { background-color: #050505; color: #00FF00; font-family: 'Roboto', sans-serif; }
    h1 { font-family: 'Orbitron', sans-serif; color: #00FF00 !important; text-shadow: 0 0 20px #00FF00; text-align: center; font-size: 50px; margin-bottom: 0px;}
    h3 { font-family: 'Roboto', sans-serif; color: #888 !important; text-align: center; font-weight: 300; letter-spacing: 2px; margin-top: 0px; margin-bottom: 30px;}
    .stButton>button { 
        background: linear-gradient(45deg, #00FF00, #00CC00); color: black; border-radius: 5px; 
        font-family: 'Orbitron', sans-serif; font-weight: bold; width: 100%; border: none; padding: 12px;
        transition: 0.3s; text-transform: uppercase; letter-spacing: 2px; box-shadow: 0 0 10px rgba(0,255,0,0.5);
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea { background-color: #101010; color: #00FF00; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- SEGURIDAD ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.markdown("<h4 style='color:#00FF00; text-align:center; font-family:Orbitron;'>ZYNTH ACCESS CONTROL</h4>", unsafe_allow_html=True)
        password = st.text_input("PASSWORD:", type="password")
        if password == "ZYNTH2026":
            st.session_state.autenticado = True
            st.rerun()
        st.stop()

st.markdown("<h1>ZYNTH ENTERPRISE</h1>", unsafe_allow_html=True)
st.markdown("<h3>NEXUS TALENT SCANNER // CONTACT EDITION</h3>", unsafe_allow_html=True)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def analyze_cv(file, user_requirements):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = "".join([page.get_text() for page in doc])[:8000]
        
        prompt = f"""
        Analiza este CV basándote en: "{user_requirements}".
        Extrae datos de contacto exactos. Si no encuentras alguno, pon 'No disponible'.
        
        FORMATO DE RESPUESTA (ESTRICTO):
        Nombre: [N] | Teléfono: [T] | Email: [E] | Puntaje: [0-100] | Veredicto: [V] | Motivo: [M]
        
        CV:
        {text}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        r = response.choices[0].message.content.split(" | ")
        return {
            "NOMBRE": r[0].split(": ")[1],
            "TELEFONO": r[1].split(": ")[1],
            "EMAIL": r[2].split(": ")[1],
            "PUNTAJE": int(''.join(filter(str.isdigit, r[3]))),
            "VEREDICTO": r[4].split(": ")[1],
            "MOTIVO": r[5].split(": ")[1]
        }
    except: return None

# --- UI ---
col_in, col_out = st.columns([1, 2.2])

with col_in:
    perfil = st.text_area("Requisitos:", placeholder="Ej: Ingeniero con experiencia en Python...")
    archivos = st.file_uploader("Subir CVs", accept_multiple_files=True, type=['pdf'])
    analizar_btn = st.button("🚀 INICIAR ESCANEO")

with col_out:
    if archivos and perfil and analizar_btn:
        resultados = []
        barra = st.progress(0)
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futuros = [executor.submit(analyze_cv, f, perfil) for f in archivos]
            for i, f in enumerate(futuros):
                res = f.result()
                if res: resultados.append(res)
                barra.progress((i + 1) / len(archivos))

        if resultados:
            df = pd.DataFrame(resultados).sort_values(by="PUNTAJE", ascending=False)
            st.dataframe(df, use_container_width=True)

            # --- EXCEL CON FORMATO ZYNTH (NOMBRE, CORREO, TELÉFONO) ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='ZYNTH_Nexus')
                workbook = writer.book
                worksheet = writer.sheets['ZYNTH_Nexus']
                
                # Encabezado Verde Brillante (Igual a tu imagen)
                header_fmt = workbook.add_format({'bold': True, 'bg_color': '#00FF00', 'border': 1, 'align': 'center'})
                data_fmt = workbook.add_format({'valign': 'top'})
                
                # Escribir encabezados con formato y ajustar anchos de columna
                columnas = {
                    "NOMBRE": 30, "TELEFONO": 20, "EMAIL": 30, 
                    "PUNTAJE": 12, "VEREDICTO": 20, "MOTIVO": 60
                }
                
                for i, (col_name, width) in enumerate(columnas.items()):
                    worksheet.write(0, i, col_name, header_fmt)
                    worksheet.set_column(i, i, width, data_fmt)
            
            st.download_button("📥 DESCARGAR REPORTE CONTACTOS", output.getvalue(), "ZYNTH_Talento_Contactos.xlsx")
