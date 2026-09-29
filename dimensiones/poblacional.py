import pandas as pd
import plotly.express as px
from flask import Blueprint, render_template, request

from datos import actores

bp = Blueprint("poblacional", __name__)

# Etiquetas legibles para los valores tal como vienen en la hoja ACTOR_VIAL.
# El orden es el del volumen de personas y es el que se usa en el filtro y en las gráficas.
CONDICIONES = {
    "CONDUCTOR": "Conductor",
    "MOTOCICLISTA": "Motociclista",
    "PASAJERO/ACOMPAÑANTE": "Pasajero / acompañante",
    "PEATON": "Peatón",
    "CICLISTA": "Ciclista",
}

SEXOS = {
    "MASCULINO": "Masculino",
    "FEMENINO": "Femenino",
    "SIN INFORMACION": "Sin información",
}

ESTADOS = {"ILESO": "Ileso", "HERIDO": "Herido", "MUERTO": "Muerto"}

# Rangos de edad de 5 años; el último (95-100) recoge hasta el máximo válido (100).
_BORDES = list(range(0, 100, 5)) + [101]
_RANGOS = [f"{b}-{b + 4}" for b in range(0, 95, 5)] + ["95-100"]


def _html(fig):
    return fig.to_html(full_html=False, include_plotlyjs=False)


def _miles(n):
    """Formato con punto de miles (196.152), igual que en la página de inicio."""
    return f"{int(n):,}".replace(",", ".")


def _decimal(x, dec=1):
    """Formato con coma decimal (72,6)."""
    return f"{x:.{dec}f}".replace(".", ",")


@bp.route("/poblacional")
def poblacional():
    sel_anio = request.args.get("anio", "Todos")
    sel_cond = request.args.get("condicion", "Todas")

    # ---------------- Filtros ----------------
    anios = [int(x) for x in sorted(actores["ANIO"].dropna().unique())]
    base = actores                      # filtrada solo por año
    if sel_anio.isdigit() and int(sel_anio) in anios:
        base = base[base["ANIO"] == int(sel_anio)]
    else:
        sel_anio = "Todos"              # año inexistente o inválido -> vista completa

    d = base                            # filtrada por año y condición
    if sel_cond in CONDICIONES:
        d = d[d["CONDICION"] == sel_cond]
    else:
        sel_cond = "Todas"

    # ---------------- Indicadores ----------------
    total = len(d)
    n_siniestros = d["CODIGO_ACCIDENTE"].nunique()

    con_sexo = d[d["SEXO"] != "SIN INFORMACION"]
    pct_hombres = (con_sexo["SEXO"] == "MASCULINO").mean() * 100 if len(con_sexo) else 0

    edad_mediana = d["EDAD"].median()

    pct_lesionados = d["ESTADO"].isin(["HERIDO", "MUERTO"]).mean() * 100 if total else 0

    # ---------------- Gráfica 1: composición por condición ----------------
    # Usa 'base' (sin filtrar por condición) porque la condición es la variable que se mide.
    c = base["CONDICION"].value_counts()
    t1 = c.rename_axis("clave").reset_index(name="personas")
    t1["condicion"] = t1["clave"].map(CONDICIONES)
    t1["pct"] = t1["personas"] / max(len(base), 1) * 100
    t1 = t1.sort_values("personas")
    g1 = px.bar(t1, x="personas", y="condicion", orientation="h", height=380,
                text=[f"{_miles(n)} ({_decimal(p)}%)" for n, p in zip(t1["personas"], t1["pct"])],
                labels={"personas": "Personas", "condicion": ""})
    g1.update_traces(textposition="outside", cliponaxis=False)
    g1.update_layout(xaxis_title="Personas involucradas", yaxis_title="",
                     xaxis_range=[0, t1["personas"].max() * 1.3 if len(t1) else 1])

    # ---------------- Gráfica 2: composición por sexo ----------------
    sx = d["SEXO"].value_counts().rename_axis("clave").reset_index(name="personas")
    sx["sexo"] = sx["clave"].map(SEXOS)
    g2 = px.pie(sx, names="sexo", values="personas", hole=0.55, height=380,
                color="sexo",
                color_discrete_map={"Masculino": "#38e8ff", "Femenino": "#ff4fa3",
                                    "Sin información": "#7c88a8"})
    g2.update_traces(textinfo="label+percent", sort=False, textfont_size=13)
    g2.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10))

    # ---------------- Gráfica 3: distribución de la edad por rangos de 5 años ----------------
    rangos = pd.cut(d["EDAD"].dropna(), bins=_BORDES, right=False, labels=_RANGOS)
    t3 = rangos.value_counts().reindex(_RANGOS, fill_value=0).rename_axis("rango").reset_index(name="personas")
    g3 = px.bar(t3, x="rango", y="personas", height=380, labels={"rango": "Rango de edad", "personas": "Personas"})
    g3.update_traces(marker_color="#c6ff3d", hovertemplate="%{x} años<br>%{y:,} personas<extra></extra>")
    g3.update_layout(xaxis_title="Rango de edad (años)", yaxis_title="Personas", bargap=0.08)

    # ---------------- Gráfica 4: estado de la persona según su condición ----------------
    # Usa 'base' (sin filtrar por condición) porque compara las condiciones entre sí.
    cruce = pd.crosstab(base["CONDICION"], base["ESTADO"])
    for est in ESTADOS:
        if est not in cruce.columns:
            cruce[est] = 0
    pct = cruce[list(ESTADOS)].div(cruce[list(ESTADOS)].sum(axis=1), axis=0) * 100
    t4 = pct.reset_index().melt(id_vars="CONDICION", var_name="estado", value_name="pct")
    t4["condicion"] = t4["CONDICION"].map(CONDICIONES)
    t4["estado"] = t4["estado"].map(ESTADOS)
    t4["texto"] = t4["pct"].map(lambda x: f"{_decimal(x)}%" if x >= 5 else "")
    orden = [CONDICIONES[k] for k in CONDICIONES if k in cruce.index][::-1]
    g4 = px.bar(t4, x="pct", y="condicion", color="estado", orientation="h", text="texto", height=380,
                category_orders={"condicion": orden, "estado": ["Ileso", "Herido", "Muerto"]},
                color_discrete_map={"Ileso": "#38e8ff", "Herido": "#ffb547", "Muerto": "#ff4fa3"},
                labels={"pct": "% de personas", "condicion": "", "estado": "Estado"})
    g4.update_traces(textposition="inside", insidetextanchor="middle",
                     hovertemplate="%{y} - %{fullData.name}: %{x:.2f}%<extra></extra>")
    g4.update_layout(barmode="stack", xaxis_title="% de las personas de cada condición", yaxis_title="",
                     xaxis_range=[0, 100], legend_title_text="")

    # ---------------- Tabla resumen por condición (año seleccionado, todas las condiciones) ----------------
    tabla = []
    for clave, etiqueta in CONDICIONES.items():
        g = base[base["CONDICION"] == clave]
        if g.empty:
            continue
        cs = g[g["SEXO"] != "SIN INFORMACION"]
        med = g["EDAD"].median()
        tabla.append({
            "condicion": etiqueta,
            "personas": _miles(len(g)),
            "participacion": _decimal(len(g) / max(len(base), 1) * 100) + "%",
            "hombres": _decimal((cs["SEXO"] == "MASCULINO").mean() * 100) + "%" if len(cs) else "-",
            "edad": f"{med:.0f}" if med == med else "-",
            "heridas": _decimal((g["ESTADO"] == "HERIDO").mean() * 100) + "%",
            "muertas": _decimal((g["ESTADO"] == "MUERTO").mean() * 100, 2) + "%",
        })

    return render_template(
        "poblacional.html",
        anios=anios,
        condiciones=CONDICIONES,
        sel_anio=sel_anio,
        sel_cond=sel_cond,
        ind_total=_miles(total),
        ind_siniestros=_miles(n_siniestros),
        ind_hombres=_decimal(pct_hombres),
        ind_edad=f"{edad_mediana:.0f}" if edad_mediana == edad_mediana else "-",
        ind_lesionados=_decimal(pct_lesionados),
        grafica1=_html(g1),
        grafica2=_html(g2),
        grafica3=_html(g3),
        grafica4=_html(g4),
        tabla=tabla,
    )
