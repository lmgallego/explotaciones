import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Control PGC",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Cargar estilo
with open(Path("assets/styles.css"), "r") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.sidebar.title("Control PGC")
st.sidebar.markdown("Seleccione una aplicación en el menú de páginas.")
st.title("Control PGC")

st.markdown(
    """
Esta aplicación permite:
- Preparar **Parcelas** y calcular rendimientos por **VARTIP**.
- Aplicar **ajustes IT04**.
- Análisis RVC y Cavanet.

    

""")
