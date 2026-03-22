import streamlit as st
import pandas as pd
from openai import OpenAI
import fitz  # PyMuPDF
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import stripe

# --- CONFIGURACIÓN DE APIS ---
stripe.api_key = st.secrets["STRIPE_API_KEY"]
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- IDs DE PRECIOS ---
ID_BUSINESS = "price_1TDs0FDumVuheYnZt2zgHmcW"
ID_STARTER = "price_1TDryXDumVuheYnZysomqD7R"

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ZYNTH Enterprise IA", page_icon="💎", layout="wide")

# --- ESTILO CSS PROFESIONAL ---
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 20px; font-weight: bold; }
    .plan-card {
        border: 1px solid #444;
        border-radius: 15px;
        padding: 20px;
        background-color: #111;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZAR CRÉDITOS ---
if "creditos" not in st.session_state:
    st.session_state.creditos = 0

# --- FUNCIÓN DE PAGO ---
def crear_pago(price_id):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='payment',
            success_url='https://zynthia-bpxt95pcezahkpuhzgjes.streamlit.app/?pago=exitoso',
            cancel_url='https://zynthia-bpxt95pcezahkpuhzgjes.streamlit.app/?pago=cancelado',
        )
        return session.url
    except Exception as e:
        st.error(f"Error de conexión con Stripe: {e}")
        return None

# --- VERIFICAR RESULTADO DEL PAGO ---
query_params = st.query_params
if query_params.get("pago") == "exitoso":
    st.balloons()
    st.success("💎 ¡PAGO CONFIRMADO! Tus créditos han sido activados.")
    # Sumamos 500 por defecto si detectamos éxito (puedes ajustar según el precio)
    st.session_state.creditos += 100 
    st.query_params.clear()

# --- LÓGICA DE PROCESAMIENTO IA ---
def procesar_cv_ia(file, perfil_busqueda):
    try:
        # Leer PDF
        pdf_data = file.read()
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        texto = ""
        for page in doc:
            texto += page.get_text()
        texto = texto[:7000] # Límite para no saturar la IA
        
        prompt = f"Analiza este CV para la vacante: {perfil_busqueda}. Responde estrictamente en este formato: Nombre | Teléfono | Correo | Puntaje (1-10) | Veredicto (Contratar/Rechazar) | Motivo corto. CV: {texto}"
        
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        
        r = res.choices[0].message.content.split(" | ")
        return {
            "NOMBRE": r[0], "TELÉFONO": r[1], "CORREO": r[2],
            "PUNTAJE": r[3], "VEREDICTO": r[4], "MOTIVO": r[5]
        }
    except Exception as e:
        return {"NOMBRE": f"Error: {file.name}", "MOTIVO": str(e)}

# --- INTERFAZ PRINCIPAL ---
st.title("💎 ZYNTH ENTERPRISE IA")
st.sidebar.metric("Saldo de Escaneos", f"{st.session_state.creditos} CVs")

# Pantalla de Compra si no hay créditos
if st.session_state.creditos <= 0:
    st.markdown("### ⚡ NO TIENES CRÉDITOS ACTIVOS")
    st.write("Selecciona un plan para desbloquear el poder de la IA en tus contrataciones.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container():
            st.markdown('<div class="plan-card">', unsafe_allow_html=True)
            st.subheader("🚀 STARTER")
            st.write("### $499 MXN")
            st.write("- **100** Escaneos de CV")
            st.write("- Extracción de contacto completa")
            st.write("- IA Adaptativa Standard")
            if st.button("ADQUIRIR STARTER"):
                url = crear_pago(ID_STARTER)
                if url:
                    st.link_button("Ir a pagar 💳", url)
            st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        with st.container():
            st.markdown('<div class="plan-card" style="border-color: #00e5ff;">', unsafe_allow_html=True)
            st.subheader("💎 BUSINESS")
            st.write("### $3,500 MXN")
            st.write("- **500** Escaneos Premium")
            st.write("- Procesamiento Masivo Ultra-rápido")
            st.write("- Análisis de Perfil Elite")
            if st.button("ADQUIRIR BUSINESS"):
                url = crear_pago(ID_BUSINESS)
                if url:
                    st.link_button("Ir a pagar 💳", url)
            st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- ÁREA DE TRABAJO (Solo si hay créditos) ---
st.write("---")
perfil = st.text_area("🎯 Describe el perfil que buscas (ej: Desarrollador Python o Chef parrillero):")
archivos = st.file_uploader("📂 Sube los currículums (PDF)", accept_multiple_files=True, type=["pdf"])

if st.button("🚀 INICIAR ESCANEO MASIVO"):
    if archivos and perfil:
        if len(archivos) <= st.session_state.creditos:
            resultados = []
            barra = st.progress(0)
            status = st.empty()
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futuros = [executor.submit(procesar_cv_ia, f, perfil) for f in archivos]
                for i, f in enumerate(futuros):
                    status.text(f"Procesando archivo {i+1} de {len(archivos)}...")
                    analisis = f.result() # LÍNEA 131 ARREGLADA
                    if analisis:
                        resultados.append(analisis)
                        st.session_state.creditos -= 1
                    barra.progress((i + 1) / len(archivos))
            
            status.success("✅ Escaneo completado.")
            df = pd.DataFrame(resultados)
            st.dataframe(df, use_container_width=True)
            
            # Botón de descarga
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Reporte Excel/CSV", csv, "reporte_zynth.csv", "text/csv")
        else:
            st.error(f"Necesitas {len(archivos)} créditos, pero solo tienes {st.session_state.creditos}.")
