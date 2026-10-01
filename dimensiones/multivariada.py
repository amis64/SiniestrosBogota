import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from flask import Blueprint, render_template, request

from datos import actores, siniestros

bp = Blueprint("multivariada", __name__)

# Etiquetas legibles (las mismas que usa la dimensión poblacional).
CONDICIONES = {
    "CONDUCTOR": "Conductor",
    "MOTOCICLISTA": "Motociclista",
    "PASAJERO/ACOMPAÑANTE": "Pasajero / acompañante",
    "PEATON": "Peatón",
    "CICLISTA": "Ciclista",
}

GRUPOS = ["0-11", "12-17", "18-28", "29-59", "60+"]
FRANJAS = ["Madrugada (0-5 h)", "Mañana (6-11 h)", "Tarde (12-17 h)", "Noche (18-23 h)"]
FRANJA_CORTES = [-1, 5, 11, 17, 23]

# Orden de los tipos de siniestro por cantidad de fallecidos (de mayor a menor).
CLASES = ["Atropello", "Choque", "Volcamiento", "Caida de ocupante", "Otro"]

# Localidades con menos de 100 siniestros no entran en comparaciones por porcentaje (Sumapaz).
MIN_SINIESTROS = 100


def _html(fig):
    return fig.to_html(full_html=False, include_plotlyjs=False)


def _miles(n):
    """Formato con punto de miles (196.152)."""
    return f"{int(n):,}".replace(",", ".")


def _decimal(x, dec=1):
    """Formato con coma decimal (72,6)."""
    return f"{x:.{dec}f}".replace(".", ",")


@bp.route("/multivariada")
def multivariada():
    sel_anio = request.args.get("anio", "Todos")
    sel_loc = request.args.get("localidad", "Todas")

    # ---------------- Filtros (año y localidad) ----------------
    ae = actores          # personas filtradas por año y localidad
    ss = siniestros       # siniestros filtrados por año y localidad
    if sel_anio.isdigit():
        ae = ae[ae["ANIO"] == int(sel_anio)]
        ss = ss[ss["ANIO"] == int(sel_anio)]
    else:
        sel_anio = "Todos"
    if sel_loc != "Todas":
        ae = ae[ae["LOCALIDAD"] == sel_loc]
        ss = ss[ss["LOCALIDAD"] == sel_loc]

    # ---------------- Indicadores ----------------
    personas = len(ae)
    muertes = int((ae["ESTADO"] == "MUERTO").sum())
    tasa_mortalidad = muertes / personas * 100 if personas else 0

    muertes_edad = ae[(ae["ESTADO"] == "MUERTO") & ae["GRUPO_EDAD"].notna()]
    peaton60 = int(((muertes_edad["CONDICION"] == "PEATON") & (muertes_edad["GRUPO_EDAD"] == "60+")).sum())
    pct_peaton60 = peaton60 / len(muertes_edad) * 100 if len(muertes_edad) else 0

    letal = ss.groupby("CLASE_TXT")["GRAVEDAD"].apply(lambda x: (x == 1).mean() * 100)
    let_volc = letal.get("Volcamiento", 0)
    let_choque = letal.get("Choque", 0)
    ratio_volc = let_volc / let_choque if let_choque else 0

    # ---------------- Gráfica 1: % de personas muertas por condición y grupo de edad ----------------
    a = ae.dropna(subset=["GRUPO_EDAD"])
    z1 = a.pivot_table(index="CONDICION", columns="GRUPO_EDAD", values="ESTADO",
                       aggfunc=lambda s: (s == "MUERTO").mean() * 100, observed=False)
    z1 = z1.reindex(index=[c for c in CONDICIONES if c in z1.index], columns=GRUPOS).fillna(0)
    txt1 = [[_decimal(v, 1) for v in fila] for fila in z1.values]
    g1 = go.Figure(go.Heatmap(
        z=z1.values, x=GRUPOS, y=[CONDICIONES[c] for c in z1.index],
        text=txt1, texttemplate="%{text}%", textfont=dict(size=13),
        colorscale="YlOrRd", xgap=2, ygap=2,
        colorbar=dict(title="% muerto", ticksuffix="%"),
    ))
    g1.update_layout(height=420, xaxis_title="Grupo de edad (años)", yaxis_title="")

    # ---------------- Gráfica 2: % de siniestros con muertos por tipo y franja horaria ----------------
    s = ss.copy()
    s["franja"] = pd.cut(s["HORA_NUM"], bins=FRANJA_CORTES, labels=FRANJAS)
    z2 = s.pivot_table(index="CLASE_TXT", columns="franja", values="GRAVEDAD",
                       aggfunc=lambda x: (x == 1).mean() * 100, observed=False)
    z2 = z2.reindex(index=[c for c in CLASES if c in z2.index], columns=FRANJAS).fillna(0)
    txt2 = [[_decimal(v, 1) for v in fila] for fila in z2.values]
    g2 = go.Figure(go.Heatmap(
        z=z2.values, x=FRANJAS, y=z2.index, text=txt2, texttemplate="%{text}%",
        textfont=dict(size=13), colorscale="YlOrRd", xgap=2, ygap=2,
        colorbar=dict(title="% con muertos", ticksuffix="%"),
    ))
    g2.update_layout(height=420, xaxis_title="Franja horaria", yaxis_title="")

    # ---------------- Gráfica 3: relación entre tipo de siniestro y gravedad por localidad ----------------
    # Solo responde al filtro de año: por construcción compara localidades entre sí.
    s3 = siniestros
    if sel_anio.isdigit():
        s3 = s3[s3["ANIO"] == int(sel_anio)]
    loc = s3.groupby("LOCALIDAD").agg(total=("GRAVEDAD", "size"),
                                      muertos=("GRAVEDAD", lambda x: (x == 1).sum()))
    loc["pct_muertos"] = loc["muertos"] / loc["total"] * 100
    atropellos = s3[s3["CLASE_TXT"] == "Atropello"].groupby("LOCALIDAD").size()
    loc["atropellos"] = atropellos.reindex(loc.index).fillna(0)
    loc["pct_atropello"] = loc["atropellos"] / loc["total"] * 100
    loc = loc[loc["total"] >= MIN_SINIESTROS].reset_index()
    prom_muertos = loc["muertos"].sum() / loc["total"].sum() * 100
    prom_atropello = loc["atropellos"].sum() / loc["total"].sum() * 100
    correlacion = loc["pct_muertos"].corr(loc["pct_atropello"])

    g3 = px.scatter(
        loc, x="pct_atropello", y="pct_muertos", size="total", color="pct_muertos",
        text="LOCALIDAD", size_max=45, height=520, color_continuous_scale="YlOrRd",
        labels={"pct_atropello": "% de siniestros que son atropellos",
                "pct_muertos": "% de siniestros con muertos", "total": "Siniestros"},
    )
    g3.update_traces(textposition="top center", textfont=dict(size=11),
                     marker=dict(line=dict(width=1, color="#0b1220")))
    g3.add_vline(x=prom_atropello, line_dash="dash", line_color="#38e8ff")
    g3.add_hline(y=prom_muertos, line_dash="dash", line_color="#c6ff3d")
    g3.update_layout(coloraxis_colorbar=dict(title="% muertos", ticksuffix="%"),
                     xaxis_title="% de siniestros que son atropellos",
                     yaxis_title="% de siniestros con muertos")

    # ---------------- Gráfica 4: quién muere según el tipo de siniestro ----------------
    m = ae[ae["ESTADO"] == "MUERTO"].merge(
        siniestros[["CODIGO_ACCIDENTE", "CLASE_TXT"]], on="CODIGO_ACCIDENTE", how="left")
    m = m.dropna(subset=["CLASE_TXT"])
    ct = pd.crosstab(m["CLASE_TXT"], m["CONDICION"])
    ct = ct.reindex(index=[c for c in CLASES if c in ct.index],
                    columns=[c for c in CONDICIONES if c in ct.columns]).fillna(0)
    pct4 = ct.div(ct.sum(axis=1).replace(0, 1), axis=0) * 100
    t4 = pct4.reset_index().melt(id_vars="CLASE_TXT", var_name="condicion", value_name="pct")
    t4["condicion"] = t4["condicion"].map(CONDICIONES)
    t4["texto"] = t4["pct"].map(lambda x: f"{_decimal(x)}%" if x >= 6 else "")
    g4 = px.bar(
        t4, x="pct", y="CLASE_TXT", color="condicion", orientation="h", text="texto",
        height=440, barmode="stack",
        category_orders={"CLASE_TXT": [c for c in CLASES if c in ct.index][::-1],
                         "condicion": [CONDICIONES[c] for c in CONDICIONES]},
        color_discrete_sequence=["#c6ff3d", "#38e8ff", "#ff4fa3", "#ffb547", "#8b7bff"],
        labels={"pct": "% de las personas fallecidas de ese tipo", "CLASE_TXT": "",
                "condicion": "Condición de la persona"},
    )
    g4.update_traces(textposition="inside", insidetextanchor="middle",
                     hovertemplate="%{y} - %{fullData.name}: %{x:.1f}%<extra></extra>")
    g4.update_layout(xaxis_title="% de las personas fallecidas en cada tipo de siniestro",
                     yaxis_title="", xaxis_range=[0, 100], legend_title_text="")

    # ---------------- Tabla resumen por tipo de siniestro ----------------
    tabla = []
    for clase in [c for c in CLASES if c in ss["CLASE_TXT"].unique()]:
        sub = ss[ss["CLASE_TXT"] == clase]
        cont = sub["GRAVEDAD"].value_counts()
        muertos_s = int(cont.get(1, 0))
        total_s = int(len(sub))
        muertes_clase = m[m["CLASE_TXT"] == clase]["CONDICION"].value_counts()
        top = muertes_clase.index[0] if len(muertes_clase) else None
        tabla.append({
            "clase": clase,
            "siniestros": _miles(total_s),
            "con_muertos": _miles(muertos_s),
            "pct": _decimal(muertos_s / total_s * 100, 2) + "%" if total_s else "-",
            "victima": CONDICIONES.get(top, "-") if top else "-",
            "victima_n": _miles(int(muertes_clase.iloc[0])) if len(muertes_clase) else "0",
        })

    return render_template(
        "multivariada.html",
        anios=[int(x) for x in sorted(siniestros["ANIO"].dropna().unique())],
        localidades=sorted(siniestros["LOCALIDAD"].dropna().unique()),
        sel_anio=sel_anio,
        sel_loc=sel_loc,
        ind_personas=_miles(personas),
        ind_muertes=_miles(muertes),
        ind_tasa=_decimal(tasa_mortalidad, 2),
        ind_peaton60=_decimal(pct_peaton60),
        ind_ratio=_decimal(ratio_volc),
        ind_let_volc=_decimal(let_volc, 2),
        ind_let_choque=_decimal(let_choque, 2),
        correlacion=_decimal(correlacion, 2),
        min_siniestros=MIN_SINIESTROS,
        tabla=tabla,
        grafica1=_html(g1),
        grafica2=_html(g2),
        grafica3=_html(g3),
        grafica4=_html(g4),
    )
