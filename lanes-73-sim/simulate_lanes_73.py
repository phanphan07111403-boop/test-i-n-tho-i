#!/usr/bin/env python3
"""
Wild Rift 7.3 — Top 5 jungle / mid / ADC that gain the most from the patch.

Rank = kit buffs this patch + how hard they use 7.3 systems
(crit 200%, AS cap 3, Yun Tal/Hexoptics/IE, farm jungle, 2v2 when jungle farms).
Pad (MB03) is reported, not a hard filter — user asked hưởng lợi, not fit-pad.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import json
import os

PATCH = "7.3"


@dataclass
class Champ:
    key: str
    name: str
    role: str  # jungle | mid | adc
    wrf: str
    kit: int          # 0-40 how much 7.3 changed THIS champion
    system: int       # 0-40 how much they use 7.3 systems
    new: bool = False
    pad: int = 70
    pad_note: str = ""
    why: List[str] = field(default_factory=list)
    skip_why: str = ""  # if not empty, listed as miss

    @property
    def patch_score(self) -> float:
        bonus = 12 if self.new else 0
        return self.kit + self.system + bonus


@dataclass
class Page:
    page: List[str]
    buy: List[str]
    skill: str
    spells: str
    runes: List[str]
    pad: Dict[str, str]
    combo: str
    sit: List[str]


CHAMPS: List[Champ] = [
    # ----- ADC: 7.3 IS the marksman patch -----
    Champ(
        "caitlyn", "Caitlyn", "adc", "B→up", 38, 36, pad=78,
        pad_note="Tầm dài, trap tap gần địch. RFC/Hexoptics kite analog.",
        why=[
            "Kit rebuild: Headshot + R scale crit chance VÀ crit damage (200% + IE 230%).",
            "AD 54→60. AS cho sẵn (growth 4%) nên mua AD/crit — Hexoptics→IE→RFC.",
            "Trap Headshot +40–190 (+30% bAD) mới. Cait 7.2d B-tier, đây là buff lớn nhất ADC.",
        ],
    ),
    Champ(
        "ashe", "Ashe", "adc", "A", 36, 32, pad=90,
        pad_note="Đã dạy MB03: W setup, R giữ/lái, analog kite.",
        why=[
            "AD/level 2.65→4, base AD 60. Frost Shot chậm 20–30% (tăng).",
            "Frost bonus damage = crit rate + (crit dmg−2)×crit — đúng công thức 7.3.",
            "Volley CD 16/13.5/11/8.5 → 15/12/9/6. Ranger's Focus 30 mana. Pad kite.",
        ],
    ),
    Champ(
        "xayah", "Xayah", "adc", "S", 32, 34, pad=76,
        pad_note="E rút lông: Q+1 AA = 3 lông root. R untarget. Nặng hơn Ashe.",
        why=[
            "Bladecaller × (1 + 50% crit + 50%×(crit dmg−2)×crit). Lông = crit item.",
            "AD 54→60. Yun Tal → Navori → IE (WRF 7.3 S-tier).",
            "W Plumage 25% feather dmg (tăng). Hypercarry 7.3.",
        ],
    ),
    Champ(
        "lucian", "Lucian", "adc", "A", 30, 30, pad=82,
        pad_note="Q xả, E dash analog. Combo 2–3 nút. R giữ hướng.",
        why=[
            "The Culling: 20 + 20×crit rate viên, cộng (crit dmg−2)×20×crit. IE = thêm đạn.",
            "Q 100% bAD mọi rank. Lightslinger 40/50/60%. Identity crit rõ.",
            "Fiendhunter Bolts (+50% AS, 3 crit sau R) sinh ra cho cửa sổ ult này.",
        ],
    ),
    Champ(
        "jinx", "Jinx", "adc", "A", 14, 36, pad=84,
        pad_note="Rocket/minigun 1 nút. Zap đường thẳng. Chomper aim vừa.",
        why=[
            "Get Excited vượt AS cap — cap 7.3 lên 3.0, Excited vẫn phá trần.",
            "Hexoptics + Runaan + IE. Rocket splash crit 200%.",
            "R bị cắt CD/ratio — Δpatch thấp hơn Cait/Ashe/Xayah nhưng hệ thống bơm hypercarry.",
        ],
    ),
    Champ(
        "twitch", "Twitch", "adc", "C→up", 28, 26, pad=72,
        pad_note="Q tàng hình rồi xả. E cần độc trong 1200. R spray analog.",
        why=["Rework Ambush +35–50% AS 6s. Fiendhunter đúng kit R."],
        skip_why="Rework lớn nhưng pad/aim R nặng hơn Jinx; WRF còn thấp.",
    ),
    Champ(
        "zeri", "Zeri", "adc", "S", 18, 30, pad=70,
        pad_note="Q = AA, phải kiting liên tục.",
        why=["Q AD-heavy lại. WRF S. Không rebuild nặng như Cait."],
        skip_why="Đã mạnh, kit 7.3 chỉnh nhẹ — không phải người hưởng nhiều nhất.",
    ),
    Champ(
        "jhin", "Jhin", "adc", "S", 8, 18, pad=88,
        pad_note="Đã dạy xả phát 4 / R từng viên.",
        why=["Crit modifier 80% để bù 200% — hưởng hệ thống ÍT hơn ADC khác."],
        skip_why="Riot cắt crit dmg Jhin. Pad đẹp nhưng không phải winner 7.3.",
    ),
    Champ(
        "mf", "Miss Fortune", "adc", "S+", 10, 22, pad=80,
        pad_note="Q bounce, R giữ.",
        why=["Love Tap không double full với crit."],
        skip_why="Vẫn S+ nhưng Love Tap bị cắt — hưởng ít hơn Cait/Ashe.",
    ),
    Champ(
        "smolder", "Smolder", "adc", "S+", 8, 16, pad=74,
        pad_note="Q stack, không phải crit auto.",
        why=["S+ sẵn. Không phải marksman crit overhaul."],
        skip_why="Stack Q, không mua crit 200%.",
    ),
    # ----- MID -----
    Champ(
        "hwei", "Hwei", "mid", "new", 28, 24, new=True, pad=48,
        pad_note="10 chiêu (3 subject). Pad rất nặng — không khuyến MB03.",
        why=[
            "Tướng mới 7.3, mid poster. Disaster / Serenity / Torment = poke + CC + shield.",
            "Jungle farm → 1v1/siege mid. Hwei wave + zone trụ plating.",
            "Pad: quá nhiều nút — rank hưởng patch, không phải pick pad.",
        ],
    ),
    Champ(
        "syndra", "Syndra", "mid", "S+", 18, 30, pad=88,
        pad_note="Đã dạy Q rồi E, hai nút. R lock tướng.",
        why=[
            "WRF S+. Jungle 7.3 farm → mid tự thắng lane. Syndra 2v1/1v1 mạnh.",
            "7.2d Q 80–230, E CD 15s, W 60% AP — buff còn sống vào 7.3.",
            "Luden → Orb → Cap. Combo pad: L1 Q → L2 E stun.",
        ],
    ),
    Champ(
        "ahri", "Ahri", "mid", "S+", 12, 28, pad=86,
        pad_note="Đã dạy E charm rồi xả Q. R dash analog.",
        why=[
            "WRF S+. Roam bot vì ADC 7.3 carry thật — Charm gank dragon.",
            "Malignance + Lich (WRF). Jungle ít gank → Ahri tự roam.",
            "Pad: L2 E trước, L1 Q sau.",
        ],
    ),
    Champ(
        "sylas", "Sylas", "mid", "new", 22, 18, new=True, pad=80,
        pad_note="W choáng rồi Q — combo 2 nút kiểu Pantheon.",
        why=[
            "Tướng mới 7.3. W stun → Q, R cướp ult ADC/jungler 7.3.",
            "Kingslayer heal missing HP. Pad combo ngắn.",
            "Riftmaker / Rocketbelt. Không skillshot dày như Hwei.",
        ],
    ),
    Champ(
        "tf", "Twisted Fate", "mid", "S", 10, 26, pad=78,
        pad_note="W bài giữ–nhả. R global. Q 3 lá aim vừa.",
        why=[
            "Gold card pick + R xuống bot. ADC 7.3 đáng gank hơn.",
            "WRF S. Luden/Lich. Jungle farm → TF roam không mất camp đồng đội.",
        ],
    ),
    Champ(
        "yone", "Yone", "mid", "S+", 6, 14, pad=62,
        pad_note="Q3 dash, E clone — analog nặng.",
        why=["S+ nhưng crit modifier 90% (cắt như Jhin). Không hưởng 200% full."],
        skip_why="Crit bị cắt 90%. S+ sẵn, không phải winner 7.3.",
    ),
    Champ(
        "annie", "Annie", "mid", "S", 8, 20, pad=90,
        pad_note="Q xả, R tibbers. Đơn giản.",
        why=["Lane bully khi jungle farm. Không có buff kit 7.3."],
        skip_why="Pad dễ nhưng Δpatch thấp hơn Hwei/Syndra/Ahri/Sylas/TF.",
    ),
    # ----- JUNGLE: farm jungle + Rek'Sai -----
    Champ(
        "reksai", "Rek'Sai", "jungle", "new", 26, 28, new=True, pad=82,
        pad_note="Q đào, W unburrow knockup (gần gồng/nhả). R lock.",
        why=[
            "Tướng mới 7.3 jungle. Unburrow knockup, ult sense địch ẩn.",
            "Tunnel clear + gank đúng meta farm-then-crash.",
            "Smite burn 600→1400 giúp duel camp/epic. Pad: W nhả gần, R targeted.",
        ],
    ),
    Champ(
        "nidalee", "Nidalee", "jungle", "S+", 16, 34, pad=58,
        pad_note="Q giáo aim — đã có sim spear, vẫn khó analog.",
        why=[
            "WRF S+. Jungle 7.3 thưởng full-clear: Nidalee clear nhanh nhất meta.",
            "Spear + cougar. Camp gold + Smite stack = snowball mà không cần gank sớm.",
            "Pad giáo khó — rank hưởng farm, không phải pick pad.",
        ],
    ),
    Champ(
        "vi", "Vi", "jungle", "S+", 14, 28, pad=91,
        pad_note="Đã dạy gồng Q xuyên bụi, nhả dính.",
        why=[
            "WRF S+. Gồng Q = MB03. Clear ổn, gank khi muốn (không bắt buộc spam).",
            "Farm gold 7.3 → Trinity/Cleaver online sớm. R lock ADC địch.",
            "Turret plating: Vi đấm trụ sau gank.",
        ],
    ),
    Champ(
        "lillia", "Lillia", "jungle", "S", 14, 30, pad=74,
        pad_note="Q spam vòng, E hạt aim vừa. R sleep.",
        why=[
            "Full-clear stacking. Liandry + camp gold 7.3 = tốc độ stack điên.",
            "Ít gank sớm — đúng design Lillia scale.",
            "Smite burn + Liandry chồng lên epic monster.",
        ],
    ),
    Champ(
        "jarvan", "Jarvan IV", "jungle", "S", 12, 26, pad=88,
        pad_note="Đã dạy E rồi Q, hai nút. Không macro EQ.",
        why=[
            "EQ knockup. Flag chặn rút. Epic 7.3 scale level → Jarvan fight mục tiêu.",
            "Plating mọi nhà: sau gank đấm trụ D-pad →.",
            "Pad combo cứng L2 E → L1 Q.",
        ],
    ),
    Champ(
        "nunu", "Nunu", "jungle", "S", 12, 24, pad=90,
        pad_note="Đã dạy gồng W lăn, Q cắn.",
        why=["Q eat camp = farm meta. Pad đẹp."],
        skip_why="Pad/farm tốt nhưng Δpatch thấp hơn Rek'Sai/Nidalee/Lillia.",
    ),
    Champ(
        "warwick", "Warwick", "jungle", "S", 10, 22, pad=80,
        pad_note="Q giữ, R lock.",
        why=["Smite burn duel. Vẫn gank-first hơn farm-first."],
        skip_why="7.3 giảm giá trị gank spam — WW hưởng ít hơn farmer.",
    ),
    Champ(
        "leesin", "Lee Sin", "jungle", "S", 8, 16, pad=55,
        pad_note="Insec 3 nút + analog. Pad khó.",
        why=["S-tier cơ. Gank-heavy, meta farm làm giảm impact."],
        skip_why="Gank champion trong patch farm. Pad insec khó.",
    ),
]


PAGES: Dict[str, Page] = {
    "caitlyn": Page(
        ["Doran's Blade", "Berserker's Greaves", "Hexoptics C44",
         "Infinity Edge", "Rapid Firecannon", "Lord Dominik's Regards"],
        ["Long Sword", "Berserker's Greaves", "Hexoptics C44",
         "Infinity Edge", "Rapid Firecannon", "Lord Dominik's Regards"],
        "Q > W > E   (R mọi cấp)",
        "Flash + Ghost",
        ["Lethal Tempo", "Brutal", "Cut Down", "Legend: Alacrity", "Bone Plating"],
        {"L1": "Q Peacemaker", "L2": "W Trap (tap gần / đặt tay)",
         "L3": "E Net (lùi analog)", "L4": "R Ace (lock)",
         "A": "AA tướng — Headshot từ bụi"},
        "Trap / net → AA Headshot → Q full dmg. Kite analog max tầm. R khi thiếu máu.",
        ["vs heal: Mortal Reminder", "vs burst: Bloodthirster / GA", "Hexoptics trước IE"],
    ),
    "ashe": Page(
        ["Doran's Blade", "Berserker's Greaves", "Hexoptics C44",
         "Runaan's Hurricane", "Infinity Edge", "Lord Dominik's Regards"],
        ["Long Sword", "Berserker's Greaves", "Hexoptics C44",
         "Runaan's Hurricane", "Infinity Edge", "Lord Dominik's Regards"],
        "W > Q > E   (R mọi cấp)",
        "Flash + Ghost",
        ["Lethal Tempo", "Brutal", "Cut Down", "Legend: Bloodline", "Bone Plating"],
        {"L1": "W Volley (setup chậm)", "L2": "R Arrow (giữ/lái)",
         "L3": "Q Ranger's Focus (4 stack)", "L4": "E Hawkshot",
         "A": "AA kite — analog nhả nhẹ"},
        "L1 chậm → AA. 4 stack rồi L3. R từ bụi, analog lái. Đã dạy MB03.",
        ["vs heal: Mortal", "Bloodthirster ô 6", "Đừng Kraken nếu đi crit 7.3 — Hexoptics/IE"],
    ),
    "xayah": Page(
        ["Doran's Blade", "Berserker's Greaves", "Yun Tal Wildarrows",
         "Navori Quickblades", "Infinity Edge", "Lord Dominik's Regards"],
        ["Long Sword", "Berserker's Greaves", "Yun Tal Wildarrows",
         "Navori Quickblades", "Infinity Edge", "Lord Dominik's Regards"],
        "Q > W > E   (R mọi cấp)",
        "Flash + Barrier",
        ["Lethal Tempo", "Brutal", "Cut Down", "Legend: Alacrity", "Bone Plating"],
        {"L1": "Q Double Daggers", "L2": "W Plumage",
         "L3": "E Bladecaller (rút lông)", "L4": "R Featherstorm",
         "A": "AA — 3 auto sau skill = lông"},
        "L1 + 1 AA = 3 lông → L3 root. W trước khi AA. R né skill.",
        ["vs heal: Mortal", "BT ô 6", "Navori giảm CD E/W — đừng bỏ"],
    ),
    "lucian": Page(
        ["Doran's Blade", "Berserker's Greaves", "Yun Tal Wildarrows",
         "Infinity Edge", "Fiendhunter Bolts", "Lord Dominik's Regards"],
        ["Long Sword", "Berserker's Greaves", "Yun Tal Wildarrows",
         "Infinity Edge", "Fiendhunter Bolts", "Lord Dominik's Regards"],
        "Q > E > W   (R mọi cấp)",
        "Flash + Ignite",
        ["Lethal Tempo", "Brutal", "Cut Down", "Legend: Alacrity", "Bone Plating"],
        {"L1": "Q Piercing Light (xả)", "L2": "E Relentless (dash analog)",
         "L3": "W Ardent", "L4": "R The Culling (giữ hướng)",
         "A": "AA sau mỗi skill (Lightslinger)"},
        "Skill → A → skill → A. All-in: E→Q→A. R + Fiendhunter 3 crit.",
        ["Essence Reaver nếu thiếu mana", "Navori nếu muốn CD E", "BT vs poke"],
    ),
    "jinx": Page(
        ["Doran's Blade", "Berserker's Greaves", "Hexoptics C44",
         "Runaan's Hurricane", "Infinity Edge", "Lord Dominik's Regards"],
        ["Long Sword", "Berserker's Greaves", "Hexoptics C44",
         "Runaan's Hurricane", "Infinity Edge", "Lord Dominik's Regards"],
        "Q > W > E   (R mọi cấp)",
        "Flash + Ghost",
        ["Lethal Tempo", "Brutal", "Cut Down", "Legend: Alacrity", "Bone Plating"],
        {"L1": "Q Switcheroo (rocket/minigun)", "L2": "W Zap",
         "L3": "E Chompers", "L4": "R Rocket (global)",
         "A": "AA — minigun gần, rocket xa"},
        "Farm minigun. Teamfight rocket. W chậm rồi AA. E gốc chân mình khi bị nhảy.",
        ["BT ô 6", "Mortal vs heal", "Excited vượt AS cap — đừng sợ cap 3.0"],
    ),
    "hwei": Page(
        ["Doran's Ring", "Ionian Boots", "Luden's Echo",
         "Horizon Focus", "Rabadon's Deathcap", "Void Staff"],
        ["Amplifying Tome", "Ionian Boots", "Luden's Echo",
         "Horizon Focus", "Rabadon's Deathcap", "Void Staff"],
        "QQ poke / QW zone / EW CC  —  học 3 subject trước ranked",
        "Flash + Ignite",
        ["First Strike", "Manaflow Band", "Transcendence", "Scorch", "Bone Plating"],
        {"L1": "Q subject", "L2": "W subject", "L3": "E subject",
         "L4": "R", "A": "AA"},
        "Không khuyến pad. PC/tay: QQ poke, EW root, WW shield.",
        ["Liandry nếu team nhiều HP", "Zhonya vs assassin", "Pad: chọn Syndra/Ahri"],
    ),
    "syndra": Page(
        ["Doran's Ring", "Boots of Mana", "Luden's Echo",
         "Infinity Orb", "Rabadon's Deathcap", "Void Staff"],
        ["Amplifying Tome", "Boots of Mana", "Luden's Echo",
         "Infinity Orb", "Rabadon's Deathcap", "Void Staff"],
        "Q > W > E   (R mọi cấp)   Transcendent: Q rồi W rồi E",
        "Flash + Ignite",
        ["Electrocute", "Hextech Flashtraption", "Transcendence", "Nimbus Cloak", "Cut Down"],
        {"L1": "Q Dark Sphere (TRƯỚC)", "L2": "E Scatter (SAU — stun)",
         "L3": "W Force of Will", "L4": "R Unleashed (lock)",
         "A": "AA"},
        "L1 → L2 stun. W ném bóng. R khi ≥5 bóng. Đã dạy MB03.",
        ["Zhonya ô 6", "Liandry vs tank", "Bone Plating vs burst"],
    ),
    "ahri": Page(
        ["Doran's Ring", "Boots of Mana", "Malignance",
         "Lich Bane", "Rabadon's Deathcap", "Infinity Orb"],
        ["Amplifying Tome", "Boots of Mana", "Malignance",
         "Lich Bane", "Rabadon's Deathcap", "Infinity Orb"],
        "Q > W > E   (R mọi cấp)",
        "Flash + Ignite",
        ["Electrocute", "Sudden Impact", "Eyeball Collector", "Ultimate Hunter", "Bone Plating"],
        {"L1": "Q Orb (xả SAU charm)", "L2": "E Charm (TRƯỚC)",
         "L3": "W Fox-Fire", "L4": "R Spirit Rush (3 dash)",
         "A": "AA Lich Bane"},
        "L2 dính → L1 → L3 → A. R đuổi/né. Roam bot sau 5. Đã dạy MB03.",
        ["Zhonya vs assassin", "Void vs MR", "Luden nếu muốn wave hơn Malig"],
    ),
    "sylas": Page(
        ["Doran's Ring", "Mercury's Treads", "Riftmaker",
         "Zhonya's Hourglass", "Cosmic Drive", "Rabadon's Deathcap"],
        ["Amplifying Tome", "Mercury's Treads", "Riftmaker",
         "Zhonya's Hourglass", "Cosmic Drive", "Rabadon's Deathcap"],
        "W > Q > E   (R mọi cấp)   — W stun rồi Q",
        "Flash + Ignite",
        ["Conqueror", "Brutal", "Bone Plating", "Revitalize", "Transcendence"],
        {"L1": "Q Chain Lash (SAU W)", "L2": "W Kingslayer (TRƯỚC — stun/heal)",
         "L3": "E dash", "L4": "R cướp ult (lock)",
         "A": "AA"},
        "L2 → L1 → A. E vào. R cướp ult ADC/jg. Combo 2 nút.",
        ["Rocketbelt nếu cần gapclose", "Ionian nếu CD R", "Steelcaps vs AD"],
    ),
    "tf": Page(
        ["Doran's Ring", "Boots of Mana", "Luden's Echo",
         "Lich Bane", "Rapid Firecannon", "Rabadon's Deathcap"],
        ["Amplifying Tome", "Boots of Mana", "Luden's Echo",
         "Lich Bane", "Rapid Firecannon", "Rabadon's Deathcap"],
        "Q > W > E   (R mọi cấp)",
        "Flash + Ignite",
        ["First Strike", "Manaflow Band", "Transcendence", "Scorch", "Bone Plating"],
        {"L1": "Q Wildcards", "L2": "W Pick a Card (GIỮ — vàng)",
         "L3": "E stacked AA", "L4": "R Destiny (global)",
         "A": "AA Lich + RFC"},
        "Giữ L2 ra bài vàng. R xem map → gold card bot. RFC + Lich AA.",
        ["Zhonya", "Mejai nếu snowball", "Ionian nếu CD R"],
    ),
    "reksai": Page(
        ["Hunter's Machete", "Plated Steelcaps", "Warrior",
         "Youmuu's Ghostblade", "Black Cleaver", "Death's Dance"],
        ["Machete", "Plated Steelcaps", "Warrior",
         "Youmuu's Ghostblade", "Black Cleaver", "Death's Dance"],
        "Q > E > W   (R mọi cấp)   — W unburrow knockup",
        "Flash + Smite",
        ["Conqueror", "Brutal", "Bone Plating", "Legend: Alacrity", "Triumph"],
        {"L1": "Q Prey Seeker / fury Q", "L2": "W Burrow/Unburrow (gồng–nhả)",
         "L3": "E Furious Bite", "L4": "R Void Rush (lock)",
         "A": "AA"},
        "Đào L2 → Q dò. Gần địch nhả W knockup → AA → E. R execute.",
        ["Eclipse thay Youmuu vs tank", "Sterak ô 6", "Mercury vs CC"],
    ),
    "nidalee": Page(
        ["Hunter's Machete", "Ionian Boots", "Luden's Echo",
         "Liandry's Torment", "Rabadon's Deathcap", "Void Staff"],
        ["Machete", "Ionian Boots", "Luden's Echo",
         "Liandry's Torment", "Rabadon's Deathcap", "Void Staff"],
        "Human Q max / Cougar Q max   — giáo rồi cougar",
        "Flash + Smite",
        ["Electrocute", "Sudden Impact", "Eyeball Collector", "Ultimate Hunter", "Bone Plating"],
        {"L1": "Q Javelin (aim)", "L2": "W trap / pounce",
         "L3": "E heal / swipe", "L4": "R swap form",
         "A": "AA"},
        "Full-clear trước. Giáo max tầm. Cougar dump. Pad khó — Syndra-jg không có.",
        ["Horizon nếu poke", "Nashor nếu on-hit", "Pad: pick Vi/Jarvan"],
    ),
    "vi": Page(
        ["Hunter's Machete", "Plated Steelcaps", "Trinity Force",
         "Black Cleaver", "Sterak's Gage", "Death's Dance"],
        ["Machete", "Plated Steelcaps", "Trinity Force",
         "Black Cleaver", "Sterak's Gage", "Death's Dance"],
        "Q > E > W   (R mọi cấp)",
        "Flash + Smite",
        ["Conqueror", "Brutal", "Bone Plating", "Legend: Alacrity", "Triumph"],
        {"L1": "Q Vault Breaker (GIỮ–NHẢ)", "L2": "E Denting",
         "L3": "W", "L4": "R lock",
         "A": "AA"},
        "Giữ L1 xuyên bụi, analog góc, nhả. R ADC. Đã dạy MB03.",
        ["Divine Sunderer vs HP", "Mercury vs CC", "D-pad → trụ sau gank"],
    ),
    "lillia": Page(
        ["Hunter's Machete", "Ionian Boots", "Liandry's Torment",
         "Riftmaker", "Cosmic Drive", "Rabadon's Deathcap"],
        ["Machete", "Ionian Boots", "Liandry's Torment",
         "Riftmaker", "Cosmic Drive", "Rabadon's Deathcap"],
        "Q > E > W   (R mọi cấp)",
        "Flash + Smite",
        ["Conqueror", "Brutal", "Bone Plating", "Legend: Alacrity", "Transcendence"],
        {"L1": "Q Blooming Blows (xả vòng)", "L2": "E seed (aim)",
         "L3": "W Watch Out", "L4": "R sleep",
         "A": "AA"},
        "Full-clear Q spam. E seed đường. R sleep teamfight. Đừng gank cấp 2.",
        ["Zhonya", "Void vs MR", "Demonic nếu có"],
    ),
    "jarvan": Page(
        ["Hunter's Machete", "Plated Steelcaps", "Eclipse",
         "Black Cleaver", "Sterak's Gage", "Death's Dance"],
        ["Machete", "Plated Steelcaps", "Eclipse",
         "Black Cleaver", "Sterak's Gage", "Death's Dance"],
        "Q > E > W   (R mọi cấp)   — E cờ TRƯỚC, Q SAU",
        "Flash + Smite",
        ["Conqueror", "Brutal", "Bone Plating", "Legend: Alacrity", "Triumph"],
        {"L1": "Q Dragon Strike (SAU E)", "L2": "E Flag (TRƯỚC)",
         "L3": "W", "L4": "R arena",
         "A": "AA"},
        "L2 → L1 knockup. R nhốt. D-pad → trụ. Đã dạy MB03.",
        ["Sunderer vs HP", "Randuin vs crit ADC", "Mercury vs CC"],
    ),
}


def rank_role(role: str) -> List[Champ]:
    pool = [c for c in CHAMPS if c.role == role and not c.skip_why]
    pool.sort(key=lambda c: c.patch_score, reverse=True)
    return pool


def write_report(path: str) -> Dict:
    roles = [("jungle", "RỪNG"), ("mid", "MID"), ("adc", "ADC")]
    payload: Dict = {"patch": PATCH, "roles": {}}
    lines: List[str] = []
    a = lines.append
    a("=" * 78)
    a("TỐC CHIẾN 7.3 — TOP 5 RỪNG / MID / ADC HƯỞNG PATCH")
    a("Crit 200% · AS cap 3 · jungle farm · tướng mới Hwei / Sylas / Rek'Sai")
    a("Pad = ghi chú MB03 (không phải filter). Hỗ trợ xem support-73-pad-sim.")
    a("=" * 78)
    a("")
    a("CÁCH TÍNH  patch_score = kit_buff (0–40) + system_7.3 (0–40) + 12 nếu tướng mới")
    a("  kit     = Riot sửa CHÍNH tướng này")
    a("  system  = dùng crit 200% / item mới / farm jungle / 2v2 khi jg farm")
    a("")

    for role, title in roles:
        top = rank_role(role)[:5]
        payload["roles"][role] = []
        a("-" * 78)
        a(f"TOP 5 {title}")
        a("-" * 78)
        a(f"  {'#':<3}{'Tướng':<14}{'WRF':<6}{'Kit':>4}{'Sys':>5}{'New':>4}{'Score':>7}  pad")
        for i, c in enumerate(top, 1):
            a(
                f"  {i:<3}{c.name:<14}{c.wrf:<6}{c.kit:>4}{c.system:>5}"
                f"{'Y' if c.new else '-':>4}{c.patch_score:>7.0f}  {c.pad}  {c.pad_note[:42]}"
            )
            pg = PAGES[c.key]
            payload["roles"][role].append({
                "rank": i, "name": c.name, "score": c.patch_score,
                "kit": c.kit, "system": c.system, "new": c.new,
                "pad": c.pad, "why": c.why, "page": pg.page,
                "buy": pg.buy, "skill": pg.skill, "spells": pg.spells,
                "runes": pg.runes, "pad_map": pg.pad, "combo": pg.combo,
                "sit": pg.sit,
            })
        a("")
        for i, c in enumerate(top, 1):
            pg = PAGES[c.key]
            a(f"  #{i} {c.name.upper()}   WRF {c.wrf}   score {c.patch_score:.0f}   pad {c.pad}")
            for w in c.why:
                a(f"    • {w}")
            a(f"    Ô: {' › '.join(pg.page)}")
            a(f"    Max {pg.skill}")
            a(f"    Spell {pg.spells}   Runes {' · '.join(pg.runes)}")
            a(f"    Pad  L1 {pg.pad['L1']}  |  L2 {pg.pad['L2']}")
            a(f"         L3 {pg.pad['L3']}  |  L4 {pg.pad['L4']}")
            a(f"    Combo: {pg.combo}")
            a("    Swap: " + " · ".join(pg.sit[:3]))
            a("")

    a("-" * 78)
    a("KHÔNG VÀO TOP DÙ META / PAD ĐẸP")
    a("-" * 78)
    for c in CHAMPS:
        if c.skip_why:
            a(f"  {c.name:<14}({c.role:<6}) {c.skip_why}")
    a("")
    a("PAD GỢI Ý (nếu chỉ chơi MB03)")
    a("  Rừng: Vi · Jarvan · Rek'Sai     (Nidalee giáo khó)")
    a("  Mid:  Syndra · Ahri · Sylas     (Hwei 10 chiêu — bỏ)")
    a("  ADC:  Ashe · Jinx · Lucian      (Cait trap ổn; Xayah E cần tập)")
    a("=" * 78)

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return payload


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    payload = write_report(os.path.join(here, "report.txt"))
    with open(os.path.join(here, "results.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    for role in ("jungle", "mid", "adc"):
        names = [c.name for c in rank_role(role)[:5]]
        print(f"{role:7}  {', '.join(names)}")
    print("Wrote report.txt and results.json")


if __name__ == "__main__":
    main()
