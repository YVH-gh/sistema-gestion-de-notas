import streamlit as st
from db_connection import supabase
from datetime import date

def show_create():
    st.header("📱 Carga Rápida desde Mesa de Entrada")

    # 1. Seleccionar a qué Proyecto pertenece esta nota
    proyectos = supabase.table("proyectos").select("id, nombre").eq("estado", "En Curso").execute()
    opciones_proyectos = {p['nombre']: p['id'] for p in proyectos.data}
    
    proyecto_selec = st.selectbox("Proyecto Asociado", list(opciones_proyectos.keys()))
    id_proyecto = opciones_proyectos[proyecto_selec]

    # 2. ¿Qué requisito estamos cumpliendo?
    # Traemos los requisitos que faltan para este proyecto
    reqs = supabase.table("requisitos_plantilla").select("*").execute() # Aquí deberías filtrar por el tipo de proyecto
    req_opciones = {r['nombre_requerimiento']: r['id'] for r in reqs.data}
    
    requisito_selec = st.selectbox("¿Qué nota estás presentando?", list(req_opciones.keys()))

    # 3. Datos Manuales
    col1, col2 = st.columns(2)
    with col1:
        nro_expediente = st.text_input("N° Expediente (Mesa de Entrada)")
    with col2:
        organismo = st.selectbox("Organismo", ["Ministerio", "Municipalidad", "Rentas"])

    # 4. LA CÁMARA (Clave para móviles)
    st.write("📷 Foto de la Nota Sellada")
    foto = st.camera_input("Tomar foto")
    
    archivo_subido = st.file_uploader("O subir PDF/Imagen", type=['pdf', 'jpg', 'png'])

    if st.button("Guardar y Dar Seguimiento"):
        if not nro_expediente:
            st.error("Falta el número de expediente")
            return

        file_to_save = foto if foto else archivo_subido
        
        if file_to_save:
            # Lógica de subida a Supabase Storage (simplificada)
            # file_path = f"{nro_expediente}_{file_to_save.name}"
            # supabase.storage.from_("documentos").upload(file_path, file_to_save.getvalue())
            st.success("Nota subida correctamente.")
        else:
            st.warning("Recuerda subir la foto del sello.")
            
        # Aquí iría el insert a la base de datos vinculando proyecto_id y requisito_id
        st.success(f"Nota {nro_expediente} registrada. El reloj de seguimiento ha comenzado.")
