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
    t1["pct"] = (t1["personas"] / max(len(base), 1) * 100).round(2)
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
    )
