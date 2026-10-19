"""Plotly figure builders for the Area 139 dashboard (dark, transparent, hover-rich)."""
import pandas as pd
import plotly.graph_objects as go

FONT = dict(family="Plus Jakarta Sans, system-ui, sans-serif", color="#cbd5e1", size=13)
GRID = "rgba(255,255,255,.06)"
AMBER, VIOLET, SKY, EMERALD, ROSE = "#fbbf24", "#a78bfa", "#38bdf8", "#34d399", "#fb7185"
BG = "#0b1220"


def _hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(hex_color, other="#0b1220", t=0.0):
    """Blend hex_color towards `other` by t (0 = original, 1 = other)."""
    a, b = _hex_rgb(hex_color), _hex_rgb(other)
    return "#%02x%02x%02x" % tuple(round(a[i] * (1 - t) + b[i] * t) for i in range(3))


def rgba(hex_color, alpha):
    r, g, b = _hex_rgb(hex_color)
    return f"rgba({r},{g},{b},{alpha})"


def base(fig, height=360, **layout):
    opts = dict(
        height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=FONT,
        margin=dict(l=14, r=14, t=34, b=14),
        hoverlabel=dict(bgcolor=BG, bordercolor="rgba(251,191,36,.55)", font=dict(family=FONT["family"], color="#f8fafc", size=13)),
        legend=dict(orientation="h", y=1.12, x=0, bgcolor="rgba(0,0,0,0)"),
    )
    opts.update(layout)  # caller overrides win (no duplicate-keyword errors)
    fig.update_layout(**opts)
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor="rgba(255,255,255,.1)")
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor="rgba(255,255,255,.1)")
    return fig


def category_bar(by_cat: pd.DataFrame, colors: dict, selected=None):
    """Horizontal bars, one per category. Clickable (Streamlit on_select)."""
    d = by_cat.sort_values("downloads", ascending=True)
    cols = [colors[c] for c in d["category"]]
    opac = [1.0 if (not selected or c in selected) else 0.28 for c in d["category"]]
    fig = go.Figure(go.Bar(
        x=d["downloads"], y=d["category"], orientation="h",
        marker=dict(color=cols, opacity=opac, line=dict(width=0)),
        text=[f"{v:,}" for v in d["downloads"]], textposition="outside", cliponaxis=False,
        textfont=dict(color="#e2e8f0", family="Space Grotesk, sans-serif", size=14),
        customdata=d["posts"],
        hovertemplate="<b>%{y}</b><br>%{x:,} downloads<br>%{customdata} notes<extra></extra>",
    ))
    base(fig, height=max(300, 56 * len(d) + 60), bargap=0.32, margin=dict(l=14, r=60, t=20, b=14))
    fig.update_yaxes(showgrid=False, automargin=True)
    fig.update_xaxes(showticklabels=False, showgrid=False)
    return fig


def category_donut(by_cat: pd.DataFrame, colors: dict):
    d = by_cat.sort_values("downloads", ascending=False)
    total = int(d["downloads"].sum())
    fig = go.Figure(go.Pie(
        labels=d["category"], values=d["downloads"], hole=0.7, sort=False, direction="clockwise",
        marker=dict(colors=[colors[c] for c in d["category"]], line=dict(color="#030712", width=3)),
        textinfo="none", pull=[0.02] * len(d),
        hovertemplate="<b>%{label}</b><br>%{value:,} downloads<br>%{percent}<extra></extra>",
    ))
    base(fig, height=max(300, 56 * len(d) + 60), showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
    fig.add_annotation(text=f"<b style='font-size:30px;color:#fff'>{total:,}</b><br><span style='color:#94a3b8;font-size:12px'>downloads</span>",
                       x=0.5, y=0.5, showarrow=False, font=dict(family="Space Grotesk, sans-serif"))
    return fig


def treemap(df: pd.DataFrame, colors: dict):
    """Library -> category -> note, sized by downloads. Click a tile to zoom in."""
    d = df[df["download_count"] > 0]
    ids, labels, parents, values, cols = ["Library"], ["Library"], [""], [0], ["rgba(0,0,0,0)"]
    total = 0
    for cat, grp in d.groupby("category"):
        grp = grp.sort_values("download_count", ascending=False)
        cat_total = int(grp["download_count"].sum())
        total += cat_total
        ids.append(f"c::{cat}"); labels.append(cat); parents.append("Library"); values.append(cat_total)
        cols.append(mix(colors[cat], t=0.05))
        n = max(len(grp) - 1, 1)
        for rank, (_, r) in enumerate(grp.iterrows()):
            ids.append(f"n::{cat}::{r['title']}::{rank}")
            labels.append(str(r["title"])); parents.append(f"c::{cat}"); values.append(int(r["download_count"]))
            cols.append(mix(colors[cat], t=0.25 + 0.4 * rank / n))
    values[0] = total
    fig = go.Figure(go.Treemap(
        ids=ids, labels=labels, parents=parents, values=values, branchvalues="total",
        marker=dict(colors=cols, line=dict(width=2, color="#030712"), cornerradius=6),
        texttemplate="<b>%{label}</b><br>%{value:,}", textfont=dict(family=FONT["family"], color="#0b1220", size=14),
        hovertemplate="<b>%{label}</b><br>%{value:,} downloads<br>%{percentParent:.0%} of %{parent}<extra></extra>",
        pathbar=dict(visible=True, thickness=26, textfont=dict(color="#e2e8f0")), tiling=dict(pad=3),
    ))
    return base(fig, height=470, margin=dict(l=8, r=8, t=8, b=8))


def growth_combo(df: pd.DataFrame):
    """New notes per month (bars) + running total (line)."""
    d = df.dropna(subset=["created_at"])
    if d.empty:
        return None
    month = d["created_at"].dt.tz_convert(None).dt.to_period("M")
    cnt = d.groupby(month).size().sort_index()
    x = [p.to_timestamp() for p in cnt.index]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x, y=cnt.values, name="New notes", marker=dict(color=rgba(AMBER, .85), line=dict(width=0)),
                         hovertemplate="%{x|%b %Y}<br><b>%{y}</b> new notes<extra></extra>"))
    fig.add_trace(go.Scatter(x=x, y=cnt.cumsum().values, name="Library size", yaxis="y2", mode="lines+markers",
                             line=dict(color=VIOLET, width=3, shape="spline"), marker=dict(size=8, color=VIOLET, line=dict(width=2, color="#030712")),
                             hovertemplate="%{x|%b %Y}<br>Total <b>%{y}</b> notes<extra></extra>"))
    base(fig, height=340, bargap=0.35, hovermode="x unified",
         yaxis2=dict(overlaying="y", side="right", showgrid=False, zeroline=False))
    return fig


def traffic_area(daily: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily["date"], y=daily["sessions"], name="Sessions", mode="lines",
                             line=dict(color=VIOLET, width=2.5, shape="spline"), fill="tozeroy", fillcolor=rgba(VIOLET, .14)))
    fig.add_trace(go.Scatter(x=daily["date"], y=daily["activeUsers"], name="Visitors", mode="lines+markers",
                             line=dict(color=AMBER, width=3, shape="spline"), marker=dict(size=6, color=AMBER),
                             fill="tozeroy", fillcolor=rgba(AMBER, .16)))
    base(fig, height=400, hovermode="x unified",
         xaxis=dict(rangeslider=dict(visible=True, thickness=0.07, bgcolor="rgba(255,255,255,.04)")))
    return fig


def world_map(countries: pd.DataFrame):
    d = countries[~countries["country"].str.contains("not set", case=False, na=False)]
    fig = go.Figure(go.Choropleth(
        locations=d["country"], locationmode="country names", z=d["activeUsers"],
        colorscale=[[0, "#1e293b"], [0.15, "#78350f"], [0.55, "#f59e0b"], [1, "#fef3c7"]],
        marker=dict(line=dict(color="#030712", width=0.6)),
        colorbar=dict(title=dict(text="Visitors", font=dict(color="#94a3b8")), thickness=10, len=0.6, tickfont=dict(color="#94a3b8"), outlinewidth=0),
        hovertemplate="<b>%{location}</b><br>%{z:,} visitors<extra></extra>",
    ))
    base(fig, height=400, margin=dict(l=0, r=0, t=0, b=0))
    fig.update_geos(bgcolor="rgba(0,0,0,0)", showframe=False, showcoastlines=False, showland=True, landcolor="#111827",
                    showocean=False, showcountries=True, countrycolor="rgba(255,255,255,.07)", projection_type="natural earth")
    return fig


def country_bar(countries: pd.DataFrame, top: int = 10):
    """Top countries as horizontal bars - sits next to the world map."""
    total = float(countries["activeUsers"].sum()) or 1.0
    d = countries[~countries["country"].str.contains("not set", case=False, na=False)]
    d = d.sort_values("activeUsers", ascending=False).head(top).sort_values("activeUsers", ascending=True)
    fig = go.Figure(go.Bar(
        x=d["activeUsers"], y=d["country"], orientation="h",
        marker=dict(color=d["activeUsers"], colorscale=[[0, "#78350f"], [0.5, "#f59e0b"], [1, "#fde68a"]], line=dict(width=0)),
        text=[f"{v:,}" for v in d["activeUsers"]], textposition="outside", cliponaxis=False,
        textfont=dict(color="#e2e8f0", family="Space Grotesk, sans-serif", size=14),
        customdata=[v / total * 100 for v in d["activeUsers"]],
        hovertemplate="<b>%{y}</b><br>%{x:,} visitors<br>%{customdata:.1f}% of all visitors<extra></extra>",
    ))
    base(fig, height=400, bargap=0.3, margin=dict(l=10, r=55, t=10, b=10))
    fig.update_yaxes(showgrid=False, automargin=True)
    fig.update_xaxes(showticklabels=False, showgrid=False)
    return fig


def donut(labels, values, colors=None, height=300):
    cols = colors or [AMBER, SKY, VIOLET, EMERALD, ROSE]
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.62, sort=False,
                           marker=dict(colors=cols[:len(labels)], line=dict(color="#030712", width=3)),
                           textinfo="percent", textfont=dict(color="#0b1220", size=13),
                           hovertemplate="<b>%{label}</b><br>%{value:,}<br>%{percent}<extra></extra>"))
    base(fig, height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center"))
    return fig
