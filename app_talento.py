import streamlit as st
import pandas as pd
from openai import OpenAI
import fitz  # PyMuPDF
from io import BytesIO
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ZYNTH Enterprise IA", page_icon="💎", layout="wide")

# --- CSS ESTILO ZYNTH NEÓN v5.1 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto:wght@300;400&display=swap');
    
    .main { background-color: #050505; color: #00FF00; font-family: 'Roboto', sans-serif; }
    
    h1 { font-family: 'Orbitron', sans-serif; color: #00FF00 !important; text-shadow: 0 0 20px #00FF00; text-align: center; font-size: 50px; margin-bottom: 0px;}
    h3 { font-family: 'Roboto', sans-serif; color: #888 !important; text-align: center; font-weight: 300; letter-spacing: 2px; margin-top: 0px; margin-bottom: 30px;}
    h4 { color: #00FF00 !important; font-family: 'Orbitron', sans-serif; letter-spacing: 2px; border-bottom: 1px solid #333; padding-bottom: 10px; margin-top: 20px;}

    /* Botón Neón */
    .stButton>button { 
        background: linear-gradient(45deg, #00FF00, #00CC00); color: black; border-radius: 5px; 
        font-family: 'Orbitron', sans-serif; font-weight: bold; width: 100%; border: none; padding: 12px;
        transition: 0.3s; text-transform: uppercase; letter-spacing: 2px; box-shadow: 0 0 10px rgba(0,255,0,0.5);
    }
    .stButton>button:hover { background: linear-gradient(45deg, #00CC00, #00FF00); transform: scale(1.03); box-shadow: 0 0 20px #00FF00; }

    /* Inputs y Áreas de Texto */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea { 
        background-color: #101010; color: #00FF00; border: 1px solid #333; font-family: 'Roboto', sans-serif; border-radius: 5px;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus { border: 1px solid #00FF00; box-shadow: 0 0 10px rgba(0,255,0,0.3); }

    /* Drag & Drop */
    .stFileUploader>div>div>button { background-color: #151515; color: #888; border: 1px dashed #333; }
    .stFileUploader>div>div>button:hover { border: 1px dashed #00FF00; color: #00FF00; }

    /* Dataframe y Tabla */
    .stDataFrame { background-color: #101010; border: 1px solid #333; border-radius: 5px; }
    
    /* Ocultar barra de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE CONTRASEÑA (RESTAURADO) ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.markdown("<h4 style='text-align:center;'>INSTALANDO CONEXIÓN SEGURA...</h4>", unsafe_allow_html=True)
        password = st.text_input("INGRESE ACCESS KEY (ENCRIPTADO):", type="password")
        if password == "ZYNTH2026":
            st.session_state.autenticado = True
            st.rerun()
        elif password:
            st.error("KEY INCORRECTA. ACCESO DENEGADO.")
        st.stop()

# --- HEADER DE MARCA ---
st.markdown("<h1>ZYNTH ENTERPRISE</h1>", unsafe_allow_html=True)
st.markdown("<h3>ULTRA-FAST TALENT SCANNER // AI EDITION v5.1</h3>", unsafe_allow_html=True)

# --- CONFIGURACIÓN DE IA (VERIFICACIÓN DE LLAVE) ---
if "OPENAI_API_KEY" not in st.secrets:
    st.error("❌ ERROR CRÍTICO: No se encontró la 'OPENAI_API_KEY' en los Secrets de Streamlit.")
    st.stop()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def extract_text_from_pdf(pdf_file):
    try:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = "".join([page.get_text() for page in doc])
        return text[:10000] # Límite de texto para no saturar
    except:
        return ""

def analyze_cv(text, user_requirements):
    if not text: return "Error: No se pudo leer el PDF."
    
    prompt = f"""
    Eres el motor de IA de ZYNTH Enterprise. Analiza este CV de forma extremadamente rigurosa basándote en estos REQUISITOS DEL CLIENTE: "{user_requirements}".
    Extrae la información y asigna un puntaje del 0 al 100.
    
    RESPONDE EXCLUSIVAMENTE EN ESTE FORMATO:
    Nombre: [Nombre Completo] | Puntaje: [0-100] | Veredicto: [CONTRATAR TOTALMENTE / ENTREVISTAR / RECHAZAR] | Motivo: [Explicación técnica y detallada] | Email: [Correo electrónico]
    
    CV TEXTO:
    {text}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # El más rápido y eficiente para volumen
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content
    except:
        return "Error en la conexión con la IA."

# --- PANEL DE CONTROL ---
col_config, col_display = st.columns([1, 2.2])

with col_config:
    st.markdown("#### ⚙️ CONFIGURACIÓN")
    reqs = st.text_area("¿Qué perfil buscas hoy?", placeholder="Ej: Desarrollador Python Senior...", height=150)
    uploaded_files = st.file_uploader("CARGAR CVS (PDF)", accept_multiple_files=True, type=['pdf'])
    analizar_btn = st.button("🚀 INICIAR ESCANEO ZYNTH")

with col_display:
    if uploaded_files and reqs and analizar_btn:
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # MAGIA: Multithreading para procesar 10 CVs a la vez
        with ThreadPoolExecutor(max_workers=10) as executor:
            futuros = [executor.submit(analyze_cv, extract_text_from_pdf(f), reqs) for f in uploaded_files]
            
            for i, f in enumerate(futuros):
                status_text.text(f"Procesando: {uploaded_files[i].name}...")
                analysis = f.result()
                
                try:
                    parts = analysis.split(" | ")
                    nombre = parts[0].split(": ")[1]
                    puntaje = int(''.join(filter(str.isdigit, parts[1].split(": ")[1])))
                    
                    results.append({
                        "NOMBRE": nombre,
                        "PUNTAJE": puntaje,
                        "VEREDICTO": parts[2].split(": ")[1],
                        "MOTIVO": parts[3].split(": ")[1],
                        "EMAIL": parts[4].split(": ")[1]
                    })
                except:
                    st.warning(f"No se pudo estructurar el análisis de: {uploaded_files[i].name}. La IA respondió: {analysis[:100]}...")
                    continue
                
                progress_bar.progress((i + 1) / len(uploaded_files))
        
        status_text.text("Escaneo completado.")
        
        if results:
            df = pd.DataFrame(results).sort_values(by="PUNTAJE", ascending=False)
            
            # Gráfica Horizontal arreglada
            st.markdown("#### 📊 RANKING DE TALENTO")
            fig = px.bar(df.head(15), x='PUNTAJE', y='NOMBRE', orientation='h',
                         color='PUNTAJE', color_continuous_scale=['#003300', '#00FF00'], # Gradiente neón
                         template="plotly_dark", title="TOP CANDIDATOS")
            fig.update_layout(yaxis={'autorange': "reversed"}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

            # Tabla de datos
            st.markdown("#### 📄 DETALLE COMPLETO")
            st.dataframe(df, use_container_width=True)

            # --- ARREGLO DE EXCEL DEFINITIVO (COLUMNAS ANCHAS Y VERDES) ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='ZYNTH_Nexus_Data')
                workbook = writer.book
                worksheet = writer.sheets['ZYNTH_Nexus_Data']
                
                # Formato Premium para los encabezados (Verde Neón con Bordes)
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#00FF00', # Verde Neón Brillante
                    'font_color': '#000000', # Texto Negro para contraste
                    'border': 1,
                    'align': 'center',
                    'font_name': 'Calibri',
                    'font_size': 12
                })
                
                # Formato para el texto de los motivos (con ajuste de línea)
                motivo_format = workbook.add_format({
                    'text_wrap': True,
                    'valign': 'top',
                    'font_name': 'Calibri'
                })
                
                # Formato para el resto de datos
                data_format = workbook.add_format({
                    'valign': 'top',
                    'font_name': 'Calibri'
                })

                # Aplicar formatos y ajustar anchos
                for col_num, value in enumerate(df.columns.values):
                    # Forzar el formato del encabezado
                    worksheet.write(0, col_num, value, header_format)
                    
                    # Ajuste de ancho masivo por columna
                    if value == "NOMBRE": worksheet.set_column(col_num, col_num, 30, data_format)
                    elif value == "PUNTAJE": worksheet.set_column(col_num, col_num, 10, data_format)
                    elif value == "VEREDICTO": worksheet.set_column(col_num, col_num, 20, data_format)
                    elif value == "MOTIVO": worksheet.set_column(col_num, col_num, 60, motivo_format) # Ancho masivo
                    elif value == "EMAIL": worksheet.set_column(col_num, col_num, 30, data_format)
                    else: worksheet.set_column(col_num, col_num, 20, data_format)
            
            st.divider()
            st.download_button("📥 DESCARGAR REPORTE PREMIUM", output.getvalue(), "ZYNTH_Nexus_Report.xlsx", mime="application/vnd.ms-excel")

        else:
            st.info("No se encontraron resultados válidos en los PDFs.")

    elif analizar_btn:
        st.warning("⚠️ Asegúrate de escribir qué perfil buscas y cargar al menos un PDF.")
    else:
        st.markdown("<br><br><br><h3 style='text-align:center; color:#333;'>Carga la configuración y presiona 'INICIAR ESCANEO' para activar Nexus Talent Processor.</h3>", unsafe_allow_html=True)
