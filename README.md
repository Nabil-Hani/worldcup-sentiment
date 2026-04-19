# ⚽ World Cup Sentiment Tracker v3

A full multi-page web application tracking fan sentiment across every match of the 2022 World Cup, plus a live preview tracker for World Cup 2026.

## Pages

| Page | Description |
|---|---|
| **Home** | Landing page with feature overview |
| **Past Matches** | All 64 Qatar 2022 matches — click any to replay sentiment |
| **Future Matches** | Live countdown + simulated sentiment for WC 2026 |

## Features
- 🌍 3 languages: English, French, Spanish
- 🌙 Dark / Light mode
- ⚽ All 64 WC 2022 matches with real results
- 🤖 RoBERTa NLP sentiment pipeline
- 📊 Timeline, donut, team comparison charts
- 🔄 Auto tweet source: tweets1.csv (past), tweets.csv (future)

## Setup

```bash
# 1 — Install
pip install -r requirements.txt

# 2 — Add data files to data/raw/
#   tweets.csv   → generated mock tweets (for future matches)
#   tweets1.csv  → real Kaggle WC 2022 tweets (for past matches)
#   Download from: https://www.kaggle.com/datasets/tirendazacademy/fifa-world-cup-2022-tweets

# 3 — Optional: add football-data.org key for live fixtures
echo "FOOTBALL_API_KEY=your_key" > .env

# 4 — Run
py app/app.py
```

Open http://localhost:8050

## Directory structure

```
wc-tracker/
├── app/
│   ├── app.py          ← Entry point
│   ├── wc2022_data.py  ← All 64 WC 2022 matches
│   ├── i18n.py         ← EN / FR / ES translations
│   ├── fixtures.py     ← WC 2026 upcoming fixtures
│   ├── simulator.py    ← Tweet stream generator
│   ├── sentiment.py    ← RoBERTa wrapper
│   ├── state.py        ← Thread-safe data store
│   └── assets/
│       └── style.css   ← Full premium stylesheet
├── data/raw/
│   ├── tweets.csv      ← Mock data (future matches)
│   └── tweets1.csv     ← Real Kaggle tweets (past matches)
└── requirements.txt
```
