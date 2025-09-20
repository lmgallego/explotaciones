import io
import pandas as pd
from typing import Dict, Optional

def exportar_excel_parcelas(df_final: pd.DataFrame, df_clean: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_final.to_excel(writer, sheet_name='dataframe_final', index=False)
        cols_export = ['vartip','NIF','nombre_completo','Variedad','RefParcela','RefParcela_norm','Superficie',
                       'PorcentajeTitularidad','superficie_efectiva','Segmento','Ejercicio','codigo_variedad','Estado']
        cols_existentes = [c for c in cols_export if c in df_clean.columns]
        df_clean[cols_existentes].to_excel(writer, sheet_name='datos_completos', index=False)
    return output.getvalue()

def exportar_excel_rvc(hojas: Dict[str, pd.DataFrame],
                       df_rend_ajustado: Optional[pd.DataFrame]=None,
                       df_it04_aggr: Optional[pd.DataFrame]=None) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for nombre, df in hojas.items():
            if df is not None and not df.empty:
                df.to_excel(writer, sheet_name=nombre, index=False)
        # IT04
        if df_rend_ajustado is not None and not df_rend_ajustado.empty:
            cols = ['vartip','rendimiento_total','kg_a_restar_total','rendimiento_ajustado_total']
            cols = [c for c in cols if c in df_rend_ajustado.columns]
            df_rend_ajustado[cols].to_excel(writer, sheet_name='IT04_Ajustes', index=False)
        if df_it04_aggr is not None and not df_it04_aggr.empty:
            df_it04_aggr.to_excel(writer, sheet_name='IT04_Entrada', index=False)
    return output.getvalue()
