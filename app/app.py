"""
app.py  —  Real-time World Cup Sentiment Tracker (fixed)
"""

import datetime
import threading
import logging

import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
import pandas as pd

from simulator import tweet_stream
from sentiment  import analyze
from state      import store, SentimentRecord

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

COLORS = {
    "Positive": "#00e676",
    "Neutral":  "#ffca28",
    "Negative": "#ff1744",
    "bg":       "#0a0e1a",
    "surface":  "#111827",
    "text":     "#e2e8f0",
    "muted":    "#64748b",
    "accent":   "#38bdf8",
}

# ---------------------------------------------------------------------------
# Background simulator thread
# ---------------------------------------------------------------------------

def _run_simulator():
    logger.info("Simulator thread starting ...")
    for tweet in tweet_stream():
        result = analyze(tweet)
        record = SentimentRecord(
            timestamp  = datetime.datetime.utcnow().isoformat(timespec="seconds"),
            tweet      = tweet[:140],
            label      = result["label"],
            confidence = result["confidence"],
            score      = result["score"],
        )
        store.append(record)


def start_simulator():
    t = threading.Thread(target=_run_simulator, name="SimulatorThread", daemon=True)
    t.start()
    logger.info("Simulator thread started (id=%d)", t.ident)


# ---------------------------------------------------------------------------
# Dash app
# ---------------------------------------------------------------------------

app = dash.Dash(
    __name__,
    title="World Cup Sentiment Tracker",
    update_title=None,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server

app.layout = html.Div(
    style={"backgroundColor": COLORS["bg"], "minHeight": "100vh",
           "fontFamily": "Inter, sans-serif"},
    children=[
        html.Div(
            style={"padding": "2rem 3rem 1rem",
                   "borderBottom": "1px solid #111827"},
            children=[
                html.H1("World Cup Sentiment Tracker",
                        style={"color": COLORS["text"], "margin": 0,
                               "fontSize": "1.6rem", "fontWeight": "700"}),
                html.P("Real-time NLP sentiment analysis on match-day Twitter chatter",
                       style={"color": COLORS["muted"], "margin": "0.25rem 0 0",
                              "fontSize": "0.9rem"}),
            ],
        ),
        html.Div(id="kpi-row",
                 style={"display": "flex", "gap": "1rem", "padding": "1.5rem 3rem"}),
        html.Div(
            style={"padding": "0 3rem"},
            children=[html.Div(
                style={"backgroundColor": COLORS["surface"], "borderRadius": "12px",
                       "padding": "1.5rem"},
                children=[
                    html.H3("Sentiment Over Time",
                            style={"color": COLORS["text"], "margin": "0 0 1rem",
                                   "fontSize": "1rem", "fontWeight": "600"}),
                    dcc.Graph(id="sentiment-timeline",
                              config={"displayModeBar": False},
                              style={"height": "340px"}),
                ],
            )],
        ),
        html.Div(
            style={"display": "flex", "gap": "1rem", "padding": "1.5rem 3rem"},
            children=[
                html.Div(
                    style={"flex": "0 0 340px", "backgroundColor": COLORS["surface"],
                           "borderRadius": "12px", "padding": "1.5rem"},
                    children=[
                        html.H3("Distribution",
                                style={"color": COLORS["text"], "margin": "0 0 1rem",
                                       "fontSize": "1rem", "fontWeight": "600"}),
                        dcc.Graph(id="sentiment-pie",
                                  config={"displayModeBar": False},
                                  style={"height": "260px"}),
                    ],
                ),
                html.Div(
                    style={"flex": "1", "backgroundColor": COLORS["surface"],
                           "borderRadius": "12px", "padding": "1.5rem",
                           "overflowY": "auto", "maxHeight": "320px"},
                    children=[
                        html.H3("Latest Tweets",
                                style={"color": COLORS["text"], "margin": "0 0 1rem",
                                       "fontSize": "1rem", "fontWeight": "600"}),
                        html.Div(id="tweet-feed"),
                    ],
                ),
            ],
        ),
        dcc.Interval(id="interval", interval=3000, n_intervals=0),
    ],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _kpi_card(label, value, color):
    return html.Div(
        style={"flex": "1", "backgroundColor": COLORS["surface"],
               "borderRadius": "12px", "padding": "1.25rem 1.5rem",
               "borderLeft": "4px solid " + color},
        children=[
            html.P(label, style={"color": COLORS["muted"], "margin": "0 0 0.25rem",
                                 "fontSize": "0.75rem", "textTransform": "uppercase",
                                 "letterSpacing": "0.08em"}),
            html.P(value, style={"color": COLORS["text"], "margin": 0,
                                 "fontSize": "1.6rem", "fontWeight": "700"}),
        ],
    )


def _empty_fig(msg="Waiting for data..."):
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": COLORS["text"]},
        xaxis={"visible": False},
        yaxis={"visible": False},
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        annotations=[{
            "text": msg,
            "showarrow": False,
            "xref": "paper",
            "yref": "paper",
            "x": 0.5,
            "y": 0.5,
            "font": {"color": COLORS["muted"], "size": 14},
        }],
    )
    return fig


# ---------------------------------------------------------------------------
# Callback
# ---------------------------------------------------------------------------

@callback(
    Output("kpi-row",            "children"),
    Output("sentiment-timeline", "figure"),
    Output("sentiment-pie",      "figure"),
    Output("tweet-feed",         "children"),
    Input("interval",            "n_intervals"),
)
def update_dashboard(n):
    try:
        records = store.get_all()
    except Exception as exc:
        logger.error("store read failed: %s", exc)
        records = []

    if not records:
        msg = html.P("Model loading - first tweets arriving soon...",
                     style={"color": COLORS["muted"], "fontSize": "0.85rem"})
        return [], _empty_fig("Loading..."), _empty_fig(), msg

    df = pd.DataFrame([
        {"ts": r.timestamp, "label": r.label,
         "score": r.score, "conf": r.confidence, "tweet": r.tweet}
        for r in records
    ])
    df["ts"] = pd.to_datetime(df["ts"])
    df = df.sort_values("ts").reset_index(drop=True)

    total     = len(df)
    counts    = df["label"].value_counts()
    pos_pct   = "{:.0f}%".format(counts.get("Positive", 0) / total * 100)
    neg_pct   = "{:.0f}%".format(counts.get("Negative", 0) / total * 100)
    avg_score = "{:+.2f}".format(df["score"].rolling(10).mean().iloc[-1]) if total >= 10 else "--"

    kpis = [
        _kpi_card("Tweets Processed", str(total),  COLORS["accent"]),
        _kpi_card("Positive",          pos_pct,     COLORS["Positive"]),
        _kpi_card("Negative",          neg_pct,     COLORS["Negative"]),
        _kpi_card("Rolling Avg (10)",  avg_score,   COLORS["Neutral"]),
    ]

    rolling_mean = df["score"].rolling(window=10, min_periods=1).mean()
    timeline_fig = go.Figure()
    for lbl, col in [("Positive", COLORS["Positive"]),
                     ("Neutral",  COLORS["Neutral"]),
                     ("Negative", COLORS["Negative"])]:
        mask = df["label"] == lbl
        if mask.any():
            timeline_fig.add_trace(go.Scatter(
                x=df.loc[mask, "ts"],
                y=df.loc[mask, "score"],
                mode="markers",
                name=lbl,
                marker={"color": col, "size": 7, "opacity": 0.75,
                        "line": {"color": "rgba(0,0,0,0.3)", "width": 1}},
                hovertemplate="%{text}<extra></extra>",
                text=df.loc[mask, "tweet"].str[:80],
            ))
    timeline_fig.add_trace(go.Scatter(
        x=df["ts"], y=rolling_mean,
        mode="lines", name="10-tweet avg",
        line={"color": COLORS["accent"], "width": 2.5, "dash": "dot"},
    ))
    timeline_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"color": COLORS["text"]},
        legend={"bgcolor": "rgba(0,0,0,0)", "font": {"size": 11}},
        margin={"l": 40, "r": 20, "t": 10, "b": 40},
        xaxis={"gridcolor": "#1e293b", "zeroline": False},
        yaxis={"gridcolor": "#1e293b", "zeroline": True,
               "zerolinecolor": "#334155",
               "tickvals": [-1, 0, 1], "ticktext": ["Neg", "Neu", "Pos"],
               "range": [-1.4, 1.4]},
        hovermode="closest",
    )

    pie_labels = list(counts.index)
    pie_colors = [COLORS[l] for l in pie_labels]
    pie_fig = go.Figure(go.Pie(
        labels=pie_labels,
        values=list(counts.values),
        hole=0.55,
        marker={"colors": pie_colors, "line": {"color": COLORS["bg"], "width": 2}},
        textfont={"color": COLORS["text"]},
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
    ))
    pie_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": COLORS["text"]},
        legend={"bgcolor": "rgba(0,0,0,0)", "font": {"size": 11}},
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        showlegend=True,
    )

    recent = df.tail(8).iloc[::-1]
    cards = []
    for _, row in recent.iterrows():
        dot = COLORS[row["label"]]
        cards.append(html.Div(
            style={"borderBottom": "1px solid " + COLORS["bg"],
                   "paddingBottom": "0.75rem", "marginBottom": "0.75rem"},
            children=[
                html.Div(
                    style={"display": "flex", "alignItems": "center",
                           "gap": "0.5rem", "marginBottom": "0.2rem"},
                    children=[
                        html.Span(style={"width": "8px", "height": "8px",
                                         "borderRadius": "50%",
                                         "backgroundColor": dot,
                                         "display": "inline-block",
                                         "flexShrink": "0"}),
                        html.Span(row["label"],
                                  style={"color": dot, "fontSize": "0.7rem",
                                         "fontWeight": "600",
                                         "textTransform": "uppercase",
                                         "letterSpacing": "0.05em"}),
                        html.Span("- {:.0%} conf".format(row["conf"]),
                                  style={"color": COLORS["muted"], "fontSize": "0.7rem"}),
                    ],
                ),
                html.P(row["tweet"],
                       style={"color": COLORS["text"], "margin": 0,
                              "fontSize": "0.82rem", "lineHeight": "1.4"}),
            ],
        ))

    return kpis, timeline_fig, pie_fig, cards


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    start_simulator()
    app.run(debug=True, host="0.0.0.0", port=8050)
