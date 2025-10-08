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

def filtrar_empresas_excluidas(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra y elimina registros de empresas específicas"""
    empresas_excluidas = ["2502-01", "2503-01", "2504-01", "4504-01", "4512-01"]
    
    df_filtrado = df.copy()
    
    # Buscar la columna que contiene la información de empresa
    # Puede estar en diferentes columnas dependiendo del archivo
    columnas_posibles = ["Empresa", "Codigo", "CodEmpresa", "Instalacion"]
    
    for columna in columnas_posibles:
        if columna in df_filtrado.columns:
            # Filtrar registros que NO estén en la lista de empresas excluidas
            mask = ~df_filtrado[columna].astype(str).isin(empresas_excluidas)
            df_filtrado = df_filtrado[mask]
            break
    
    return df_filtrado

def procesar_agrupacion(df: pd.DataFrame) -> pd.DataFrame:
    """Mantiene todos los registros sin agrupación - la lógica de agrupación se aplicará en los cálculos posteriores"""
    
    # Crear una copia del DataFrame sin modificaciones de agrupación
    df_resultado = df.copy()
    
    # Ajustar formato de fecha dd/mm/aaaa
    df_resultado["Fecha"] = df_resultado["Fecha"].dt.strftime("%d/%m/%Y")
    
    # Selección final de columnas
    df_resultado = df_resultado[[
        "Fecha", "Empresa", "Instalacion", "TipoVinoBase",
        "Segmento", "Zona", "SubZona", "Acumulado"
    ]]
    
    return df_resultado

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
    
    # Filtrar empresas excluidas
    df = filtrar_empresas_excluidas(df)
    
    # Procesar agrupación
    df_acumulado = procesar_agrupacion(df)
    
    # Generar Excel
    excel_bytes = generar_excel_vi_base(df_acumulado)
    
    return df_acumulado, excel_bytes