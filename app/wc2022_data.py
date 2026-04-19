"""
wc2022_data.py
--------------
Complete list of all 64 FIFA World Cup 2022 matches with results.
Used to power the "Past Matches" page.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class WC2022Match:
    id: str
    stage: str          # Group A-H, Round of 16, Quarter, Semi, Third, Final
    home: str
    away: str
    home_flag: str      # emoji flag
    away_flag: str
    date: str           # "2022-11-20"
    kickoff: str        # "16:00 UTC"
    home_score: int
    away_score: int
    home_score_aet: Optional[int] = None   # after extra time
    away_score_aet: Optional[int] = None
    home_pens: Optional[int] = None
    away_pens: Optional[int] = None
    stadium: str = ""
    group: str = ""

    @property
    def result_str(self) -> str:
        s = f"{self.home_score} – {self.away_score}"
        if self.home_score_aet is not None:
            s += f" (AET {self.home_score_aet}–{self.away_score_aet})"
        if self.home_pens is not None:
            s += f" | {self.home_pens}–{self.away_pens} pens"
        return s

    @property
    def winner(self) -> Optional[str]:
        hs = self.home_score_aet if self.home_score_aet is not None else self.home_score
        as_ = self.away_score_aet if self.away_score_aet is not None else self.away_score
        if self.home_pens is not None:
            return self.home if self.home_pens > self.away_pens else self.away
        if hs > as_:
            return self.home
        elif as_ > hs:
            return self.away
        return None  # Draw


FLAGS = {
    "Qatar": "🇶🇦", "Ecuador": "🇪🇨", "Senegal": "🇸🇳", "Netherlands": "🇳🇱",
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Iran": "🇮🇷", "USA": "🇺🇸", "Wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    "Argentina": "🇦🇷", "Saudi Arabia": "🇸🇦", "Denmark": "🇩🇰", "Tunisia": "🇹🇳",
    "Mexico": "🇲🇽", "Poland": "🇵🇱", "France": "🇫🇷", "Australia": "🇦🇺",
    "Morocco": "🇲🇦", "Croatia": "🇭🇷", "Germany": "🇩🇪", "Japan": "🇯🇵",
    "Spain": "🇪🇸", "Costa Rica": "🇨🇷", "Belgium": "🇧🇪", "Canada": "🇨🇦",
    "Switzerland": "🇨🇭", "Cameroon": "🇨🇲", "Uruguay": "🇺🇾", "South Korea": "🇰🇷",
    "Portugal": "🇵🇹", "Ghana": "🇬🇭", "Brazil": "🇧🇷", "Serbia": "🇷🇸",
}

def flag(team: str) -> str:
    return FLAGS.get(team, "🏳️")


ALL_MATCHES: list[WC2022Match] = [
    # ── Group A ──────────────────────────────────────────────────────────────
    WC2022Match("a1","Group A","Qatar","Ecuador",flag("Qatar"),flag("Ecuador"),"2022-11-20","16:00",0,2,stadium="Al Bayt",group="A"),
    WC2022Match("a2","Group A","Senegal","Netherlands",flag("Senegal"),flag("Netherlands"),"2022-11-21","13:00",0,2,stadium="Al Thumama",group="A"),
    WC2022Match("a3","Group A","Qatar","Senegal",flag("Qatar"),flag("Senegal"),"2022-11-25","10:00",1,3,stadium="Al Thumama",group="A"),
    WC2022Match("a4","Group A","Netherlands","Ecuador",flag("Netherlands"),flag("Ecuador"),"2022-11-25","16:00",1,1,stadium="Khalifa",group="A"),
    WC2022Match("a5","Group A","Ecuador","Senegal",flag("Ecuador"),flag("Senegal"),"2022-11-29","18:00",1,2,stadium="Khalifa",group="A"),
    WC2022Match("a6","Group A","Netherlands","Qatar",flag("Netherlands"),flag("Qatar"),"2022-11-29","18:00",2,0,stadium="Al Bayt",group="A"),
    # ── Group B ──────────────────────────────────────────────────────────────
    WC2022Match("b1","Group B","England","Iran",flag("England"),flag("Iran"),"2022-11-21","16:00",6,2,stadium="Khalifa",group="B"),
    WC2022Match("b2","Group B","USA","Wales",flag("USA"),flag("Wales"),"2022-11-21","19:00",1,1,stadium="Ahmad Bin Ali",group="B"),
    WC2022Match("b3","Group B","Wales","Iran",flag("Wales"),flag("Iran"),"2022-11-25","10:00",0,2,stadium="Ahmad Bin Ali",group="B"),
    WC2022Match("b4","Group B","England","USA",flag("England"),flag("USA"),"2022-11-25","19:00",0,0,stadium="Al Bayt",group="B"),
    WC2022Match("b5","Group B","Wales","England",flag("Wales"),flag("England"),"2022-11-29","18:00",0,3,stadium="Ahmad Bin Ali",group="B"),
    WC2022Match("b6","Group B","Iran","USA",flag("Iran"),flag("USA"),"2022-11-29","18:00",0,1,stadium="Al Thumama",group="B"),
    # ── Group C ──────────────────────────────────────────────────────────────
    WC2022Match("c1","Group C","Argentina","Saudi Arabia",flag("Argentina"),flag("Saudi Arabia"),"2022-11-22","10:00",1,2,stadium="Lusail",group="C"),
    WC2022Match("c2","Group C","Mexico","Poland",flag("Mexico"),flag("Poland"),"2022-11-22","16:00",0,0,stadium="Stadium 974",group="C"),
    WC2022Match("c3","Group C","Poland","Saudi Arabia",flag("Poland"),flag("Saudi Arabia"),"2022-11-26","13:00",2,0,stadium="Education City",group="C"),
    WC2022Match("c4","Group C","Argentina","Mexico",flag("Argentina"),flag("Mexico"),"2022-11-26","19:00",2,0,stadium="Lusail",group="C"),
    WC2022Match("c5","Group C","Poland","Argentina",flag("Poland"),flag("Argentina"),"2022-11-30","18:00",0,2,stadium="Stadium 974",group="C"),
    WC2022Match("c6","Group C","Saudi Arabia","Mexico",flag("Saudi Arabia"),flag("Mexico"),"2022-11-30","18:00",1,2,stadium="Lusail",group="C"),
    # ── Group D ──────────────────────────────────────────────────────────────
    WC2022Match("d1","Group D","Denmark","Tunisia",flag("Denmark"),flag("Tunisia"),"2022-11-22","13:00",0,0,stadium="Education City",group="D"),
    WC2022Match("d2","Group D","France","Australia",flag("France"),flag("Australia"),"2022-11-22","19:00",4,1,stadium="Al Janoub",group="D"),
    WC2022Match("d3","Group D","Tunisia","Australia",flag("Tunisia"),flag("Australia"),"2022-11-26","10:00",0,1,stadium="Al Janoub",group="D"),
    WC2022Match("d4","Group D","France","Denmark",flag("France"),flag("Denmark"),"2022-11-26","16:00",2,1,stadium="Stadium 974",group="D"),
    WC2022Match("d5","Group D","Australia","Denmark",flag("Australia"),flag("Denmark"),"2022-11-30","18:00",1,0,stadium="Al Janoub",group="D"),
    WC2022Match("d6","Group D","Tunisia","France",flag("Tunisia"),flag("France"),"2022-11-30","18:00",1,0,stadium="Education City",group="D"),
    # ── Group E ──────────────────────────────────────────────────────────────
    WC2022Match("e1","Group E","Spain","Costa Rica",flag("Spain"),flag("Costa Rica"),"2022-11-23","16:00",7,0,stadium="Al Thumama",group="E"),
    WC2022Match("e2","Group E","Germany","Japan",flag("Germany"),flag("Japan"),"2022-11-23","19:00",1,2,stadium="Khalifa",group="E"),
    WC2022Match("e3","Group E","Japan","Costa Rica",flag("Japan"),flag("Costa Rica"),"2022-11-27","10:00",0,1,stadium="Ahmad Bin Ali",group="E"),
    WC2022Match("e4","Group E","Spain","Germany",flag("Spain"),flag("Germany"),"2022-11-27","19:00",1,1,stadium="Al Bayt",group="E"),
    WC2022Match("e5","Group E","Japan","Spain",flag("Japan"),flag("Spain"),"2022-12-01","18:00",2,1,stadium="Khalifa",group="E"),
    WC2022Match("e6","Group E","Costa Rica","Germany",flag("Costa Rica"),flag("Germany"),"2022-12-01","18:00",2,4,stadium="Al Bayt",group="E"),
    # ── Group F ──────────────────────────────────────────────────────────────
    WC2022Match("f1","Group F","Belgium","Canada",flag("Belgium"),flag("Canada"),"2022-11-23","13:00",1,0,stadium="Ahmad Bin Ali",group="F"),
    WC2022Match("f2","Group F","Morocco","Croatia",flag("Morocco"),flag("Croatia"),"2022-11-23","10:00",0,0,stadium="Al Bayt",group="F"),
    WC2022Match("f3","Group F","Belgium","Morocco",flag("Belgium"),flag("Morocco"),"2022-11-27","13:00",0,2,stadium="Al Thumama",group="F"),
    WC2022Match("f4","Group F","Croatia","Canada",flag("Croatia"),flag("Canada"),"2022-11-27","16:00",4,1,stadium="Khalifa",group="F"),
    WC2022Match("f5","Group F","Croatia","Belgium",flag("Croatia"),flag("Belgium"),"2022-12-01","18:00",0,0,stadium="Al Thumama",group="F"),
    WC2022Match("f6","Group F","Canada","Morocco",flag("Canada"),flag("Morocco"),"2022-12-01","18:00",1,2,stadium="Al Thumama",group="F"),
    # ── Group G ──────────────────────────────────────────────────────────────
    WC2022Match("g1","Group G","Switzerland","Cameroon",flag("Switzerland"),flag("Cameroon"),"2022-11-24","10:00",1,0,stadium="Al Janoub",group="G"),
    WC2022Match("g2","Group G","Brazil","Serbia",flag("Brazil"),flag("Serbia"),"2022-11-24","19:00",2,0,stadium="Lusail",group="G"),
    WC2022Match("g3","Group G","Cameroon","Serbia",flag("Cameroon"),flag("Serbia"),"2022-11-28","13:00",3,3,stadium="Al Janoub",group="G"),
    WC2022Match("g4","Group G","Brazil","Switzerland",flag("Brazil"),flag("Switzerland"),"2022-11-28","19:00",1,0,stadium="Stadium 974",group="G"),
    WC2022Match("g5","Group G","Serbia","Switzerland",flag("Serbia"),flag("Switzerland"),"2022-12-02","18:00",2,3,stadium="Stadium 974",group="G"),
    WC2022Match("g6","Group G","Cameroon","Brazil",flag("Cameroon"),flag("Brazil"),"2022-12-02","18:00",1,0,stadium="Lusail",group="G"),
    # ── Group H ──────────────────────────────────────────────────────────────
    WC2022Match("h1","Group H","Uruguay","South Korea",flag("Uruguay"),flag("South Korea"),"2022-11-24","13:00",0,0,stadium="Education City",group="H"),
    WC2022Match("h2","Group H","Portugal","Ghana",flag("Portugal"),flag("Ghana"),"2022-11-24","16:00",3,2,stadium="Stadium 974",group="H"),
    WC2022Match("h3","Group H","South Korea","Ghana",flag("South Korea"),flag("Ghana"),"2022-11-28","10:00",2,3,stadium="Education City",group="H"),
    WC2022Match("h4","Group H","Portugal","Uruguay",flag("Portugal"),flag("Uruguay"),"2022-11-28","16:00",2,0,stadium="Lusail",group="H"),
    WC2022Match("h5","Group H","Ghana","Uruguay",flag("Ghana"),flag("Uruguay"),"2022-12-02","18:00",0,2,stadium="Al Janoub",group="H"),
    WC2022Match("h6","Group H","South Korea","Portugal",flag("South Korea"),flag("Portugal"),"2022-12-02","18:00",2,1,stadium="Education City",group="H"),
    # ── Round of 16 ──────────────────────────────────────────────────────────
    WC2022Match("r16_1","Round of 16","Netherlands","USA",flag("Netherlands"),flag("USA"),"2022-12-03","16:00",3,1,stadium="Khalifa"),
    WC2022Match("r16_2","Round of 16","Argentina","Australia",flag("Argentina"),flag("Australia"),"2022-12-03","20:00",2,1,stadium="Ahmad Bin Ali"),
    WC2022Match("r16_3","Round of 16","France","Poland",flag("France"),flag("Poland"),"2022-12-04","16:00",3,1,stadium="Al Thumama"),
    WC2022Match("r16_4","Round of 16","England","Senegal",flag("England"),flag("Senegal"),"2022-12-04","20:00",3,0,stadium="Al Bayt"),
    WC2022Match("r16_5","Round of 16","Japan","Croatia",flag("Japan"),flag("Croatia"),"2022-12-05","16:00",1,1,home_score_aet=1,away_score_aet=1,home_pens=1,away_pens=3,stadium="Al Janoub"),
    WC2022Match("r16_6","Round of 16","Brazil","South Korea",flag("Brazil"),flag("South Korea"),"2022-12-05","20:00",4,1,stadium="Stadium 974"),
    WC2022Match("r16_7","Round of 16","Morocco","Spain",flag("Morocco"),flag("Spain"),"2022-12-06","16:00",0,0,home_score_aet=0,away_score_aet=0,home_pens=3,away_pens=0,stadium="Education City"),
    WC2022Match("r16_8","Round of 16","Portugal","Switzerland",flag("Portugal"),flag("Switzerland"),"2022-12-06","20:00",6,1,stadium="Lusail"),
    # ── Quarter Finals ────────────────────────────────────────────────────────
    WC2022Match("qf1","Quarter-Final","Croatia","Brazil",flag("Croatia"),flag("Brazil"),"2022-12-09","16:00",1,1,home_score_aet=1,away_score_aet=1,home_pens=4,away_pens=2,stadium="Education City"),
    WC2022Match("qf2","Quarter-Final","Netherlands","Argentina",flag("Netherlands"),flag("Argentina"),"2022-12-09","20:00",2,2,home_score_aet=2,away_score_aet=2,home_pens=3,away_pens=4,stadium="Lusail"),
    WC2022Match("qf3","Quarter-Final","Morocco","Portugal",flag("Morocco"),flag("Portugal"),"2022-12-10","16:00",1,0,stadium="Al Thumama"),
    WC2022Match("qf4","Quarter-Final","England","France",flag("England"),flag("France"),"2022-12-10","20:00",1,2,stadium="Al Bayt"),
    # ── Semi Finals ───────────────────────────────────────────────────────────
    WC2022Match("sf1","Semi-Final","Argentina","Croatia",flag("Argentina"),flag("Croatia"),"2022-12-13","20:00",3,0,stadium="Lusail"),
    WC2022Match("sf2","Semi-Final","France","Morocco",flag("France"),flag("Morocco"),"2022-12-14","20:00",2,0,stadium="Al Bayt"),
    # ── Third Place ───────────────────────────────────────────────────────────
    WC2022Match("3rd","Third Place","Croatia","Morocco",flag("Croatia"),flag("Morocco"),"2022-12-17","16:00",2,1,stadium="Khalifa"),
    # ── Final ─────────────────────────────────────────────────────────────────
    WC2022Match("final","Final","Argentina","France",flag("Argentina"),flag("France"),"2022-12-18","16:00",3,3,home_score_aet=3,away_score_aet=3,home_pens=4,away_pens=2,stadium="Lusail"),
]

MATCHES_BY_ID = {m.id: m for m in ALL_MATCHES}

STAGE_ORDER = ["Group A","Group B","Group C","Group D","Group E","Group F","Group G","Group H",
               "Round of 16","Quarter-Final","Semi-Final","Third Place","Final"]
