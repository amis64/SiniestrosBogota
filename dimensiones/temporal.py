import pandas as pd
import plotly.express as px
from flask import Blueprint, render_template, request
from datos import siniestros
 
bp = Blueprint("temporal", __name__)
 
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
FRANJAS = ["Madrugada (0-5 h)", "Mañana (6-11 h)", "Tarde (12-17 h)", "Noche (18-23 h)"]
 
 
def _html(fig):
    return fig.to_html(full_html=False, include_plotlyjs=False)
 
 
@bp.route("/temporal")
def temporal():
    sel_grav = request.args.get("gravedad", "Todas")
    sel_loc = request.args.get("localidad", "Todas")
 
    base = siniestros                 # filtrada solo por localidad
    if sel_loc != "Todas":
        base = base[base["LOCALIDAD"] == sel_loc]
 
    d = base                          # filtrada por localidad y gravedad
    if sel_grav != "Todas":
        d = d[d["GRAVEDAD_TXT"] == sel_grav]
 
    # Series base
    mensual = (d.groupby(d["FECHA"].dt.to_period("M")).size()
               .reindex(pd.period_range("2015-01", "2020-12", freq="M"), fill_value=0))
    anual = d.groupby("ANIO").size().reindex(range(2015, 2021), fill_value=0)
 
    # Indicadores
    total = int(len(d))
    promedio_mensual = round(total / 72)
    mes_pico = mensual.idxmax()
    mes_pico_txt = f"{MESES[mes_pico.month - 1]} {mes_pico.year}" if total else "-"
    var_2020 = (round((anual[2020] / anual[2019] - 1) * 100, 1) if anual[2019] else None)
 
    # Gráfica 1: evolución mensual 2015-2020
    t1 = pd.DataFrame({"mes": mensual.index.to_timestamp(), "siniestros": mensual.values})
    g1 = px.line(t1, x="mes", y="siniestros", markers=True, height=420)
    g1.add_vrect(x0="2020-03-01", x1="2020-08-31", fillcolor="#ff4fa3", opacity=0.12, line_width=0,
                 annotation_text="Aislamiento obligatorio 2020", annotation_position="top left",
                 annotation_font_color="#ff4fa3")
    g1.update_layout(xaxis_title="", yaxis_title="Siniestros por mes", hovermode="x unified")
 
    # Gráfica 2: comparación mes a mes entre años
    t2 = d.groupby(["ANIO", "MES"]).size().reset_index(name="siniestros")
    t2["mes_txt"] = t2["MES"].map(lambda m: MESES[m - 1])
    t2["ANIO"] = t2["ANIO"].astype(str)
    g2 = px.line(t2, x="mes_txt", y="siniestros", color="ANIO", markers=True, height=420,
                 category_orders={"mes_txt": MESES}, labels={"ANIO": "Año", "mes_txt": "Mes"})
    g2.update_layout(xaxis_title="", yaxis_title="Siniestros", hovermode="x unified")
 
    # Gráfica 3: mapa de calor día de la semana x hora
    t3 = (d.groupby(["DIA_SEMANA", "HORA_NUM"]).size().unstack(fill_value=0)
          .reindex(index=DIAS, columns=range(24), fill_value=0))
    g3 = px.imshow(t3, aspect="auto", height=420, color_continuous_scale="Viridis",
                   labels={"x": "Hora del día", "y": "", "color": "Siniestros"})
    g3.update_xaxes(dtick=1)
 
    # Gráfica 4: % de siniestros con muertos por franja horaria
    # Usa 'base' (sin filtrar por gravedad) porque la gravedad es la variable que se mide.
    franja = pd.cut(base["HORA_NUM"], bins=[-1, 5, 11, 17, 23], labels=FRANJAS)
    g_fr = (base.assign(franja=franja, muerto=base["GRAVEDAD"] == 1)
            .groupby("franja", observed=False)["muerto"].agg(["size", "sum"]))
    promedio = g_fr["sum"].sum() / max(g_fr["size"].sum(), 1) * 100
    g_fr["pct"] = (g_fr["sum"] / g_fr["size"].where(g_fr["size"] > 0) * 100).round(2)
    t4 = g_fr.rename_axis("franja").reset_index()
    g4 = px.bar(t4, x="franja", y="pct", text="pct", height=420,
                hover_data={"sum": True, "size": True, "pct": ":.2f"},
                labels={"franja": "", "pct": "% con muertos", "sum": "Siniestros con muertos",
                        "size": "Total siniestros"})
    g4.update_traces(texttemplate="%{text:.2f}%", textposition="outside", cliponaxis=False,
                     marker_color="#ff4fa3")
    g4.add_hline(y=promedio, line_dash="dash", line_color="#c6ff3d",
                 annotation_text=f"Promedio: {promedio:.2f}%", annotation_font_color="#c6ff3d")
    g4.update_layout(yaxis_title="% de siniestros con muertos")
 
    # Tabla resumen anual
    muertos_anio = base[base["GRAVEDAD"] == 1].groupby("ANIO").size()
    total_anio_base = base.groupby("ANIO").size()
    tabla = []
    anterior = None
    for anio, n in anual.items():
        var = "-" if not anterior else f"{(n / anterior - 1) * 100:+.1f}%"
        tb = total_anio_base.get(anio, 0)
        tabla.append({
            "anio": anio,
            "siniestros": f"{int(n):,}",
            "variacion": var,
            "promedio_mes": f"{n / 12:,.0f}",
            "pct_muertos": f"{muertos_anio.get(anio, 0) / tb * 100:.2f}%" if tb else "-",
        })
        anterior = n
 
    return render_template(
        "temporal.html",
        gravedades=sorted(siniestros["GRAVEDAD_TXT"].dropna().unique()),
        localidades=sorted(siniestros["LOCALIDAD"].dropna().unique()),
        sel_grav=sel_grav,
        sel_loc=sel_loc,
        ind_total=f"{total:,}",
        ind_promedio=f"{promedio_mensual:,}",
        ind_mes_pico=mes_pico_txt,
        ind_mes_pico_valor=f"{int(mensual.max()):,}",
        ind_var_2020="-" if var_2020 is None else f"{var_2020:+.1f}%",
        tabla=tabla,
        grafica1=_html(g1),
        grafica2=_html(g2),
        grafica3=_html(g3),
        grafica4=_html(g4),
    )