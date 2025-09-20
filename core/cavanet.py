# core/cavanet.py
# ============================================================
# CAVANET (Parcelas + IT04 + Cavanet)
# - Misma lógica que tu Colab (detección de cabecera desplazada,
#   triple cruce y reparto CAVA/PGC), más hoja VARTIP_Detalle_ticket.
# - No toca nada de módulos existentes.
# - Devuelve DataFrames y un binario Excel listo para descargar.
# ============================================================

from __future__ import annotations
import io, re, unicodedata
from typing import Optional, Tuple, List, Dict

import numpy as np
import pandas as pd


# --------------------------
# Config por defecto
# --------------------------
RENDIMIENTO_POR_HECTAREA_DEFAULT = 10500
AGRUPAR_POR_EJERCICIO_DEFAULT = True


# --------------------------
# Utilidades internas
# --------------------------
def _strip_accents(s: str) -> str:
    if pd.isna(s):
        return ""
    s = str(s)
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

def _norm_text(s: str) -> str:
    return _strip_accents(s).strip().upper()

def _norm_segmento(s: str) -> str:
    s = _norm_text(s)
    return re.sub(r"\s+", " ", s)

def _norm_variedad(s: str) -> str:
    s = _norm_text(s)
    s = s.replace("XAREL.LO", "XARELLO").replace("XAREL·LO", "XARELLO").replace("PINOT-NOIR", "PINOT NOIR")
    return s

def _norm_nif(x) -> str:
    if pd.isna(x):
        return ""
    s = str(x).strip()
    if re.fullmatch(r"\d+\.0", s):
        s = s[:-2]
    s = s.replace(",", "").replace(" ", "")
    s = re.sub(r"[^0-9A-Za-z]", "", s)
    return s.upper()

def _norm_refparcela(x) -> str:
    if pd.isna(x):
        return ""
    s = str(x).strip().upper()
    # Para robustez en el cruce, dejamos solo A-Z y dígitos
    s = re.sub(r"[^0-9A-Z]", "", s)
    return s

def _to_numeric_safe(x):
    if isinstance(x, str):
        x = x.replace(",", ".")
    return pd.to_numeric(x, errors="coerce")

def _codigo_variedad_from_name(var_name: str) -> str:
    s = _norm_variedad(var_name)
    s = re.sub(r"[^A-Z]", "", s)
    if not s:
        return "UNK"
    return (s[:3] if len(s) >= 3 else s).upper()

def _find_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    norm_map = {col: _norm_text(col) for col in df.columns}
    targets = [_norm_text(c) for c in candidates]
    for col, ncol in norm_map.items():
        if ncol in targets:
            return col
    for t in targets:
        for col, ncol in norm_map.items():
            if t in ncol:
                return col
    return None

def _find_col_by_terms(df: pd.DataFrame, must_have_terms: List[str]) -> Optional[str]:
    norm_map = {col: _norm_text(col) for col in df.columns}
    for col, ncol in norm_map.items():
        if all(term in ncol for term in must_have_terms):
            return col
    return None

def crear_diccionario_variedades() -> Dict[str, str]:
    base = {
        'CHARDONNAY': 'CHB', 'GARNATXA NEGRA': 'GAN', 'MACABEU': 'MAB',
        'MONASTRELL': 'MTN', 'PARELLADA': 'PAB', 'PINOT NOIR': 'PTN',
        'SUBIRAT PARENT': 'SPB', 'TREPAT': 'TRN', 'XARELLO': 'XAB',
    }
    return { _norm_variedad(k): v for k, v in base.items() }

def _codigo_variedad_robusto(nombre: str) -> str:
    base = _norm_variedad(nombre)
    base = re.sub(r"[^A-Z ]", " ", base)
    base = re.sub(r"\s+", " ", base).strip()
    dic = crear_diccionario_variedades()
    code = dic.get(base)
    if code:
        return code
    return _codigo_variedad_from_name(base)

def _ord_tiquet(x):
    try:
        s = str(x)
        m = re.match(r'^\s*(\d+)\s*([A-Za-z]*)\s*$', s)
        if m:
            return (int(m.group(1)), m.group(2) or '')
        return (0, s)
    except:
        return (0, str(x))


# ============================================================
# PARCELAS
# ============================================================
def cargar_parcelas_desde_excel(parc_file: bytes, sheet_name='Parcelas') -> pd.DataFrame:
    # Detección de cabecera desplazada (como en tu Colab)
    df_test = pd.read_excel(io.BytesIO(parc_file), sheet_name=sheet_name, nrows=10)
    columnas_esperadas = [
        'Ejercicio','RefParcela','NRegistro','NIF','Apellidos','Nombre',
        'Variedad','Superficie','PorcentajeTitularidad','Estado','Segmento'
    ]
    esper_norm = [_norm_text(c) for c in columnas_esperadas]
    test_norm = [_norm_text(c) for c in df_test.columns]
    coincidencias = sum(1 for c in esper_norm if c in test_norm)
    if coincidencias < 4:
        df = pd.read_excel(io.BytesIO(parc_file), sheet_name=sheet_name, skiprows=6)
    else:
        df = pd.read_excel(io.BytesIO(parc_file), sheet_name=sheet_name)
    return df


def procesar_parcelas(df: pd.DataFrame) -> pd.DataFrame:
    df_clean = df.copy()

    rename_pairs = [
        ('NIF', ['NIF','nif']),
        ('Variedad', ['Variedad','variedad','Varietat','varietat']),
        ('RefParcela', ['RefParcela','refparcela','Ref_Parcela','Ref Parcela','Ref parcela','origenParcela','origenParcella']),
        ('Superficie', ['Superficie','superficie','Sup','sup','Hectáreas','Hectareas','ha','HA']),
        ('Segmento', ['Segmento','segmento']),
        ('Nombre', ['Nombre','nombre']),
        ('Apellidos', ['Apellidos','apellidos']),
        ('Ejercicio', ['Ejercicio','ejercicio','Any','Año','ano','Ano']),
        ('PorcentajeTitularidad', ['PorcentajeTitularidad','porcentajetitularidad','Porcentaje Titularidad','PorcTitularidad']),
        ('NRegistro', ['NRegistro','Nº Registro','NºRegistro','NumRegistro']),
        ('Estado', ['Estado','estado','Estat','estat','Status']),
    ]
    for std, cands in rename_pairs:
        c = _find_col(df_clean, cands)
        if c:
            df_clean.rename(columns={c: std}, inplace=True)

    # Filtros
    if 'Segmento' in df_clean.columns:
        df_clean['Segmento'] = df_clean['Segmento'].astype(str).map(_norm_segmento)
        df_clean = df_clean[df_clean['Segmento'] == 'GUARDA']

    if 'Estado' in df_clean.columns:
        estado_norm = df_clean['Estado'].astype(str).map(_norm_text)
        aceptados_exactos = {
            'VALID', 'VALIDA', 'VALIDADA', 'VALIDADO', 'VALIDADOS', 'VALIDADES',
            'VALIDE', 'VALIDEZ', 'VIGENT', 'VIGENTE', 'APROVAT', 'APROBADO', 'APROBADA'
        }
        mask_valid = estado_norm.str.startswith('VALID') | estado_norm.isin(aceptados_exactos)
        df_clean = df_clean[mask_valid].copy()

    if 'NIF' in df_clean.columns:
        df_clean['NIF'] = df_clean['NIF'].map(_norm_nif)
        df_clean = df_clean[df_clean['NIF'] != ""]

    if 'Variedad' in df_clean.columns:
        df_clean['Variedad'] = df_clean['Variedad'].map(_norm_variedad)

    if 'Superficie' in df_clean.columns:
        df_clean['Superficie'] = df_clean['Superficie'].map(_to_numeric_safe)
        df_clean = df_clean.dropna(subset=['Superficie'])
    else:
        raise ValueError("Falta 'Superficie' en Parcelas.")

    if 'PorcentajeTitularidad' in df_clean.columns:
        df_clean['PorcentajeTitularidad'] = pd.to_numeric(df_clean['PorcentajeTitularidad'], errors='coerce').fillna(100).clip(0,100)
        df_clean['superficie_efectiva'] = df_clean['Superficie'] * (df_clean['PorcentajeTitularidad']/100.0)
    else:
        df_clean['superficie_efectiva'] = df_clean['Superficie']

    if 'Nombre' in df_clean.columns and 'Apellidos' in df_clean.columns:
        df_clean['nombre_completo'] = (df_clean['Nombre'].astype(str).str.strip() + ' ' + df_clean['Apellidos'].astype(str).str.strip()).str.strip()
    else:
        df_clean['nombre_completo'] = 'N/A'

    df_clean['codigo_variedad'] = df_clean['Variedad'].map(_codigo_variedad_robusto) if 'Variedad' in df_clean.columns else 'UNK'
    df_clean['vartip'] = df_clean['codigo_variedad'].astype(str) + '-' + df_clean['NIF'].astype(str)

    if 'RefParcela' in df_clean.columns:
        df_clean['RefParcela_norm'] = df_clean['RefParcela'].map(_norm_refparcela)
    else:
        df_clean['RefParcela_norm'] = ""

    if 'Ejercicio' in df_clean.columns:
        ej_num = pd.to_numeric(df_clean['Ejercicio'], errors='coerce')
        df_clean['Ejercicio'] = np.where(ej_num.notna(), ej_num.astype('Int64'), df_clean['Ejercicio'].astype(str))

    return df_clean


def crear_dataframe_final_parcelas(
    df_clean: pd.DataFrame,
    rendimiento_por_ha: float = RENDIMIENTO_POR_HECTAREA_DEFAULT,
    agrupar_por_ejercicio: bool = AGRUPAR_POR_EJERCICIO_DEFAULT
) -> pd.DataFrame:
    clave = ['Ejercicio','vartip'] if agrupar_por_ejercicio and ('Ejercicio' in df_clean.columns) else ['vartip']
    hect = (df_clean.groupby(clave, dropna=False)['superficie_efectiva']
            .sum().reset_index().rename(columns={'superficie_efectiva':'hectareas_variedad'}))
    agg = {
        'NIF':'first','nombre_completo':'first','Segmento':'first','Variedad':'first','codigo_variedad':'first'
    }
    df_final = (df_clean.groupby(clave, dropna=False).agg(agg).reset_index()
                .merge(hect, on=clave, how='left'))
    df_final['rendimiento'] = df_final['hectareas_variedad'] * float(rendimiento_por_ha)

    rename_map = {'NIF':'nif','nombre_completo':'nombre','Segmento':'segmento'}
    if 'Ejercicio' in df_final.columns:
        rename_map['Ejercicio'] = 'ejercicio'
    df_final.rename(columns=rename_map, inplace=True)

    cols = (['ejercicio'] if 'ejercicio' in df_final.columns else []) + \
           ['nif','nombre','vartip','segmento','hectareas_variedad','rendimiento']
    df_final = df_final[cols]
    df_final['hectareas_variedad'] = df_final['hectareas_variedad'].astype(float).round(4)
    df_final['rendimiento'] = df_final['rendimiento'].astype(float).round(2)
    sort_cols = (['ejercicio','rendimiento'] if 'ejercicio' in df_final.columns else ['rendimiento'])
    df_final = df_final.sort_values(sort_cols, ascending=[True,False] if 'ejercicio' in df_final.columns else [False]).reset_index(drop=True)
    return df_final


# ============================================================
# IT04
# ============================================================
def cargar_it04_df(it04_file: Optional[bytes]) -> Optional[pd.DataFrame]:
    if not it04_file:
        return None
    df = pd.read_excel(io.BytesIO(it04_file))
    cols = {c.lower().strip(): c for c in df.columns}
    col_vt = next((cols[k] for k in cols if k == 'vartip'), None)
    col_kg = next((cols[k] for k in cols if k in ('kg_a_restar','kgarestar','kg_restar')), None)
    if col_vt is None or col_kg is None:
        raise ValueError("El archivo it04 debe tener columnas 'vartip' y 'kg_a_restar'.")
    df = df.rename(columns={col_vt:'vartip', col_kg:'kg_a_restar'})
    df['vartip'] = df['vartip'].astype(str).str.strip().str.upper()
    df['kg_a_restar'] = pd.to_numeric(df['kg_a_restar'], errors='coerce').fillna(0.0)
    df.loc[df['kg_a_restar'] < 0, 'kg_a_restar'] = 0.0
    df_aggr = df.groupby('vartip', dropna=False)['kg_a_restar'].sum().reset_index().rename(columns={'kg_a_restar':'kg_a_restar_total'})
    return df_aggr


def construir_rendimiento_ajustado(
    df_final: pd.DataFrame,
    df_it04_aggr: Optional[pd.DataFrame]
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    rend_total = (df_final.groupby('vartip', dropna=False)['rendimiento']
                  .sum().reset_index().rename(columns={'rendimiento':'rendimiento_total'}))
    if df_it04_aggr is None or df_it04_aggr.empty:
        rend_total['kg_a_restar_total'] = 0.0
        rend_total['rendimiento_ajustado_total'] = rend_total['rendimiento_total']
        return rend_total, pd.DataFrame()
    out = rend_total.merge(df_it04_aggr, on='vartip', how='left')
    out['kg_a_restar_total'] = out['kg_a_restar_total'].fillna(0.0)
    out['rendimiento_ajustado_total'] = (out['rendimiento_total'] - out['kg_a_restar_total']).clip(lower=0.0)
    return out, df_it04_aggr


# ============================================================
# CAVANET (carga y proceso)
# ============================================================
def _guess_header_row_cavanet(xls_bytes: bytes, sheet_name=None, lookahead_rows=30) -> int:
    preview = pd.read_excel(io.BytesIO(xls_bytes), sheet_name=sheet_name, header=None, nrows=lookahead_rows)
    expected = [
        'FECHA','TIQUET','BODEGA','NIFBODEGA','INSTALACION','DNI',
        'NOMBREVITICULTOR','VARIEDAD','SEGMENTO','PARCELA','KG','ESTADO'
    ]
    expected_set = set(expected)
    def score_row(vals):
        cells = [_norm_text(v) for v in vals]
        return sum(1 for c in cells if c in expected_set)
    best_row, best_score = 0, -1
    for i in range(len(preview)):
        sc = score_row(list(preview.iloc[i].values))
        if sc > best_score:
            best_score, best_row = sc, i
    return best_row if best_score >= 4 else 0


def cargar_cavanet_desde_excel(cav_file: bytes) -> pd.DataFrame:
    xls = pd.ExcelFile(io.BytesIO(cav_file))
    sheet = xls.sheet_names[0]
    for s in xls.sheet_names:
        s_norm = _norm_text(s)
        if 'PESAD' in s_norm or 'BODEGA' in s_norm or 'DETALLE' in s_norm:
            sheet = s
            break
    hdr = _guess_header_row_cavanet(cav_file, sheet_name=sheet, lookahead_rows=30)
    df = pd.read_excel(io.BytesIO(cav_file), sheet_name=sheet, header=hdr)
    df = df.dropna(axis=1, how='all')
    return df


def procesar_cavanet(df: pd.DataFrame) -> pd.DataFrame:
    dfc = df.copy()

    col_fecha  = _find_col(dfc, ['Fecha','Data']) or _find_col_by_terms(dfc, ['FECH'])
    col_tiquet = _find_col(dfc, ['Tiquet','Ticket','TiquetBascula'])
    col_bodega = _find_col(dfc, ['Bodega','nomCeller','Celler'])
    col_nifbog = _find_col(dfc, ['NifBodega','NIF Bodega','NIF_Bodega'])
    col_inst   = _find_col(dfc, ['Instalacion','Instalación','instalacion','instal·lacio','instalacio','instalación'])
    col_dni    = _find_col(dfc, ['Dni','DNI','NIF','nif'])
    col_nomvit = _find_col(dfc, ['NombreViticultor','NomViticultor','Proveedor','nomLliurador'])
    col_var    = _find_col(dfc, ['Variedad','Varietat','varietat','variedad'])
    col_seg    = _find_col(dfc, ['Segmento','segmento'])
    col_parc   = _find_col(dfc, ['Parcela','Parcella','parcela','parcella'])
    col_kg     = _find_col(dfc, ['kg','Kg','Kgs','Kilos','KILOS','Peso','PESO'])
    col_est    = _find_col(dfc, ['Estado','Estat','estado'])

    # Eliminar columnas no usadas
    for c in ['FechaEstado','FechaModificacion','UsuarioModificacion']:
        if c in dfc.columns:
            dfc.drop(columns=[c], inplace=True)

    # Renombrado a estándar
    ren = {}
    if col_fecha:  ren[col_fecha]='Fecha'
    if col_tiquet: ren[col_tiquet]='Tiquet'
    if col_bodega: ren[col_bodega]='Bodega'
    if col_nifbog: ren[col_nifbog]='NifBodega'
    if col_inst:   ren[col_inst]='Instalacion'
    if col_dni:    ren[col_dni]='Dni'
    if col_nomvit: ren[col_nomvit]='NombreViticultor'
    if col_var:    ren[col_var]='Variedad'
    if col_seg:    ren[col_seg]='Segmento'
    if col_parc:   ren[col_parc]='Parcela'
    if col_kg:     ren[col_kg]='kg'
    if col_est:    ren[col_est]='Estado'
    dfc = dfc.rename(columns=ren)

    # Filtros
    if 'Segmento' in dfc.columns:
        dfc['Segmento'] = dfc['Segmento'].astype(str).map(_norm_segmento)
        dfc = dfc[dfc['Segmento'] == 'GUARDA']
    if 'Estado' in dfc.columns:
        dfc['Estado'] = dfc['Estado'].astype(str).map(_norm_text)
        dfc = dfc[dfc['Estado'] == 'VALID']

    # Normalizaciones
    if 'Dni' in dfc.columns:
        dfc['Dni'] = dfc['Dni'].map(_norm_nif)
        dfc = dfc[dfc['Dni'] != ""]
    if 'Variedad' in dfc.columns:
        dfc['Variedad'] = dfc['Variedad'].map(_norm_variedad)
    if 'Parcela' in dfc.columns:
        dfc['RefParcela_norm'] = dfc['Parcela'].map(_norm_refparcela)
    else:
        dfc['RefParcela_norm'] = ""

    if 'kg' in dfc.columns:
        dfc['kg'] = pd.to_numeric(dfc['kg'], errors='coerce').fillna(0.0).clip(lower=0.0)
    else:
        raise ValueError("Cavanet necesita columna de kilos ('kg').")

    if 'Fecha' in dfc.columns:
        dfc['Fecha_dt'] = pd.to_datetime(dfc['Fecha'], errors='coerce', dayfirst=True, utc=False)
    else:
        dfc['Fecha_dt'] = pd.NaT

    # Orden por Fecha
    dfc = dfc.sort_values(['Fecha_dt','Tiquet'] if 'Tiquet' in dfc.columns else ['Fecha_dt']).reset_index(drop=True)
    return dfc


# ============================================================
# Cruce + Repartos
# ============================================================
def crear_vartip_cavanet(
    df_cav_clean: pd.DataFrame,
    df_final_parcelas: pd.DataFrame,
    df_parcelas_clean: pd.DataFrame,
    df_rend_ajustado: pd.DataFrame
) -> pd.DataFrame:
    # Filtramos por NIF presentes en Parcelas (viticultores válidos)
    socios_nif = set(df_final_parcelas['nif'].astype(str))
    mask_socios = df_cav_clean['Dni'].isin(socios_nif) if 'Dni' in df_cav_clean.columns \
        else pd.Series(False, index=df_cav_clean.index)
    df_filtrado = df_cav_clean[mask_socios].copy()

    # VARTIP (mismo criterio que Parcelas)
    df_filtrado['codigo_variedad'] = df_filtrado['Variedad'].map(_codigo_variedad_robusto)
    df_filtrado['vartip'] = df_filtrado['codigo_variedad'].astype(str) + '-' + df_filtrado['Dni'].astype(str)

    # Rendimiento ajustado por IT04
    df_rend = df_rend_ajustado.rename(columns={'rendimiento_ajustado_total':'rendimiento'})[['vartip','rendimiento']]
    tmp = df_filtrado.merge(df_rend, on='vartip', how='inner')

    # Filtro por origen de parcela (solo parcelas registradas para ese VARTIP)
    valid_parc = (df_parcelas_clean[['vartip','RefParcela_norm']].dropna().drop_duplicates())
    df_merge = tmp.merge(valid_parc, on=['vartip','RefParcela_norm'], how='inner')

    return df_merge


def controlar_rendimientos_por_fecha(df_cav_con_rend: pd.DataFrame) -> pd.DataFrame:
    if 'kg' not in df_cav_con_rend.columns:
        raise ValueError("Falta columna 'kg' en Cavanet procesado.")

    df = df_cav_con_rend.copy()
    df['kg_cava'] = 0.0
    df['kg_pgc'] = 0.0
    df['acumulado_antes'] = 0.0
    df['acumulado_despues'] = 0.0
    df['estado_vartip'] = 'ACTIVO'

    df = df.sort_values(['vartip','Fecha_dt','Tiquet'] if 'Tiquet' in df.columns else ['vartip','Fecha_dt']).reset_index(drop=True)

    for vt, idxs in df.groupby('vartip').groups.items():
        idxs = list(idxs)
        if not idxs:
            continue
        r_vals = df.loc[idxs, 'rendimiento'].dropna()
        if r_vals.empty:
            continue
        r_max = float(r_vals.iloc[0])

        acum = 0.0
        completo = False
        for i in idxs:
            kg = float(df.loc[i, 'kg'])
            df.loc[i, 'acumulado_antes'] = acum
            if not completo:
                if acum + kg <= r_max:
                    df.loc[i, 'kg_cava'] = kg
                    df.loc[i, 'kg_pgc'] = 0.0
                    acum += kg
                    if abs(acum - r_max) < 1e-9:
                        completo = True
                        df.loc[i, 'estado_vartip'] = 'COMPLETADO'
                else:
                    kg_cava = max(r_max - acum, 0.0)
                    kg_pgc = kg - kg_cava
                    df.loc[i, 'kg_cava'] = kg_cava
                    df.loc[i, 'kg_pgc'] = kg_pgc
                    acum = r_max
                    completo = True
                    df.loc[i, 'estado_vartip'] = 'EXCEDIDO'
            else:
                df.loc[i, 'kg_cava'] = 0.0
                df.loc[i, 'kg_pgc'] = kg
                df.loc[i, 'estado_vartip'] = 'EXCEDIDO'

            df.loc[i, 'acumulado_despues'] = acum

    return df


def generar_resumenes_cavanet(df_procesado: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    # Resumen por Bodega (y por Instalación si existe)
    if 'Bodega' in df_procesado.columns:
        group_cols = ['Bodega']
        if 'Instalacion' in df_procesado.columns:
            group_cols.append('Instalacion')
        resumen_bodegas = (
            df_procesado.groupby(group_cols, dropna=False)
                .agg(
                    total_kg_pgc=('kg_pgc', 'sum'),
                    total_kg_cava=('kg_cava', 'sum'),
                    total_kg_general=('kg', 'sum'),
                    num_pesadas=('kg', 'count'),
                )
                .round(2)
                .reset_index()
        )
    else:
        resumen_bodegas = pd.DataFrame()

    # Resumen por VARTIP
    agg = (
        df_procesado.groupby('vartip', dropna=False)
            .agg(
                total_kg_pgc=('kg_pgc', 'sum'),
                total_kg_cava=('kg_cava', 'sum'),
                total_kg_general=('kg', 'sum'),
                rendimiento_maximo=('rendimiento', 'first'),
                num_pesadas=('kg', 'count'),
                variedad=('Variedad', 'first'),
            )
            .reset_index()
    )
    agg['porcentaje_uso_rendimiento'] = np.where(
        agg['rendimiento_maximo'] > 0,
        (agg['total_kg_cava'] / agg['rendimiento_maximo'] * 100).round(2),
        np.nan,
    )
    resumen_vartips = agg.sort_values('total_kg_pgc', ascending=False)
    return resumen_bodegas, resumen_vartips


# ============================================================
# Excel (con VARTIP_Detalle y VARTIP_Detalle_ticket)
# ============================================================
def _ensure_fecha_dt(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if 'Fecha_dt' not in df.columns:
        if 'Fecha' in df.columns:
            df['Fecha_dt'] = pd.to_datetime(df['Fecha'], errors='coerce', dayfirst=True, utc=False)
        else:
            df['Fecha_dt'] = pd.NaT
    return df

def _build_vartip_detalle_por_fecha(df_procesado: pd.DataFrame) -> pd.DataFrame:
    df_det = _ensure_fecha_dt(df_procesado)
    df_det = df_det.rename(columns={'estado_vartip': 'estado'})
    df_det['acumulado_nif'] = df_det.groupby('vartip')['kg'].cumsum()
    cols_det = [
        'vartip', 'Variedad', 'Dni', 'NombreViticultor', 'Bodega', 'Instalacion', 'NifBodega',
        'Fecha', 'Fecha_dt', 'Tiquet', 'Parcela', 'RefParcela_norm',
        'kg', 'acumulado_nif', 'kg_cava', 'kg_pgc', 'estado', 'rendimiento',
    ]
    cols_det = [c for c in cols_det if c in df_det.columns]
    df_vartip_detalle = df_det[cols_det].sort_values(
        ['vartip', 'Fecha_dt', 'Tiquet'] if 'Tiquet' in df_det.columns else ['vartip', 'Fecha_dt']
    ).reset_index(drop=True)
    return df_vartip_detalle


def _build_vartip_detalle_por_tiquet(df_procesado: pd.DataFrame) -> pd.DataFrame:
    # Recalcula reparto/acumulados en ORDEN de Tiquet
    df_tick = df_procesado.copy()
    if 'Tiquet' in df_tick.columns:
        df_tick['_ord_t'] = df_tick['Tiquet'].apply(_ord_tiquet)
    else:
        df_tick['_ord_t'] = list(range(len(df_tick)))
    df_tick = df_tick.sort_values(['vartip', '_ord_t']).reset_index(drop=True)

    df_tick['kg_cava_ticket'] = 0.0
    df_tick['kg_pgc_ticket'] = 0.0
    df_tick['acum_antes_ticket'] = 0.0
    df_tick['acum_despues_ticket'] = 0.0
    df_tick['estado_ticket'] = 'ACTIVO'

    for vt, idxs in df_tick.groupby('vartip').groups.items():
        idxs = list(idxs)
        if not idxs:
            continue
        r_vals = df_tick.loc[idxs, 'rendimiento'].dropna()
        if r_vals.empty:
            continue
        r_max = float(r_vals.iloc[0])

        acum = 0.0
        completo = False
        for i in idxs:
            kg = float(df_tick.loc[i, 'kg'])
            df_tick.loc[i, 'acum_antes_ticket'] = acum
            if not completo:
                if acum + kg <= r_max:
                    df_tick.loc[i, 'kg_cava_ticket'] = kg
                    df_tick.loc[i, 'kg_pgc_ticket'] = 0.0
                    acum += kg
                    if abs(acum - r_max) < 1e-9:
                        completo = True
                        df_tick.loc[i, 'estado_ticket'] = 'COMPLETADO'
                else:
                    kg_cava = max(r_max - acum, 0.0)
                    kg_pgc = kg - kg_cava
                    df_tick.loc[i, 'kg_cava_ticket'] = kg_cava
                    df_tick.loc[i, 'kg_pgc_ticket'] = kg_pgc
                    acum = r_max
                    completo = True
                    df_tick.loc[i, 'estado_ticket'] = 'EXCEDIDO'
            else:
                df_tick.loc[i, 'kg_cava_ticket'] = 0.0
                df_tick.loc[i, 'kg_pgc_ticket'] = kg
                df_tick.loc[i, 'estado_ticket'] = 'EXCEDIDO'
            df_tick.loc[i, 'acum_despues_ticket'] = acum

    df_tick['acumulado_nif_ticket'] = df_tick.groupby('vartip')['kg'].cumsum()

    cols_det_ticket = [
        'vartip', 'Variedad', 'Dni', 'NombreViticultor', 'Bodega', 'Instalacion', 'NifBodega',
        'Fecha', 'Fecha_dt', 'Tiquet', 'Parcela', 'RefParcela_norm',
        'kg', 'acumulado_nif_ticket', 'kg_cava_ticket', 'kg_pgc_ticket', 'estado_ticket', 'rendimiento',
    ]
    cols_det_ticket = [c for c in cols_det_ticket if c in df_tick.columns]
    df_vartip_detalle_ticket = df_tick[cols_det_ticket].reset_index(drop=True)
    return df_vartip_detalle_ticket


def build_excel_bytes_cavanet(
    df_procesado: pd.DataFrame,
    resumen_bodegas: pd.DataFrame,
    resumen_vartips: pd.DataFrame,
    df_rend_ajustado: Optional[pd.DataFrame] = None,
    df_it04_aggr: Optional[pd.DataFrame] = None
) -> bytes:
    # Derivados
    df_vartip_detalle = _build_vartip_detalle_por_fecha(df_procesado)
    df_vartip_detalle_ticket = _build_vartip_detalle_por_tiquet(df_procesado)

    df_con_pgc = _ensure_fecha_dt(df_procesado[df_procesado['kg_pgc'] > 0].copy())
    cols_pgc_vt = [
        'vartip', 'Bodega', 'Instalacion', 'Tiquet', 'Fecha', 'Fecha_dt', 'Parcela',
        'kg', 'kg_cava', 'kg_pgc', 'acumulado_antes', 'acumulado_despues', 'estado_vartip'
    ]
    cols_pgc_vt = [c for c in cols_pgc_vt if c in df_con_pgc.columns]
    df_pgc_por_vartip = df_con_pgc[cols_pgc_vt].sort_values(
        ['vartip','Fecha_dt','Tiquet'] if 'Tiquet' in df_con_pgc.columns else ['vartip','Fecha_dt']
    ).reset_index(drop=True)

    # Resumen desde la primera PGC (por fecha)
    df_ord = _ensure_fecha_dt(df_procesado.copy())
    df_ord = df_ord.sort_values(['vartip','Fecha_dt','Tiquet'] if 'Tiquet' in df_ord.columns else ['vartip','Fecha_dt']).reset_index(drop=True)
    df_ord['pos'] = df_ord.groupby('vartip').cumcount() + 1
    primer_pgc_pos = (df_ord[df_ord['kg_pgc'] > 0].groupby('vartip', as_index=False)
                      .agg(primer_pgc_pos=('pos', 'min')))
    pgc_counts = (df_con_pgc.groupby('vartip', as_index=False)
                  .agg(n_pesadas_pgc=('kg_pgc','count'), kg_pgc_total=('kg_pgc','sum')))
    df_join = df_ord.merge(primer_pgc_pos, on='vartip', how='left')
    df_join['desde_primer_pgc'] = (df_join['pos'] >= df_join['primer_pgc_pos'])
    post_counts = (df_join[df_join['desde_primer_pgc']]
                   .groupby('vartip', as_index=False)
                   .agg(n_pesadas_desde_primer_pgc=('pos','count')))
    pgc_resumen_vartip = (pgc_counts
                          .merge(primer_pgc_pos, on='vartip', how='left')
                          .merge(post_counts, on='vartip', how='left')
                          .sort_values('kg_pgc_total', ascending=False))

    desired_cols_inst = [
        'Bodega','Instalacion','NifBodega','Dni','Variedad','Fecha','Fecha_dt','Parcela','Tiquet','kg_pgc'
    ]
    cols_exist = [c for c in desired_cols_inst if c in df_con_pgc.columns]
    df_pgc_por_inst = df_con_pgc[cols_exist].copy()
    for c in desired_cols_inst:
        if c not in df_pgc_por_inst.columns:
            df_pgc_por_inst[c] = np.nan
    df_pgc_por_inst = df_pgc_por_inst[desired_cols_inst].sort_values(
        ['Bodega','Instalacion','Fecha_dt','Tiquet'] if 'Tiquet' in df_pgc_por_inst.columns else ['Bodega','Instalacion','Fecha_dt']
    ).reset_index(drop=True)

    # ---- Escritura a Excel en memoria ----
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine='openpyxl') as w:
        df_vartip_detalle.to_excel(w, sheet_name='VARTIP_Detalle', index=False)
        df_vartip_detalle_ticket.to_excel(w, sheet_name='VARTIP_Detalle_ticket', index=False)
        df_procesado.to_excel(w, sheet_name='Pesadas_Procesadas', index=False)
        if not resumen_bodegas.empty:
            resumen_bodegas.to_excel(w, sheet_name='Resumen_Bodegas', index=False)
        resumen_vartips.to_excel(w, sheet_name='Resumen_VARTIPs', index=False)
        if not df_con_pgc.empty:
            df_con_pgc.to_excel(w, sheet_name='Control_Excesos_PGC', index=False)
        if not df_pgc_por_vartip.empty:
            df_pgc_por_vartip.to_excel(w, sheet_name='PGC_por_VARTIP', index=False)
        if not pgc_resumen_vartip.empty:
            pgc_resumen_vartip.to_excel(w, sheet_name='PGC_Resumen_VARTIP', index=False)
        if not df_pgc_por_inst.empty:
            df_pgc_por_inst.to_excel(w, sheet_name='PGC_pesadas_por_Inst', index=False)
        if df_rend_ajustado is not None and not df_rend_ajustado.empty:
            df_rend_ajustado[['vartip','rendimiento_total','kg_a_restar_total','rendimiento_ajustado_total']].to_excel(
                w, sheet_name='IT04_Ajustes', index=False
            )
        if df_it04_aggr is not None and not df_it04_aggr.empty:
            df_it04_aggr.to_excel(w, sheet_name='IT04_Entrada', index=False)

    bio.seek(0)
    return bio.getvalue()
