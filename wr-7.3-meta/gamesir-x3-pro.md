# GameSir X3 Pro — which 7.3 champs to play

Wild Rift has **no native gamepad**. X3 Pro on **Android** is G-Touch / V-Touch mapping in GameSir World. **iPhone cannot map Tốc Chiến.**

## How the pad actually plays

| Physical | Map it to |
|----------|-----------|
| Left Hall stick | Move (WR joystick = **locked / cố định**) |
| Right Hall stick | Camera **or** skill-aim wheel. Not both. |
| A/B/X/Y | Q W E R |
| LT analog | Charge / hold skills (Galio W, K'Sante W, Rammus Q) |
| RT | Attack |
| LB / RB | Flash + 2nd summoner |
| L4 / R4 | Item 1–2 |
| D-pad as **4 normal buttons** | ← minion lock · → tower lock · ↓ recall · ↑ scoreboard |

Do **not** bind D-pad to the move stick. Details: GameSir World → Click Mode. Cloned Mode = one physical tap, two HUD spots (not a champ picker).

WR setting that matters: locked joystick + mapping delay as low as it goes (~50 ms). Otherwise a skill press **stops the walk** — that is the X3 Pro vs Wild Rift complaint.

## Analog kite + autos (what they are)

**Auto** = basic attack / đánh thường. Not Q W E R. The champ stops, winds up, fires, then can walk again. On pad that is **RT** tapping the attack HUD.

**Analog** = the left Hall stick. 360° walk that does not snap to 8 directions. That stick is how you kite.

**Analog kite** = walk with the stick **between** autos, not instead of them.

```
stick away  →  RT (auto fires)  →  stick away  →  RT  →  stick away
   walk          stand + shoot        walk           shoot        walk
```

Two clocks inside one auto:

| Clock | Champ | You |
|-------|-------|-----|
| **Wind-up** | Stands still and shoots | Stick can stay pushed, but a **new** move command in this window **cancels** the shot. Mapping must not drop the joystick touch. |
| **Cooldown** | Cannot shoot yet | **This is the walk.** Stick away / sideways. This is kite. |

If you hold RT with **Force Attack Follow ON**, the champ **chases** when they leave range — that is the opposite of kite. Follow **OFF**. Tap RT on each cooldown. Do not hold RT unless they are planted in range.

Hall stick vs D-pad: D-pad is 4 HUD taps (minion / tower / recall / scoreboard). It is **not** movement. Analog kite dies if you bind the hat to the move joystick.

| Champ | Autos in the kite | What you add |
|-------|-------------------|--------------|
| **Kai'Sa** | Almost all the damage (Plasma). Analog **is** the champ. | Q when isolated. E to haste. Stop **only** to fire W. |
| **Ashe** | Autos + Frost. Analog is very good. | W cone between autos. R is extra. |
| **Smolder** | Autos are filler. Damage is targeted Q. | Stick between Qs. Analog is nice, not required. |

## Setup (do this in order)

Android only. Open Tốc Chiến **from GameSir World**. iPhone cannot map Wild Rift.

### 1. Wild Rift HUD first

Lobby: **Cài đặt → Điều khiển → Tùy chỉnh bố cục nút**. Save a layout named pad, separate from touch.

| Icon | Put it | Why |
|------|--------|-----|
| Attack (đánh thường) | Right side, easy for RT | This is every auto. |
| Minion lock (đánh lính) | Below attack, spaced | ← D-pad. Last-hit without stealing champion autos. |
| Tower lock (đánh trụ) | Above attack, spaced | → D-pad. |
| Recall | Far from skills | ↓ D-pad. |
| Scoreboard | Far from skills | ↑ D-pad. |
| Move joystick | Fixed corner | Must match **Locked** below. |

Do not stack minion/tower on QWER. Map after the icons are parked.

### 2. Wild Rift settings (kite)

**Cài đặt → Điều khiển:**

| Setting | Set | If wrong |
|---------|-----|----------|
| Joystick type | **Locked / Cố định** | Floating stick jumps; every RT drops the walk. |
| Force Attack Follow | **OFF** | Holding RT chases. Kite dies. |
| Portrait lock | **ON** (priority display) | RT hits champs, not a random minion. |
| Lock Target | **No Minion/Structure** in fights | Same. Last-hit with ← instead. |
| Aim Panning | **ON** | Right stick can pull camera when you aim W. |
| Semi-lock camera | **ON** | Map does not fly away while you kite. |
| Turbo | **OFF** | Turbo AA last-hits wrong and cancels wind-ups. |

### 3. GameSir World map

1. Mode **G-Touch** (Hardware Mapping). MediaTek phones: **V-Touch**. Enable **Mapping Enhancement** so stick + RT are two touches at once. Without it, RT **stops the walk** — analog kite is impossible.
2. Floating icon → **Adjust buttons / 调整键位**.
3. Left Hall stick → WR move joystick. Joystick touch duration / delay = **50 ms** (as low as the slider goes). Higher delay = late autos. Zero-but-broken = skill still cancels walk; keep 50.
4. Bind:

| Physical | HUD | Click Mode |
|----------|-----|------------|
| Left stick | Move joystick | Joystick, locked spot |
| **RT** | Attack | **Normal** tap. No Turbo. No Cloned. |
| A B X Y | Q W E R | Normal. Charge skills (Galio W, K'Sante W, Rammus Q) on **LT analog**, not a tap. |
| LB / RB | Flash + Ghost/Heal | Normal |
| L4 / R4 | Item 1–2 | Normal |
| ← ↑ ↓ → | Minion / scoreboard / recall / tower | Four **Add Button** dots. Not Add D-pad. |

5. Right stick = camera **or** skill-aim wheel. Not both at once. For Kai'Sa analog kite, leave RS idle while you stick+RT. Use RS only when you stop to fire W.
6. **Save.** Do not Cloned-Mode the attack button (one tap would hit attack + something else).

D-pad error `Property setting is not available for D-pad button`: delete the cross widget, **Add Button** four times, press one direction per dot, drag onto the four HUD icons. Default is already Normal.

### 4. Practice tool — prove kite before ranked

**Tập luyện.** Dummy, then a wave.

| Test | Pass | Fail |
|------|------|------|
| Left stick only | Smooth 360, no 8-way snap | D-pad is still bound to move |
| Stick + RT | Champ **keeps walking** while autos fire | Mapping Enhancement off, or joystick not Locked |
| Tap RT then stick **during wind-up** | Shot cancels (you should see this once) | You now know the window: wait for the projectile, *then* walk |
| Stick away, RT on each cooldown | Dummy dies while you circle | You are holding RT and walking into them |
| ← then RT | Last-hits the wave, ignores dummy | Attack button is still champion-priority; use minion lock |
| Q/E/R while stick is pushed | Walk does not stop | Delay > 50 ms or Enhancement off |
| Hold RT, dummy walks out of range | You **stop**, you do not chase | Follow is still ON |

Drill until stick+RT is one motion: **away, tap, away, tap**. That is analog kite. Then add Q (Kai'Sa isolated / Smolder lock) on the walk window, not on the wind-up.

If a skill press still stops the walk: G-Touch → V-Touch, keep Enhancement on, confirm Locked joystick, 50 ms, reopen the game from GameSir World.

## What "pad" means

**Pad** = GameSir X3 Pro in your hands. Left stick walk, RT attack, A/B/X/Y = Q W E R. Not thumbs on the Wild Rift HUD.

That is a different ADC than touch. On glass you tap a minion, drop a trap, swipe a skillshot, then thumb-kite. On pad you **lock a unit with a button**, hold a stick, press attack. Anything that needs a **pixel on the ground** (Caitlyn trap, delayed circle) gets worse. Anything that is **click the locked unit** (Smolder Q, Ashe auto) stays the same or gets better.

**"Best pad ADC"** is not "best ADC in 7.3". Caitlyn is still the patch ADC on touch (~36% pick). It means: of these five outstanding ADCs, **Smolder is the one whose job still works when you cannot tap the screen.**

## Best pad ADC — the situations (Smolder)

Smolder's job is **Q stacks**. Super Scorcher Breath is **targeted**: lock a unit, press Q. That is the whole early game. Muramana / Trinity, not Yun Tal.

| Situation | What the pad does | Smolder | Rest of the five |
|-----------|-------------------|---------|------------------|
| **Last-hit / stacks** | Analog last-hit is sloppy. Bind ← D-pad to minion lock, then Q or RT. | Q the locked cannon/caster = a stack. This is why he is first. | Ashe / Kai'Sa last-hit with RT (fine). Caitlyn last-hit is fine; her traps are not. Yunara last-hit is fine until ult swaps the skill buttons. |
| **Short trade** | Face button + stick. No ground click. | Lock champ, Q, maybe W cone. Two buttons. Walk out on Phase Rush. | Ashe W cone is OK. Kai'Sa Q is OK. Caitlyn wants a trap in the brush *while* she autos — pad cannot do both. |
| **Kite** | Left stick + RT attack-move. Hall sticks are good here. | E hop + stick. Damage is still Q, so you are not glued to auto range. | **Kai'Sa** and **Ashe** kite better on pad than on touch. They are should-play, just not first — they need more autos than Smolder needs Qs. |
| **Teamfight** | You cannot place gadgets. You can lock the nearest body and mash. | Stand back, Q the closest, execute when stacks are high. W/R are extra. | Caitlyn without traps is a long-range auto. Yunara ult is a third HUD. |
| **Vs Caitlyn (36% pick)** | You will not out-trap her on G-Touch. | Ban her. Q still hits the locked Caitlyn if she is in lane. | Do not pick Caitlyn on pad to "match" her. |

Hands in a Smolder pad lane: ← minion lock · Q or RT to farm · left stick to walk · W when the wave is shoved.

## Kai'Sa analog kite

**Analog** = the left Hall stick. 360° walk that does not snap to 8 directions. For Kai'Sa that stick **is** the champ: she deals damage while moving. Smolder presses Q. Kai'Sa walks and autos.

Hands:

| Finger | Button | Kai'Sa |
|--------|--------|--------|
| Left thumb | Hall stick | Walk. Never let go. |
| Right index | **RT** | Attack. Tap on every auto cooldown. |
| Right thumb | **A** Q | Missiles split by themselves. Isolated = all on one. No aim. |
| Right thumb | **X** E | Self haste / evolved invis. No aim. |
| Right thumb | **Y** R | Dash to Plasma. Need stacks first. |
| Right thumb | **B** W | The **one** skillshot. Stop or fire down a corridor. Do not flick W while you kite. |
| Left index | **LB** Ghost | Analog chase. Flash on RB. |
| Left thumb | ← D-pad | Minion lock for last-hits. |

If a skill press **stops the walk**, analog kite is dead. Fix it in **Setup** above: Mapping Enhancement, Locked joystick, 50 ms delay.

**The loop** (this is the analog):

1. Left stick **away or sideways** (never stand still).
2. **RT** when the auto is up — Plasma stack.
3. Stick again. RT again. That is kite.
4. **Q** when they are isolated or the wave is a clump (missiles split; you do not aim).
5. **E** to haste out, or evolved E to invis and re-enter.
6. At 5 Plasma: **R** onto them, Q dump, stick out.

Do not use the right stick as camera during this. Right stick is W-aim only when you have stopped.

| Situation | Analog | Buttons |
|-----------|--------|---------|
| **Last-hit** | Stick to the side of the wave | ← lock, RT. Q the leftover. |
| **Short trade** | Stick in, then immediately out | RT 2–3 times → Q (isolated) → E out. |
| **Kite a melee** | Circle-strafe with the stick | RT on cooldown. Q when they cannot share missiles. E if they gapclose. |
| **Vs tank (7.3 on-hit)** | Stick keeps you in Kraken/Rageblade range without planting | Same loop. BotRK 5th. You outwalk them; you do not out-aim them. |
| **All-in** | Stick onto the marked target | Plasma 5 → R → Q → RT → E invis if evolved. |
| **W poke** | **Stop the stick** | B down river / into a choke. Then go back to stick+RT. Missing W is fine; missing the kite is not. |

Kai'Sa vs Smolder on pad: analog is **nice** on Smolder (walk between Qs). Analog is **the champ** on Kai'Sa (walk during autos). Pick Smolder if you want lock-and-press. Pick Kai'Sa if the Hall stick feels good.

## Rule

**Should** = kit is lock-on, self-cast, hold-on-trigger, 2-button combo, or attack-move. Hall sticks + D-pad minion/tower lock help.

**Should not** = kit is pixel place, delayed ground circle, 10-spell palette, or hold-aim-and-fly at once. Extra paddles do not fix that.

## Top 3 pad per role

Ranked by **pad fit** inside each role's 7.3 outstanding five. Not by touch winrate. #1 is lock-and-press or hold-trigger. Analog kite is #2 on ADC, not #1.

| Role | 1st | 2nd | 3rd | Do not play |
|------|-----|-----|-----|-------------|
| **ADC** | **Smolder** — targeted Q, stack with ← minion lock | **Kai'Sa** — analog kite (stick + RT) | **Ashe** — autos + W cone | Caitlyn, Yunara |
| **Support** | **Sona** — auras, no aim | **Malphite** — Q missile, R click | **Senna** — tap-through Q, souls on ← | Zyra, Janna |
| **Jungle** | **Rammus** — hold Q on LT, E targeted | **Jarvan IV** — E then Q, R targeted | **Amumu** — two Q charges, self R | (Nocturne / Olaf are 4–5, still playable) |
| **Mid** | **Galio** — hold W on LT, E dash, R ally | **Malphite** (flex mid — same kit) | **Ambessa** (flex mid — Feint is the stick) | Syndra, Hwei, Brand, ASol |
| **Top** | **Malphite** — Q missile, R click | **Shen** — Q blade, E dash, R ally | **Ambessa** — Feint is the left stick | Cho'Gath (K'Sante is 4th: LT W, skip wall-bang) |

Mid's outstanding five only has **one** pad champ (Galio). 2nd / 3rd are flex from this same 25 so you still have three locks. Do not fill those slots with Syndra / Hwei / Brand / ASol.

**Ban on pad:** Caitlyn.

---

## Should play on X3 Pro

These are the 7.3 outstanding champs whose buttons match the pad.

### ADC — Ashe · Smolder · Kai'Sa

| Champ | Why the pad fits |
|-------|------------------|
| **Ashe** | Autos + W cone. D-pad minion lock last-hits. Hawk/R are extra, not the lane. |
| **Smolder** | Q is a **targeted** belch. Stack farm with ← minion lock. **Best pad ADC** = this lane still works on the controller, not "best ADC in 7.3". Situations above. |
| **Kai'Sa** | Analog kite **is** the champ: left stick + RT autos, Q splits, E self, R to Plasma. One skillshot (W). Loop above. |

### Support — Senna · Malphite · Sona

| Champ | Why the pad fits |
|-------|------------------|
| **Senna** | Q is a tap-through line. Souls = D-pad last-hit. W is the only real skillshot. |
| **Malphite** | Q slow missile, R is a click. Same kit top or support. |
| **Sona** | Auras and Power Chord. No aim. Best pad support in this five. |

### Jungle — all five

| Champ | Why the pad fits |
|-------|------------------|
| **Rammus** | Hold Q on **LT**. E targeted. R slam. |
| **Amumu** | Q is a line but two charges + self R. Classic pad jungler. |
| **Nocturne** | R is a click. E targeted. Q line is "good enough". |
| **Olaf** | Ghost + analog chase. Q throw-and-pick is fine, not pixel. |
| **Jarvan IV** | Flag-drag = **two buttons** (E then Q). R targeted. |

### Mid — Galio only from this five

| Champ | Why the pad fits |
|-------|------------------|
| **Galio** | Hold W on LT. E dash. R ally-target. Anti-mage roam. |

### Top — Malphite · Shen · Ambessa · K'Sante

| Champ | Why the pad fits |
|-------|------------------|
| **Malphite** | Same as support. |
| **Shen** | Q blade, E dash, R ally. No ground circle. |
| **Ambessa** | Feint **is** the left stick after a spell. Hall stick = her kit. Save W on a bumper for CC. |
| **K'Sante** | Charge W on **LT**. Q slams in front. Play All Out as a dash, not a wall-bang clip. |

**Pad first-picks from the 7.3 list:** Smolder · Sona · Rammus · Galio · Malphite · Shen · Ambessa · Jarvan · Ashe · Kai'Sa

---

## Should not play on X3 Pro

These 7.3 outstanding champs **lose the thing that makes them good** under G-Touch.

### ADC — Caitlyn · Yunara

| Champ | Why the pad fights the kit |
|-------|----------------------------|
| **Caitlyn** | The champ **is** trap placement + brush Headshot. Analog cannot drop W in a choke while you kite. Q/R still work; you are not playing Caitlyn. |
| **Yunara** | Ult swaps three skills, Unleash stacks, bead skillshot while kiting. Too many HUD states for one map. |

### Support — Zyra · Janna

| Champ | Why the pad fights the kit |
|-------|----------------------------|
| **Zyra** | Plants are ground-place. Q is a horizontal line. E is a skillshot. Skip Rylai uptime if you miss the root. |
| **Janna** | Identity is Q tornado from fog. W auto-picks 3 targets now, but the pad still cannot hide-charge Q. Play **Sona**. |

### Mid — Syndra · Hwei · Brand · Aurelion Sol

| Champ | Why the pad fights the kit |
|-------|----------------------------|
| **Syndra** | Q is a ground click. E stun needs the sphere angle. Spheres expire. Touch champ. |
| **Hwei** | **10 abilities** (3×3 + wash + R). X3 Pro does not have a palette. Cloned Mode is two HUD taps, not ten spells. |
| **Brand** | W delayed circle + Q blocked by minions. Combo is E→Q→W on touch. On pad you eat creeps. |
| **Aurelion Sol** | Hold Q breath **and** W fly **and** aim. Two sticks fight. Early-game stack farm dies. |

### Top — Cho'Gath

| Champ | Why the pad fights the kit |
|-------|----------------------------|
| **Cho'Gath** | Lane **is** delayed Q circle. Feast is a click (fine). If Q misses, you are a walking Heartsteel. |

**Do not first-pick on X3 Pro:** Hwei · Caitlyn · Zyra · Syndra · Brand · Aurelion Sol · Yunara · Cho'Gath · Janna

---

## If you still want a 7.3 meta lane on pad

| Role | Play (1 → 3) | Ban / dodge |
|------|----------------|-------------|
| ADC | **Smolder** → Kai'Sa → Ashe | Caitlyn, Yunara |
| Support | **Sona** → Malphite → Senna | Zyra, Janna |
| Jungle | **Rammus** → Jarvan → Amumu | (Nocturne / Olaf still playable) |
| Mid | **Galio** → Malphite flex → Ambessa flex | Syndra, Hwei, Brand, ASol |
| Top | **Malphite** → Shen → Ambessa | Cho'Gath |

Caitlyn is 36% pick. On pad you **ban her** or pick Malphite/Rammus into her — you do not try to out-trap her with G-Touch.

## Mapping notes that are not champ-specific

- Android + open the game **from GameSir World**. iOS = no.
- Locked WR joystick. Low stick delay. Skill press must not cancel walk.
- D-pad = 4 **normal** buttons, not one analog hat. Error `Property setting is not available for D-pad button` → delete the cross widget, Add Button four times.
- Cloned Mode is for "attack + secondary HUD", not for Hwei's brush.
