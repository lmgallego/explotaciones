import pandas as pd
import numpy as np
from .utils import (
    norm_text, norm_segmento, norm_variedad, norm_nif, norm_refparcela,
    to_numeric_safe, codigo_variedad_from_name, crear_diccionario_variedades,
    find_col, find_col_by_terms
)

def _pick_superficie_col(df: pd.DataFrame) -> str | None:
    """
    Busca una columna de 'Superficie' de forma robusta (insensible a acentos y variantes).
    Prioriza nombres más específicos si hay varias coincidencias.
    """
    # 1) candidatos directos más comunes
    direct_candidates = [
        'Superficie', 'Superfície', 'superficie',
        'Superficie (ha)', 'Superfície (ha)',
        'Sup', 'sup', 'Sup (ha)', 'sup (ha)',
        'Hectáreas', 'Hectareas', 'Hectárea', 'Hectarea',
        'ha', 'HA'
    ]
    col = find_col(df, direct_candidates)
    if col:
        return col

    # 2) por términos contenidos
    #   - primero SUPERFIC, luego HECTA
    for terms in (['SUPERFIC'], ['HECTA'], ['HA']):
        col = find_col_by_terms(df, terms)
        if col:
            return col

    return None


def procesar_parcelas(df: pd.DataFrame) -> pd.DataFrame:
    df_clean = df.copy()

    # ---- Detección y renombrado de columnas (robusto) ----
    # Usamos find_col (insensible a acentos/case) y, si hace falta, find_col_by_terms (por fragmentos)
    # Para cada clave lógica, intentamos varios alias.

    # NIF
    col_nif = find_col(df_clean, ['NIF', 'nif'])
    if col_nif:
        df_clean.rename(columns={col_nif: 'NIF'}, inplace=True)

    # Variedad
    col_var = find_col(df_clean, ['Variedad', 'variedad', 'Varietat', 'varietat'])
    if col_var:
        df_clean.rename(columns={col_var: 'Variedad'}, inplace=True)

    # RefParcela
    col_refp = find_col(df_clean, [
        'RefParcela', 'refparcela', 'Ref_Parcela', 'Ref Parcela', 'Ref parcela',
        'origenParcela', 'origenParcella'
    ]) or find_col_by_terms(df_clean, ['PARCEL'])
    if col_refp:
        df_clean.rename(columns={col_refp: 'RefParcela'}, inplace=True)

    # Superficie (robusta)
    col_sup = _pick_superficie_col(df_clean)
    if col_sup:
        df_clean.rename(columns={col_sup: 'Superficie'}, inplace=True)

    # Segmento
    col_seg = find_col(df_clean, ['Segmento', 'segmento'])
    if col_seg:
        df_clean.rename(columns={col_seg: 'Segmento'}, inplace=True)

    # Nombre / Apellidos
    col_nom = find_col(df_clean, ['Nombre', 'nombre'])
    if col_nom:
        df_clean.rename(columns={col_nom: 'Nombre'}, inplace=True)
    col_ape = find_col(df_clean, ['Apellidos', 'apellidos'])
    if col_ape:
        df_clean.rename(columns={col_ape: 'Apellidos'}, inplace=True)

    # Ejercicio
    col_ej = find_col(df_clean, ['Ejercicio', 'ejercicio', 'Any', 'Año', 'ano', 'Ano'])
    if col_ej:
        df_clean.rename(columns={col_ej: 'Ejercicio'}, inplace=True)

    # PorcentajeTitularidad
    col_tit = find_col(df_clean, [
        'PorcentajeTitularidad', 'porcentajetitularidad', 'Porcentaje Titularidad', 'PorcTitularidad'
    ])
    if col_tit:
        df_clean.rename(columns={col_tit: 'PorcentajeTitularidad'}, inplace=True)

    # NRegistro
    col_reg = find_col(df_clean, ['NRegistro', 'Nº Registro', 'NºRegistro', 'NumRegistro'])
    if col_reg:
        df_clean.rename(columns={col_reg: 'NRegistro'}, inplace=True)

    # Estado
    col_est = find_col(df_clean, ['Estado', 'estado', 'Estat', 'estat', 'Status'])
    if col_est:
        df_clean.rename(columns={col_est: 'Estado'}, inplace=True)

    # ---- Filtros: Segmento = GUARDA (excluye Guarda Superior implícitamente) ----
    if 'Segmento' in df_clean.columns:
        df_clean['Segmento'] = df_clean['Segmento'].astype(str).map(norm_segmento)
        before = len(df_clean)
        df_clean = df_clean[df_clean['Segmento'] == 'GUARDA']
        # print(f"Filtro Segmento=GUARDA: {before} → {len(df_clean)}")

    # ---- Filtro: Estado = VALIDADA ----
    if 'Estado' in df_clean.columns:
        before = len(df_clean)
        df_clean['Estado'] = df_clean['Estado'].astype(str).map(norm_text)
        df_clean = df_clean[df_clean['Estado'] == 'VALIDADA']
        # print(f"Filtro Estado=VALIDADA: {before} → {len(df_clean)}")

    # ---- NIF ----
    if 'NIF' in df_clean.columns:
        df_clean['NIF'] = df_clean['NIF'].map(norm_nif)
        df_clean = df_clean[df_clean['NIF'] != ""]
    else:
        # No abortamos, pero sin NIF no habrá VARTIP válido
        pass

    # ---- Variedad ----
    if 'Variedad' in df_clean.columns:
        df_clean['Variedad'] = df_clean['Variedad'].map(norm_variedad)

    # ---- Superficie -> numérico ----
    if 'Superficie' in df_clean.columns:
        df_clean['Superficie'] = df_clean['Superficie'].map(to_numeric_safe)
        df_clean = df_clean.dropna(subset=['Superficie'])
    else:
        # Aquí estaba tu error; ahora damos un mensaje claro y listamos columnas detectadas.
        cols_dbg = ", ".join(df_clean.columns.astype(str))
        raise ValueError(
            "Falta columna de superficie en Parcelas. "
            "Intenta renombrar tu columna a 'Superficie' o alguna variante como "
            "'Superfície', 'Hectáreas', 'ha', 'Sup'. "
            f"Columnas disponibles: {cols_dbg}"
        )

    # ---- PorcentajeTitularidad -> superficie_efectiva ----
    if 'PorcentajeTitularidad' in df_clean.columns:
        df_clean['PorcentajeTitularidad'] = pd.to_numeric(df_clean['PorcentajeTitularidad'], errors='coerce').fillna(100)
        df_clean['PorcentajeTitularidad'] = df_clean['PorcentajeTitularidad'].clip(0, 100)
        df_clean['superficie_efectiva'] = df_clean['Superficie'] * (df_clean['PorcentajeTitularidad'] / 100.0)
    else:
        df_clean['superficie_efectiva'] = df_clean['Superficie']

    # ---- Nombre completo ----
    if 'Nombre' in df_clean.columns and 'Apellidos' in df_clean.columns:
        df_clean['nombre_completo'] = (
            df_clean['Nombre'].astype(str).str.strip() + ' ' + df_clean['Apellidos'].astype(str).str.strip()
        ).str.strip()
    else:
        df_clean['nombre_completo'] = 'N/A'

    # ---- Código variedad + VARTIP ----
    dict_var = crear_diccionario_variedades()
    if 'Variedad' in df_clean.columns:
        df_clean['codigo_variedad'] = df_clean['Variedad'].map(lambda s: dict_var.get(s, codigo_variedad_from_name(s)))
    else:
        df_clean['codigo_variedad'] = 'UNK'

    if 'NIF' in df_clean.columns:
        df_clean['vartip'] = df_clean['codigo_variedad'].astype(str) + '-' + df_clean['NIF'].astype(str)
    else:
        df_clean['vartip'] = df_clean['codigo_variedad'].astype(str) + '-'

    # ---- RefParcela normalizada ----
    if 'RefParcela' in df_clean.columns:
        df_clean['RefParcela_norm'] = df_clean['RefParcela'].map(norm_refparcela)
    else:
        df_clean['RefParcela_norm'] = ""

    # ---- Ejercicio a Int64 si posible ----
    if 'Ejercicio' in df_clean.columns:
        ej_num = pd.to_numeric(df_clean['Ejercicio'], errors='coerce')
        df_clean['Ejercicio'] = np.where(ej_num.notna(), ej_num.astype('Int64'), df_clean['Ejercicio'].astype(str))

    return df_clean


def crear_dataframe_final(df_clean: pd.DataFrame, rendimiento_ha: float, agrupar_por_ejercicio: bool = True) -> pd.DataFrame:
    if agrupar_por_ejercicio and ('Ejercicio' in df_clean.columns):
        clave = ['Ejercicio', 'vartip']
    else:
        clave = ['vartip']

    hectareas_por_vartip = (
        df_clean.groupby(clave, dropna=False)['superficie_efectiva']
        .sum()
        .reset_index()
        .rename(columns={'superficie_efectiva': 'hectareas_variedad'})
    )

    agg_dict = {
        'NIF': 'first',
        'nombre_completo': 'first',
        'Segmento': 'first',
        'Variedad': 'first',
        'codigo_variedad': 'first'
    }

    df_final = (
        df_clean.groupby(clave, dropna=False)
        .agg(agg_dict)
        .reset_index()
        .merge(hectareas_por_vartip, on=clave, how='left')
    )

    df_final['rendimiento'] = df_final['hectareas_variedad'] * float(rendimiento_ha)

    rename_map = {'NIF': 'nif', 'nombre_completo': 'nombre', 'Segmento': 'segmento'}
    if 'Ejercicio' in df_final.columns:
        rename_map['Ejercicio'] = 'ejercicio'
    df_final = df_final.rename(columns=rename_map)

    columnas_finales = (['ejercicio'] if 'ejercicio' in df_final.columns else []) + \
                       ['nif', 'nombre', 'vartip', 'segmento', 'hectareas_variedad', 'rendimiento']
    df_final = df_final[columnas_finales]
    df_final['hectareas_variedad'] = df_final['hectareas_variedad'].astype(float).round(4)
    df_final['rendimiento'] = df_final['rendimiento'].astype(float).round(2)

    sort_cols = (['ejercicio', 'rendimiento'] if 'ejercicio' in df_final.columns else ['rendimiento'])
    df_final = df_final.sort_values(sort_cols, ascending=[True, False] if 'ejercicio' in df_final.columns else [False]).reset_index(drop=True)
    return df_final

