import streamlit as st

st.title("Cavanet • Próximamente")

st.markdown("""
Este módulo reutilizará los datos ya cargados de:

- Parcelas (df_parcelas_clean, df_final)
- IT04 (df_it04_aggr, df_rend_ajustado)

y pedirá el archivo **Cavanet** cuando corresponda. La arquitectura actual
permite añadir un flujo de procesamiento análogo al de RVC con:
- Normalización y filtros
- Cruces por VARTIP y parcela
- Reparto CAVA/PGC si aplica o reglas propias de Cavanet
- Exportación a Excel con las hojas requeridas

Cuando esté listo el formato definitivo de Cavanet, se implementará en `core/cavanet.py`
y se añadirá la exportación en `core/export.py`.
""")
