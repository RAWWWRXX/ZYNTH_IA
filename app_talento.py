import streamlit as st
import pandas as pd
from openai import OpenAI
import fitz  # PyMuPDF
from io import BytesIO

# Configuración de página estilo "Dark Mode" Premium
st.set_page_config(page_title="ZYNTH Enterprise IA", page_icon="💎", layout="wide")

# Estilo CSS Personalizado (Neon ZYNTH Style)
st.markdown("""
    <style>
    .main { background-color: #0E1117; color: #00FF00; }
    .stButton>button { background-color: #00FF00; color: black; border-radius: 10px; font-weight: bold; }
    .stTextInput>div>div>input { background-color: #1A1C24; color: white; border: 1px solid #00FF00; }
    h1, h2, h3 { color: #00FF00 !important; font-family: 'Courier New', monospace; }
    </style>
    """, unsafe_allow_html=True)

st.title("💎 ZYNTH ENTERPRISE IA")
st.subheader("High-Performance Talent Processor v1.0")

# --- SEGURIDAD ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    password = st.text_input("ENTER ACCESS KEY:", type="password")
    if password == "ZYNTH2026":
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.warning("SYSTEM LOCKED. PLEASE ENTER CREDENTIALS.")
        st.stop()

# --- CONFIGURACIÓN DE IA ---
# Toma la clave desde los Secrets de Streamlit que configuramos
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def analyze_cv(text):
    prompt = f"""
    Eres un experto en Reclutamiento de IT. Analiza el siguiente CV y extrae:
    1. Nombre del candidato.
    2. Un puntaje de 1 a 100 basado en su experiencia.
    3. Correo electrónico.
    4. Teléfono.
    5. Un breve análisis de 1 frase.
    6. Veredicto: (CONTRATAR, ENTREVISTAR o RECHAZAR).
    7. Motivo: Por qué diste ese veredicto.

    CV: {text}
    
    Responde ÚNICAMENTE en este formato exacto:
    Nombre: [Nombre] | Puntaje: [0-100] | Correo: [Email] | Telefono: [Tel] | Analisis: [Texto] | Veredicto: [Veredicto] | Motivo: [Texto]
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# --- INTERFAZ DE CARGA ---
uploaded_files = st.file_uploader("Arrastra los CVs de los candidatos (PDF)", accept_multiple_files=True, type=['pdf'])

if uploaded_files:
    if st.button("🚀 INICIAR PROCESAMIENTO MASIVO"):
        results = []
        progress_bar = st.progress(0)
        
        for i, file in enumerate(uploaded_files):
            with st.spinner(f"Procesando: {file.name}..."):
                text = extract_text_from_pdf(file)
                analysis = analyze_cv(text)
                
                # Limpiar la respuesta para el Excel
                parts = analysis.split(" | ")
                res_dict = {
                    "NOMBRE": parts[0].split(": ")[1],
                    "PUNTAJE": parts[1].split(": ")[1],
                    "VEREDICTO": parts[5].split(": ")[1],
                    "MOTIVO": parts[6].split(": ")[1],
                    "CORREO": parts[2].split(": ")[1],
                    "TELÉFONO": parts[3].split(": ")[1],
                    "ANÁLISIS": parts[4].split(": ")[1],
                    "ARCHIVO": file.name
                }
                results.append(res_dict)
                progress_bar.progress((i + 1) / len(uploaded_files))

        df = pd.DataFrame(results)
        st.success("✅ PROCESAMIENTO COMPLETADO")
        st.dataframe(df)

        # --- GENERACIÓN DE EXCEL PREMIUM ---
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='ZYNTH_DATA')
            
            workbook  = writer.book
            worksheet = writer.sheets['ZYNTH_DATA']
            
            # Formatos de diseño
            header_format = workbook.add_format({
                'bold': True, 
                'bg_color': '#000000', 
                'font_color': '#00FF00',
                'border': 1
            })
            
            cell_format = workbook.add_format({'border': 1})

            # Auto-ajuste de columnas para que no se vea amontonado
            for i, col in enumerate(df.columns):
                # Calculamos el largo máximo del contenido en esa columna
                max_len = max(df[col].astype(str).map(len).max(), len(col)) + 5
                worksheet.set_column(i, i, max_len, cell_format)
                # Aplicamos el estilo neón al encabezado
                worksheet.write(0, i, col, header_format)

        data = output.getvalue()
        
        st.download_button(
            label="📥 DESCARGAR REPORTE PREMIUM EXCEL",
            data=data,
            file_name="Reporte_ZYNTH_IA.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
