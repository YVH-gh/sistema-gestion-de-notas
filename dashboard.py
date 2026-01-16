import streamlit as st
import pandas as pd
from datetime import date, timedelta
from db_connection import supabase

def show():
    st.title("Tablero de Control y Alertas")

    # Traer datos
    response = supabase.table("notas").select("*").execute()
    df = pd.DataFrame(response.data)

    if df.empty:
        st.info("No hay notas cargadas aún.")
        return

    # Convertir fechas a objetos datetime
    df['fecha_ultima_verificacion'] = pd.to_datetime(df['fecha_ultima_verificacion']).dt.date
    df['fecha_presentacion'] = pd.to_datetime(df['fecha_presentacion']).dt.date
    today = date.today()

    # --- MÉTRICAS SUPERIORES ---
    col1, col2, col3 = st.columns(3)
    col1.metric("En Seguimiento", len(df[df['estado'] == 'En Seguimiento']))
    col2.metric("Resueltas este mes", len(df[df['estado'] == 'Resuelta']))
    
    # --- LOGICA DE ALERTAS (El requerimiento crítico) ---
    st.divider()
    st.subheader("⚠️ Alertas de Acción Inmediata")

    # Alerta 1: REVISIÓN DE ESTADO (La regla de los 2 días)
    # Lógica: Si estado es 'En Seguimiento' Y pasaron más de 2 días desde la última verificación.
    alert_check = df[
        (df['estado'] == 'En Seguimiento') & 
        (df['fecha_ultima_verificacion'] < (today - timedelta(days=2)))
    ]

    if not alert_check.empty:
        st.error(f"🚨 Tienes {len(alert_check)} expedientes sin verificar hace más de 2 días.")
        st.write("Debes llamar o ir a mesa de entrada para consultar si ya lo vieron:")
        st.dataframe(alert_check[['numero_expediente', 'organismo_id', 'fecha_ultima_verificacion', 'asunto']])
    else:
        st.success("✅ Todo verificado recientemente.")

    # Alerta 2: PRONTO DESPACHO (La regla de los 10 días)
    # Lógica: Si pasaron 10 días desde la presentación y aún no está resuelta.
    pronto_despacho = df[
        (df['estado'] != 'Resuelta') & 
        (df['estado'] != 'Archivada') &
        (df['fecha_presentacion'] < (today - timedelta(days=10)))
    ]

    if not pronto_despacho.empty:
        st.warning(f"⏳ Hay {len(pronto_despacho)} notas que superaron los 10 días. Considerar Pronto Despacho.")
        st.dataframe(pronto_despacho[['numero_expediente', 'fecha_presentacion', 'tipo_tramite']])

st.title("🚦 Semáforo de Proyectos")
    
    # Supongamos que seleccionamos un proyecto activo
    proyecto_id = "uuid-del-proyecto-ejemplo" 
    
    # 1. Traer lo que el proyecto NECESITA (La plantilla)
    # 2. Traer lo que el proyecto YA TIENE (Las notas cargadas)
    # (Omito consultas SQL complejas por brevedad, pero la lógica es cruzar tablas)
    
    # Ejemplo de datos procesados:
    progreso = [
        {"Requisito": "Nota Inicio", "Dia_Limite": "2024-01-10", "Estado": "✅ Completado"},
        {"Requisito": "Pedido Presupuesto", "Dia_Limite": "2024-01-15", "Estado": "✅ Completado"},
        {"Requisito": "Autorización Legal", "Dia_Limite": "2024-01-20", "Estado": "❌ PENDIENTE"}, # HOY es 25, esto es ALERTA
    ]
    
    df_progreso = pd.DataFrame(progreso)
    
    st.subheader("Estado del Proyecto: Capacitación 2026")
    
    # Alerta visual
    pendientes_vencidos = df_progreso[df_progreso['Estado'] == "❌ PENDIENTE"]
    
    if not pendientes_vencidos.empty:
        st.error("🚨 ALERTA DE GESTIÓN: Faltan presentar notas críticas")
        for index, row in pendientes_vencidos.iterrows():
            st.write(f"⚠️ **{row['Requisito']}**: Debió presentarse antes del {row['Dia_Limite']}. ¡Estamos atrasados!")
    
    st.table(df_progreso)
