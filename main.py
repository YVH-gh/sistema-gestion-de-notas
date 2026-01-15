import streamlit as st
from modules import dashboard, gestion_notas, ia_tools

st.set_page_config(page_title="Gestión de Expedientes", layout="wide")

# Sidebar de navegación
st.sidebar.title("🗂️ Sistema de Notas")
menu = st.sidebar.radio("Ir a:", ["Dashboard & Alertas", "Cargar Nueva Nota", "Buscador de Expedientes", "Asistente IA (Redacción)"])

if menu == "Dashboard & Alertas":
    dashboard.show()
elif menu == "Cargar Nueva Nota":
    gestion_notas.show_create()
elif menu == "Buscador de Expedientes":
    gestion_notas.show_list()
elif menu == "Asistente IA (Redacción)":
    ia_tools.show_drafter()
