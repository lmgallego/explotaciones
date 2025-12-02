# Sistema de Control PGC - D.O. CAVA

Sistema de gestión y control de PGC (Producción de Gran Cultivo) y Movimientos de Vi Base para la Denominación de Origen CAVA.

## Descripción General

Esta aplicación Streamlit permite gestionar y controlar los rendimientos de uva por viticultor y variedad, determinando qué kilos van a **CAVA** (dentro del rendimiento permitido) y cuáles van a **PGC** (exceso sobre el rendimiento máximo autorizado).

## Módulos Principales

### 1. CAT PGC (Control PGC Catalunya)
**Archivo:** `pages/01_CAT_PGC.py`

Control de rendimientos para Catalunya utilizando datos del RVC (Registro Vitícola de Catalunya).

**Flujo de trabajo:**
1. **Carga de Parcelas**: Procesa archivo Excel con datos de parcelas (NIF, variedad, superficie, etc.)
2. **Ajustes IT04** (opcional): Permite restar kilos previamente declarados
3. **Análisis RVC**: Cruza pesadas con parcelas y calcula reparto CAVA/PGC

**Filtros aplicados:**
- Segmento = GUARDA (excluye Guarda Superior)
- Estado = VALIDADA
- Antigüedad de plantación: mínimo **3 años** (`AñoPlantacion <= año_actual - 3`)

**Salidas generadas:**
- `VARTIP_Detalle`: Detalle de todas las pesadas con estado
- `Resumen_Cellers`: Totales por bodega
- `Resumen_VARTIPs`: Totales por VARTIP con % uso rendimiento
- `Control_Excesos_PGC`: Solo pesadas con exceso
- `PGC_por_VARTIP`: Pesadas PGC ordenadas por VARTIP
- `PGC_pesadas_por_NIPD`: Para comunicación con bodegas

---

### 2. ESP PGC (Control PGC España)
**Archivo:** `pages/02_ESP_PGC.py`

Control de rendimientos para España utilizando datos de CAVANET.

**Flujo de trabajo:**
1. **Carga de Parcelas**: Procesa archivo Excel con datos de parcelas
2. **Ajustes IT04** (opcional): Permite restar kilos previamente declarados
3. **Análisis CAVANET**: Cruza pesadas con parcelas y calcula reparto CAVA/PGC

**Filtros aplicados:**
- Segmento = GUARDA
- Estado = VALIDADA (y variantes)
- Antigüedad de plantación: mínimo **2 años** (`AñoPlantacion <= año_actual - 2`)

**Salidas generadas:**
- `VARTIP_Detalle`: Detalle por fecha
- `VARTIP_Detalle_ticket`: Detalle por número de tiquet
- `Resumen_Bodegas`: Totales por bodega/instalación
- `Resumen_VARTIPs`: Totales por VARTIP
- Hojas adicionales de control PGC

---

### 3. Moviments Vi Base
**Archivo:** `pages/03_MOVIMENTS_VI_BASE.py`

Gestión y visualización de movimientos de Vi Base.

**Funcionalidades:**
- Procesamiento de datos CAVANET
- Filtrado por tipos de movimiento
- Visualizaciones interactivas con Plotly
- Cálculo de acumulados por fecha

---

## Lógica de Control de Rendimientos

### Concepto VARTIP
Clave única que combina código de variedad + NIF del viticultor:
```
VARTIP = código_variedad + '-' + NIF
Ejemplo: MAC-12345678A (Macabeo para el NIF 12345678A)
```

### Cálculo de Rendimiento
```
rendimiento = superficie × porcentaje_titularidad × rendimiento_por_hectárea
```
- Rendimiento por hectárea por defecto: **10,500 kg/ha**

### Reparto CAVA/PGC
Para cada VARTIP, se procesan las pesadas en orden cronológico:

```python
for cada pesada:
    if acumulado + kg <= rendimiento_máximo:
        kg_cava = kg          # Todo va a CAVA
        kg_pgc = 0
    else:
        kg_cava = rendimiento_máximo - acumulado  # Solo lo que cabe
        kg_pgc = kg - kg_cava                      # El resto a PGC
        estado = 'EXCEDIDO'
```

### Estados por VARTIP
| Estado | Significado |
|--------|-------------|
| **ACTIVO** | Aún hay margen de rendimiento |
| **COMPLETADO** | Se alcanzó exactamente el límite |
| **EXCEDIDO** | Se superó el rendimiento máximo |

---

## Filtro de Antigüedad de Plantación

Las parcelas se filtran por año de plantación para asegurar que la viña tenga la antigüedad mínima requerida:

| Módulo | Antigüedad Mínima | Fórmula |
|--------|-------------------|---------|
| **CAT PGC** | 3 años | `AñoPlantacion <= año_actual - 3` |
| **ESP PGC** | 2 años | `AñoPlantacion <= año_actual - 2` |

**Ejemplo (año 2025):**
- CAT PGC: Solo parcelas con `AñoPlantacion <= 2022`
- ESP PGC: Solo parcelas con `AñoPlantacion <= 2023`

Las parcelas sin `AñoPlantacion` (valor nulo) son eliminadas.

---

## Estructura del Proyecto

```
explotaciones/
├── streamlit_app.py          # Página principal
├── requirements.txt          # Dependencias
├── README.md                 # Este archivo
├── assets/
│   └── styles.css            # Estilos CSS personalizados
├── core/
│   ├── __init__.py
│   ├── parcelas.py           # Procesamiento de parcelas (CAT)
│   ├── rvc.py                # Lógica RVC (Catalunya)
│   ├── cavanet.py            # Lógica CAVANET (España)
│   ├── it04.py               # Procesamiento IT04
│   ├── export.py             # Exportación a Excel
│   ├── utils.py              # Utilidades comunes
│   ├── moviments_vi_base.py  # Movimientos Vi Base
│   ├── colors.py             # Paleta de colores
│   └── icons.py              # Iconos SVG
└── pages/
    ├── 01_CAT_PGC.py         # Control PGC Catalunya
    ├── 02_ESP_PGC.py         # Control PGC España
    └── 03_MOVIMENTS_VI_BASE.py # Movimientos Vi Base
```

---

## Instalación

### Requisitos
- Python 3.10+
- Dependencias en `requirements.txt`

### Instalación de dependencias
```bash
pip install -r requirements.txt
```

### Ejecución
```bash
python -m streamlit run streamlit_app.py
```

La aplicación estará disponible en `http://localhost:8501`

---

## Dependencias Principales

| Paquete | Versión | Uso |
|---------|---------|-----|
| streamlit | ≥1.37.0 | Framework web |
| pandas | ≥2.2.2 | Procesamiento de datos |
| numpy | ≥1.26.4 | Cálculos numéricos |
| openpyxl | ≥3.1.2 | Lectura/escritura Excel |
| streamlit-aggrid | ≥0.3.5 | Tablas interactivas |
| plotly | ≥5.17.0 | Visualizaciones |
| scikit-learn | ≥1.3.0 | Análisis estadístico |

---

## Archivos de Entrada

### Parcelas (Excel)
Columnas esperadas:
- `Ejercicio`: Año del ejercicio
- `RefParcela`: Referencia catastral
- `NIF`: NIF del viticultor
- `Variedad`: Variedad de uva
- `Superficie`: Superficie en hectáreas
- `PorcentajeTitularidad`: % de titularidad
- `Estado`: Estado de la parcela (VALIDADA)
- `Segmento`: Segmento (GUARDA)
- `AñoPlantacion`: Año de plantación de la viña

### IT04 (Excel/CSV)
Columnas esperadas:
- `vartip`: Código VARTIP
- `kg_a_restar`: Kilos a restar del rendimiento

### RVC / CAVANET (Excel/CSV)
Columnas principales:
- `nifLliurador` / `Dni`: NIF del entregador
- `varietatDesc` / `Variedad`: Variedad de uva
- `kgTotals` / `kg`: Kilos de la pesada
- `numPesada` / `Tiquet`: Número de pesada
- `dataPesada` / `Fecha`: Fecha de la pesada
- `origenParcella` / `Parcela`: Referencia de parcela
- `nomCeller` / `Bodega`: Nombre de la bodega

---

## Versión

**Sistema Control PGC - Versión 2025**

---

## Notas Técnicas

- El sistema detecta automáticamente variantes de nombres de columnas (con/sin acentos, mayúsculas/minúsculas)
- Los filtros de RVC excluyen pesadas con `dos != CV` y `cavaGuardaSuperior = SI`
- Se excluyen pesadas con motivo incidental `IN-01`
- El año de plantación se calcula dinámicamente usando `datetime.now().year`
