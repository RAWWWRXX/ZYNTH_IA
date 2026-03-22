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
        border: none; box-shadow: 0 0 15px #00FF00; font-weight: bold;
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea { background-color: #111; color: #00FF00; border: 1px solid #00FF00; }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE CONTRASEÑA ---
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
st.markdown("<p style='text-align:center; color:#555;'>NEXUS TALENT SCANNER v6.0</p>", unsafe_allow_html=True)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def procesar_cv(file, reqs):
    try:
        # Abrir PDF y extraer texto
        doc = fitz.open(stream=file.read(), filetype="pdf")
        texto = " ".join([p.get_text() for p in doc])[:8000]
        
        # Prompt agresivo para extraer datos de contacto
        prompt = f"""
        Analiza este CV basándote en estos requisitos: {reqs}
        Extrae NOMBRE, TELÉFONO y CORREO de forma obligatoria.
        
        RESPONDE ÚNICAMENTE EN ESTE FORMATO:
        Nombre: [N] | Teléfono: [T] | Correo: [C] | Puntaje: [0-100] | Veredicto: [V] | Motivo: [M]
        
        CV: {texto}
        """
        
        envio = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        r = envio.choices[0].message.content.split(" | ")
        return {
            "NOMBRE": r[0].split(": ")[1],
            "TELÉFONO": r[1].split(": ")[1],
            "CORREO": r[2].split(": ")[1],
            "PUNTAJE": int(''.join(filter(str.isdigit, r[3]))),
            "VEREDICTO": r[4].split(": ")[1],
            "MOTIVO": r[5].split(": ")[1]
        }
    except Exception as e:
        return None

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("#### ⚙️ CONFIG")
    perfil = st.text_area("Perfil buscado:", placeholder="Ej: Ingeniero Software...", height=150)
    archivos = st.file_uploader("PDFs", accept_multiple_files=True, type=['pdf'])
    boton_escanear = st.button("🚀 INICIAR ESCANEO ZYNTH")

with col2:
    if boton_escanear:
        if not archivos or not perfil:
            st.warning("⚠️ Sube los archivos y define el perfil.")
        else:
            resultados = []
            barra = st.progress(0)
            status = st.empty()
            
            # MULTITHREADING PARA VELOCIDAD (1,000 CVs)
            with ThreadPoolExecutor(max_workers=10) as exe:
                futuros = [exe.submit(procesar_cv, f, perfil) for f in archivos]
                for i, f in enumerate(futuros):
                    res = f.result()
                    if res: resultados.append(res)
                    barra.progress((i + 1) / len(archivos))
                    status.text(f"Procesando: {i+1} / {len(archivos)}")

            if resultados:
                df = pd.DataFrame(resultados).sort_values("PUNTAJE", ascending=False)
                
                # REORDENAR COLUMNAS PARA EL EXCEL (NOMBRE, TELÉFONO, CORREO PRIMERO)
                columnas_orden = ["NOMBRE", "TELÉFONO", "CORREO", "PUNTAJE", "VEREDICTO", "MOTIVO"]
                df = df[columnas_orden]
                
                st.dataframe(df, use_container_width=True)

                # --- EXCEL PROFESIONAL CON FORMATO ---
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Resultados')
                    workbook = writer.book
                    worksheet = writer.sheets['Resultados']
                    
                    # Formato Verde Neón para encabezados (Igual a tu imagen)
                    header_fmt = workbook.add_format({
                        'bold': True, 'bg_color': '#00FF00', 'border': 1, 'align': 'center'
                    })
                    
                    # Formato para el texto (con ajuste de línea para el Motivo)
                    wrap_fmt = workbook.add_format({'text_wrap': True, 'valign': 'top'})
                    
                    # Ajustar anchos de columnas
                    worksheet.set_column('A:A', 35, wrap_fmt) # Nombre
                    worksheet.set_column('B:B', 20, wrap_fmt) # Teléfono
                    worksheet.set_column('C:C', 35, wrap_fmt) # Correo
                    worksheet.set_column('D:D', 10, wrap_fmt) # Puntaje
                    worksheet.set_column('E:E', 25, wrap_fmt) # Veredicto
                    worksheet.set_column('F:F', 70, wrap_fmt) # Motivo (Muy ancho)
                    
                    # Aplicar formato de encabezado
                    for col_num, value in enumerate(df.columns.values):
                        worksheet.write(0, col_num, value, header_fmt)

                st.divider()
                st.download_button("📥 DESCARGAR REPORTE EXCEL (CONTACTOS)", output.getvalue(), "ZYNTH_Talento.xlsx")
