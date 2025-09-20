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

st.sidebar.title("Análisis Control PGC")
st.sidebar.markdown("Seleccione una aplicación en el menú de páginas.")
st.title("Centro de Análisis • CAVA / PGC")

st.markdown(
    """
Esta aplicación permite:
- Preparar **Parcelas** y calcular rendimientos por **VARTIP**.
- Aplicar **ajustes IT04** (kg a restar por VARTIP).
- Analizar **RVC** y repartir **CAVA/PGC**, con exportación a Excel.
- Base preparada para **Cavanet** (página placeholder).
    
Use el menú de la izquierda para navegar por cada módulo.
""")
