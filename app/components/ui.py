"""
components/ui.py
----------------
Reusable Dash HTML building blocks.
All components are pure functions: inputs in, html.Div out.
"""

from dash import html, dcc
from config.settings import SENTIMENT_COLORS, TEAM_COLORS, ACCENT


def navbar(lang: str = "en", theme: str = "dark", path: str = "/") -> html.Nav:
    from i18n import t
    icon = "☀" if theme == "dark" else "☾"
    links = [
        ("/",       t("nav_home",   lang)),
        ("/past",   t("nav_past",   lang)),
        ("/future", t("nav_future", lang)),
    ]
    return html.Nav(className="navbar", children=[
        html.Div(className="brand", children=[
            html.Span("WC", className="brand-wc"),
            html.Span("SENTIMENT", className="brand-text"),
            html.Span("|", className="brand-sep"),
            html.Span("Qatar 2022 · 2026", className="brand-sub"),
        ]),
        html.Div(className="nav-links", children=[
            dcc.Link(label, href=href,
                     className="nav-item" + (" nav-item--active" if path == href else ""))
            for href, label in links
        ]),
        html.Div(className="nav-controls", children=[
            html.Button("EN", id="lang-en", n_clicks=0,
                        className="ctrl" + (" ctrl--active" if lang == "en" else "")),
            html.Button("FR", id="lang-fr", n_clicks=0,
                        className="ctrl" + (" ctrl--active" if lang == "fr" else "")),
            html.Button("ES", id="lang-es", n_clicks=0,
                        className="ctrl" + (" ctrl--active" if lang == "es" else "")),
            html.Div(className="ctrl-sep"),
            html.Button(icon, id="theme-toggle", n_clicks=0, className="ctrl ctrl--icon",
                        title="Toggle theme"),
        ]),
    ])


def kpi_card(label: str, value: str, accent: str = ACCENT) -> html.Div:
    return html.Div(className="kpi", style={"--kpi-accent": accent}, children=[
        html.Div(label, className="kpi__label"),
        html.Div(value, className="kpi__value"),
    ])


def section_card(title: str, children, extra_class: str = "") -> html.Div:
    return html.Div(className=f"card {extra_class}", children=[
        html.Div(title, className="card__title"),
        html.Div(children, className="card__body"),
    ])


def match_hero_card(home: str, home_flag: str, away: str, away_flag: str,
                    score: str, note: str, meta: list[tuple]) -> html.Div:
    return html.Div(className="match-card", children=[
        html.Div(className="match-card__teams", children=[
            html.Div(className="match-card__team", children=[
                html.Span(home_flag, className="match-card__flag"),
                html.Div(home, className="match-card__name"),
                html.Div("HOME", className="match-card__role"),
            ]),
            html.Div(className="match-card__center", children=[
                html.Div(score, className="match-card__score"),
                html.Div(note,  className="match-card__note"),
            ]),
            html.Div(className="match-card__team", children=[
                html.Span(away_flag, className="match-card__flag"),
                html.Div(away, className="match-card__name"),
                html.Div("AWAY", className="match-card__role"),
            ]),
        ]),
        html.Div(className="match-card__meta", children=[
            html.Div(className="match-card__meta-item", children=[
                html.Div(label, className="match-card__meta-label"),
                html.Div(value, className="match-card__meta-value"),
            ]) for label, value in meta
        ]),
    ])


def tweet_item(label: str, team: str, conf: float, text: str,
               home: str, away: str) -> html.Div:
    col   = SENTIMENT_COLORS.get(label, "#64748b")
    tcol  = TEAM_COLORS["home"] if team == "home" else \
            TEAM_COLORS["away"] if team == "away" else "#64748b"
    tlbl  = home if team == "home" else away if team == "away" else "—"
    return html.Div(className="tweet", children=[
        html.Div(className="tweet__meta", children=[
            html.Span(className="tweet__dot", style={"background": col}),
            html.Span(label, className="tweet__label", style={"color": col}),
            html.Span(tlbl,  className="tweet__team",  style={"color": tcol}),
            html.Span(f"{conf:.0%}", className="tweet__conf"),
        ]),
        html.P(text, className="tweet__text"),
    ])


def lineup_column(team: str, players: list[str], color: str) -> html.Div:
    return html.Div(className="lineup", children=[
        html.Div(team, className="lineup__team", style={"color": color}),
        html.Ol(className="lineup__list", children=[
            html.Li(p, className="lineup__player") for p in players
        ]),
    ])


def news_item(text: str) -> html.Div:
    return html.Div(className="news-item", children=[
        html.Div(className="news-item__dot"),
        html.P(text, className="news-item__text"),
    ])


def warning_banner(text: str) -> html.Div:
    return html.Div(className="warning", children=[
        html.Span("!", className="warning__icon"),
        html.Span(text, className="warning__text"),
    ])


def fixture_row(home: str, away: str, time_str: str,
                is_live: bool = False, is_active: bool = False) -> html.Div:
    cls = "fixture"
    if is_active: cls += " fixture--active"
    tc  = "#ef4444" if is_live else ACCENT
    return html.Div(className=cls, children=[
        html.Span(f"{home} vs {away}", className="fixture__teams"),
        html.Span(time_str, className="fixture__time", style={"color": tc}),
    ])
