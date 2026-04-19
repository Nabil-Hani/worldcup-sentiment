"""
state.py
--------
Thread-safe, in-memory store that buffers the live sentiment results
produced by the background simulator thread and consumed by the Dash
callback on every Interval tick.

Using a `deque` with a fixed `maxlen` ensures memory usage is bounded
even for very long demo runs.
"""

import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Deque

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MAX_HISTORY = 200    # Maximum number of data-points kept in memory
# ---------------------------------------------------------------------------


@dataclass
class SentimentRecord:
    """One processed tweet's result."""
    timestamp: str      # ISO-8601 string, e.g. "2024-07-14T18:05:23"
    tweet: str          # Raw tweet text (truncated for display)
    label: str          # "Positive" | "Neutral" | "Negative"
    confidence: float   # [0.0, 1.0]
    score: float        # -1 | 0 | +1


class SentimentStore:
    """
    Thread-safe ring-buffer that stores the most recent sentiment records.

    The background simulator thread writes via `append()`.
    The Dash callback thread reads via `get_all()` — both are protected
    by the same reentrant lock, so no race conditions occur.
    """

    def __init__(self, maxlen: int = MAX_HISTORY):
        self._lock: threading.RLock = threading.RLock()
        self._records: Deque[SentimentRecord] = deque(maxlen=maxlen)

    def append(self, record: SentimentRecord) -> None:
        """Add a new record (called from the simulator thread)."""
        with self._lock:
            self._records.append(record)

    def get_all(self) -> list[SentimentRecord]:
        """Return a snapshot of all stored records (called from Dash thread)."""
        with self._lock:
            return list(self._records)

    def __len__(self) -> int:
        with self._lock:
            return len(self._records)


# Singleton — imported and shared across app.py, background threads, etc.
store = SentimentStore()
