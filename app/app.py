"""
app.py  —  World Cup Sentiment Tracker  (Production SaaS build)
===============================================================
Architecture:
  - dcc.Store(id='store-session') persists match + ui state across renders
  - sim_engine.py runs independently of the UI layer
  - Theme / language changes NEVER restart the simulation
  - Pages are pure functions; callbacks are minimal and focused
"""

import os, sys
sys.path.insert(0, os.path.dirname(__file__))

import dash
from dash import dcc, html, Input, Output, State, callback, ctx, no_update, ALL
import plotly.graph_objects as go
import pandas as pd

from config.settings  import FAST_INTERVAL_MS, SLOW_INTERVAL_MS, SENTIMENT_COLORS, TEAM_COLORS
from services         import sim_engine
from services.state   import store
from services.fixtures import get_fixtures, get_next_match
from services.match_data import get_match_state
from components       import charts as C
from components       import ui
from wc2022_data      import ALL_MATCHES, MATCHES_BY_ID, STAGE_ORDER
from i18n             import t

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Bootstrap ─────────────────────────────────────────────────────────────────
from config.settings import FOOTBALL_API_KEY
ALL_FIXTURES = get_fixtures(FOOTBALL_API_KEY, limit=8)
NEXT_MATCH   = get_next_match(FOOTBALL_API_KEY)

# Start the engine for the future page on launch (doesn't reset on re-render)
if NEXT_MATCH:
    sim_engine.start(NEXT_MATCH.home_team, NEXT_MATCH.away_team, use_past=False)
else:
    sim_engine.start("Brazil", "Argentina", use_past=False)

# ── App ───────────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    title="WC Sentiment",
    meta_tags=[{"name": "viewport", "content": "width=device-width,initial-scale=1"}],
)
server = app.server

# ── Root layout ───────────────────────────────────────────────────────────────
app.layout = html.Div(
    id="root",
    **{"data-theme": "dark"},
    children=[
        # ── Persistent state stores ──────────────────────────────────────────
        # store-ui: theme + lang only — never triggers sim restart
        dcc.Store(id="store-ui",      data={"theme": "dark", "lang": "en"}),
        # store-match: which past match is selected
        dcc.Store(id="store-match",   data=None),
        # ── Routing ──────────────────────────────────────────────────────────
        dcc.Location(id="url", refresh=False),
        # ── Shell ────────────────────────────────────────────────────────────
        html.Div(id="shell-navbar"),
        html.Div(id="shell-page",  className="page fade-up"),
        # ── Timers ───────────────────────────────────────────────────────────
        dcc.Interval(id="iv-fast", interval=FAST_INTERVAL_MS, n_intervals=0),
        dcc.Interval(id="iv-slow", interval=SLOW_INTERVAL_MS, n_intervals=0),
    ],
)

# ── Helper: build DataFrame from store ────────────────────────────────────────

def _df() -> pd.DataFrame | None:
    records = store.get_all()
    if not records:
        return None
    df = pd.DataFrame([
        {"ts": r.timestamp, "label": r.label, "score": r.score,
         "conf": r.confidence, "tweet": r.tweet,
         "team": getattr(r, "team_tag", "both")}
        for r in records
    ])
    df["ts"] = pd.to_datetime(df["ts"])
    return df.sort_values("ts").reset_index(drop=True)

# ── Theme toggle ──────────────────────────────────────────────────────────────
@callback(
    Output("store-ui", "data"),
    Output("root", "data-theme"),
    Input("theme-toggle", "n_clicks"),
    Input("lang-en", "n_clicks"),
    Input("lang-fr", "n_clicks"),
    Input("lang-es", "n_clicks"),
    State("store-ui", "data"),
    prevent_initial_call=True,
)
def update_ui(t_click, en, fr, es, ui_state):
    """
    This callback ONLY updates the UI store.
    It does NOT touch sim_engine — theme/language changes never reset the sim.
    """
    ui_state = ui_state or {"theme": "dark", "lang": "en"}
    tid = ctx.triggered_id

    if tid == "theme-toggle":
        new_theme = "light" if ui_state["theme"] == "dark" else "dark"
        ui_state = {**ui_state, "theme": new_theme}
    elif tid in ("lang-en", "lang-fr", "lang-es"):
        ui_state = {**ui_state, "lang": {"lang-en": "en", "lang-fr": "fr", "lang-es": "es"}[tid]}

    return ui_state, ui_state["theme"]

# ── Page router ───────────────────────────────────────────────────────────────
@callback(
    Output("shell-navbar", "children"),
    Output("shell-page",   "children"),
    Input("url",           "pathname"),
    Input("store-ui",      "data"),
    Input("store-match",   "data"),
)
def render_page(path, ui_state, match_id):
    ui_state = ui_state or {"theme": "dark", "lang": "en"}
    lang     = ui_state["lang"]
    theme    = ui_state["theme"]
    path     = path or "/"

    nav  = ui.navbar(lang=lang, theme=theme, path=path)

    if path == "/past":
        page = _page_past(lang, match_id)
    elif path == "/future":
        page = _page_future(lang)
    else:
        page = _page_home(lang)

    return nav, page

# ── Past: match selection ─────────────────────────────────────────────────────
@callback(
    Output("store-match", "data"),
    Input({"type": "match-row", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def select_match(clicks):
    if not any(c for c in clicks if c):
        return no_update
    tid = ctx.triggered_id
    if tid and "index" in tid:
        mid = tid["index"]
        m   = MATCHES_BY_ID.get(mid)
        if m:
            # This is the ONLY place sim restarts — explicit user match selection
            sim_engine.start(m.home, m.away, use_past=True)
        return mid
    return no_update

# ── Past: analysis panel ──────────────────────────────────────────────────────
@callback(
    Output("past-panel", "children"),
    Input("store-match",  "data"),
    State("store-ui",     "data"),
)
def update_past_panel(match_id, ui_state):
    lang = (ui_state or {}).get("lang", "en")
    if not match_id or match_id not in MATCHES_BY_ID:
        return html.Div(t("select_prompt", lang), className="empty-state")
    return _analysis_panel(MATCHES_BY_ID[match_id], lang)

# ── Past: charts (polling) ────────────────────────────────────────────────────
@callback(
    Output("past-kpis",     "children"),
    Output("past-timeline", "figure"),
    Output("past-pie",      "figure"),
    Output("past-team",     "figure"),
    Output("past-odds",     "figure"),
    Output("past-news",     "children"),
    Output("past-feed",     "children"),
    Input("iv-slow",        "n_intervals"),
    State("store-match",    "data"),
    State("store-ui",       "data"),
)
def update_past_charts(n, match_id, ui_state):
    theme = (ui_state or {}).get("theme", "dark")
    lang  = (ui_state or {}).get("lang",  "en")
    empty = C.empty_fig(t("streaming", lang), theme)

    if not match_id:
        return [], empty, empty, empty, empty, [], []

    m  = MATCHES_BY_ID.get(match_id)
    df = _df()

    home = m.home if m else "Home"
    away = m.away if m else "Away"

    if df is None:
        return _empty_kpis(lang), empty, empty, empty, empty, [], []

    kpis, tl, pie, team, odds, news, feed = _build_charts(df, home, away, lang, theme)
    return kpis, tl, pie, team, odds, news, feed

# ── Future: hero countdown (fast) ─────────────────────────────────────────────
@callback(
    Output("future-hero",     "children"),
    Output("future-fixtures", "children"),
    Input("iv-fast",          "n_intervals"),
    State("store-ui",         "data"),
)
def update_future_hero(n, ui_state):
    lang    = (ui_state or {}).get("lang", "en")
    session = sim_engine.get_session()
    home    = session.get("home") or (NEXT_MATCH.home_team if NEXT_MATCH else "TBD")
    away    = session.get("away") or (NEXT_MATCH.away_team if NEXT_MATCH else "TBD")
    fixture = NEXT_MATCH

    # Fixture rows
    rows = []
    for f in ALL_FIXTURES:
        secs   = f.seconds_until
        h2, m2 = int(secs // 3600), int((secs % 3600) // 60)
        ts     = f"{h2}h {m2}m" if secs > 0 else t("live", lang)
        rows.append(ui.fixture_row(
            f.home_team, f.away_team, ts,
            is_live=secs <= 0,
            is_active=(fixture and f.home_team == fixture.home_team),
        ))

    if not fixture:
        return html.Div("No fixture data.", style={"color": "var(--c-text-3)"}), rows

    secs = fixture.seconds_until
    if secs > 0:
        h2 = int(secs // 3600); m2 = int((secs % 3600) // 60); s2 = int(secs % 60)
        time_str  = f"{h2:02d}:{m2:02d}:{s2:02d}"
        status    = t("kickoff_in", lang)
        badge     = html.Div()
    else:
        time_str  = t("live", lang)
        status    = t("match_in_progress", lang)
        badge     = html.Div(t("live", lang), className="live-badge")

    hero = html.Div(className="countdown-hero", children=[
        html.Div(fixture.competition, className="countdown-hero__comp"),
        html.Div(className="countdown-hero__teams", children=[
            html.Div(children=[
                html.Div(home, className="countdown-hero__team-name",
                         style={"color": "var(--c-home)"}),
                html.Div(t("home_fans", lang), className="countdown-hero__team-role"),
            ]),
            html.Div("vs", className="countdown-hero__vs"),
            html.Div(children=[
                html.Div(away, className="countdown-hero__team-name",
                         style={"color": "var(--c-away)"}),
                html.Div(t("away_fans", lang), className="countdown-hero__team-role"),
            ]),
        ]),
        html.Div(status,    className="countdown-hero__label"),
        html.Div(time_str,  className="countdown-hero__time"),
        html.Div(fixture.kickoff_local, className="countdown-hero__date"),
        badge,
    ])
    return hero, rows

# ── Future: charts (polling) ──────────────────────────────────────────────────
@callback(
    Output("future-kpis",     "children"),
    Output("future-timeline", "figure"),
    Output("future-pie",      "figure"),
    Output("future-team",     "figure"),
    Output("future-odds",     "figure"),
    Output("future-news",     "children"),
    Output("future-feed",     "children"),
    Input("iv-slow",          "n_intervals"),
    State("store-ui",         "data"),
)
def update_future_charts(n, ui_state):
    theme   = (ui_state or {}).get("theme", "dark")
    lang    = (ui_state or {}).get("lang",  "en")
    session = sim_engine.get_session()
    home    = session.get("home") or "TBD"
    away    = session.get("away") or "TBD"
    df      = _df()
    empty   = C.empty_fig(t("streaming", lang), theme)

    if df is None:
        return _empty_kpis(lang), empty, empty, empty, empty, [], []

    return _build_charts(df, home, away, lang, theme)

# ── Shared chart builder ──────────────────────────────────────────────────────

def _empty_kpis(lang):
    return [
        ui.kpi_card(t("tweets_analysed", lang), "0",  "var(--c-accent)"),
        ui.kpi_card(t("positive",        lang), "—",  "var(--c-positive)"),
        ui.kpi_card(t("negative",        lang), "—",  "var(--c-negative)"),
        ui.kpi_card(t("overall_mood",    lang), "—",  "var(--c-neutral)"),
    ]


def _build_charts(df, home, away, lang, theme):
    total  = len(df)
    counts = df["label"].value_counts()
    pos_p  = f"{counts.get('Positive', 0) / total * 100:.0f}%"
    neg_p  = f"{counts.get('Negative', 0) / total * 100:.0f}%"
    mean   = df["score"].mean()
    mood   = "Positive" if mean > 0.1 else "Negative" if mean < -0.1 else "Neutral"
    mood_color = {"Positive": "var(--c-positive)", "Neutral": "var(--c-neutral)",
                  "Negative": "var(--c-negative)"}[mood]

    kpis = [
        ui.kpi_card(t("tweets_analysed", lang), str(total), "var(--c-accent)"),
        ui.kpi_card(t("positive",        lang), pos_p,      "var(--c-positive)"),
        ui.kpi_card(t("negative",        lang), neg_p,      "var(--c-negative)"),
        ui.kpi_card(t("overall_mood",    lang), mood,       mood_color),
    ]

    tl   = C.timeline_fig(df, theme)
    pie  = C.donut_fig(df, theme)
    team = C.team_bar_fig(df, home, away, theme)

    # Odds — shift based on sentiment
    ms   = get_match_state(home, away, sentiment_mean=mean)
    odds = C.odds_gauge_fig(ms.odds.home_win, ms.odds.draw, ms.odds.away_win,
                             home, away, theme)

    # News
    news = [ui.news_item(item) for item in ms.news]

    # Tweet feed
    recent = df.tail(8).iloc[::-1]
    feed   = [
        ui.tweet_item(row["label"], row["team"], row["conf"],
                      row["tweet"], home, away)
        for _, row in recent.iterrows()
    ]

    return kpis, tl, pie, team, odds, news, feed

# ── Page builders ─────────────────────────────────────────────────────────────

def _page_home(lang):
    feats = [
        ("01", "feat1_title", "feat1_desc"),
        ("02", "feat2_title", "feat2_desc"),
        ("03", "feat3_title", "feat3_desc"),
        ("04", "feat4_title", "feat4_desc"),
    ]
    title_lines = t("home_hero_title", lang).split("\n")
    return html.Div(children=[
        html.Div(className="hero", children=[
            html.Div("Qatar 2022  ·  World Cup 2026", className="hero__badge"),
            html.H1(className="hero__title", children=[
                title_lines[0], html.Br(),
                html.Span(title_lines[1] if len(title_lines) > 1 else "",
                          className="hero__title--hl"),
            ]),
            html.P(t("home_hero_sub", lang), className="hero__sub"),
            html.Div(className="hero__cta", children=[
                dcc.Link(t("explore_past",   lang), href="/past",   className="btn btn--primary"),
                dcc.Link(t("explore_future", lang), href="/future", className="btn btn--secondary"),
            ]),
        ]),
        html.Div(className="features", children=[
            html.Div(className="feat", children=[
                html.Div(num, className="feat__num"),
                html.Div(t(tk, lang), className="feat__title"),
                html.Div(t(dk, lang), className="feat__desc"),
            ]) for num, tk, dk in feats
        ]),
        html.Div("Built with RoBERTa · Plotly Dash · World Cup 2022 data",
                 className="footer"),
    ])


def _page_past(lang, selected_id=None):
    from collections import defaultdict
    by_stage = defaultdict(list)
    for m in ALL_MATCHES:
        by_stage[m.stage].append(m)

    sidebar_rows = []
    for stage in STAGE_ORDER:
        if stage not in by_stage:
            continue
        sidebar_rows.append(html.Div(stage, className="sidebar__stage"))
        for m in by_stage[stage]:
            active = selected_id == m.id
            sidebar_rows.append(html.Div(
                id={"type": "match-row", "index": m.id},
                n_clicks=0,
                className="match-row" + (" match-row--active" if active else ""),
                children=[
                    html.Div(m.stage, className="match-row__stage"),
                    html.Div(className="match-row__teams", children=[
                        html.Span(f"{m.home_flag} {m.home}",
                                  className="match-row__team"),
                        html.Span(f"{m.home_score}–{m.away_score}",
                                  className="match-row__score"),
                        html.Span(f"{m.away} {m.away_flag}",
                                  className="match-row__team match-row__team--away"),
                    ]),
                    html.Div(m.date, className="match-row__date"),
                ],
            ))

    return html.Div(children=[
        html.Div(className="section-hdr", children=[
            html.H2(t("past_title",    lang), className="section-hdr__title"),
            html.P( t("past_subtitle", lang), className="section-hdr__sub"),
        ]),
        html.Div(className="dash-layout", children=[
            html.Div(className="sidebar", children=sidebar_rows),
            html.Div(id="past-panel", children=[
                html.Div(t("select_prompt", lang), className="empty-state"),
            ]),
        ]),
    ])


def _analysis_panel(m, lang):
    """Full analysis panel for a WC 2022 match."""
    winner = m.winner
    score_note = m.result_str.replace(f"{m.home_score} – {m.away_score}", "").strip(" ()")

    return html.Div(className="dash-main fade-up", children=[

        # ── Match card ───────────────────────────────────────────────────────
        ui.match_hero_card(
            home=m.home, home_flag=m.home_flag,
            away=m.away, away_flag=m.away_flag,
            score=f"{m.home_score} – {m.away_score}",
            note=score_note or m.stage,
            meta=[
                (t("kickoff", lang), f"{m.date}  {m.kickoff}"),
                (t("stadium", lang), m.stadium),
                (t("winner",  lang), winner or "—"),
                (t("phase",   lang), m.stage),
            ],
        ),

        # ── Replay note ──────────────────────────────────────────────────────
        html.Div(
            f"{t('replay_note', lang)} — {m.home} vs {m.away}",
            className="replay-note",
        ),

        # ── KPI row ──────────────────────────────────────────────────────────
        html.Div(id="past-kpis", className="kpi-row",
                 style={"padding": "0", "gridTemplateColumns": "repeat(4,1fr)"}),

        # ── Odds bar ─────────────────────────────────────────────────────────
        ui.section_card(
            "Win Probability (Sentiment-Adjusted)",
            dcc.Graph(id="past-odds", config={"displayModeBar": False},
                      style={"height": "100px"}),
        ),

        # ── Timeline + Pie ───────────────────────────────────────────────────
        html.Div(className="dash-row dash-row--21", children=[
            ui.section_card(t("timeline",     lang),
                            dcc.Graph(id="past-timeline",
                                      config={"displayModeBar": False},
                                      style={"height": "220px"})),
            ui.section_card(t("distribution", lang),
                            dcc.Graph(id="past-pie",
                                      config={"displayModeBar": False},
                                      style={"height": "220px"})),
        ]),

        # ── Team bar + Lineups ───────────────────────────────────────────────
        html.Div(className="dash-row dash-row--2", children=[
            ui.section_card(t("home_vs_away", lang),
                            dcc.Graph(id="past-team",
                                      config={"displayModeBar": False},
                                      style={"height": "200px"})),
            ui.section_card("Lineups",
                            html.Div(className="lineups", id="past-lineups",
                                     children=_lineup_panel(m.home, m.away))),
        ]),

        # ── News + Tweet feed ────────────────────────────────────────────────
        html.Div(className="dash-row dash-row--2", children=[
            ui.section_card("Match Analysis",
                            html.Div(id="past-news")),
            ui.section_card(t("live_feed", lang),
                            html.Div(id="past-feed", className="tweet-feed",
                                     style={"maxHeight": "260px"})),
        ]),
    ])


def _page_future(lang):
    return html.Div(children=[
        html.Div(className="section-hdr", children=[
            html.H2(t("future_title",    lang), className="section-hdr__title"),
            html.P( t("future_subtitle", lang), className="section-hdr__sub"),
        ]),
        ui.warning_banner(t("future_warning", lang)),

        html.Div(className="kpi-row", id="future-kpis"),

        html.Div(style={"padding": "0 2rem"}, children=[
            html.Div(id="future-hero"),
        ]),

        html.Div(className="dash-row dash-row--21",
                 style={"padding": "0.85rem 2rem"}, children=[
            ui.section_card(t("timeline", lang),
                            dcc.Graph(id="future-timeline",
                                      config={"displayModeBar": False},
                                      style={"height": "220px"})),
            ui.section_card(t("distribution", lang),
                            dcc.Graph(id="future-pie",
                                      config={"displayModeBar": False},
                                      style={"height": "220px"})),
        ]),

        html.Div(className="dash-row dash-row--3",
                 style={"padding": "0 2rem 0.85rem"}, children=[
            ui.section_card(t("home_vs_away", lang),
                            dcc.Graph(id="future-team",
                                      config={"displayModeBar": False},
                                      style={"height": "200px"})),
            ui.section_card("Win Probability",
                            dcc.Graph(id="future-odds",
                                      config={"displayModeBar": False},
                                      style={"height": "200px"})),
            ui.section_card(t("upcoming_fixtures", lang),
                            html.Div(id="future-fixtures")),
        ]),

        html.Div(className="dash-row dash-row--2",
                 style={"padding": "0 2rem 1.5rem"}, children=[
            ui.section_card("Match Intelligence",
                            html.Div(id="future-news")),
            ui.section_card(t("live_feed", lang),
                            html.Div(id="future-feed", className="tweet-feed",
                                     style={"maxHeight": "260px"})),
        ]),
    ])


def _lineup_panel(home: str, away: str):
    ms = get_match_state(home, away)
    return [
        ui.lineup_column(home, ms.home_lineup, "var(--c-home)"),
        ui.lineup_column(away, ms.away_lineup, "var(--c-away)"),
    ]


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
