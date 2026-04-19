"""
simulator.py
------------
Streams real tweets from a Kaggle World Cup tweet dataset.
Filters by team name so sentiment is match-specific.

Kaggle dataset to download:
  "FIFA World Cup 2022 Tweets" by datasets owner: hammadjavaid
  URL: https://www.kaggle.com/datasets/hammadjavaid/fifa-world-cup-2022-tweets
  File: FIFA_world_cup_tweets.csv  (place in data/raw/)

  Alternative (larger):
  "World Cup Twitter Dataset" — search Kaggle for "world cup tweets 2022"

Expected CSV columns (flexible — see TWEET_COL / TEAM_COL below):
  text        : raw tweet text
  (optional)  : any column mentioning team names for filtering
"""

import os
import time
import csv
import random
import logging
from typing import Generator, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — adjust to match your downloaded CSV column names
# ---------------------------------------------------------------------------
DEFAULT_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "raw", "tweets.csv"
)
TWEET_COL        = "text"       # Column containing tweet text
DEFAULT_INTERVAL = 1.2          # Seconds between tweets
# ---------------------------------------------------------------------------


def tweet_stream(
    home_team: Optional[str] = None,
    away_team: Optional[str] = None,
    csv_path: str = DEFAULT_DATA_PATH,
    interval: float = DEFAULT_INTERVAL,
    loop: bool = True,
    shuffle: bool = True,
) -> Generator[str, None, None]:
    """
    Generator that streams tweets from a CSV file.

    If home_team / away_team are provided, filters to tweets that mention
    either team — making the sentiment match-specific.

    Args:
        home_team : Filter tweets mentioning this team (optional).
        away_team : Filter tweets mentioning this team (optional).
        csv_path  : Path to the tweets CSV file.
        interval  : Seconds to sleep between each tweet.
        loop      : Restart from the top when file is exhausted.
        shuffle   : Shuffle tweets before streaming (more realistic).

    Yields:
        str: A single tweet string.
    """
    if not os.path.exists(csv_path):
        logger.error("Tweet CSV not found at: %s", csv_path)
        raise FileNotFoundError(f"Tweet CSV not found at: {csv_path}")

    # Build keyword filter list from team names
    keywords = []
    if home_team:
        keywords.extend(_team_keywords(home_team))
    if away_team:
        keywords.extend(_team_keywords(away_team))
    keywords = [k.lower() for k in keywords]

    logger.info("Starting stream | filter keywords: %s", keywords or "none (all tweets)")

    while True:
        tweets = _load_tweets(csv_path, keywords)

        if not tweets:
            logger.warning("No tweets matched the filter — streaming all tweets.")
            tweets = _load_tweets(csv_path, [])

        if shuffle:
            random.shuffle(tweets)

        for tweet in tweets:
            yield tweet
            time.sleep(interval)

        if not loop:
            logger.info("Stream exhausted. loop=False, stopping.")
            break

        logger.info("Stream exhausted — looping.")


def _load_tweets(csv_path: str, keywords: list[str]) -> list[str]:
    """Load and optionally filter tweets from CSV into memory."""
    tweets = []
    try:
        with open(csv_path, newline="", encoding="utf-8", errors="replace") as fh:
            reader = csv.DictReader(fh)

            # Find the text column (flexible — tries common names)
            col = _find_column(reader.fieldnames or [], TWEET_COL)
            if not col:
                logger.error("Could not find tweet text column. Available: %s",
                             reader.fieldnames)
                return []

            for row in reader:
                text = row.get(col, "").strip()
                if not text:
                    continue
                if keywords:
                    text_lower = text.lower()
                    if not any(kw in text_lower for kw in keywords):
                        continue
                tweets.append(text)

    except Exception as e:
        logger.error("Error reading CSV: %s", e)

    logger.info("Loaded %d tweets from %s", len(tweets), csv_path)
    return tweets


def _find_column(fieldnames: list[str], preferred: str) -> Optional[str]:
    """Find the best matching column name (case-insensitive)."""
    # Try exact match first
    if preferred in fieldnames:
        return preferred
    # Try case-insensitive
    for col in fieldnames:
        if col.lower() == preferred.lower():
            return col
    # Try common alternatives
    for candidate in ["tweet", "content", "body", "message", "full_text"]:
        for col in fieldnames:
            if col.lower() == candidate:
                return col
    # Return first column as fallback
    return fieldnames[0] if fieldnames else None


def _team_keywords(team_name: str) -> list[str]:
    """
    Expand a team name into search keywords.
    e.g. "United States" -> ["United States", "USA", "USMNT"]
    """
    base = [team_name]
    aliases = {
        "United States": ["USA", "USMNT", "US Soccer"],
        "South Korea":   ["Korea", "KOR"],
        "Saudi Arabia":  ["KSA", "Saudi"],
        "Costa Rica":    ["CRC"],
        "South Africa":  ["Bafana"],
        "Ivory Coast":   ["Cote d'Ivoire"],
        "England":       ["Three Lions", "ENG"],
        "Brazil":        ["Selecao", "BRA"],
        "Argentina":     ["Albiceleste", "ARG"],
        "France":        ["Les Bleus", "FRA"],
        "Germany":       ["Die Mannschaft", "GER"],
        "Spain":         ["La Roja", "ESP"],
        "Portugal":      ["Selecao", "POR"],
        "Netherlands":   ["Holland", "Oranje", "NED"],
        "Morocco":       ["Atlas Lions", "MAR"],
        "Japan":         ["Samurai Blue", "JPN"],
        "Mexico":        ["El Tri", "MEX"],
    }
    base.extend(aliases.get(team_name, []))
    return base


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    for i, tweet in enumerate(tweet_stream(home_team="Brazil", away_team="Argentina",
                                            loop=False, shuffle=False)):
        print(f"[{i+1}] {tweet[:100]}")
        if i >= 4:
            break
