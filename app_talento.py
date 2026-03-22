import streamlit as st
import pandas as pd
from openai import OpenAI
import fitz 
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURACIÓN ZYNTH ---
st.set_page_config(page_title="ZYNTH Enterprise IA", page_icon="💎", layout="wide")

# --- LOGIN SEGURO ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align:center; color:#00FF00; font-family:Orbitron;'>ZYNTH ACCESS</h1>", unsafe_allow_html=True)
    clave = st.text_input("PASSWORD:", type="password")
    if clave == "ZYNTH2026":
        st.session_state.autenticado = True
        st.rerun()
    st.stop()

# --- MOTOR DE INTELIGENCIA ADAPTATIVA ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def procesar_cv_adaptativo(file, industria_reqs):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        texto_cv = " ".join([p.get_text() for p in doc])[:8000]
        
        # Este prompt hace que la IA se comporte como experto en la industria que el usuario pida
        prompt = f"""
        Actúa como un reclutador experto en la siguiente industria/perfil: {industria_reqs}
        Analiza el CV adjunto y extrae los datos de contacto.
        
        RESPONDE ÚNICAMENTE ASÍ:
        Nombre: [N] | Teléfono: [T] | Correo: [C] | Puntaje: [0-100] | Veredicto: [V] | Motivo: [M]
        
        CV: {texto_cv}
        """
        
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        r = res.choices[0].message.content.split(" | ")
        return {
            "NOMBRE": r[0].split(": ")[1],
            "TELÉFONO": r[1].split(": ")[1],
            "CORREO": r[2].split(": ")[1],
            "PUNTAJE": int(''.join(filter(str.isdigit, r[3]))),
            "VEREDICTO": r[4].split(": ")[1],
            "MOTIVO": r[5].split(": ")[1]
        }
    except: return None

# --- INTERFAZ ---
st.markdown("<h1 style='text-align:center; color:#00FF00;'>ZYNTH ENTERPRISE</h1>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 2])

with col1:
    st.info("💡 Consejo: Describe bien el negocio (comida, ropa, tech) para que la IA filtre mejor.")
    perfil = st.text_area("Descripción de la vacante e industria:", height=200)
    archivos = st.file_uploader("Subir base de datos (PDFs)", accept_multiple_files=True)
    btn = st.button("🚀 INICIAR ESCANEO MULTI-INDUSTRIA")

with col2:
    if btn and archivos and perfil:
        resultados = []
        barra = st.progress(0)
        with ThreadPoolExecutor(max_workers=10) as exe:
            futuros = [exe.submit(procesar_cv_adaptativo, f, perfil) for f in archivos]
            for i, f in enumerate(futuros):
                res = f.result()
                if res: resultados.append(res)
                barra.progress((i + 1) / len(archivos))
        
        if resultados:
            df = pd.DataFrame(resultados).sort_values("PUNTAJE", ascending=False)
            # Orden para el Excel solicitado
            df = df[["NOMBRE", "TELÉFONO", "CORREO", "PUNTAJE", "VEREDICTO", "MOTIVO"]]
            st.dataframe(df, use_container_width=True)

            # --- EXCEL CON FORMATO ZYNTH ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='ZYNTH_Nexus')
                wb, ws = writer.book, writer.sheets['ZYNTH_Nexus']
                
                # Celdas verdes y anchas
                fmt_head = wb.add_format({'bold':True, 'bg_color':'#00FF00', 'border':1})
                fmt_txt = wb.add_format({'text_wrap': True, 'valign': 'top'})
                
                ws.set_column('A:A', 30, fmt_txt) # Nombre
                ws.set_column('B:C', 25, fmt_txt) # Tel y Correo
                ws.set_column('D:E', 15, fmt_txt) # Score y Ver
                ws.set_column('F:F', 60, fmt_txt) # Motivo
                
                for i, col in enumerate(df.columns):
                    ws.write(0, i, col, fmt_head)

            st.download_button("📥 DESCARGAR BASE DE DATOS", output.getvalue(), "ZYNTH_Report.xlsx")
