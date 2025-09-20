import pandas as pd
from typing import Tuple

def cargar_it04(df: pd.DataFrame) -> pd.DataFrame:
    # Normaliza nombres
    cols = {c.lower().strip(): c for c in df.columns}
    col_vt = next((cols[k] for k in cols if k == 'vartip'), None)
    col_kg = next((cols[k] for k in cols if k in ('kg_a_restar','kgarestar','kg_restar')), None)
    if col_vt is None or col_kg is None:
        raise ValueError("El archivo it04 debe tener columnas 'vartip' y 'kg_a_restar'.")

    df = df.rename(columns={col_vt:'vartip', col_kg:'kg_a_restar'})
    df['vartip'] = df['vartip'].astype(str).str.strip().str.upper()
    df['kg_a_restar'] = pd.to_numeric(df['kg_a_restar'], errors='coerce').fillna(0.0)
    df.loc[df['kg_a_restar'] < 0, 'kg_a_restar'] = 0.0

    df_it04_aggr = df.groupby('vartip', dropna=False)['kg_a_restar'].sum().reset_index()
    df_it04_aggr = df_it04_aggr.rename(columns={'kg_a_restar':'kg_a_restar_total'})
    return df_it04_aggr


def construir_rendimiento_ajustado(df_final: pd.DataFrame, df_it04_aggr: pd.DataFrame) -> pd.DataFrame:
    # rendimiento total por VARTIP
    rend_total = df_final.groupby('vartip', dropna=False)['rendimiento'].sum().reset_index()
    rend_total = rend_total.rename(columns={'rendimiento':'rendimiento_total'})

    if df_it04_aggr is None or df_it04_aggr.empty:
        rend_total['kg_a_restar_total'] = 0.0
        rend_total['rendimiento_ajustado_total'] = rend_total['rendimiento_total']
        return rend_total

    df_rend = rend_total.merge(df_it04_aggr, on='vartip', how='left')
    df_rend['kg_a_restar_total'] = df_rend['kg_a_restar_total'].fillna(0.0)
    df_rend['rendimiento_ajustado_total'] = (df_rend['rendimiento_total'] - df_rend['kg_a_restar_total']).clip(lower=0.0)
    return df_rend
