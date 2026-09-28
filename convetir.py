"""Convierte el Excel descargado de datos.gov.co en un CSV por hoja.

Se ejecuta UNA sola vez:  python convertir.py
Requiere:  pip install openpyxl
"""
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent / "data"
EXCEL = DATA / "siniestros_viales_consolidados_bogota_dc.xlsx"

if not EXCEL.exists():
    raise SystemExit(f"No se encontró {EXCEL}. Copia el Excel dentro de la carpeta data/.")

hojas = pd.read_excel(EXCEL, sheet_name=None)
for nombre, tabla in hojas.items():
    salida = DATA / f"{nombre.lower()}.csv"
    tabla.to_csv(salida, index=False)
    print(f"{nombre:12s} {tabla.shape[0]:>8,} filas  ->  {salida.name}")