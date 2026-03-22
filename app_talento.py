import streamlit as st
import pandas as pd
from openai import OpenAI
import fitz
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import stripe
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ZYNTH Enterprise IA", page_icon="💎", layout="wide")

# --- ESTILOS CSS (FONDO NEGRO Y NEÓN) ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: white; }
    .main-card {
        border-radius: 15px; padding: 30px; background-color: #0a0a0a;
        text-align: center; min-height: 350px;
        display: flex; flex-direction: column; justify-content: center;
    }
    .starter-card { border: 2px solid #00FF00; box-shadow: 0px 0px 15px rgba(0, 255, 0, 0.3); }
    .elite-card { border: 2px solid #00e5ff; box-shadow: 0px 0px 15px rgba(0, 229, 255, 0.3); }
    div.stButton > button {
        background-color: #00FF00 !important; color: black !important;
        border-radius: 25px !important; font-weight: bold !important; height: 50px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZAR ESTADOS ---
if "creditos" not in st.session_state:
    st.session_state.creditos = 0
if "pago_verificado" not in st.session_state:
    st.session_state.pago_verificado = False

# --- FUNCIÓN DE VERIFICACIÓN DE CLAVES ---
def verificar_claves():
    try:
        if not st.secrets["STRIPE_API_KEY"] or not st.secrets["OPENAI_API_KEY"]:
            st.error("🚨 FALTAN CLAVES API EN LOS SECRETS.")
            st.stop()
        
        # Configurar APIs
        stripe.api_key = st.secrets["STRIPE_API_KEY"]
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # Verificar si la clave es de prueba o real
        if stripe.api_key.startswith("sk_test_"):
            st.warning("⚠️ ESTÁS EN MODO DE PRUEBA. LOS PAGOS NO SON REALES.")
        elif stripe.api_key.startswith("sk_live_"):
            st.success("✅ ESTÁS EN MODO REAL. LOS PAGOS SON VERDADEROS.")
        else:
            st.error("🚨 LA CLAVE STRIPE_API_KEY NO PARECE VÁLIDA.")
            st.stop()
            
        return client, stripe
        
    except KeyError:
        st.error("🚨 NO SE ENCONTRARON LAS CLAVES 'STRIPE_API_KEY' O 'OPENAI_API_KEY' EN LOS SECRETS.")
        st.stop()
    except Exception as e:
        st.error(f"🚨 ERROR AL VERIFICAR LAS CLAVES: {e}")
        st.stop()

# --- VERIFICAR CLAVES Y OBJETOS DE CLIENTE ---
openai_client, stripe_client = verificar_claves()

# --- IDs DE PRECIOS ---
# Usa sk_test_... para test, sk_live_... para producción
ID_BUSINESS_ELITE = "price_1TDs0FDumVuheYnZt2zgHmcW" # $3,999 MXN
ID_BUSINESS_STARTER = "price_1TDryXDumVuheYnZysomqD7R" # $2,199 MXN

# URL de retorno configurada en Secrets
APP_URL = st.secrets.get("APP_URL", "zynthia-bpxt95pcezahkpuhzgjes.streamlit.app")

# --- FUNCIÓN DE PAGO ---
def crear_pago(price_id, modo_suscripcion=True):
    try:
        # Detectar el modo de pago (subscription o payment)
        modo = 'subscription' if modo_suscripcion else 'payment'
        
        # Crear sesión de pago
        session = stripe_client.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode=modo,
            success_url=f'https://{APP_URL}/?pago=exitoso&id={price_id}',
            cancel_url=f'https://{APP_URL}/?pago=cancelado',
        )
        return session.url
    except Exception as e:
        st.error(f"🚨 Error al crear la sesión de pago: {e}")
        # Ofrecer opción de cambiar el modo de pago si falla
        if "Recurring prices" in str(e) and modo == 'payment':
            st.warning("Intenta cambiar el modo de pago a 'subscription' en el código.")
        return None

# --- LÓGICA DE PAGO ---
# Recuperar parámetros de URL
qp = st.query_params
if qp.get("pago") == "exitoso" and not st.session_state.pago_verificado:
    pid = qp.get("id")
    # Asignar créditos
    if pid == ID_BUSINESS_ELITE:
        st.session_state.creditos += 500
        plan = "BUSINESS ELITE"
    elif pid == ID_BUSINESS_STARTER:
        st.session_state.creditos += 200
        plan = "BUSINESS STARTER"
    else:
        plan = "PLAN DESCONOCIDO"

    st.success(f"✅ ¡PAGO EXITOSO DEL PLAN {plan}! SE HAN AÑADIDO TUS CRÉDITOS.")
    st.session_state.pago_verificado = True
    st.balloons()
    
    # Limpiar parámetros de URL para evitar recargas
    st.query_params.clear()
    time.sleep(2)
    st.rerun()

# --- INTERFAZ ---
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
        # Cambiar el modo de pago si es recurrente
        if st.button("ADQUIRIR STARTER", key="btn_s"):
            # Usar subscription si es precio recurrente
            url = crear_pago(ID_BUSINESS_STARTER, modo_suscripcion=True)
            if url: st.link_button("Ir a pagar 💳", url, use_container_width=True)

    with col2:
        st.markdown(f"""
        <div class="main-card elite-card">
            <h2 style="color: #00e5ff;">💎 BUSINESS ELITE</h2>
            <h1 style="color: white;">$3,999 MXN</h1>
            <p style="font-size: 18px;">• 500 Escaneos Premium<br>• Procesamiento Masivo Elite</p>
        </div>
        """, unsafe_allow_html=True)
        # Cambiar el modo de pago si es recurrente
        if st.button("ADQUIRIR ELITE", key="btn_e"):
            # Usar subscription si es precio recurrente
            url = crear_pago(ID_BUSINESS_ELITE, modo_suscripcion=True)
            if url: st.link_button("Ir a pagar 💳", url, use_container_width=True)
    st.stop()

# --- PANEL DE TRABAJO ---
# Sidebar para mostrar créditos
st.sidebar.metric("Saldo actual", f"{st.session_state.creditos} CVs")

st.write("---")
# Aquí sigue tu lógica de procesamiento...
