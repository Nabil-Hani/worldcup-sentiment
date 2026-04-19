"""
simulator.py
------------
A data-streaming simulator that mimics a real-time tweet feed.
Reads a CSV of historical football tweets line-by-line and yields
them at a configurable interval, acting as a lightweight stand-in
for a live Twitter/X API stream.
"""

import time
import csv
import os
import logging
from typing import Generator, Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEFAULT_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "raw", "tweets.csv"
)
DEFAULT_TWEET_COLUMN = "text"   # Column name that holds the tweet text
DEFAULT_INTERVAL    = 1.5       # Seconds to wait between yielding each tweet
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def tweet_stream(
    csv_path: str = DEFAULT_DATA_PATH,
    tweet_col: str = DEFAULT_TWEET_COLUMN,
    interval: float = DEFAULT_INTERVAL,
    loop: bool = True,
) -> Generator[str, None, None]:
    """
    A generator that yields tweet strings from a CSV file.

    Args:
        csv_path  : Path to the CSV file containing tweets.
        tweet_col : Name of the CSV column that holds the raw tweet text.
        interval  : Seconds to sleep between each yielded tweet.
        loop      : If True, restarts from the top of the file when exhausted
                    (useful for demos that run indefinitely).

    Yields:
        str: A single tweet string.
    """
    if not os.path.exists(csv_path):
        logger.error("Tweet CSV not found at: %s", csv_path)
        raise FileNotFoundError(f"Tweet CSV not found at: {csv_path}")

    while True:  # Outer loop enables `loop=True` replaying
        logger.info("Starting tweet stream from: %s", csv_path)

        with open(csv_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)

            if tweet_col not in (reader.fieldnames or []):
                raise ValueError(
                    f"Column '{tweet_col}' not found. Available: {reader.fieldnames}"
                )

            for row in reader:
                tweet_text = row[tweet_col].strip()

                if not tweet_text:   # Skip empty rows
                    continue

                yield tweet_text
                time.sleep(interval)

        if not loop:
            logger.info("Stream exhausted and loop=False. Stopping.")
            break

        logger.info("Stream exhausted. Looping back to start.")


# ---------------------------------------------------------------------------
# Standalone smoke-test — run `python simulator.py` directly to verify
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    for i, tweet in enumerate(tweet_stream(loop=False)):
        print(f"[Tweet {i+1}] {tweet}")
        if i >= 4:          # Print only the first 5 for the test
            print("... (stopping early in smoke-test mode)")
            break
