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
    
    .main { background-color: #050505; color: #e0e0e0; font-family: 'Roboto', sans-serif; }
    
    h1 { font-family: 'Orbitron', sans-serif; color: #00FF00 !important; text-align: center; text-transform: uppercase; letter-spacing: 4px; text-shadow: 0 0 15px #00FF00; margin-bottom: 0px;}
    h3 { font-family: 'Roboto', sans-serif; color: #888 !important; text-align: center; font-weight: 300; letter-spacing: 2px; margin-top: 0px; margin-bottom: 30px;}
    h4 { color: #00FF00 !important; font-family: 'Orbitron', sans-serif; letter-spacing: 2px; border-bottom: 1px solid #333; padding-bottom: 10px; margin-top: 20px;}

    .stButton>button { 
        background: linear-gradient(45deg, #00FF00, #00CC00); color: black; border-radius: 5px; 
        font-family: 'Orbitron', sans-serif; font-weight: bold; width: 100%; border: none; padding: 12px;
        transition: 0.3s; text-transform: uppercase; letter-spacing: 2px; box-shadow: 0 0 10px rgba(0,255,0,0.5);
    }
    .stButton>button:hover { background: linear-gradient(45deg, #00CC00, #00FF00); transform: scale(1.03); box-shadow: 0 0 20px #00FF00; }

    .stTextInput>div>div>input, .stTextArea>div>div>textarea { 
        background-color: #101010; color: #00FF00; border: 1px solid #333; font-family: 'Roboto', sans-serif; border-radius: 5px;
    }
    
    .stDataFrame { background-color: #101010; border: 1px solid #333; border-radius: 5px; }
    
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
        password = st.text_input("INGRESE ACCESS KEY (ENCRIPTADO):", type="password")
        if password == "ZYNTH2026":
            st.session_state.authenticated = True
            st.rerun()
        elif password:
            st.error("KEY INCORRECTA. ACCESO DENEGADO.")
        st.stop()

# --- CONFIGURACIÓN DE IA ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def extract_text_from_pdf(pdf_file):
    try:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        return "".join([page.get_text() for page in doc])[:10000]
    except:
        return ""

def analyze_cv(text, user_requirements):
    prompt = f"""
    Eres el motor de IA de ZYNTH Enterprise. Analiza este CV basándote en: "{user_requirements}".
    Extrae la info y asigna puntaje 0-100.
    
    RESPONDE EXCLUSIVAMENTE ASÍ:
    Nombre: [N] | Puntaje: [P] | Veredicto: [V] | Motivo: [M] | Correo: [C] | Telefono: [T]
    
    CV: {text}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

# --- INTERFAZ ---
col_config, col_display = st.columns([1, 2.2])

with col_config:
    st.markdown("#### ⚙️ CONFIGURACIÓN")
    reqs = st.text_area("¿Qué perfil buscas?", placeholder="Ej: Ingeniero de Software...", height=150)
    uploaded_files = st.file_uploader("CARGAR CVS (PDF)", accept_multiple_files=True, type=['pdf'])
    analizar_btn = st.button("🚀 INICIAR ESCANEO ZYNTH")

with col_display:
    if uploaded_files and reqs and analizar_btn:
        results = []
        progress_bar = st.progress(0)
        
        for i, file in enumerate(uploaded_files):
            text = extract_text_from_pdf(file)
            analysis = analyze_cv(text, reqs)
            
            try:
                parts = analysis.split(" | ")
                results.append({
                    "NOMBRE": parts[0].split(": ")[1],
                    "PUNTAJE": int(''.join(filter(str.isdigit, parts[1].split(": ")[1]))),
                    "VEREDICTO": parts[2].split(": ")[1],
                    "MOTIVO": parts[3].split(": ")[1],
                    "CORREO": parts[4].split(": ")[1],
                    "TELÉFONO": parts[5].split(": ")[1]
                })
            except:
                continue
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        if results:
            df = pd.DataFrame(results).sort_values(by="PUNTAJE", ascending=False)
            
            # Gráfica Horizontal Premium
            fig = px.bar(df.head(10), x='PUNTAJE', y='NOMBRE', orientation='h',
                         color='PUNTAJE', color_continuous_scale=['#003300', '#00FF00'],
                         template="plotly_dark", title="TOP TALENTO")
            fig.update_layout(yaxis={'autorange': "reversed"}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df, use_container_width=True)

            # Excel Premium
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='ZYNTH_DATA')
                workbook, worksheet = writer.book, writer.sheets['ZYNTH_DATA']
                header_fmt = workbook.add_format({'bold': True, 'bg_color': '#000000', 'font_color': '#00FF00', 'border': 1})
                for i, col in enumerate(df.columns):
                    worksheet.set_column(i, i, 20)
                    worksheet.write(0, i, col, header_fmt)
            
            st.download_button("📥 DESCARGAR REPORTE EXCEL", output.getvalue(), "ZYNTH_Report.xlsx")

    elif analizar_btn:
        st.warning("⚠️ Carga archivos y escribe el perfil.")
    else:
        st.markdown("<h3 style='color:#444 !important; margin-top:100px;'>Esperando activación de Nexus...</h3>", unsafe_allow_html=True)
