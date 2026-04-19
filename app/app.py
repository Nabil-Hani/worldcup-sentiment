"""
app.py  —  World Cup Sentiment Tracker  (multi-page, i18n, dark/light)
Run: python app/app.py
"""

import os, sys, datetime, threading, logging, random
sys.path.insert(0, os.path.dirname(__file__))

import dash
from dash import dcc, html, Input, Output, State, callback, ctx, no_update
import plotly.graph_objects as go
import pandas as pd

from simulator   import tweet_stream
from sentiment   import analyze
from state       import store, SentimentRecord
from fixtures    import get_fixtures, get_next_match, Fixture
from wc2022_data import ALL_MATCHES, MATCHES_BY_ID, STAGE_ORDER
from i18n        import t, TRANSLATIONS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv; load_dotenv()
except ImportError:
    pass

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PAST_CSV   = os.path.join(DATA_DIR, "tweets1.csv")   # Real 2022 Kaggle tweets
FUTURE_CSV = os.path.join(DATA_DIR, "tweets.csv")    # Generated mock tweets

# ── Thread management ────────────────────────────────────────────────────────
_stop_event   = threading.Event()
_current      = {"home": None, "away": None, "csv": FUTURE_CSV, "match_id": None}

def _run_sim(home, away, csv_path, stop_ev):
    logger.info("Sim: %s vs %s | %s", home, away, os.path.basename(csv_path))
    for tweet in tweet_stream(home_team=home, away_team=away, csv_path=csv_path):
        if stop_ev.is_set():
            return
        result = analyze(tweet)
        tl = tweet.lower()
        hk = home.lower().split()[0]
        ak = away.lower().split()[0]
        tag = "home" if hk in tl and ak not in tl else \
              "away" if ak in tl and hk not in tl else "both"
        rec = SentimentRecord(
            timestamp=datetime.datetime.utcnow().isoformat(timespec="seconds"),
            tweet=tweet[:140], label=result["label"],
            confidence=result["confidence"], score=result["score"],
        )
        rec.__dict__["team_tag"] = tag
        store.append(rec)

def start_sim(home, away, csv_path):
    global _stop_event
    _stop_event.set()
    _stop_event = threading.Event()
    _current.update(home=home, away=away, csv=csv_path)
    store._records.clear()
    t = threading.Thread(target=_run_sim, args=(home, away, csv_path, _stop_event),
                         daemon=True)
    t.start()
    logger.info("Sim started id=%d", t.ident)

# ── Fixtures ─────────────────────────────────────────────────────────────────
ALL_FIXTURES = get_fixtures(FOOTBALL_API_KEY, limit=8)
NEXT_MATCH   = get_next_match(FOOTBALL_API_KEY)
if NEXT_MATCH:
    start_sim(NEXT_MATCH.home_team, NEXT_MATCH.away_team, FUTURE_CSV)
    _current["match_id"] = "future"
else:
    start_sim("Brazil", "Argentina", FUTURE_CSV)

# ── App ──────────────────────────────────────────────────────────────────────
app = dash.Dash(__name__, suppress_callback_exceptions=True,
                title="World Cup Sentiment",
                meta_tags=[{"name":"viewport","content":"width=device-width,initial-scale=1"}])
server = app.server

# ── Helpers ──────────────────────────────────────────────────────────────────
def _ef(msg="..."):
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"color":"#8a9bb8"}, xaxis={"visible":False}, yaxis={"visible":False},
        margin={"l":0,"r":0,"t":0,"b":0},
        annotations=[{"text":msg,"showarrow":False,"xref":"paper","yref":"paper",
                      "x":0.5,"y":0.5,"font":{"size":13,"color":"#4a5a74"}}])
    return fig

def _chart_layout(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"color":"#8a9bb8","family":"DM Sans"},
        legend={"bgcolor":"rgba(0,0,0,0)","font":{"size":11}},
        margin={"l":40,"r":10,"t":10,"b":40},
        hovermode="closest",
    )
    return fig

def _kpi(label, value, color, lang="en"):
    return html.Div(className="kpi-card", style={"borderLeftColor": color}, children=[
        html.Div(label, className="kpi-label"),
        html.Div(value, className="kpi-value"),
    ])

COLORS = {"Positive":"#10b981","Neutral":"#f59e0b","Negative":"#ef4444",
          "home":"#818cf8","away":"#fb923c","accent":"#3b82f6"}

# ── Navbar ────────────────────────────────────────────────────────────────────
def make_navbar(lang="en", theme="dark", page="/"):
    return html.Nav(className="navbar", children=[
        html.Div(className="navbar-brand", children=[
            html.Div(className="navbar-logo", children=[
                "WC", html.Span("SENTIMENT")
            ]),
        ]),
        html.Div(className="navbar-links", children=[
            dcc.Link(t("nav_home", lang), href="/", className=f"nav-link{'  active' if page=='/' else ''}"),
            dcc.Link(t("nav_past", lang), href="/past", className=f"nav-link{'  active' if page=='/past' else ''}"),
            dcc.Link(t("nav_future", lang), href="/future", className=f"nav-link{'  active' if page=='/future' else ''}"),
        ]),
        html.Div(className="navbar-controls", children=[
            # Language
            html.Button("EN", id="lang-en", n_clicks=0, className=f"ctrl-btn{'  active' if lang=='en' else ''}"),
            html.Button("FR", id="lang-fr", n_clicks=0, className=f"ctrl-btn{'  active' if lang=='fr' else ''}"),
            html.Button("ES", id="lang-es", n_clicks=0, className=f"ctrl-btn{'  active' if lang=='es' else ''}"),
            html.Div(className="lang-divider"),
            # Theme
            html.Button("☀" if theme=="dark" else "☾", id="theme-toggle", n_clicks=0, className="ctrl-btn"),
        ]),
    ])

# ── Layout ────────────────────────────────────────────────────────────────────
app.layout = html.Div(id="root-wrapper", **{"data-theme":"dark"}, children=[
    dcc.Store(id="store-lang",  data="en"),
    dcc.Store(id="store-theme", data="dark"),
    dcc.Store(id="store-match", data=None),
    dcc.Location(id="url", refresh=False),
    html.Div(id="navbar-container"),
    html.Div(id="page-content"),
    dcc.Interval(id="iv-fast", interval=1000,  n_intervals=0),
    dcc.Interval(id="iv-slow", interval=3000,  n_intervals=0),
])

# ── Page: Home ────────────────────────────────────────────────────────────────
def page_home(lang):
    feats = [
        ("🧠","feat1_title","feat1_desc"),
        ("⚽","feat2_title","feat2_desc"),
        ("📊","feat3_title","feat3_desc"),
        ("🌍","feat4_title","feat4_desc"),
    ]
    title_parts = t("home_hero_title", lang).split("\n")
    return html.Div(className="page fade-up", children=[
        html.Div(className="hero", children=[
            html.Div("⚽  Qatar 2022 + World Cup 2026", className="hero-badge"),
            html.H1(className="hero-title", children=[
                title_parts[0], html.Span(" "), html.Br(),
                html.Span(title_parts[1] if len(title_parts)>1 else "", className="hl"),
            ]),
            html.P(t("home_hero_sub", lang), className="hero-sub"),
            html.Div(className="hero-cta", children=[
                dcc.Link(t("explore_past",   lang), href="/past",   className="btn-primary"),
                dcc.Link(t("explore_future", lang), href="/future", className="btn-secondary"),
            ]),
        ]),
        html.Div(className="features", children=[
            html.Div(className="feature-card", children=[
                html.Div(icon, className="feature-icon"),
                html.Div(t(tkey, lang), className="feature-title"),
                html.Div(t(dkey, lang), className="feature-desc"),
            ]) for icon,tkey,dkey in feats
        ]),
        html.Div(className="footer", children=[
            "Built with RoBERTa · Plotly Dash · World Cup 2022 data"
        ]),
    ])

# ── Page: Past matches ────────────────────────────────────────────────────────
def page_past(lang, selected_id=None):
    # Group matches by stage
    from collections import defaultdict
    by_stage = defaultdict(list)
    for m in ALL_MATCHES:
        by_stage[m.stage].append(m)

    sidebar_items = []
    for stage in STAGE_ORDER:
        if stage not in by_stage:
            continue
        sidebar_items.append(html.Div(stage, className="stage-header"))
        for m in by_stage[stage]:
            is_sel = selected_id == m.id
            sidebar_items.append(
                html.Div(
                    id={"type":"match-btn","index":m.id},
                    n_clicks=0,
                    className="match-card" + (" active" if is_sel else ""),
                    style={"borderColor":"var(--accent)" if is_sel else ""},
                    children=[
                        html.Div(m.stage, className="match-card-stage"),
                        html.Div(className="match-card-teams", children=[
                            html.Span(f"{m.home_flag} {m.home}", className="match-card-team"),
                            html.Span(m.result_str.split(" (")[0], className="match-card-score"),
                            html.Span(f"{m.away} {m.away_flag}", className="match-card-team",
                                      style={"textAlign":"right"}),
                        ]),
                        html.Div(m.date, className="match-card-date"),
                    ]
                )
            )

    # Right panel
    if selected_id and selected_id in MATCHES_BY_ID:
        right = html.Div(id="analysis-panel")
    else:
        right = html.Div(style={"display":"flex","alignItems":"center","justifyContent":"center",
                                  "height":"400px","color":"var(--text3)","fontSize":"1rem"},
                          children=[t("select_prompt", lang)])

    return html.Div(className="page", children=[
        html.Div(className="section-header", children=[
            html.H2(t("past_title", lang), className="section-title"),
            html.P(t("past_subtitle", lang), className="section-sub"),
        ]),
        html.Div(style={"display":"grid","gridTemplateColumns":"340px 1fr","gap":"1rem",
                         "padding":"1.25rem 2.5rem","alignItems":"start"}, children=[
            # Sidebar — scrollable match list
            html.Div(style={"background":"var(--surface)","borderRadius":"var(--radius-lg)",
                             "border":"1px solid var(--border)","overflowY":"auto",
                             "maxHeight":"calc(100vh - 200px)","padding":"0.5rem 0"},
                      children=sidebar_items),
            # Analysis area
            html.Div(id="analysis-panel", children=[right]),
        ]),
    ])

def analysis_panel(match, lang):
    """Build the sentiment analysis panel for a given WC2022Match."""
    winner = match.winner
    return html.Div(className="fade-up", children=[
        # Match info card
        html.Div(className="match-info-card", style={"marginBottom":"1rem"}, children=[
            html.Div(className="match-teams", children=[
                html.Div(className="team-block", children=[
                    html.Span(match.home_flag, className="team-flag"),
                    html.Div(match.home, className="team-name"),
                    html.Div(t("home_fans", lang), className="team-role"),
                ]),
                html.Div(className="score-block", children=[
                    html.Div(f"{match.home_score} – {match.away_score}", className="score-main"),
                    html.Div(match.result_str.split(f"{match.home_score} – {match.away_score}")[-1].strip(" ()") or match.stage,
                             className="score-note"),
                ]),
                html.Div(className="team-block", children=[
                    html.Span(match.away_flag, className="team-flag"),
                    html.Div(match.away, className="team-name"),
                    html.Div(t("away_fans", lang), className="team-role"),
                ]),
            ]),
            html.Div(className="match-meta", children=[
                html.Div(children=[html.Div(t("kickoff",lang),className="meta-label"),
                                    html.Div(f"{match.date}  {match.kickoff}",className="meta-value")]),
                html.Div(children=[html.Div(t("stadium",lang),className="meta-label"),
                                    html.Div(match.stadium,className="meta-value")]),
                html.Div(children=[html.Div(t("winner",lang),className="meta-label"),
                                    html.Div(winner or "—",className="meta-value",
                                             style={"color":"var(--positive)"} if winner else {})]),
                html.Div(children=[html.Div(t("phase",lang),className="meta-label"),
                                    html.Div(match.stage,className="meta-value")]),
            ]),
        ]),
        # Replay note
        html.Div(style={"padding":"0.6rem 1rem","background":"rgba(59,130,246,0.08)",
                         "border":"1px solid rgba(59,130,246,0.2)","borderRadius":"var(--radius)",
                         "fontSize":"0.78rem","color":"var(--accent2)","marginBottom":"1rem"},
                  children=f"🔄  {t('replay_note', lang)} — {match.home} vs {match.away}"),
        # KPI row
        html.Div(id="kpi-row-past", className="kpi-row", style={"marginBottom":"1rem"}),
        # Charts
        html.Div(style={"display":"grid","gridTemplateColumns":"1fr 300px","gap":"1rem",
                         "marginBottom":"1rem"}, children=[
            html.Div(className="card", children=[
                html.Div(t("timeline",lang), className="card-title"),
                dcc.Graph(id="chart-timeline-past", config={"displayModeBar":False},
                          style={"height":"240px"}),
            ]),
            html.Div(className="card", children=[
                html.Div(t("distribution",lang), className="card-title"),
                dcc.Graph(id="chart-pie-past", config={"displayModeBar":False},
                          style={"height":"240px"}),
            ]),
        ]),
        html.Div(style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"1rem"}, children=[
            html.Div(className="card", children=[
                html.Div(t("home_vs_away",lang), className="card-title"),
                dcc.Graph(id="chart-team-past", config={"displayModeBar":False},
                          style={"height":"220px"}),
            ]),
            html.Div(className="card", style={"overflowY":"auto","maxHeight":"300px"}, children=[
                html.Div(t("live_feed",lang), className="card-title"),
                html.Div(id="tweet-feed-past", className="tweet-feed"),
            ]),
        ]),
    ])

# ── Page: Future matches ──────────────────────────────────────────────────────
def page_future(lang):
    return html.Div(className="page", children=[
        html.Div(className="section-header", children=[
            html.H2(t("future_title", lang), className="section-title"),
            html.P(t("future_subtitle", lang), className="section-sub"),
        ]),
        html.Div(className="warning-banner",
                  children=t("future_warning", lang)),
        html.Div(style={"display":"grid","gridTemplateColumns":"1fr 1fr 1fr 1fr",
                         "gap":"0.75rem","padding":"1rem 2.5rem","marginBottom":"0.5rem"},
                  id="kpi-row-future"),
        html.Div(style={"padding":"0 2.5rem","marginBottom":"1rem"},
                  children=[html.Div(id="match-hero-future", className="match-hero")]),
        html.Div(style={"display":"grid","gridTemplateColumns":"1fr 280px","gap":"1rem",
                         "padding":"0 2.5rem","marginBottom":"1rem"}, children=[
            html.Div(className="card", children=[
                html.Div(t("timeline",lang), className="card-title"),
                dcc.Graph(id="chart-timeline-future", config={"displayModeBar":False},
                          style={"height":"240px"}),
            ]),
            html.Div(className="card", children=[
                html.Div(t("distribution",lang), className="card-title"),
                dcc.Graph(id="chart-pie-future", config={"displayModeBar":False},
                          style={"height":"240px"}),
            ]),
        ]),
        html.Div(style={"display":"grid","gridTemplateColumns":"1fr 1fr 1fr","gap":"1rem",
                         "padding":"0 2.5rem 1.5rem"}, children=[
            html.Div(className="card", children=[
                html.Div(t("home_vs_away",lang), className="card-title"),
                dcc.Graph(id="chart-team-future", config={"displayModeBar":False},
                          style={"height":"220px"}),
            ]),
            html.Div(className="card", children=[
                html.Div(t("upcoming_fixtures",lang), className="card-title"),
                html.Div(id="fixtures-list-future"),
            ]),
            html.Div(className="card", style={"overflowY":"auto","maxHeight":"300px"}, children=[
                html.Div(t("live_feed",lang), className="card-title"),
                html.Div(id="tweet-feed-future", className="tweet-feed"),
            ]),
        ]),
    ])

# ── Route callback ────────────────────────────────────────────────────────────
@callback(
    Output("navbar-container","children"),
    Output("page-content","children"),
    Output("root-wrapper","**data-theme**"),
    Input("url","pathname"),
    Input("store-lang","data"),
    Input("store-theme","data"),
    Input("store-match","data"),
)
def render_page(path, lang, theme, match_id):
    lang  = lang  or "en"
    theme = theme or "dark"
    nav   = make_navbar(lang, theme, path or "/")
    path  = path or "/"
    if path == "/past":
        page = page_past(lang, match_id)
    elif path == "/future":
        page = page_future(lang)
    else:
        page = page_home(lang)
    return nav, page, theme

# ── Theme toggle ──────────────────────────────────────────────────────────────
@callback(
    Output("store-theme","data"),
    Output("root-wrapper","data-theme"),
    Input("theme-toggle","n_clicks"),
    State("store-theme","data"),
    prevent_initial_call=True,
)
def toggle_theme(n, current):
    new = "light" if current == "dark" else "dark"
    return new, new

# ── Language ──────────────────────────────────────────────────────────────────
@callback(
    Output("store-lang","data"),
    Input("lang-en","n_clicks"),
    Input("lang-fr","n_clicks"),
    Input("lang-es","n_clicks"),
    prevent_initial_call=True,
)
def set_lang(en, fr, es):
    triggered = ctx.triggered_id
    return {"lang-en":"en","lang-fr":"fr","lang-es":"es"}.get(triggered,"en")

# ── Past match selection ──────────────────────────────────────────────────────
@callback(
    Output("store-match","data"),
    Input({"type":"match-btn","index":dash.ALL},"n_clicks"),
    prevent_initial_call=True,
)
def select_match(clicks):
    if not any(c for c in clicks if c):
        return no_update
    triggered = ctx.triggered_id
    if triggered and "index" in triggered:
        match_id = triggered["index"]
        m = MATCHES_BY_ID.get(match_id)
        if m:
            _current["match_id"] = match_id
            start_sim(m.home, m.away, PAST_CSV)
        return match_id
    return no_update

# ── Past analysis panel update ────────────────────────────────────────────────
@callback(
    Output("analysis-panel","children"),
    Input("store-match","data"),
    State("store-lang","data"),
)
def update_analysis_panel(match_id, lang):
    lang = lang or "en"
    if not match_id or match_id not in MATCHES_BY_ID:
        return html.Div(style={"display":"flex","alignItems":"center",
                                "justifyContent":"center","height":"400px",
                                "color":"var(--text3)"},
                         children=t("select_prompt", lang))
    return analysis_panel(MATCHES_BY_ID[match_id], lang)

# ── Shared chart builder ──────────────────────────────────────────────────────
def _build_charts(lang):
    records = []
    try:
        records = store.get_all()
    except Exception:
        pass

    home = _current.get("home") or "Home"
    away = _current.get("away") or "Away"

    if not records:
        return ([_kpi(t("tweets_analysed",lang),"0","var(--accent)",lang),
                 _kpi(t("positive",lang),"—","var(--positive)",lang),
                 _kpi(t("negative",lang),"—","var(--negative)",lang),
                 _kpi(t("overall_mood",lang),"—","var(--neutral)",lang)],
                _ef(t("streaming",lang)), _ef(), _ef(),
                html.P(t("streaming",lang), style={"color":"var(--text3)","fontSize":"0.83rem"}))

    df = pd.DataFrame([{"ts":r.timestamp,"label":r.label,"score":r.score,
                         "conf":r.confidence,"tweet":r.tweet,
                         "team":getattr(r,"team_tag","both")} for r in records])
    df["ts"] = pd.to_datetime(df["ts"])
    df = df.sort_values("ts").reset_index(drop=True)

    total  = len(df)
    counts = df["label"].value_counts()
    pos_p  = f"{counts.get('Positive',0)/total*100:.0f}%"
    neg_p  = f"{counts.get('Negative',0)/total*100:.0f}%"
    mean   = df["score"].mean()
    mood   = "Positive" if mean>0.1 else "Negative" if mean<-0.1 else "Neutral"

    kpis = [
        _kpi(t("tweets_analysed",lang), str(total), "var(--accent)", lang),
        _kpi(t("positive",lang),        pos_p,      "var(--positive)", lang),
        _kpi(t("negative",lang),        neg_p,      "var(--negative)", lang),
        _kpi(t("overall_mood",lang),    mood,       COLORS[mood], lang),
    ]

    # Timeline
    roll = df["score"].rolling(10, min_periods=1).mean()
    tl = go.Figure()
    for lbl in ["Positive","Neutral","Negative"]:
        mask = df["label"]==lbl
        if mask.any():
            tl.add_trace(go.Scatter(
                x=df.loc[mask,"ts"], y=df.loc[mask,"score"],
                mode="markers", name=lbl,
                marker={"color":COLORS[lbl],"size":6,"opacity":0.75,
                        "line":{"color":"rgba(0,0,0,0.2)","width":1}},
                hovertemplate="%{text}<extra></extra>",
                text=df.loc[mask,"tweet"].str[:80],
            ))
    tl.add_trace(go.Scatter(x=df["ts"], y=roll, mode="lines",
                             name="avg", line={"color":"var(--accent2,#60a5fa)",
                                               "width":2,"dash":"dot"}))
    _chart_layout(tl)
    tl.update_layout(
        xaxis={"gridcolor":"rgba(255,255,255,0.05)","zeroline":False},
        yaxis={"gridcolor":"rgba(255,255,255,0.05)","tickvals":[-1,0,1],
               "ticktext":["Neg","Neu","Pos"],"range":[-1.4,1.4]},
    )

    # Pie
    pie_labels = list(counts.index)
    pie_fig = go.Figure(go.Pie(
        labels=pie_labels, values=list(counts.values), hole=0.58,
        marker={"colors":[COLORS[l] for l in pie_labels],
                "line":{"color":"rgba(0,0,0,0.3)","width":2}},
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
    ))
    _chart_layout(pie_fig)
    pie_fig.update_layout(margin={"l":5,"r":5,"t":5,"b":5})

    # Team bar
    def _pct(sub):
        if sub.empty: return {"Positive":0,"Neutral":0,"Negative":0}
        c = sub["label"].value_counts(normalize=True)*100
        return {l:round(c.get(l,0),1) for l in ["Positive","Neutral","Negative"]}
    hs = _pct(df[df["team"]=="home"])
    as_ = _pct(df[df["team"]=="away"])
    team_fig = go.Figure()
    team_fig.add_trace(go.Bar(name=home, x=list(hs.keys()), y=list(hs.values()),
                               marker_color=COLORS["home"], opacity=0.85))
    team_fig.add_trace(go.Bar(name=away, x=list(as_.keys()), y=list(as_.values()),
                               marker_color=COLORS["away"], opacity=0.85))
    _chart_layout(team_fig)
    team_fig.update_layout(barmode="group",
        xaxis={"gridcolor":"rgba(255,255,255,0.05)"},
        yaxis={"gridcolor":"rgba(255,255,255,0.05)","ticksuffix":"%"},
        margin={"l":30,"r":10,"t":10,"b":40})

    # Tweet feed
    recent = df.tail(8).iloc[::-1]
    feed = []
    for _, row in recent.iterrows():
        col  = COLORS[row["label"]]
        tcol = COLORS["home"] if row["team"]=="home" else \
               COLORS["away"] if row["team"]=="away" else "var(--text3)"
        tlbl = home if row["team"]=="home" else away if row["team"]=="away" else "—"
        feed.append(html.Div(className="tweet-item", children=[
            html.Div(className="tweet-meta", children=[
                html.Span(className="sentiment-dot", style={"backgroundColor":col}),
                html.Span(row["label"], className="sentiment-label", style={"color":col}),
                html.Span(tlbl, className="tweet-team", style={"color":tcol}),
                html.Span(f"{row['conf']:.0%}", className="tweet-conf"),
            ]),
            html.Div(row["tweet"], className="tweet-text"),
        ]))

    return kpis, tl, pie_fig, team_fig, feed

# ── Past charts callback ──────────────────────────────────────────────────────
@callback(
    Output("kpi-row-past","children"),
    Output("chart-timeline-past","figure"),
    Output("chart-pie-past","figure"),
    Output("chart-team-past","figure"),
    Output("tweet-feed-past","children"),
    Input("iv-slow","n_intervals"),
    State("store-match","data"),
    State("store-lang","data"),
)
def update_past_charts(n, match_id, lang):
    lang = lang or "en"
    if not match_id:
        return [], _ef(), _ef(), _ef(), []
    kpis, tl, pie, team, feed = _build_charts(lang)
    return kpis, tl, pie, team, feed

# ── Future charts callback ────────────────────────────────────────────────────
@callback(
    Output("kpi-row-future","children"),
    Output("chart-timeline-future","figure"),
    Output("chart-pie-future","figure"),
    Output("chart-team-future","figure"),
    Output("tweet-feed-future","children"),
    Input("iv-slow","n_intervals"),
    State("store-lang","data"),
)
def update_future_charts(n, lang):
    lang = lang or "en"
    kpis, tl, pie, team, feed = _build_charts(lang)
    return kpis, tl, pie, team, feed

# ── Future hero (countdown) ───────────────────────────────────────────────────
@callback(
    Output("match-hero-future","children"),
    Output("fixtures-list-future","children"),
    Input("iv-fast","n_intervals"),
    State("store-lang","data"),
)
def update_future_hero(n, lang):
    lang    = lang or "en"
    fixture = NEXT_MATCH
    home    = _current.get("home") or (fixture.home_team if fixture else "TBD")
    away    = _current.get("away") or (fixture.away_team if fixture else "TBD")

    # Fixtures list
    rows = []
    for f in ALL_FIXTURES:
        secs = f.seconds_until
        h2 = int(secs//3600); m2 = int((secs%3600)//60)
        ts  = f"in {h2}h {m2}m" if secs>0 else t("live",lang)
        tc  = "var(--accent2)" if secs>0 else "var(--negative)"
        rows.append(html.Div(className="fixture-item", children=[
            html.Span(f"{f.home_team} vs {f.away_team}", className="fixture-teams"),
            html.Span(ts, className="fixture-time", style={"color":tc}),
        ]))

    # Hero
    if not fixture:
        hero = html.P("No fixtures", style={"color":"var(--text3)"})
        return hero, rows

    secs = fixture.seconds_until
    if secs > 0:
        h2=int(secs//3600); m2=int((secs%3600)//60); s2=int(secs%60)
        cd = f"{h2:02d}:{m2:02d}:{s2:02d}"
        status = t("kickoff_in", lang)
        badge  = None
    else:
        cd     = t("live", lang)
        status = t("match_in_progress", lang)
        badge  = html.Span(t("live",lang), className="live-pill")

    hero = html.Div([
        html.Div(fixture.competition,
                 style={"fontSize":"0.72rem","color":"var(--text3)","textTransform":"uppercase",
                         "letterSpacing":"0.1em","marginBottom":"0.75rem"}),
        html.Div(style={"display":"flex","justifyContent":"center","alignItems":"center",
                         "gap":"2.5rem","marginBottom":"1.25rem"}, children=[
            html.Div(style={"textAlign":"center"}, children=[
                html.Div(style={"fontSize":"1.5rem","fontWeight":"700","color":"var(--home)"},
                          children=home),
                html.Div(t("home_fans",lang),
                          style={"fontSize":"0.68rem","color":"var(--text3)","marginTop":"0.15rem"}),
            ]),
            html.Div("vs", style={"color":"var(--text3)","fontSize":"1.1rem"}),
            html.Div(style={"textAlign":"center"}, children=[
                html.Div(style={"fontSize":"1.5rem","fontWeight":"700","color":"var(--away)"},
                          children=away),
                html.Div(t("away_fans",lang),
                          style={"fontSize":"0.68rem","color":"var(--text3)","marginTop":"0.15rem"}),
            ]),
        ]),
        html.Div(status, style={"color":"var(--text3)","fontSize":"0.78rem","marginBottom":"0.4rem"}),
        html.Div(cd, className="countdown"),
        html.Div(fixture.kickoff_local,
                 style={"color":"var(--text3)","fontSize":"0.78rem","marginTop":"0.4rem"}),
        (badge or html.Div()),
    ])
    return hero, rows

# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
