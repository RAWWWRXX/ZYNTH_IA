import streamlit as st
import fitz
from openai import OpenAI
import pandas as pd
import io
import re
import time 
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- ESTILO NEÓN GAMER / PREMIUM ---
st.set_page_config(page_title="ZYNTH Enterprise", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .stButton>button { 
        background-color: #00ffcc; color: black; 
        border-radius: 8px; border: none; font-weight: bold;
        transition: 0.3s; width: 100%;
    }
    .stButton>button:hover { background-color: #00cca3; transform: scale(1.02); }
    .stTextInput>div>div>input { background-color: #1a1c23; color: #00ffcc; border: 1px solid #333; }
    .stProgress > div > div > div > div { background-color: #00ffcc; }
    h1, h2, h3 { color: #00ffcc; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

# --- SEGURIDAD ---
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

def check_password():
    if not st.session_state["password_correct"]:
        with st.container():
            st.title("🔒 ZYNTH PRIVATE ACCESS")
            pw = st.text_input("PASSWORD MAESTRA:", type="password")
            if st.button("DESBLOQUEAR SISTEMA"):
                if pw == "ZYNTH2026":
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("❌ ACCESO DENEGADO")
        return False
    return True

if check_password():
    # CONFIGURACIÓN DE API
    client = OpenAI(api_key="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")

    st.title("⚡ ZYNTH ENTERPRISE IA")
    st.write("### Sistema de Procesamiento de Talento de Alto Nivel")

    col1, col2 = st.columns([1, 2])
    with col1:
        perfil = st.text_area("🎯 PERFIL OBJETIVO:", "Ej: Ingeniero de Software SR...", height=150)
        hilos = st.slider("POTENCIA (HILOS SIMULTÁNEOS):", 1, 15, 2)
        st.caption("Recomendado: 2-4 para estabilidad máxima.")
    with col2:
        uploaded_files = st.file_uploader("📂 CARGAR CVs EN PDF:", type="pdf", accept_multiple_files=True)

    def process_cv(file, p_texto):
        try:
            with fitz.open(stream=file.read(), filetype="pdf") as doc:
                texto = " ".join([pag.get_text() for pag in doc[:2]])[:3000]
            
            prompt = f"Analiza para: {p_texto}. Responde: NOMBRE: [N] | CORREO: [E] | TEL: [T] | PUNTAJE: [0-100] | ANALISIS: [30 palabras] | VIRTUD: [V]"
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"{prompt}\n\nTexto: {texto}"}],
                temperature=0
            )
            res = response.choices[0].message.content
            
            def find_v(p, t):
                match = re.search(p, t, re.IGNORECASE)
                return match.group(1).strip() if match else "N/A"

            return {
                "NOMBRE": find_v(r'NOMBRE:\s*(.*?)(?:\||$)', res),
                "PUNTAJE": int(re.search(r'PUNTAJE:\s*(\d+)', res).group(1)) if re.search(r'PUNTAJE:\s*(\d+)', res) else 0,
                "CORREO": find_v(r'CORREO:\s*(.*?)(?:\||$)', res),
                "TELÉFONO": find_v(r'TEL:\s*(.*?)(?:\||$)', res),
                "ANÁLISIS": find_v(r'ANALISIS:\s*(.*?)(?:\||$)', res),
                "ARCHIVO": file.name
            }
        except: return None

    if st.button("🚀 INICIAR PROCESAMIENTO MASIVO") and uploaded_files:
        resultados = []
        barra = st.progress(0)
        status = st.empty()
        
        with ThreadPoolExecutor(max_workers=hilos) as executor:
            futures = {executor.submit(process_cv, f, perfil): f for f in uploaded_files}
            for i, future in enumerate(as_completed(futures)):
                r = future.result()
                if r: resultados.append(r)
                barra.progress((i + 1) / len(uploaded_files))
                status.markdown(f"**⚡ PROCESADOS:** {i+1} / {len(uploaded_files)}")

        if resultados:
            st.success("✅ ANÁLISIS COMPLETADO")
            df = pd.DataFrame(resultados).sort_values(by="PUNTAJE", ascending=False)
            
            # --- BUSCADOR EN VIVO ---
            st.markdown("### 🔍 BUSCADOR DE TALENTO")
            query = st.text_input("Filtrar candidatos por cualquier dato:")
            df_view = df[df.apply(lambda row: row.astype(str).str.contains(query, case=False).any(), axis=1)] if query else df
            
            st.dataframe(df_view, use_container_width=True)

            # --- DESCARGA ---
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='ZYNTH_DATA')
            st.download_button("📥 DESCARGAR REPORTE EXCEL", output.getvalue(), "ZYNTH_REPORT.xlsx")

st.sidebar.markdown("---")
st.sidebar.write("Developed by **ZYNTH MX**")