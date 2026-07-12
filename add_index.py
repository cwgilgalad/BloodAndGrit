#!/usr/bin/env python3
"""One-shot: bake the Index into player-src.html (Player's Book v2.9).

Adds anchor ids across the book, appends the Index section after The Ledger,
adds the Index TOC line and .ix CSS, and bumps v2.8 -> v2.9 in player-src.html
plus the cascade match strings in build_keeper.py / build_bestiary.py.

DO NOT RE-RUN after it has been applied (like add_detail.py).
"""
import re, sys

P = "player-src.html"
html = open(P, encoding="utf-8").read()

if 'id="index"' in html:
    sys.exit("already applied — refusing to re-run")

# ---------- helpers ----------
def tag_id(h, prefix, ident):
    n = h.count(prefix)
    assert n == 1, f"{ident}: {n} matches for {prefix!r}"
    gt = prefix.index(">")
    return h.replace(prefix, prefix[:gt] + f' id="{ident}"' + prefix[gt:], 1)

# ---------- heading anchors ----------
HEADS = [
    ("<h2>The Three Truths</h2>", "ix-truths"),
    ("<h3>When This Is — the Year of 1885</h3>", "ix-1885"),
    ("<h3>On Tone — for Everyone at the Table</h3>", "ix-tone"),
    ("<h4>A Word on the Rules</h4>", "ix-pf2e"),
    ("<h2>The Core Roll</h2>", "ix-core-roll"),
    ("<h2>Difficulty at a Glance</h2>", "ix-difficulty"),
    ("<h2>Degrees of Success</h2>", "ix-degrees"),
    ("<h2>Checks, Saves, and Opposed Rolls</h2>", "ix-checks"),
    ("<h3>Taking Your Time</h3>", "ix-take-time"),
    ("<h2>Grit</h2>", "ix-grit"),
    ("<h2>The Measures of Time</h2>", "ix-time"),
    ("<h2>Step 2 — The Six Abilities</h2>", "ix-abilities"),
    ("<h3>Generating the Scores</h3>", "ix-scores"),
    ("<h4>A Word on Modifiers</h4>", "ix-modifiers"),
    ("<h2>Step 6 — Reckoning Your Numbers</h2>", "ix-reckoning"),
    ("<h2>Step 8 — The Four Questions</h2>", "ix-questions"),
    ("<h2>Step 9 — The Compass</h2>", "ix-compass"),
    ("<h3>Holy, Unholy, and the Unsanctified</h3>", "ix-holy"),
    ("<h3>The Drummer</h3>", "ix-o-drummer"),
    ("<h3>The Fallen Gentry</h3>", "ix-o-gentry"),
    ("<h3>The Freed</h3>", "ix-o-freed"),
    ("<h3>The Gambler</h3>", "ix-o-gambler"),
    ("<h3>The Homesteader</h3>", "ix-o-homesteader"),
    ("<h3>The Laborer</h3>", "ix-o-laborer"),
    ("<h3>The Outlaw</h3>", "ix-o-outlaw"),
    ("<h3>The Scout</h3>", "ix-o-scout"),
    ("<h3>The Veteran</h3>", "ix-o-veteran"),
    ("<h3>Came Back Wrong</h3>", "ix-o-wrong"),
    ("<h2>Bounty Hunter</h2>", "ix-c-bounty"),
    ("<h2>Drifter</h2>", "ix-c-drifter"),
    ("<h2>Gambler</h2>", "ix-c-gambler"),
    ("<h2>Gunhand</h2>", "ix-c-gunhand"),
    ("<h2>Marshal</h2>", "ix-c-marshal"),
    ("<h2>Mountain Man</h2>", "ix-c-mountain"),
    ("<h2>Prospector</h2>", "ix-c-prospector"),
    ("<h2>Sawbones</h2>", "ix-c-sawbones"),
    ("<h2>Medicine Man</h2>", "ix-c-medicine"),
    ("<h2>Padre</h2>", "ix-c-padre"),
    ("<h2>Preacher</h2>", "ix-c-preacher"),
    ("<h2>Shaman</h2>", "ix-c-shaman"),
    ("<h2>Witch Hunter</h2>", "ix-c-witchhunter"),
    ("<h2>Dark Cultist</h2>", "ix-c-cultist"),
    ("<h2>False Prophet</h2>", "ix-c-prophet"),
    ("<h2>Hexer</h2>", "ix-c-hexer"),
    ("<h2>Witch</h2>", "ix-c-witch"),
    ("<h4>Alienist</h4>", "ix-alienist"),
    ("<h4>Familiar</h4>", "ix-familiar"),
    ("<h2>The Patrons of the Old Dark</h2>", "ix-patrons"),
    ("<h4>Three Debts: Hexer, Witch, False Prophet</h4>", "ix-three-debts"),
    ("<h2>Using a Skill</h2>", "ix-using-skills"),
    ("<h4>At the Green Table &mdash; Each Trade Its Own Tell</h4>", "ix-green-table"),
    ("<h2>Edges of the Gun</h2>", "ix-eg"),
    ("<h2>Edges of the Body</h2>", "ix-ebd"),
    ("<h2>Edges of Mind and Nerve</h2>", "ix-emn"),
    ("<h2>Edges of the Frontier</h2>", "ix-efr"),
    ("<h2>Edges of the Old Dark</h2>", "ix-eod"),
    ("<h4>Of Rarity — Common, Uncommon &amp; Rare</h4>", "ix-rarity"),
    ("<h2>Firearms</h2>", "ix-firearms"),
    ("<h3>Weapon Traits</h3>", "ix-weapon-traits"),
    ("<h2>Blades &amp; Bludgeons</h2>", "ix-blades"),
    ("<h2>On Armor</h2>", "ix-armor"),
    ("<h2>Provisions, Gear &amp; Sundries</h2>", "ix-gear"),
    ("<h2>Tonics &amp; the Sawbones' Trade</h2>", "ix-tonics"),
    ("<h3>Special Ammunition</h3>", "ix-special-ammo"),
    ("<h2>Mounts &amp; Tack</h2>", "ix-mounts"),
    ("<h4>A Horse's Nerve</h4>", "ix-horse-nerve"),
    ("<h2>More Arms &amp; Powder</h2>", "ix-more-arms"),
    ("<h2>Ammunition &amp; Specialty Rounds</h2>", "ix-spec-rounds"),
    ("<h2>Weapon Furniture</h2>", "ix-furniture"),
    ("<h2>Clothing &amp; the Cold</h2>", "ix-clothing"),
    ("<h2>Tools of Many Trades</h2>", "ix-tools"),
    ("<h2>The Camp &amp; the Trail</h2>", "ix-camp"),
    ("<h2>Vittles &amp; Comforts</h2>", "ix-vittles"),
    ("<h2>Provisions Against the Dark</h2>", "ix-prov-dark"),
    ("<h2>Services &amp; Lodging</h2>", "ix-services"),
    ("<h2>Livestock &amp; Conveyances</h2>", "ix-livestock"),
    ("<h2>Uncommon Goods</h2>", "ix-uncommon"),
    ("<h2>Rare — Charms &amp; Lesser Relics</h2>", "ix-charms"),
    ("<h2>Rare — Artifacts &amp; Relics of Power</h2>", "ix-artifacts"),
    ("<h2>Rounds, Turns, and the Three Beats</h2>", "ix-beats"),
    ("<h2>The Strike, and the Multiple Attack Penalty</h2>", "ix-map"),
    ("<h2>The Four Degrees of Success</h2>", "ix-four-degrees"),
    ("<h2>Circumstance</h2>", "ix-circumstance"),
    ("<h2>Aiming and Bracing</h2>", "ix-aiming"),
    ("<h2>Reloading</h2>", "ix-reloading"),
    ("<h2>Wounds, Bleeding, and Death</h2>", "ix-wounds"),
    ("<h2>Fighting from the Saddle</h2>", "ix-saddle"),
    ("<h4>The Charge</h4>", "ix-charge"),
    ("<h2>Grievous Wounds</h2>", "ix-grievous"),
    ("<h2>Two Kinds of Fighting</h2>", "ix-nonlethal"),
    ("<h2>The Nerve Pool</h2>", "ix-nerve-pool"),
    ("<h2>Breaking</h2>", "ix-breaking"),
    ("<h2>The Mark</h2>", "ix-mark"),
    ("<h2>Recovering Nerve</h2>", "ix-recover-nerve"),
    ("<h3>A Second Word on Safety</h3>", "ix-safety"),
    ("<h2>The Taint of the Land</h2>", "ix-taint"),
    ("<h3>Shedding the Taint</h3>", "ix-shed-taint"),
    ("<h3>The Stilling</h3>", "ix-s-stilling"),
    ("<h3>Witch-Sight</h3>", "ix-s-witchsight"),
    ("<h3>The Crimson Word</h3>", "ix-s-crimson"),
    ("<h3>Hollow Step</h3>", "ix-s-hollow"),
    ("<h3>The Tally</h3>", "ix-s-tally"),
    ("<h3>Salt &amp; Iron</h3>", "ix-s-salt"),
    ("<h3>Borrowed Breath</h3>", "ix-s-breath"),
    ("<h3>The Calling</h3>", "ix-s-calling"),
    ("<h2>The Old Rites</h2>", "ix-old-rites"),
    ("<h3>Who May Work the Dark</h3>", "ix-who-works"),
    ("<h3>The Unmarked at the Threshold</h3>", "ix-unmarked"),
    ("<h2>What a Level Brings</h2>", "ix-level-brings"),
    ("<h2>Milestones over Tallies</h2>", "ix-milestones"),
]

# ---------- inline anchors (paragraphs, list items, table rows) ----------
INLINE = [
    ('<p class="note"><strong>Free of charge.</strong>', "ix-reactions"),
    ('<p class="note"><strong>Off-Guard</strong>', "ix-offguard"),
    ("<p><strong>Damage Reduction (DR)</strong>", "ix-dr"),
    ("<p><strong>Lasting Afflictions</strong>", "ix-afflictions"),
    ('<p class="note">Where a Sign forces a save', "ix-sign-dc"),
    ("<tr><td>Frightened</td>", "ix-frightened"),
    ("<li><strong>Demoralize.</strong>", "ix-demoralize"),
    ("<li><strong>Helping (Aid).</strong>", "ix-aid"),
    ("<li><strong>Untrained.</strong>", "ix-untrained"),
    ("<li><strong>Calling the Rain.</strong>", "ix-r-rain"),
    ("<li><strong>Laying the Dead.</strong>", "ix-r-laying"),
    ("<li><strong>Reading the Bones.</strong>", "ix-r-bones"),
    ("<li><strong>The Sain.</strong>", "ix-r-sain"),
    ("<li><strong>Warding Salt.</strong>", "ix-r-salt"),
]

# named general Edges: (li prefix, id, index display)
EDGES = [
    ("Cylinder &amp; Sky", "ix-e-cylinder", "Cylinder &amp; Sky (Edge)"),
    ("Dead Eye", "ix-e-dead-eye", "Dead Eye (Edge)"),
    ("Fan the Hammer", "ix-e-fan", "Fan the Hammer (Edge)"),
    ("Gunfighter's Calm", "ix-e-calm", "Gunfighter's Calm (Edge)"),
    ("Practiced Reload", "ix-e-reload", "Practiced Reload (Edge)"),
    ("Quick Draw", "ix-e-quick-draw", "Quick Draw (Edge)"),
    ("Steady Shot", "ix-e-steady", "Steady Shot (Edge)"),
    ("Throw the Stick", "ix-e-throw", "Throw the Stick (Edge)"),
    ("Two-Gun", "ix-e-two-gun", "Two-Gun (Edge)"),
    ("Fleet", "ix-e-fleet", "Fleet (Edge)"),
    ("Hard to Kill", "ix-e-hard-to-kill", "Hard to Kill (Edge)"),
    ("Iron Gut", "ix-e-iron-gut", "Iron Gut (Edge)"),
    ("Saddle-Born", "ix-e-saddle-born", "Saddle-Born (Edge)"),
    ("Tough as Rawhide", "ix-e-rawhide", "Tough as Rawhide (Edge)"),
    ("Born Lucky", "ix-e-born-lucky", "Born Lucky (Edge)"),
    ("Cold Read", "ix-e-cold-read", "Cold Read (Edge)"),
    ("Gallows Humor", "ix-e-gallows", "Gallows Humor (Edge)"),
    ("Iron Will", "ix-e-iron-will", "Iron Will (Edge)"),
    ("Stone Nerve", "ix-e-stone", "Stone Nerve (Edge)"),
    ("Unshakable", "ix-e-unshakable", "Unshakable (Edge)"),
    ("Dead Shot Provider", "ix-e-provider", "Dead Shot Provider (Edge)"),
    ("Frontier Medicine", "ix-e-frontier-med", "Frontier Medicine (Edge)"),
    ("Pathfinder", "ix-e-pathfinder", "Pathfinder (Edge)"),
    ("Powder Sense", "ix-e-powder", "Powder Sense (Edge)"),
    ("Tracker", "ix-e-tracker", "Tracker (Edge)"),
    ("Hedge Magic", "ix-e-hedge", "Hedge Magic (Edge)"),
    ("Salt-Wise", "ix-e-salt-wise", "Salt-Wise (Edge)"),
    ("Touched", "ix-e-touched", "Touched (Edge)"),
    ("Warded", "ix-e-warded", "Warded (Edge)"),
]

# Rare items: (h4 prefix, id, index display)
RELICS = [
    ("<h4>Hangman's Coin <span", "ix-rel-coin", "Hangman's Coin (relic)"),
    ("<h4>Dead Man's Compass <span", "ix-rel-compass", "Dead Man's Compass (relic)"),
    ("<h4>Witch-Bottle <span", "ix-rel-bottle", "Witch-Bottle (relic)"),
    ("<h4>Saint's Finger-Bone <span", "ix-rel-bone", "Saint's Finger-Bone (relic)"),
    ("<h4>Gambler's Marked Deck <span", "ix-rel-deck", "Gambler's Marked Deck (relic)"),
    ("<h4>Ghost-Iron Spurs <span", "ix-rel-spurs", "Ghost-Iron Spurs (relic)"),
    ("<h4>Salt of the Forty Martyrs <span", "ix-rel-salt", "Salt of the Forty Martyrs (relic)"),
    ("<h4>The Peacemaker's Last Round <span", "ix-rel-round", "Peacemaker's Last Round, the (artifact)"),
    ("<h4>Vial from the Weeping Spring <span", "ix-rel-vial", "Vial from the Weeping Spring (artifact)"),
    ("<h4>Saint Dymphna's Bell <span", "ix-rel-bell", "Saint Dymphna's Bell (artifact)"),
    ("<h4>The Cartographer's Eye <span", "ix-rel-cartographer", "Cartographer's Eye, the (artifact)"),
    ("<h4>The Hanged Man's Rope <span", "ix-rel-rope", "Hanged Man's Rope, the (artifact)"),
    ("<h4>The Conquistador's Cuirass <span", "ix-rel-cuirass", "Conquistador's Cuirass, the (artifact)"),
    ("<h4>The Iron Star <span", "ix-rel-star", "Iron Star, the (artifact)"),
]

for pre, ident in HEADS + INLINE:
    html = tag_id(html, pre, ident)
for name, ident, _ in EDGES:
    html = tag_id(html, f"<li><strong>{name}.</strong>", ident)
for pre, ident, _ in RELICS:
    html = tag_id(html, pre, ident)

# ---------- the index entries ----------
E = [
    ("Abilities, the six", "ix-abilities"),
    ("Ability boosts", "ix-level-brings"),
    ("Advancement", "advancement"),
    ("Afflictions, lasting", "ix-afflictions"),
    ("Aid (Helping)", "ix-aid"),
    ("Aiming &amp; bracing", "ix-aiming"),
    ("Alienist (Sawbones)", "ix-alienist"),
    ("Ammunition, special — silver &amp; blessed", "ix-special-ammo"),
    ("Ammunition &amp; specialty rounds", "ix-spec-rounds"),
    ("Armor", "ix-armor"),
    ("Artifacts &amp; relics of power", "ix-artifacts"),
    ("Backlash", "signs"),
    ("Beats, the three", "ix-beats"),
    ("Blades &amp; bludgeons", "ix-blades"),
    ("Bleeding", "ix-wounds"),
    ("Blood (hit points)", "ix-wounds"),
    ("Borrowed Breath (Sign)", "ix-s-breath"),
    ("Bounty Hunter (Calling)", "ix-c-bounty"),
    ("Breaking (0 Nerve)", "ix-breaking"),
    ("Callings, worldly", "callings"),
    ("Callings of Faith", "faith"),
    ("Callings of the Old Dark", "hexer"),
    ("Calling, the (Sign)", "ix-s-calling"),
    ("Calling the Rain (Rite)", "ix-r-rain"),
    ("Came Back Wrong (Origin)", "ix-o-wrong"),
    ("Camp &amp; the trail, the", "ix-camp"),
    ("Character creation", "character"),
    ("Charge, the (mounted)", "ix-charge"),
    ("Charms &amp; lesser relics", "ix-charms"),
    ("Checks, saves &amp; opposed rolls", "ix-checks"),
    ("Clothing &amp; the cold", "ix-clothing"),
    ("Compass, the (alignment)", "ix-compass"),
    ("Conditions, table of", "conditions"),
    ("Core roll, the", "ix-core-roll"),
    ("Cover &amp; circumstance", "ix-circumstance"),
    ("Crimson Word, the (Sign)", "ix-s-crimson"),
    ("Critical success &amp; failure", "ix-degrees"),
    ("Damage Reduction &amp; resistance", "ix-dr"),
    ("Dark Cultist (Calling)", "ix-c-cultist"),
    ("Death &amp; dying", "ix-wounds"),
    ("Debts, the three (Old Dark)", "ix-three-debts"),
    ("Defense", "ix-reckoning"),
    ("Degrees of success", "ix-degrees"),
    ("Demoralize", "ix-demoralize"),
    ("Difficulty Classes", "ix-difficulty"),
    ("Dive for Cover (reaction)", "ix-reactions"),
    ("Dread Checks", "ix-nerve-pool"),
    ("Drifter (Calling)", "ix-c-drifter"),
    ("Drummer, the (Origin)", "ix-o-drummer"),
    ("Edges", "edges"),
    ("Edges of the Callings", "calling-edges"),
    ("Example of play", "play"),
    ("Experience &amp; levels", "advancement"),
    ("Fallen Gentry, the (Origin)", "ix-o-gentry"),
    ("False Prophet (Calling)", "ix-c-prophet"),
    ("Familiar (Witch)", "ix-familiar"),
    ("Fatal die", "ix-weapon-traits"),
    ("Firearms", "ix-firearms"),
    ("First Peoples, the", "firstpeoples"),
    ("Four Degrees, in a fight", "ix-four-degrees"),
    ("Four Questions, the", "ix-questions"),
    ("Freed, the (Origin)", "ix-o-freed"),
    ("Frightened", "ix-frightened"),
    ("Gambler (Calling)", "ix-c-gambler"),
    ("Gambler, the (Origin)", "ix-o-gambler"),
    ("Gambling at the green table", "ix-green-table"),
    ("Goods &amp; provisions", "goods"),
    ("Grievous wounds", "ix-grievous"),
    ("Grit", "ix-grit"),
    ("Gunhand (Calling)", "ix-c-gunhand"),
    ("Healing &amp; tonics", "ix-tonics"),
    ("Hexer (Calling)", "ix-c-hexer"),
    ("Hollow Step (Sign)", "ix-s-hollow"),
    ("Holy, unholy &amp; unsanctified", "ix-holy"),
    ("Homesteader, the (Origin)", "ix-o-homesteader"),
    ("Horse's Nerve, a", "ix-horse-nerve"),
    ("Initiative", "ix-beats"),
    ("Iron Code, the", "conflict"),
    ("Kickback weapons", "ix-aiming"),
    ("Laborer, the (Origin)", "ix-o-laborer"),
    ("Lasting Injuries", "ix-grievous"),
    ("Laying the Dead (Rite)", "ix-r-laying"),
    ("Ledger, the (character sheet)", "ledger"),
    ("Levels, what they bring", "ix-level-brings"),
    ("Livestock &amp; conveyances", "ix-livestock"),
    ("Lost (Mark 6)", "ix-mark"),
    ("Mark, the", "ix-mark"),
    ("Marshal (Calling)", "ix-c-marshal"),
    ("Measures of time, the", "ix-time"),
    ("Medicine Man (Calling)", "ix-c-medicine"),
    ("Mexican Frontier, the", "mexicanpeoples"),
    ("Milestones", "ix-milestones"),
    ("Misfire", "ix-weapon-traits"),
    ("Modifiers", "ix-modifiers"),
    ("More arms &amp; powder", "ix-more-arms"),
    ("Mounts &amp; tack", "ix-mounts"),
    ("Mounted combat", "ix-saddle"),
    ("Mountain Man (Calling)", "ix-c-mountain"),
    ("Multiple Attack Penalty", "ix-map"),
    ("Nerve", "ix-nerve-pool"),
    ("Nerve, recovering", "ix-recover-nerve"),
    ("Nonlethal blows", "ix-nonlethal"),
    ("Off-Guard", "ix-offguard"),
    ("Old Rites, the", "ix-old-rites"),
    ("Opposed rolls", "ix-checks"),
    ("Origins", "origins"),
    ("Outlaw, the (Origin)", "ix-o-outlaw"),
    ("Padre (Calling)", "ix-c-padre"),
    ("Pathfinder Second Edition", "ix-pf2e"),
    ("Patrons of the Old Dark, the", "ix-patrons"),
    ("Posse, ready-made (pregenerated characters)", "posse"),
    ("Preacher (Calling)", "ix-c-preacher"),
    ("Proficiency", "ix-core-roll"),
    ("Prospector (Calling)", "ix-c-prospector"),
    ("Provisions against the dark", "ix-prov-dark"),
    ("Provisions, gear &amp; sundries", "ix-gear"),
    ("Quick Reference", "quickref"),
    ("Rarity — Common, Uncommon &amp; Rare", "ix-rarity"),
    ("Reactions", "ix-reactions"),
    ("Reading the Bones (Rite)", "ix-r-bones"),
    ("Reloading", "ix-reloading"),
    ("Rounds &amp; turns", "ix-beats"),
    ("Saddle, fighting from the", "ix-saddle"),
    ("Safety at the table", "ix-safety"),
    ("Sain, the (Rite)", "ix-r-sain"),
    ("Salt &amp; Iron (Sign)", "ix-s-salt"),
    ("Sanctification", "ix-holy"),
    ("Saves", "ix-checks"),
    ("Sawbones (Calling)", "ix-c-sawbones"),
    ("Scores, generating the", "ix-scores"),
    ("Scout, the (Origin)", "ix-o-scout"),
    ("Services &amp; lodging", "ix-services"),
    ("Shaman (Calling)", "ix-c-shaman"),
    ("Sign DC", "ix-sign-dc"),
    ("Signs", "signs"),
    ("Signs, who may work", "ix-who-works"),
    ("Skills", "skills"),
    ("Skills, using", "ix-using-skills"),
    ("Speed", "ix-reckoning"),
    ("Stilling, the (Sign)", "ix-s-stilling"),
    ("Taint of the Land, the", "ix-taint"),
    ("Taint, shedding the", "ix-shed-taint"),
    ("Take 10 / Take 20", "ix-take-time"),
    ("Tally, the (Sign)", "ix-s-tally"),
    ("Three Truths, the", "ix-truths"),
    ("Tone, on", "ix-tone"),
    ("Tonics &amp; the Sawbones' trade", "ix-tonics"),
    ("Tools of many trades", "ix-tools"),
    ("Uncommon goods", "ix-uncommon"),
    ("Unmarked at the threshold, the", "ix-unmarked"),
    ("Untrained skills", "ix-untrained"),
    ("Veteran, the (Origin)", "ix-o-veteran"),
    ("Vittles &amp; comforts", "ix-vittles"),
    ("Warding Salt (Rite)", "ix-r-salt"),
    ("Weapon furniture", "ix-furniture"),
    ("Weapon traits", "ix-weapon-traits"),
    ("Witch (Calling)", "ix-c-witch"),
    ("Witch Hunter (Calling)", "ix-c-witchhunter"),
    ("Witch-Sight (Sign)", "ix-s-witchsight"),
    ("Wounds, bleeding &amp; death", "ix-wounds"),
    ("Year of 1885, the", "ix-1885"),
]
E += [(disp, ident) for _, ident, disp in EDGES]
E += [(disp, ident) for _, ident, disp in RELICS]

def key(s):
    return s.replace("&amp;", "and").replace("—", " ").lower()

E.sort(key=lambda t: key(t[0]))

lines, letter = [], None
for disp, anchor in E:
    l = key(disp)[0].upper()
    if l != letter:
        letter = l
        lines.append(f'    <li class="ix-hd">{l}</li>')
    lines.append(f'    <li><a href="#{anchor}">{disp}</a><span class="pg">0</span></li>')
entries = "\n".join(lines)

SECTION = f'''

<!-- ===================== INDEX ===================== -->
<section class="page" id="index">
  <div class="runhead"><span class="l">Blood &amp; Grit</span><span>Index</span></div>
  <h1 class="chapter">Index</h1>
  <p class="chapter-sub">Every rule in its place, and the page where it waits.</p>
  <div class="divider"></div>
  <ul class="ix">
{entries}
  </ul>
  <div class="pageno">56</div>
</section>'''

LEDGER_END = '<div class="pageno">55</div>\n</section>'
assert html.count(LEDGER_END) == 1, "ledger close not unique"
html = html.replace(LEDGER_END, LEDGER_END + SECTION, 1)

# ---------- TOC line ----------
TOC_LEDGER = '<li><a href="#ledger">The Ledger</a><span class="pg">162</span></li>'
assert html.count(TOC_LEDGER) == 1
html = html.replace(
    TOC_LEDGER,
    TOC_LEDGER + '\n    <li><a href="#index">Index</a><span class="pg">164</span></li>', 1)

# ---------- CSS ----------
TOC_CSS = ".toc li .pg{color:var(--ink-soft); font-weight:700;}"
assert html.count(TOC_CSS) == 1
IX_CSS = """

  /* index */
  .ix{list-style:none; padding:0; margin:.1em 0; font-size:13px; columns:2; column-gap:30px;}
  .ix li{display:flex; align-items:baseline; gap:8px; padding:1px 0 2px; border-bottom:1px dotted var(--gold-d); break-inside:avoid;}
  .ix li a{flex:1; border:none; color:var(--ink); font-weight:600;}
  .ix li .pg{color:var(--ink-soft); font-weight:700;}
  .ix li.ix-hd{display:block; border-bottom:none; font-family:var(--display); font-weight:700; font-size:16px; color:var(--blood-d); margin-top:.55em; break-after:avoid;}"""
html = html.replace(TOC_CSS, TOC_CSS + IX_CSS, 1)

# ---------- validation ----------
new_ids = re.findall(r'id="(ix-[\w-]+|index)"', html)
assert len(new_ids) == len(set(new_ids)), "duplicate ids"
for m in re.finditer(r'href="#([\w-]+)"', html):
    assert f'id="{m.group(1)}"' in html, f"dangling anchor #{m.group(1)}"

# ---------- version bump + cascade ----------
def bump(path, expect):
    s = open(path, encoding="utf-8").read()
    n = s.count("v2.8") + s.count("Version 2.8")
    assert n == expect, f"{path}: expected {expect} version strings, found {n}"
    s = s.replace("v2.8", "v2.9").replace("Version 2.8", "Version 2.9")
    open(path, "w", encoding="utf-8", newline="").write(s)

open(P, "w", encoding="utf-8", newline="").write(html)
bump(P, 4)
bump("build_keeper.py", 4)
bump("build_bestiary.py", 4)

print(f"applied: {len(E)} index entries, {len(new_ids)} new ids, v2.8 -> v2.9 in all three files")
