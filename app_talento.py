import streamlit as st
import stripe
import time

# --- CONFIGURACIÓN DE IDs CORREGIDA ---
# Estos son los IDs que me pasaste (Business Elite y Starter)
ID_ELITE = "price_1TDs0FDumVuheYnZt2zgHmcW"
ID_STARTER = "price_1TDryXDumVuheYnZysomqD7R"

# Tu URL de Streamlit (asegúrate que sea esta la que usas)
APP_URL = "zynthia-bpxt95pcezahkpuhzgjes.streamlit.app"

# Configurar Stripe desde Secrets
stripe.api_key = st.secrets["STRIPE_API_KEY"]

if "creditos" not in st.session_state:
    st.session_state.creditos = 0

# --- DETECTAR REGRESO DE STRIPE ---
qp = st.query_params
if "pago" in qp and qp["pago"] == "exitoso":
    # Asignar créditos según el ID que regresa
    if qp.get("id") == ID_ELITE:
        st.session_state.creditos = 500
    elif qp.get("id") == ID_STARTER:
        st.session_state.creditos = 200
    
    st.balloons()
    st.success("💎 ¡PAGO EXITOSO! CRÉDITOS CARGADOS.")
    # Limpiar la URL para evitar errores de acceso
    st.query_params.clear()
    time.sleep(2)
    st.rerun()

# --- INTERFAZ ---
st.title("💎 ZYNTH IA")

if st.session_state.creditos == 0:
    st.subheader("Selecciona tu Plan")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("🚀 STARTER - $2,199")
        if st.button("Pagar Starter"):
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{'price': ID_STARTER, 'quantity': 1}],
                mode='subscription', # Modo correcto para tus precios
                success_url=f"https://{APP_URL}/?pago=exitoso&id={ID_STARTER}",
                cancel_url=f"https://{APP_URL}/",
            )
            st.link_button("Ir a Stripe 💳", session.url)

    with col2:
        st.info("💎 ELITE - $3,999")
        if st.button("Pagar Elite"):
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{'price': ID_ELITE, 'quantity': 1}],
                mode='subscription',
                success_url=f"https://{APP_URL}/?pago=exitoso&id={ID_ELITE}",
                cancel_url=f"https://{APP_URL}/",
            )
            st.link_button("Ir a Stripe 💳", session.url)
else:
    st.sidebar.metric("Saldo actual", f"{st.session_state.creditos} CVs")
    st.success("¡Bienvenido, Paolo! Sistema desbloqueado.")
    if st.button("Reiniciar Créditos"):
        st.session_state.creditos = 0
        st.rerun()
