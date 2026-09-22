# Wild Rift 7.3 marksman kit notes

Stored so later build sims do not need to re-fetch patch notes.

System:
- Crit damage 175% → **200%**. Infinity Edge then takes crit damage to **230%**.
- Attack speed cap 2.5 → **3.0**.
- Attack speed ratios are per champion (see `champions.json`).
- Lifesteal replaces omnivamp / physical vamp on BT, BotRK, Scimitar, Vampiric Scepter, Gunmetal Greaves.
- Lethal Tempo rewritten: 6.4% AS per stack ranged (max 6). At max stacks, a bolt that scales with **built** attack speed.

New items: Hexoptics C44, Yun Tal Wildarrows, Stormrazor, Rapid Firecannon, Fiendhunter Bolts, Immortal Shieldbow, Statikk Shiv (on-hit energized). Magnetic Blaster removed.

Champion-specific (7.3 live):

- **Varus** — base AD 54 → **58**. Kit otherwise unchanged from 7.2. W on-hit 15/25/35/45 + 35% AP. Blight 3/3.5/4/4.5% max HP per stack (+1.2% per 100 AP).
- **Caitlyn** — rebuilt around crit. Headshot and Ace in the Hole scale with crit chance **and** crit damage. AS ratio 0.625, bonus AS 0.28, growth 0.04. Base AD 60.
- **Jinx** — AD/level 4.5 → 4. Rocket ratios trimmed. Still AS-scaling crit.
- **Lucian** — The Culling bullet count = 20 + 20 × crit chance, plus extra from crit damage above 200%. Lightslinger 40/50/60%.
- **Miss Fortune** — Love Tap no longer fully doubles with crit. Double Up second hit = 60% × current crit damage.
- **Vayne** — base AD 54 → 60. Tumble 50–80% AD. Silver Bolts 6/7/8/9% max HP true. R AD 30/40/50.
- **Ashe** — AD/level 2.65 → 4, base AD 60. Frost Shot bonus = crit chance + extra from crit damage above 200%. Volley CD 15/12/9/6.
- **Xayah** — feathers scale with crit chance and crit damage. Deadly Plumage AS 40–55%.
- **Tristana** — jump/charge/ult pick up bonus AD. Explosive Charge active scales with crit.
- **Sivir** — boomerang rewritten around bonus AD and crit. Ricochet 37.5–45% AD.
- **Kai'Sa** — base AD 62 → 59. Plasma now scales with current stacks. Evolutions still on-hit/AS.
- **Twitch** — AS no longer from max venom; Ambush grants 35–50% AS for 6s after stealth. Contaminate needs a poisoned target in 1200.
- **Draven** — axes 80–110% AD. Ult executes if HP < Adoration stacks. Gold from stacks reduced.
- **Jhin** — crits deal **80%** of normal crit damage. Fourth shot turret amp 150% / 172.5% with IE.
- **Senna** — crits deal **90%** of normal crit damage. Mist crit 15% → 10% per 20.
- **Yasuo / Yone** — crits 90% of normal. Excess crit → AD 0.6 → 0.5.
- **Zeri** — Q is AD-heavy again; crit damage on laser/lightning = 150% + 0.5 × (crit damage − 2).
- **Samira** — style MS per grade now scales with level. Inferno Trigger can lifesteal at 66.7%. Flair cannot.
- **Ezreal** — Q CD longer, base damage down, but Q refunds **all** abilities including itself.
- **Yunara** — crit bonus damage 10% → 8% per 100 AP.

Full numeric AS / durability: `champions.json`. Full Varus kit: `varus.json`. Items: `items.json`.
