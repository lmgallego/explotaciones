import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression
import io

# Configurar layout wide permanente
st.set_page_config(
    page_title="Moviments Vi Base",
    page_icon="🍇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cargar CSS personalizado también en esta página
try:
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(current_dir, '..', 'assets', 'styles.css')
    if os.path.exists(css_path):
        with open(css_path, 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except Exception:
    pass

from core.moviments_vi_base import procesar_moviments_vi_base
from core.colors import CUSTOM_PALETTE, CHART_COLORS, apply_custom_style_to_fig, get_color_sequence

# Funciones auxiliares para cálculo de acumulados
def obtener_acumulado_mas_reciente(grupo):
    """
    Selecciona siempre el registro más reciente (fecha máxima) para cada grupo.
    En caso de empate de fechas, desempata por menor FilaOriginal (orden original del Excel).
    """
    # Encontrar la fecha máxima en el grupo
    fecha_max = grupo['Fecha'].max()
    
    # Filtrar registros con fecha máxima
    registros_fecha_max = grupo[grupo['Fecha'] == fecha_max]
    
    # En caso de empate de fechas, tomar el registro con menor FilaOriginal (orden original)
    registro_seleccionado = registros_fecha_max.loc[registros_fecha_max['FilaOriginal'].idxmin()]
    
    return registro_seleccionado

def acumulado_estado_actual(df):
    """
    Calcula el estado actual tomando únicamente el último registro (más reciente)
    de cada combinación única: Empresa + TipoVinoBase + Segmento + Zona + SubZona.
    """
    columnas = ["Empresa", "TipoVinoBase", "Segmento", "Zona", "SubZona"]
    df_filtrado = df.groupby(columnas, group_keys=False).apply(obtener_acumulado_mas_reciente).reset_index(drop=True)
    return df_filtrado

def acumulado_historico_completo(df):
    """
    Mantiene todos los registros históricos para preservar la evolución temporal.
    Esta función es para mantener la lógica actual en la sección de Gráficos.
    """
    return df.copy()

def calcular_opcions_filtres_dinamics(df, filtres_actuals, camps_filtres):
    """
    Calcula les opcions disponibles per a cada filtre basant-se en les seleccions actuals.
    
    Args:
        df: DataFrame amb les dades
        filtres_actuals: Dict amb els valors actuals dels filtres
        camps_filtres: List amb els noms dels camps a filtrar
    
    Returns:
        Dict amb les opcions disponibles per a cada camp
    """
    opcions = {}
    
    # Per cada camp, calcular opcions basant-se en els altres filtres
    for camp_actual in camps_filtres:
        df_temp = df.copy()
        
        # Aplicar tots els filtres EXCEPTE el camp actual
        for camp, valor in filtres_actuals.items():
            if camp != camp_actual and valor not in ["Tots", "Todas", "Todos"] and camp in df_temp.columns:
                df_temp = df_temp[df_temp[camp] == valor]
        
        # Obtenir valors únics per al camp actual
        if camp_actual in df_temp.columns:
            valors_unics = sorted(df_temp[camp_actual].dropna().unique().tolist())
            
            # Afegir valor per defecte (siempre "Todos" para consistencia)
            opcions[camp_actual] = ["Todos"] + valors_unics
    
    return opcions

st.title("MOVIMENTS VI BASE")

# Crear pestañas
tab1, tab2, tab3, tab4 = st.tabs(["📂 Processament", "📊 Resultats", "📦 Gestió Stocks", "📈 Gràfics"])

with tab1:
    st.subheader("Gestió i visualització de Moviments Vi Base")
    
    # Subir archivo
    st.markdown("### Pujar arxiu Excel")
    uploaded_file = st.file_uploader(
        "Seleccionar arxiu moviments vi base Cavanet",
        type=["xlsx", "xls"],
        key="moviments_vi_base_file"
    )
    
    st.markdown("---")
    
    # Botón de procesamiento
    if st.button("Processar Arxiu", type="primary", disabled=uploaded_file is None):
        if uploaded_file is not None:
            try:
                # Mostrar progreso
                progress_bar = st.progress(0, text="Iniciant processament...")
                
                progress_bar.progress(20, text="Llegint arxiu...")
                file_bytes = uploaded_file.read()
                
                progress_bar.progress(40, text="Detectant headers...")
                
                progress_bar.progress(60, text="Normalitzant dades...")
                
                progress_bar.progress(80, text="Procesant agrupació...")
                
                # Procesar archivo
                df_resultado, excel_bytes = procesar_moviments_vi_base(file_bytes)
                
                progress_bar.progress(100, text="✅ Processament Completant amb èxit")
                
                # Guardar en session_state
                st.session_state["df_moviments_resultado"] = df_resultado
                st.session_state["excel_moviments_bytes"] = excel_bytes
                
                # Mostrar resumen
                st.success(f"✅ Arxiu processat amb èxit")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total registres", len(df_resultado))
                with col2:
                    st.metric("Instal.lacions Ùniques", df_resultado["Instalacion"].nunique())
                with col3:
                    st.metric("Tipos de vi", df_resultado["TipoVinoBase"].nunique())
                
                # Botón de descarga
                st.download_button(
                    label="📥 Descarregar Excel",
                    data=excel_bytes,
                    file_name="Acumulado_Vi_Base.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"❌ Error al processar l'arxiu: {str(e)}")
                st.exception(e)
    
    # Mostrar información si hay datos procesados
    if "df_moviments_resultado" in st.session_state:
        st.info("✅ Dades processades disponibles a la secció 'Resultats'")

with tab2:
    st.subheader("Resultats")
    
    if "df_moviments_resultado" in st.session_state:
        df_resultado = st.session_state["df_moviments_resultado"]
        
        # Métricas en contenedor más compacto
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total registres", len(df_resultado))
        with col2:
            st.metric("Instal.lacions", df_resultado["Instalacion"].nunique())
        with col3:
            st.metric("Empreses", df_resultado["Empresa"].nunique())
        with col4:
            st.metric("Zones", df_resultado["Zona"].nunique())
        
        # Crear columna combinada Empresa_Instalacion
        df_resultado_con_empresa_instalacion = df_resultado.copy()
        df_resultado_con_empresa_instalacion["Empresa_Instalacion"] = (
            df_resultado_con_empresa_instalacion["Empresa"] + "->" + 
            df_resultado_con_empresa_instalacion["Instalacion"]
        )
        
        # Sección de filtros más compacta
        with st.container():
            st.markdown("### 🔍 Filtres")
            
            # Botón de reset en una sola línea
            if st.button("🔄 Reestablir filtres", use_container_width=True):
                # Resetear todos los filtros usando session_state
                for key in ["filtro_empresa_instalacion", "filtro_tipo_vino", "filtro_segmento", "filtro_zona", "filtro_subzona"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
            
            # Filtros en layout más compacto - 3 columnas en lugar de 2
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            col_filter4, col_filter5 = st.columns(2)
            
            # Aplicar filtres dinàmics
            df_filtrado = df_resultado_con_empresa_instalacion.copy()
            
            # Obtener valores actuales de los filtros (todos con "Todos" para consistencia)
            filtres_actuals = {
                'Empresa_Instalacion': st.session_state.get('filtro_empresa_instalacion', 'Todos'),
                'TipoVinoBase': st.session_state.get('filtro_tipo_vino', 'Todos'),
                'Segmento': st.session_state.get('filtro_segmento', 'Todos'),
                'Zona': st.session_state.get('filtro_zona', 'Todos'),
                'SubZona': st.session_state.get('filtro_subzona', 'Todos')
            }
            
            # Calcular opciones disponibles de forma dinámica e inteligente
            # Cada filtro muestra opciones basadas en los OTROS filtros activos
            camps_filtres = ['Empresa_Instalacion', 'TipoVinoBase', 'Segmento', 'Zona', 'SubZona']
            opcions_disponibles = calcular_opcions_filtres_dinamics(df_resultado_con_empresa_instalacion, filtres_actuals, camps_filtres)


            with col_filter1:
                # Filtro Empresa-Instalación
                empresa_instalacion_seleccionada = st.selectbox(
                    "Empresa - Instalación", 
                    opcions_disponibles['Empresa_Instalacion'], 
                    index=0 if filtres_actuals['Empresa_Instalacion'] not in opcions_disponibles['Empresa_Instalacion'] 
                          else opcions_disponibles['Empresa_Instalacion'].index(filtres_actuals['Empresa_Instalacion']),
                    key="filtro_empresa_instalacion"
                )
                
                # Aplicar filtro
                if empresa_instalacion_seleccionada != "Todos":
                    df_filtrado = df_filtrado[df_filtrado["Empresa_Instalacion"] == empresa_instalacion_seleccionada]
            
            with col_filter2:
                # Filtro Tipo Vino Base
                tipo_vino_seleccionado = st.selectbox(
                    "Tipo Vino Base", 
                    opcions_disponibles['TipoVinoBase'], 
                    index=0 if filtres_actuals['TipoVinoBase'] not in opcions_disponibles['TipoVinoBase'] 
                          else opcions_disponibles['TipoVinoBase'].index(filtres_actuals['TipoVinoBase']),
                    key="filtro_tipo_vino"
                )
                
                # Aplicar filtro
                if tipo_vino_seleccionado != "Todos":
                    df_filtrado = df_filtrado[df_filtrado["TipoVinoBase"] == tipo_vino_seleccionado]
            
            with col_filter3:
                # Filtro Segmento
                segmento_seleccionado = st.selectbox(
                    "Segmento", 
                    opcions_disponibles['Segmento'], 
                    index=0 if filtres_actuals['Segmento'] not in opcions_disponibles['Segmento'] 
                          else opcions_disponibles['Segmento'].index(filtres_actuals['Segmento']),
                    key="filtro_segmento"
                )
                
                # Aplicar filtro
                if segmento_seleccionado != "Todos":
                    df_filtrado = df_filtrado[df_filtrado["Segmento"] == segmento_seleccionado]
            
            with col_filter4:
                # Filtro Zona
                zona_seleccionada = st.selectbox(
                    "Zona", 
                    opcions_disponibles['Zona'], 
                    index=0 if filtres_actuals['Zona'] not in opcions_disponibles['Zona'] 
                          else opcions_disponibles['Zona'].index(filtres_actuals['Zona']),
                    key="filtro_zona"
                )
                
                # Aplicar filtro
                if zona_seleccionada != "Todos":
                    df_filtrado = df_filtrado[df_filtrado["Zona"] == zona_seleccionada]
            
            with col_filter5:
                # Filtro SubZona
                subzona_seleccionada = st.selectbox(
                    "SubZona", 
                    opcions_disponibles['SubZona'], 
                    index=0 if filtres_actuals['SubZona'] not in opcions_disponibles['SubZona'] 
                          else opcions_disponibles['SubZona'].index(filtres_actuals['SubZona']),
                    key="filtro_subzona"
                )
                
                # Aplicar filtro
                if subzona_seleccionada != "Todos":
                    df_filtrado = df_filtrado[df_filtrado["SubZona"] == subzona_seleccionada]
        
        # Verificar si hay algún filtro activo
        filtros_activos = []
        if empresa_instalacion_seleccionada != "Todos":
            filtros_activos.append(f"Empresa: {empresa_instalacion_seleccionada}")
        if tipo_vino_seleccionado != "Todos":
            filtros_activos.append(f"Tipo Vino: {tipo_vino_seleccionado}")
        if segmento_seleccionado != "Todos":
            filtros_activos.append(f"Segmento: {segmento_seleccionado}")
        if zona_seleccionada != "Todos":
            filtros_activos.append(f"Zona: {zona_seleccionada}")
        if subzona_seleccionada != "Todos":
            filtros_activos.append(f"SubZona: {subzona_seleccionada}")
        
        # Mostrar tabla solo si hay filtros activos
        if len(filtros_activos) > 0:
            # Mostrar información de filtrado
            st.info(f"📊 Mostrant {len(df_filtrado):,} registres | Filtres actius: {', '.join(filtros_activos)}")
            
            st.markdown(f"### 📋 Taula filtrada ({len(df_filtrado)} registres)")
            
            # Preparar datos para mostrar
            columnas_mostrar = ["Fecha", "Empresa_Instalacion", "TipoVinoBase", "Segmento", "Zona", "SubZona", "Acumulado"]
            df_para_mostrar = df_filtrado[columnas_mostrar].copy()
            
            # Convertir Fecha a string si es datetime
            if pd.api.types.is_datetime64_any_dtype(df_para_mostrar['Fecha']):
                df_para_mostrar['Fecha'] = df_para_mostrar['Fecha'].dt.strftime('%d/%m/%Y')
            
            # Convertir tipos numpy a Python nativos para evitar problemas
            for col in df_para_mostrar.select_dtypes(include=['int64', 'int32', 'int16', 'int8']).columns:
                df_para_mostrar[col] = df_para_mostrar[col].astype(object)
            for col in df_para_mostrar.select_dtypes(include=['float64', 'float32']).columns:
                df_para_mostrar[col] = df_para_mostrar[col].astype(object)
            
            # Resetear índice
            df_para_mostrar = df_para_mostrar.reset_index(drop=True)
            
            # Mostrar tabla con st.dataframe nativo (más rápido y confiable)
            st.dataframe(
                df_para_mostrar,
                use_container_width=True,
                height=600,
                hide_index=True,
                column_config={
                    "Fecha": st.column_config.TextColumn("Fecha", width="small"),
                    "Empresa_Instalacion": st.column_config.TextColumn("Empresa - Instalación", width="large"),
                    "TipoVinoBase": st.column_config.TextColumn("Tipo Vino Base", width="medium"),
                    "Segmento": st.column_config.TextColumn("Segmento", width="medium"),
                    "Zona": st.column_config.TextColumn("Zona", width="medium"),
                    "SubZona": st.column_config.TextColumn("SubZona", width="medium"),
                    "Acumulado": st.column_config.NumberColumn(
                        "Acumulado",
                        format="%d",
                        width="medium"
                    )
                }
            )
        else:
            # Mostrar mensaje cuando no hay filtros activos
            st.info("👆 Selecciona almenys un filtre per veure els resultats")
            st.markdown(f"### 📊 Dades disponibles: {len(df_resultado_con_empresa_instalacion):,} registres totals")
        
        # Botón de descarga para datos filtrados
        if len(df_filtrado) < len(df_resultado_con_empresa_instalacion):
            st.markdown("### 📥 Descarregar dades filtrades")
            
            # Generar Excel con datos filtrados (solo columnas relevantes)
            import io
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_para_mostrar.to_excel(writer, sheet_name="Datos Filtrados", index=False)
            
            st.download_button(
                label="📥 Descarregar Excel filtrat",
                data=output.getvalue(),
                file_name="Moviments_Vi_Base_Filtrado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    else:
        st.info("📂 Processa un fitxer a la pestanya 'Processament' per veure els resultats aquí")

with tab3:
    st.subheader("Gestió Stocks")
    
    if "df_moviments_resultado" in st.session_state:
        df_resultado_con_empresa_instalacion = st.session_state["df_moviments_resultado"].copy()
        df_resultado_con_empresa_instalacion["Empresa_Instalacion"] = (
            df_resultado_con_empresa_instalacion["Empresa"] + "->" + 
            df_resultado_con_empresa_instalacion["Instalacion"]
        )
        
        # Crear columna FilaOriginal para mantener el orden original del Excel
        df_resultado_con_empresa_instalacion['FilaOriginal'] = range(len(df_resultado_con_empresa_instalacion))
        # Convertir Fecha a datetime para comparar correctamente por fecha más reciente
        if not pd.api.types.is_datetime64_any_dtype(df_resultado_con_empresa_instalacion['Fecha']):
            df_resultado_con_empresa_instalacion['Fecha'] = pd.to_datetime(
                df_resultado_con_empresa_instalacion['Fecha'],
                format='%d/%m/%Y',
                dayfirst=True,
                errors='coerce'
            )
        
        # Todas las Instalaciones con Acumulado > 0 - Tabla a todo lo ancho
        st.markdown("#### Instal.lacions amb Acumulat")
        
        # Agrupar por Empresa_Instalacion y sumar acumulados, luego filtrar > 0
        # Usar lógica de estado actual: último registro por combinación única
        df_estado_actual = acumulado_estado_actual(df_resultado_con_empresa_instalacion)
        
        instalaciones_agrupadas = df_estado_actual.groupby("Empresa_Instalacion")["Acumulado"].sum().reset_index()
        
        instalaciones_con_acumulado = instalaciones_agrupadas[instalaciones_agrupadas["Acumulado"] > 0].sort_values("Acumulado", ascending=False)
        # Convertir tipos numpy a Python nativos antes de AgGrid
        instalaciones_con_acumulado = instalaciones_con_acumulado.copy()
        for col in instalaciones_con_acumulado.select_dtypes(include=['int64', 'int32', 'int16', 'int8']).columns:
            instalaciones_con_acumulado[col] = instalaciones_con_acumulado[col].astype(object)
        for col in instalaciones_con_acumulado.select_dtypes(include=['float64', 'float32']).columns:
            instalaciones_con_acumulado[col] = instalaciones_con_acumulado[col].astype(object)
        
        
        # Buscador dinámico con botón de limpieza
        col_search, col_clear = st.columns([4, 1])
        with col_search:
            search_term = st.text_input(
                "🔍 Cerca Empresa-Instalació",
                placeholder="Escriu per filtrar...",
                key="search_instalacion_input"
            )
        with col_clear:
            st.write("")  # Espaciado
            if st.button("🗑️ Netejar", key="clear_search", use_container_width=True):
                # Limpiar el campo mediante query params para forzar reset
                st.query_params.clear()
                del st.session_state['search_instalacion_input']
                st.rerun()
        
        # Filtrar por término de búsqueda si existe (filtrado dinámico)
        if search_term:
            instalaciones_con_acumulado = instalaciones_con_acumulado[
                instalaciones_con_acumulado['Empresa_Instalacion'].str.contains(search_term, case=False, na=False)
            ]
        
        # Mostrar contador de resultados
        st.caption(f"Mostrant {len(instalaciones_con_acumulado)} instal·lacions")
        
        # Mostrar tabla con selección usando st.dataframe
        event = st.dataframe(
            instalaciones_con_acumulado,
            use_container_width=True,
            height=400,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            column_config={
                "Empresa_Instalacion": st.column_config.TextColumn("Empresa - Instalación", width="large"),
                "Acumulado": st.column_config.NumberColumn(
                    "Acumulado",
                    format="%d",
                    width="medium"
                )
            }
        )
        
        # Procesar selección
        if len(event.selection.rows) > 0:
            selected_idx = event.selection.rows[0]
            selected_instalacion = str(instalaciones_con_acumulado.iloc[selected_idx]['Empresa_Instalacion'])
            st.session_state['instalacion_seleccionada'] = selected_instalacion
        
        # Mostrar detalle de la instalación seleccionada
        if 'instalacion_seleccionada' in st.session_state:
            st.markdown("---")
            instalacion_sel = st.session_state['instalacion_seleccionada']
            st.markdown(f"### 🔍 Detall de: {instalacion_sel}")
            
            # Filtrar datos de la instalación seleccionada y aplicar lógica de estado actual
            detalle_instalacion_completo = df_resultado_con_empresa_instalacion[
                df_resultado_con_empresa_instalacion["Empresa_Instalacion"] == instalacion_sel
            ].copy()
            
            # Aplicar lógica de estado actual para el detalle de la instalación
            detalle_instalacion = acumulado_estado_actual(detalle_instalacion_completo)
            
            if not detalle_instalacion.empty:
                # Mostrar métricas de la instalación
                col_det1, col_det2, col_det3, col_det4 = st.columns(4)
                with col_det1:
                    st.metric("Total Registres", len(detalle_instalacion))
                with col_det2:
                    st.metric("Tipus de Vi", detalle_instalacion["TipoVinoBase"].nunique())
                with col_det3:
                    st.metric("Segments", detalle_instalacion["Segmento"].nunique())
                with col_det4:
                    st.metric("Acumulat Total", f"{detalle_instalacion['Acumulado'].sum():,.0f}")
                
                # Mostrar tabla detallada ordenada por fecha descendente y posición original
                st.markdown("#### Registres de l'instal.lació")
                
                # Ordenar por fecha descendente (más reciente primero) y luego por índice original
                detalle_ordenado = detalle_instalacion.sort_values(
                    by=["Fecha", "FilaOriginal"], 
                    ascending=[False, True]
                ).copy()
                
                # Seleccionar columnas relevantes para mostrar y filtrar acumulado > 0
                columnas_detalle = ["Fecha", "TipoVinoBase", "Segmento", "Zona", "SubZona", "Acumulado"]
                detalle_mostrar = detalle_ordenado[columnas_detalle].copy()
                # Filtrar registros con acumulado mayor a 0
                detalle_mostrar = detalle_mostrar[detalle_mostrar["Acumulado"] > 0]
                
                # Convertir Fecha a string para visualización
                if 'Fecha' in detalle_mostrar.columns:
                    detalle_mostrar['Fecha'] = detalle_mostrar['Fecha'].dt.strftime('%d/%m/%Y')
                
                # Convertir tipos numpy a tipos Python nativos para evitar errores de serialización JSON
                # Forzar a object dtype para que pandas no reconvierta a numpy
                for col in detalle_mostrar.select_dtypes(include=['int64', 'int32', 'int16', 'int8']).columns:
                    detalle_mostrar[col] = detalle_mostrar[col].astype(object)
                for col in detalle_mostrar.select_dtypes(include=['float64', 'float32']).columns:
                    detalle_mostrar[col] = detalle_mostrar[col].astype(object)
                
                # Resetear índice y asegurar que el DataFrame esté limpio
                detalle_mostrar = detalle_mostrar.reset_index(drop=True)
                
                # Mostrar tabla con st.dataframe (nativo de Streamlit, más confiable)
                st.dataframe(
                    detalle_mostrar,
                    use_container_width=True,
                    height=400,
                    hide_index=True,
                    column_config={
                        "Fecha": st.column_config.TextColumn("Fecha", width="medium"),
                        "TipoVinoBase": st.column_config.TextColumn("Tipo Vino Base", width="medium"),
                        "Segmento": st.column_config.TextColumn("Segmento", width="medium"),
                        "Zona": st.column_config.TextColumn("Zona", width="medium"),
                        "SubZona": st.column_config.TextColumn("SubZona", width="medium"),
                        "Acumulado": st.column_config.NumberColumn(
                            "Acumulado",
                            format="%d",
                            width="medium"
                        )
                    }
                )
                
                # Botón para limpiar selección
                if st.button("🔄 Netejar selecció", key="limpiar_seleccion"):
                    if 'instalacion_seleccionada' in st.session_state:
                        del st.session_state['instalacion_seleccionada']
                    st.rerun()
    
    else:
        st.info("📂 Procesa l'arxiu per veure els resultats aquí")

with tab4:
    st.subheader("Gràfics")
    
    if "df_moviments_resultado" in st.session_state:
        df_resultado = st.session_state["df_moviments_resultado"]
        
        # Crear columna FilaOriginal para mantener el orden original del Excel
        df_resultado = df_resultado.copy()
        df_resultado['FilaOriginal'] = range(len(df_resultado))
        
        # Convertir la columna Fecha a datetime si no lo está
        if not pd.api.types.is_datetime64_any_dtype(df_resultado['Fecha']):
            df_resultado['Fecha'] = pd.to_datetime(df_resultado['Fecha'], format='%d/%m/%Y', dayfirst=True)
        
        # ====== Insights anuals (no afectats per filtres) ======
        try:
            df_any = df_resultado.copy()
            any_actual = pd.Timestamp.today().year
            df_any['Any'] = df_any['Fecha'].dt.year
            df_any_actual = df_any[df_any['Any'] == any_actual]
            
            # Agrupació com a "Mètriques per Segment": per cada combinació única
            # ens quedem amb el registre més recent (i en cas d'empat, el de menor FilaOriginal)
            if not df_any_actual.empty:
                df_any_actual_agrupat = (
                    df_any_actual.groupby(['Empresa','TipoVinoBase','Zona','SubZona','Segmento'], group_keys=False)
                                 .apply(lambda g: g.sort_values(['Fecha','FilaOriginal'], ascending=[False, True]).iloc[0])
                                 .reset_index(drop=True)
                )
            else:
                df_any_actual_agrupat = df_any_actual
            
            # Càlculs com a "Mètriques per Segment" però limitats a l'any en curs
            litres_actuals = float(df_any_actual_agrupat['Acumulado'].sum()) if not df_any_actual_agrupat.empty else 0.0
            guarda = float(df_any_actual_agrupat[df_any_actual_agrupat['Segmento'] == 'Guarda']['Acumulado'].sum()) if not df_any_actual_agrupat.empty else 0.0
            guarda_superior = float(df_any_actual_agrupat[df_any_actual_agrupat['Segmento'] == 'Guarda Superior']['Acumulado'].sum()) if not df_any_actual_agrupat.empty else 0.0
            gs_paratge = float(df_any_actual_agrupat[df_any_actual_agrupat['Segmento'] == 'Guarda Superior Paratge Qualificat']['Acumulado'].sum()) if not df_any_actual_agrupat.empty else 0.0
            
            # Comptatge de registres basat en la mateixa agrupació
            regs_total = int(len(df_any_actual_agrupat))
            regs_guarda = int(len(df_any_actual_agrupat[df_any_actual_agrupat['Segmento'] == 'Guarda']))
            regs_guarda_sup = int(len(df_any_actual_agrupat[df_any_actual_agrupat['Segmento'] == 'Guarda Superior']))
            regs_gs_paratge = int(len(df_any_actual_agrupat[df_any_actual_agrupat['Segmento'] == 'Guarda Superior Paratge Qualificat']))
            
            col_i1, col_i2, col_i3, col_i4 = st.columns(4)
            
            def fmt(v):
                return f"{v:,.0f}" if v else "0"
            
            with col_i1:
                st.markdown('<div class="insight-card"><div class="insight-title">Litres Actuals</div><div class="insight-value">' + fmt(litres_actuals) + '</div><div class="insight-subtitle">' + str(regs_total) + ' registres</div></div>', unsafe_allow_html=True)
            with col_i2:
                st.markdown('<div class="insight-card"><div class="insight-title">Guarda</div><div class="insight-value">' + fmt(guarda) + '</div><div class="insight-subtitle">' + str(regs_guarda) + ' registres</div></div>', unsafe_allow_html=True)
            with col_i3:
                st.markdown('<div class="insight-card"><div class="insight-title">Guarda Superior</div><div class="insight-value">' + fmt(guarda_superior) + '</div><div class="insight-subtitle">' + str(regs_guarda_sup) + ' registres</div></div>', unsafe_allow_html=True)
            with col_i4:
                st.markdown('<div class="insight-card"><div class="insight-title">G.S. Paratge Qualificat</div><div class="insight-value">' + fmt(gs_paratge) + '</div><div class="insight-subtitle">' + str(regs_gs_paratge) + ' registres</div></div>', unsafe_allow_html=True)
        except Exception as _e:
            st.caption("No s'han pogut calcular els insights anuals.")
        
        
        # Botón de descarga para registros utilizados en el cálculo de insights
        try:
            if 'df_any_actual_agrupat' in locals() and not df_any_actual_agrupat.empty:
                st.markdown("---")
                st.markdown("#### 📥 Descarregar registres utilitzats per al càlcul")
                
                # Preparar DataFrame para descarga
                df_descarga = df_any_actual_agrupat.copy()
                
                # Convertir Fecha a string si es datetime
                if pd.api.types.is_datetime64_any_dtype(df_descarga['Fecha']):
                    df_descarga['Fecha'] = df_descarga['Fecha'].dt.strftime('%d/%m/%Y')
                
                # Seleccionar columnas relevantes
                columnas_descarga = ['Fecha', 'Empresa', 'Instalacion', 'TipoVinoBase', 'Zona', 'SubZona', 'Segmento', 'Acumulado']
                df_descarga = df_descarga[[col for col in columnas_descarga if col in df_descarga.columns]]
                
                # Generar Excel
                output_insights = io.BytesIO()
                with pd.ExcelWriter(output_insights, engine="openpyxl") as writer:
                    df_descarga.to_excel(writer, sheet_name=f"Insights_{any_actual}", index=False)
                
                st.download_button(
                    label=f"📥 Descarregar registres insights {any_actual} ({len(df_descarga)} registres)",
                    data=output_insights.getvalue(),
                    file_name=f"Insights_Calcul_{any_actual}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        except Exception:
            pass
        # Selector de rango de fechas
        st.markdown("### Seleccionar Rang de Dates")
        
        # Obtener información de fechas disponibles
        min_date = df_resultado['Fecha'].min().date()
        max_date = df_resultado['Fecha'].max().date()
        min_year = df_resultado['Fecha'].dt.year.min()
        max_year = df_resultado['Fecha'].dt.year.max()
        
        # Selector de tipo de filtro de fecha
        tipo_filtro_fecha = st.radio(
            "Selecciona el tipo de filtro de fecha:",
            options=["📅 Per Dates", "📆 Per Anys", "🗓️ Per Mesos"],
            horizontal=True,
            key="tipo_filtro_fecha_graficos"
        )
        
        # Inicializar df_filtrado_fechas con todos los datos
        df_filtrado_fechas = df_resultado.copy()
        
        if tipo_filtro_fecha == "📅 Per Dates":
            st.markdown("**Selecciona un rang de dates específic**")
            col_date1, col_date2 = st.columns(2)
            
            with col_date1:
                # Establecer fecha de inicio por defecto al 01/01/2025
                from datetime import date
                default_start_date = date(2025, 1, 1)
                
                fecha_inicio = st.date_input(
                    "Fecha de Inicio",
                    value=default_start_date,
                    min_value=min_date,
                    max_value=max_date,
                    key="fecha_inicio_graficos"
                )
            
            with col_date2:
                fecha_fin = st.date_input(
                    "Fecha de Fin",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date,
                    key="fecha_fin_graficos"
                )
            
            # Filtrar datos por rango de fechas
            df_filtrado_fechas = df_resultado[
                (df_resultado['Fecha'].dt.date >= fecha_inicio) & 
                (df_resultado['Fecha'].dt.date <= fecha_fin)
            ].copy()
            
            st.info(f"📊 Mostrant dades del {fecha_inicio} al {fecha_fin}")
        
        elif tipo_filtro_fecha == "📆 Per Anys":
            st.markdown("**Selecciona un o més anys**")
            
            # Obtener lista de años disponibles
            years_available = sorted(df_resultado['Fecha'].dt.year.unique())
            
            # Selector múltiple de años
            selected_years = st.multiselect(
                "Selecciona els anys:",
                options=years_available,
                default=[2025] if 2025 in years_available else [max_year],
                key="selected_years_graficos"
            )
            
            if selected_years:
                # Filtrar datos por años seleccionados
                df_filtrado_fechas = df_resultado[
                    df_resultado['Fecha'].dt.year.isin(selected_years)
                ].copy()
                
                st.info(f"📊 Mostrant dades per als anys: {', '.join(map(str, selected_years))}")
            else:
                st.warning("⚠️ Selecciona almenys un any")
                df_filtrado_fechas = df_resultado.copy()
        
        elif tipo_filtro_fecha == "🗓️ Per Mesos":
            st.markdown("**Selecciona un o més mesos**")
            
            col_year_month, col_months = st.columns([1, 2])
            
            with col_year_month:
                # Selector de año para filtrar meses
                year_for_months = st.selectbox(
                    "Any de referència:",
                    options=sorted(df_resultado['Fecha'].dt.year.unique()),
                    index=len(sorted(df_resultado['Fecha'].dt.year.unique())) - 1,  # Último año por defecto
                    key="year_for_months_graficos"
                )
            
            with col_months:
                # Obtener meses disponibles para el año seleccionado
                months_in_year = df_resultado[
                    df_resultado['Fecha'].dt.year == year_for_months
                ]['Fecha'].dt.month.unique()
                
                month_names = {
                    1: "Gener", 2: "Febrer", 3: "Març", 4: "Abril",
                    5: "Maig", 6: "Juny", 7: "Juliol", 8: "Agost",
                    9: "Setembre", 10: "Octubre", 11: "Novembre", 12: "Desembre"
                }
                
                available_months = [(month, month_names[month]) for month in sorted(months_in_year)]
                
                selected_months = st.multiselect(
                    "Selecciona els mesos:",
                    options=[month[0] for month in available_months],
                    format_func=lambda x: month_names[x],
                    default=[month[0] for month in available_months[:3]] if available_months else [],
                    key="selected_months_graficos"
                )
            
            if selected_months:
                # Filtrar datos por año y meses seleccionados
                df_filtrado_fechas = df_resultado[
                    (df_resultado['Fecha'].dt.year == year_for_months) &
                    (df_resultado['Fecha'].dt.month.isin(selected_months))
                ].copy()
                
                selected_month_names = [month_names[month] for month in selected_months]
                st.info(f"📊 Mostrant dades per {year_for_months}: {', '.join(selected_month_names)}")
            else:
                st.warning("⚠️ Selecciona almenys un mes")
                df_filtrado_fechas = df_resultado[
                    df_resultado['Fecha'].dt.year == year_for_months
                ].copy()
        
        if len(df_filtrado_fechas) == 0:
            st.warning("⚠️ No hi ha dades en el període seleccionat")
        else:
            # Crear columna de semana
            df_filtrado_fechas['Semana'] = df_filtrado_fechas['Fecha'].dt.to_period('W').astype(str)
            df_filtrado_fechas['SemanaInicio'] = df_filtrado_fechas['Fecha'].dt.to_period('W').apply(lambda p: p.start_time)
            
            # Función para obtener el acumulado más reciente por grupo
            def obtener_acumulado_mas_reciente(grupo):
                """
                Para un grupo, devuelve el registro completo con fecha más reciente.
                En caso de empate de fechas, devuelve el de menor FilaOriginal (orden original del Excel).
                """
                # Encontrar la fecha máxima en el grupo
                fecha_max = grupo['Fecha'].max()
                
                # Filtrar registros con fecha máxima
                registros_fecha_max = grupo[grupo['Fecha'] == fecha_max]
                
                # En caso de empate de fechas, tomar el registro con menor FilaOriginal (orden original)
                registro_seleccionado = registros_fecha_max.loc[registros_fecha_max['FilaOriginal'].idxmin()]
                
                return registro_seleccionado
            
            def obtener_acumulado_por_combinacion_unica(df, columnas_agrupacion):
                """
                Agrupa por las columnas especificadas (incluyendo Segmento) y obtiene el registro más reciente.
                En caso de empate de fecha, se queda con el de menor FilaOriginal (posición original en el Excel).
                """
                resultado = (
                    df.groupby(columnas_agrupacion, group_keys=False)
                      .apply(lambda grupo: grupo.sort_values(
                          ['Fecha','FilaOriginal'], ascending=[False, True]).iloc[0])
                      .reset_index(drop=True)
                )
                return resultado
            
            st.markdown("---")
            
            # Siempre usar modo agrupado (recomendado)
            usar_agrupacion = True
            
            st.markdown("---")
            
            # 1. GRÁFICO DE ACUMULADO TOTAL CON LÍNEA DE TENDENCIA
            st.markdown("### Acumulat total per setmanes")
            
            if usar_agrupacion:
                # Modo agrupado: obtener el acumulado más reciente de cada combinación única POR EMPRESA
                # Agrupa por: Empresa, TipoVinoBase, Zona, SubZona, Segmento
                df_agrupado = obtener_acumulado_por_combinacion_unica(df_filtrado_fechas, ['Empresa', 'TipoVinoBase', 'Zona', 'SubZona', 'Segmento'])
                
                # Re-agregar la columna Semana basada en los datos originales
                # Crear mapeo solo para Semana (Segmento ya está incluido en la agrupación)
                fecha_semana_map = df_filtrado_fechas[['Fecha', 'Semana']].drop_duplicates().set_index('Fecha')['Semana'].to_dict()
                
                df_agrupado['Semana'] = df_agrupado['Fecha'].map(fecha_semana_map)
                
                # Sumar por Semana (suma de todas las combinaciones únicas en cada semana)
                acumulado_semanal = df_agrupado.groupby(['Semana','SemanaInicio'])['Acumulado'].sum().reset_index()
                
            else:
                # Modo todos los registros: sumar directamente todos los acumulados por semana
                acumulado_semanal = df_filtrado_fechas.groupby(['Semana','SemanaInicio'])['Acumulado'].sum().reset_index()
            
            acumulado_semanal = acumulado_semanal.sort_values('SemanaInicio')
            
            # Crear gráfico de barras
            fig_barras = go.Figure()
            
            # Agregar barras
            fig_barras.add_trace(go.Bar(
                x=acumulado_semanal['Semana'],
                y=acumulado_semanal['Acumulado'],
                name='Acumulado Semanal',
                marker_color=CUSTOM_PALETTE['600'],
                opacity=0.8,
                hovertemplate='<b>Semana:</b> %{x}<br>' +
                             '<b>Acumulado:</b> %{y:,.0f}<br>' +
                             '<extra></extra>'
            ))
            
            # Calcular línea de tendencia (regresión lineal)
            if len(acumulado_semanal) > 1:
                x_numeric = np.arange(len(acumulado_semanal)).reshape(-1, 1)
                y_values = acumulado_semanal['Acumulado'].values
                
                reg_model = LinearRegression()
                reg_model.fit(x_numeric, y_values)
                y_pred = reg_model.predict(x_numeric)
                
                # Agregar línea de tendencia
                fig_barras.add_trace(go.Scatter(
                    x=acumulado_semanal['Semana'],
                    y=y_pred,
                    mode='lines',
                    name='Tendencia (Regresión Lineal)',
                    line=dict(color=CUSTOM_PALETTE['900'], width=3, dash='dash'),
                    hovertemplate='<b>Semana:</b> %{x}<br>' +
                                 '<b>Tendencia:</b> %{y:,.0f}<br>' +
                                 '<extra></extra>'
                ))
            
            # Aplicar estilo personalizado
            fig_barras = apply_custom_style_to_fig(fig_barras)
            fig_barras.update_layout(
                title="Acumulat Total per Setmanes",
                xaxis_title="Setmana",
                yaxis_title="Acumulat",
                height=400,
                showlegend=True,
                hovermode='x unified',
                hoverlabel=dict(
                    bgcolor="white",
                    bordercolor=CUSTOM_PALETTE['600'],
                    font_size=12,
                    font_family="Arial"
                )
            )
            
            st.plotly_chart(fig_barras, use_container_width=True)
            
            st.markdown("---")
            
            # 2. GRÁFICO DE PASTEL POR SEGMENTOS
            col_pie1, col_pie2 = st.columns([1, 1])
            
            with col_pie1:
                st.markdown("### Distribució per Segments")
                
                if usar_agrupacion:
                    # Modo agrupado: obtener el acumulado más reciente de cada combinación única POR EMPRESA
                    # Agrupa por: Empresa, TipoVinoBase, Zona, SubZona, Segmento
                    df_agrupado = obtener_acumulado_por_combinacion_unica(df_filtrado_fechas, ['Empresa', 'TipoVinoBase', 'Zona', 'SubZona', 'Segmento'])
                    
                    # Sumar por Segmento
                    segmentos_data = df_agrupado.groupby('Segmento')['Acumulado'].sum().reset_index()
                    

                else:
                    # Modo todos los registros: sumar directamente por segmento
                    segmentos_data = df_filtrado_fechas.groupby('Segmento')['Acumulado'].sum().reset_index()
                
                segmentos_data = segmentos_data.sort_values('Acumulado', ascending=False)
                
                # Crear gráfico de pastel
                fig_pie = go.Figure(data=[go.Pie(
                    labels=segmentos_data['Segmento'],
                    values=segmentos_data['Acumulado'],
                    hole=0.3,
                    marker=dict(colors=get_color_sequence(len(segmentos_data))),
                    textinfo='label+percent+value',
                    textposition='auto',
                    hovertemplate='<b>Segmento:</b> %{label}<br>' +
                                 '<b>Acumulado:</b> %{value:,.0f}<br>' +
                                 '<b>Porcentaje:</b> %{percent}<br>' +
                                 '<extra></extra>'
                )])
                
                fig_pie = apply_custom_style_to_fig(fig_pie)
                fig_pie.update_layout(
                    title="Acumulado por Segmentos",
                    height=400,
                    showlegend=True,
                    hoverlabel=dict(
                        bgcolor="white",
                        bordercolor=CUSTOM_PALETTE['600'],
                        font_size=12,
                        font_family="Arial"
                    )
                )
                
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col_pie2:
                st.markdown("### Mètriques per Segment")
                
                for idx, row in segmentos_data.iterrows():
                    porcentaje = (row['Acumulado'] / segmentos_data['Acumulado'].sum()) * 100
                    st.metric(
                        label=row['Segmento'],
                        value=f"{row['Acumulado']:,.0f}",
                        delta=f"{porcentaje:.1f}%"
                    )
            
            st.markdown("---")
            
            # 3. GRÁFICO PERSONALIZADO CON FILTROS
            st.markdown("### Temporal per Tipologia")
            
            # Filtros personalizados - Simplificados para mejor rendimiento
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            
            # Obtener valores únicos directamente del DataFrame filtrado por fechas
            tipos_vino_disponibles = ["Todos"] + sorted(df_filtrado_fechas['TipoVinoBase'].dropna().unique().tolist())
            segmentos_disponibles = ["Todos"] + sorted(df_filtrado_fechas['Segmento'].dropna().unique().tolist())
            zonas_disponibles = ["Todas"] + sorted(df_filtrado_fechas['Zona'].dropna().unique().tolist())
            subzonas_disponibles = ["Todas"] + sorted(df_filtrado_fechas['SubZona'].dropna().unique().tolist())

            with col_f1:
                tipo_vino_grafico = st.selectbox(
                    "Tipo Vino Base", 
                    tipos_vino_disponibles,
                    key="grafico_tipo_vino"
                )

            with col_f2:
                segmento_grafico = st.selectbox(
                    "Segmento", 
                    segmentos_disponibles,
                    key="grafico_segmento"
                )

            with col_f3:
                zona_grafico = st.selectbox(
                    "Zona", 
                    zonas_disponibles,
                    key="grafico_zona"
                )

            with col_f4:
                subzona_grafico = st.selectbox(
                    "SubZona", 
                    subzonas_disponibles,
                    key="grafico_subzona"
                )
            
            # Aplicar filtros al DataFrame filtrado por fechas
            df_grafico_personalizado = df_filtrado_fechas.copy()
            
            if tipo_vino_grafico != "Todos":
                df_grafico_personalizado = df_grafico_personalizado[df_grafico_personalizado["TipoVinoBase"] == tipo_vino_grafico]
            
            if segmento_grafico != "Todos":
                df_grafico_personalizado = df_grafico_personalizado[df_grafico_personalizado["Segmento"] == segmento_grafico]
            
            if zona_grafico != "Todas":
                df_grafico_personalizado = df_grafico_personalizado[df_grafico_personalizado["Zona"] == zona_grafico]
            
            if subzona_grafico != "Todas":
                df_grafico_personalizado = df_grafico_personalizado[df_grafico_personalizado["SubZona"] == subzona_grafico]
            
            # Aplicar el mismo modo de cálculo que "Acumulat Total Per Setmanes"
            if usar_agrupacion:
                # Modo agrupado: obtener el acumulado más reciente de cada combinación única
                # Agrupa por: Empresa, TipoVinoBase, Zona, SubZona, Segmento
                df_agrupado_personalizado = obtener_acumulado_por_combinacion_unica(
                    df_grafico_personalizado, 
                    ['Empresa', 'TipoVinoBase', 'Zona', 'SubZona', 'Segmento']
                )
                
                # Re-agregar la columna Semana basada en los datos originales
                fecha_semana_map = df_grafico_personalizado[['Fecha', 'Semana']].drop_duplicates().set_index('Fecha')['Semana'].to_dict()
                df_agrupado_personalizado['Semana'] = df_agrupado_personalizado['Fecha'].map(fecha_semana_map)
                
                # Sumar por Semana (suma de todas las combinaciones únicas en cada semana)
                personalizado_semanal = df_agrupado_personalizado.groupby('Semana')['Acumulado'].sum().reset_index()
            else:
                # Modo todos los registros: sumar directamente por semana
                personalizado_semanal = df_grafico_personalizado.groupby('Semana')['Acumulado'].sum().reset_index()
            
            # Verificar si hay datos y crear el gráfico
            if len(personalizado_semanal) > 0:
                personalizado_semanal = personalizado_semanal.sort_values('Semana')
                
                # Crear acumulado progresivo (cada punto suma al anterior)
                personalizado_semanal['Acumulado_Progresivo'] = personalizado_semanal['Acumulado'].cumsum()
                
                # Crear gráfico de líneas
                fig_personalizado = go.Figure()
                
                fig_personalizado.add_trace(go.Scatter(
                    x=personalizado_semanal['Semana'],
                    y=personalizado_semanal['Acumulado_Progresivo'],
                    mode='lines+markers',
                    name='Acumulado Filtrado',
                    line=dict(color=CUSTOM_PALETTE['700'], width=3),
                    marker=dict(size=8, color=CUSTOM_PALETTE['600']),
                    hovertemplate='<b>Semana:</b> %{x}<br>' +
                                 '<b>Acumulado Total:</b> %{y:,.0f}<br>' +
                                 '<extra></extra>'
                ))
                
                fig_personalizado = apply_custom_style_to_fig(fig_personalizado)
                fig_personalizado.update_layout(
                    title="Acumulat setmanal",
                    xaxis_title="Setmana",
                    yaxis_title="Acumulat",
                    height=400,
                    showlegend=True,
                    hovermode='x unified',
                    hoverlabel=dict(
                        bgcolor="white",
                        bordercolor=CUSTOM_PALETTE['600'],
                        font_size=12,
                        font_family="Arial"
                    )
                )
                
                st.plotly_chart(fig_personalizado, use_container_width=True)
                
                # Mostrar métricas del filtro
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric("Registros Filtrados", len(df_grafico_personalizado))
                with col_m2:
                    total_acumulat_metric = personalizado_semanal['Acumulado_Progresivo'].iloc[-1]
                    st.metric("Acumulat total", f"{total_acumulat_metric:,.0f}")
                with col_m3:
                    st.metric("Mitjana Setmanal", f"{personalizado_semanal['Acumulado'].mean():,.0f}")
            else:
                st.warning("⚠️ No hi ha dades amb els filtres seleccionats")
    
    else:
        st.info("📂 Procesa l'arxiu per veure els gràfics aquí")