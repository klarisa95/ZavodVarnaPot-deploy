import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output, State, ctx

# ── paths ──────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
DATA_PATH    = os.path.join(BASE_DIR, "data_izpis.csv")
GEOJSON_PATH = os.path.join(BASE_DIR, "OB.geojson")

app = Dash(__name__, title="Zavod Varna Pot")
server = app.server

# ── static data ────────────────────────────────────────────────────────────────
with open(GEOJSON_PATH, encoding="utf-8") as f:
    GEOJSON = json.load(f)

# three municipalities whose capitalisation differs between the CSV and GeoJSON
NAME_FIXES = {
    "Sveta Trojica v Slovenskih Goricah": "Sveta Trojica v Slovenskih goricah",
    "Sveti Andraž v Slov. Goricah":       "Sveti Andraž v Slov. goricah",
    "Sveti Jurij v Slovenskih Goricah":   "Sveti Jurij v Slovenskih goricah",
}

# step scale: 0 → zelena, 1 → rumena, 2 → rdeča  (range_color=[0, 2])
COLOR_SCALE = [
    (0.0,   "#52b788"), (0.333, "#52b788"),
    (0.334, "#f4a261"), (0.666, "#f4a261"),
    (0.667, "#e63946"), (1.0,   "#e63946"),
]

DF         = pd.read_csv(DATA_PATH, index_col=0)
ALL_YEARS  = sorted(DF["leto"].unique().tolist())
COLORS     = {"Nizka": "#52b788", "Srednja": "#f4a261", "Visoka": "#e63946"}
ALL_LEVELS = ["Nizka", "Srednja", "Visoka"]

# ── helpers ────────────────────────────────────────────────────────────────────
def compute_stopnja(df_in):
    df   = df_in.copy()
    df["Občina"] = df["Občina"].replace(NAME_FIXES)
    preb = df["Število prebivalcev"].replace(0, float("nan"))
    df["Stopnja"]  = df["index"].apply(
        lambda v: "Nizka" if v == 0 else ("Srednja" if v == 1 else "Visoka")
    )
    return df


def build_map(df_leto):
    fig = px.choropleth_mapbox(
        df_leto,
        geojson=GEOJSON,
        featureidkey="properties.OB_UIME",
        locations="Občina",
        color="index",
        color_continuous_scale=COLOR_SCALE,
        range_color=[0, 2],
        zoom=8,
        center={"lat": 46.12, "lon": 14.95},
        mapbox_style="carto-positron",
        hover_name="Občina",
        hover_data={"index": ":.2f", "Stopnja": True, "Občina": False},
        labels={"index": "Vrednost", "Stopnja": "Stopnja"},
    )
    fig.update_traces(marker_line_width=0.4, marker_line_color="#888")
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        coloraxis_showscale=False,
        uirevision="map",
        dragmode=False,
    )
    return fig


# ── layout helpers ─────────────────────────────────────────────────────────────
def stat_card(value, label, color="#333", dot=False):
    num_children = (
        [html.Span("● ", style={"color": color, "fontSize": "20px"}), str(value)]
        if dot else str(value)
    )
    return html.Div([
        html.Div(num_children, style={"fontSize": "30px", "fontWeight": "700", "color": color}),
        html.Div(label, style={"fontSize": "12px", "color": "#777", "marginTop": "3px"}),
    ], style={
        "background": "#f5f5f5", "borderRadius": "10px",
        "padding": "16px 8px", "textAlign": "center", "border": "1px solid #eee",
    })


def pill_btn(label, btn_id, dot_color, active=True):
    suffix = {"#4caf50": "green", "#f0a500": "amber", "#e53935": "red"}[dot_color]
    return html.Button(
        [html.Span("●", className="dot"), f" {label}"],
        id=btn_id,
        className=f"pill pill-{suffix}" + (" active" if active else ""),
        n_clicks=0,
    )


# ── layout ─────────────────────────────────────────────────────────────────────
app.layout = html.Div(
    style={"display": "flex", "height": "100vh", "margin": "0"},
    children=[

        # ── LEFT PANEL ────────────────────────────────────────────────────────
        html.Div(
            style={
                "width": "440px", "flexShrink": "0",
                "overflowY": "auto", "height": "100vh",
                "padding": "14px 16px", "borderRight": "1px solid #e0e0e0",
            },
            children=[

                html.Div(
                    style={
                        "background": "#181a2e", "borderRadius": "10px",
                        "padding": "20px 16px 16px", "marginBottom": "10px",
                    },
                    children=[
                        html.Div(
                            "Analiza posledic prometnih nesreč",
                            style={"fontSize": "20px", "fontWeight": "700",
                                   "color": "#c8b000", "lineHeight": "1.35"},
                        ),
                        html.Div(id="header-year",
                                 style={"fontSize": "12px", "color": "#aaa", "marginTop": "5px"}),
                        html.Details(
                            style={"marginTop": "12px", "borderTop": "1px solid #2e3150",
                                   "paddingTop": "4px"},
                            children=[
                                html.Summary("O metodologiji",
                                             style={"cursor": "pointer", "padding": "6px 0",
                                                    "fontWeight": "600", "fontSize": "13px",
                                                    "color": "#ccc"}),
                                html.Div(
                                    style={"padding": "6px 0 4px", "fontSize": "12px",
                                           "color": "#aaa", "lineHeight": "1.6"},
                                    children=[
                                        html.P("S posameznikovo odločitvijo za sprejem in identifikacijo s cilji Vizije NIČ ter konkretnim udejanjanjem je narejen prvi in najpomembnejši korak. Rezultati se bodo kot prvi začeli izkazovati v okolju kjer živimo ali delamo, to je v naših lokalnih skupnostih."),
                                        html.P("Metodologija uspešnosti zasledovanja ciljev je razmerje med številom umrlih in hudo telesno poškodovanih glede na 10.000 prebivalcev."),
                                        html.P("Izraža se v 3 razrednih stopnjah obarvano z zeleno, rumeno in rdečo barvo, pri čemer je zelena (dosežen cilj Vizije NIČ), rumena (srednja vrednost do cilja), rdeča (nad srednjo vrednostjo od cilja)."),
                                        html.P("Obdelavo podatkov za posamezno občino v različnih obdobjih izvaja podjetje Solvesall d.o.o. pod vodstvom dr. Luka Bradeška."),
                                        html.P("Za njihov strokovni prispevek udejanjanju Vizije NIČ se iskreno zahvaljujemo.",
                                               style={"fontStyle": "italic"}),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),


                dcc.Dropdown(
                    id="year-dd",
                    options=[{"label": str(y), "value": y} for y in ALL_YEARS],
                    value=ALL_YEARS[-1],
                    clearable=False,
                    searchable=False,
                    className="year-dd",
                    style={"marginBottom": "10px"},
                ),

                html.Div(id="stats-cards"),

                html.Div(
                    style={"margin": "4px 0 14px"},
                    children=[
                        html.Div(
                            style={"display": "flex", "height": "10px",
                                   "borderRadius": "5px", "overflow": "hidden", "marginBottom": "6px"},
                            children=[
                                html.Div(style={"flex": "1", "background": "#52b788"}),
                                html.Div(style={"flex": "1", "background": "#f4a261"}),
                                html.Div(style={"flex": "1", "background": "#e63946"}),
                            ],
                        ),
                        html.Div(style={"display": "flex", "marginBottom": "8px"}, children=[
                            html.Div([
                                html.Div("0 – 2", style={"fontSize": "12px", "fontWeight": "600", "color": "#333"}),
                                html.Div("Nizka", style={"fontSize": "10px", "fontWeight": "700",
                                                          "color": "#52b788", "textTransform": "uppercase"}),
                            ], style={"flex": "1", "textAlign": "center"}),
                            html.Div([
                                html.Div("2 – 4", style={"fontSize": "12px", "fontWeight": "600", "color": "#333"}),
                                html.Div("Srednja", style={"fontSize": "10px", "fontWeight": "700",
                                                            "color": "#f4a261", "textTransform": "uppercase"}),
                            ], style={"flex": "1", "textAlign": "center"}),
                            html.Div([
                                html.Div("4 +", style={"fontSize": "12px", "fontWeight": "600", "color": "#333"}),
                                html.Div("Visoka", style={"fontSize": "10px", "fontWeight": "700",
                                                           "color": "#e63946", "textTransform": "uppercase"}),
                            ], style={"flex": "1", "textAlign": "center"}),
                        ]),
                        html.Div(
                            [html.Strong("Vrednost"),
                             " = št. smrti / 10.000 preb. + 0,8 × št. hudih telesnih poškodb / 10.000 preb."],
                            style={"fontSize": "11px", "color": "#888"},
                        ),
                    ],
                ),

                html.Div("SEZNAM OBČIN", style={
                    "fontSize": "12px", "fontWeight": "800", "letterSpacing": "1.5px",
                    "color": "#333", "margin": "4px 0 10px",
                    "borderTop": "1px solid #ddd", "paddingTop": "12px",
                }),

                dcc.Store(id="level-store", data=ALL_LEVELS),
                html.Div(
                    style={"display": "flex", "gap": "8px", "marginBottom": "10px", "flexWrap": "wrap"},
                    children=[
                        pill_btn("Nizka",   "btn-n", "#4caf50"),
                        pill_btn("Srednja", "btn-s", "#f0a500"),
                        pill_btn("Visoka",  "btn-v", "#e53935"),
                    ],
                ),

                dcc.Input(
                    id="search", type="text",
                    placeholder="🔍  Vpišite ime občine...",
                    debounce=True,
                    style={
                        "width": "100%", "padding": "8px 12px",
                        "border": "1.5px solid #ddd", "borderRadius": "6px",
                        "fontSize": "13px", "marginBottom": "10px", "outline": "none",
                    },
                ),

                html.Div(id="muni-table", className="muni-table",
                         style={"height": "350px", "overflowY": "auto",
                                "border": "1.5px solid #ddd", "borderRadius": "8px"}),

                html.Div(id="muni-count",
                         style={"fontSize": "12px", "color": "#888", "margin": "6px 0 0 2px"}),

                html.Div("PORAZDELITEV", style={
                    "fontSize": "12px", "fontWeight": "800", "letterSpacing": "1.5px",
                    "color": "#333", "margin": "16px 0 4px",
                    "borderTop": "1px solid #ddd", "paddingTop": "12px",
                }),
                dcc.Graph(id="dist-chart", config={"displayModeBar": False},
                          style={"height": "180px", "marginBottom": "4px"}),

                # footer logos
                html.Div(
                    style={
                        "borderTop": "1px solid #ddd", "paddingTop": "14px",
                        "marginBottom": "20px",
                    },
                    children=[
                        html.Div(
                            style={"display": "flex", "alignItems": "center",
                                   "justifyContent": "center", "gap": "12px",
                                   "marginBottom": "8px"},
                            children=[
                                html.Img(src="/assets/zavod-varna-pot-logo.svg",
                                         style={"height": "40px"}),
                                html.Img(src="/assets/solvesall.svg",
                                         style={"height": "32px"}),
                            ],
                        ),
                        html.Div(id="footer-year",
                                 style={"textAlign": "center", "fontSize": "11px",
                                        "color": "#999"}),
                    ],
                ),
            ],
        ),

        # ── RIGHT PANEL – choropleth map ──────────────────────────────────────
        dcc.Graph(
            id="map-graph",
            config={"scrollZoom": True, "displayModeBar": False},
            style={"flex": "1", "height": "100vh"},
        ),

        # dummy sink for the clientside callback below
        html.Div(id="_map-lock", style={"display": "none"}),
    ],
)

# ── callbacks ──────────────────────────────────────────────────────────────────

# After every map render, reach into the Maplibre GL instance and
# disable all interaction handlers so the map stays locked.
app.clientside_callback(
    """
    function(figure) {
        if (!figure) return '';
        setTimeout(function () {
            var el = document.getElementById('map-graph');
            if (!el || !el._fullLayout) return;
            try {
                var m = el._fullLayout.map._subplot._map;
                if (!m) return;
                m.dragPan.disable();
                m.touchZoomRotate.disable();
                m.boxZoom.disable();
                m.keyboard.disable();
            } catch (e) {}
        }, 400);
        return '';
    }
    """,
    Output("_map-lock", "children"),
    Input("map-graph", "figure"),
)


@app.callback(
    Output("level-store", "data"),
    Output("btn-n", "className"),
    Output("btn-s", "className"),
    Output("btn-v", "className"),
    Input("btn-n", "n_clicks"),
    Input("btn-s", "n_clicks"),
    Input("btn-v", "n_clicks"),
    State("level-store", "data"),
    prevent_initial_call=True,
)
def toggle_level(n1, n2, n3, active):
    triggered = ctx.triggered_id
    mapping = {"btn-n": "Nizka", "btn-s": "Srednja", "btn-v": "Visoka"}
    level = mapping[triggered]
    active = list(active)
    if level in active:
        active.remove(level)
    else:
        active.append(level)

    def cls(lvl):
        suffix = {"Nizka": "green", "Srednja": "amber", "Visoka": "red"}[lvl]
        return f"pill pill-{suffix}" + (" active" if lvl in active else "")

    return active, cls("Nizka"), cls("Srednja"), cls("Visoka")


@app.callback(
    Output("map-graph", "figure"),
    Input("year-dd",    "value"),
)
def update_map(leto):
    df_leto = compute_stopnja(DF[DF["leto"] == leto])
    return build_map(df_leto)


@app.callback(
    Output("header-year",  "children"),
    Output("stats-cards",  "children"),
    Output("muni-table",   "children"),
    Output("muni-count",   "children"),
    Output("dist-chart",   "figure"),
    Output("footer-year",  "children"),
    Input("year-dd",      "value"),
    Input("level-store",  "data"),
    Input("search",       "value"),
)
def update_ui(leto, active_levels, search):
    active_levels = active_levels or []

    subtitle = f"Vizija NIČ · Podatki {leto}"

    df_leto   = compute_stopnja(DF[DF["leto"] == leto])
    n_total   = len(df_leto)
    n_nizka   = int((df_leto["Stopnja"] == "Nizka").sum())
    n_srednja = int((df_leto["Stopnja"] == "Srednja").sum())
    n_visoka  = int((df_leto["Stopnja"] == "Visoka").sum())

    cards = html.Div([
        stat_card(n_total,   "Skupaj občin"),
        stat_card(n_nizka,   "Nizka",   COLORS["Nizka"],   dot=True),
        stat_card(n_srednja, "Srednja", COLORS["Srednja"], dot=True),
        stat_card(n_visoka,  "Visoka",  COLORS["Visoka"],  dot=True),
    ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
              "gap": "10px", "margin": "12px 0 14px"})

    df_f = (
        df_leto[df_leto["Stopnja"].isin(active_levels)][["Občina", "Stopnja"]]
        .sort_values("Občina").reset_index(drop=True)
    )
    if search:
        df_f = df_f[df_f["Občina"].str.contains(search, case=False, na=False)]

    header = html.Div(
        [html.Div("Občina", className="muni-name"),
         html.Div("Stopnja", className="muni-level")],
        className="muni-header",
    )
    rows = [header]
    for _, row in df_f.iterrows():
        c = COLORS[row["Stopnja"]]
        rows.append(html.Div([
            html.Div(row["Občina"], className="muni-name"),
            html.Div([html.Span("● ", style={"color": c}), row["Stopnja"]],
                     className="muni-level", style={"color": c}),
        ], className="muni-row"))
    table = html.Div(rows)
    count = f"Prikazanih {len(df_f)} od {n_total} občin"

    max_y = max(n_nizka, n_srednja, n_visoka, 1)
    bar = go.Figure(go.Bar(
        x=["Nizka", "Srednja", "Visoka"],
        y=[n_nizka, n_srednja, n_visoka],
        marker_color=[COLORS["Nizka"], COLORS["Srednja"], COLORS["Visoka"]],
        text=[n_nizka, n_srednja, n_visoka],
        textposition="outside",
        width=0.5,
    ))
    bar.update_layout(
        margin={"l": 10, "r": 10, "t": 20, "b": 30},
        paper_bgcolor="white", plot_bgcolor="white",
        showlegend=False, height=160,
        yaxis={"visible": False, "range": [0, max_y * 1.25]},
        xaxis={"showgrid": False, "tickfont": {"size": 13}},
    )

    footer = f"Podatki za leto {leto} · Slovenija"
    return subtitle, cards, table, count, bar, footer


if __name__ == "__main__":
    app.run(debug=True, port=8050)
