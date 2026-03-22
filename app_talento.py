import streamlit as st
import pandas as pd
from openai import OpenAI
import fitz 
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import stripe

# --- CONFIGURACIÓN DE APIS ---
# Asegúrate de tener estas llaves en los "Secrets" de Streamlit
stripe.api_key = st.secrets["STRIPE_API_KEY"]
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- IDs DE PRECIOS QUE PASASTE ---
ID_BUSINESS = "price_1TDs0FDumVuheYnZt2zgHmcW" # El de $3,500
ID_STARTER = "price_1TDryXDumVuheYnZysomqD7R"

# --- INICIALIZAR ESTADO DE CRÉDITOS ---
if "creditos" not in st.session_state:
    st.session_state.creditos = 0

# --- FUNCIÓN PARA COBRAR ---
def crear_pago(price_id):
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{'price': price_id, 'quantity': 1}],
        mode='payment', # Cambia a 'subscription' si en Stripe lo pusiste como recurrente
        success_url='https://tu-app.streamlit.app/?pago=exitoso',
        cancel_url='https://tu-app.streamlit.app/?pago=cancelado',
    )
    return session.url

# --- VERIFICACIÓN AUTOMÁTICA DE PAGO ---
if st.query_params.get("pago") == "exitoso":
    # Aquí sumamos los créditos según lo que compraron (puedes ajustar la lógica)
    st.session_state.creditos += 500 
    st.success("💎 CRÉDITOS ZYNTH ACTIVADOS: +500")
    st.query_params.clear()

# --- LÓGICA DE PROCESAMIENTO (LA QUE TENÍA ERROR) ---
def procesar_cv_ia(file, perfil):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        texto = " ".join([p.get_text() for p in doc])[:8000]
        
        prompt = f"Analiza este CV para la vacante: {perfil}. Responde: Nombre | Teléfono | Correo | Puntaje | Veredicto | Motivo. CV: {texto}"
        
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        # Aquí es donde se limpia y estructura la respuesta
        r = res.choices[0].message.content.split(" | ")
        return {
            "NOMBRE": r[0], "TELÉFONO": r[1], "CORREO": r[2],
            "PUNTAJE": r[3], "VEREDICTO": r[4], "MOTIVO": r[5]
        }
    except:
        return None

# --- INTERFAZ DE USUARIO ---
st.title("💎 ZYNTH ENTERPRISE")
st.sidebar.metric("Saldo actual", f"{st.session_state.creditos} CVs")

if st.session_state.creditos <= 0:
    st.warning("⚠️ No tienes créditos. Selecciona un plan para continuar:")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Comprar Starter ($)"):
            st.markdown(f"[Pagar aquí]({crear_pago(ID_STARTER)})")
    with c2:
        if st.button("Comprar Business ($$$)"):
            st.markdown(f"[Pagar aquí]({crear_pago(ID_BUSINESS)})")
    st.stop()

# --- ÁREA DE CARGA ---
perfil = st.text_area("Describe qué buscas (ej: Parrillero Cumbres o Vendedora Boutique):")
archivos = st.file_uploader("Sube los PDFs", accept_multiple_files=True)

if st.button("🚀 INICIAR ESCANEO"):
    if archivos and perfil:
        if len(archivos) <= st.session_state.creditos:
            resultados = []
            barra = st.progress(0)
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futuros = [executor.submit(procesar_cv_ia, f, perfil) for f in archivos]
                for i, f in enumerate(futuros):
                    # ESTA ES LA LÍNEA 131 ARREGLADA:
                    analisis = f.result() 
                    if analisis:
                        resultados.append(analisis)
                        st.session_state.creditos -= 1
                    barra.progress((i + 1) / len(archivos))
            
            df = pd.DataFrame(resultados)
            st.dataframe(df)
        else:
            st.error("No tienes suficientes créditos para esta cantidad de archivos.")
