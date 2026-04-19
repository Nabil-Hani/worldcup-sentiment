"""
services/match_data.py
----------------------
Generates realistic mock match-state data: odds, lineups, and news.
Odds shift dynamically based on live sentiment — the more positive the
crowd, the more the home team's win probability improves.
"""

import random
from dataclasses import dataclass, field
from typing import Optional


# ── Lineups ───────────────────────────────────────────────────────────────────

SQUAD_POOL = {
    "Argentina":    ["E. Martínez","N. Molina","C. Romero","L. Martínez","M. Acuña",
                     "R. De Paul","E. Fernández","A. Mac Allister","L. Messi","J. Álvarez","A. Di María"],
    "France":       ["H. Lloris","J. Konaté","R. Varane","D. Upamecano","T. Hernández",
                     "A. Tchouaméni","A. Rabiot","O. Dembélé","A. Griezmann","K. Mbappé","O. Giroud"],
    "Brazil":       ["Alisson","Danilo","Thiago Silva","Marquinhos","Alex Sandro",
                     "Casemiro","Lucas Paquetá","Raphinha","Neymar","Vinicius Jr","Richarlison"],
    "England":      ["J. Pickford","K. Walker","J. Stones","H. Maguire","L. Shaw",
                     "D. Rice","J. Bellingham","B. Saka","P. Foden","R. Sterling","H. Kane"],
    "Portugal":     ["D. Costa","J. Cancelo","Pepe","R. Dias","N. Mendes",
                     "Bernardo Silva","Rúben Neves","Bruno Fernandes","B. Silva","João Félix","C. Ronaldo"],
    "Spain":        ["U. Simón","D. Carvajal","E. García","A. Laporte","J. Alba",
                     "Sergio Busquets","Gavi","Pedri","Dani Olmo","F. Torres","A. Morata"],
    "Germany":      ["M. Neuer","B. Pavard","A. Rüdiger","M. Süle","D. Raum",
                     "L. Goretzka","I. Gündogan","J. Kimmich","T. Müller","L. Sané","K. Havertz"],
    "Netherlands":  ["A. Flekken","D. Dumfries","V. van Dijk","J. Timber","T. Blind",
                     "F. de Jong","D. Blind","S. Berghuis","S. Bergwijn","M. Depay","C. Gakpo"],
    "Morocco":      ["Y. Bounou","A. Hakimi","N. Aguerd","R. Saïss","N. Mazraoui",
                     "S. Amrabat","A. Amallah","H. Ziyech","S. Boufal","Y. En-Nesyri","I. Ounahi"],
    "Croatia":      ["D. Livaković","J. Stanišić","D. Vida","L. Gvardiol","B. Sosa",
                     "M. Brozović","L. Modrić","M. Kovačić","I. Perišić","A. Kramarić","B. Petković"],
    "Japan":        ["Gonda","Sakai","Itakura","Yoshida","Nagatomo",
                     "Endo","Tanaka","Kamada","Doan","Minamino","Maeda"],
    "South Korea":  ["Kim Seung-gyu","Kim Moon-hwan","Kim Min-jae","Kwon Gyeong-won","Kim Jin-su",
                     "Jung Woo-young","Hwang In-beom","Lee Jae-sung","Son Heung-min","Hwang Ui-jo","Cho Gue-sung"],
    "USA":          ["M. Turner","S. Dest","W. Zimmerman","T. Ream","A. Robinson",
                     "T. Adams","W. McKennie","Y. Musah","C. Pulisic","B. Aaronson","J. Sargent"],
    "Mexico":       ["G. Ochoa","J. Sánchez","C. Montes","H. Moreno","J. Gallardo",
                     "E. Herrera","A. Guardado","H. Lozano","L. Chávez","R. Jiménez","H. Martín"],
    "Senegal":      ["É. Mendy","B. Sabaly","K. Koulibaly","A. Diallo","F. Mendy",
                     "N. Mendy","I. Gueye","P. Sarr","I. Sarr","B. Diallo","S. Mané"],
    "Australia":    ["M. Ryan","N. Atkinson","H. Souttar","K. Rowles","M. Behich",
                     "A. Mooy","R. McGree","B. Irvine","M. Leckie","M. Duke","M. Goodwin"],
    "Poland":       ["W. Szczesny","M. Cash","G. Bednarek","J. Kiwior","B. Bereszynski",
                     "G. Krychowiak","J. Zielinski","P. Zielinski","K. Swiderski","A. Milik","R. Lewandowski"],
    "Switzerland":  ["Y. Sommer","S. Widmer","M. Akanji","N. Elvedi","R. Rodriguez",
                     "G. Xhaka","R. Freuler","X. Shaqiri","R. Vargas","B. Embolo","N. Okafor"],
    "Uruguay":      ["F. Muslera","G. de Arrascaeta","D. Godín","J. Giménez","M. Olivera",
                     "F. Valverde","M. Vecino","R. Bentancur","F. Pellistri","L. Suárez","D. Núñez"],
    "Ghana":        ["L. Ati-Zigi","A. Ayew","D. Amartey","A. Salisu","G. Mensah",
                     "T. Partey","M. Kudus","J. Ayew","O. Paintsil","I. Williams","J. Benson"],
    "Serbia":       ["V. Milinkovic-Savić","N. Milenkovic","S. Pavlovic","S. Veljkovic","M. Lazovic",
                     "S. Milinkovic-Savic","N. Gudelj","F. Kostic","A. Tadic","L. Jovic","A. Mitrovic"],
    "Cameroon":     ["A. Onana","C. Fai","J. Castelletto","N. N'Koulou","U. Tolo",
                     "M. Anguissa","P. Ondoa","N. Nkoudou","V. Aboubakar","B. Ekambi","G. Moumi Ngamaleu"],
    "Tunisia":      ["A. Dahmen","W. Hichri","Y. Meriah","D. Bronn","A. Abdi",
                     "E. Skhiri","A. Laidouni","H. Msakni","Y. Jebali","S. Jaziri","N. Sliti"],
    "Denmark":      ["K. Schmeichel","J. Andersen","A. Christensen","V. Kühn","J. Maehle",
                     "P. Hjulmand","T. Delaney","M. Eriksen","A. Skov Olsen","K. Dolberg","K. Braithwaite"],
    "Belgium":      ["T. Courtois","T. Castagne","J. Vertonghen","T. Alderweireld","A. Theate",
                     "Y. Tielemans","A. Witsel","K. De Bruyne","T. Hazard","R. Lukaku","E. Hazard"],
    "Canada":       ["M. Crepeau","R. Laryea","K. Miller","D. Vitoria","S. Johnston",
                     "S. Eustaquio","M. Kaye","T. Davies","J. David","C. Buchanan","L. Larin"],
    "Costa Rica":   ["K. Navas","J. Fuller","F. Calvo","O. Duarte","B. Oviedo",
                     "C. Borges","Y. Tejeda","G. Torres","B. Ruiz","J. Campbell","A. Contreras"],
    "Wales":        ["W. Hennessey","B. Davies","C. Mepham","J. Rodon","N. Williams",
                     "J. Morrell","J. Allen","D. James","H. Wilson","G. Bale","K. Moore"],
    "Iran":         ["A. Beiranvand","E. Hajsafi","M. Hosseini","M. Cheshmi","R. Rezaeian",
                     "M. Ezatolahi","A. Nourollahi","A. Jahanbakhsh","M. Taremi","S. Azmoun","V. Amiri"],
    "Ecuador":      ["H. Galíndez","A. Preciado","F. Hincapié","P. Hincapié","P. Estupiñán",
                     "C. Gruezo","J. Plata","M. Caicedo","A. Mena","E. Valencia","G. Cifuentes"],
    "Qatar":        ["M. Barsham","P. Correia","B. Al-Rawi","A. Salman","H. Al-Haydos",
                     "K. Boudiaf","A. Al-Haydos","H. Al-Haydos","M. Muntari","A. Afif","A. Al-Shahrani"],
    "Saudi Arabia": ["M. Al-Owais","S. Al-Ghannam","A. Al-Amri","A. Al-Bulaihi","Y. Al-Shahrani",
                     "M. Al-Burayk","S. Al-Dawsari","H. Al-Tambakti","M. Al-Burayk","F. Al-Brikan","S. Al-Shehri"],
}

NEWS_POOL = {
    "Argentina": [
        "Messi produces another moment of magic as Argentina dominate possession.",
        "Di María's pace causing major problems down the left flank.",
        "Argentina's pressing game nullifying the opposition midfield effectively.",
        "Álvarez links up brilliantly with Messi in the final third.",
    ],
    "France": [
        "Mbappé's electric pace is tearing the defence apart repeatedly.",
        "Griezmann dictating the tempo from his advanced midfield role.",
        "France's defensive block looking extremely well-organised tonight.",
        "Giroud making intelligent runs to stretch the opposition backline.",
    ],
    "Brazil": [
        "Vinicius Jr. causing chaos with his direct running at defenders.",
        "Brazil's samba football drawing gasps from the Lusail crowd.",
        "Neymar dropping deep to receive and drive the tempo higher.",
        "Richarlison's movement making life incredibly difficult for the centre-backs.",
    ],
    "England": [
        "Bellingham's box-to-box energy setting the standard for England.",
        "Kane dropping deep to link play and threading incisive passes.",
        "Saka and Sterling combining with precision down the right flank.",
        "England's high press forcing errors in the opposition build-up.",
    ],
    "Morocco": [
        "Morocco's defensive organisation has been absolutely impeccable so far.",
        "Ziyech's creativity from wide areas opening up space centrally.",
        "Bounou making another crucial save to keep Morocco in it.",
        "Hakimi's overlapping runs creating a constant threat on the right.",
    ],
    "default": [
        "Both sides giving everything in what is proving to be a tactical battle.",
        "The referee is the centre of attention after a controversial decision.",
        "Substitutions have changed the dynamic of the second half significantly.",
        "A moment of individual brilliance has shifted the momentum completely.",
        "The crowd here in Qatar is absolutely electric tonight.",
        "The manager makes a bold tactical switch that surprises everyone.",
        "A VAR check has halted play — tension rising in the stadium.",
        "Injury concern as the physios rush on to attend to a player.",
    ]
}


@dataclass
class MatchOdds:
    home_win: float
    draw: float
    away_win: float

    def to_dict(self):
        return {"home": self.home_win, "draw": self.draw, "away": self.away_win}


@dataclass
class MatchState:
    home_team:   str
    away_team:   str
    home_lineup: list[str]
    away_lineup: list[str]
    odds:        MatchOdds
    news:        list[str]
    minute:      Optional[int] = None   # None = pre-match


def _get_lineup(team: str) -> list[str]:
    pool = SQUAD_POOL.get(team)
    if pool and len(pool) >= 11:
        return pool[:11]
    return [f"Player {i+1}" for i in range(11)]


def get_match_state(home: str, away: str,
                    sentiment_mean: float = 0.0,
                    minute: Optional[int] = None) -> MatchState:
    """
    Generate a realistic MatchState.
    Odds shift by ±5% based on sentiment_mean: positive crowd → home improves.
    """
    # Base odds (roughly realistic for an even match)
    base_home = 0.40
    base_draw = 0.28
    base_away = 0.32

    # Sentiment nudge: clamp to ±0.08
    nudge = max(-0.08, min(0.08, sentiment_mean * 0.08))
    home_win = round(base_home + nudge, 3)
    away_win = round(base_away - nudge, 3)
    draw     = round(1.0 - home_win - away_win, 3)
    draw     = max(0.05, draw)

    # Pick news items relevant to these teams
    pool = (NEWS_POOL.get(home, []) + NEWS_POOL.get(away, []) + NEWS_POOL["default"])
    random.shuffle(pool)
    news = pool[:4]

    return MatchState(
        home_team   = home,
        away_team   = away,
        home_lineup = _get_lineup(home),
        away_lineup = _get_lineup(away),
        odds        = MatchOdds(home_win=home_win, draw=draw, away_win=away_win),
        news        = news,
        minute      = minute,
    )
