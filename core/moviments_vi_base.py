import pandas as pd
import unicodedata
import re
import io
from typing import Tuple

# === Funciones auxiliares ===
def quitar_acentos_y_mayus(texto):
    """Quita acentos, pasa a mayúsculas y elimina espacios extremos"""
    if pd.isna(texto):
        return ""
    texto = unicodedata.normalize('NFKD', str(texto))
    texto = ''.join([c for c in texto if not unicodedata.combining(c)])
    return texto.upper().strip()

def limpiar_instalacion(texto):
    """Deja solo NOMBRE-MUNICIPIO en la columna Instalacion"""
    if pd.isna(texto):
        return ""
    partes = [p.strip() for p in str(texto).split("-") if p.strip()]
    if len(partes) >= 2:
        nombre = partes[0]
        municipio = partes[-1]  # tomar siempre el último bloque
        return f"{quitar_acentos_y_mayus(nombre)}-{quitar_acentos_y_mayus(municipio)}"
    return quitar_acentos_y_mayus(texto)

def limpiar_descripcion(texto):
    """Normaliza la columna Descripcion eliminando espacios y guiones sobrantes"""
    if pd.isna(texto):
        return ""
    texto = str(texto).strip()
    texto = re.sub(r"\s*-\s*", "-", texto)  # espacios alrededor de guiones
    if texto.startswith("-"):
        texto = texto[1:].strip()
    return quitar_acentos_y_mayus(texto)

def detectar_encabezados_y_cargar(file_bytes: bytes) -> pd.DataFrame:
    """Detecta si los encabezados están en fila 1 o fila 7 y carga el DataFrame"""
    try:
        # Probar primero con header=0 (fila 1)
        df_test = pd.read_excel(io.BytesIO(file_bytes), nrows=1)
        if "Instalacion" in df_test.columns:
            df = pd.read_excel(io.BytesIO(file_bytes), header=0)
        else:
            # Si no encuentra "Instalacion" en fila 1, usar fila 7 (header=6)
            df = pd.read_excel(io.BytesIO(file_bytes), header=6)
        return df
    except Exception as e:
        raise ValueError(f"❌ Error al leer el archivo: {e}")

def normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica normalización a las columnas Instalacion y Descripcion"""
    df_norm = df.copy()
    
    # Normalización columnas
    if "Instalacion" in df_norm.columns:
        df_norm["Instalacion"] = df_norm["Instalacion"].apply(limpiar_instalacion)
    
    if "Descripcion" in df_norm.columns:
        df_norm["Descripcion"] = df_norm["Descripcion"].apply(limpiar_descripcion)
    
    # Correcciones manuales puntuales
    df_norm["Instalacion"] = df_norm["Instalacion"].replace(
        {
            "CELLER JOSEP PINOL, S.L.-RUBI": "CELLER JOSEP PINOL, S.L.-FONT-RUBI",
            "U MES U FAN TRES, S.L.-RUBI": "U MES U FAN TRES, S.L.-FONT-RUBI"
        }
    )
    
    return df_norm

def normalizar_fecha(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza la columna Fecha a datetime"""
    df_fecha = df.copy()
    if "Fecha" in df_fecha.columns:
        df_fecha["Fecha"] = pd.to_datetime(df_fecha["Fecha"], errors="coerce", dayfirst=True)
    return df_fecha

def procesar_agrupacion(df: pd.DataFrame) -> pd.DataFrame:
    """Realiza la agrupación tomando el registro más reciente por grupo"""
    agrupacion = ["Instalacion", "TipoVinoBase", "Segmento", "Zona", "SubZona"]
    
    # Crear columna auxiliar con el orden original
    df_proc = df.copy()
    df_proc["RowOrder"] = df_proc.index
    
    # Ordenar por fecha descendente y RowOrder ascendente
    # → si hay empate de fechas, se queda con el primer registro del Excel
    df_sorted = df_proc.sort_values(by=["Fecha", "RowOrder"], ascending=[False, True])
    
    # Tomamos el registro más reciente (y en caso de empate, el primero del Excel)
    df_acumulado = df_sorted.groupby(agrupacion, as_index=False).first()
    
    # Eliminar columna auxiliar
    df_acumulado = df_acumulado.drop(columns=["RowOrder"], errors="ignore")
    
    # Ajustar formato de fecha dd/mm/aaaa
    df_acumulado["Fecha"] = df_acumulado["Fecha"].dt.strftime("%d/%m/%Y")
    
    # Selección final de columnas
    df_acumulado = df_acumulado[[
        "Fecha", "Empresa", "Instalacion", "TipoVinoBase",
        "Segmento", "Zona", "SubZona", "Acumulado"
    ]]
    
    return df_acumulado

def generar_excel_vi_base(df_acumulado: pd.DataFrame) -> bytes:
    """Genera el archivo Excel con los datos procesados"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_acumulado.to_excel(writer, sheet_name="Acumulado Vi Base", index=False)
    return output.getvalue()

def procesar_moviments_vi_base(file_bytes: bytes) -> Tuple[pd.DataFrame, bytes]:
    """Función principal que procesa el archivo completo y devuelve DataFrame y Excel"""
    # Detectar encabezados y cargar
    df = detectar_encabezados_y_cargar(file_bytes)
    
    # Normalizar columnas
    df = normalizar_columnas(df)
    
    # Normalizar fecha
    df = normalizar_fecha(df)
    
    # Procesar agrupación
    df_acumulado = procesar_agrupacion(df)
    
    # Generar Excel
    excel_bytes = generar_excel_vi_base(df_acumulado)
    
    return df_acumulado, excel_bytes