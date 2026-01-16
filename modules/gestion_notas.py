import streamlit as st
from db_connection import supabase
from datetime import datetime
import pandas as pd

# --- PANTALLA 1: CARGA (Esta ya funciona) ---
def show_create():
    st.title("📱 Carga de Nueva Nota")
    
    # 1. BUSCAR PROYECTOS
    try:
        proyectos = supabase.table("proyectos").select("id, nombre").eq("estado", "En Curso").execute()
        opciones_proyectos = {p['nombre']: p['id'] for p in proyectos.data}
    except Exception as e:
        st.error(f"Error conectando a BD: {e}")
        return

    if not opciones_proyectos:
        st.warning("No hay proyectos activos.")
        return

    col_proj, col_req = st.columns(2)
    with col_proj:
        proyecto_selec = st.selectbox("Proyecto", list(opciones_proyectos.keys()))
        id_proyecto = opciones_proyectos[proyecto_selec]

    # 2. BUSCAR REQUISITOS
    reqs = supabase.table("requisitos_plantilla").select("*").execute()
    opciones_req = {r['nombre_requerimiento']: r['id'] for r in reqs.data}
    
    with col_req:
        lista_reqs = ["Otro / Genérico"] + list(opciones_req.keys())
        tipo_nota_selec = st.selectbox("Tipo de Nota", lista_reqs)
        id_requisito = None
        if tipo_nota_selec != "Otro / Genérico":
            id_requisito = opciones_req[tipo_nota_selec]

    # 3. FORMULARIO
    with st.form("formulario_nota", clear_on_submit=True):
        st.write("---")
        c1, c2 = st.columns(2)
        nro_expediente = c1.text_input("N° Expediente")
        organismo = c2.selectbox("Destino", ["Ministerio de Educación", "Municipalidad", "Rentas", "Privado"])
        asunto = st.text_input("Asunto")
        prioridad = st.select_slider("Prioridad", ["Baja", "Media", "Alta"], value="Media")
        
        st.write("📷 **Foto del Sello**")
        foto = st.camera_input("Tomar foto")
        archivo_extra = st.file_uploader("O subir archivo", type=['pdf', 'jpg', 'png'])
        
        if st.form_submit_button("💾 GUARDAR"):
            if not nro_expediente or not asunto:
                st.error("Faltan datos.")
            else:
                # Subida de archivo
                url_archivo = None
                archivo_final = foto if foto else archivo_extra
                
                if archivo_final:
                    try:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        nombre_archivo = f"{timestamp}_{nro_expediente}_{archivo_final.name}"
                        supabase.storage.from_("registros").upload(nombre_archivo, archivo_final.getvalue(), {"content-type": archivo_final.type})
                        url_archivo = supabase.storage.from_("registros").get_public_url(nombre_archivo)
                    except Exception as e:
                        st.warning(f"Error subiendo imagen: {e}")

                # Insertar en BD
                datos = {
                    "numero_expediente": nro_expediente,
                    "organismo_id": 1, 
                    "asunto": asunto,
                    "tipo_tramite": tipo_nota_selec,
                    "prioridad": prioridad,
                    "estado": "Presentada",
                    "fecha_presentacion": datetime.now().strftime("%Y-%m-%d"),
                    "proyecto_id": id_proyecto,
                    "requisito_id": id_requisito,
                    "archivo_url": url_archivo
                }
                supabase.table("notas").insert(datos).execute()
                st.success("✅ Nota guardada correctamente.")

# --- PANTALLA 2: LISTADO (Esta es la nueva) ---
def show_list():
    st.title("📂 Buscador de Expedientes")
    
    # Traer todas las notas ordenadas por fecha (las más nuevas primero)
    response = supabase.table("notas").select("*").order("created_at", desc=True).execute()
    data = response.data
    
    if not data:
        st.info("No hay notas cargadas todavía.")
        return

    # Convertir a DataFrame para mostrarlo lindo
    df = pd.DataFrame(data)
    
    # Seleccionar solo columnas útiles para la tabla
    columnas_visibles = ["numero_expediente", "asunto", "estado", "prioridad", "fecha_presentacion", "archivo_url"]
    
    # Configurar la tabla para que el link sea clicable
    st.data_editor(
        df[columnas_visibles],
        column_config={
            "archivo_url": st.column_config.LinkColumn("Evidencia", display_text="Ver Foto"),
            "fecha_presentacion": st.column_config.DateColumn("Fecha"),
            "prioridad": st.column_config.TextColumn("Prioridad"),
        },
        hide_index=True,
        use_container_width=True
    )

    # Vista detallada (Tarjetas)
    st.divider()
    st.subheader("🔍 Vista Detallada")
    for nota in data:
        with st.expander(f"{nota['numero_expediente']} - {nota['asunto']}"):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"**Estado:** {nota['estado']}")
                st.write(f"**Trámite:** {nota['tipo_tramite']}")
                st.write(f"**Fecha:** {nota['fecha_presentacion']}")
            with c2:
                if nota['archivo_url']:
                    st.image(nota['archivo_url'], width=150, caption="Sello")
                else:
                    st.write("Sin foto")
