import streamlit as st
from db_connection import supabase
from datetime import datetime, timedelta
import pandas as pd

# --- PANTALLA 1: CARGA ---
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

    # [NUEVO] BUSCAR ORGANISMOS (DESTINOS) EN LA BASE DE DATOS
    try:
        orgs = supabase.table("organismos").select("id, nombre").execute()
        opciones_orgs = {o['nombre']: o['id'] for o in orgs.data}
    except Exception as e:
        st.error("Error cargando organismos. Usando lista por defecto.")
        opciones_orgs = {"Ministerio de Educación": 1} # Fallback

    # 3. FORMULARIO
    with st.form("formulario_nota", clear_on_submit=True):
        st.write("---")
        c1, c2 = st.columns(2)
        nro_expediente = c1.text_input("N° Expediente")
        nombre_organismo = c2.selectbox("Destino", list(opciones_orgs.keys()))
        id_organismo = opciones_orgs[nombre_organismo] # Guardamos el ID real
                
        asunto = st.text_input("Asunto")
        
        # NUEVO: Fecha de Recordatorio
        fecha_default = datetime.now().date() + timedelta(days=5)
        fecha_recordatorio = st.date_input("¿Cuándo consultar estado?", value=fecha_default)
        
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
                        # Usamos "registros" como definimos antes
                        supabase.storage.from_("registros").upload(nombre_archivo, archivo_final.getvalue(), {"content-type": archivo_final.type})
                        url_archivo = supabase.storage.from_("registros").get_public_url(nombre_archivo)
                    except Exception as e:
                        st.warning(f"Error subiendo imagen: {e}")

                # Insertar en BD
                datos = {
                    "numero_expediente": nro_expediente,
                    "organismo_id": id_organismo, 
                    "asunto": asunto,
                    "tipo_tramite": tipo_nota_selec,
                    # "prioridad": prioridad,  <-- ELIMINADO
                    "fecha_recordatorio": str(fecha_recordatorio), # <-- NUEVO
                    "estado": "Presentada",
                    "fecha_presentacion": datetime.now().strftime("%Y-%m-%d"),
                    "proyecto_id": id_proyecto,
                    "requisito_id": id_requisito,
                    "archivo_url": url_archivo
                }
                
                try:
                    supabase.table("notas").insert(datos).execute()
                    st.success(f"✅ Nota guardada. Te recordaremos consultar el {fecha_recordatorio}.")
                except Exception as e:
                     st.error(f"Error guardando: {e}")

# --- PANTALLA 2: LISTADO ACTUALIZADA ---
def show_list():
    st.title("📂 Buscador de Expedientes")
    
    # Traemos las notas
    response = supabase.table("notas").select("*").order("created_at", desc=True).execute()
    data = response.data
    
    if not data:
        st.info("No hay notas cargadas todavía.")
        return

    df = pd.DataFrame(data)
    
    # --- CORRECCIÓN DEL ERROR ---
    # Convertimos explícitamente las columnas de texto a objetos "Fecha" reales.
    # 'errors="coerce"' significa: "si hay un error o está vacío, ponlo como NaT (Not a Time) y no rompas la app".
    
    if "fecha_presentacion" in df.columns:
        df["fecha_presentacion"] = pd.to_datetime(df["fecha_presentacion"], errors="coerce").dt.date
        
    if "fecha_recordatorio" in df.columns:
        df["fecha_recordatorio"] = pd.to_datetime(df["fecha_recordatorio"], errors="coerce").dt.date

    # Definimos qué columnas mostrar
    cols = ["numero_expediente", "asunto", "estado", "fecha_presentacion", "fecha_recordatorio", "archivo_url"]
    cols_final = [c for c in cols if c in df.columns]

    st.data_editor(
        df[cols_final],
        column_config={
            "archivo_url": st.column_config.LinkColumn("Evidencia", display_text="Ver Foto"),
            "fecha_presentacion": st.column_config.DateColumn("Presentada", format="DD/MM/YYYY"),
            "fecha_recordatorio": st.column_config.DateColumn("Consultar el...", format="DD/MM/YYYY"),
        },
        hide_index=True,
        use_container_width=True
    )

    st.divider()
    st.subheader("🔍 Vista Detallada")
    for nota in data:
        with st.expander(f"{nota.get('numero_expediente', 'S/N')} - {nota.get('asunto', 'Sin Asunto')}"):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"**Estado:** {nota.get('estado', '-')}")
                
                # Mostramos fecha solo si existe
                fecha_rec = nota.get('fecha_recordatorio')
                if fecha_rec:
                    st.info(f"📅 **Consultar el:** {fecha_rec}")
                else:
                    st.warning("Sin fecha de recordatorio establecida")
                    
            with c2:
                if nota.get('archivo_url'):
                    st.image(nota['archivo_url'], width=150)
                else:
                    st.write("Sin foto")
