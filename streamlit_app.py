import streamlit as st

# Configurar layout wide permanente
st.set_page_config(
    page_title="Control PGC",
    page_icon="🍇",
    layout="wide",
    initial_sidebar_state="expanded"
)
from pathlib import Path
from core.icons import get_svg_icon

# Configuración de página - DEBE ser lo primero
st.set_page_config(
    page_title="Control PGC",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cargar CSS personalizado
def load_css():
    with open('assets/styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# Sidebar (sin contenido adicional)

st.title("D.O.  C A V A ")

home_icon = get_svg_icon("globe", size=24)
st.html(f"""
<div class="card">
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
        {home_icon}
        <h2 style="margin: 0;">Sistema  de Gestió PGC / Moviments Vi Base</h2>
    </div>
    <p class="subtitle">Gestió i Control PGC i Moviments de Vi Base</p>
</div>
""")

st.markdown("---")

# Información de las aplicaciones disponibles
col1, col2, col3 = st.columns(3)

with col1:
    database_icon = get_svg_icon("database", size=32)
    st.html(f"""
    <div class="card">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
            {database_icon}
            <h3 style="margin: 0;">CONTROL PGC CATALUNYA</h3>
        </div>
        <p class="subtitle">Dades actuals situació PGC Catalunya</p>
        <ul>
            <li>Rendiment parcel.les</li>
            <li>IT04</li>
            <li>Gestió PGC-RVC</li>
        </ul>
    </div>
    """)
    
    # Botón centrado usando st.button nativo
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("🔗 Accedeix", key="btn_cat_pgc", type="primary", use_container_width=True):
            st.switch_page("pages/01_CAT_PGC.py")

with col2:
    chart_icon = get_svg_icon("chart", size=32)
    st.html(f"""
    <div class="card">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
            {chart_icon}
            <h3 style="margin: 0;">CONTROL PGC ESPANYA</h3>
        </div>
        <p class="subtitle">Dades actuals situació PGC Espanya</p>
        <ul>
            <li>Rendiment parcel.les</strong></li>
            <li>IT04</li>
            <li>Gestió PGC-CAVANET</li>
        </ul>
    </div>
    """)
    
    # Botón centrado usando st.button nativo
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("🔗 Accedeix", key="btn_esp_pgc", type="primary", use_container_width=True):
            st.switch_page("pages/02_ESP_PGC.py")

with col3:
    file_icon = get_svg_icon("file", size=32)
    chart_small_icon = get_svg_icon("chart", size=20)
    st.html(f"""
    <div class="card">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
            {file_icon}
            <div style="display: flex; align-items: center; gap: 5px;">
                {chart_small_icon}
                <h3 style="margin: 0;">GESTIÓ VI BASE</h3>
            </div>
        </div>
        <p class="subtitle">Gestió Moviments Vi Base</p>
        <ul>
            <li>Processament CAVANET</li>
            <li>Filtrat per Tipus</li>
            <li>Visualitzacions</li>
        </ul>
    </div>
    """)
    
    # Botón centrado usando st.button nativo
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("🔗 Accedeix", key="btn_moviments", type="primary", use_container_width=True):
            st.switch_page("pages/03_MOVIMENTS_VI_BASE.py")

st.markdown("---")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #4F4E4D; font-size: 0.9rem;">
    <p>Sistema Control PGC - Versión 2024</p>
</div>
""", unsafe_allow_html=True)
