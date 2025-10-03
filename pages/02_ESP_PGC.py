# pages/02_Cavanet_Analyzer.py
# ============================================================
# Interfaz Streamlit para CAVANET 
# ============================================================

import streamlit as st
import pandas as pd

# Configurar layout wide permanente
st.set_page_config(
    page_title="ESP PGC",
    page_icon="🍇",
    layout="wide",
    initial_sidebar_state="expanded"
)

from core.cavanet import (
    RENDIMIENTO_POR_HECTAREA_DEFAULT,
    AGRUPAR_POR_EJERCICIO_DEFAULT,
    cargar_parcelas_desde_excel, procesar_parcelas, crear_dataframe_final_parcelas,
    cargar_it04_df, construir_rendimiento_ajustado,
    cargar_cavanet_desde_excel, procesar_cavanet,
    crear_vartip_cavanet, controlar_rendimientos_por_fecha,
    generar_resumenes_cavanet, build_excel_bytes_cavanet,
)

st.title("ESP PGC")

# Fallback defensivo por si el import de la constante cambiara en el futuro
_default_rend = float(RENDIMIENTO_POR_HECTAREA_DEFAULT) if 'RENDTIMIENTO_POR_HECTAREA_DEFAULT' in globals() \
    else float(RENDIMIENTO_POR_HECTAREA_DEFAULT)

with st.sidebar:
    st.subheader("Parámetros")
    rendimiento_ha = st.number_input(
        "Rendimiento por hectárea (kg/ha)",
        min_value=1.0, step=100.0,
        value=_default_rend
    )
    agrupar_por_ejercicio = st.checkbox(
        "Agrupar por Ejercicio",
        value=AGRUPAR_POR_EJERCICIO_DEFAULT
    )

st.markdown("### 1) Subir archivos")
col1, col2, col3 = st.columns(3)
with col1:
    f_parcelas = st.file_uploader("Parcelas (hoja 'Parcelas')", type=["xlsx", "xls"], key="cav_parcelas")
with col2:
    f_it04 = st.file_uploader("it04 (opc.)", type=["xlsx", "xls"], key="cav_it04")
with col3:
    f_cavanet = st.file_uploader("Cavanet", type=["xlsx", "xls"], key="cav_file")

procesar = st.button("Procesar CAVANET", type="primary")

if procesar:
    if not f_parcelas or not f_cavanet:
        st.error("Debes subir Parcelas y Cavanet.")
        st.stop()

    try:
        progress_cav = st.progress(5, text="Iniciando procesamiento CAVANET…")
        # --- Parcelas ---
        progress_cav.progress(20, text="Leyendo Parcelas…")
        df_parcelas = cargar_parcelas_desde_excel(f_parcelas.read())
        progress_cav.progress(35, text="Procesando Parcelas…")
        df_parcelas_clean = procesar_parcelas(df_parcelas)
        progress_cav.progress(50, text="Construyendo dataframe final de Parcelas…")
        df_final = crear_dataframe_final_parcelas(
            df_parcelas_clean,
            rendimiento_por_ha=rendimiento_ha,
            agrupar_por_ejercicio=agrupar_por_ejercicio
        )

        st.success(f"Parcelas OK — VARTIPs: {df_final['vartip'].nunique():,}")
        with st.expander("Parcelas (resumen)", expanded=False):
            st.dataframe(df_final.head(50), use_container_width=True)

        # --- IT04 ---
        progress_cav.progress(60, text="Aplicando ajustes IT04 (si hay)…")
        df_it04_aggr = cargar_it04_df(f_it04.read()) if f_it04 else None
        df_rend_ajustado, _ = construir_rendimiento_ajustado(df_final, df_it04_aggr)

        # --- Cavanet ---
        progress_cav.progress(70, text="Leyendo archivo Cavanet…")
        df_cav = cargar_cavanet_desde_excel(f_cavanet.read())
        progress_cav.progress(78, text="Limpiando Cavanet…")
        df_cav_clean = procesar_cavanet(df_cav)

        # Cruce y reparto
        progress_cav.progress(86, text="Cruzando con Parcelas y reparto por VARTIP…")
        df_cav_con_rend = crear_vartip_cavanet(df_cav_clean, df_final, df_parcelas_clean, df_rend_ajustado)
        if df_cav_con_rend.empty:
            st.warning("Tras los cruces (NIF + parcela + VARTIP) no quedan pesadas. Revisa normalizaciones y columnas.")
            st.stop()

        progress_cav.progress(90, text="Controlando rendimientos por fecha…")
        df_procesado = controlar_rendimientos_por_fecha(df_cav_con_rend)
        resumen_bodegas, resumen_vartips = generar_resumenes_cavanet(df_procesado)

        st.markdown("### 2) Resultados")
        tabs = st.tabs(["Pesadas procesadas", "Resumen bodegas", "Resumen VARTIPs"])
        with tabs[0]:
            st.dataframe(df_procesado.head(1000), use_container_width=True)
        with tabs[1]:
            st.dataframe(resumen_bodegas, use_container_width=True)
        with tabs[2]:
            st.dataframe(resumen_vartips, use_container_width=True)

        # --- Excel de salida (incluye VARTIP_Detalle y VARTIP_Detalle_ticket) ---
        progress_cav.progress(96, text="Generando Excel de resultados…")
        xls_bytes = build_excel_bytes_cavanet(
            df_procesado=df_procesado,
            resumen_bodegas=resumen_bodegas,
            resumen_vartips=resumen_vartips,
            df_rend_ajustado=df_rend_ajustado,
            df_it04_aggr=df_it04_aggr
        )
        st.download_button(
            "Descargar Excel resultados (CAVANET)",
            data=xls_bytes,
            file_name="analisis_pesadas_cavanet_resultados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        progress_cav.progress(100, text="Proceso completado.")
        st.success("Proceso completado.")

    except Exception as e:
        st.exception(e)
