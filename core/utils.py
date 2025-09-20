import pandas as pd
import numpy as np
import re
import unicodedata
from typing import List, Optional, Tuple, Dict

RENDIMIENTO_POR_HECTAREA_DEFAULT = 10500

def strip_accents(s: str) -> str:
    if pd.isna(s):
        return ""
    s = str(s)
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

def norm_text(s: str) -> str:
    return strip_accents(s).strip().upper()

def norm_segmento(s: str) -> str:
    s = norm_text(s)
    return re.sub(r"\s+", " ", s)

def norm_variedad(s: str) -> str:
    s = norm_text(s)
    s = s.replace("XAREL.LO", "XARELLO").replace("XAREL·LO", "XARELLO").replace("PINOT-NOIR", "PINOT NOIR")
    return s

def norm_nif(x) -> str:
    if pd.isna(x):
        return ""
    s = str(x).strip()
    if re.fullmatch(r"\d+\.0", s):
        s = s[:-2]
    s = s.replace(",", "").replace(" ", "")
    s = re.sub(r"[^0-9A-Za-z]", "", s)
    return s.upper()

def norm_refparcela(x) -> str:
    if pd.isna(x):
        return ""
    s = str(x).strip().upper().replace(" ", "")
    return s

def to_numeric_safe(x):
    if isinstance(x, str):
        x = x.replace(",", ".")
    return pd.to_numeric(x, errors="coerce")

def codigo_variedad_from_name(var_name: str) -> str:
    s = norm_variedad(var_name)
    s = re.sub(r"[^A-Z]", "", s)
    if not s:
        return "UNK"
    return (s[:3] if len(s) >= 3 else s).upper()

def find_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    norm_map = {col: norm_text(col) for col in df.columns}
    targets = [norm_text(c) for c in candidates]
    for col, ncol in norm_map.items():
        if ncol in targets:
            return col
    for t in targets:
        for col, ncol in norm_map.items():
            if t in ncol:
                return col
    return None

def find_col_by_terms(df: pd.DataFrame, must_have_terms: List[str]) -> Optional[str]:
    norm_map = {col: norm_text(col) for col in df.columns}
    for col, ncol in norm_map.items():
        if all(term in ncol for term in must_have_terms):
            return col
    return None

def ordenar_num_pesada_key(pesada_str):
    try:
        s = str(pesada_str)
        m = re.match(r'(\d+)([A-Za-z]*)', s)
        if m:
            return (int(m.group(1)), m.group(2) or '')
        return (0, s)
    except:
        return (0, str(pesada_str))

def crear_diccionario_variedades() -> Dict[str, str]:
    base = {
        'CHARDONNAY': 'CHB',
        'GARNATXA NEGRA': 'GAN',
        'MACABEU': 'MAB',
        'MONASTRELL': 'MTN',
        'PARELLADA': 'PAB',
        'PINOT NOIR': 'PTN',
        'SUBIRAT PARENT': 'SPB',
        'TREPAT': 'TRN',
        'XARELLO': 'XAB',
    }
    return { norm_variedad(k): v for k, v in base.items() }
