# World Cup Sentiment Tracker — Production Build

## Directory structure

```
wc-saas/
├── app/
│   ├── app.py                  ← Entry point
│   ├── wc2022_data.py          ← All 64 WC 2022 matches
│   ├── i18n.py                 ← EN / FR / ES translations
│   ├── config/
│   │   └── settings.py         ← All config in one place
│   ├── services/
│   │   ├── sim_engine.py       ← Persistent simulation (never resets on UI change)
│   │   ├── match_data.py       ← Odds, lineups, news generation
│   │   ├── simulator.py        ← Tweet stream generator
│   │   ├── sentiment.py        ← RoBERTa wrapper
│   │   ├── state.py            ← Thread-safe store
│   │   └── fixtures.py         ← WC 2026 fixtures API
│   ├── components/
│   │   ├── charts.py           ← Plotly figure builders
│   │   └── ui.py               ← Reusable HTML components
│   └── assets/
│       └── style.css           ← Production stylesheet
├── data/raw/
│   ├── tweets.csv              ← Mock tweets (future matches)
│   └── tweets1.csv             ← Real Kaggle tweets (past matches)
├── .env                        ← FOOTBALL_API_KEY=your_key
└── requirements.txt
```

## Key architectural decisions

| Problem | Solution |
|---|---|
| Theme toggle resets simulation | `dcc.Store` for UI state only; `sim_engine` runs independently |
| Language switch resets simulation | Same — UI store and engine are completely decoupled |
| Match switch must reset simulation | `select_match` callback is the ONLY place `sim_engine.start()` is called |
| Memory leak on long runs | `deque(maxlen=300)` bounds store size |
| Race condition on thread restart | `threading.Event` stop signal + lock in `sim_engine` |

## Run

```bash
pip install -r requirements.txt
py app/app.py
# Open http://localhost:8050
```

## Deploy (Render / Railway)

Start command: `gunicorn app.app:server --workers=1 --threads=4 --bind=0.0.0.0:$PORT`
