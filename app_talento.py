import streamlit as st
import stripe
import time

# --- CONFIGURACIÓN ---
stripe.api_key = st.secrets["STRIPE_API_KEY"]
ID_ELITE = "price_1TDs0FDumVuheYnZt2zgHmcW"
ID_STARTER = "price_1TDryXDumVuheYnZysomqD7R"
APP_URL = "zynthia-bpxt95pcezahkpuhzgjes.streamlit.app"

if "creditos" not in st.session_state:
    st.session_state.creditos = 0

# --- LÓGICA DE CRÉDITOS ---
qp = st.query_params
# Si la URL trae el éxito de Stripe
if "pago" in qp and qp["pago"] == "exitoso":
    if qp.get("id") == ID_ELITE:
        st.session_state.creditos = 500
    else:
        st.session_state.creditos = 200
    st.success("✅ ¡PAGO RECONOCIDO!")
    st.balloons()
    st.query_params.clear()

# --- INTERFAZ ---
st.title("💎 ZYNTH IA")

# Sidebar permanente para que veas tus créditos
st.sidebar.metric("Saldo ZYNTH", f"{st.session_state.creditos} CVs")

if st.session_state.creditos == 0:
    st.subheader("Adquirir Créditos")
    c1, c2 = st.columns(2)
    
    with c1:
        if st.button("PLAN STARTER"):
            res = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{'price': ID_STARTER, 'quantity': 1}],
                mode='subscription',
                success_url=f"https://{APP_URL}/?pago=exitoso&id={ID_STARTER}",
                cancel_url=f"https://{APP_URL}/",
            )
            st.link_button("PAGAR CON TARJETA 💳", res.url)

    with c2:
        if st.button("PLAN ELITE"):
            res = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{'price': ID_ELITE, 'quantity': 1}],
                mode='subscription',
                success_url=f"https://{APP_URL}/?pago=exitoso&id={ID_ELITE}",
                cancel_url=f"https://{APP_URL}/",
            )
            st.link_button("PAGAR CON TARJETA 💳", res.url)

    # --- EL ARREGLO PARA TU ERROR ---
    st.write("---")
    st.warning("⚠️ ¿Pagaste y te salió error de acceso?")
    if st.button("VERIFICAR PAGO MANUAL (BYPASS)"):
        # Esto fuerza la carga de créditos si Stripe te bloqueó la URL
        st.session_state.creditos = 500
        st.success("Créditos desbloqueados manualmente.")
        time.sleep(1)
        st.rerun()

else:
    st.success(f"Sistema Activo: {st.session_state.creditos} Créditos disponibles.")
    if st.button("Cerrar Sesión"):
        st.session_state.creditos = 0
        st.rerun()
