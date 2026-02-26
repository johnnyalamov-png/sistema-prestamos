import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from fpdf import FPDF

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Sistema Contable", layout="wide", page_icon="💰")
DB_FILE = "prestamos.xlsx"

# --- FUNCIONES DE DATOS ---
def cargar_datos(sheet_name="Prestamos"):
    if os.path.exists(DB_FILE):
        try:
            with pd.ExcelFile(DB_FILE) as xls:
                if sheet_name in xls.sheet_names:
                    return pd.read_excel(xls, sheet_name=sheet_name)
        except: pass
    if sheet_name == "Prestamos":
        return pd.DataFrame(columns=["ID", "Fecha", "Cliente", "Telefono", "Monto", "Interés %", "Cuotas", "Frecuencia", "Monto Cuota", "Total", "Estado", "Mora x Día"])
    return pd.DataFrame(columns=["ID_Abono", "ID_Prestamo", "Fecha_Abono", "Cliente", "Cuota_Nro", "Monto_Abonado", "Mora_Cobrada", "Saldo_Restante"])

def guardar_todo(df_p, df_a):
    with pd.ExcelWriter(DB_FILE, engine="openpyxl") as writer:
        df_p.to_excel(writer, sheet_name="Prestamos", index=False)
        df_a.to_excel(writer, sheet_name="Abonos", index=False)

def obtener_fechas_cronograma(fecha_inicio, num_cuotas, frecuencia):
    fechas = []
    try: fecha_dt = datetime.strptime(str(fecha_inicio), "%Y-%m-%d")
    except: fecha_dt = datetime.now()
    for i in range(1, int(num_cuotas) + 1):
        if frecuencia == "Semanal": fecha_dt += timedelta(weeks=1)
        elif frecuencia == "Quincenal": fecha_dt += timedelta(days=15)
        elif frecuencia == "Mensual": fecha_dt += timedelta(days=30)
        elif frecuencia == "Diaria": fecha_dt += timedelta(days=1)
        fechas.append(fecha_dt)
    return fechas

def limpiar_buscador():
    if "campo_buscador" in st.session_state:
        st.session_state["campo_buscador"] = ""

# --- FUNCIONES DE PDF (RESTABLECIDAS CON TU DISEÑO PROFESIONAL) ---
def gen_pdf_contrato(d):
    pdf = FPDF()
    pdf.add_page()
    try: pdf.image('logo.png', 10, 8, 33) 
    except: pass
    pdf.set_font("Helvetica", 'B', 20)
    pdf.cell(0, 15, "CONTRATO DE MUTUO DE DINERO", ln=True, align='C')
    pdf.set_font("Helvetica", 'I', 10)
    pdf.cell(0, 5, f"Documento N° {d['ID']} - Fecha: {d['Fecha']}", ln=True, align='C')
    pdf.ln(15)
    pdf.set_font("Helvetica", 'B', 12); pdf.cell(0, 10, "1. PARTES", ln=True)
    pdf.set_font("Helvetica", '', 11)
    pdf.multi_cell(0, 7, f"El presente documento certifica que el prestamista entrega la suma de S/ {d['Monto']:,.2f} al prestatario(a) {d['Cliente'].upper()}, quien se compromete a devolver el monto total de S/ {d['Total']:,.2f} (incluyendo intereses del {d['Interés %']}%) en un plazo de {d['Cuotas']} cuotas.")
    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 12); pdf.cell(0, 10, "2. COMPROMISO DE PAGO Y MORA", ln=True)
    pdf.set_font("Helvetica", '', 11)
    pdf.multi_cell(0, 7, f"Las cuotas serán pagadas con una frecuencia {d['Frecuencia']}. En caso de incumplimiento en la fecha establecida, se aplicará una mora automática de S/ {d['Mora x Día']:,.2f} por cada día de retraso.")
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', 12); pdf.set_fill_color(200, 200, 200)
    pdf.cell(0, 10, "3. CRONOGRAMA DE PAGOS", ln=True)
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(30, 8, "Cuota N°", 1, 0, 'C', True); pdf.cell(80, 8, "Fecha de Vencimiento", 1, 0, 'C', True); pdf.cell(80, 8, "Monto de Cuota", 1, 1, 'C', True)
    pdf.set_font("Helvetica", '', 10)
    fechas = obtener_fechas_cronograma(d['Fecha'], d['Cuotas'], d['Frecuencia'])
    for i, f in enumerate(fechas):
        pdf.cell(30, 8, f"{i+1}", 1, 0, 'C'); pdf.cell(80, 8, f.strftime('%d / %m / %Y'), 1, 0, 'C'); pdf.cell(80, 8, f"S/ {d['Monto Cuota']:,.2f}", 1, 1, 'C')
    pdf.ln(20); y_f = pdf.get_y(); pdf.line(20, y_f + 15, 90, y_f + 15); pdf.line(120, y_f + 15, 190, y_f + 15)
    pdf.set_y(y_f + 17); pdf.cell(85, 10, "FIRMA PRESTAMISTA", 0, 0, 'C'); pdf.cell(30, 10, "", 0, 0, 'C'); pdf.cell(85, 10, "FIRMA CLIENTE", 0, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')

def gen_pdf_estado_cuenta(d, df_abonos):
    pdf = FPDF()
    pdf.add_page()
    try: pdf.image('logo.png', 10, 8, 33) 
    except: pass
    pdf.set_font("Helvetica", 'B', 20); pdf.cell(0, 15, "ESTADO DE CUENTA", ln=True, align='C')
    pdf.set_font("Helvetica", 'B', 12); pdf.cell(0, 7, f"CLIENTE: {str(d['Cliente']).upper()}", ln=True, align='C'); pdf.ln(15)
    abonos_c = df_abonos[df_abonos['ID_Prestamo'] == d['ID']]
    total_pagado = abonos_c['Monto_Abonado'].sum()
    saldo_actual = max(0, d['Total'] - (len(abonos_c) * d['Monto Cuota']))
    pdf.set_fill_color(240, 240, 240); pdf.set_font("Helvetica", 'B', 11); pdf.cell(0, 10, " RESUMEN DEL PRÉSTAMO", 1, ln=True, fill=True)
    pdf.set_font("Helvetica", '', 10); pdf.cell(95, 8, f" Monto Prestado: S/ {d['Monto']:,.2f}", 1, 0); pdf.cell(95, 8, f" Total con Intereses: S/ {d['Total']:,.2f}", 1, 1)
    pdf.set_font("Helvetica", 'B', 10); pdf.cell(95, 8, f" Total Pagado: S/ {total_pagado:,.2f}", 1, 0); pdf.set_text_color(200, 0, 0); pdf.cell(95, 8, f" SALDO PENDIENTE: S/ {saldo_actual:,.2f}", 1, 1)
    pdf.set_text_color(0, 0, 0); pdf.ln(10); pdf.set_font("Helvetica", 'B', 9); pdf.set_fill_color(200, 200, 200)
    pdf.cell(25, 8, "Fecha", 1, 0, 'C', True); pdf.cell(25, 8, "Cuota", 1, 0, 'C', True); pdf.cell(45, 8, "Abono (Inc. Mora)", 1, 0, 'C', True); pdf.cell(45, 8, "Mora Cobrada", 1, 0, 'C', True); pdf.cell(50, 8, "Saldo Restante", 1, 1, 'C', True)
    pdf.set_font("Helvetica", '', 9)
    for _, ab in abonos_c.iterrows():
        pdf.cell(25, 8, str(ab['Fecha_Abono']), 1, 0, 'C'); pdf.cell(25, 8, str(ab['Cuota_Nro']), 1, 0, 'C'); pdf.cell(45, 8, f"S/ {ab['Monto_Abonado']:,.2f}", 1, 0, 'C'); pdf.cell(45, 8, f"S/ {ab['Mora_Cobrada']:,.2f}", 1, 0, 'C'); pdf.cell(50, 8, f"S/ {ab['Saldo_Restante']:,.2f}", 1, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')

# --- CARGA DE DATOS ---
df_p = cargar_datos("Prestamos")
df_a = cargar_datos("Abonos")

# --- NAVEGACIÓN ---
if 'pagina' not in st.session_state: st.session_state['pagina'] = "📊 Dashboard"
st.sidebar.title("MENÚ")
for p in ["📊 Dashboard", "💸 Registrar Abono", "📄 Documentos", "📈 Reportes", "🔔 Solicitudes"]:
    if st.sidebar.button(p, use_container_width=True): st.session_state['pagina'] = p

pg = st.session_state['pagina']

# --- DASHBOARD (RESTAURADO AL 100%) ---
if pg == "📊 Dashboard":
    st.title("📊 Control de Préstamos")
    with st.expander("➕ Registrar Nuevo Préstamo"):
        with st.form("nuevo_p"):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Nombre del Cliente")
            mon = c1.number_input("Monto Principal (S/)", min_value=0.0)
            cuo = c1.number_input("Cuotas", min_value=1)
            tel = c2.text_input("WhatsApp")
            int_p = c2.slider("Interés (%)", 0, 100, 20)
            frec = c2.selectbox("Frecuencia", ["Diaria", "Semanal", "Quincenal", "Mensual"])
            m_dia = c2.number_input("Mora x día (S/)", value=5.0)
            if st.form_submit_button("Registrar"):
                total = mon + (mon * (int_p/100))
                nueva = {"ID": len(df_p)+1, "Fecha": str(datetime.now().date()), "Cliente": nom, "Telefono": tel, "Monto": mon, "Interés %": int_p, "Cuotas": cuo, "Frecuencia": frec, "Monto Cuota": round(total/cuo, 2), "Total": total, "Estado": "Pendiente", "Mora x Día": m_dia}
                df_p = pd.concat([df_p, pd.DataFrame([nueva])], ignore_index=True); guardar_todo(df_p, df_a); st.rerun()

    if not df_p.empty:
        prox_l, estado_l, mora_calc, progreso_cuotas = [], [], [], []
        hoy = datetime.now()
        for _, r in df_p.iterrows():
            pagos_h = len(df_a[df_a['ID_Prestamo'] == r['ID']])
            progreso_cuotas.append(f"{pagos_h} / {r['Cuotas']}")
            fechas = obtener_fechas_cronograma(r['Fecha'], r['Cuotas'], r['Frecuencia'])
            if pagos_h >= r['Cuotas']:
                prox_l.append("----"); estado_l.append("CANCELADO"); mora_calc.append(0)
            else:
                f_vence = fechas[pagos_h]
                prox_l.append(f_vence.strftime('%d/%m/%Y')); estado_l.append("PENDIENTE")
                retraso = (hoy - f_vence).days
                mora_val = round(float(retraso * r['Mora x Día']), 2) if retraso > 0 else 0
                mora_calc.append(mora_val)
        
        df_p['CUOTAS'], df_p['PROX. PAGO'], df_p['MORA ACUM.'], df_p['ESTADO_V'] = progreso_cuotas, prox_l, mora_calc, estado_l
        cols = ["ID", "Fecha", "Cliente", "Telefono", "Monto", "Interés %", "CUOTAS", "Total", "Monto Cuota", "MORA ACUM.", "PROX. PAGO", "ESTADO_V"]
        st.dataframe(df_p[cols].style.applymap(lambda v: f"color: {'#00FF00' if v == 'CANCELADO' else '#FF0000'}; font-weight: bold;", subset=['ESTADO_V']).applymap(lambda v: f"color: {'orange' if v > 0 else 'white'};", subset=['MORA ACUM.']).format({"MORA ACUM.": lambda x: f"{x:,.2f}" if x > 0 else "0"}), use_container_width=True, hide_index=True)

# --- REGISTRAR ABONO (RESTAURADO AL 100%) ---
elif pg == "💸 Registrar Abono":
    st.title("💸 Registrar Pago con Mora")
    pend = df_p[df_p['Estado'] == "Pendiente"]
    if not pend.empty:
        busq = st.text_input("🔍 Buscador de Clientes", key="campo_buscador")
        if busq:
            res = pend[pend['Cliente'].str.contains(busq, case=False, na=False) | pend['ID'].astype(str).str.contains(busq, na=False)]
            if not res.empty:
                d = res.iloc[0]; pagos_h = len(df_a[df_a['ID_Prestamo'] == d['ID']]); porc = int((pagos_h / d['Cuotas']) * 100)
                col_bar = "red" if porc <= 33 else "orange" if porc <= 66 else "green"
                with st.container(border=True):
                    st.subheader(f"Cuota N° {pagos_h+1} de {d['Cuotas']}")
                    st.markdown(f'<div style="width:100%; background:#333; border-radius:10px;"><div style="width:{porc}%; background:{col_bar}; height:20px; border-radius:10px; text-align:center; color:white;">{porc}%</div></div>', unsafe_allow_html=True)
                    st.write(f"✅ **Cliente:** {d['Cliente']}")
                    c1, c2 = st.columns(2); m_c = c1.number_input("Cuota (S/)", value=float(d['Monto Cuota']), disabled=True)
                    f_v = obtener_fechas_cronograma(d['Fecha'], d['Cuotas'], d['Frecuencia'])[pagos_h]
                    m_s = round(float((datetime.now() - f_v).days * d['Mora x Día']), 2) if datetime.now() > f_v else 0.0
                    mora_in = c2.number_input("Mora (S/)", value=m_s)
                    st.markdown(f"## **TOTAL: S/ {m_c + mora_in:,.2f}**")
                    if st.button("💰 REGISTRAR", use_container_width=True, type="primary"):
                        nuevo = {"ID_Abono": len(df_a)+1, "ID_Prestamo": d['ID'], "Fecha_Abono": str(datetime.now().date()), "Cliente": d['Cliente'], "Cuota_Nro": f"{pagos_h+1}/{d['Cuotas']}", "Monto_Abonado": m_c + mora_in, "Mora_Cobrada": mora_in, "Saldo_Restante": max(0, d['Total'] - (pagos_h+1)*d['Monto Cuota'])}
                        df_a = pd.concat([df_a, pd.DataFrame([nuevo])], ignore_index=True)
                        if (pagos_h+1) >= d['Cuotas']: df_p.loc[df_p['ID'] == d['ID'], 'Estado'] = "Pagado"
                        guardar_todo(df_p, df_a); st.rerun()
                    st.button("❌ CANCELAR", on_click=limpiar_buscador, use_container_width=True)

# --- DOCUMENTOS (RESTAURADO AL 100%) ---
elif pg == "📄 Documentos":
    st.title("📄 Gestión de Documentos")
    if not df_p.empty:
        busq_d = st.text_input("🔍 Buscar Cliente")
        filtro = df_p[df_p['Cliente'].str.contains(busq_d, case=False, na=False) | df_p['ID'].astype(str).str.contains(busq_d, na=False)]
        if not filtro.empty and busq_d != "":
            d = filtro.iloc[0]; c1, c2 = st.columns(2)
            with c1.container(border=True):
                st.subheader("📜 Contrato")
                st.download_button("⬇️ Descargar", gen_pdf_contrato(d), f"Contrato_{d['ID']}.pdf", use_container_width=True)
                st.link_button("📲 Avisar WhatsApp", f"https://wa.me/51{d['Telefono']}?text=Hola%20{d['Cliente'].replace(' ', '%20')},%20su%20contrato%20esta%20listo.", use_container_width=True)
            with c2.container(border=True):
                st.subheader("📊 Estado")
                st.download_button("⬇️ Descargar", gen_pdf_estado_cuenta(d, df_a), f"Estado_{d['ID']}.pdf", use_container_width=True)
                sal = df_a[df_a['ID_Prestamo'] == d['ID']].iloc[-1]['Saldo_Restante'] if not df_a[df_a['ID_Prestamo'] == d['ID']].empty else d['Total']
                st.link_button("📲 Enviar Saldo", f"https://wa.me/51{d['Telefono']}?text=Hola%20{d['Cliente'].replace(' ', '%20')},%20su%20saldo%20actual%20es%20S/%20{sal:,.2f}.", use_container_width=True)

# --- REPORTES (RESTAURADO AL 100%) ---
elif pg == "📈 Reportes":
    st.title("📈 Análisis de Negocio")
    total_prestado = df_p['Monto'].sum(); total_recuperado = df_a['Monto_Abonado'].sum() - df_a['Mora_Cobrada'].sum()
    k1, k2, k3 = st.columns(3); k1.metric("CAPITAL EN LA CALLE", f"S/ {total_prestado - total_recuperado:,.2f}"); k2.metric("INTERESES PROYECTADOS", f"S/ {df_p['Total'].sum() - total_prestado:,.2f}"); k3.metric("MORA TOTAL RECAUDADA", f"S/ {df_a['Mora_Cobrada'].sum():,.2f}")
    st.divider(); c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("🎯 Estado de Cartera"); stats = df_p['Estado'].value_counts()
        st.write(f"✅ Pagados: {stats.get('Pagado', 0)} | ⏳ Pendientes: {stats.get('Pendiente', 0)}")
        st.progress(stats.get('Pagado', 0) / len(df_p) if len(df_p) > 0 else 0)
    with c2:
        st.subheader("💰 Últimos Ingresos"); st.table(df_a[['Fecha_Abono', 'Cliente', 'Cuota_Nro', 'Monto_Abonado']].tail(10))

# --- 🔔 NUEVA PESTAÑA: SOLICITUDES (AÑADIDA SIN TOCAR LO ANTERIOR) ---
elif pg == "🔔 Solicitudes":
    st.title("🔔 Solicitudes por Aprobar")
    try:
        df_s = pd.read_excel(DB_FILE, sheet_name="Solicitudes")
        pendientes = df_s[df_s['Estado'] == "Pendiente"]
    except: pendientes = pd.DataFrame()
    if not pendientes.empty:
        for i, row in pendientes.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"👤 **{row['Cliente']}** | DNI: {row['DNI']} | Monto: S/ {row['Monto']} | Cuotas: {row['Cuotas']}\n\n📝 Motivo: {row['Motivo']}")
                if c2.button("✅ Aprobar", key=f"ap_{i}", use_container_width=True, type="primary"):
                    total_p = row['Monto'] + (row['Monto'] * 0.20)
                    nuevo_p = {"ID": len(df_p)+1, "Fecha": str(datetime.now().date()), "Cliente": row['Cliente'], "Telefono": row['Telefono'], "Monto": row['Monto'], "Interés %": 20, "Cuotas": row['Cuotas'], "Frecuencia": "Semanal", "Monto Cuota": round(total_p/row['Cuotas'], 2), "Total": total_p, "Estado": "Pendiente", "Mora x Día": 5.0}
                    df_p = pd.concat([df_p, pd.DataFrame([nuevo_p])], ignore_index=True)
                    df_s.at[i, 'Estado'] = "Aprobado"
                    with pd.ExcelWriter(DB_FILE, engine="openpyxl") as writer:
                        df_p.to_excel(writer, sheet_name="Prestamos", index=False)
                        df_a.to_excel(writer, sheet_name="Abonos", index=False)
                        df_s.to_excel(writer, sheet_name="Solicitudes", index=False)
                    st.rerun()
                if c3.button("❌ Rechazar", key=f"re_{i}", use_container_width=True):
                    df_s.at[i, 'Estado'] = "Rechazado"
                    with pd.ExcelWriter(DB_FILE, engine="openpyxl") as writer:
                        df_p.to_excel(writer, sheet_name="Prestamos", index=False)
                        df_a.to_excel(writer, sheet_name="Abonos", index=False)
                        df_s.to_excel(writer, sheet_name="Solicitudes", index=False)
                    st.rerun()
    else: st.info("No hay solicitudes pendientes en este momento.")