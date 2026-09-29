"""Carga y preparación de los datos. Lo usan las cuatro dimensiones:

    from datos import siniestros, actores, vehiculos, hipotesis

Tablas resultantes (todas ya traducidas con el diccionario):
    siniestros : 1 fila por siniestro   (LOCALIDAD, GRAVEDAD_TXT, CLASE_TXT, DISENO_TXT,
                                         CHOQUE_TXT, ANIO, MES, TRIMESTRE, DIA_SEMANA, HORA_NUM)
    actores    : 1 fila por persona     (EDAD, GRUPO_EDAD, CONDICION, ESTADO, SEXO,
                                         LOCALIDAD, ANIO, GRAVEDAD_SINIESTRO)
    vehiculos  : 1 fila por vehículo    (CLASE_TXT, SERVICIO_TXT, MODALIDAD_TXT, LOCALIDAD, ANIO)
    hipotesis  : 1 fila por causa       (CAUSA_TXT, LOCALIDAD, ANIO)
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.io as pio

DATA = Path(__file__).resolve().parent / "data"


def _leer(nombre, **kwargs):
    ruta = DATA / f"{nombre}.csv"
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró {ruta}. Ejecuta primero: python convertir.py")
    return pd.read_csv(ruta, **kwargs)


# ---------------------------------------------------------------- Carga
diccionario = _leer("diccionario")
siniestros = _leer("siniestros")
actores = _leer("actor_vial", low_memory=False)
vehiculos = _leer("vehiculos")
hipotesis = _leer("hipotesis")


def _mapa(hoja, campo):
    """Código -> descripción. Se filtra por HOJA porque CLASE existe en SINIESTROS y en VEHICULOS."""
    d = diccionario[(diccionario["HOJA"] == hoja) & (diccionario["CAMPO"] == campo)]
    return dict(zip(d["CODIGO"], d["DESCRIPCION"]))


# ---------------------------------------------------------------- Siniestros
siniestros["LOCALIDAD"] = siniestros["CODIGO_LOCALIDAD"].map(_mapa("SINIESTROS", "CODIGO_LOCALIDAD"))
siniestros["GRAVEDAD_TXT"] = siniestros["GRAVEDAD"].map(_mapa("SINIESTROS", "GRAVEDAD"))
siniestros["CLASE_TXT"] = siniestros["CLASE"].map(_mapa("SINIESTROS", "CLASE"))
siniestros["DISENO_TXT"] = siniestros["DISENO_LUGAR"].map(_mapa("SINIESTROS", "DISENO_LUGAR"))
siniestros["CHOQUE_TXT"] = siniestros["CHOQUE"].map(_mapa("SINIESTROS", "CHOQUE"))

siniestros["FECHA"] = pd.to_datetime(siniestros["FECHA"], format="%d/%m/%Y", errors="coerce")
siniestros["ANIO"] = siniestros["FECHA"].dt.year
siniestros["MES"] = siniestros["FECHA"].dt.month
siniestros["TRIMESTRE"] = siniestros["FECHA"].dt.quarter
_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
siniestros["DIA_SEMANA"] = siniestros["FECHA"].dt.dayofweek.map(dict(enumerate(_dias)))
siniestros["HORA_NUM"] = pd.to_numeric(siniestros["HORA"].astype(str).str[:2], errors="coerce")

# Columnas de siniestros que se agregan a las demás tablas
_geo = siniestros[["CODIGO_ACCIDENTE", "LOCALIDAD", "ANIO", "GRAVEDAD_TXT"]].rename(
    columns={"GRAVEDAD_TXT": "GRAVEDAD_SINIESTRO"}
)

# ---------------------------------------------------------------- Actores viales (personas)
# "SIN INFORMACION" -> NaN.  Edades > 100 se consideran errores de captura -> NaN.
actores["EDAD"] = pd.to_numeric(actores["EDAD"], errors="coerce")
actores["EDAD"] = actores["EDAD"].where(actores["EDAD"] <= 100)
actores["GRUPO_EDAD"] = pd.cut(
    actores["EDAD"],
    bins=[-1, 11, 17, 28, 59, 100],
    labels=["0-11", "12-17", "18-28", "29-59", "60+"],
)
actores = actores.merge(_geo, on="CODIGO_ACCIDENTE", how="left")

# ---------------------------------------------------------------- Vehículos
vehiculos["CLASE_TXT"] = vehiculos["CLASE"].map(_mapa("VEHICULOS", "CLASE"))
vehiculos["SERVICIO_TXT"] = vehiculos["SERVICIO"].map(_mapa("VEHICULOS", "SERVICIO"))
vehiculos["MODALIDAD_TXT"] = vehiculos["MODALIDAD"].map(_mapa("VEHICULOS", "MODALIDAD"))
vehiculos = vehiculos.merge(_geo, on="CODIGO_ACCIDENTE", how="left")

# ---------------------------------------------------------------- Hipótesis (causas)
# En esta hoja el código puede venir como texto; se compara como texto en ambos lados.
_causas = {str(k): v for k, v in _mapa("HIPOTESIS", "CODIGO_CAUSA").items()}
hipotesis["CAUSA_TXT"] = hipotesis["CODIGO_CAUSA"].astype(str).str.strip().map(_causas)
hipotesis = hipotesis.merge(_geo, on="CODIGO_ACCIDENTE", how="left")

# ---------------------------------------------------------------- Tema oscuro de las gráficas
tema = pio.templates["plotly_dark"]
tema.layout.paper_bgcolor = "rgba(0,0,0,0)"
tema.layout.plot_bgcolor = "rgba(0,0,0,0)"
tema.layout.font = dict(family="JetBrains Mono, monospace", color="#d6ddf0", size=12)
tema.layout.xaxis.gridcolor = "#1d2842"
tema.layout.yaxis.gridcolor = "#1d2842"
tema.layout.margin = dict(l=40, r=20, t=40, b=40)

px.defaults.template = tema
px.defaults.color_discrete_sequence = [
    "#c6ff3d", "#38e8ff", "#ff4fa3", "#ffb547", "#8b7bff", "#3dffb0",
]