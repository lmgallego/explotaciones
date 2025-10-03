"""
Módulo para generar iconos SVG vectoriales personalizados
"""

def get_svg_icon(icon_name: str, size: int = 24, stroke_color: str = "#84817e", fill: str = "none", stroke_width: int = 2) -> str:
    """
    Genera iconos SVG vectoriales personalizados
    
    Args:
        icon_name: Nombre del icono
        size: Tamaño del icono en píxeles
        stroke_color: Color del contorno
        fill: Color de relleno
        stroke_width: Grosor del contorno
    
    Returns:
        String con el código SVG del icono
    """
    
    icons = {
        "globe": f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}" stroke="{stroke_color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="2" y1="12" x2="22" y2="12"/>
            <path d="m12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
        </svg>
        """,
        
        "map_pin": f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}" stroke="{stroke_color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
            <circle cx="12" cy="10" r="3"/>
        </svg>
        """,
        
        "heart": f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}" stroke="{stroke_color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
        </svg>
        """,
        
        "mail": f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}" stroke="{stroke_color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
            <polyline points="22,6 12,13 2,6"/>
        </svg>
        """,
        
        "play": f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}" stroke="{stroke_color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
            <polygon points="10,8.5 16,12 10,15.5"/>
        </svg>
        """,
        
        "camera": f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}" stroke="{stroke_color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
            <circle cx="12" cy="10" r="3"/>
        </svg>
        """,
        
        "instagram": f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}" stroke="{stroke_color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="2" width="20" height="20" rx="5" ry="5"/>
            <path d="m16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/>
            <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/>
        </svg>
        """,
        
        "location": f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}" stroke="{stroke_color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="10" r="3"/>
            <path d="m12 21.7-6.3-6.3a9 9 0 1 1 12.6 0L12 21.7z"/>
        </svg>
        """,
        
        "database": f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}" stroke="{stroke_color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">
            <ellipse cx="12" cy="5" rx="9" ry="3"/>
            <path d="m3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5"/>
            <path d="m3 12c0 1.66 4.03 3 9 3s9-1.34 9-3"/>
        </svg>
        """,
        
        "chart": f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}" stroke="{stroke_color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="20" x2="18" y2="10"/>
            <line x1="12" y1="20" x2="12" y2="4"/>
            <line x1="6" y1="20" x2="6" y2="14"/>
        </svg>
        """,
        
        "file": f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}" stroke="{stroke_color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
            <polyline points="14,2 14,8 20,8"/>
        </svg>
        """,
        
        "download": f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}" stroke="{stroke_color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7,10 12,15 17,10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        """
    }
    
    return icons.get(icon_name, icons["file"])  # Retorna icono de archivo por defecto


def display_icon_grid(icons_list: list, cols: int = 4, size: int = 48):
    """
    Muestra una grilla de iconos en Streamlit
    
    Args:
        icons_list: Lista de nombres de iconos
        cols: Número de columnas
        size: Tamaño de los iconos
    """
    import streamlit as st
    
    # Crear columnas
    columns = st.columns(cols)
    
    for i, icon_name in enumerate(icons_list):
        col_index = i % cols
        with columns[col_index]:
            icon_svg = get_svg_icon(icon_name, size=size)
            st.html(f"""
            <div style="text-align: center; padding: 10px;">
                {icon_svg}
                <p style="margin-top: 5px; font-size: 12px; color: #84817e;">{icon_name}</p>
            </div>
            """)


def create_icon_button(icon_name: str, text: str, size: int = 20) -> str:
    """
    Crea un botón con icono SVG
    
    Args:
        icon_name: Nombre del icono
        text: Texto del botón
        size: Tamaño del icono
    
    Returns:
        HTML del botón con icono
    """
    icon_svg = get_svg_icon(icon_name, size=size)
    
    return f"""
    <div style="
        display: inline-flex; 
        align-items: center; 
        gap: 8px; 
        padding: 8px 16px; 
        border: 1px solid #84817e; 
        border-radius: 6px; 
        background: white; 
        cursor: pointer;
        transition: all 0.2s ease;
    " onmouseover="this.style.backgroundColor='#f5f5f5'" onmouseout="this.style.backgroundColor='white'">
        {icon_svg}
        <span style="color: #84817e; font-weight: 500;">{text}</span>
    </div>
    """