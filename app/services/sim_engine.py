"""
services/sim_engine.py
----------------------
Singleton simulation engine.
The key architectural decision: the engine runs independently of the UI.
Theme toggles, language switches, and page navigation NEVER restart it.
Only an explicit match selection does.
"""

import os, sys, threading, datetime, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.simulator import tweet_stream
from services.sentiment import analyze
from services.state     import store, SentimentRecord
from config.settings    import PAST_CSV, FUTURE_CSV

logger = logging.getLogger(__name__)

_stop_event   = threading.Event()
_lock         = threading.Lock()
_session: dict = {
    "home":     None,
    "away":     None,
    "csv":      FUTURE_CSV,
    "match_id": None,
    "started":  False,
}


def _worker(home: str, away: str, csv_path: str, stop_ev: threading.Event):
    logger.info("Engine worker: %s vs %s | %s", home, away, os.path.basename(csv_path))
    try:
        for tweet in tweet_stream(home_team=home, away_team=away, csv_path=csv_path):
            if stop_ev.is_set():
                logger.info("Engine worker stopped.")
                return
            result = analyze(tweet)
            tl  = tweet.lower()
            hk  = home.lower().split()[0]
            ak  = away.lower().split()[0]
            tag = "home" if (hk in tl and ak not in tl) else \
                  "away" if (ak in tl and hk not in tl) else "both"
            rec = SentimentRecord(
                timestamp  = datetime.datetime.utcnow().isoformat(timespec="seconds"),
                tweet      = tweet[:140],
                label      = result["label"],
                confidence = result["confidence"],
                score      = result["score"],
            )
            rec.__dict__["team_tag"] = tag
            store.append(rec)
    except FileNotFoundError as e:
        logger.error("CSV not found: %s", e)
    except Exception as e:
        logger.error("Worker error: %s", e)


def start(home: str, away: str, use_past: bool = False):
    """
    Start (or restart) the simulation for a given match.
    Calling this is the ONLY way to reset the stream.
    Theme/language changes must NEVER call this.
    """
    global _stop_event

    with _lock:
        # Signal old thread to stop
        _stop_event.set()
        _stop_event = threading.Event()

        csv_path = PAST_CSV if use_past else FUTURE_CSV

        # Check CSV exists — fall back gracefully
        if not os.path.exists(csv_path):
            alt = FUTURE_CSV if use_past else PAST_CSV
            if os.path.exists(alt):
                logger.warning("CSV %s not found, falling back to %s", csv_path, alt)
                csv_path = alt
            else:
                logger.error("No CSV found at all. Stream will not start.")
                return

        _session.update(home=home, away=away, csv=csv_path, started=True)
        store._records.clear()

        t = threading.Thread(
            target=_worker,
            args=(home, away, csv_path, _stop_event),
            daemon=True,
            name="SimEngine",
        )
        t.start()
        logger.info("Engine started (thread id=%d)", t.ident)


def get_session() -> dict:
    """Return a copy of the current session state (thread-safe)."""
    with _lock:
        return dict(_session)
