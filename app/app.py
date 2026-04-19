"""
app.py
------
Entry-point for the Real-time World Cup Sentiment Tracker dashboard.

Architecture:
  ┌─────────────────┐    ┌──────────────────┐    ┌──────────────────────┐
  │  simulator.py   │───▶│    state.py       │◀───│       app.py         │
  │  (background    │    │  (thread-safe     │    │  (Dash + Plotly UI   │
  │   thread)       │    │   ring-buffer)    │    │   + Interval update) │
  └─────────────────┘    └──────────────────┘    └──────────────────────┘

Run with:
    python app/app.py
Or with gunicorn for production:
    gunicorn app.app:server --workers=1 --threads=4
"""

import datetime
import threading
import logging

import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
import pandas as pd

# Internal modules
from simulator import tweet_stream
from sentiment  import analyze
from state      import store, SentimentRecord

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
COLORS = {
    "Positive": "#00e676",   # Vivid green
    "Neutral":  "#ffca28",   # Warm amber
    "Negative": "#ff1744",   # Sharp red
    "bg":       "#0a0e1a",   # Near-black navy
    "surface":  "#111827",   # Card background
    "text":     "#e2e8f0",   # Off-white
    "muted":    "#64748b",   # Slate gray
    "accent":   "#38bdf8",   # Sky blue
}

# ---------------------------------------------------------------------------
# Background simulator thread
# ---------------------------------------------------------------------------

def _run_simulator() -> None:
    """
    Runs forever in a daemon thread.
    Pulls tweets from the stream generator, scores them, and pushes
    SentimentRecord objects into the shared store.
    """
    logger.info("Simulator thread starting …")
    for tweet in tweet_stream():                     # Generator — blocks on time.sleep()
        result = analyze(tweet)
        record = SentimentRecord(
            timestamp  = datetime.datetime.utcnow().isoformat(timespec="seconds"),
            tweet      = tweet[:140],                # Cap display length
            label      = result["label"],
            confidence = result["confidence"],
            score      = result["score"],
        )
        store.append(record)
        logger.debug("Stored [%s] → %s", record.label, record.tweet[:50])


def start_simulator() -> None:
    """Launch the simulator as a background daemon thread."""
    t = threading.Thread(target=_run_simulator, name="SimulatorThread", daemon=True)
    t.start()
    logger.info("Simulator thread started (id=%d)", t.ident)


# ---------------------------------------------------------------------------
# Dash application
# ---------------------------------------------------------------------------

app = dash.Dash(
    __name__,
    title="⚽ World Cup Sentiment Tracker",
    update_title=None,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

# Expose the Flask server for gunicorn / deployment
server = app.server

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

app.layout = html.Div(
    style={"backgroundColor": COLORS["bg"], "minHeight": "100vh", "fontFamily": "'Inter', sans-serif"},
    children=[

        # ── Header ──────────────────────────────────────────────────────────
        html.Div(
            style={"padding": "2rem 3rem 1rem", "borderBottom": f"1px solid {COLORS['surface']}"},
            children=[
                html.H1("⚽ World Cup Sentiment Tracker",
                        style={"color": COLORS["text"], "margin": 0, "fontSize": "1.6rem",
                               "fontWeight": "700", "letterSpacing": "-0.5px"}),
                html.P("Real-time NLP sentiment analysis on match-day Twitter chatter",
                       style={"color": COLORS["muted"], "margin": "0.25rem 0 0", "fontSize": "0.9rem"}),
            ],
        ),

        # ── KPI Cards ───────────────────────────────────────────────────────
        html.Div(
            id="kpi-row",
            style={"display": "flex", "gap": "1rem", "padding": "1.5rem 3rem"},
        ),

        # ── Main chart ──────────────────────────────────────────────────────
        html.Div(
            style={"padding": "0 3rem"},
            children=[
                html.Div(
                    style={"backgroundColor": COLORS["surface"], "borderRadius": "12px",
                           "padding": "1.5rem"},
                    children=[
                        html.H3("Sentiment Over Time", style={"color": COLORS["text"],
                                "margin": "0 0 1rem", "fontSize": "1rem", "fontWeight": "600"}),
                        dcc.Graph(id="sentiment-timeline", config={"displayModeBar": False},
                                  style={"height": "340px"}),
                    ],
                ),
            ],
        ),

        # ── Bottom row: distribution pie + latest tweets ─────────────────
        html.Div(
            style={"display": "flex", "gap": "1rem", "padding": "1.5rem 3rem"},
            children=[
                # Distribution donut
                html.Div(
                    style={"flex": "0 0 340px", "backgroundColor": COLORS["surface"],
                           "borderRadius": "12px", "padding": "1.5rem"},
                    children=[
                        html.H3("Distribution", style={"color": COLORS["text"],
                                "margin": "0 0 1rem", "fontSize": "1rem", "fontWeight": "600"}),
                        dcc.Graph(id="sentiment-pie", config={"displayModeBar": False},
                                  style={"height": "260px"}),
                    ],
                ),
                # Latest tweets feed
                html.Div(
                    style={"flex": "1", "backgroundColor": COLORS["surface"],
                           "borderRadius": "12px", "padding": "1.5rem", "overflowY": "auto",
                           "maxHeight": "320px"},
                    children=[
                        html.H3("Latest Tweets", style={"color": COLORS["text"],
                                "margin": "0 0 1rem", "fontSize": "1rem", "fontWeight": "600"}),
                        html.Div(id="tweet-feed"),
                    ],
                ),
            ],
        ),

        # ── Interval driver ─────────────────────────────────────────────────
        # Fires every 3 seconds, triggering all @callback functions below
        dcc.Interval(id="interval", interval=3_000, n_intervals=0),
    ],
)


# ---------------------------------------------------------------------------
# Helper: build a small KPI card
# ---------------------------------------------------------------------------

def _kpi_card(label: str, value: str, color: str) -> html.Div:
    return html.Div(
        style={"flex": "1", "backgroundColor": COLORS["surface"], "borderRadius": "12px",
               "padding": "1.25rem 1.5rem", "borderLeft": f"4px solid {color}"},
        children=[
            html.P(label, style={"color": COLORS["muted"], "margin": "0 0 0.25rem",
                                 "fontSize": "0.75rem", "textTransform": "uppercase",
                                 "letterSpacing": "0.08em"}),
            html.P(value, style={"color": COLORS["text"], "margin": 0,
                                 "fontSize": "1.6rem", "fontWeight": "700"}),
        ],
    )


# ---------------------------------------------------------------------------
# Callbacks — all driven by dcc.Interval
# ---------------------------------------------------------------------------

@callback(
    Output("kpi-row",          "children"),
    Output("sentiment-timeline","figure"),
    Output("sentiment-pie",    "figure"),
    Output("tweet-feed",       "children"),
    Input("interval",          "n_intervals"),
)
def update_dashboard(n: int):
    """
    Called every `interval` ms.  Reads the current snapshot from the shared
    store and rebuilds every visual component.
    """
    records = store.get_all()

    # ── Empty state ─────────────────────────────────────────────────────────
    if not records:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color=COLORS["text"],
            annotations=[{"text": "Waiting for data…", "showarrow": False,
                          "font": {"color": COLORS["muted"], "size": 14}}],
        )
        return [], empty_fig, empty_fig, html.P("No tweets yet.", style={"color": COLORS["muted"]})

    # ── Build DataFrame ──────────────────────────────────────────────────────
    df = pd.DataFrame([
        {"ts": r.timestamp, "label": r.label, "score": r.score,
         "conf": r.confidence, "tweet": r.tweet}
        for r in records
    ])
    df["ts"] = pd.to_datetime(df["ts"])
    df = df.sort_values("ts")

    counts    = df["label"].value_counts()
    total     = len(df)
    pos_pct   = f"{counts.get('Positive', 0) / total * 100:.0f}%"
    neg_pct   = f"{counts.get('Negative', 0) / total * 100:.0f}%"
    avg_score = f"{df['score'].rolling(10).mean().iloc[-1]:+.2f}" if total >= 10 else "—"

    # ── KPI cards ───────────────────────────────────────────────────────────
    kpis = [
        _kpi_card("Tweets Processed", str(total),   COLORS["accent"]),
        _kpi_card("Positive",          pos_pct,      COLORS["Positive"]),
        _kpi_card("Negative",          neg_pct,      COLORS["Negative"]),
        _kpi_card("Rolling Avg (10)",  avg_score,    COLORS["Neutral"]),
    ]

    # ── Timeline scatter + rolling mean ─────────────────────────────────────
    rolling_mean = df["score"].rolling(window=10, min_periods=1).mean()

    timeline_fig = go.Figure()
    for lbl, col in [("Positive", COLORS["Positive"]),
                     ("Neutral",  COLORS["Neutral"]),
                     ("Negative", COLORS["Negative"])]:
        mask = df["label"] == lbl
        timeline_fig.add_trace(go.Scatter(
            x=df["ts"][mask], y=df["score"][mask],
            mode="markers",
            name=lbl,
            marker={"color": col, "size": 7, "opacity": 0.75,
                    "line": {"color": "rgba(0,0,0,0.3)", "width": 1}},
            hovertemplate="%{text}<extra></extra>",
            text=df["tweet"][mask].str[:80],
        ))

    timeline_fig.add_trace(go.Scatter(
        x=df["ts"], y=rolling_mean,
        mode="lines", name="10-tweet avg",
        line={"color": COLORS["accent"], "width": 2.5, "dash": "dot"},
    ))

    timeline_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color=COLORS["text"],
        legend={"bgcolor": "rgba(0,0,0,0)", "font": {"size": 11}},
        margin={"l": 40, "r": 20, "t": 10, "b": 40},
        xaxis={"gridcolor": "#1e293b", "zeroline": False},
        yaxis={"gridcolor": "#1e293b", "zeroline": True, "zerolinecolor": "#334155",
               "tickvals": [-1, 0, 1], "ticktext": ["Neg", "Neu", "Pos"],
               "range": [-1.4, 1.4]},
        hovermode="closest",
    )

    # ── Distribution donut ───────────────────────────────────────────────────
    pie_labels  = list(counts.index)
    pie_vals    = list(counts.values)
    pie_colors  = [COLORS[l] for l in pie_labels]

    pie_fig = go.Figure(go.Pie(
        labels=pie_labels, values=pie_vals,
        hole=0.55,
        marker={"colors": pie_colors, "line": {"color": COLORS["bg"], "width": 2}},
        textfont={"color": COLORS["text"]},
        hovertemplate="%{label}: %{value} tweets (%{percent})<extra></extra>",
    ))
    pie_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font_color=COLORS["text"],
        legend={"bgcolor": "rgba(0,0,0,0)", "font": {"size": 11}},
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        showlegend=True,
    )

    # ── Tweet feed (latest 8) ────────────────────────────────────────────────
    recent = df.tail(8).iloc[::-1]   # Newest first
    tweet_cards = []
    for _, row in recent.iterrows():
        dot_color = COLORS[row["label"]]
        tweet_cards.append(
            html.Div(
                style={"borderBottom": f"1px solid {COLORS['bg']}", "paddingBottom": "0.75rem",
                       "marginBottom": "0.75rem"},
                children=[
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "0.5rem",
                               "marginBottom": "0.2rem"},
                        children=[
                            html.Span(style={"width": "8px", "height": "8px",
                                             "borderRadius": "50%",
                                             "backgroundColor": dot_color,
                                             "display": "inline-block", "flexShrink": "0"}),
                            html.Span(row["label"], style={"color": dot_color,
                                       "fontSize": "0.7rem", "fontWeight": "600",
                                       "textTransform": "uppercase", "letterSpacing": "0.05em"}),
                            html.Span(f"· {row['conf']:.0%} conf",
                                      style={"color": COLORS["muted"], "fontSize": "0.7rem"}),
                        ],
                    ),
                    html.P(row["tweet"], style={"color": COLORS["text"], "margin": 0,
                                               "fontSize": "0.82rem", "lineHeight": "1.4"}),
                ],
            )
        )

    return kpis, timeline_fig, pie_fig, tweet_cards


# ---------------------------------------------------------------------------
# Main entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    start_simulator()   # Launch background thread
    app.run(debug=True, host="0.0.0.0", port=8050)
