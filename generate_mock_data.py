"""
generate_mock_data.py
---------------------
One-time helper script — run this ONCE to produce data/raw/tweets.csv
before launching the main dashboard.

It creates 500 realistic-looking football match-day tweets with varied
sentiment so the dashboard has data to stream from day one.

Usage:
    python generate_mock_data.py
"""

import csv
import random
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data", "raw", "tweets.csv")

POSITIVE = [
    "What a goal! Absolute worldie from the edge of the box! 🔥⚽",
    "YESSSSS!! 3-1 in extra time!! History made! 🏆🇧🇷",
    "That keeper is absolutely unbeatable tonight. Incredible reflexes.",
    "Best World Cup final in 20 years. Both teams giving everything.",
    "The crowd here in Lusail is electric. Nothing like a World Cup semi.",
    "Mbappe is from another planet. That hat-trick was insane.",
    "Full-time whistle! We're through to the final! 🙌🙌🙌",
    "I've never been more proud of this team. What a performance!",
    "Unreal atmosphere. Football is just the best sport in the world.",
    "That passing sequence — 22 touches before the goal. Beautiful football.",
    "Standing ovation from the whole stadium. Truly deserved.",
    "GOOOOOAL!!! 🎉🎉🎉 Twitter is going to crash tonight I swear",
    "The teamwork and spirit in this squad is something else entirely.",
    "Tears in my eyes. This is why we love football. ❤️⚽",
    "History written tonight. Champions of the world!! 🌍🏆",
]

NEGATIVE = [
    "Absolutely shambles. How do you not defend a set-piece at this level?",
    "The referee is an absolute joke tonight. Two clear penalties ignored.",
    "We should have won that. Terrible finishing all game long. So disappointed.",
    "That red card killed us. Awful decision to lunge in like that.",
    "Out at the group stage. Again. When will this team wake up?",
    "3-0 down at half-time. Just embarrassing to watch.",
    "That goalkeeper cost us the match. Every single error went in.",
    "Boring, negative, defensive football. Zero shots on target. Useless.",
    "The worst performance I've seen from this side in a decade. Disgusting.",
    "Penalty missed in stoppage time. I can't watch this anymore.",
    "VAR overturned a clear goal. The laws of the game are a farce now.",
    "We were outrun, outthought, and outplayed in every area. Deserved to lose.",
    "Gutted. Season over. Going to bed early tonight. 😤",
    "How is that striker even here? Hasn't touched the ball in 60 minutes.",
    "Conceded from a corner again. Same mistake, different tournament.",
]

NEUTRAL = [
    "Half-time. 1-1. Could go either way from here. Edgy stuff.",
    "Both keepers having strong games. Tactical battle in midfield.",
    "Pre-match now. Stadium filling up. Weather looks fine thankfully.",
    "Just checking in — what's the score? Can't find a stream.",
    "Substitution just made. Interesting tactical change from the manager.",
    "0-0 at 70 minutes. Whoever scores next wins this. Nervy.",
    "VAR check underway. Seems like it could be offside.",
    "Possession stats: 52% vs 48%. Very even contest so far.",
    "Yellow card shown. Second of the night for the centre-back.",
    "Injury stoppage. Both physios on the pitch. Hope it's nothing serious.",
    "Drinks break. Manager talking intensely to the midfield right now.",
    "Match kicks off in 10 minutes. Line-ups confirmed a while back.",
    "Players warming up. Noise level rising in the stadium.",
    "Stats at 60 mins: 5 shots each. Fair reflection of the game.",
    "Corner kick to the attacking side. Wall setting up now.",
]

ALL_TWEETS = [(t, "Positive") for t in POSITIVE] + \
             [(t, "Negative") for t in NEGATIVE] + \
             [(t, "Neutral")  for t in NEUTRAL]

# Repeat and shuffle to produce 500 rows
rows = ALL_TWEETS * 12          # 45 templates × 12 ≈ 540
rows = random.sample(rows, 500) # Sample exactly 500, shuffle implicitly

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=["text", "true_label"])
    writer.writeheader()
    for text, label in rows:
        writer.writerow({"text": text, "true_label": label})

print(f"✅ Generated {len(rows)} mock tweets → {OUTPUT_PATH}")
