import streamlit as st
from db_connection import supabase
from datetime import datetime

def show_create():
    st.title("📱 Carga de Nueva Nota")
    
    # 1. BUSCAR PROYECTOS ACTIVOS
    try:
        proyectos = supabase.table("proyectos").select("id, nombre").eq("estado", "En Curso").execute()
        opciones_proyectos = {p['nombre']: p['id'] for p in proyectos.data}
    except Exception as e:
        st.error(f"Error conectando a BD: {e}")
        return

    if not opciones_proyectos:
        st.warning("No hay proyectos activos. Pide al admin que cree uno.")
        return

    col_proj, col_req = st.columns(2)
    with col_proj:
        proyecto_selec = st.selectbox("Proyecto", list(opciones_proyectos.keys()))
        id_proyecto = opciones_proyectos[proyecto_selec]

    # 2. BUSCAR REQUISITOS (Tipos de nota para ese proyecto)
    # Traemos todos los requisitos disponibles para probar
    reqs = supabase.table("requisitos_plantilla").select("*").execute()
    opciones_req = {r['nombre_requerimiento']: r['id'] for r in reqs.data}
    
    with col_req:
        lista_reqs = ["Otro / Genérico"] + list(opciones_req.keys())
        tipo_nota_selec = st.selectbox("Tipo de Nota", lista_reqs)
        
        id_requisito = None
        if tipo_nota_selec != "Otro / Genérico":
            id_requisito = opciones_req[tipo_nota_selec]

    # 3. DATOS DE LA NOTA FÍSICA
    with st.form("formulario_nota", clear_on_submit=True):
        st.write("---")
        c1, c2 = st.columns(2)
        nro_expediente = c1.text_input("N° Expediente / ID Nota")
        organismo = c2.selectbox("Organismo Destino", ["Ministerio de Educación", "Municipalidad", "Rentas", "Privado"])
        
        asunto = st.text_input("Asunto / Detalle")
        prioridad = st.select_slider("Prioridad", options=["Baja", "Media", "Alta"], value="Media")
        
        st.write("📷 **Evidencia (Foto del sello)**")
        foto = st.camera_input("Tomar foto ahora")
        archivo_extra = st.file_uploader("O subir PDF", type=['pdf', 'jpg', 'png'])
        
        guardar = st.form_submit_button("💾 REGISTRAR SEGUIMIENTO")
        
        if guardar:
            if not nro_expediente or not asunto:
                st.error("⚠️ Faltan datos obligatorios (Expediente o Asunto).")
            else:
                # A. SUBIR ARCHIVO A BUCKET "REGISTROS"
                url_archivo = None
                archivo_final = foto if foto else archivo_extra
                
                if archivo_final:
                    try:
                        # Nombre único: fecha_expediente_nombre
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        nombre_archivo = f"{timestamp}_{nro_expediente}_{archivo_final.name}"
                        
                        # AQUÍ ESTÁ EL CAMBIO: Usamos "registros"
                        supabase.storage.from_("registros").upload(
                            path=nombre_archivo,
                            file=archivo_final.getvalue(),
                            file_options={"content-type": archivo_final.type}
                        )
                        # Obtener URL Pública
                        url_archivo = supabase.storage.from_("registros").get_public_url(nombre_archivo)
                    except Exception as e:
                        st.warning(f"No se pudo subir la imagen (¿Creaste el bucket 'registros'?), pero guardaremos los datos. Error: {e}")

                # B. GUARDAR EN BASE DE DATOS
                datos_nota = {
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
                
                try:
                    supabase.table("notas").insert(datos_nota).execute()
                    st.success(f"✅ ¡Éxito! La nota {nro_expediente} guardada en 'registros'.")
                except Exception as e:
                    st.error(f"Error al guardar en base de datos: {e}")
