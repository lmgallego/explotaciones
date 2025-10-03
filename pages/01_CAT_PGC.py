import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# Configurar layout wide permanente
st.set_page_config(
    page_title="CAT PGC",
    page_icon="🍇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constante con fallback limpio (10500 si no se pudiera importar)
try:
    from core.utils import RENDIMIENTO_POR_HECTAREA_DEFAULT
except Exception:
    RENDIMIENTO_POR_HECTAREA_DEFAULT = 10500

from core.parcelas import procesar_parcelas, crear_dataframe_final
from core.it04 import cargar_it04, construir_rendimiento_ajustado
from core.rvc import (
    procesar_rvc, crear_vartip_rvc, controlar_rendimientos,
    generar_resumenes, construir_hojas_salida
)
from core.export import exportar_excel_parcelas, exportar_excel_rvc


st.title("CAT PGC")

# -----------------------------
# Parámetros (sidebar)
# -----------------------------
with st.sidebar:
    st.header("Parámetros")
    rendimiento_ha = st.number_input(
        "Rendimiento por hectárea (kg/ha)",
        min_value=1.0,
        step=100.0,
        value=float(RENDIMIENTO_POR_HECTAREA_DEFAULT)
    )
    agrupar_ejercicio = st.checkbox("Agrupar Parcelas por ejercicio", value=True)

# -----------------------------
# 1) Parcelas
# -----------------------------
st.subheader("1) Parcelas")

col1, col2 = st.columns([1, 1])
with col1:
    f_parcelas = st.file_uploader(
        "Subir archivo de Parcelas",
        type=["xlsx", "xls"],
        key="parcelas_upl"
    )
with col2:
    if "df_parcelas_clean" in st.session_state:
        st.success("Parcelas ya cargado desde sesión.")
    else:
        st.info("No hay Parcelas en sesión.")

process_parcelas = st.button("Procesar Parcelas", type="primary")

if process_parcelas:
    if f_parcelas is None:
        st.error("Debe subir el archivo de Parcelas.")
    else:
        progress_parc = st.progress(5, text="Iniciando procesamiento de Parcelas…")
        # Igual que en Colab: detección de cabecera desplazada
        xls = pd.ExcelFile(f_parcelas)
        sheet_name = "Parcelas" if "Parcelas" in xls.sheet_names else xls.sheet_names[0]
        progress_parc.progress(20, text="Leyendo hoja de Parcelas…")

        # Primer intento: encabezados en la primera fila
        dfp_try = xls.parse(sheet_name=sheet_name, nrows=10)
        columnas_esperadas = [
            'Ejercicio','RefParcela','NRegistro','NIF','Apellidos','Nombre',
            'Variedad','Superficie','PorcentajeTitularidad','Estado','Segmento'
        ]
        # Normalizamos para comparar
        from core.utils import norm_text
        cols_norm = [norm_text(c) for c in dfp_try.columns]
        esper_norm = [norm_text(c) for c in columnas_esperadas]
        coincidencias = sum(1 for col in esper_norm if col in cols_norm)

        progress_parc.progress(35, text="Analizando cabeceras…")
        if coincidencias < 4:
            # Cabecera en fila 7 (saltando metadata), igual que en Colab
            dfp = xls.parse(sheet_name=sheet_name, skiprows=6)
        else:
            dfp = xls.parse(sheet_name=sheet_name)

        progress_parc.progress(55, text="Procesando Parcelas…")
        # Procesado y dataframe final
        from core.parcelas import procesar_parcelas, crear_dataframe_final  # aseguramos la versión nueva
        df_parcelas_clean = procesar_parcelas(dfp)

        progress_parc.progress(75, text="Construyendo dataframe final…")
        df_final = crear_dataframe_final(
            df_parcelas_clean,
            rendimiento_ha,
            agrupar_por_ejercicio=agrupar_ejercicio
        )

        # Guardar en sesión
        st.session_state["df_parcelas_clean"] = df_parcelas_clean
        st.session_state["df_final"] = df_final

        # Export Parcels
        from core.export import exportar_excel_parcelas
        progress_parc.progress(90, text="Generando Excel de Parcelas…")
        bin_parcelas = exportar_excel_parcelas(df_final, df_parcelas_clean)
        st.download_button(
            "Descargar dataframe_final.xlsx",
            data=bin_parcelas,
            file_name="dataframe_final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        progress_parc.progress(100, text="Parcelas procesadas.")

        # Preview
        from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
        st.markdown("**Vista rápida de `dataframe_final`**")
        gob = GridOptionsBuilder.from_dataframe(df_final)
        gob.configure_default_column(resizable=True, filter=True, sortable=True)
        AgGrid(df_final, gridOptions=gob.build(),
               update_mode=GridUpdateMode.NO_UPDATE, height=300)


st.divider()

# -----------------------------
# 2) IT04
# -----------------------------
st.subheader("2) IT04")

col3, col4 = st.columns([1, 1])
with col3:
    f_it04 = st.file_uploader(
        "Suba el archivo it04",
        type=["xlsx", "xls", "csv"],
        key="it04_upl"
    )
with col4:
    if "df_rend_ajustado" in st.session_state:
        st.success("Ajustes IT04 ya calculados.")

apply_it04 = st.button("Aplicar ajustes IT04", type="primary")

if apply_it04:
    if "df_final" not in st.session_state:
        st.error("Debe procesar Parcelas antes de aplicar IT04.")
    else:
        progress_it04 = st.progress(5, text="Preparando ajustes IT04…")
        if f_it04 is None:
            # Sin archivo it04: ajustes nulos
            df_it04_aggr = pd.DataFrame(columns=["vartip", "kg_a_restar_total"])
        else:
            progress_it04.progress(25, text="Leyendo archivo IT04…")
            if f_it04.name.lower().endswith(".csv"):
                df_i = pd.read_csv(f_it04)
            else:
                df_i = pd.read_excel(f_it04)
            df_it04_aggr = cargar_it04(df_i)
        progress_it04.progress(65, text="Construyendo rendimiento ajustado…")
        df_rend_ajustado = construir_rendimiento_ajustado(
            st.session_state["df_final"],
            df_it04_aggr
        )
        st.session_state["df_it04_aggr"] = df_it04_aggr
        st.session_state["df_rend_ajustado"] = df_rend_ajustado

        st.markdown("**Vista rápida de ajustes (IT04_Ajustes)**")
        gob = GridOptionsBuilder.from_dataframe(df_rend_ajustado)
        gob.configure_default_column(resizable=True, filter=True, sortable=True)
        AgGrid(df_rend_ajustado, gridOptions=gob.build(),
               update_mode=GridUpdateMode.NO_UPDATE, height=280)
        progress_it04.progress(100, text="Ajustes IT04 aplicados.")

st.divider()

# -----------------------------
# 3) RVC
# -----------------------------
st.subheader("3) RVC")

f_rvc = st.file_uploader(
    "Suba el archivo RVC",
    type=["xlsx", "xls", "csv"],
    key="rvc_upl"
)
run_rvc = st.button("Ejecutar análisis RVC", type="primary")

if run_rvc:
    # Precondiciones
    if "df_parcelas_clean" not in st.session_state or "df_final" not in st.session_state:
        st.error("Debe procesar Parcelas primero.")
    else:
        progress_rvc = st.progress(5, text="Iniciando análisis RVC…")
        # IT04 opcional: si no hay, construimos sin ajuste
        if "df_rend_ajustado" not in st.session_state:
            df_rend_ajustado = construir_rendimiento_ajustado(
                st.session_state["df_final"],
                pd.DataFrame(columns=["vartip", "kg_a_restar_total"])
            )
            st.session_state["df_rend_ajustado"] = df_rend_ajustado

        if f_rvc is None:
            st.error("Debe subir un archivo RVC.")
        else:
            progress_rvc.progress(20, text="Leyendo archivo RVC…")
            if f_rvc.name.lower().endswith(".csv"):
                df_r = pd.read_csv(f_rvc)
            else:
                df_r = pd.read_excel(f_rvc)

            progress_rvc.progress(40, text="Limpiando RVC…")
            # Procesado RVC y cruce con Parcelas + IT04
            df_rvc_clean = procesar_rvc(df_r)

            progress_rvc.progress(60, text="Cruzando con Parcelas e IT04…")
            df_rvc_con_rend = crear_vartip_rvc(
                df_rvc_clean,
                st.session_state["df_final"],
                st.session_state["df_parcelas_clean"],
                st.session_state["df_rend_ajustado"]
            )
            progress_rvc.progress(75, text="Controlando rendimientos…")
            df_procesado = controlar_rendimientos(df_rvc_con_rend)

            progress_rvc.progress(85, text="Generando resúmenes y hojas…")
            resumen_cellers, resumen_vartips = generar_resumenes(df_procesado)
            hojas = construir_hojas_salida(df_procesado, resumen_cellers, resumen_vartips)

            # Guardar en sesión
            st.session_state["df_rvc_clean"] = df_rvc_clean
            st.session_state["df_procesado"] = df_procesado
            st.session_state["resumen_cellers"] = resumen_cellers
            st.session_state["resumen_vartips"] = resumen_vartips
            st.session_state["hojas_rvc"] = hojas

            progress_rvc.progress(92, text="Generando Excel de resultados…")
            # Descarga Excel RVC
            with st.spinner("Generando Excel de resultados…"):
                bin_rvc = exportar_excel_rvc(
                    hojas,
                    df_rend_ajustado=st.session_state["df_rend_ajustado"],
                    df_it04_aggr=st.session_state.get("df_it04_aggr")
                )
            st.download_button(
                "Descargar analisis_pesadas_rvc_resultados.xlsx",
                data=bin_rvc,
                file_name="analisis_pesadas_rvc_resultados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # Vistas rápidas
            st.markdown("**Resumen_Cellers**")
            gob = GridOptionsBuilder.from_dataframe(resumen_cellers)
            gob.configure_default_column(resizable=True, filter=True, sortable=True)
            AgGrid(resumen_cellers, gridOptions=gob.build(),
                   update_mode=GridUpdateMode.NO_UPDATE, height=260)

            st.markdown("**Resumen_VARTIPs**")
            gob = GridOptionsBuilder.from_dataframe(resumen_vartips)
            gob.configure_default_column(resizable=True, filter=True, sortable=True)
            AgGrid(resumen_vartips, gridOptions=gob.build(),
                   update_mode=GridUpdateMode.NO_UPDATE, height=260)

            st.markdown("**VARTIP_Detalle**")
            df_vt = hojas["VARTIP_Detalle"]
            gob = GridOptionsBuilder.from_dataframe(df_vt)
            gob.configure_default_column(resizable=True, filter=True, sortable=True)
            AgGrid(df_vt, gridOptions=gob.build(),
                   update_mode=GridUpdateMode.NO_UPDATE, height=420)

            progress_rvc.progress(100, text="Análisis RVC completado.")


