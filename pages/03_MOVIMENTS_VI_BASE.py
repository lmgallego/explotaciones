import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

from core.moviments_vi_base import procesar_moviments_vi_base

st.title("MOVIMENTS VI BASE")

# Crear pestañas
tab1, tab2, tab3 = st.tabs(["📂 Procesamiento", "📊 Tabla Resultados", "📈 Gráficos"])

with tab1:
    st.subheader("Procesamiento de Moviments Vi Base")
    
    # Subir archivo
    st.markdown("### Subir archivo Excel")
    uploaded_file = st.file_uploader(
        "Selecciona el archivo Excel de Moviments Vi Base",
        type=["xlsx", "xls"],
        key="moviments_vi_base_file"
    )
    
    st.markdown("---")
    
    # Botón de procesamiento
    if st.button("🚀 Procesar Archivo", type="primary", disabled=uploaded_file is None):
        if uploaded_file is not None:
            try:
                # Mostrar progreso
                progress_bar = st.progress(0, text="Iniciando procesamiento...")
                
                progress_bar.progress(20, text="Leyendo archivo Excel...")
                file_bytes = uploaded_file.read()
                
                progress_bar.progress(40, text="Detectando encabezados...")
                
                progress_bar.progress(60, text="Normalizando datos...")
                
                progress_bar.progress(80, text="Procesando agrupación...")
                
                # Procesar archivo
                df_resultado, excel_bytes = procesar_moviments_vi_base(file_bytes)
                
                progress_bar.progress(100, text="✅ Procesamiento completado")
                
                # Guardar en session_state
                st.session_state["df_moviments_resultado"] = df_resultado
                st.session_state["excel_moviments_bytes"] = excel_bytes
                
                # Mostrar resumen
                st.success(f"✅ Archivo procesado correctamente")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total registros", len(df_resultado))
                with col2:
                    st.metric("Instalaciones únicas", df_resultado["Instalacion"].nunique())
                with col3:
                    st.metric("Tipos de vino", df_resultado["TipoVinoBase"].nunique())
                
                # Botón de descarga
                st.download_button(
                    label="📥 Descargar Acumulado_Vi_Base.xlsx",
                    data=excel_bytes,
                    file_name="Acumulado_Vi_Base.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"❌ Error al procesar el archivo: {str(e)}")
                st.exception(e)
    
    # Estado del procesamiento
    if "df_moviments_resultado" in st.session_state:
        st.info("✅ Datos procesados disponibles en la pestaña 'Tabla Resultados'")
    else:
        st.info("📂 Sube un archivo Excel para comenzar el procesamiento")

with tab2:
    st.subheader("Tabla de Resultados")
    
    if "df_moviments_resultado" in st.session_state:
        df_resultado = st.session_state["df_moviments_resultado"]
        
        # Métricas en contenedor más compacto
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total registros", len(df_resultado))
        with col2:
            st.metric("Instalaciones", df_resultado["Instalacion"].nunique())
        with col3:
            st.metric("Empresas", df_resultado["Empresa"].nunique())
        with col4:
            st.metric("Zonas", df_resultado["Zona"].nunique())
        
        # Crear columna combinada Empresa_Instalacion
        df_resultado_con_empresa_instalacion = df_resultado.copy()
        df_resultado_con_empresa_instalacion["Empresa_Instalacion"] = (
            df_resultado_con_empresa_instalacion["Empresa"] + "->" + 
            df_resultado_con_empresa_instalacion["Instalacion"]
        )
        
        # Sección de filtros más compacta
        with st.container():
            st.markdown("### 🔍 Filtros")
            
            # Botón de reset en una sola línea
            if st.button("🔄 Reestablecer filtros", use_container_width=True):
                # Resetear todos los filtros usando session_state
                for key in ["filtro_empresa_instalacion", "filtro_tipo_vino", "filtro_segmento", "filtro_zona", "filtro_subzona"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
            
            # Filtros en layout más compacto - 3 columnas en lugar de 2
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            col_filter4, col_filter5 = st.columns(2)
            
            # Aplicar filtros de forma cascada
            df_filtrado = df_resultado_con_empresa_instalacion.copy()
            
            with col_filter1:
                # Filtro Empresa-Instalación
                empresas_instalacion_disponibles = ["Todas"] + sorted(df_filtrado["Empresa_Instalacion"].dropna().unique().tolist())
                empresa_instalacion_seleccionada = st.selectbox("Empresa - Instalación", empresas_instalacion_disponibles, key="filtro_empresa_instalacion")
                
                # Aplicar filtro
                if empresa_instalacion_seleccionada != "Todas":
                    df_filtrado = df_filtrado[df_filtrado["Empresa_Instalacion"] == empresa_instalacion_seleccionada]
            
            with col_filter2:
                # Filtro Tipo Vino Base
                tipos_vino_disponibles = ["Todos"] + sorted(df_filtrado["TipoVinoBase"].dropna().unique().tolist())
                tipo_vino_seleccionado = st.selectbox("Tipo Vino Base", tipos_vino_disponibles, key="filtro_tipo_vino")
                
                # Aplicar filtro
                if tipo_vino_seleccionado != "Todos":
                    df_filtrado = df_filtrado[df_filtrado["TipoVinoBase"] == tipo_vino_seleccionado]
            
            with col_filter3:
                # Filtro Segmento
                segmentos_disponibles = ["Todos"] + sorted(df_filtrado["Segmento"].dropna().unique().tolist())
                segmento_seleccionado = st.selectbox("Segmento", segmentos_disponibles, key="filtro_segmento")
                
                # Aplicar filtro
                if segmento_seleccionado != "Todos":
                    df_filtrado = df_filtrado[df_filtrado["Segmento"] == segmento_seleccionado]
            
            with col_filter4:
                # Filtro Zona
                zonas_disponibles = ["Todas"] + sorted(df_filtrado["Zona"].dropna().unique().tolist())
                zona_seleccionada = st.selectbox("Zona", zonas_disponibles, key="filtro_zona")
                
                # Aplicar filtro
                if zona_seleccionada != "Todas":
                    df_filtrado = df_filtrado[df_filtrado["Zona"] == zona_seleccionada]
            
            with col_filter5:
                # Filtro SubZona
                subzonas_disponibles = ["Todas"] + sorted(df_filtrado["SubZona"].dropna().unique().tolist())
                subzona_seleccionada = st.selectbox("SubZona", subzonas_disponibles, key="filtro_subzona")
                
                # Aplicar filtro
                if subzona_seleccionada != "Todas":
                    df_filtrado = df_filtrado[df_filtrado["SubZona"] == subzona_seleccionada]
        
        st.markdown(f"### 📋 Tabla Filtrada ({len(df_filtrado)} registros)")
        
        # Configurar AgGrid - Reordenar columnas para mostrar Empresa_Instalacion
        columnas_mostrar = ["Fecha", "Empresa_Instalacion", "TipoVinoBase", "Segmento", "Zona", "SubZona", "Acumulado"]
        df_para_mostrar = df_filtrado[columnas_mostrar].copy()
        
        # Configurar AgGrid para máximo aprovechamiento del ancho
        gb = GridOptionsBuilder.from_dataframe(df_para_mostrar)
        gb.configure_default_column(
            resizable=True, 
            filter=True, 
            sortable=True,
            minWidth=100,
            flex=1  # Permite que las columnas se expandan proporcionalmente
        )
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_side_bar()
        
        # Configuraciones adicionales para maximizar el ancho
        gb.configure_grid_options(
            domLayout='normal',
            suppressHorizontalScroll=False,
            enableRangeSelection=True,
            rowSelection='multiple'
        )
        
        # Usar contenedor completo para la tabla
        AgGrid(
            df_para_mostrar,
            gridOptions=gb.build(),
            update_mode=GridUpdateMode.NO_UPDATE,
            height=600,  # Aumentar altura también
            fit_columns_on_grid_load=True,
            allow_unsafe_jscode=True,
            theme='streamlit'  # Tema que se adapta mejor al ancho
        )
        
        # Botón de descarga para datos filtrados
        if len(df_filtrado) < len(df_resultado_con_empresa_instalacion):
            st.markdown("### 📥 Descargar datos filtrados")
            
            # Generar Excel con datos filtrados (solo columnas relevantes)
            import io
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_para_mostrar.to_excel(writer, sheet_name="Datos Filtrados", index=False)
            
            st.download_button(
                label="📥 Descargar datos filtrados",
                data=output.getvalue(),
                file_name="Moviments_Vi_Base_Filtrado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    else:
        st.info("📂 Procesa un archivo en la pestaña 'Procesamiento' para ver los resultados aquí")

with tab3:
    st.subheader("Gráficos y Análisis")
    
    if "df_moviments_resultado" in st.session_state:
        st.info("📈 Esta sección estará disponible próximamente para visualizaciones gráficas")
        
        # Placeholder para futuros gráficos
        st.markdown("""
        ### 🚧 Próximamente disponible:
        
        - Gráficos de distribución por zona
        - Análisis temporal de acumulados
        - Comparativas por tipo de vino base
        - Mapas de instalaciones
        - Y más visualizaciones...
        """)
        
        # Mostrar algunos datos básicos mientras tanto
        df_resultado_con_empresa_instalacion = st.session_state["df_moviments_resultado"].copy()
        df_resultado_con_empresa_instalacion["Empresa_Instalacion"] = (
            df_resultado_con_empresa_instalacion["Empresa"] + "->" + 
            df_resultado_con_empresa_instalacion["Instalacion"]
        )
        
        # Top 10 Instalaciones por Acumulado - Tabla a todo lo ancho
        st.markdown("#### Top 10 Instalaciones por Acumulado")
        top_instalaciones = df_resultado_con_empresa_instalacion.nlargest(10, "Acumulado")[["Empresa_Instalacion", "Acumulado"]]
        
        # Configurar AgGrid para hacer la tabla clickeable
        gb_top = GridOptionsBuilder.from_dataframe(top_instalaciones)
        gb_top.configure_selection('single', use_checkbox=False, rowMultiSelectWithClick=False)
        gb_top.configure_default_column(resizable=True, sortable=True, flex=1)
        gb_top.configure_grid_options(domLayout='normal')
        
        # Mostrar tabla clickeable a todo lo ancho
        grid_response = AgGrid(
            top_instalaciones,
            gridOptions=gb_top.build(),
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            height=350,
            fit_columns_on_grid_load=True,
            theme='streamlit'
        )
        
        # Procesar selección
        if grid_response['selected_rows'] is not None and len(grid_response['selected_rows']) > 0:
            selected_instalacion = grid_response['selected_rows'].iloc[0]['Empresa_Instalacion']
            st.session_state['instalacion_seleccionada'] = selected_instalacion
            st.info(f"📍 Instalación seleccionada: {selected_instalacion}")
        
        # Distribución por Tipo de Vino Base - Tabla a todo lo ancho
        st.markdown("#### Distribución por Tipo de Vino Base")
        dist_tipo_vino = df_resultado_con_empresa_instalacion["TipoVinoBase"].value_counts().head(10)
        st.dataframe(dist_tipo_vino, use_container_width=True)
        
        # Mostrar detalle de la instalación seleccionada
        if 'instalacion_seleccionada' in st.session_state:
            st.markdown("---")
            instalacion_sel = st.session_state['instalacion_seleccionada']
            st.markdown(f"### 🔍 Detalle de: {instalacion_sel}")
            
            # Filtrar datos de la instalación seleccionada
            detalle_instalacion = df_resultado_con_empresa_instalacion[
                df_resultado_con_empresa_instalacion["Empresa_Instalacion"] == instalacion_sel
            ].copy()
            
            if not detalle_instalacion.empty:
                # Mostrar métricas de la instalación
                col_det1, col_det2, col_det3, col_det4 = st.columns(4)
                with col_det1:
                    st.metric("Total Registros", len(detalle_instalacion))
                with col_det2:
                    st.metric("Tipos de Vino", detalle_instalacion["TipoVinoBase"].nunique())
                with col_det3:
                    st.metric("Segmentos", detalle_instalacion["Segmento"].nunique())
                with col_det4:
                    st.metric("Acumulado Total", f"{detalle_instalacion['Acumulado'].sum():,.0f}")
                
                # Mostrar tabla detallada ordenada por fecha descendente y posición original
                st.markdown("#### 📋 Registros de la Instalación (ordenados por fecha más reciente)")
                
                # Ordenar por fecha descendente (más reciente primero) y luego por índice original
                detalle_ordenado = detalle_instalacion.sort_values(
                    by=["Fecha"], 
                    ascending=[False]
                ).copy()
                
                # Seleccionar columnas relevantes para mostrar
                columnas_detalle = ["Fecha", "TipoVinoBase", "Segmento", "Zona", "SubZona", "Acumulado"]
                detalle_mostrar = detalle_ordenado[columnas_detalle].copy()
                
                # Configurar AgGrid para el detalle
                gb_detalle = GridOptionsBuilder.from_dataframe(detalle_mostrar)
                gb_detalle.configure_default_column(
                    resizable=True, 
                    filter=True, 
                    sortable=True,
                    minWidth=100,
                    flex=1
                )
                gb_detalle.configure_pagination(paginationAutoPageSize=True)
                gb_detalle.configure_grid_options(domLayout='normal')
                
                AgGrid(
                    detalle_mostrar,
                    gridOptions=gb_detalle.build(),
                    update_mode=GridUpdateMode.NO_UPDATE,
                    height=400,
                    fit_columns_on_grid_load=True,
                    theme='streamlit'
                )
                
                # Botón para limpiar selección
                if st.button("🔄 Limpiar selección", key="limpiar_seleccion"):
                    if 'instalacion_seleccionada' in st.session_state:
                        del st.session_state['instalacion_seleccionada']
                    st.rerun()
    
    else:
        st.info("📂 Procesa un archivo en la pestaña 'Procesamiento' para ver los gráficos aquí")