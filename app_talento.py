import streamlit as st
import stripe
import time

# 1. CONFIGURACIÓN DE LLAVES (Saca todo de st.secrets)
stripe.api_key = st.secrets["STRIPE_API_KEY"]
ID_ELITE = "price_1TDs0FDumVuheYnZt2zgHmcW"
ID_STARTER = "price_1TDryXDumVuheYnZysomqD7R"
APP_URL = "zynthia-bpxt95pcezahkpuhzgjes.streamlit.app"

# 2. INICIALIZACIÓN DE ESTADO
if "creditos" not in st.session_state:
    st.session_state.creditos = 0

# 3. DETECTOR AUTOMÁTICO DE PAGO (Aquí ocurre la magia)
# Si Stripe te regresa con ?pago=exitoso, esto se activa solo
query_params = st.query_params
if query_params.get("pago") == "exitoso":
    st.session_state.creditos = 500  # Asignamos los créditos de una
    st.balloons()
    st.success("✅ ¡PAGO CONFIRMADO! CRÉDITOS ACTIVADOS.")
    # Limpiamos la URL para que no de error de acceso al refrescar
    st.query_params.clear()
    time.sleep(2)
    st.rerun()

# 4. INTERFAZ DE USUARIO
st.set_page_config(page_title="ZYNTH IA", layout="wide")
st.title("💎 ZYNTH ENTERPRISE IA")

# Sidebar con el saldo real
st.sidebar.metric("Saldo Disponible", f"{st.session_state.creditos} CVs")

# --- FLUJO A: SI NO TIENE CRÉDITOS ---
if st.session_state.creditos <= 0:
    st.warning("⚠️ No tienes créditos suficientes para procesar CVs.")
    st.subheader("Adquiere un Plan para Desbloquear el Escaneo")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("🚀 Business Starter")
        if st.button("Comprar Starter ($2,199)"):
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{'price': ID_STARTER, 'quantity': 1}],
                mode='subscription',
                success_url=f"https://{APP_URL}/?pago=exitoso", # URL limpia
                cancel_url=f"https://{APP_URL}/",
            )
            st.link_button("Ir a Pago Seguro 💳", session.url)

    with col2:
        st.info("💎 Business Elite")
        if st.button("Comprar Elite ($3,999)"):
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{'price': ID_ELITE, 'quantity': 1}],
                mode='subscription',
                success_url=f"https://{APP_URL}/?pago=exitoso",
                cancel_url=f"https://{APP_URL}/",
            )
            st.link_button("Ir a Pago Seguro 💳", session.url)

# --- FLUJO B: SI YA PAGÓ Y TIENE CRÉDITOS ---
else:
    st.success(f"SISTEMA DESBLOQUEADO - {st.session_state.creditos} Créditos")
    
    # SECCIÓN DE SUBIDA DE PDFS
    st.subheader("📤 Carga de Currículums (PDF)")
    archivos = st.file_uploader("Arrastra los PDF aquí", type=["pdf"], accept_multiple_files=True)
    
    if archivos:
        st.write(f"Has seleccionado {len(archivos)} archivos.")
        if st.button("🚀 Iniciar Análisis con IA"):
            if len(archivos) > st.session_state.creditos:
                st.error("No tienes suficientes créditos para tantos archivos.")
            else:
                with st.spinner("Analizando perfiles..."):
                    # Aquí va tu lógica de lectura de PDF y OpenAI
                    time.sleep(3) # Simulación
                    st.session_state.creditos -= len(archivos)
                    st.success("Análisis completado.")
                    st.rerun()

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.creditos = 0
        st.rerun()
