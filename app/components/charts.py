"""
components/charts.py
--------------------
Reusable Plotly figure builders.
All charts accept a theme parameter ('dark'|'light') and return go.Figure.
"""

import plotly.graph_objects as go
import pandas as pd
from config.settings import SENTIMENT_COLORS, TEAM_COLORS, ACCENT


def _base_layout(theme: str = "dark") -> dict:
    bg   = "rgba(0,0,0,0)"
    grid = "rgba(255,255,255,0.06)" if theme == "dark" else "rgba(0,0,0,0.06)"
    font_color = "#94a3b8" if theme == "dark" else "#64748b"
    return dict(
        paper_bgcolor=bg, plot_bgcolor=bg,
        font={"color": font_color, "family": "DM Sans, sans-serif", "size": 12},
        legend={"bgcolor": "rgba(0,0,0,0)", "font": {"size": 11}},
        margin={"l": 40, "r": 10, "t": 10, "b": 40},
        hovermode="closest",
        xaxis={"gridcolor": grid, "zeroline": False, "linecolor": "rgba(0,0,0,0)"},
        yaxis={"gridcolor": grid, "zeroline": False, "linecolor": "rgba(0,0,0,0)"},
    )


def empty_fig(msg: str = "Waiting for data...", theme: str = "dark") -> go.Figure:
    fig = go.Figure()
    fc  = "#4a5a74" if theme == "dark" else "#94a3b8"
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": fc, "family": "DM Sans, sans-serif", "size": 12},
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[{"text": msg, "showarrow": False,
                      "xref": "paper", "yref": "paper",
                      "x": 0.5, "y": 0.5,
                      "font": {"color": fc, "size": 13}}],
    )
    return fig


def timeline_fig(df: pd.DataFrame, theme: str = "dark") -> go.Figure:
    fig  = go.Figure()
    roll = df["score"].rolling(10, min_periods=1).mean()

    for lbl in ["Positive", "Neutral", "Negative"]:
        mask = df["label"] == lbl
        if not mask.any():
            continue
        fig.add_trace(go.Scatter(
            x=df.loc[mask, "ts"], y=df.loc[mask, "score"],
            mode="markers", name=lbl,
            marker={"color": SENTIMENT_COLORS[lbl], "size": 6, "opacity": 0.8,
                    "line": {"color": "rgba(0,0,0,0.2)", "width": 1}},
            hovertemplate="%{text}<extra></extra>",
            text=df.loc[mask, "tweet"].str[:80],
        ))

    fig.add_trace(go.Scatter(
        x=df["ts"], y=roll, mode="lines", name="10-avg",
        line={"color": ACCENT, "width": 2, "dash": "dot"},
    ))

    layout = _base_layout(theme)
    layout["yaxis"].update(
        tickvals=[-1, 0, 1], ticktext=["Neg", "Neu", "Pos"], range=[-1.4, 1.4]
    )
    fig.update_layout(**layout)
    return fig


def donut_fig(df: pd.DataFrame, theme: str = "dark") -> go.Figure:
    counts = df["label"].value_counts()
    labels = list(counts.index)
    fig = go.Figure(go.Pie(
        labels=labels,
        values=list(counts.values),
        hole=0.62,
        marker={"colors": [SENTIMENT_COLORS[l] for l in labels],
                "line": {"color": "rgba(0,0,0,0.4)", "width": 2}},
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
        textinfo="none",
    ))
    layout = _base_layout(theme)
    layout.update(margin={"l": 5, "r": 5, "t": 5, "b": 5})
    fig.update_layout(**layout)
    return fig


def team_bar_fig(df: pd.DataFrame, home: str, away: str,
                 theme: str = "dark") -> go.Figure:
    def _pct(sub):
        if sub.empty:
            return {"Positive": 0, "Neutral": 0, "Negative": 0}
        c = sub["label"].value_counts(normalize=True) * 100
        return {l: round(c.get(l, 0), 1) for l in ["Positive", "Neutral", "Negative"]}

    hs  = _pct(df[df["team"] == "home"])
    as_ = _pct(df[df["team"] == "away"])

    fig = go.Figure()
    fig.add_trace(go.Bar(name=home, x=list(hs.keys()), y=list(hs.values()),
                         marker_color=TEAM_COLORS["home"], opacity=0.9))
    fig.add_trace(go.Bar(name=away, x=list(as_.keys()), y=list(as_.values()),
                         marker_color=TEAM_COLORS["away"], opacity=0.9))
    layout = _base_layout(theme)
    layout.update(barmode="group",
                  yaxis=dict(layout["yaxis"], ticksuffix="%"))
    fig.update_layout(**layout)
    return fig


def odds_gauge_fig(home_win: float, draw: float, away_win: float,
                   home: str, away: str, theme: str = "dark") -> go.Figure:
    """Horizontal stacked bar showing Win/Draw/Win probabilities."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[home_win * 100], y=["Odds"],
        orientation="h", name=home,
        marker_color=TEAM_COLORS["home"], opacity=0.9,
        hovertemplate=f"{home} win: {home_win*100:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=[draw * 100], y=["Odds"],
        orientation="h", name="Draw",
        marker_color="#64748b", opacity=0.85,
        hovertemplate=f"Draw: {draw*100:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=[away_win * 100], y=["Odds"],
        orientation="h", name=away,
        marker_color=TEAM_COLORS["away"], opacity=0.9,
        hovertemplate=f"{away} win: {away_win*100:.1f}%<extra></extra>",
    ))
    layout = _base_layout(theme)
    layout.update(
        barmode="stack",
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        height=60,
        showlegend=True,
        xaxis=dict(layout["xaxis"], range=[0, 100], ticksuffix="%", showgrid=False),
        yaxis=dict(layout["yaxis"], showticklabels=False, showgrid=False),
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.1,
                "xanchor": "center", "x": 0.5, "font": {"size": 10}},
    )
    fig.update_layout(**layout)
    return fig
