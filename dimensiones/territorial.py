import plotly.express as px
from flask import Blueprint, render_template, request

from datos import actores, siniestros

bp = Blueprint("territorial", __name__)

MIN_SINIESTROS = 100   # localidades con menos registros no se comparan en porcentajes (ej. Sumapaz)


def _html(fig):
    return fig.to_html(full_html=False, include_plotlyjs=False)


@bp.route("/territorial")
def territorial():
    sel_grav = request.args.get("gravedad", "Todas")
    sel_anio = request.args.get("anio", "Todos")

    # ---------------- Filtros ----------------
    base = siniestros                 # filtrada solo por año
    a = actores
    if sel_anio.isdigit():
        base = base[base["ANIO"] == int(sel_anio)]
        a = a[a["ANIO"] == int(sel_anio)]
    else:
        sel_anio = "Todos"

    d = base                          # filtrada por año y gravedad
    if sel_grav != "Todas":
        d = d[d["GRAVEDAD_TXT"] == sel_grav]
        a = a[a["GRAVEDAD_SINIESTRO"] == sel_grav]

    # ---------------- Indicadores ----------------
    conteo = d["LOCALIDAD"].value_counts()
    total = int(conteo.sum())
    top_nombre = conteo.index[0] if total else "-"
    top_valor = int(conteo.iloc[0]) if total else 0
    pct_top5 = round(conteo.head(5).sum() / max(total, 1) * 100, 1)

    # ---------------- Gráfica 1: siniestros por localidad ----------------
    t1 = conteo.sort_values().rename_axis("localidad").reset_index(name="siniestros")
    g1 = px.bar(t1, x="siniestros", y="localidad", orientation="h", text="siniestros", height=620)
    g1.update_traces(texttemplate="%{text:,}", textposition="outside", cliponaxis=False)
    g1.update_layout(xaxis_title="Siniestros", yaxis_title="")

    # ---------------- Gráfica 2: participación porcentual (treemap) ----------------
    t2 = conteo.rename_axis("localidad").reset_index(name="siniestros")
    g2 = px.treemap(t2, path=["localidad"], values="siniestros", height=620)
    g2.update_traces(textinfo="label+percent root", textfont_size=14)
    g2.update_layout(margin=dict(l=4, r=4, t=4, b=4))

    # ---------------- Gráfica 3: % de siniestros con muertos por localidad ----------------
    # Usa 'base' (sin filtrar por gravedad) porque la gravedad es la variable que se mide.
    g_loc = base.assign(muerto=base["GRAVEDAD"] == 1).groupby("LOCALIDAD")["muerto"].agg(["size", "sum"])
    promedio = g_loc["sum"].sum() / max(g_loc["size"].sum(), 1) * 100
    g_loc = g_loc[g_loc["size"] >= MIN_SINIESTROS]
    g_loc["pct"] = (g_loc["sum"] / g_loc["size"] * 100).round(2)
    t3 = g_loc.sort_values("pct").rename_axis("localidad").reset_index()
    g3 = px.bar(t3, x="pct", y="localidad", orientation="h", text="pct", height=620,
                hover_data={"sum": True, "size": True, "pct": ":.2f"},
                labels={"pct": "% con muertos", "sum": "Siniestros con muertos", "size": "Total siniestros"})
    g3.update_traces(texttemplate="%{text:.1f}%", textposition="outside", cliponaxis=False,
                     marker_color="#ff4fa3")
    g3.add_vline(x=promedio, line_dash="dash", line_color="#c6ff3d",
                 annotation_text=f"Bogotá: {promedio:.1f}%", annotation_font_color="#c6ff3d")
    g3.update_layout(xaxis_title="% de siniestros con muertos", yaxis_title="")

    # ---------------- Gráfica 4: edad mediana de las personas involucradas ----------------
    edad = a.groupby("LOCALIDAD")["EDAD"].agg(["median", "count"])
    edad_g = edad[edad["count"] >= MIN_SINIESTROS].sort_values("median").reset_index()
    g4 = px.scatter(edad_g, x="median", y="LOCALIDAD", size="count", height=620,
                    labels={"median": "Edad mediana", "count": "Personas", "LOCALIDAD": ""})
    g4.update_traces(marker=dict(color="#38e8ff", sizemin=8))
    g4.update_layout(xaxis_title="Edad mediana (años)", yaxis_title="")

    # ---------------- Tabla resumen ----------------
    tabla = []
    for loc, n in conteo.items():
        mediana = edad["median"].get(loc)
        tabla.append({
            "localidad": loc,
            "siniestros": f"{int(n):,}",
            "participacion": f"{n / max(total, 1) * 100:.1f}%",
            "edad": "-" if mediana != mediana or mediana is None else f"{mediana:.0f}",
        })

    return render_template(
        "territorial.html",
        gravedades=sorted(siniestros["GRAVEDAD_TXT"].dropna().unique()),
        anios=[int(x) for x in sorted(siniestros["ANIO"].dropna().unique())],
        sel_grav=sel_grav,
        sel_anio=sel_anio,
        ind_total=f"{total:,}",
        ind_territorios=int(conteo.size),
        ind_top=top_nombre,
        ind_top_valor=f"{top_valor:,}",
        ind_pct_top5=pct_top5,
        min_siniestros=MIN_SINIESTROS,
        tabla=tabla,
        grafica1=_html(g1),
        grafica2=_html(g2),
        grafica3=_html(g3),
        grafica4=_html(g4),
    )