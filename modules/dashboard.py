import streamlit as st
import pandas as pd
from datetime import date, timedelta
from db_connection import supabase

def show():
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
    
    st.subheader("Estado del Proyecto: Capacitación 2025")
    
    # Alerta visual
    pendientes_vencidos = df_progreso[df_progreso['Estado'] == "❌ PENDIENTE"]
    
    if not pendientes_vencidos.empty:
        st.error("🚨 ALERTA DE GESTIÓN: Faltan presentar notas críticas")
        for index, row in pendientes_vencidos.iterrows():
            st.write(f"⚠️ **{row['Requisito']}**: Debió presentarse antes del {row['Dia_Limite']}. ¡Estamos atrasados!")
    
    st.table(df_progreso)
