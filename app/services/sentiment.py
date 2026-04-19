"""
sentiment.py
------------
Wraps the Hugging Face `transformers` pipeline around a pre-trained
RoBERTa model fine-tuned on tweets.  Exposes a single, easy-to-call
function so the rest of the app never needs to touch the HF API directly.
"""

import logging
from functools import lru_cache
from typing import TypedDict

from transformers import pipeline

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# cardiffnlp/twitter-roberta-base-sentiment-latest is the successor to the
# original twitter-roberta-base-sentiment and is trained on 124M tweets.
# Labels: LABEL_0 = Negative  |  LABEL_1 = Neutral  |  LABEL_2 = Positive
MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
MAX_TOKEN_LENGTH = 128   # Keep it short for speed; tweets are ≤ 280 chars
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# Map raw model label strings to human-readable names
LABEL_MAP: dict[str, str] = {
    "LABEL_0": "Negative",
    "LABEL_1": "Neutral",
    "LABEL_2": "Positive",
    "negative": "Negative",
    "neutral":  "Neutral",
    "positive": "Positive",
}

# Numeric score for charting (-1 = Negative, 0 = Neutral, +1 = Positive)
SCORE_MAP: dict[str, float] = {
    "Negative": -1.0,
    "Neutral":   0.0,
    "Positive":  1.0,
}


class SentimentResult(TypedDict):
    """Structured return type for `analyze()`."""
    label: str          # "Positive" | "Neutral" | "Negative"
    confidence: float   # Model's softmax confidence  [0.0, 1.0]
    score: float        # Numeric mapping  {-1, 0, +1}


@lru_cache(maxsize=1)  # Load the model exactly once for the lifetime of the app
def _get_pipeline():
    """
    Lazy-loads the HuggingFace inference pipeline.
    `lru_cache` ensures we only pay the model-load cost a single time.
    """
    logger.info("Loading sentiment model: %s (first run only)", MODEL_NAME)
    return pipeline(
        task="sentiment-analysis",
        model=MODEL_NAME,
        tokenizer=MODEL_NAME,
        max_length=MAX_TOKEN_LENGTH,
        truncation=True,
    )


def analyze(text: str) -> SentimentResult:
    """
    Run sentiment analysis on a single string.

    Args:
        text: Raw tweet or any short text string.

    Returns:
        SentimentResult dict with `label`, `confidence`, and `score`.
    """
    if not text or not text.strip():
        return {"label": "Neutral", "confidence": 1.0, "score": 0.0}

    nlp = _get_pipeline()
    raw: list[dict] = nlp(text)      # Returns e.g. [{"label": "LABEL_2", "score": 0.97}]
    top = raw[0]

    label = LABEL_MAP.get(top["label"], top["label"]).capitalize()
    confidence = round(float(top["score"]), 4)
    score      = SCORE_MAP.get(label, 0.0)

    logger.debug("Tweet: %s → %s (%.2f)", text[:60], label, confidence)
    return {"label": label, "confidence": confidence, "score": score}


# ---------------------------------------------------------------------------
# Smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    samples = [
        "GOOOAL! Argentina wins! What a match! 🏆🇦🇷",
        "Terrible defending. Conceding 3 in 10 minutes is embarrassing.",
        "Half time. 0-0. Both teams playing cautiously.",
    ]
    for s in samples:
        result = analyze(s)
        print(f"[{result['label']:8s} | conf={result['confidence']:.2f}] {s}")
