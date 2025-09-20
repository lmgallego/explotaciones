import pandas as pd
import numpy as np
from .utils import (
    norm_text, norm_variedad, norm_nif, norm_refparcela,
    find_col, find_col_by_terms, ordenar_num_pesada_key,
    crear_diccionario_variedades, codigo_variedad_from_name
)

def procesar_rvc(df_rvc: pd.DataFrame) -> pd.DataFrame:
    # Detectar columnas
    col_dos    = find_col(df_rvc, ['dos'])
    col_cgs    = find_col(df_rvc, ['cavaGuardaSuperior', 'cava_guarda_superior'])
    col_num    = find_col(df_rvc, ['numPesada', 'num_pesada'])
    col_kg     = find_col(df_rvc, ['kgTotals', 'kg_totals', 'kgTotal', 'kg'])
    col_celler = find_col(df_rvc, ['nomCeller', 'celler', 'nombreCeller', 'nom_celler'])
    col_var    = find_col(df_rvc, ['varietatDesc','variedad','varietat','variety'])
    col_nifll  = find_col(df_rvc, ['nifLliurador','nifLLiurador','nif lliurador','nif_entrega','nifProveedor'])
    col_nomll  = find_col(df_rvc, ['nomLliurador','nom lliurador','nombreLliurador','proveedor','nombreProveedor'])
    col_nipd   = find_col(df_rvc, ['nipd','nip','idProveedor'])
    col_fecha  = find_col(df_rvc, ['dataPesada','fechaPesada','data_pesada','fecha'])
    col_origen = find_col(df_rvc, ['origenParcella','origenParcela','origen parcela','origen_parcela'])
    col_tiquet = find_col(df_rvc, ['tiquetBascula','tiquetBascu','tiquet_bascu','ticketBascula','tiquetBascul'])
    col_motiu  = find_col(df_rvc, ['motiuPesadaIncidental','motivoPesadaIncidental','motiu incidental','motivo incidental'])
    if col_motiu is None:
        col_motiu = find_col_by_terms(df_rvc, ['MOTIU','INCID']) or find_col_by_terms(df_rvc, ['MOTIVO','INCID'])
    if col_motiu is None:
        col_motiu = find_col_by_terms(df_rvc, ['MOTIU','INCIDENTAL']) or find_col_by_terms(df_rvc, ['MOTIVO','INCIDENTAL'])

    if col_kg is None:
        raise ValueError("No se encontró columna de kilos (kgTotals).")

    # Copia de trabajo
    df = df_rvc.copy()

    # Filtros: dos=CV y cavaGuardaSuperior NO explícito (blancos cuentan)
    if col_dos:
        df[col_dos] = df[col_dos].astype(str).map(norm_text)
    if col_cgs:
        cgs = df[col_cgs].astype(str).map(norm_text)
        si_vals = {'SI','SÍ','YES','Y','1','TRUE'}
        mask_no_gs = ~cgs.isin(si_vals) | cgs.isna()
    else:
        mask_no_gs = pd.Series(True, index=df.index)

    if col_dos:
        df = df[(df[col_dos] == 'CV') & mask_no_gs]
    else:
        df = df[mask_no_gs]

    # Excluir IN-01
    if col_motiu:
        mot_norm = df[col_motiu].astype(str).map(norm_text)
        excl = mot_norm.str.match(r'^\s*IN[-\s]*0*1\b', na=False)
        df = df[~excl].copy()

    # Ordenar por numPesada si existe
    if col_num:
        df['_ord'] = df[col_num].apply(ordenar_num_pesada_key)
        df = df.sort_values('_ord').drop(columns=['_ord']).reset_index(drop=True)

    # Kilos a numérico
    df[col_kg] = pd.to_numeric(df[col_kg], errors='coerce').fillna(0.0)

    # Renombrar a estándar
    rename_map = {}
    if col_celler: rename_map[col_celler] = 'nomCeller'
    if col_num:    rename_map[col_num]    = 'numPesada'
    if col_kg:     rename_map[col_kg]     = 'kgTotals'
    if col_var:    rename_map[col_var]    = 'varietatDesc'
    if col_nifll:  rename_map[col_nifll]  = 'nifLliurador'
    if col_nomll:  rename_map[col_nomll]  = 'nomLliurador'
    if col_nipd:   rename_map[col_nipd]   = 'nipd'
    if col_fecha:  rename_map[col_fecha]  = 'dataPesada'
    if col_origen: rename_map[col_origen] = 'origenParcella'
    if col_motiu:  rename_map[col_motiu]  = 'motiuPesadaIncidental'
    if col_tiquet: rename_map[col_tiquet] = 'tiquetBascula'
    df = df.rename(columns=rename_map)

    # RefParcela_norm
    if 'origenParcella' in df.columns:
        df['RefParcela_norm'] = df['origenParcella'].map(norm_refparcela)
    else:
        df['RefParcela_norm'] = ""

    return df


def crear_vartip_rvc(df_rvc_clean: pd.DataFrame,
                     df_final: pd.DataFrame,
                     df_parcelas_clean: pd.DataFrame,
                     df_rend_ajustado: pd.DataFrame) -> pd.DataFrame:

    dict_variedades = crear_diccionario_variedades()

    if 'varietatDesc' not in df_rvc_clean.columns or 'nifLliurador' not in df_rvc_clean.columns:
        raise ValueError("Faltan columnas para crear VARTIP (varietatDesc/nifLliurador).")

    socios_nif = set(df_final['nif'].astype(str))

    var_norm = df_rvc_clean['varietatDesc'].map(norm_variedad)
    nif_norm = df_rvc_clean['nifLliurador'].map(norm_nif)

    # Solo viticultores
    mask_socios = nif_norm.isin(socios_nif)
    df_filtrado = df_rvc_clean[mask_socios].copy()
    var_norm = var_norm[mask_socios]
    nif_norm = nif_norm[mask_socios]

    # VARTIP
    cod_var = var_norm.map(lambda s: dict_variedades.get(s, codigo_variedad_from_name(s)))
    df_filtrado['vartip'] = cod_var.astype(str) + '-' + nif_norm.astype(str)

    # Rendimientos ajustados
    df_rend = df_rend_ajustado.rename(columns={'rendimiento_ajustado_total':'rendimiento'})[['vartip','rendimiento']]

    # INNER por VARTIP
    df_merge = df_filtrado.merge(df_rend, on='vartip', how='inner')

    # INNER por (VARTIP, RefParcela_norm)
    if 'RefParcela_norm' in df_parcelas_clean.columns and df_parcelas_clean['RefParcela_norm'].notna().any():
        valid_parcels = (df_parcelas_clean[['vartip','RefParcela_norm']].dropna().drop_duplicates())
        df_merge = df_merge.merge(valid_parcels, on=['vartip','RefParcela_norm'], how='inner')

    return df_merge


def controlar_rendimientos(df_rvc_con_rend: pd.DataFrame) -> pd.DataFrame:
    if 'kgTotals' not in df_rvc_con_rend.columns:
        raise ValueError("Falta 'kgTotals' tras el preprocesado.")

    df = df_rvc_con_rend.copy()
    df['kg_cava'] = 0.0
    df['kg_pgc'] = 0.0
    df['acumulado_antes'] = 0.0
    df['acumulado_despues'] = 0.0
    df['estado_vartip'] = 'ACTIVO'

    # Orden interno
    if 'numPesada' in df.columns:
        df['_ord'] = df['numPesada'].apply(ordenar_num_pesada_key)
        df = df.sort_values(['vartip','_ord']).drop(columns=['_ord']).reset_index(drop=True)
    else:
        df = df.sort_values(['vartip']).reset_index(drop=True)

    for vartip, grp_idx in df.groupby('vartip').groups.items():
        idxs = list(grp_idx)
        if not idxs: continue
        r_vals = df.loc[idxs, 'rendimiento'].dropna()
        if r_vals.empty: continue
        r_max = float(r_vals.iloc[0])

        acumulado = 0.0
        completo = False
        for i in idxs:
            kg = float(df.loc[i, 'kgTotals'])
            df.loc[i, 'acumulado_antes'] = acumulado

            if not completo:
                if acumulado + kg <= r_max:
                    df.loc[i, 'kg_cava'] = kg
                    df.loc[i, 'kg_pgc'] = 0.0
                    acumulado += kg
                    if abs(acumulado - r_max) < 1e-9:
                        completo = True
                        df.loc[i, 'estado_vartip'] = 'COMPLETADO'
                else:
                    kg_cava = max(r_max - acumulado, 0.0)
                    kg_pgc = kg - kg_cava
                    df.loc[i, 'kg_cava'] = kg_cava
                    df.loc[i, 'kg_pgc'] = kg_pgc
                    acumulado = r_max
                    completo = True
                    df.loc[i, 'estado_vartip'] = 'EXCEDIDO'
            else:
                df.loc[i, 'kg_cava'] = 0.0
                df.loc[i, 'kg_pgc'] = kg
                df.loc[i, 'estado_vartip'] = 'EXCEDIDO'

            df.loc[i, 'acumulado_despues'] = acumulado

    return df


def generar_resumenes(df_procesado: pd.DataFrame):
    # Resumen cellers (nomCeller + nipd)
    if 'nomCeller' in df_procesado.columns:
        tmp = df_procesado.copy()
        if 'nipd' in tmp.columns:
            tmp['nipd'] = tmp['nipd'].astype(str).replace({'nan':''}).fillna('').str.strip()
            tmp['nipd'] = np.where(tmp['nipd'] == '', 'SIN_NIPD', tmp['nipd'])
            group_cols = ['nomCeller','nipd']
        else:
            group_cols = ['nomCeller']

        resumen_cellers = (tmp.groupby(group_cols, dropna=False)
            .agg(total_kg_pgc=('kg_pgc','sum'),
                 total_kg_cava=('kg_cava','sum'),
                 total_kg_general=('kgTotals','sum'),
                 num_pesadas=('kgTotals','count'))
            .round(2).reset_index())
        resumen_cellers = resumen_cellers.sort_values(['nomCeller','total_kg_pgc'], ascending=[True, False])
    else:
        resumen_cellers = pd.DataFrame()

    # Resumen VARTIP
    agg_dict = dict(
        total_kg_pgc=('kg_pgc','sum'),
        total_kg_cava=('kg_cava','sum'),
        total_kg_general=('kgTotals','sum'),
        rendimiento_maximo=('rendimiento','first'),
        num_pesadas=('kgTotals','count')
    )
    resumen_vartips = (df_procesado.groupby(['vartip'], dropna=False)
                       .agg(**agg_dict).reset_index())
    resumen_vartips['porcentaje_uso_rendimiento'] = np.where(
        resumen_vartips['rendimiento_maximo'] > 0,
        (resumen_vartips['total_kg_cava'] / resumen_vartips['rendimiento_maximo'] * 100).round(2),
        np.nan
    )
    resumen_vartips = resumen_vartips.sort_values('total_kg_pgc', ascending=False)

    return resumen_cellers, resumen_vartips


def construir_hojas_salida(df_procesado: pd.DataFrame, resumen_cellers: pd.DataFrame, resumen_vartips: pd.DataFrame):
    # VARTIP_Detalle
    df_det = df_procesado.copy()
    if 'kgTotals' in df_det.columns:
        df_det = df_det.rename(columns={'kgTotals':'kg', 'estado_vartip':'estado'})
    if 'numPesada' in df_det.columns:
        df_det['_ord'] = df_det['numPesada'].apply(ordenar_num_pesada_key)
        df_det = df_det.sort_values(['vartip','_ord']).drop(columns=['_ord']).reset_index(drop=True)
    else:
        df_det = df_det.sort_values(['vartip']).reset_index(drop=True)
    df_det['acumulado_nif'] = df_det.groupby('vartip')['kg'].cumsum()
    cols_vartip_det = [
        'vartip', 'varietatDesc', 'nipd', 'nomLliurador', 'nifLliurador',
        'rendimiento', 'dataPesada', 'numPesada', 'nomCeller', 'origenParcella', 'RefParcela_norm',
        'kg', 'acumulado_nif', 'kg_cava', 'kg_pgc', 'estado', 'motiuPesadaIncidental', 'tiquetBascula'
    ]
    cols_vartip_det = [c for c in cols_vartip_det if c in df_det.columns]
    df_vartip_detalle = df_det[cols_vartip_det].copy()

    # Pesadas con PGC
    df_con_pgc = df_procesado[df_procesado['kg_pgc'] > 0].copy()
    cols_pgc_por_vt = ['vartip','nomCeller','numPesada','kgTotals','kg_cava','kg_pgc','acumulado_antes','acumulado_despues','estado_vartip','origenParcella','RefParcela_norm','motiuPesadaIncidental','tiquetBascula']
    cols_pgc_por_vt = [c for c in cols_pgc_por_vt if c in df_con_pgc.columns]
    df_pgc_por_vartip = df_con_pgc[cols_pgc_por_vt].copy()
    if 'numPesada' in df_pgc_por_vartip.columns:
        df_pgc_por_vartip['_ord'] = df_pgc_por_vartip['numPesada'].apply(ordenar_num_pesada_key)
        df_pgc_por_vartip = df_pgc_por_vartip.sort_values(['vartip','_ord']).drop(columns=['_ord']).reset_index(drop=True)

    # PGC por NIPD (para comunicación con bodegas)
    desired_cols = ['nomCeller','nipd','nifLliurador','varietatDesc','dataPesada','origenParcella','numPesada','tiquetBascula','kg_pgc']
    cols_exist_nipd = [c for c in desired_cols if c in df_con_pgc.columns]
    df_pgc_por_nipd = df_con_pgc[cols_exist_nipd].copy()
    for c in desired_cols:
        if c not in df_pgc_por_nipd.columns:
            df_pgc_por_nipd[c] = np.nan
    df_pgc_por_nipd = df_pgc_por_nipd[desired_cols].sort_values(['nomCeller','nipd','dataPesada','numPesada']).reset_index(drop=True)

    # Resumen desde primera PGC
    df_ord = df_procesado.copy()
    if 'numPesada' in df_ord.columns:
        df_ord['_ord'] = df_ord['numPesada'].apply(ordenar_num_pesada_key)
        df_ord = df_ord.sort_values(['vartip','_ord']).reset_index(drop=True)
    else:
        df_ord = df_ord.sort_values(['vartip']).reset_index(drop=True)
    df_ord['pos'] = df_ord.groupby('vartip').cumcount() + 1

    primer_pgc_pos = (df_ord[df_ord['kg_pgc']>0].groupby('vartip', as_index=False)
                      .agg(primer_pgc_pos=('pos','min')))
    if 'numPesada' in df_ord.columns:
        primer_pgc_num = (df_ord[df_ord['kg_pgc']>0].groupby('vartip', as_index=False)
                          .agg(primer_numPesada_pgc=('numPesada','first')))
        primer_pgc = primer_pgc_pos.merge(primer_pgc_num, on='vartip', how='left')
    else:
        primer_pgc = primer_pgc_pos.copy(); primer_pgc['primer_numPesada_pgc'] = np.nan

    pgc_counts = (df_con_pgc.groupby('vartip', as_index=False)
                  .agg(n_pesadas_pgc=('kg_pgc','count'),
                       kg_pgc_total=('kg_pgc','sum')))

    df_join = df_ord.merge(primer_pgc[['vartip','primer_pgc_pos']], on='vartip', how='left')
    df_join['desde_primer_pgc'] = (df_join['pos'] >= df_join['primer_pgc_pos'])
    post_counts = (df_join[df_join['desde_primer_pgc']]
                   .groupby('vartip', as_index=False)
                   .agg(n_pesadas_desde_primer_pgc=('pos','count')))

    pgc_resumen_vartip = (pgc_counts
                          .merge(primer_pgc, on='vartip', how='left')
                          .merge(post_counts, on='vartip', how='left')
                          .sort_values('kg_pgc_total', ascending=False))

    hojas = {
        'VARTIP_Detalle': df_vartip_detalle,
        'Pesadas_Procesadas': df_procesado,
        'Resumen_Cellers': resumen_cellers,
        'Resumen_VARTIPs': resumen_vartips,
        'Control_Excesos_PGC': df_con_pgc,
        'PGC_por_VARTIP': df_pgc_por_vartip,
        'PGC_Resumen_VARTIP': pgc_resumen_vartip,
        'PGC_pesadas_por_NIPD': df_pgc_por_nipd
    }
    return hojas
