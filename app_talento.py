import streamlit as st
import pandas as pd
from openai import OpenAI
import fitz
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import stripe

# --- CONFIGURACIÓN DE APIS ---
stripe.api_key = st.secrets["STRIPE_API_KEY"]
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- IDs DE PRECIOS REALES (LIVE) ---
ID_BUSINESS_ELITE = "price_1TDsW5Ra9HsPj8S8DjjHLUDV" # $3,999 MXN
ID_BUSINESS_STARTER = "price_1TDsXsRa9HsPj8S83TKH7aNS" # $2,199 MXN

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ZYNTH Enterprise IA", page_icon="💎", layout="wide")

# --- DISEÑO NEÓN LIMPIO ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: white; }
    .main-card {
        border-radius: 15px;
        padding: 30px;
        background-color: #0a0a0a;
        text-align: center;
        min-height: 350px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .starter-card { border: 2px solid #00FF00; box-shadow: 0px 0px 15px rgba(0, 255, 0, 0.3); }
    .elite-card { border: 2px solid #00e5ff; box-shadow: 0px 0px 15px rgba(0, 229, 255, 0.3); }
    div.stButton > button {
        background-color: #00FF00 !important;
        color: black !important;
        border-radius: 25px !important;
        font-weight: bold !important;
        height: 50px !important;
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
            success_url=f'https://{st.secrets["APP_URL"]}/?pago=exitoso&id={price_id}',
            cancel_url=f'https://{st.secrets["APP_URL"]}/?pago=cancelado',
        )
        return session.url
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# --- LÓGICA DE PAGO ---
qp = st.query_params
if qp.get("pago") == "exitoso":
    st.balloons()
    pid = qp.get("id")
    if pid == ID_BUSINESS_ELITE: st.session_state.creditos += 500
    elif pid == ID_BUSINESS_STARTER: st.session_state.creditos += 200
    st.success("✅ CRÉDITOS ACTIVADOS EXITOSAMENTE")
    st.query_params.clear()

# --- INTERFAZ DE PLANES ---
st.title("💎 ZYNTH ENTERPRISE IA")

if st.session_state.creditos <= 0:
    st.subheader("⚡ ACCESO RESTRINGIDO: SELECCIONA TU PLAN")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="main-card starter-card">
            <h2 style="color: #00FF00;">🚀 BUSINESS STARTER</h2>
            <h1 style="color: white;">$2,199 MXN</h1>
            <p style="font-size: 18px;">• 200 Escaneos de CV<br>• IA Adaptativa Standard</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("ADQUIRIR STARTER", key="btn_starter", use_container_width=True):
            url = crear_pago(ID_BUSINESS_STARTER)
            if url: st.link_button("Ir a la pasarela 💳", url, use_container_width=True)

    with col2:
        st.markdown(f"""
        <div class="main-card elite-card">
            <h2 style="color: #00e5ff;">💎 BUSINESS ELITE</h2>
            <h1 style="color: white;">$3,999 MXN</h1>
            <p style="font-size: 18px;">• 500 Escaneos Premium<br>• Procesamiento Masivo Elite</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("ADQUIRIR ELITE", key="btn_elite", use_container_width=True):
            url = crear_pago(ID_BUSINESS_ELITE)
            if url: st.link_button("Ir a la pasarela 💳", url, use_container_width=True)
    st.stop()

# --- LÓGICA DE PROCESAMIENTO IA ---
def procesar_cv_ia(file, perfil_busqueda):
    try:
        pdf_data = file.read()
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        texto = "".join([page.get_text() for page in doc])[:7000]
        prompt = f"Analiza este CV para la vacante: {perfil_busqueda}. Responde estrictamente: Nombre | Teléfono | Correo | Puntaje (1-10) | Veredicto | Motivo corto. CV: {texto}"
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        r = res.choices[0].message.content.split(" | ")
        return {"NOMBRE": r[0], "TELÉFONO": r[1], "CORREO": r[2], "PUNTAJE": r[3], "VEREDICTO": r[4], "MOTIVO": r[5]}
    except:
        return None

# --- PANEL DE TRABAJO ---
st.sidebar.metric("Saldo actual", f"{st.session_state.creditos} CVs")
st.write("---")
perfil = st.text_area("🎯 Perfil buscado (ej: Gerente de Ventas):")
archivos = st.file_uploader("📂 Sube los currículums (PDF)", accept_multiple_files=True, type=["pdf"])

if st.button("🚀 INICIAR ESCANEO"):
    if archivos and perfil and len(archivos) <= st.session_state.creditos:
        resultados = []
        barra = st.progress(0)
        with ThreadPoolExecutor(max_workers=10) as ex:
            futuros = [ex.submit(procesar_cv_ia, f, perfil) for f in archivos]
            for i, f in enumerate(futuros):
                res = f.result()
                if res:
                    resultados.append(res)
                    st.session_state.creditos -= 1
                barra.progress((i + 1) / len(archivos))
        st.dataframe(pd.DataFrame(resultados), use_container_width=True)
    else:
        st.error("Revisa tus créditos o archivos subidos.")
