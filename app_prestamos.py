import streamlit as st
import pandas as pd

# Configuración de la hoja de Google
SHEET_ID = "1j7LzXg5Sj1aFBx5YNJEdjrudltBStYLC0am4oX3_tdI"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Solicitudes"

st.set_page_config(page_title="Sistema de Préstamos - Admin", layout="wide")

st.title("💰 Panel de Administración")

# Función para leer datos de Google Sheets
def cargar_solicitudes():
    try:
        df = pd.read_csv(SHEET_URL)
        return df
    except:
        return pd.DataFrame(columns=['Nombre', 'DNI', 'WhatsApp', 'Monto', 'Cuotas', 'Motivo', 'Estado'])

menu = st.sidebar.selectbox("Menú", ["Dashboard", "🔔 Solicitudes", "Clientes", "Caja"])

if menu == "🔔 Solicitudes":
    st.header("🔔 Solicitudes por Aprobar")
    df_sol = cargar_solicitudes()
    
    if not df_sol.empty:
        st.dataframe(df_sol)
        
        nombre_sel = st.selectbox("Seleccione cliente para aprobar", df_sol['Nombre'].tolist())
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Aprobar Préstamo"):
                st.success(f"Préstamo de {nombre_sel} aprobado!")
        with col2:
            if st.button("❌ Rechazar"):
                st.warning("Solicitud rechazada.")
    else:
        st.info("No hay solicitudes pendientes en este momento.")

# ... (Resto de las secciones de tu Dashboard actual)
