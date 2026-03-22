import streamlit as st
import pandas as pd
from openai import OpenAI
import fitz  # PyMuPDF
from io import BytesIO
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ZYNTH Enterprise IA", page_icon="💎", layout="wide")

# --- CSS ESTILO ZYNTH ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto:wght@300;400&display=swap');
    .main { background-color: #050505; color: #00FF00; font-family: 'Roboto', sans-serif; }
    h1 { font-family: 'Orbitron', sans-serif; color: #00FF00 !important; text-shadow: 0 0 20px #00FF00; text-align: center; font-size: 50px;}
    .stButton>button { 
        background: #00FF00; color: black; font-family: 'Orbitron'; width: 100%; height: 50px;
        border: none; box-shadow: 0 0 15px #00FF00; font-weight: bold;
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea { background-color: #111; color: #00FF00; border: 1px solid #00FF00; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h1>ZYNTH ACCESS</h1>", unsafe_allow_html=True)
    clave = st.text_input("PASSWORD:", type="password")
    if clave == "ZYNTH2026":
        st.session_state.autenticado = True
        st.rerun()
    st.stop()

# --- APP PRINCIPAL ---
st.markdown("<h1>ZYNTH ENTERPRISE</h1>", unsafe_allow_html=True)

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Falta la API KEY en Secrets.")
    st.stop()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def procesar_cv(file, reqs):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        texto = " ".join([p.get_text() for p in doc])[:7000]
        prompt = f"CV: {texto}\nBusco: {reqs}\nResponde EXACTO: Nombre: [N] | Tel: [T] | Email: [E] | Score: [S] | Veredicto: [V] | Motivo: [M]"
        
        envio = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        r = envio.choices[0].message.content.split(" | ")
        return {
            "NOMBRE": r[0].split(": ")[1],
            "TELEFONO": r[1].split(": ")[1],
            "CORREO": r[2].split(": ")[1],
            "PUNTAJE": int(''.join(filter(str.isdigit, r[3]))),
            "VEREDICTO": r[4].split(": ")[1],
            "MOTIVO": r[5].split(": ")[1]
        }
    except: return None

col1, col2 = st.columns([1, 2])

with col1:
    perfil = st.text_area("Perfil buscado:", height=150)
    archivos = st.file_uploader("PDFs", accept_multiple_files=True, type=['pdf'])
    boton_escanear = st.button("🚀 INICIAR ESCANEO ZYNTH")

with col2:
    if boton_escanear:
        if not archivos or not perfil:
            st.warning("Faltan archivos o perfil.")
        else:
            resultados = []
            barra = st.progress(0)
            with ThreadPoolExecutor(max_workers=10) as exe:
                futuros = [exe.submit(procesar_cv, f, perfil) for f in archivos]
                for i, f in enumerate(futuros):
                    res = f.result()
                    if res: resultados.append(res)
                    barra.progress((i + 1) / len(archivos))
            
            if resultados:
                df = pd.DataFrame(resultados).sort_values("PUNTAJE", ascending=False)
                # Reordenar columnas para el Excel
                df = df[["NOMBRE", "TELEFONO", "CORREO", "PUNTAJE", "VEREDICTO", "MOTIVO"]]
                
                st.dataframe(df, use_container_width=True)

                # --- EXCEL PRO ---
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Data')
                    wb = writer.book
                    ws = writer.sheets['Data']
                    
                    # Formato Verde Zynth (como image_b30ec8.png)
                    head_fmt = wb.add_format({'bold':True,'bg_color':'#00FF00','border':1})
                    
                    # Ajuste de columnas
                    ws.set_column('A:C', 30) # Nombre, Tel, Correo
                    ws.set_column('D:E', 15) # Score, Veredicto
                    ws.set_column('F:F', 60) # Motivo (Súper ancho)
                    
                    for col_num, value in enumerate(df.columns.values):
                        ws.write(0, col_num, value, head_fmt)

                st.download_button("📥 DESCARGAR EXCEL", output.getvalue(), "Reporte_Zynth.xlsx")
