import streamlit as st
import pandas as pd
import os

DB_FILE = "prestamos.xlsx"

st.set_page_config(page_title="Solicitud de Crédito", page_icon="📝")

st.title("📝 Solicitud de Préstamo")
st.write("Complete sus datos para evaluar su solicitud.")

with st.form("form_solicitud"):
    nom = st.text_input("Nombre Completo")
    dni = st.text_input("DNI / CE")
    tel = st.text_input("Número de WhatsApp")
    mon = st.number_input("Monto que solicita (S/)", min_value=0.0)
    cuo = st.number_input("Número de cuotas", min_value=1)
    motivo = st.text_area("¿Para qué necesita el préstamo?")
    
    if st.form_submit_button("Enviar Solicitud"):
        nueva_sol = {
            "Fecha": str(pd.Timestamp.now().date()),
            "Cliente": nom,
            "DNI": dni,
            "Telefono": tel,
            "Monto": mon,
            "Cuotas": cuo,
            "Motivo": motivo,
            "Estado": "Pendiente"
        }
        
        # Guardar en una nueva hoja llamada 'Solicitudes'
        with pd.ExcelWriter(DB_FILE, engine="openpyxl", mode="a", if_sheet_exists="overlay") as writer:
            try:
                df_s = pd.read_excel(DB_FILE, sheet_name="Solicitudes")
                df_s = pd.concat([df_s, pd.DataFrame([nueva_sol])], ignore_index=True)
            except:
                df_s = pd.DataFrame([nueva_sol])
            df_s.to_excel(writer, sheet_name="Solicitudes", index=False)
            
        st.success("✅ Solicitud enviada con éxito. Nos comunicaremos con usted pronto.")