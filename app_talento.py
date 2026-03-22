import streamlit as st
import pandas as pd
from openai import OpenAI
import fitz  # PyMuPDF
from io import BytesIO
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA (WIDE MODE) ---
st.set_page_config(page_title="ZYNTH Enterprise IA", page_icon="💎", layout="wide")

# --- CSS ULTRA-PREMIUM (ESTILO CYBERPUNK) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto:wght@300;400;700&display=swap');
    
    /* Fondo y Texto Base */
    .main { background-color: #050505; color: #e0e0e0; font-family: 'Roboto', sans-serif; }
    
    /* Encabezados Futuristas */
    h1 { font-family: 'Orbitron', sans-serif; color: #00FF00 !important; text-align: center; text-transform: uppercase; letter-spacing: 4px; text-shadow: 0 0 15px #00FF00; margin-bottom: 0px;}
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

# --- HEADER DE MARCA ---
st.markdown("<h1>ZYNTH ENTERPRISE</h1>", unsafe_allow_html=True)
st.markdown("<h3>NEXUS TALENT PROCESSOR // AI EDITION v3.0</h3>", unsafe_allow_html=True)

# --- SEGURIDAD ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.markdown("<h4 style='text-align:center;'>INSTALANDO CONEXIÓN SEGURA...</h4>", unsafe_allow_html=True)
        password = st.text_input("INGRESE ACCESS KEY (ENCRIPTADO):", type="password")
        if password == "ZYNTH2026":
            st.session_state.authenticated = True
            st.rerun()
        elif password:
            st.error("KEY INCORRECTA. ACCESO DENEGADO.")
        st.stop()

# --- CONFIGURACIÓN DE IA ---
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except:
    st.error("ERROR CRÍTICO: No se encontró la API Key en los Secrets.")
    st.stop()

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
    Extrae la información y asigna un puntaje del 0 al 100 de qué tanto cumple con el perfil buscado.
    
    CV TEXTO:
    {text}
    
    RESPONDE EXCLUSIVAMENTE EN ESTE FORMATO (SIN EXPLICACIONES EXTRA):
    Nombre: [Nombre Completo] | Puntaje: [0-100] | Veredicto: [CONTRATAR TOTALMENTE / ENTREVISTAR / RECHAZAR] | Motivo: [Explicación técnica y detallada de por qué tiene ese puntaje basándote en los requisitos] | Correo: [Correo electrónico] | Teléfono: [Número]
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3 # Más preciso, menos creativo
        )
        return response.choices[0].message.content
    except:
        return "Error en la conexión con la IA."

# --- PANEL DE CONTROL ---
col_config, col_display = st.columns([1, 2.2])

with col_config:
    st.markdown("#### ⚙️ CONFIGURACIÓN DE FILTRO")
    reqs = st.text_area("¿Qué perfil buscas hoy? (Sé específico)", placeholder="Ej: Ingeniero de Software Senior con 5 años en Python, experiencia en AWS y que viva en Monterrey...", height=150)
    uploaded_files = st.file_uploader("CARGAR CVS (PDF)", accept_multiple_files=True, type=['pdf'])
    
    analizar_btn = st.button("🚀 INICIAR ESCANEO ZYNTH")

with col_display:
    if uploaded_files and reqs and analizar_btn:
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, file in enumerate(uploaded_files):
            status_text.text(f"Procesando: {file.name}...")
            text = extract_text_from_pdf(file)
            analysis = analyze_cv(text, reqs)
            
            # Limpieza y estructuración de datos
            try:
                parts = analysis.split(" | ")
                nombre = parts[0].split(": ")[1]
                puntaje_str = parts[1].split(": ")[1]
                puntaje = int(''.join(filter(str.isdigit, puntaje_str))) # Extraer solo números
                
                res_dict = {
                    "NOMBRE": nombre,
                    "PUNTAJE": puntaje,
                    "VEREDICTO": parts[2].split(": ")[1],
                    "MOTIVO DETALLADO": parts[3].split(": ")[1],
                    "CORREO": parts[4].split(": ")[1],
                    "TELÉFONO": parts[5].split(": ")[1],
                    "ARCHIVO": file.name
                }
                results.append(res_dict)
            except:
                st.warning(f"No se pudo estructurar el análisis de: {file.name}. La IA respondió: {analysis[:100]}...")
                continue
                
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        status_text.text("Escaneo completado.")
        
        if results:
            df = pd.DataFrame(results)
            df_sorted = df.sort_values(by="PUNTAJE", ascending=False)
            
            # --- VISUALIZACIÓN DE DATOS PREMIUM ---
            st.markdown("#### 📊 RANKING DE TALENTO (NEXUS)")
            
            # Gráfica Horizontal con gradiente neón
            fig = px.bar(df_sorted.head(10), x='PUNTAJE', y='NOMBRE', 
                         orientation='h',
                         color='PUNTAJE',
                         color_continuous_scale=['#003300', '#00FF00', '#FFFF00'], # De verde oscuro a amarillo
                         template="plotly_dark",
                         labels={'PUNTAJE': 'Score (0-100)', 'NOMBRE': 'Candidato'},
                         title="TOP CANDIDATOS")
            
            fig.update_layout(
                font_family="Roboto",
                title_font_family="Orbitron",
                title_font_color="#00FF00",
                xaxis=dict(range=[0, 100], gridcolor='#222'),
                yaxis=dict(gridcolor='#222', autorange="reversed"), # Top 1 arriba
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                coloraxis_showscale=False # Ocultar barra de color lateral
            )
            fig.update_traces(marker_line_color='#00FF00', marker_line_width=1, opacity=0.9)
            
            st.plotly_chart(fig, use_container_width=True)

            # Tabla de datos estilizada
            st.markdown("#### 📄 DETALLE COMPLETO")
            st.dataframe(df_sorted, use_container_width=True)

            # --- EXCEL PREMIUM (STYLIZED) ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_sorted.to_excel(writer, index=False, sheet_name='ZYNTH_Nexus_Data')
                workbook = writer.book
                worksheet = writer.sheets['ZYNTH_Nexus_Data']
                
                # Formatos de Celda
                header_fmt = workbook.add_format({'bold': True, 'bg_color': '#000000', 'font_color': '#00FF00', 'border': 1, 'align': 'center', 'font_name': 'Arial'})
                data_fmt = workbook.add_format({'bg_color': '#101010', 'font_color': '#e0e0e0', 'border': 1, 'font_name': 'Arial', 'text_wrap': True, 'valign': 'top'})
                high_score_fmt = workbook.add_format({'bg_color': '#003300', 'font_color': '#00FF00', 'bold': True, 'border': 1})
                
                # Aplicar formatos y ajustar columnas
                num_rows = len(df_sorted)
                num_cols = len(df_sorted.columns)
                
                for i, col in enumerate(df_sorted.columns):
                    # Ancho automático basado en el texto más largo
                    max_len = max(df_sorted[col].astype(str).map(len).max(), len(col)) + 3
                    if col == "MOTIVO DETALLADO": max_len = 50 # Columna de motivo más ancha
                    
                    worksheet.set_column(i, i, max_len, data_fmt)
                    worksheet.write(0, i, col, header_fmt)

                # Resaltar puntajes altos (más de 80)
                worksheet.conditional_format(1, 1, num_rows, 1, {
                    'type': 'cell', 'criteria': '>=', 'value': 80, 'format': high_score_fmt
                })
            
            st.divider()
            col_dl1, col_dl2 = st.columns([1,1])
            with col_dl1:
                st.download_button("📥 DESCARGAR REPORTE PREMIUM (EXCEL)", output.getvalue(), "ZYNTH_Nexus_Report.xlsx", mime="application/vnd.ms-excel")

        else:
            st.info("No se encontraron resultados válidos en los PDFs.")

    elif analizr_btn:
        st.warning("⚠️ Asegúrate de escribir qué perfil buscas y cargar al menos un PDF.")
    else:
        st.markdown("<br><br><br><h3 style='text-align:center; color:#444 !important;'>Carga la configuración y presiona 'INICIAR ESCANEO' para activar Nexus Talent Processor.</h3>", unsafe_allow_html=True)
