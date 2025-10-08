# Configuración de paleta de colores personalizada
import plotly.graph_objects as go
import plotly.express as px

# Paleta de colores personalizada
CUSTOM_PALETTE = {
    '50': '#f8f8f8',
    '100': '#f0f0f0', 
    '200': '#e5e4e3',
    '300': '#d2d1cf',
    '400': '#b2b0ae',
    '500': '#9c9a97',
    '600': '#84817e',
    '700': '#6d6a68',
    '800': '#5c5a58',
    '900': '#4f4e4d',
    '950': '#282827'
}

# Lista de colores para gráficos (del más claro al más oscuro)
CHART_COLORS = [
    CUSTOM_PALETTE['300'],  # #d2d1cf
    CUSTOM_PALETTE['400'],  # #b2b0ae
    CUSTOM_PALETTE['500'],  # #9c9a97
    CUSTOM_PALETTE['600'],  # #84817e
    CUSTOM_PALETTE['700'],  # #6d6a68
    CUSTOM_PALETTE['800'],  # #5c5a58
    CUSTOM_PALETTE['900'],  # #4f4e4d
    CUSTOM_PALETTE['950'],  # #282827
]

# Colores específicos para diferentes tipos de gráficos
PRIMARY_COLOR = CUSTOM_PALETTE['600']  # #84817e
SECONDARY_COLOR = CUSTOM_PALETTE['400']  # #b2b0ae
ACCENT_COLOR = CUSTOM_PALETTE['800']  # #5c5a58
BACKGROUND_COLOR = CUSTOM_PALETTE['50']  # #f8f8f8
TEXT_COLOR = CUSTOM_PALETTE['900']  # #4f4e4d

def get_custom_plotly_template():
    """
    Retorna un template personalizado de Plotly con nuestra paleta de colores
    """
    template = go.layout.Template()
    
    # Configuración del layout
    template.layout = go.Layout(
        colorway=CHART_COLORS,
        plot_bgcolor=BACKGROUND_COLOR,
        paper_bgcolor='white',
        font=dict(
            color=TEXT_COLOR,
            family="Arial, sans-serif"
        ),
        title=dict(
            font=dict(
                color=TEXT_COLOR,
                size=16,
                family="Arial, sans-serif"
            )
        ),
        xaxis=dict(
            gridcolor=CUSTOM_PALETTE['200'],
            linecolor=CUSTOM_PALETTE['300'],
            tickcolor=CUSTOM_PALETTE['300'],
            title=dict(font=dict(color=TEXT_COLOR))
        ),
        yaxis=dict(
            gridcolor=CUSTOM_PALETTE['200'],
            linecolor=CUSTOM_PALETTE['300'],
            tickcolor=CUSTOM_PALETTE['300'],
            title=dict(font=dict(color=TEXT_COLOR))
        )
    )
    
    return template

def get_color_sequence(n_colors=None):
    """
    Retorna una secuencia de colores de nuestra paleta
    """
    if n_colors is None:
        return CHART_COLORS
    
    # Si necesitamos más colores de los que tenemos, repetimos la secuencia
    if n_colors > len(CHART_COLORS):
        multiplier = (n_colors // len(CHART_COLORS)) + 1
        extended_colors = CHART_COLORS * multiplier
        return extended_colors[:n_colors]
    
    return CHART_COLORS[:n_colors]

def apply_custom_style_to_fig(fig):
    """
    Aplica el estilo personalizado a una figura de Plotly
    """
    fig.update_layout(
        plot_bgcolor=BACKGROUND_COLOR,
        paper_bgcolor='white',
        font=dict(
            color=TEXT_COLOR,
            family="Arial, sans-serif"
        ),
        title=dict(
            font=dict(
                color=TEXT_COLOR,
                size=16,
                family="Arial, sans-serif"
            )
        ),
        xaxis=dict(
            gridcolor=CUSTOM_PALETTE['200'],
            linecolor=CUSTOM_PALETTE['300'],
            tickcolor=CUSTOM_PALETTE['300'],
            title=dict(font=dict(color=TEXT_COLOR))
        ),
        yaxis=dict(
            gridcolor=CUSTOM_PALETTE['200'],
            linecolor=CUSTOM_PALETTE['300'],
            tickcolor=CUSTOM_PALETTE['300'],
            title=dict(font=dict(color=TEXT_COLOR))
        )
    )
    return fig