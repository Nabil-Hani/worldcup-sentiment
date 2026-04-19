"""
config/settings.py
------------------
Central configuration. All magic numbers and paths live here.
"""
import os

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT_DIR   = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR   = os.path.join(ROOT_DIR, "data", "raw")
PAST_CSV   = os.path.join(DATA_DIR, "tweets1.csv")   # Real 2022 Kaggle tweets
FUTURE_CSV = os.path.join(DATA_DIR, "tweets.csv")    # Mock generated tweets

# ── NLP ───────────────────────────────────────────────────────────────────────
MODEL_NAME       = "cardiffnlp/twitter-roberta-base-sentiment-latest"
MAX_TOKEN_LENGTH = 128
STREAM_INTERVAL  = 1.2   # seconds between tweets

# ── Dashboard ─────────────────────────────────────────────────────────────────
STORE_MAX_RECORDS = 300
FAST_INTERVAL_MS  = 1_000
SLOW_INTERVAL_MS  = 3_000

# ── Colors ────────────────────────────────────────────────────────────────────
SENTIMENT_COLORS = {
    "Positive": "#22c55e",
    "Neutral":  "#eab308",
    "Negative": "#ef4444",
}
TEAM_COLORS = {
    "home": "#6366f1",
    "away": "#f97316",
}
ACCENT = "#3b82f6"

# ── Football API ──────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv; load_dotenv(os.path.join(ROOT_DIR, ".env"))
except ImportError:
    pass
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "")
