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
    base = actores                      # filtrada solo por año
    if sel_anio.isdigit():
        base = base[base["ANIO"] == int(sel_anio)]
    else:
        sel_anio = "Todos"

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

    return render_template(
        "poblacional.html",
        anios=[int(x) for x in sorted(actores["ANIO"].dropna().unique())],
        condiciones=CONDICIONES,
        sel_anio=sel_anio,
        sel_cond=sel_cond,
        ind_total=_miles(total),
        ind_siniestros=_miles(n_siniestros),
        ind_hombres=_decimal(pct_hombres),
        ind_edad=f"{edad_mediana:.0f}" if edad_mediana == edad_mediana else "-",
        ind_lesionados=_decimal(pct_lesionados),
    )
