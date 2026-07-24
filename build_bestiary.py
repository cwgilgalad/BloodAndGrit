#!/usr/bin/env python3
# Build "Blood & Grit — The Bestiary" on the shared engine (the Player's Book shell).
# Reads blood-and-grit.html (run build_player.py first), writes bestiary.html.
import re

H = open("blood-and-grit.html", encoding="utf-8").read()

# ---- whitespace optimization: make .statblock splittable across pages ----
from pag_patch import patch_paginator as _patch_paginator
H = _patch_paginator(H)

# ---- stat-block CSS (same family as the Keeper's Book) ----
_css = """
  /* ---- Bestiary additions ---- */
  .statblock{ background:#efe6cf; border:1px solid var(--gold-d); border-left:4px solid var(--blood); padding:9px 13px 11px; margin:1.0em 0; }
  .statblock .sb-head{ display:flex; justify-content:space-between; align-items:baseline; gap:10px; border-bottom:1.5px solid var(--gold-d); padding-bottom:4px; margin-bottom:6px; }
  .statblock .sb-name{ font-family:var(--display); font-weight:700; color:var(--blood-d); font-size:17px; letter-spacing:.01em; }
  .statblock .sb-tier{ font-style:italic; color:var(--ink-soft); font-size:12.5px; white-space:nowrap; }
  .statblock p{ margin:.28em 0; font-size:13.8px; line-height:1.32; }
  .statblock p strong{ color:var(--shade); }
  .statblock .sb-tag{ font-variant:small-caps; letter-spacing:.05em; color:var(--blood-d); font-weight:700; font-size:12.5px; }
  .statblock .sb-cont{ font-style:italic; font-weight:400; color:var(--ink-soft); font-size:12px; letter-spacing:0; }
  .keeper-note{ background:#ece2c8; border-left:3px solid var(--gold-d); padding:8px 12px; margin:1em 0; font-size:14.5px; }
  .keeper-note .kn-tag{ font-variant:small-caps; letter-spacing:.06em; color:var(--blood-d); font-weight:700; display:block; font-size:12.5px; margin-bottom:2px; }
  /* ---- Expanded creature entries (lore + stat block + keeper note as one unit) ---- */
  .creature{ margin:1.5em 0 1.7em; }
  .creature > .cr-name{ font-family:var(--display); color:var(--blood-d); font-weight:700; font-size:21px; margin:0 0 .15em; letter-spacing:.01em; }
  .creature > .cr-kind{ font-style:italic; color:var(--ink-soft); font-size:13px; margin:0 0 .5em; }
  .creature .cr-lore{ font-size:14.5px; line-height:1.42; margin:.5em 0; }
  .creature .cr-lore:first-of-type{ text-indent:0; }
  .creature .cr-found{ font-size:13.5px; line-height:1.4; margin:.5em 0; background:#ede3ca; border-left:3px solid var(--blood); padding:6px 11px; }
  .creature .cr-found .cf-tag{ font-variant:small-caps; letter-spacing:.05em; color:var(--blood-d); font-weight:700; }
  .creature .statblock{ margin:.7em 0; }
  /* Bestiary cover — a third sibling: cold green-black ground, a verdigris keyline, a pale-green label */
  .title-page{ background:#0f130e; box-shadow:0 0 0 4px #0f130e inset, 0 0 0 5px rgba(74,112,92,.9) inset, 0 14px 40px rgba(0,0,0,.66); }
  .title-page .t-foot{ color:#85b196; }
  .title-page .t-sub{ color:#b8c1a8; }
</style>"""
if ".statblock{" not in H:
    H = H.replace("</style>", _css, 1)

# ---- cover / meta retext ----
_meta = [
 ("<!-- Blood & Grit — The Player's Book · Version 2.23 -->", "<!-- Blood & Grit — The Bestiary · Version 2.8 -->"),
 ("<title>Blood &amp; Grit — The Player's Book (Revised &amp; Expanded · v2.23)</title>", "<title>Blood &amp; Grit — The Bestiary (v2.8)</title>"),
 ('<div class="kicker">Being a Field Manual for the Living</div>', '<div class="kicker">A True Account of the Things That Walk</div>'),
 ('<div class="t-foot">The Player\'s Book</div>', '<div class="t-foot">The Bestiary</div>'),
 ('<div class="t-tiny">Revised &amp; Expanded · Compiled in the Territories · Edition of 1885 · Version 2.23</div>', '<div class="t-tiny">Compiled in the Territories · Edition of 1885 · Version 2.8</div>'),
 ('<div class="t-tiny">Most rules herein are adapted from Pathfinder Second Edition, with some unique rules &amp; systems of its own</div>', '<div class="t-tiny">A field-guide to the dead, the cursed, and the things that were never men</div>'),
 ('<p class="note" style="text-align:center; margin:0;">Blood &amp; Grit · The Player\'s Book · Version 2.23 · First Complete Edition</p>', '<p class="note" style="text-align:center; margin:0;">Blood &amp; Grit · The Bestiary · Version 2.8 · For the Keeper Alone</p>'),
]
for a,b in _meta:
    if a in H: H = H.replace(a,b,1)

# ---- replace the two Player's-Book epigraph quotes with new Bestiary ones (same voice) ----
_q_old1 = ('"We came west to be made new, and found instead that the country was older\n'
           '    than newness, older than God, and had been waiting a long while in the quiet for company."\n'
           '    <span class="src">— from the burned journal of Eliza Hart, Surveyor</span>')
_q_new1 = ('"I set out to make an honest catalogue of the country\'s animals. I have filled four ledgers since,\n'
           '    and not one of them holds an animal."\n'
           '    <span class="src">— from the field-books of N. Ashby, naturalist; last entry near Calvary Wells</span>')
_q_old2 = ('"Keep your powder dry, your salt close, and your accounts with the dark paid up.\n'
           '    The country settles every debt in the end."\n'
           '    <span class="src">— a saying common to the trail, author unknown</span>')
_q_new2 = ('"Name a thing and you have a handle on it, my mother used to say. She never met the things out here.\n'
           '    They have your name long before you ever learn theirs."\n'
           '    <span class="src">— Eulalie &lsquo;Lucky&rsquo; Devereaux</span>')
for a,b in [(_q_old1,_q_new1),(_q_old2,_q_new2)]:
    if a in H: H = H.replace(a,b,1)

def runhead(short):
    return f'<div class="runhead"><span class="l">Blood &amp; Grit</span><span>{short}</span></div>'

def quote(text, src):
    return f'<div class="quote">{text}<span class="src">— {src}</span></div>'

def statblock(name, tier, lines):
    body = "".join(f"<p>{l}</p>" for l in lines)
    return (f'<div class="statblock"><div class="sb-head"><span class="sb-name">{name}</span>'
            f'<span class="sb-tier">{tier}</span></div>{body}</div>')

def sb(name, tier, dfn, blood, speed, fort, ref, will, attacks, special, dread, down, mark=None):
    lines = [
        f"<span class='sb-tag'>Defense</span> {dfn} &nbsp; <span class='sb-tag'>Blood</span> {blood} &nbsp; <span class='sb-tag'>Speed</span> {speed}",
        f"<span class='sb-tag'>Saves</span> Fort {fort}, Ref {ref}, Will {will}",
        f"<span class='sb-tag'>Attacks</span> {attacks}",
        f"<span class='sb-tag'>Special</span> {special}",
        f"<span class='sb-tag'>Dread</span> {dread}",
    ]
    if mark: lines.append(f"<span class='sb-tag'>Mark</span> {mark}")
    lines.append(f"<span class='sb-tag'>Putting It Down</span> {down}")
    return statblock(name, tier, lines)


def creature(stat_html, lore, found, keeper, kn_tag="How to Play It", witness=None):
    """Wrap a stat block with the lore a Keeper wants after months of play.

    The whole thing is one <div class="creature"> so the build-time sorter and
    appendix generator treat it as a single unit (they read the sb-name/sb-tier
    out of the stat block inside it). Order on the page: name + kind heading,
    lore prose, an optional in-voice witness quote, a 'Found' line, the stat
    block, then the Keeper's how-to-play.

      stat_html : the sb(...) call for this creature (carries name + tier)
      lore      : str or list[str] — descriptive / background paragraphs
      found     : str — where and when it is met (the 'Found' line)
      keeper    : str — how the Keeper should run it (the keeper-note body)
      kn_tag    : the small-caps tag on the keeper note
      witness   : optional (text, source) tuple — an in-voice quote, set
                  between the lore and the Found line for flavor
    """
    nm = re.search(r'<span class="sb-name">(.*?)</span>', stat_html, re.S).group(1)
    kind = re.search(r'<span class="sb-tier">(.*?)</span>', stat_html, re.S).group(1)
    paras = [lore] if isinstance(lore, str) else list(lore)
    lore_html = "".join(f'<p class="cr-lore">{p}</p>' for p in paras)
    witness_html = (f'<div class="quote">{witness[0]}<span class="src">&mdash; {witness[1]}</span></div>'
                    if witness else "")
    found_html = (f'<p class="cr-found"><span class="cf-tag">Found</span> &mdash; {found}</p>'
                  if found else "")
    keeper_html = (f'<div class="keeper-note"><span class="kn-tag">{kn_tag}</span>{keeper}</div>'
                   if keeper else "")
    return (f'<div class="creature">'
            f'<p class="cr-name">{nm}</p>'
            f'<p class="cr-kind">{kind}</p>'
            f'{lore_html}{witness_html}{found_html}{stat_html}{keeper_html}'
            f'</div>')

# ---- replace the two carried-over Player's epigraph quotes (regex on the quote divs) ----
import re as _re
def _set_epigraph(s, mt, text, src):
    pat = _re.compile(r'<div class="quote" style="margin-top:'+mt+r';">.*?</div>', _re.DOTALL)
    new = ('<div class="quote" style="margin-top:'+mt+';">\n    '+text+
           '\n    <span class="src">\u2014 '+src+'</span>\n  </div>')
    s2, n = pat.subn(new, s, count=1)
    assert n==1, "epigraph "+mt+" not found"
    return s2
H = _set_epigraph(H, "120px",
    '"I set out to make an honest catalogue of the territory\'s animals. I have filled four ledgers\n'
    '    since, and not one of them holds an animal."',
    "from the field-books of N. Ashby, naturalist; last entry near Calvary Wells")
H = _set_epigraph(H, "90px",
    '"Name a thing and you have a handle on it, my grandmother said. She did not say the handle\n'
    '    runs both ways &mdash; that some things, once named, will know yours."',
    "Eulalie &lsquo;Lucky&rsquo; Devereaux")

CONTENTS = f"""<!-- ===================== BESTIARY CONTENTS ===================== -->
<section class="page" id="contents">
  {runhead('Contents')}
  <h1 class="chapter">Contents</h1>
  <p class="chapter-sub">A reckoning of the things that walk.</p>
  <div class="divider"></div>
  <p class="note">This is the Bestiary &mdash; the companion to the Player's Book and the Keeper's Book, and the
  ledger of everything in the country that wants you dead, changed, or worse. It is for the Keeper's eyes. Every
  entry gives the numbers to run a thing and the one hard truth a party must learn to put it down. Reskin freely;
  the country has more shapes than any one book can name.</p>
  <ul class="toc">
    <li><a href="#howto">I. How to Read the Dead</a><span class="pg">4</span></li>
    <li><a href="#dead">II. The Restless Dead</a><span class="pg">7</span></li>
    <li><a href="#beasts">III. Cursed Beasts &amp; Wild Things</a><span class="pg">23</span></li>
    <li><a href="#men">IV. Men, and the Shapes of Men</a><span class="pg">41</span></li>
    <li><a href="#spirits">V. Spirits &amp; Hauntings</a><span class="pg">59</span></li>
    <li><a href="#wild">VI. The Wild &amp; the Weather</a><span class="pg">72</span></li>
    <li><a href="#olddark">VII. The Old Dark</a><span class="pg">84</span></li>
    <li><a href="#living">VIII. Beasts of the Living World</a><span class="pg">103</span></li>
    <li><a href="#hard">IX. Hard Men &amp; Hard Country</a><span class="pg">121</span></li>
    <li><a href="#index">Appendix: The Roll, by Tier</a><span class="pg">121</span></li>
    <li><a href="#grounds">Appendix: The Grounds <span class="sub">(encounters by terrain)</span></a><span class="pg">123</span></li>
    <li><a href="#build">Appendix: Building Your Own Dead</a><span class="pg">128</span></li>
  </ul>
</section>
"""

HOWTO = f"""<!-- I -->
<section class="page" id="howto">
  {runhead('I. How to Read the Dead')}
  <h1 class="chapter">I. How to Read the Dead</h1>
  <p class="chapter-sub">The shape of an entry, and how to bend it.</p>
  <div class="divider"></div>
  {quote("Every monster is a sum and a secret. The sum you can read off the page. The secret you have to bleed for.", "from the field-books of N. Ashby")}
  <div class="narr">Approach this volume as you would any honest field-book: species, habitat, sign, and
  season. The early chapters catalogue dangers a rifle understands, and a careful outfit may ride years
  and meet nothing worse. But the reader will notice the catalogue is arranged in a particular order,
  and that the order is not alphabetical. It is the order in which a soul out in that country comes to
  meet these things &mdash; which is to say, it is a road, and the road runs downhill.</div>
  <p class="dropcap lead">Each creature here is built on the same bones as a player's character, so you can run it
  without a second system in your head. Below is what every line means; after that, the country.</p>
  <div class="box">
    <h4>Reading a Stat Block</h4>
    <ul>
      <li><strong>Tier</strong> (I&ndash;V) is the measure of danger. A creature is a fair, hard fight for a party
      whose <strong>level is twice its Tier</strong>; two Tiers above the party is a thing to flee.</li>
      <li><strong>Defense</strong> is the number to beat to hit it; <strong>Blood</strong> is what it can take.</li>
      <li><strong>Saves</strong> are Fortitude / Reflex / Will. <strong>Attacks</strong> give the bonus to hit and the
      damage on a hit; apply the Multiple Attack Penalty to extra strikes as a player would.</li>
      <li><strong>Special</strong> is the one thing that makes it more than its numbers. <strong>Dread</strong> is the
      Will-save DC on first sight and the Nerve it costs to fail (Keeper's Book, Ch. III).</li>
      <li><strong>Mark</strong>, where it appears, is what touching the thing's power costs a living soul.</li>
      <li><strong>Putting It Down</strong> is the secret &mdash; the weakness the party must learn, usually the hard way.</li>
    </ul>
  </div>
  <div class="keeper-note"><span class="kn-tag">Reskin freely</span>A name is a costume. The Pale Wolf's numbers serve
  any cursed pack; the Nightwalker's serve any blood-drinking dead; a Tier-IV horror is a Tier-IV horror whatever you
  call it. When the players have learned a thing's secret, change its face and its secret both, and let them learn
  again. Familiarity is the death of dread.</div>

  <h2>Bending the Numbers</h2>
  <p>One block serves a dozen monsters. Beyond changing a thing's <em>name</em>, you can bend its <em>numbers</em> to
  fit the night and the party in front of you. These templates stack on any entry here.</p>
  <div class="box">
    <h4>Templates</h4>
    <ul>
      <li><strong>Up a Tier / Down a Tier.</strong> The fastest dial: read the creature off the next row of the
      Threat-by-Tier table (Keeper's Book, Ch. IV) instead of its own &mdash; Defense, attack, Blood, saves, damage,
      and Dread DC all step together. Make a Tier-II haunt menace a 6th-level party, or gentle a Tier-IV horror for
      greener hands.</li>
      <li><strong>The Swarm.</strong> Run many weak things &mdash; a host of Risen, a cloud of the dead &mdash; as
      <em>one</em> threat a Tier higher: a single Defense and Blood pool, one area attack that catches all who stand
      close, no aimed shots and no called blows. It thins as it bleeds rather than dropping, and it comes through
      doors and walls and patience.</li>
      <li><strong>The Lieutenant.</strong> The named one in the pack: +2 Defense, half again the Blood, a second
      action each round, and one signature trick of its own. Every gang has a boss; every haunt, a heart.</li>
      <li><strong>The Boss &amp; its Lair.</strong> On its own ground, give a creature a <em>Lair Action</em> each
      round &mdash; the ground itself takes a turn: a cold that bites, a floor that grasps, a dark that gathers, a wall
      that weeps &mdash; and let it shrug off the first Break or rout it would suffer. A monster at home is a monster at
      its worst.</li>
      <li><strong>Fledgling / Weakened.</strong> A Tier down, its healing or its dread-regard stripped away, its
      weakness laid bare &mdash; for the night the party is <em>meant</em> to win, or the thing they catch before it
      ripens.</li>
    </ul>
  </div>
  <div class="keeper-note"><span class="kn-tag">A caution</span>Bend the numbers, not the fiction. A thing made a Tier
  tougher should look it &mdash; older, hungrier, surer &mdash; so the players read the danger before the dice do. A
  boss that hits harder for no visible reason is just a cheat with antlers.</div>
</section>
"""

# ============================================================ II. THE RESTLESS DEAD
DEAD = f"""<!-- II -->
<section class="page" id="dead">
  {runhead('II. The Restless Dead')}
  <h1 class="chapter">II. The Restless Dead</h1>
  <p class="chapter-sub">What will not stay buried in a country too thin to hold it.</p>
  <div class="divider"></div>
  {quote("The dead don't rest out here. The ground's too thin, the nights too long, and they have too much left unsaid.", "Marshal T. Coyle")}
  <p class="dropcap lead">Burial is a promise the frontier does not always keep. These are the dead that came back &mdash;
  some hungry, some grieving, some only obedient to a will that called them up.</p>
  <p class="note"> <strong>Signs of the kind:</strong> ground that will not keep a grave, stock that balks at a certain plot, fresh-turned earth where none was turned, and the dead reported home days after the burying.</p>

  {creature(
    sb("The Risen", "Tier I &middot; the shambling dead", 12, 14, "shuffling (half)", "+6", "+0", "+2",
       "grasping hands +4 (1d6+2 and grab); bite +4 (1d4+2)",
       "<strong>Does not stop.</strong> Ignores pain, fear, and being bloodied; immune to anything worked on a living mind.",
       "DC 16, 1d6 (the first time the dead get up)",
       "Break the body past use or take the head; salt and fire end it for good."),
    lore=[
      "There is nothing clever in the Risen and nothing left of whoever it used to be. The country called it up out of thin ground &mdash; a battlefield, a hanging-tree, a pauper's trench dug too shallow in a hard winter &mdash; and what climbed out is a body that has forgotten it is supposed to lie down. It does not hate you. It does not know you. It simply comes, slow and certain, with the dumb patience of running water, and it will be coming long after you have run out of reasons to stay.",
      "A single Risen is a sad and ugly thing a frightened farmhand can put down with a fence-post and nerve enough. The horror of them is arithmetic. Where one rises, a dozen rise, and a dozen become a wall of cold hands that does not tire, does not flank, and does not stop coming through the door you barred."],
    witness=("&ldquo;Shot the Pearson boy twice through the chest at his own funeral. He got up both times and kept walking. We learned to use the fire after that.&rdquo;", "deposition of a Kansas deputy, 1884"),
    found="Where the dead were buried wrong or buried angry &mdash; mass graves, massacre grounds, potter's fields, the floor of a burned church. They rise at full dark and the first night is always the worst.",
    keeper="The Risen are the party's first lesson, and the lesson is simple: the dead out here do not play by living rules. Run a lone one to teach that &mdash; let them shoot it, watch it keep walking, and feel the cold of it. Then, the next time, give them six, and a closing door, and a window that won't latch. The dread of the Risen is never one corpse; it is the math of <em>more</em>. Never let a fight against them feel winnable by damage alone &mdash; make the players solve the room, the exits, the salt, the fire. A party that learns to think their way out of a Risen swarm is a party ready for worse.")}

  {creature(
    sb("The Boneyard Host", "Tier II &middot; a graveyard, risen at once", 13, 26, "shuffling", "+8", "+2", "+4",
       "a dozen clutching hands +6 (2d6+2); drags the fallen down into the press",
       "<strong>Many as one.</strong> Run the whole graveyard as a single tide; it cannot be killed, only outlasted, scattered, or unbound.",
       "DC 16, 1d6",
       "Find and break the thing that woke them &mdash; a Gravecaller, a buried sign, a broken oath &mdash; and the host falls still."),
    lore=[
      "When every grave in a yard opens on the same night, you are not fighting the dead &mdash; you are fighting the ground itself. The Boneyard Host is the Risen multiplied past counting and bound into one slow, grinding will: a churchyard, a battlefield cemetery, a town's whole century of dead, all standing at once and all turning toward the warm and the living with a single terrible patience.",
      "It moves like a flood finds a valley. There is no front line to hold, no flank to turn &mdash; only the press, closing from every quarter, and the dreadful certainty that for every hand you break there are forty behind it. Men have emptied every gun they owned into a Host and changed nothing but the noise."],
    found="Old churchyards, the cemeteries of vanished towns, the burial trenches of a battle or an epidemic. Something always wakes them &mdash; a Gravecaller in the dirt, a desecration, a debt the town forgot it owed.",
    keeper="Do not run this as two dozen separate enemies; that way lies a four-hour slog and a bored table. Run the Host as <em>one</em> thing with one Blood pool, one area attack, and a relentless advance &mdash; a clock, not a brawl. The real fight is the question: <em>what woke them, and how do we make it stop?</em> Seed the answer before the Host ever rises &mdash; the cracked headstone, the missing reverend, the railroad cut through hallowed ground. Let the players feel the futility of fighting the tide for a round or two, then reward the one who thinks to ask <em>why</em>. The Host is a puzzle wearing a battle's face.")}

  {creature(
    sb("The Gallows-Hung", "Tier II &middot; a hanged man come down", 15, 22, "normal", "+8", "+4", "+6",
       "the noose, cast and cinched +6 (1d8+3 and grab, drags toward a high beam); strangling grip +6 (1d8+3)",
       "<strong>Cannot be hanged twice.</strong> Bullets and blades barely slow it; it means to hang you as it was hanged.",
       "DC 16, 1d6",
       "Cut it down, burn the rope, and bury the bones at a crossroads with a coin in the mouth."),
    lore=[
      "Some men are hanged for what they did. Some are hanged because the town needed a body and they were handy. The Gallows-Hung does not much care which it was &mdash; what rose with it was the rage of the rope, the long minute of strangling, the faces of the crowd that watched and did nothing. It comes down off its tree with the noose still around its neck, and it has learned exactly one trade, and means to teach it.",
      "It carries its own rope like a lariat, and it is a better hand with it dead than any living cowboy. It does not want to kill you with a gun or a knife. It wants the beam, the drop, the cinch, and your face going purple while a crowd that isn't there watches and does nothing &mdash; just as they did for it."],
    found="Under hanging-trees, in the rafters of old courthouses and barns, at the crossroads where the territory used to do its justice. It rises on the anniversary of its death, or whenever a fresh injustice is done on its ground.",
    keeper="The Gallows-Hung is a creature of grim irony, and you should lean into it. It targets the man who pulls a rope, the lawman, the one who recently saw someone hang &mdash; anyone whose hands match its memory. Describe the noose seeking necks, the way it drags a grabbed victim toward any high beam in the room; make the players fear the architecture. Mechanically it shrugs off gunfire, which teaches the lesson that <em>some</em> dead need their <em>story</em> addressed, not their body destroyed. The party that learns its name, its wrong, and the crossroads burial is the party that ends it. Bullets just make it angry.")}

  {creature(
    sb("The Drowned", "Tier II &middot; the river's dead", 14, 24, "swim fast; slow on land", "+8", "+4", "+5",
       "swollen grasp +6 (1d8+3 and grab); drags a grabbed soul under (Athletics or Fort DC 15 or begin drowning)",
       "<strong>Of the water.</strong> Strong and tireless in the river, weak and floundering more than a few yards from it.",
       "DC 13, 1d4 (1d6 as it surfaces)",
       "Draw it onto dry land and end it there, or give its drowned body a proper burial above the flood-line."),
    lore=[
      "The river takes more than it gives back, and not all of what it keeps stays still. The Drowned are those the water took &mdash; the forded too late, the swept-away, the weighted-down by men who wanted them gone &mdash; and the water has made them its own. Bloated, pale, patient, they wait in the green dark under the surface for a shadow to cross, a hand to dip, a horse to wade.",
      "On its own water the Drowned is terribly strong, and tireless, and at home. Pulled onto dry land it is a floundering, helpless ruin &mdash; which is the whole secret of fighting one, and the whole danger, because it knows this too, and will not be pulled if it can help it."],
    found="River fords and bends, mill-ponds, flooded mines, the slack water below a dam. Wherever someone drowned and was never properly buried, the water remembers.",
    keeper="The Drowned teaches terrain. In the water, it is a Tier above its numbers; on land, a Tier below. Make the players solve <em>where</em> the fight happens. A clever party lures it to shallows, ropes it, drags it ashore; a careless one wades in after it and learns what drowning feels like from the inside. Use the drowning rules to put a clock on grabbed characters &mdash; nothing focuses a table like a friend being pulled under, two rounds from dead. And remember the gentler ending: a Drowned given proper burial above the flood-line simply sinks back, grateful, and does not rise. Not every dead thing wants to hurt you. Some just want to be put to rest where the water can't reach.")}

  {creature(
    sb("The Weeping Woman", "Tier III &middot; she who lost her children", 17, 40, "fast along water", "+9", "+8", "+11",
       "drowning embrace +9 (2d6+4 and grab toward deep water); her wail (Will DC 16 or Frightened 2)",
       "<strong>The lure.</strong> Her weeping is heard for a mile and draws the soft-hearted to the water's edge; she takes children and the childlike first.",
       "DC 16, 1d6",
       "She cannot be killed, only freed &mdash; return what she lost, or lay her own drowned child to rest, and she goes into the water for good."),
    lore=[
      "Every river country tells her story, and tells it a little differently, but the grief is always the same. A woman lost her children to the water &mdash; by accident, by a faithless man, by her own drowning hand in a madness she has spent death regretting &mdash; and she has been walking the banks ever since, weeping, searching, calling for them in a voice that carries a mile on a still night.",
      "She is not cruel. That is the worst of her. She takes children because she is looking for her own, and the childlike and the soft-hearted because they answer her grief instead of fleeing it. Anyone who hears her weeping and feels their heart go out to her is already walking toward the water, and does not know it."],
    found="Along the rivers and irrigation ditches, the mill-races and the mission ponds &mdash; any water deep enough to drown a child, anywhere her own loss happened or anywhere grief like hers has stained the bank.",
    keeper="She is a tragedy with teeth, and you should let the tragedy do the work. Play her weeping as a genuine pull &mdash; have the soft-hearted character make the Will save to not walk toward the sound, and let them <em>want</em> to comfort her. The horror is that helping her is how she gets you. She cannot be killed; a party that tries to gun down a grieving mother and watches their bullets pass through her should feel that wrongness in their stomachs. The way through is mercy and investigation: who was she, what did she lose, where do the bones lie? Lay her child to rest and she goes into the water at peace. This is one to break their hearts a little. The best sessions with her end in a funeral, not a fight.")}

  {creature(
    sb("The Cold Bride", "Tier II &middot; jilted at the altar of the grave", 15, 22, "normal", "+7", "+5", "+8",
       "a touch like January +6 (1d8+3 cold and Drained 1); the offered hand (Will DC 14 or step toward her)",
       "<strong>Bound to her ground.</strong> She haunts the place she was wronged and cannot leave it; within it, the cold is hers.",
       "DC 13, 1d4",
       "Give her the wedding she was denied, the truth she was owed, or the bones of the man who wronged her &mdash; then she rests."),
    lore=[
      "She put on the dress and waited, and he did not come &mdash; or he came and did worse. The Cold Bride died at the threshold of a promise broken: jilted at the altar, murdered on her wedding night, left waiting at a window for a man who had already taken another road. The cold that killed her, or the cold that grew in her, never left. Now she waits still, in her grey and rotted finery, and the temperature drops where she walks.",
      "She is bound to the place she was wronged &mdash; a chapel, a homestead, a particular cold room &mdash; and cannot step past its bounds. But within it, the winter is hers to command, and she offers her hand to every man who enters with the terrible hope that this one, finally, will not leave her at the altar."],
    found="Abandoned chapels and the parlors of dead homesteads, the room where a wedding should have happened, the window where a bride waited too long. She does not leave her ground; her ground is the whole of her.",
    keeper="The Cold Bride is a haunting you can negotiate with, and that is what makes her interesting. Her binding to one place means a smart party can simply leave &mdash; but she usually sits between them and something they need, so leaving costs them. Her offered hand is a trap dressed as courtesy; let a player take it and feel the January cold climb their arm. The resolution is a question of justice: what was she owed? The truth named, the wedding mimed, the bones of the faithless man laid where she can see them &mdash; any of these can lay her to rest. Reward the player who treats her as a wronged woman rather than a monster. She has been waiting a very long time to be heard.")}

  {creature(
    sb("The Plague-Dead", "Tier II &middot; the dead of a bad season", 13, 20, "shuffling", "+9", "+1", "+3",
       "fevered claws +6 (1d8+3); any wound it deals festers (Fort DC 15 or Sickened 1, worsening nightly)",
       "<strong>Contagion.</strong> Its sickness spreads through wound, breath, and the water it has fouled; a town that buries it wrong buries itself.",
       "DC 13, 1d4",
       "Burn the bodies and everything they touched; salt and quicklime the ground. Do not bury. Do not loot."),
    lore=[
      "A bad season comes through &mdash; cholera, the bloody flux, the spotted fever &mdash; and a town buries more than it can grieve, fast and shallow and frightened. The Plague-Dead are what rises from those graves, still burning with the fever that killed them, still carrying it. They are not the worst fighters in this book. They do not need to be. The danger of the Plague-Dead is not in their hands; it is in their breath, their blood, the well they have fouled, the wound they leave behind.",
      "They shuffle, slow and feverish, and a child could outrun one. But a town that handles them wrong &mdash; that buries them, that loots the clothes off them, that drinks downstream of where they lie &mdash; buries itself by the next season."],
    found="The cemeteries and trench-graves of a town that took a hard epidemic, especially one buried in a panic. Fouled wells, sickrooms left as they were, the abandoned pest-house at the edge of a played-out settlement.",
    keeper="The Plague-Dead are a horror of consequence, not combat. The fight is easy; surviving it clean is not. Track the festering wounds, the worsening sickness, the contamination of water and supply &mdash; make the players feel that <em>winning</em> the fight can still doom them if they're careless with the aftermath. This is the entry that teaches a party to burn rather than bury, to salt and quicklime, to never loot the dead. Use them to put a clock on a whole town: the players have until the sickness spreads to act. A grim, slow-burn scenario where the monster is half disease, half corpse, and entirely a test of whether the party does the hard, thankless, correct thing.")}

  {creature(
    sb("The Scalp-Taker's Ghost", "Tier III &middot; a debt of old violence", 17, 38, "fast", "+9", "+9", "+10",
       "a spectral blade +9 (2d6+4); takes from the slain what was taken from it",
       "<strong>An old wrong.</strong> It rises where a massacre was done and hunts those of the blood that did it &mdash; or any who walk its ground at the wrong hour.",
       "DC 16, 1d6",
       "It is laid only by restitution &mdash; the wrong named aloud, the dead honored, the ground given back &mdash; not by the gun."),
    lore=[
      "The frontier was won with a great deal of blood that the history books have learned to skip past, and the country has not forgotten a drop of it. Where a massacre was done &mdash; a camp burned, a column ambushed, a wagon-train butchered, a people driven off a cliff &mdash; the wrong can rise as a single avenging shape, taking from the living what was taken from the dead.",
      "It does not distinguish finely between the guilty and the merely present. It hunts the blood of those who did the deed first, but anyone caught on its ground at the wrong hour is fair game for an old and indiscriminate rage. It is grief and fury given an edge, and it has waited a very long time to use it."],
    found="Massacre grounds &mdash; a particular draw, a burned village-site, a stretch of trail where something unforgivable happened. The land remembers even when the maps have been redrawn to forget.",
    keeper="This is the bestiary's hardest entry to run well, and its most rewarding. The Scalp-Taker's Ghost is a reckoning, and the table should feel the weight of real history behind it &mdash; handle it with gravity, not as a costume. It cannot be solved with violence; a party that tries to out-shoot an avenging massacre only adds to the body count it feeds on. The resolution is restitution: the wrong named aloud and unflinchingly, the dead honored, the ground returned or marked or made right. Use it when your table is ready for a story that asks something of them. The players who lay it to rest will remember that session for a long time, and so will the ones who refuse to.")}

  {creature(
    sb("The Mummied Prospector", "Tier I &middot; dried hard around his greed", 13, 16, "slow", "+6", "+2", "+4",
       "pick and claw +4 (1d6+2); throws himself between you and the gold",
       "<strong>His claim.</strong> Bound to the strike that killed him; harmless until the gold is touched, then tireless.",
       "DC 13, 1d4",
       "Leave the gold, or put it back. He wants nothing else, and will not stop while it's in your saddlebags."),
    lore=[
      "He found color at last, the strike of a lifetime, and it killed him &mdash; a cave-in, a winter, a partner's knife, a thirst he would not leave the diggings long enough to slake. The dry air of the high country cured him hard as jerky around the one thought he died holding: <em>mine</em>. The Mummied Prospector is greed mummified, a leathered scarecrow squatting on a fortune in a hole in the rock, and he has stopped being a man and become a condition of the claim.",
      "Walk into his diggings and he will not stir. Look at his gold and he watches. Touch his gold and the dried thing comes off its haunches with a pick in its fist and the tireless single-mindedness of the truly damned, and it will follow that gold to the ends of the earth and yours."],
    found="Played-out mines and lonely diggings, the dry caves and desert claims where a man could die and cure rather than rot. Always somewhere with gold still in it, because the gold is the whole of why he stays.",
    keeper="A perfect early-game morality trap, and a great one-shot. The Mummied Prospector is almost no threat &mdash; until the players' own greed wakes him, and then he is a relentless, low-grade curse that follows the gold forever. The lesson is restraint, and it lands best if you let the gold be genuinely tempting: a real payday, more than the party has ever seen, sitting right there. Let them take it. Let him rise. Then let them discover that he does not stop, does not tire, and does not want anything but the gold back. The table that puts the gold back learns a frontier truth &mdash; some fortunes cost more than they pay. The table that keeps it earns a recurring problem with a pick.")}

  {creature(
    sb("The Grave-Wight", "Tier III &middot; the thing in the old barrow", 17, 42, "normal", "+11", "+5", "+9",
       "cold grip +9 (2d6+4 and Drained 1, healing itself as much)",
       "<strong>Hoard-bound.</strong> It guards a buried trove and grows stronger the more of it remains; sunlight withers it.",
       "DC 16, 1d6",
       "Drag it into the sun, or scatter and cleanse its hoard so it has nothing left to keep."),
    lore=[
      "Older than the territory, older than the towns, there are barrows in the bad lands that no settler dug &mdash; mounded tombs of a people gone before the first wagon, with something still keeping watch inside. The Grave-Wight is that keeper: a withered, cold-handed thing wound around a hoard it has guarded past the death of everyone who ever knew its name, drawing strength from the wealth at its back.",
      "It is strongest in the dark of its mound, surrounded by its trove, and it heals the cold it deals straight back into itself. Drag it into honest sunlight, or take from it the gold and grave-goods that are the source of its strength, and the centuries catch up with it all at once."],
    found="Ancient burial mounds and barrows in the deep country, the tombs of vanished peoples, any old grave rich enough to be worth guarding for a few hundred years. Far from town, deep in the dark, down where the air is older.",
    keeper="The Grave-Wight is a dungeon boss in the old style, and you should build the dungeon around it. The barrow is its strength &mdash; the dark, the close air, the hoard &mdash; so the fight is really about <em>changing the conditions</em>: opening the mound to daylight, scattering the trove, denying it the wealth it feeds on. A party that learns to fight the room rather than the wight will win; one that trades cold grips with it in the dark will be drained dry, because every wound it lands heals it. Use the hoard as both lure and weakness: the gold that drew the players in is the very thing keeping the wight alive. Greed brought them down here. Greed is also the lock on the door.")}

  {creature(
    sb("The Ash Child", "Tier II &middot; a small grief that burns", 14, 18, "normal", "+5", "+6", "+7",
       "a touch that blisters +6 (1d8+3 fire); fires kindle on their own in its presence",
       "<strong>Grief made flame.</strong> Not cruel, only lost and hot; it follows whoever shows it kindness, and burns them all the same.",
       "DC 13, 1d4",
       "Find its bones in the burned place and bury them with its name and a kind word; nothing else cools it."),
    lore=[
      "A house burned, or a church, or a wagon, and a child did not get out. What came back is not vengeful and not cruel &mdash; it is just a small lost thing, frightened and alone and very, very hot, looking for the comfort it was denied at the end. The Ash Child drifts through the burned place where it died, and fires kindle on their own where it passes, and it reaches for any warmth that reaches back.",
      "That is the tragedy of it. Show the Ash Child kindness &mdash; speak gently, offer a hand, try to help &mdash; and it will follow you, grateful and trusting, and its touch will blister you to the bone, because it does not know its own heat. It cannot help what it does. It only wants not to be alone in the dark."],
    found="Burned homesteads and churches, the black bones of a torched wagon, any place a child died in fire and was never properly mourned. It haunts the ash, and the ash is never quite cold.",
    keeper="The Ash Child is the gentle gut-punch of the chapter, a sibling to the Weeping Woman in grief but smaller and sadder. Run it as something the players will <em>want</em> to save, and let that instinct be the danger &mdash; the kind-hearted character who tries to comfort it gets burned, not by malice but by a child who does not understand it is on fire. There is no fighting this one in any way that feels good; gunning down a frightened ghost-child is a thing that should sit wrong at the table. The mercy ending is the only right one: find the bones, learn the name, bury it with a kind word. A small, quiet, heartbreaking scenario. Use it when you want the party to remember that not everything in the dark deserved what happened to it.")}

  {creature(
    sb("The Revenant", "Tier III &middot; risen for one purpose", 17, 44, "normal", "+11", "+6", "+10",
       "ruinous blows +9 (2d6+5); singles out the one it died hating and walks through all else to reach them",
       "<strong>Cannot rest unfinished.</strong> Destroy the body and it rises again by the next night, whole, until its purpose is met.",
       "DC 16, 1d6",
       "Let it have its vengeance &mdash; or settle the wrong it died over &mdash; and it falls and does not rise."),
    lore=[
      "Murder leaves a debt, and some men die hating with enough force to come back and collect it personally. The Revenant rises with one purpose burned into whatever passes for its soul &mdash; the man who killed it, the betrayer, the one name it carried into the grave &mdash; and it walks toward that purpose through fire, through bullets, through anything and anyone in the way, with the awful patience of a thing that already knows it cannot truly die until the debt is paid.",
      "Kill the body and it is back the next night, whole, still walking. It does not flank, does not parley, does not deviate. It singles out the one it hates and goes through the rest of you as if you were so much brush, and it will keep coming, night after night, until its one purpose is satisfied or the world ends."],
    found="Wherever a murder went unanswered &mdash; the spot of a betrayal, the trail a wronged man walked, the town his killer fled to. It rises where it died and walks toward whoever it died hating, however far that is.",
    keeper="The Revenant is a force of moral physics, and the table needs to understand that early: it <em>will not stay dead</em>. Let them destroy it the first night and feel good about it. Then bring it back, whole, the next night, and let the dread set in &mdash; this is not a thing you kill, it is a thing you <em>resolve</em>. The drama is in the question of its target. If the one it hates is a villain, the party may be tempted to simply step aside and let justice walk; if the target is someone they've come to protect, they have a much harder problem &mdash; settle an old murder, or stand between an unkillable thing and the person it was made to destroy. Few monsters force better roleplay. The Revenant doesn't want the party. It wants one man. What they do about that is the whole story.")}

  {creature(
    sb("The Nightwalker", "Tier III &middot; the vampire dead", 18, 44, "fast; climbs sheer", "+11", "+9", "+8",
       "seizing grasp +9 (1d8+4 and grab); bite (vs. grabbed/helpless) +9 (2d6+4 and drain 1d6 Blood, healing as much)",
       "<strong>Cold blood.</strong> Heals 5 Blood each turn unless burned or in sunlight; its regard frightens (Will DC 16). It cannot cross an uninvited threshold, running water, or noon.",
       "DC 16, 1d6 (1d10 caught feeding)",
       "Pin it, stake it through the heart with seasoned wood, take the head and burn it, and salt the grave."),
    lore=[
      "The blood-drinking dead are an old terror that came west with the settlers and found the thin country much to their liking. The Nightwalker was a person once, and often still wears that person's face and manners and name &mdash; the genteel rancher who entertains only after dark, the charming stranger at the boarding house, the respected man whose household has a great many rules about windows and invitations. Underneath, it is a corpse that murders to keep walking.",
      "It is fast, strong, and hard to put down &mdash; it knits its wounds shut faster than guns can open them &mdash; and its mere regard can freeze a brave soul in place. But it labors under the old laws: it cannot cross a threshold it was not invited past, cannot cross running water, cannot abide the noon sun. The country gives even its worst dead some rules, if you are clever enough to use them."],
    witness=("&ldquo;It was polite. That&rsquo;s the part I can&rsquo;t shake. It knocked, and it waited to be asked, and God help me the Hendersons asked.&rdquo;", "the only survivor of the Henderson place"),
    found="Old houses with the curtains always drawn, played-out estates, the respectable parts of a town with a quiet problem. It keeps a lair &mdash; a grave, a cellar, a coffin of home soil &mdash; and must return to it before dawn.",
    keeper="The Nightwalker rewards the slow-burn. It is most frightening as a <em>person</em> first &mdash; a host, a benefactor, a neighbor whose hospitality has strange conditions &mdash; before it is ever a monster. Let the party meet it in daylight as a charming man, then slowly assemble the wrongness: the rules of the house, the missing ranch-hands, the pallor. Mechanically, its self-healing punishes a straight slugging-match; the secret is its laws. A clever party doesn't out-damage a Nightwalker, they out-<em>think</em> it &mdash; revoke its invitation, put running water between, trap it on the wrong side of dawn, then do the grim ritual work of staking and burning and salting. Make the laws discoverable through play, and let the climax be a tense daylight raid on the lair while the thing sleeps. This is your gothic centerpiece. Give it a name, a face, and a reason the town hasn't dealt with it. The best Nightwalker is one the players were guests of.")}

  {creature(
    sb("The Gravecaller", "Tier III &middot; the corpse that wakes the others", 16, 36, "shuffling", "+10", "+4", "+11",
       "withering touch +8 (2d6+3); each round, calls 1d4 Risen from any ground that holds the dead",
       "<strong>The conductor.</strong> Weak itself, but a battle against it is a battle against everything buried nearby.",
       "DC 16, 1d6",
       "Cut through the Risen to the Gravecaller and put it down; without it, the dead lie back down."),
    lore=[
      "Something has to do the waking. Behind many a risen graveyard, many a shambling host, there is a single corpse that woke first and remembered how &mdash; the Gravecaller, a withered dead thing with the terrible gift of calling its neighbors up out of the dirt. It is not much of a fighter on its own. It does not need to be. It stands at the back of the boneyard and conducts, and the dead answer.",
      "Each turn it draws fresh Risen from any ground that holds the buried, an endless tide so long as it stands and so long as there are graves to empty. To fight near a Gravecaller is to fight the whole cemetery; the only way to stop the flood is to reach the thing at its source and put it down."],
    found="At the heart of a risen graveyard or battlefield, usually toward the back, usually shielded by the very dead it raises. It is the cause behind the Boneyard Host as often as not &mdash; find the Host, and somewhere in it is the caller.",
    keeper="The Gravecaller is the answer to the Boneyard Host puzzle, and running them together is the chapter's signature set-piece. Mechanically it is simple but vicious: a fragile spellcaster behind an endless wall of bodies, where the only win condition is <em>reach it and end it</em>. This forces the tactical question the whole chapter has been building toward &mdash; do you grind forward through the press, or split off a fast striker to punch through to the conductor while the others hold the line? Place it cleverly: behind cover, up on a crypt, surrounded. Make getting to it the entire fight. The moment a player realizes the swarm has a heart, and goes for it, is the moment the encounter turns from despair to hope. Reward that realization. Kill the caller, and watch the dead lie back down all at once &mdash; one of the most satisfying images you can give a table.")}

  {creature(
    sb("The Restless Herd", "Tier II &middot; a stampede that never ended", 14, 30, "very fast", "+9", "+6", "+3",
       "trampling charge +6 (2d6+3, all in its path); cannot be turned once running",
       "<strong>Ghost cattle.</strong> The herd that died in the dark runs it still, and the drover who died with them rides at its head.",
       "DC 13, 1d4",
       "Lay the drover to rest &mdash; or turn the herd over the same draw that killed them &mdash; and the thunder stops."),
    lore=[
      "A drive went wrong in the dark &mdash; a lightning-spook, a cut bank, a river in flood &mdash; and a thousand head and the men riding them went over or under or down, all at once, in a thunder of terror. They never stopped running. On the bad nights you hear them first: a far-off rumble like weather, then the ground shaking, then the cold shapes of cattle pouring out of the dark with a dead drover riding hard at their head, and nothing alive in their path that stays standing.",
      "The Restless Herd cannot be turned once it runs and cannot be reasoned with, any more than a flood can. It is grief and terror and momentum, the last panicked moment of a hundred animals stretched out across the years, and the drover at its head is as trapped in it as they are."],
    found="The trails and river-crossings where a drive met disaster, the draws and cut banks that swallowed a herd. It runs on the anniversary, in the storm, or whenever the conditions of that first bad night come round again.",
    keeper="The Restless Herd is a hazard as much as a monster &mdash; run it like weather with intent. The terror of it is sensory: the distant rumble, the trembling ground, the realization of what is coming and the scramble to be anywhere but in the lane. Don't let the party fight it head-on; let them survive it, the way you survive a flood, by getting clear, gaining high ground, finding the rocks. The resolution lies with the drover at its head &mdash; lay him to rest, or turn the herd back over the same fatal ground that killed it, and the long stampede finally ends. A great chase set-piece and a good reminder that on this frontier, even the cattle can be ghosts. Pair it with a town that's been losing stock and riders on the same stretch of trail for thirty years, and let the players work out why.")}
</section>
"""

# ============================================================ III. CURSED BEASTS
BEASTS = f"""<!-- III -->
<section class="page" id="beasts">
  {runhead('III. Cursed Beasts &amp; Wild Things')}
  <h1 class="chapter">III. Cursed Beasts &amp; Wild Things</h1>
  <p class="chapter-sub">Animals the country bent, and things that were always wrong.</p>
  <div class="divider"></div>
  {quote("A wolf will kill you and think nothing of it. The thing I shot last winter thought about it the whole time.", "Eb Tuttle, trapper")}
  <p class="dropcap lead">Most beasts only want a living, same as you. These are the ones a hex, a hunger, or the deep
  places of the world have made into something else.</p>
  <p class="note"> <strong>Signs of the kind:</strong> tracks that change shape between prints, a kill left whole and uneaten, dogs and horses that will not enter their own country, and a wrong silence where the birds should be.</p>

  {creature(
    sb("The Hexed Beast", "Tier I&ndash;II &middot; a thing set upon you", 14, 16, "fast (1&frac12;&times;)", "+5", "+7", "+1",
       "rending bite +6 (1d8+3); a crit festers (Fort DC 15 or Sickened 1)",
       "<strong>Sent.</strong> A beast made wrong by a Witch or Hexer and bound to a quarry it knows by scent or name; while its maker lives, it returns by the next night if slain.",
       "DC 13, 1d4",
       "Kill the beast to buy a night; break the binding to end it. Silver and salt both bite it."),
    lore=[
      "Somebody wanted somebody dead and went to the kind of person who can arrange it. The Hexed Beast was an ordinary animal &mdash; a dog, a wolf, a wildcat, a hog &mdash; until a Witch or a Hexer worked a hate into it and pointed it at a name. Now it runs that name down with a single-minded wrongness no natural creature has, faster than it should be, surer than it should be, and it knows its quarry by scent or by the sound of a name spoken aloud.",
      "You can see the hex on it if you know to look: eyes that hold a little too much purpose, a hide marked with a brand or a stitched sign or a knotted hank of the victim's own hair worked into the fur. It does not hunt for food. It hunts for whoever paid to have it sent."],
    found="Anywhere its quarry runs &mdash; it crosses fences, towns, and territory lines without slowing. Look for its maker nearby: a Witch's cabin, a Hexer's wagon, a cuckolded rancher who paid cash for a curse.",
    keeper="The Hexed Beast is the party's introduction to the rule that runs half this book: <em>kill the body, and the binding brings it back</em>. Let them put it down the first night and feel the satisfaction, then have it come loping out of the dark the next night, whole and patient. The lesson is to follow the thread back to the hand that sent it. Use it as a clock and a breadcrumb &mdash; every night it returns, it points the party closer to its maker. The Tier band (I&ndash;II) lets you scale it to whatever the table can handle. Drop the brand or the hair-knot somewhere they'll find it; let a tracker or a wise NPC name it as a sending. Then the real adventure begins: not the beast, but the person who wanted blood badly enough to buy it.")}

  {creature(
    sb("The Pale Wolf", "Tier II &middot; a pack with one mind", 15, 22, "very fast", "+8", "+8", "+3",
       "pack-fang +6 (1d8+3); flanks and drags down; a crit knocks prone",
       "<strong>One will.</strong> Run the pack as a single hunter &mdash; patient, coordinated, and unafraid; it culls the strays and the wounded first.",
       "DC 13, 1d4",
       "Silver wounds it true; break its nerve by felling the lead wolf, the one with the old eyes."),
    lore=[
      "An honest wolf pack fears men, and rightly. The Pale Wolves do not. Something has burned the fear out of them and bred in its place a cold, shared cunning &mdash; ash-white in coat, old-eyed, and moving with a coordination that no natural pack has, as if a single mind were looking out of a dozen sets of eyes. They are wrong in a way you feel before you can name it.",
      "They hunt like a thinking thing. They cull the strays first, the wounded, the one who wandered from the fire; they flank, they feint, they wait. A man alone is already taken. A camp that lets one of its number drift to the edge of the light has fed the pack without knowing it yet."],
    found="The high lonesome country, the long stretches between towns, the winter range where help is far. They follow a party for days before they strike, learning its habits and its weak ones.",
    keeper="Run the Pale Wolves as one intelligence in many bodies. They should feel <em>tactical</em> in a way that unnerves the players &mdash; pulling back when hurt, concentrating on the isolated, never doing the dumb thing a real animal would do. The dread is the slow realization that they are being <em>hunted by something that thinks</em>. Mechanically, the lead wolf is the linchpin: fell the old-eyed one and the shared nerve breaks, and the rest become ordinary frightened animals. Make that lead wolf identifiable &mdash; bigger, scarred, hanging back to direct &mdash; so a sharp-eyed player can pick it out and solve the fight with one good shot. Silver bites them true, which is a useful early lesson that the right tool matters more than the most lead.")}

  {creature(
    sb("The Ghost Cat", "Tier II &middot; the cougar that isn't there", 16, 20, "very fast; leaps", "+7", "+9", "+5",
       "ambush pounce +7 (1d8+4 and grab); +2 and a die from surprise",
       "<strong>Unseen.</strong> Leaves no track and makes no sound until it strikes; it haunts the trail where it died and the bones it still guards.",
       "DC 13, 1d4",
       "Salt and burn its old kill-cache, or its own bleached bones in the rocks above the trail."),
    lore=[
      "A cougar killed wrong &mdash; shot and left to die slow, trapped and starved, poisoned by a rancher's bait &mdash; can come back as the Ghost Cat, and it brings its grudge with it. It haunts the trail where it died, a pale shape glimpsed at the edge of vision and never twice in the same place, leaving no track in the dust and making no cry until it is already on you.",
      "It guards the bones of its old kills and its own bleached skeleton in the rocks with a jealous, patient fury. Riders who use that trail begin to go missing, taken from the saddle so quietly that the horse comes home alone and the rest of the party rides on a while before they notice the empty place in the line."],
    found="A particular stretch of trail, pass, or canyon where a cougar died badly &mdash; usually a route the party has reason to use more than once. Its kill-cache and its own bones lie hidden in the rocks above.",
    keeper="The Ghost Cat is about the dread of the unseen. It leaves no tracks, makes no sound, and is never seen full &mdash; play it as glimpses, wrongness, the horse that spooks at nothing, the rider who isn't there anymore. Lean on the surprise mechanics: when it strikes from hiding, it hits hard and grabs, and the table should feel the terror of a friend simply <em>gone</em>, dragged off into the rocks. It can't be hunted like a normal animal because you can't find it. The solution is to find what anchors it &mdash; its kill-cache, its own bones in the high rocks &mdash; and salt and burn them. This rewards investigation over marksmanship: a party that tracks the disappearances back to the source ends it; a party that just keeps riding the trail keeps losing people.")}

  {creature(
    sb("The Chupacabra", "Tier I &middot; the goat-sucker", 14, 12, "fast; springs", "+5", "+7", "+2",
       "draining bite +4 (1d6+2 and drinks 1 Blood); spines bristle (1d4 to a grappler)",
       "<strong>Night-thirst.</strong> Comes for penned stock by dark, draining them bloodless; bold only against the cornered and the small.",
       "DC 13, 1d4 (the sight of what it leaves)",
       "Salt the pens, ward with iron and light; run it down by day when it lies up, slow and gorged."),
    lore=[
      "The goat-sucker is a small terror and a thief in the night, more a plague on a homestead than a threat to an armed man. It comes for the penned stock by dark &mdash; goats, sheep, a calf, a dog &mdash; and leaves them dead and bloodless, two neat punctures and not a drop spilled on the ground, which is the sight that earns the Dread Check more than the thing itself.",
      "It is a sprung, spined, leathery thing, bold only against the small and the cornered. Face it with a gun and a lantern and it would rather flee; corner it at its lying-up place by day, gorged and sluggish, and it is barely a fight at all. But find a homestead it has been visiting and you find a family being slowly ruined, one animal a night."],
    found="The edges of homesteads and ranches, especially poor ones with stock penned close. It lies up by day in brush, an old burrow, or a dry wash within a night's range of its feeding-ground.",
    keeper="The Chupacabra is a low-stakes mystery and a fine first creature for a green party. The horror is in the discovery, not the fight &mdash; the bloodless stock, the neat punctures, the family's mounting fear and ruin. Play the investigation: what's killing the goats, where does it go, how do you catch a thing that only comes in the dark? Reward the party that thinks to ward the pens, stand watch, and track it back to its day-lair where it's slow and beatable. It's a teaching creature &mdash; it shows the table that not every problem is solved by a stand-up fight, and that protecting ordinary people from small, persistent evils is its own kind of heroism. Save the big monsters for later; let them earn a town's gratitude over a goat-sucker first.")}

  {creature(
    sb("The Hidebehind", "Tier III &middot; the thing at your back", 17, 38, "fast", "+9", "+11", "+8",
       "raking pull +9 (2d6+4, from behind); always strikes from cover",
       "<strong>Never seen full.</strong> It keeps a tree, a man, a shadow always between you and it; you cannot harm what you cannot face.",
       "DC 16, 1d6",
       "Force it into the open &mdash; firelight in a ring, a mirror, two who watch each other's backs &mdash; and it can be shot like anything else."),
    lore=[
      "The lumber camps of the deep woods tell of it, and they do not tell it laughing. The Hidebehind is the thing you never quite see &mdash; it keeps a tree-trunk, a shadow, the body of your own companion always between itself and your eyes, so that no matter how fast you turn, it has already slipped behind the next thing. You feel it at your back. You hear it move. You never face it.",
      "It takes the woodsman who works alone, the straggler, the one who wandered off to relieve himself in the dark. By the time the others come looking there is blood at the base of a tree and nothing else, and the certainty, prickling up every neck in the party, that whatever did it is watching them look."],
    found="The deep timber, the old-growth forest, the logging camps and the trails through dense cover &mdash; anywhere there are enough trunks and shadows for it to keep something always between you and it. It hates open ground.",
    keeper="The Hidebehind is a puzzle dressed as terror, and the puzzle is its whole charm. Mechanically, it always has cover and you cannot harm what you cannot face &mdash; so a party that just tries to shoot it loses, every time. The solution is to <em>take away its hiding</em>: a ring of firelight with no shadow to hold, a mirror that shows what's behind, two people standing back-to-back watching each other's blind side, an open meadow with nowhere to slip to. Make the players figure out that the fight is really about geometry and light. The dread comes from the build-up &mdash; the missing straggler, the feeling of being watched, the thing always one turn behind your eyes. When they finally corner it in the open and it stands revealed, let the reveal land: it was solvable all along, if they could just make it stop hiding. A great creature for a party that's learned to think.")}

  {creature(
    sb("The Snallygaster", "Tier III &middot; the winged thing off the ridge", 16, 40, "fly fast", "+9", "+10", "+5",
       "stoop and seize +9 (2d6+4 and carries a soul aloft); a screech that scatters horses",
       "<strong>From above.</strong> It hunts from the dark sky and is gone before the echo, taking livestock and lone riders.",
       "DC 16, 1d6",
       "It will not cross a threshold marked with a seven-pointed star, nor abide the toll of a true iron bell; ground it, then finish it."),
    lore=[
      "It nests in the high broken country off the ridge, and it hunts the way a hawk hunts a mouse &mdash; from far above, unseen against the dark sky, a sudden rush of wings and a screech that sends every horse for a mile into a panic, and then it is climbing again with a calf or a steer or a man clutched in its talons, gone before the echo dies.",
      "The old families of the valley know the wards: a seven-pointed star painted on the barn door and the byre, an iron bell rung true at dusk. The Snallygaster will not cross the star, and the bell's toll drives it back to its crags. Newcomers who scoff at the painted stars tend to lose stock until they stop scoffing."],
    found="The high crags and broken ridges above a settled valley, from which it stoops on the farms and trails below. It nests somewhere nearly inaccessible; getting to the nest is half the campaign.",
    keeper="The Snallygaster is an aerial predator and a folk-horror puzzle in one. Its altitude is its strength &mdash; it strikes from above and is gone, so a party can't just trade blows with it. The wards are the lever: the seven-pointed star and the true iron bell are protections the locals already use, and a clever party learns them, uses them to deny the thing its hunting-grounds, and forces it to either starve or come down low where it can be fought. Stage the climax as a hunt for the nest in the high rocks, or an ambush sprung when the wards finally pen it in. Use the local lore as both color and mechanics &mdash; the superstitious farmers were right all along, and the players' respect (or contempt) for old knowledge shapes how badly the hunt goes.")}

  {creature(
    sb("The Thunderbird", "Tier IV &middot; the storm that has eyes", 20, 70, "fly very fast", "+15", "+13", "+9",
       "talons like fence-posts +13 (2d8+6); wingbeat thunderclap (Fort DC 18 or deafened and prone)",
       "<strong>Brings the weather.</strong> The storm rides with it; it is old, proud, and not always hostile &mdash; an offering and a wide berth have turned it before.",
       "DC 20, 1d10",
       "It is not meant to be killed by men. Drive it off with respect, with fire, or with the high ground &mdash; and pray it judges you not worth the trouble."),
    lore=[
      "It is older than the territory and older than the men who named it, and the storm is its shadow on the land. Where the Thunderbird flies, the weather flies with it &mdash; the sky goes green-black, the thunder rolls in its wingbeats, the lightning answers its eye. It is vast beyond reckoning, proud, and it does not think of men the way a hawk does not think of insects.",
      "It is not, as such things go, malicious. It has been turned aside by respect, by an offering left on a high place, by men who had the sense to give it a wide berth and bow their heads. But a fool who fires on it, or fouls its high country, or simply stands where it wants to be, will learn how small a man is under a thing that wears the storm for a coat."],
    witness=("&ldquo;The storm had eyes. I will not be talked out of it. It looked at the herd, and it chose.&rdquo;", "Eb Tuttle, trapper"),
    found="The high plains and the mountain peaks, the open sky where the great storms build. It does not lair so much as range, vast and far-traveling; it comes when the weather comes.",
    keeper="The Thunderbird is one of the book's lessons that <em>not everything is yours to kill</em>. Its numbers are punishing on purpose &mdash; a stand-up fight is a losing proposition, and the table should sense that. Run it with grandeur and ancient indifference: it is weather with intent, not a beast with a grudge. The right resolution is almost never combat; it is respect, offering, retreat, reading the signs and giving the old thing its road. Use it to humble a party that has gotten used to winning, or as a force of nature woven through a larger story &mdash; the storm that guards a mountain pass, the omen that precedes a reckoning. If the players must drive it off, make it cost them, and make the victory feel like surviving a hurricane rather than slaying a monster. Some things you don't defeat. You endure them, and you're grateful they let you.")}

  {creature(
    sb("The Horned Serpent", "Tier III &middot; the thing in the deep water", 17, 46, "swim very fast", "+11", "+8", "+7",
       "crushing coils +9 (2d6+4 and grab, Constricting); swallows the small whole",
       "<strong>Patient and vast.</strong> It lies in river-bend and lake-bottom and takes what comes to drink; its single horn is a coveted, dangerous prize.",
       "DC 16, 1d6",
       "The horn is the heart of it &mdash; strike there, or break it off, and the serpent's strength goes out of it."),
    lore=[
      "In the deep water &mdash; the lake-bottom, the still river-bend, the flooded sink that never seems to drain &mdash; something old and patient waits. The Horned Serpent is vast, scaled, and crowned with a single great horn, and it lies in the dark below for days or weeks until something comes to drink, and then the water erupts and the coils close and whatever it was is gone under without a cry.",
      "The horn is the prize and the danger both. Old tales say it cures any poison, wards any curse, brings luck or rain or sight beyond sight &mdash; and the men who go after it mostly become part of the reason the next man believes the legend. The horn is also the serpent's heart and strength; break it off, and the great coils go slack."],
    found="Deep, still water &mdash; a lake, a flooded quarry, a river's deepest bend, a spring-fed sink. It claims one body of water and rules it utterly; the locals know not to swim there and not to say why too loudly.",
    keeper="The Horned Serpent is a terrain monster and a temptation. On its own water it is overwhelming &mdash; vast, patient, constricting, able to swallow the small whole &mdash; so the fight is really about denying it the water or striking its one weakness. The horn is the elegant solution and the bait: it's the source of its strength (break it and the serpent weakens) and a coveted treasure that drew the party in. Let the legend of the horn's powers pull greedy hands toward deep water; let the cost of reaching it be steep. Stage the fight so the party must lure it to the shallows, pin it, or get someone dangerously close to strike or break the horn. A good water-monster set-piece, and a reminder that the most valuable thing in the country is usually attached to the most dangerous thing in the country.")}

  {creature(
    sb("The Carrion Cloud", "Tier II &middot; a thousand wrong birds", 13, 24, "fly fast", "+7", "+9", "+4",
       "a storm of beaks +6 (2d6+2, all nearby); blinds and smothers",
       "<strong>One hunger.</strong> Crows and buzzards moved by a single dark appetite; they strip a steer to bone in minutes and a man not much slower.",
       "DC 13, 1d4",
       "Fire, smoke, and loud iron scatter the flock; find and burn the carrion-thing at its center that calls them."),
    lore=[
      "A flock of crows is an omen; a flock of crows with one mind is a horror. The Carrion Cloud is a great wheeling mass of crows and buzzards moved by a single dark hunger, and where it descends it leaves bone. A steer is stripped in minutes, a downed man not much slower, in a shrieking blizzard of beaks and wings that blinds and smothers and gives the prey nowhere to look and nothing to hit.",
      "At the heart of the cloud is the thing that calls them &mdash; a carrion-spirit, a cursed corpse, a black appetite that wears the flock like a coat. Scatter the birds and they re-gather; the only way to end it is to find the cold center and burn it."],
    found="Over battlefields, killing-grounds, and the wake of disaster &mdash; anywhere death has been plentiful and the carrion-thing at the cloud's heart was born or drawn. It follows slaughter the way buzzards follow a dying steer.",
    keeper="The Carrion Cloud is a fight against an area, not a body. Run it as a single swarming hazard &mdash; one Blood pool, one area attack that catches everyone caught in it, blinding and smothering &mdash; and let the players feel the panic of being inside a storm of beaks with nothing solid to shoot. Fire and smoke and loud iron scatter it temporarily, buying room to think, but it always re-gathers. The real win is finding the carrion-thing at its center: the cursed corpse, the spirit, the black heart that calls the birds. Burn that, and the cloud disperses into ordinary frightened crows. This teaches the swarm-with-a-heart pattern (sibling to the Gravecaller) &mdash; the lesson that some swarms have a source, and you fight the source, not the storm.")}

  {creature(
    sb("The Bewitched Grizzly", "Tier III &middot; a mountain under a hex", 17, 48, "fast", "+11", "+5", "+4",
       "claw and maw +9 (2d6+5, two a round); a crit carries you off the trail",
       "<strong>Ridden by rage.</strong> A great bear made tireless and cruel by a charm worked into its hide; it does not tire, flee, or feel a wound that should fell it.",
       "DC 16, 1d6",
       "Cut the charm from its hide &mdash; a knot of hair, a brand, a stitched sign &mdash; and it is only a bear again, and dying."),
    lore=[
      "A grizzly is danger enough on its own terms. Take one and work a charm into its hide &mdash; a brand burned in, a sign stitched under the fur, a knot of hair and bone bound to its hide &mdash; and you have a mountain of muscle and tooth that does not tire, does not flee, does not feel the wounds that should have felled it three shots ago. It is ridden by a borrowed rage, and it keeps coming long after a natural bear would have broken off and gone to die.",
      "Whoever hexed it had a reason &mdash; a feud, a grudge, a witch's spite &mdash; and the bear is the instrument. Underneath the charm it is still only a bear, confused and in pain and made cruel against its nature. End the charm and you give it back its death."],
    found="The high country and the deep timber, wherever grizzlies range and a Witch or Hexer had cause to make a weapon of one. It's usually aimed: sent against a homestead, a rival, a town that crossed the wrong person.",
    keeper="The Bewitched Grizzly is the Hexed Beast scaled up to a wall of fury, and it teaches the same lesson harder: <em>damage isn't the answer, the charm is</em>. Let the party empty their guns into it and watch it shrug off wounds that should drop a bull. The secret is the charm worked into its hide &mdash; a brand, a stitched sign, a hair-knot &mdash; and cutting it free turns the unkillable monster back into a dying bear. This forces a different kind of fight: someone has to get close enough to find and cut the charm while the rest hold the line, which is terrifying against something this strong. Seed the charm visually &mdash; a glimpse of the brand, fur that's been tampered with &mdash; so an observant player can deduce the trick. And remember the pathos: it's a victim too, and ending the charm is a mercy as much as a kill.")}

  {creature(
    sb("The Razorback Shoat", "Tier II &middot; the hog out of the bad bottoms", 15, 26, "fast", "+9", "+5", "+2",
       "goring tusks +6 (1d8+4); a crit gores and tramples",
       "<strong>Eats anything.</strong> Bone, iron, the dead, the living; a sounder of them will clear a homestead and leave nothing to bury.",
       "DC 13, 1d4",
       "Cold iron in the heart; they fear fire and a true-aimed shot to the shoulder that drops them mid-charge."),
    lore=[
      "The hogs out of the bad bottoms are not right, and have not been for a long time. Something in the sour ground down there got into the stock that went feral, and what came back up is a sounder of razorbacks that will eat anything &mdash; bone, iron, the carrion dead, the living &mdash; with a relentless, grinding hunger that clears a homestead down to the foundations.",
      "They come in numbers, low and fast and armored in gristle, and they are not afraid of a man the way a wild hog ought to be. A family that finds the pens torn open and the dog half-eaten and the prints of a dozen heavy hogs in the mud has a hard night coming, and not much time to get ready for it."],
    found="The sour bottoms and bad swamps where feral hogs have gone wrong, and the homesteads within raiding range. They range out at night and clear everything edible before moving on.",
    keeper="The Razorback Shoat is a swarm of the mundane gone wrong &mdash; a whole sounder, a tide of armored, anything-eating hogs that comes at a homestead in numbers. Run it as a defense scenario: the family, the pens, the night coming, the prints in the mud. The fight is about position and fire &mdash; they fear flame, and a true shot to the shoulder drops one mid-charge, but a dozen low fast targets in the dark is genuinely dangerous. Use them to bloody a party that's gotten cocky, or as the opening threat that brings the players to a place with a deeper problem (what soured the bottoms?). A good honest meat-grinder of an encounter that rewards barricades, choke points, and not letting the sounder surround you.")}

  {creature(
    sb("The Hodag", "Tier II &middot; the swamp's bad temper", 16, 28, "normal; wallows", "+9", "+4", "+3",
       "horned charge +6 (1d8+4); spined back (1d6 to any who close)",
       "<strong>Mean and armored.</strong> A low, plated brute of the wet country that wants only to be left alone, and kills lavishly when it isn't.",
       "DC 13, 1d4",
       "It cannot abide woodsmoke and lye; lure it onto open ground and break its short, brittle legs."),
    lore=[
      "Low to the ground, plated like a snapping turtle, horned and spined and foul of temper, the Hodag is the swamp's own bad mood given a body. It wallows in the wet country and wants only to be left alone &mdash; but it defines 'left alone' generously, and a logging crew or a homestead that crowds its range will find out exactly how lavishly a thing this armored can kill when it's put out.",
      "Its plates turn light shot and its spined back punishes anything that closes to grapple, but it is built wrong for speed &mdash; short, brittle legs under all that armor. On open ground, away from its wallow, it is a slow fortress that can be toppled. In the muck it called home, it is another matter."],
    found="Cedar swamps, bogs, and the deep wet timber. It claims a wallow and a range around it and grows meaner the more its country is encroached on by logging, draining, or settlement.",
    keeper="The Hodag is a terrain-and-tactics puzzle wearing a foul temper. Its armor turns light shot and its spines punish grapplers, so the party can't just blast it or pile on. The keys are in the entry: it can't abide woodsmoke and lye (drive it with those), and its short brittle legs are the weak point (lure it onto firm open ground where its weight works against it and break its legs out from under it). Reward the party that fights the matchup instead of the monster &mdash; that uses smoke to herd it, picks the ground, goes for the legs. It also works as a 'the land is fighting back' creature: the more a logging operation or a draining scheme chews up the swamp, the meaner the Hodag gets, which can tie it into a larger story about what settlement costs the country.")}

  {creature(
    sb("The Pale Crawler", "Tier II &middot; the blind thing from below", 15, 22, "fast; climbs", "+7", "+8", "+3",
       "claws in the dark +6 (1d8+3); drags prey down into the rock",
       "<strong>Hears everything.</strong> Eyeless and white from the deep caves; it hunts by sound and is helpless against true silence and sudden light.",
       "DC 13, 1d4",
       "Bright light staggers it; move slow and quiet, then strike &mdash; or wall it back into the dark it came from."),
    lore=[
      "Deep under the rock, in the lightless places no settler ever meant to go, things live that have never needed eyes. The Pale Crawler is one &mdash; eyeless, bone-white, long-limbed, and built to climb the cave walls and ceilings in perfect dark, hunting entirely by sound. It hears a heartbeat across a cavern, a held breath, the scuff of a boot on stone, and it comes for the source fast and silent.",
      "It surfaces where the deep caves meet the world of men: a played-out mine that broke into older tunnels, a sinkhole, a cellar dug too deep. And then the miners start disappearing, dragged down into the rock, and the ones left learn to work in a silence that is its own kind of terror."],
    found="Deep caves, mineshafts that broke into natural caverns, sinkholes and the lowest cellars. It comes up from below when men dig too far, and it drags its prey back down into the dark to feed.",
    keeper="The Pale Crawler inverts the usual rules: it hunts by sound and is helpless against silence and light. This makes encounters with it tense and tactical in a wonderful way &mdash; the party that blunders in loud and dark feeds it; the party that learns to move slow and silent, that brings bright light to stagger it, that sets up an ambush in the quiet, wins. Run the soundscape: make the players nervous about every dropped tool and loud word, reward whispered planning and careful movement. Bright light is the great equalizer &mdash; a lantern unhooded at the right moment staggers it and turns the tables. Use it in any underground scenario to make the dark itself the enemy, and to teach the party that sometimes survival is about discipline and quiet, not firepower. A lantern, a held breath, and a steady hand beat a fast gun down there.")}

  {creature(
    sb("The Devil's Coyote", "Tier I &middot; the trickster on the trail", 14, 12, "very fast", "+4", "+8", "+5",
       "snapping bite +4 (1d6+2); leads travelers astray with false sign and called voices",
       "<strong>Never where it seems.</strong> More nuisance than killer until it has you lost, alone, and far from the fire &mdash; which is the whole game.",
       "DC 10, 1",
       "It cannot cross a line of salt or a running rope of prayer; hold your ground, and it loses interest by dawn."),
    lore=[
      "The trickster of the old stories never left, and it still finds the whole business of leading men astray richly amusing. The Devil's Coyote is rarely a killer outright &mdash; it is a mischief, a will-o'-wisp with fur, a thing that throws false trail-sign and calls in voices you know and leads you in circles until you are lost, alone, and a long way from the fire and the friends who could help you. <em>That</em> is the game. The bite, if it comes to that, is almost an afterthought.",
      "It loves a traveler who is sure of his bearings, a guide who is proud of his skill, a party that splits up. Where it has been working, men ride confidently in exactly the wrong direction, follow voices that call their names from the dark, and end the night much farther from home than they started, and much more afraid."],
    found="The trails and open country between settlements, especially at dusk and after dark. It works the over-confident and the lone traveler; it loves a crossroads, a fork, a place where one wrong turn compounds.",
    keeper="The Devil's Coyote is a low-stakes, high-flavor creature that turns navigation and confidence into the battlefield. It barely fights &mdash; the danger is being led astray, separated, and worn down until you're somewhere much worse. Run it as creeping wrongness: the trail that doesn't match the map, the voice calling a player's name from the dark, the campfire that should be due east now somehow behind them. The wards are folk-simple and should feel earned &mdash; a line of salt, a rope of prayer, holding your ground until dawn breaks its game. Use it to teach the party to distrust easy paths and called voices, to stick together, to hold position when lost rather than chasing. It's a great unsettling opener before a bigger threat, or a recurring nuisance that makes the country itself feel alive and faintly malicious. Don't let it kill anyone outright &mdash; let it strand them somewhere that something else can.")}

  {creature(
    sb("The Skinned Stallion", "Tier II &middot; the horse that was flayed", 15, 24, "very fast", "+8", "+8", "+3",
       "trampling hooves +6 (1d8+3, two a round); runs down what flees",
       "<strong>Runs forever.</strong> A wronged, flayed horse that gallops the range by night and tramples whatever it overtakes; it never tires.",
       "DC 13, 1d4 (the look of it)",
       "Find and burn its stolen hide where it was hung, and the stallion lies down at last."),
    lore=[
      "A horse was flayed alive &mdash; by a cruel man, a vicious punishment, a ritual that wanted the hide for something &mdash; and the wrong of it was great enough to bring the animal back. The Skinned Stallion gallops the night range, a raw and terrible shape, red and glistening and tireless, running down whatever crosses its path and trampling it under hooves that never slow.",
      "It is not malicious so much as agonized, a pain given motion, and it cannot stop. The look of it alone is a Dread Check. Somewhere its stolen hide hangs &mdash; on a barn wall, a drying-rack, in the lodge of whoever took it &mdash; and until that hide is found and burned, the stallion runs and the country it runs is not safe after dark."],
    found="The open range and the night trails near where it was flayed. Its stolen hide hangs somewhere within that country &mdash; a barn, a trophy wall, a ritualist's lodge; find the hide and you find the key.",
    keeper="The Skinned Stallion is a tragedy that resolves through investigation, not combat. Fighting the thing directly is grim and largely futile &mdash; it's tireless and runs down whatever flees. The answer is to find its flayed hide, wherever the cruel hand that took it hung it, and burn it. This turns the encounter into a hunt for a story: who flayed a horse, and why, and where's the hide now? The cruelty at the root gives you a villain and a mystery. Play the stallion's appearances as horror set-pieces &mdash; the raw red shape thundering out of the dark, the Dread of just seeing it &mdash; while the real work is tracking the wrong back to its source. When the party burns the hide and the stallion finally folds and lies still, let it be a release, not a victory. Cruelty made it; mercy ends it.")}

  {creature(
    sb("The Glutton", "Tier II &middot; the hunger with claws", 16, 24, "fast; tireless", "+9", "+7", "+3",
       "tearing claws +6 (1d8+4, two a round); fouls and eats what it cannot carry",
       "<strong>Never full.</strong> A carcajou-thing that follows a party for days, raiding, ruining stores, and growing bolder as they grow weak.",
       "DC 13, 1d4",
       "Fire frightens it and a full belly will not; deny it your stores, corner it, and it fights stupid."),
    lore=[
      "It is a wolverine-thing grown wrong, all appetite and spite, and it has decided your party is a moving larder. The Glutton follows for days &mdash; never quite seen, always at the edge of camp &mdash; raiding the stores, fouling what it cannot carry off, killing more than it eats out of pure malice, and growing bolder with every night as the party grows hungrier, more tired, and more desperate.",
      "It is not strong enough to take an armed and rested camp head-on, and it knows it. So it wages a war of attrition instead: a torn grain-sack here, a stolen haunch there, a horse spooked off in the night, until the party is worn thin enough to be worth a real fight. It is patient, tireless, and never, ever full."],
    found="The wilderness trails, the long crossings between supply, the deep country where a party carries everything it needs. It attaches itself to travelers and follows them as far as the food lasts &mdash; theirs, then them.",
    keeper="The Glutton is a creature of attrition and dread-by-erosion, best run over several nights rather than one fight. It's a logistics nightmare with claws: it doesn't beat the party in a battle, it beats them by ruining their supplies, spooking their horses, and wearing them down until they're weak enough to take. Run the slow grind &mdash; each morning, something's gone or fouled; each night, it's a little bolder. The players will come to <em>hate</em> it, which is exactly right. The resolution is to stop reacting and start hunting: deny it the stores it's after, set a trap, corner it &mdash; because cornered and denied, it fights stupid and dies easy. The lesson is that some threats are about discipline and supply, not heroics, and that a small relentless enemy can be deadlier than a big one if you let it dictate the terms.")}

  {creature(
    sb("The Rattlewyrm", "Tier III &middot; the serpent grown long as a fence-line", 17, 40, "fast; burrows", "+11", "+9", "+4",
       "venom-fang +9 (2d6+4 and Fort DC 16 or Drained and slowed); coils and crushes",
       "<strong>The rattle.</strong> Heard before seen; the dry sound of it from the rocks is itself a Dread Check (DC 13). It strikes from cover and is gone.",
       "DC 16, 1d6",
       "Smoke it from its den and take the head; the venom answers to no remedy the frontier carries, so do not be bitten."),
    lore=[
      "Somewhere out in the rocks a rattlesnake kept growing, long past the size God meant for it, until it was long as a fence-line and thick as a man's thigh, with a rattle like dry bones in a bucket and a venom that no remedy the frontier carries can answer. The Rattlewyrm is heard before it is seen &mdash; that dry, buzzing warning from the rocks above the trail is itself enough to set a brave man's nerve to fraying.",
      "It strikes from cover, fast and certain, and is gone back into the rock before the echo fades. It burrows, it climbs, it lies in wait in the warm stones, and it takes the stock and the children and the careless from the edges of a settlement that has learned to fear a particular stretch of broken ground."],
    found="Rocky badlands, canyon country, and the broken sun-warmed ground where rattlesnakes thrive &mdash; grown to monstrous size. It dens in the deep rocks and ranges out to hunt the warm hours and the cool nights.",
    keeper="The Rattlewyrm weaponizes the most American of fears and makes it monstrous. The rattle is the centerpiece &mdash; that dry sound from the rocks is a Dread Check on its own, and you should use it to make the players tense before the thing ever strikes. It fights as a hit-and-run ambusher: strikes from cover, injects a venom nothing can cure, and vanishes back into the rock. The Drained-and-slowed venom turns a bitten character into a liability, ratcheting the pressure. The key in the entry is plain: don't get bitten, and smoke it from its den to fight it on your terms rather than its. Reward the party that locates the den, blocks the bolt-holes, and forces it into the open with smoke &mdash; and that respects the venom enough to keep someone back with a remedy that probably won't work. A great creature for canyon country and a hard lesson in why the locals walk careful in the rocks.")}
</section>
"""

# ============================================================ IV. MEN, AND THE SHAPES OF MEN
MEN = f"""<!-- IV -->
<section class="page" id="men">
  {runhead('IV. Men, and the Shapes of Men')}
  <h1 class="chapter">IV. Men, and the Shapes of Men</h1>
  <p class="chapter-sub">The worst of the dark wears a face and answers to a name.</p>
  <div class="divider"></div>
  {quote("The worst of them started human. Some of them still answer to their Christian names, and smile when you use them.", "Rev. A. Jensen")}
  <p class="dropcap lead">Bullets work on these &mdash; mostly &mdash; which is its own kind of horror, because so often the
  thing you have to shoot has a name you knew.</p>
  <p class="note"> <strong>Signs of the kind:</strong> a neighbor whose shadow falls wrong, a stranger who knows what he should not, a reflection a beat behind its owner, and a town gone quiet about one name.</p>

  {creature(
    sb("Road Agents", "Tier I&ndash;II &middot; men, and only men", "14 (15 cover)", "13 (boss 24)", "normal", "+4", "+5", "+2 (boss +5)",
       "revolver +5 (1d8+2, range 60 ft); boss: two shots +7 (1d8+3)",
       "<strong>Mortal.</strong> They break (morale) when bloodied or leaderless &mdash; the only foes in this book who do. Use them to teach that bullets work, before the night teaches what doesn't.",
       "none &mdash; until something takes the gang from behind",
       "Lead, leverage, or a worse monster; a routed gang scatters and is done."),
    lore=[
      "Before the country teaches the party what they cannot kill, it ought to remind them of what they can. Road Agents are exactly what they appear: men with guns and bad intentions, holding up the stage, the bank, the lone rider, working the lonely stretches where the law is a day's ride away. They are dangerous the ordinary way &mdash; a bullet in the dark, a shotgun at close range &mdash; and they die the ordinary way too.",
      "They are the baseline against which every horror in this book is measured. They break when they're losing. They run when their boss goes down. They can be reasoned with, bribed, bluffed, and outdrawn. Remember the feeling of fighting them, because the whole rest of the country is built out of things that do none of those reassuring things."],
    found="The lonely roads, the stage routes, the trail to the bank town, the canyon ambush-spots. Anywhere there's money moving and not enough law to guard it.",
    keeper="Road Agents are your control group, and you should use them deliberately as one. Run a gang of them <em>before</em> the first real horror so the table internalizes the normal rules of a fight: cover matters, morale breaks, a downed leader routs the rest, bullets simply work. Then, when the dead get up and keep walking, the contrast lands like a slap &mdash; <em>oh, this isn't that kind of thing.</em> They're also useful mid-campaign as a palate cleanser, a reminder that ordinary human danger is still danger, and as a setup: a gang of Road Agents that's gone quiet, or that's fleeing something, points the party toward a worse problem behind them. Let them be beatable. That's their whole job &mdash; to make the unbeatable things feel as wrong as they should.")}

  {creature(
    sb("The Skin-Walker", "Tier III &middot; the thing that wears men", 17, 38, "fast in any shape", "+9", "+11", "+6",
       "claws +9 (2d6+4, two a round), or whatever the borrowed shape carries",
       "<strong>Another's skin.</strong> Wears the face and manner of any it has killed; one thing is always wrong &mdash; a shadow, a reflection, an animal's terror, the eyes by firelight.",
       "DC 16, 1d6 (when it sheds a face)",
       "It cannot abide its true reflection nor cross a line of ash and bone; a prayed-over or silver bullet wounds past the borrowed skin."),
    lore=[
      "It is old and it is hungry in a way that has nothing to do with food, and what it hungers for is to <em>be</em> &mdash; to wear a person, to slip into a life and a face and a name and live there a while before it grows bored or careless and moves on. The Skin-Walker takes the shape of any it has killed, down to the voice and the small habits, and it walks into the dead man's home and sits at the dead man's table and no one is the wiser. At first.",
      "But the borrowed skin is never quite right, and the wrongness leaks out at the edges. A shadow that falls the wrong way. A reflection that lags. The way the dogs and horses lose their minds when it comes near. The eyes catching the firelight like an animal's. The party that learns to watch for the one wrong detail is the party that survives it; the party that trusts a familiar face is the party that's already lost a member and doesn't know which one."],
    witness=("&ldquo;My brother came back from the hunt wearing my brother. Took me three days to be sure, and by then it had slept in his bed a week.&rdquo;", "as told to a mission doctor"),
    found="In the heart of a community, wearing someone's face &mdash; a homestead, a small town, a trail party, a fort. It hunts the isolated to take their shape, then walks back in among people as one of them.",
    keeper="The Skin-Walker is the book's great paranoia engine, and it works best when the players don't know they're in a Skin-Walker scenario yet. It's a social-horror puzzle: someone the party knows and trusts is already dead and replaced, and the game is figuring out <em>who</em> before it takes another. Seed the wrongness carefully &mdash; a reflection that's a beat slow, animals that panic, a beloved NPC who suddenly doesn't know a thing they should. Reward the player who catches the one wrong detail. The tells in the entry (true reflection, line of ash and bone, silver or blessed bullets) give the party tools to test the suspect and to strike past the borrowed skin. The horror is the trust it exploits &mdash; and the gut-punch is the moment they realize how long it's been wearing a friend. Use sparingly and devastatingly.")}

  {creature(
    sb("The Cursed Man", "Tier II &middot; the slow turning", "13 (rising)", 26, "normal, then fast", "+8", "+4", "+3",
       "as a man early; later claws +7 (1d8+4) and a strength that bends iron",
       "<strong>Turning.</strong> Run it as a clock, not a fight &mdash; a person the party may know, sickening into something else over hours; each stage stronger and less himself.",
       "DC 13 rising to 20 as he is lost",
       "Early, the curse can be drawn or prayed out; late, only a bullet &mdash; and the party must choose the moment."),
    lore=[
      "He was bitten, or cursed, or he touched a thing he should not have, and now something is growing in him that will not be stopped. The Cursed Man is a person &mdash; often one the party knows, sometimes one of their own &mdash; in the slow, terrible process of becoming something else. It happens over hours or days, not all at once: the fever, the strange appetites, the strength that surprises everyone including him, the moments of lucid horror as he feels himself slipping.",
      "There is a window, early, when the curse can still be drawn out &mdash; prayed away, cut free, broken at its root &mdash; and the man saved. The window closes. Past a certain point there is only the thing he's becoming, and the only kindness left is a bullet, and the party has to decide, with the clock running and a friend's eyes pleading, exactly when that moment has come."],
    found="Anywhere a curse can take root &mdash; after an encounter with another monster, a touched relic, a witch's spite. Most often it's a companion or a sympathetic NPC, which is the whole tragedy of it.",
    keeper="The Cursed Man is a clock and a moral knife, not a monster to be fought. Run it as a countdown with stages: each hour he's stronger, stranger, less himself, the DC rising as the person fades. The drama is entirely in the <em>choice</em> &mdash; there's an early window to save him (a cure, a prayer, a ritual the party must scramble to find or perform) and a late point where only a bullet remains, and the party has to decide when hope runs out. Make them <em>like</em> him first; make the turning visible and pitiable; let him have lucid moments where he begs them to do what's necessary, or begs them not to. This is one of the heaviest things you can put at a table, especially if the cursed man is a player character. Don't rush the clock. Let them feel every tick, and let the decision cost them.")}

  {creature(
    sb("Dark Cultist &amp; the Hollow Prophet", "Tier II (flock) / III (prophet)", "14 / 16", "18 / 42", "normal", "+4 / +5", "+4 / +6", "+6 / +11",
       "cultist knife +5 (1d6+2) or rifle +5 (1d10+1); prophet calls 1d4 Risen (3/night)",
       "<strong>The Word.</strong> Once a round the prophet's sermon forces a Will save (DC 16) or Frightened 2 and unwilling to harm him; the flock fights without fear of death.",
       "prophet DC 16, 1d6",
       "The flock breaks if the prophet falls; the prophet has bargained his death away &mdash; find and break the token that holds it.",
       mark="A soul that heeds the Word willingly, or takes the prophet's bargain, gains +1 Mark."),
    lore=[
      "Out where the churches are far apart and the nights are long, a charismatic man with the wrong book and the right voice can gather a congregation that should have known better. The Hollow Prophet was a person once &mdash; a preacher, a prospector, a stranger who came to town with a light in his eye. Then he gave himself over, and what fills him now speaks through him. His flock are ordinary folk: neighbors, farmers, a sheriff's own deputy, hollowed out one sermon at a time until they fear nothing, doubt nothing, and will die smiling for him.",
      "He has bargained his own death away and keeps it somewhere safe &mdash; a token, a buried thing, a heart kept in a box &mdash; so that bullets pass through him like he's already a ghost. His Word is a weapon: a sermon that turns a brave soul's own hands against itself, that makes the faithful unkillable in spirit if not in body. The flock breaks only when he falls, and he falls only when the thing that holds his death is found and broken."],
    found="An isolated congregation &mdash; a remote chapel, a mining camp, a town the railroad forgot. The flock looks normal at first; the wrongness is in what they all believe, and what they've all agreed not to see.",
    keeper="This dual entry is a whole scenario in a box: a cult, its leader, and the bargain that protects him. Run the flock as the immediate threat &mdash; fearless, numerous, armed with farm tools and old rifles &mdash; and the prophet as the puzzle behind them. His sermon (the Will-save Frightened effect) makes a frontal assault costly and can turn party members against each other or freeze them mid-fight. Killing his body does nothing; the win is finding the token that holds his bargained-away death. Build the investigation: where does he keep it, who knows, what will the flock do to protect it? The Mark warning matters &mdash; a player tempted by the Word, or by the prophet's own offer, courts corruption. Use the flock to show how ordinary people get hollowed out, and the prophet to show what's doing the hollowing. The best version makes the party realize, too late, how many 'normal' townsfolk were already his.")}

  {creature(
    sb("The Witch", "Tier II&ndash;III &middot; the Craft, born or bought", 16, 36, "normal", "+8", "+7", "+12",
       "hexing touch +8 (2d6+3 and a lingering curse); the Evil Eye (Will DC 16 or Enfeebled)",
       "<strong>Familiar-bound.</strong> Her power is doubled while her familiar lives, and she feels what it feels; harm the one to weaken the other.",
       "DC 16, 1d6",
       "Her true name spoken, her heart-charm found and broken, or her familiar killed; cold iron foils her workings.",
       mark="Bargaining with her, or working a hex at her teaching, is +1 Mark."),
    lore=[
      "She might have been born to it or come to it desperate; she might be the cackling crone of the stories or a respectable widow three farms over whom no one suspects. The Witch works the Craft &mdash; the hexing touch, the Evil Eye that withers a man's strength, the lingering curse that follows a victim home and ruins his luck, his health, his marriage, his crops. She is patient and she is subtle and she does not forget a slight.",
      "Her power runs through her familiar &mdash; the cat, the crow, the toad, the strange tame thing that's always near her &mdash; and while it lives, her strength is doubled and she feels what it feels. Kill the familiar and you halve the Witch. The old protections hold against her: cold iron foils her workings, her true name spoken aloud binds her, and somewhere she keeps a heart-charm that holds her life, which is the surest way to end her for good."],
    found="On the edge of a community &mdash; the last farm on the road, the cabin in the woods, a respectable house in town hiding a cellar. Wherever she can work unwatched and be near the people she means to curse or aid.",
    keeper="The Witch is a recurring antagonist more than a single fight, and she rewards being played long. She works through hexes and curses that land days before the party ever sees her &mdash; the homestead's bad luck, the wasting illness, the cursed rival &mdash; so she's often the answer to a mystery rather than a creature in a clearing. When it does come to confrontation, the structure is elegant: cold iron foils her, her true name binds her, her familiar doubles her (so killing it is the tactical key), and her heart-charm is the true kill-switch. Let the party assemble these through investigation. She's also a tempter &mdash; the Mark warning means a desperate party might bargain with her, and that's a story in itself. Play her as intelligent, proud, and long-memoried; she should feel like a person with reasons, not a cackling obstacle. The best Witch is one the party dealt with once and now has to deal with again, angrier.")}

  {creature(
    sb("The Hexer", "Tier II &middot; a man who pays for power", 15, 22, "normal", "+5", "+5", "+9",
       "borrowed curse +6 (1d8+3 and a small bane); throws ill-luck before him",
       "<strong>On credit.</strong> Everything he does, the dark does for him, and the bill comes in his own slow ruin; he is more dangerous cornered, having less left to lose.",
       "DC 13, 1d4",
       "Take or break his charms and bag of tricks and he is just a frightened, marked man; salt unworks his signs.",
       mark="Striking a bargain with what backs him is +1 Mark."),
    lore=[
      "The Hexer is what the Witch's power looks like in a smaller, sadder, more dangerous man. He has no Craft of his own &mdash; he buys it, all of it, on credit, from something that keeps a very exact account. Every curse he throws, every charm he works, the dark does for him, and the bill comes due in his own slow ruin: his health, his years, his soul, paid out a piece at a time until there's nothing left but a marked and frightened man with a bag of borrowed tricks.",
      "That ruin is what makes him dangerous. He knows what he's spending and where it ends, and a man with nothing left to lose and a line of credit to the dark will do desperate, ugly things. Take away his charms and his bag of tricks and the borrowed power goes with them, leaving just the wretch underneath."],
    found="Drifting through towns and camps, selling small curses and luck-charms, settling scores for cash. He's often a hireling &mdash; the cheap muscle a richer villain buys to do the supernatural dirty work.",
    keeper="The Hexer is a pathetic, dangerous middle-man, useful as a recurring low-tier antagonist and as a window into how ordinary greed and desperation feed the dark. He's weak when disarmed &mdash; his power is all in his charms and his bag of tricks, and salt unworks his signs &mdash; so the tactical answer is to strip him of his tools, after which he's just a frightened marked man. The drama is in his ruin: he's visibly paying for his power, rotting from the inside, and a perceptive party might pity him even as they stop him. Use him as a hired gun for a bigger villain, a cautionary tale about the cost of bargains, or a desperate man the party could possibly save if they're inclined to mercy. The Mark warning cuts both ways &mdash; he's a tempter too, offering quick curses for a price, and a party member who buys from him starts down his road.")}

  {creature(
    sb("The Hanging Judge", "Tier III &middot; the law that died and kept the bench", 17, 42, "normal", "+11", "+5", "+10",
       "the sentence, pronounced +9 (2d6+4 and Frightened 1); his gavel-crack stuns (Fort DC 16)",
       "<strong>Holds court.</strong> A dead lawman who still tries, sentences, and hangs all who enter his jurisdiction; within his town his word is iron law.",
       "DC 16, 1d6",
       "Win a true verdict against him &mdash; prove the wrong he died hiding &mdash; or break his gallows and burn his bench."),
    lore=[
      "He was the law in his town, judge and jury and gallows all in one, and he hanged a great many men &mdash; some guilty, some guilty only of being inconvenient, and at least one whose innocence he knew and buried along with the body. He died still on the bench, and death did not retire him. The Hanging Judge holds court still, in the ruin of his courthouse, and any soul who wanders into his jurisdiction is hauled before him, tried, sentenced, and hanged with the cold ceremony of a man who never once doubted himself.",
      "Within his town his word is iron law &mdash; his sentence carries a weight that makes the bravest soul quail, his gavel-crack stuns like a thunderclap. He cannot be argued with by ordinary means, because in his own mind he is simply doing his duty, as he always did. The wrong he died hiding is the crack in the bench: prove it, win a true verdict against him, and the false majesty of his court comes down."],
    found="The abandoned courthouse and gallows-square of a dead or dying town, the seat of his old jurisdiction. He's bound to his bench; leave the town and you leave him, but the town usually holds something the party needs.",
    keeper="The Hanging Judge is a courtroom drama with a noose, and the way to beat him is to play the trial, not the fight. His numbers make a straight brawl punishing, and morally he believes he's righteous, so you can't just shoot your way out of his jurisdiction. The keys are in the entry: win a true verdict against him (prove the wrong he died concealing &mdash; the innocent man he knowingly hanged) or destroy the instruments of his false court (break the gallows, burn the bench). Build the scenario as an investigation into his old cases: who did he hang wrongly, where's the evidence, what's the truth he's been holding court to avoid? Then stage a confrontation where the party turns his own ritual against him &mdash; puts <em>him</em> on trial. It's a set-piece for a party that likes to think, and a sharp comment on frontier justice. Let them win by being right, not just by being armed.")}

  {creature(
    sb("The Resurrectionist", "Tier II &middot; the grave-robber gone wrong", 14, 24, "normal", "+6", "+5", "+7",
       "bone-saw +6 (1d8+3); raises the freshly bought dead to shield him",
       "<strong>His ledger.</strong> He has sold and stitched too many corpses, and they answer when he calls; his book names every grave he's emptied.",
       "DC 13, 1d4",
       "Burn the ledger and his stitched servants fall; he himself bleeds like any man once his dead are down."),
    lore=[
      "He started honest enough, as these things go &mdash; a body-snatcher selling the freshly dead to the medical colleges back east, ugly work but a living. Somewhere along the way he learned that the dead he handled so casually could be made to sit up, and to serve, and the Resurrectionist crossed from grave-robber to something worse. Now he keeps a stable of stitched and reassembled corpses, and a ledger naming every grave he's emptied, and he raises his dead to shield him while he works.",
      "His ledger is the heart of him &mdash; a precise and damning account of every body he's stolen, sold, and bound &mdash; and it's also the binding that holds his stitched servants together. Burn the book and the dead fall to pieces, and the Resurrectionist is revealed for what he is under all his borrowed protection: a soft, frightened man with a bone-saw, who bleeds like anyone."],
    found="Near graveyards and the towns that feed them &mdash; a cellar workshop, an abandoned mortuary, a shack at the edge of the boneyard. Follow the disturbed graves and the missing dead.",
    keeper="The Resurrectionist is a grisly mystery with a clean mechanical hook: his ledger binds his servants, so burning the book ends the fight and strips him of his shield. Run the lead-up as an investigation &mdash; graves disturbed, the recent dead gone missing, a town uneasy about its boneyard &mdash; and let the party trace it to his workshop. The ledger is both clue and kill-switch: it names his crimes (useful for the law, and for understanding the scope) and it holds his stitched dead together. Make the players figure out that the book is the target, not the man. He's a coward at heart, dangerous only behind his wall of corpses, so once the dead are down he folds fast. Use him to explore the frontier's casual relationship with the dead, the ugliness of the body trade, and the line a desperate or greedy man crosses when he stops seeing corpses as people. A good mid-tier villain with a satisfying, decisive weakness.")}

  {creature(
    sb("The Wendigo-Touched", "Tier II &middot; the man who ate what he must not", 15, 24, "fast", "+8", "+6", "+4",
       "frostbitten claws +6 (1d8+3 cold); a hunger that grows with every kill",
       "<strong>Half-turned.</strong> A starving man who crossed the line and is becoming something colder; kill him soon or meet the Wendigo proper by spring.",
       "DC 13, 1d4",
       "Fire and iron; a bullet now is a mercy and a wisdom both, for what he is becoming.",
       mark="Sharing his meal, even unknowing, risks +1 Mark."),
    lore=[
      "The winters out here can starve a man down to a choice no man should ever face, and some men make the wrong one. The Wendigo-Touched ate what he must not &mdash; in a snowbound cabin, a stranded wagon, a played-out mining camp where the food ran out before the snow did &mdash; and the eating started something in him that won't stop. He is half-turned: still mostly a man, but cold now, fast, and gripped by a hunger that grows with every kill and points always in one direction.",
      "He is what the Wendigo proper grows from. Catch him now, in this half-state, and he can still be stopped with fire and iron &mdash; and a bullet is a mercy as much as a defense, because the thing he's becoming by spring is something this book has a much worse entry for. Let him go, let him feed, and you'll meet the finished article in the deep snow, and wish you'd ended it while it still had a human face."],
    found="The deep-winter country, the snowbound passes and isolated cabins, the camps cut off by storm. Look for the survivor of a starvation tragedy who came out of the snow changed, and hungry in a wrong way.",
    keeper="The Wendigo-Touched is the seed of the Wendigo (see The Wild &amp; the Weather), and running them as a connected pair across a campaign is deeply effective. He's a tragedy in progress &mdash; a man who made an unforgivable choice under unbearable pressure and is now turning into a monster because of it. The mechanical lesson is mercy-as-wisdom: ending him now is both easier and kinder than facing what he becomes. Play the horror of the half-state &mdash; the cold, the growing hunger, the man still partly aware of what he's doing. The Mark warning is a dark hook: a party that unknowingly shares his 'meal' (the starvation-camp food) risks the same corruption. Use him to explore the frontier's worst desperation, and as a ticking clock &mdash; deal with him before spring, or meet the Wendigo. Few creatures better capture this book's theme that the worst monsters were once just people the country pushed too far.")}

  {creature(
    sb("The Mesmerist", "Tier III &middot; the eyes that own you", 15, 30, "normal", "+6", "+7", "+11",
       "a word and a gesture (Will DC 16 or do as bid for a round); hidden blade +7 (1d6+3)",
       "<strong>The bend.</strong> He turns your own hands and friends against you, and watches from safety while you do his killing.",
       "DC 16, 1d6",
       "Break his line of sight, blind him, or close the distance before he speaks; freed thralls turn on him fast."),
    lore=[
      "He came to town with a traveling show, perhaps, or a patent-medicine wagon, or simply a fine coat and a way of looking at you that made you want to agree. The Mesmerist owns people with a word and a gesture &mdash; turns a man's own hands against his friends, walks a thrall off a roof with a smile, sits safe in the corner while the people he's bent do his killing for him. He rarely lifts a hand himself; he doesn't need to, when he can borrow yours.",
      "The bend takes hold through the eyes and the voice, so a man who can't see him or hear him can't be taken. Break his line of sight, blind him, get close before he speaks &mdash; and the thralls he was riding come back to themselves all at once, and remember what he made them do, and turn on him with a fury he can't talk his way out of."],
    found="Wherever there are crowds to work and marks to bend &mdash; a boomtown, a traveling show, a respectable parlor where he's the charming guest. He hides behind influence and other people's hands.",
    keeper="The Mesmerist makes the party's greatest strength &mdash; each other &mdash; into the threat, which is unsettling in exactly the right way. Mechanically he's a glass cannon who fights through other people: his thralls (which may include party members) do the dangerous work while he stays safe. The counters are clear and tactical: break his line of sight, blind him, or close and silence him before he can speak. Run the dread of watching a friend's eyes go flat and their gun come up. Be careful and generous with player agency &mdash; telegraph the save, let players fight the bend, and make the freed-thrall turnaround satisfying when his control breaks. He's a great social-infiltration villain who hides behind influence, and a fight that's won by disrupting him rather than out-damaging him. The lesson: against some enemies, the move is to take away their tool, not trade blows &mdash; and their tool might be your own people.")}

  {creature(
    sb("The Bruja", "Tier III &middot; the owl-witch of the night roads", 17, 40, "fly fast by night", "+9", "+10", "+11",
       "talon and curse +9 (2d6+4); takes the shape of a great owl to hunt",
       "<strong>Night-flight.</strong> She rides the dark as a giant owl and lands as a woman; she preys on travelers and the newborn, and knows when she is spoken of.",
       "DC 16, 1d6",
       "Salt, prayer, and the sign against the eye ground her; named in her true form, by daylight, she cannot fly &mdash; or flee.",
       mark="Seeking her favor is +1 Mark."),
    lore=[
      "She flies the night roads as a great owl, vast and silent, and lands as a woman where no one is watching. The Bruja is an old terror of the borderlands &mdash; a witch who preys on travelers caught out after dark and, worst of all, on the newborn, slipping into a house where a baby has just come and taking what she came for. She knows when she is spoken of, so the people who fear her speak of her carefully, and never by the open window.",
      "The wards against her are old and specific: salt, prayer, the sign made against the evil eye. They ground her, break her flight, pin her to her woman's shape. And there is a deeper truth &mdash; named in her true form, in daylight, she cannot take wing, cannot flee, cannot become the owl and vanish into the dark. Catch her as what she is, when the sun is up, and she's trapped on the ground with the rest of us."],
    found="The night roads and lonely trails of the borderlands, and the houses of the newly-born. She ranges far on the wing by dark and must return to her woman's life by day.",
    keeper="The Bruja blends folk-horror specificity with a satisfying mechanical structure. By night, on the wing, she's an elusive aerial predator &mdash; hard to pin, preying on the vulnerable. The wards (salt, prayer, the sign against the eye) are the locals' defense and the party's tools: they ground her, strip her flight, force her human shape. The deeper key is identity and daylight &mdash; learn who she really is, name her true form, catch her by day, and she can't escape into the owl. Build the scenario around her dual life: she's a woman in the community by day, the owl-terror by night, and unmasking her is the heart of it. The preying-on-newborns angle is genuinely dark; use it to give the threat real stakes and the community real fear. The Mark warning notes she can also be sought out as a power-broker, which makes her a tempter as well as a terror. Play her as cunning, old, and aware &mdash; she knows when she's hunted.")}

  {creature(
    sb("The Deathless Gun", "Tier III &middot; the man who can't be killed wrong", 18, 40, "normal", "+9", "+11", "+6",
       "two shots +10 (1d8+4); the drop adds +2 and a die",
       "<strong>The terms.</strong> A gunfighter who bargained away his death &mdash; he cannot be killed by ambush, poison, or numbers, only by being outdrawn fair and alone.",
       "DC 13, 1d4 (the wounds that close)",
       "Meet his terms: a fair draw, one on one, in the open. There is no other way, and he knows it, and he is fast."),
    lore=[
      "He was good with a gun &mdash; maybe the best in three territories &mdash; but good wasn't enough, or wasn't safe enough, and he made a bargain to be sure. The Deathless Gun cannot be killed wrong. Ambush him and the bullets find nothing vital. Poison him and he shrugs it off. Send ten men and watch the wounds close as fast as they open. The terms of his bargain are precise and cruel: he can only die one way, outdrawn in a fair fight, one on one, in the open, with no trick and no edge.",
      "He knows his terms better than anyone, and he's built a life on them. He'll provoke the fair fight he can't lose, walk into ambushes smiling, let a whole posse empty their guns into him just to watch their faces. The only way past him is the one way he's spent years getting good at &mdash; and he is very, very fast."],
    found="The streets and saloons of the gun-towns, anywhere reputation is currency and a fast draw settles accounts. He goes where the fighting is, because the fight is the only thing that can end him, and he's not afraid of it.",
    keeper="The Deathless Gun is the book's great showdown, and its whole point is that the party <em>can't cheat</em>. Every clever trick they've learned &mdash; ambush, numbers, poison, dynamite &mdash; fails against his terms, and you should let them try and fail once so the rule lands. The only path is the one he's mastered: a fair, open, one-on-one draw. This forces the dramatic question &mdash; <em>who</em> faces him, and are they fast enough? Build to it: let his reputation precede him, let the party watch him survive something that should have killed him, let the dread of the inevitable showdown build. Make the duel itself a real moment &mdash; the empty street, the held breath, the single exchange. It's a rare creature that turns the genre's central iconography (the quick-draw duel) into the only viable tactic. Reward the gunslinger character's whole build with this. And if they win, let it be earned, and close.")}

  {creature(
    sb("The Possessed", "Tier II &middot; a soul with a rider", "12 (host)", 22, "normal", "+5", "+6", "+9",
       "the host's hands, made strong +6 (1d8+3); speaks in a borrowed, wrong voice",
       "<strong>Two in one skin.</strong> An innocent person ridden by something else; every wound you deal, you deal to the host you may be trying to save.",
       "DC 16, 1d6",
       "Drive the rider out &mdash; a true exorcism, a holy ground, the thing's name &mdash; without killing the host. Kill the body and the rider only finds another."),
    lore=[
      "Something got inside &mdash; through a broken ward, a foolish invitation, a moment of weakness or grief &mdash; and now there are two things in one skin. The Possessed is an innocent person ridden by a rider that wears them like a coat: speaking in a borrowed, wrong voice, working the host's body to a strength it never had, doing harm with hands that, underneath, are still the hands of someone the party may be trying desperately to save.",
      "That's the cruelty of it. Every wound you deal the monster, you deal to the host. Kill the body and you've murdered an innocent and accomplished nothing &mdash; the rider simply steps out and finds another skin. The only true answer is to drive the rider out and leave the host alive: a real exorcism, holy ground, the thing's true name spoken to cast it loose."],
    found="Anywhere a door was left open &mdash; a house where a ward broke, a person who dabbled and lost, a survivor of another haunting. The host is usually someone with a connection to the party or the community, to make the stakes personal.",
    keeper="The Possessed is a fight you win by <em>not</em> fighting, and that inversion is its whole design. The host is innocent and every point of damage hurts them, so the party that treats it like a normal combat ends up killing the person they came to save and accomplishing nothing &mdash; the rider just relocates. The real work is the exorcism: discover the rider's nature and name, find holy ground or a true rite, and cast it out while keeping the host alive and restrained. Build it as a race against the rider's escalation and a puzzle of how to subdue without killing. The wrong voice, the borrowed strength, the flashes of the trapped host pleading &mdash; lean into all of it. It pairs beautifully with the Possession rules in the Keeper's Book. Use it when you want the party to feel the weight of a life in their hands that they cannot simply shoot their way out of protecting. The kill is easy. The <em>save</em> is the adventure.")}

  {creature(
    sb("The Bonepicker", "Tier I &middot; the man who eats the dead", 13, 14, "fast; scuttles", "+5", "+6", "+2",
       "filthy claws and teeth +4 (1d6+2 and Fort DC 13 or Sickened)",
       "<strong>Coward.</strong> A man turned ghoul by long famine and worse meals; bold among the dead and the sleeping, gutless against the armed and waking.",
       "DC 13, 1d4",
       "Light and a loud, advancing line send it fleeing; run it down before it reaches the dark, where it is strong."),
    lore=[
      "Hunger and worse meals turned him from a man into something that scuttles &mdash; a ghoul, a corpse-eater, a thing that haunts the boneyards and the battlefields and the fresh graves, feeding on the dead and, when it's bold enough, the sleeping. The Bonepicker is filthy, fast, and diseased, and its bite carries the sickness of everything it's eaten. But it is, above all, a coward.",
      "It is brave only among the helpless &mdash; the dead, the sick, the sleeping &mdash; and gutless against anything armed and awake and willing to come at it. Light terrifies it. A loud, advancing line sends it scuttling for the dark. The danger is letting it reach that dark, where it's at home and the odds turn; run it down in the open, in the light, and it dies as miserably as it lived."],
    found="Graveyards, battlefields, plague-pits, the edges of any place with fresh dead to feed on. It dens somewhere dark and close &mdash; a crypt, a mine, a cellar &mdash; and ventures out to feed by night.",
    keeper="The Bonepicker is a low-tier creature that teaches courage and aggression as tactics. It's a coward &mdash; bold only among the helpless, gutless against the armed and waking &mdash; so the counterintuitive lesson is that <em>advancing</em> beats defending. A party that holds light, keeps a loud advancing line, and refuses to let it reach the dark will rout it easily; a party that hangs back or gets separated in the shadows lets it work. Use it to bloody green characters, to populate a graveyard or battlefield scenario with low-grade dread, or as a scavenger pointing toward bigger death (where there are Bonepickers, there are a lot of fresh dead &mdash; why?). The bite-sickness adds a lingering cost to sloppiness. It's also a grim character study: a man reduced to this by famine, a reminder of how thin the line is out here between person and predator. Easy to kill, easy to underestimate, and a good way to make the dark between the gravestones feel dangerous.")}

  {creature(
    sb("The Flock of the Open Eye", "Tier II &middot; a town that looked too long", "13", "12 each", "normal", "+4", "+3", "+6",
       "farm tools and old guns +5 (1d8+2); presses in numbers, unafraid, smiling",
       "<strong>Of one mind.</strong> Ordinary folk hollowed and joined by a thing they carry and worship; they do not break, bargain, or stop.",
       "DC 16, 1d6 (the wrongness of the crowd)",
       "Take or destroy the idol at the heart of the flock and the people, those still people, fall down weeping.",
       mark="Looking upon the idol as they do is +1 Mark."),
    lore=[
      "A whole town looked at the wrong thing for too long, and now they are of one mind, and the mind is not theirs. The Flock of the Open Eye are ordinary folk &mdash; the storekeeper, the schoolmarm, the children &mdash; hollowed out and joined together by an idol they carry and worship, a thing that looked back when they looked at it. They press in close, unafraid, smiling, armed with whatever a town has to hand: farm tools, old guns, kitchen knives.",
      "They do not break. They do not bargain. They do not stop. You cannot reason with a crowd that shares one will and feels no fear, and the wrongness of all those familiar smiling faces moving together is its own kind of Dread. But they are still people, underneath, trapped in there &mdash; and the idol at the heart of the flock is the binding. Take it, break it, and the people who are still people fall down weeping, suddenly themselves, suddenly aware of what they've become."],
    found="An entire isolated settlement &mdash; a valley town, a mining camp, a religious commune &mdash; that found or was given the idol and looked too long. The whole place is the flock; outsiders who stay too long join it.",
    keeper="The Flock of the Open Eye is a town-sized horror and a moral hard place. The 'monster' is an entire community of innocent people, hollowed and bound, and they're still <em>people</em> underneath &mdash; so mowing them down is killing victims. The structure pushes the party toward the right answer: the idol is the binding, and destroying it frees everyone still salvageable. But getting to the idol means moving through a town that won't stop coming, without slaughtering the very people they're trying to save. Build the dread of the smiling, fearless crowd; the familiar faces; the children. Make the party feel the wrongness and the weight of restraint. The Mark warning is a real danger &mdash; a player who looks at the idol the way the flock does starts to join them. It's one of the book's strongest statements of its central theme: the horror here wears no fangs and no claws &mdash; it wears the faces of good ordinary people, turned into something that no longer breaks or bargains or stops. Solve the idol, save the town. Fail, and the flock just grows by however many the party brought.")}

  {creature(
    sb("The Tallyman", "Tier III &middot; he who collects the dark's debts", 16, 36, "normal; unhurried", "+9", "+7", "+12",
       "the reckoning +8 (2d6+4, ignores armor); he never misses one who owes",
       "<strong>Your name in his book.</strong> Once he has it, he cannot be refused, outrun, or barred; he comes at the appointed hour to collect what was promised the Old Dark.",
       "DC 16, 1d6",
       "Pay the debt, trick him into a worse one, or strike his name from the ledger he carries &mdash; the gun does nothing.",
       mark="Any dealing that puts your name in his book is +1 Mark or more."),
    lore=[
      "Every bargain with the dark has terms, and someone has to collect. The Tallyman is that someone &mdash; an unhurried, patient figure in a dark coat with a ledger under his arm, who comes at the appointed hour for the debt that was promised. He does not threaten and he does not hurry, because he does not need to. Once your name is in his book he cannot be refused, outrun, locked out, or shot; he simply arrives, at the time agreed, and collects.",
      "His reckoning ignores armor and never misses one who owes. The gun does nothing &mdash; you cannot kill a debt. The only ways past him are the ways of any creditor: pay what's owed, trick him into accepting a worse bargain, or get your name struck from the ledger he carries. And the surest way never to face him is the simplest: never put your name in his book at all, however good the deal sounds at the time."],
    found="He comes to wherever the debtor is, at the hour the bargain named. There's no lair to raid and no territory to leave &mdash; he is summoned by the debt itself, and he always knows where you are.",
    keeper="The Tallyman is consequence made flesh, and he's best used as the back half of a bargain a player or NPC made earlier. He cannot be fought &mdash; the gun does nothing, he can't be outrun or barred &mdash; so the whole drama is in the three real options: pay the debt (and what does that cost?), trick him into a worse bargain (a battle of wits and contracts), or strike the name from his ledger (steal or destroy the book, which he guards as his whole purpose). Build the dread of the appointed hour approaching with no way to simply fight free. He's the perfect enforcement mechanism for the book's bargain economy: when someone deals with the Witch, the Hexer, or the Old Dark itself, the Tallyman is who comes to collect, and knowing he's out there should make every tempting bargain feel heavier. The Mark warning underlines it &mdash; getting into his book is itself corruption. Use him to teach that on this frontier, the dark always keeps its accounts, and it always, eventually, sends someone to settle them.")}
</section>
"""

# ============================================================ V. SPIRITS & HAUNTINGS
SPIRITS = f"""<!-- V -->
<section class="page" id="spirits">
  {runhead('V. Spirits &amp; Hauntings')}
  <h1 class="chapter">V. Spirits &amp; Hauntings</h1>
  <p class="chapter-sub">The dead that left no body, and the places that keep them.</p>
  <div class="divider"></div>
  {quote("A house remembers what was done in it, same as a man. Only a house can't ever leave, and can't ever forgive.", "J. Halloran")}
  <div class="narr">You may have noticed that somewhere in the last hundred entries, the remedies stopped
  mentioning the rifle. That was not an oversight. From this chapter forward the catalogue concerns what
  is left when the body is subtracted &mdash; the grief, the grudge, the place itself gone wrong &mdash;
  and the tools that answer it are older and cost more. A reader who has come this far in a single
  sitting is advised to look up from the page a moment, and confirm the hour, and the room.</div>
  <p class="dropcap lead">You cannot always shoot a haunting. These are answered with salt and truth and the right words
  said over the right ground &mdash; and they punish a party that reaches for the gun first.</p>
  <p class="note"> <strong>Signs of the kind:</strong> a cold with no draft to carry it, a sound with no mouth to make it, a latch that will not hold, and one room always colder than the next.</p>

  {creature(
    sb("The Cold Spot", "Tier I &middot; a small unrest", "&mdash;", 10, "fixed", "+6", "&mdash;", "+4",
       "a chill, a whisper, a hand on the neck (Will DC 12 or Shaken); cannot truly harm &mdash; yet",
       "<strong>Bound to a spot.</strong> A minor dead clinging to where it fell; mostly an omen and a warning of worse, but it festers if ignored.",
       "DC 10, 1",
       "Find and bury the bones, say the name, or cleanse the ground; small mercies lay it."),
    lore=[
      "It is the smallest of the hauntings and the easiest to dismiss &mdash; one room always colder than the rest, a whisper at the edge of hearing, the brush of a hand on the back of the neck when no one's there. The Cold Spot is a minor dead, a soul clinging to the patch of ground where it fell, too weak to do real harm and too unquiet to rest. Mostly it's an omen, a small wrongness, a warning that something happened here that was never set right.",
      "But it festers if it's ignored. Left to itself, fed by fear and neglect, a Cold Spot can deepen into something with hands and hunger. It is, more than anything, an invitation: the country offering the party an easy mercy, and a hint of the larger wrong it points toward."],
    found="A particular spot &mdash; a corner of a room, a bend in the road, a single grave in a field &mdash; where someone died small and was forgotten. It doesn't move; it waits to be noticed.",
    keeper="The Cold Spot is your gentlest haunting and your best teaching tool for the chapter's central rule: <em>you don't shoot a ghost, you answer it</em>. It can't really hurt the party (yet), so it's a safe place to let them learn that salt, names, burial, and truth are the tools here, not lead. Use it as an omen and a breadcrumb &mdash; a small unrest that points to a buried wrong, a hint of a larger haunting nearby, a test of whether the party will take the trouble to do the small kind thing. Reward them when they do: a few minutes of investigation and a proper burial lays it, and maybe earns them a clue or a grateful local. And seed the warning &mdash; mention that a Cold Spot ignored can grow into something worse, so the party that brushes it off may find it waiting, stronger, later. It's the haunting equivalent of the Risen: small, simple, and setting up everything that comes after.")}

  {creature(
    sb("The Throwing Spirit", "Tier II &middot; the poltergeist", "&mdash;", 24, "fixed to a place or person", "+8", "+6", "+8",
       "hurled iron and stone +6 (1d8+3, anywhere in the room); slams doors and souls",
       "<strong>Cannot be struck.</strong> No body to shoot; it is grief or rage with hands, tied to a living person or an unquiet room.",
       "DC 13, 1d4",
       "It quiets only when its grief is named and answered &mdash; the wrong righted, the truth spoken, the person it haunts set free."),
    lore=[
      "It throws things. That's the first sign and the lasting impression &mdash; iron and stone and crockery hurled across a room by no hand, doors slammed hard enough to crack the frame, a sleeping soul dragged from bed by the ankles. The Throwing Spirit is grief or rage that has found hands without a body, and it is tied either to a place where something terrible was held in, or to a living person &mdash; often a child, often someone in the grip of an emotion too big to hold.",
      "You cannot shoot it. There's nothing to shoot. A party that empties their guns into a room full of flying crockery has accomplished nothing but noise. The poltergeist quiets only when the grief beneath it is named and answered: the wrong righted, the truth finally spoken, the haunted person freed of whatever they're carrying that the spirit feeds on."],
    found="A house with a history, or a person with a wound &mdash; an unquiet room where something was suppressed, or near a living soul (often young) in the grip of unbearable grief, rage, or fear.",
    keeper="The Throwing Spirit teaches the chapter's lesson with more force than the Cold Spot: it's actively dangerous, it cannot be struck, and the only way to stop it is to solve the grief. Run the chaos &mdash; objects flying, doors slamming, the genuine danger of hurled iron &mdash; and let the party's first instinct (shoot it) fail completely so the rule lands. The investigation is the real work: is it tied to the place or to a person? What's the grief, the wrong, the unspoken truth? Often the most affecting version anchors it to a living person, frequently a child or a grieving soul, whose pain is doing the throwing without their knowing &mdash; which makes 'solving' it an act of compassion, not exorcism. Pair it with a family drama, a buried secret, a person who needs to be heard. The party wins by understanding, not by force, and the best resolutions feel like healing a wound rather than killing a monster.")}

  {creature(
    sb("The Crossroads Man", "Tier IV &middot; the bargain in the dark", 19, 64, "as he pleases", "+13", "+13", "+16",
       "no need of hands &mdash; he deals; but crossed, the road itself turns on you (2d8+6)",
       "<strong>The deal.</strong> He waits where roads cross at midnight and offers exactly what you want for exactly what you cannot spare; refusing is safe, dealing is not.",
       "DC 20, 1d10",
       "You do not beat him with force. Refuse the deal, or bind him to terms he did not foresee &mdash; and never speak your true name.",
       mark="Any bargain struck is +1 Mark at the very least, and the start of a long road down."),
    lore=[
      "Come to a crossroads at midnight with a need too big to fill honestly, and he'll be there &mdash; though you came alone, and the road was empty a moment ago. The Crossroads Man is patient, courteous, and terribly accommodating. He offers exactly what you want most: the fast gun, the cure for the dying child, the gold, the love, the second chance. The price is always something you think you can spare, and it never is.",
      "He has no need of hands and rarely shows force, because he doesn't have to &mdash; refusing him is perfectly safe, and dealing with him is the only danger. But cross him, break a bargain, or try to cheat the terms, and the road itself turns on you. The only ways past him are to walk away from the deal, or to be cleverer than he is and bind him to terms he didn't see coming. And whatever you do, you never, ever tell him your true name."],
    found="Where roads cross, at midnight, when someone's need is great enough to call him. He doesn't haunt a place so much as appear at the intersection of desperation and opportunity. The crossroads is always empty until it isn't.",
    keeper="The Crossroads Man is a temptation, not a fight, and the entire encounter is built so that <em>force is the wrong tool</em>. His combat numbers exist only to punish the party that tries to cheat or attack him; the real interaction is the negotiation. He offers each character exactly what they most want, for a price that sounds bearable and isn't, and the drama is whether they walk away. The Mark warning is the heart of it &mdash; any deal is corruption, and the start of a long road down &mdash; so he's a recurring tempter who tests the party's souls more than their guns. The clever-victory path (bind him to terms he didn't foresee, out-lawyer the dealmaker) rewards player ingenuity and makes for a memorable wits-battle. Use him at moments of genuine desperation, when the party <em>needs</em> something badly enough that his offer is real temptation. The best Crossroads Man scenes end with the party walking away from something they wanted very much &mdash; or with one of them taking the deal, and a whole campaign growing out of what it costs.")}

  {creature(
    sb("The Shadow That Lags", "Tier II &middot; a shadow come loose", 14, 20, "fast; flat to any surface", "+6", "+8", "+7",
       "a cold grip from the floor +6 (1d8+3 and Enfeebled); mimics your own movements a beat late",
       "<strong>Yours, or someone's.</strong> A shadow parted from its owner, hunting to rejoin or replace; it strengthens in the dark and cringes from bright, sourceless light.",
       "DC 13, 1d4",
       "Pin it with crossed lights so it casts no edge, then reunite it with its owner or banish it with flame."),
    lore=[
      "A shadow can come loose. Through a curse, a near-death, a bargain, a moment where a soul and its shadow were pulled apart and didn't quite go back together &mdash; and then the shadow has its own ideas. The Shadow That Lags moves flat along the floor and walls, fast and silent, mimicking its owner's movements a beat too late, and it wants one of two things: to rejoin the person it fell from, or to replace them.",
      "It strengthens in the dark and cowers from bright, sourceless light. The trick to pinning it is light from several sides at once, so that it can cast no edge and has nowhere to lie flat &mdash; and then it can be reunited with its owner (if the owner still lives and wants it back) or banished with flame. A person whose shadow is loose and hunting them is in slow, terrible danger, because what the shadow replaces, no one notices is gone."],
    found="Attached, at a distance, to the person it came loose from &mdash; following them through their days a beat behind, growing bolder in the dark. The owner may not even know their shadow has its own intentions yet.",
    keeper="The Shadow That Lags is an eerie, intimate haunting that turns light and dark into the mechanical battlefield. It's strong in shadow and helpless in sourceless, multi-directional light &mdash; so the tactical puzzle is to pin it with crossed lights until it can't cast an edge, then resolve it (reunite or banish). Run the creep of it: the shadow that moves wrong, the owner who feels watched by their own outline, the dread of a thing that wants to <em>replace</em> someone. The replacement angle is the real horror &mdash; if it succeeds, who's to say the person you're talking to is still casting their own shadow? Use it for an unsettling personal haunting, ideally targeting an NPC the party cares about or even a player character. The light-based solution rewards clever staging (lanterns at angles, a ring of fire, mirrors throwing light) over brute force, keeping it true to the chapter's ethos that hauntings are solved by understanding their rules, not by shooting them.")}

  {creature(
    sb("The House That Hungers", "Tier IV &middot; a place gone carnivorous", 18, 75, "fixed (it is the building)", "+15", "+6", "+13",
       "doors, stairs, and walls +13 (2d8+6); rearranges itself to trap and separate",
       "<strong>It is the haunting.</strong> Not a ghost in a house but a house that is a ghost; it lures, divides, and digests those who shelter in it.",
       "DC 20, 1d10",
       "Find the wrong at its foundation &mdash; the body in the wall, the deed in blood &mdash; and burn or cleanse it; until then the house cannot be fought, only survived and fled."),
    lore=[
      "Some houses are haunted. This one <em>is</em> the haunting. The House That Hungers has no ghost rattling around in its empty rooms &mdash; the building itself has gone carnivorous, a place that lures travelers in out of the storm with warm windows and open doors and then closes around them. The doors lead where they didn't before. The stairs go down when they should go up. Hallways stretch, rooms multiply, and the party that sheltered here finds itself separated, lost, and slowly digested by a thing the size of a house.",
      "You cannot fight a building with a gun. The walls take the bullets and the house barely notices. It can only be survived, fled, or unmade &mdash; and unmaking it means finding the wrong at its foundation, the thing that made it hungry: the body bricked up in the wall, the deed signed in blood, the murder in the cellar. Burn or cleanse that, and the house is just a house again, or just ash."],
    found="On a lonely road, offering shelter from the storm or the dark &mdash; a fine old house where there shouldn't be one, lights warm in the windows, the door unlatched. It looks like exactly what a cold, tired party wants to find.",
    keeper="The House That Hungers is a whole dungeon that's also the monster, and the design is built around denying the party a target to shoot. The building rearranges to separate and trap them, so run it as a survival-horror crawl: split the party, disorient them, make the architecture itself the threat &mdash; doors that vanish, stairs that betray, rooms that weren't there. The lesson lands hard: there's nothing to fight, only a puzzle to solve and a maze to survive. The win condition is finding the foundational wrong (the body in the wall, the bloody deed, the buried murder) and destroying it &mdash; which means exploring the very thing trying to digest them. Build the house's history into its rooms so investigation and survival are the same act. The classic haunted-house scenario, weaponized: the players don't clear the house, they <em>diagnose</em> it, all while it tries to eat them. Pair it with a storm outside so leaving isn't easy, and let the warm inviting windows at the start make the trap that much crueler.")}

  {creature(
    sb("The Dollmaker's Children", "Tier II &middot; small things that move when unseen", 13, 8, "fast when unwatched", "+4", "+8", "+6",
       "needles and little knives +6 (1d6+3, in a swarm); only move when no one looks",
       "<strong>Stillness is a lie.</strong> Painted dolls housing small, spiteful spirits; they freeze under a watching eye and rush the moment it blinks.",
       "DC 13, 1d4",
       "Fire ends them; keep eyes on them till the flames take hold, and do not, ever, count them wrong."),
    lore=[
      "Someone made dolls, and made them too well, and put something into them &mdash; grief, spite, the small souls of children who died. The dolls woke. The Dollmaker's Children are painted, jointed, doll-sized things that move only when no one is watching. Under a steady eye they are perfectly, innocently still. The instant that eye blinks or turns away, they rush &mdash; needles and little knives, a swarm of small spiteful hands &mdash; and freeze again before anyone can be sure they moved at all.",
      "The whole horror of them is the watching. You cannot look at all of them at once. You cannot blink in unison. And you must never, ever count them wrong, because if there are more of them than you thought, one is already behind you, and it has all the time it needs the moment you look away."],
    found="A nursery, a toy-shop, the workshop or home of the dollmaker who made them. They cluster where children were &mdash; or where children were lost &mdash; and they spread, doll by doll, through the houses of a town.",
    keeper="The Dollmaker's Children turn <em>attention</em> into a resource the party has to manage, which makes for uniquely tense play. They only move when unobserved, so the table is forced to think about who's watching what, who's turning their back, what happens when the lantern swings away. Run the dread of glimpsed movement, the doll that's closer than it was, the miscount. Mechanically they're fragile and fire ends them &mdash; but the catch is you have to keep eyes on them until the flames actually take, and they're a swarm, so you can't watch them all. Stage it in a confined, doll-filled space (a nursery, a workshop) where there are always more than the party can cover. The 'never count them wrong' line is a perfect way to plant dread &mdash; have the count come out different twice. It's a set-piece for a tense, claustrophobic scene, and a creature that punishes panic and rewards discipline, teamwork, and a cool head. Pair with the tragedy of <em>why</em> the dolls woke for emotional weight.")}

  {creature(
    sb("The Mirror-Dweller", "Tier III &middot; the thing in the glass", 16, 36, "through any reflection", "+9", "+9", "+11",
       "a reaching arm +9 (2d6+4 and drags toward the glass); wears your face back at you",
       "<strong>Behind the silver.</strong> It lives in mirrors and still water and reaches through to pull souls in; what it pulls in, it replaces.",
       "DC 16, 1d6",
       "Break or cover every glass; it cannot cross into a room with no reflection to hold it. Shatter the mirror it calls home."),
    lore=[
      "It lives behind the silver, in the world that mirrors show and still water holds, and it has been watching you through every reflective surface you've ever passed. The Mirror-Dweller reaches through the glass &mdash; a cold arm out of a mirror, a hand from the surface of a well &mdash; to seize a soul and drag it through to the other side. And what it pulls in, it replaces: it climbs out wearing your face, your reflection made flesh, and walks away into your life while you scream from behind the silver where no one can hear.",
      "It can only act where there's a reflection to hold it. A room with every mirror broken or covered, every basin emptied, every window dark, is a room it cannot enter. Somewhere there's the mirror it calls home, the one it came through first &mdash; shatter that, and you cut it off from this side for good."],
    found="Anywhere there are mirrors and still water &mdash; a house full of looking-glasses, a town's barber-shop and parlors, a still pond. It has a home mirror it favors and spreads its reach through every reflection nearby.",
    keeper="The Mirror-Dweller makes every reflective surface a door, which makes every glass in the house a thing to watch. The party learns to fear mirrors, dark windows, still water, the polished surface of a gun &mdash; anywhere it can reach through or wear a stolen face back at them. The defensive rule is concrete and tactical: break or cover every reflection and it can't enter; a reflection-free room is a safe room. The win is finding and shattering its home mirror. The replacement horror gives it teeth beyond combat &mdash; if it takes someone, an impostor wearing their face is now loose, which can fuel a whole paranoid scenario (which of us is real?). Run the dread of the reflection that moves wrong, the face in the glass that smiles when you don't. It rewards a party that thinks about their environment and covers their mirrors, and punishes the one that walks past a looking-glass without a second thought. A gothic, claustrophobic favorite, and a great pairing with the Skin-Walker for a campaign about impostors and stolen identities.")}

  {creature(
    sb("The Hangman's Echo", "Tier II &middot; a death that replays", "&mdash;", 22, "fixed to the gallows-ground", "+7", "+6", "+9",
       "draws the living into the noose's place (Will DC 15 or act out the hanging); the rope finds throats",
       "<strong>A loop.</strong> The same hanging, over and over, that will use any neck to fill the part &mdash; guilty or not.",
       "DC 16, 1d6",
       "Break the loop: right the false verdict, cut and burn the gallows-beam, or bury the wronged man's bones with honor."),
    lore=[
      "A hanging happened here that should not have, and the ground has been replaying it ever since. The Hangman's Echo is not quite a ghost &mdash; it's a loop, a death stuck repeating itself, the same execution acted out over and over on the gallows-ground. And the loop is always short a player. It reaches for the living to fill the empty part, drawing a soul into the condemned man's place to act out the hanging again, and the rope does not care whether the neck it finds is guilty or innocent.",
      "Stand too long on that ground and you may find yourself climbing the steps you didn't mean to climb, putting your own head through the noose, while your friends watch you move like a puppet. The loop breaks only when the original wrong is answered: the false verdict righted, the gallows-beam cut and burned, the wronged man's bones given honest burial at last."],
    found="The old gallows-ground &mdash; a hanging-tree, a courthouse square, a prison yard &mdash; where an unjust execution was carried out. The structure or the spot replays the death; the bones of the wronged are usually nearby.",
    keeper="The Hangman's Echo is a haunting-as-recording, and the danger is that it conscripts the living into its replay. The Will-save mechanic &mdash; a character drawn to act out the hanging, climbing toward the noose against their will &mdash; is genuinely chilling and forces the party to save each other from a death that's trying to use them as a prop. Run the loop's eeriness: the spectral crowd, the repeated sentence, the rope that finds throats. It can't be fought (no body, just a recording with a grip), so the win is breaking the loop by answering the original injustice: right the false verdict (investigation), destroy the gallows-beam (action), or bury the wronged bones with honor (mercy). Build the historical wrong into the scenario so the party has to uncover what really happened on this ground. It pairs naturally with the Hanging Judge (the law that did the wrong) and the Gallows-Hung (the man who came back angry) for a whole campaign about frontier injustice and the dead it leaves. A strong, thematic haunting that turns the party's own bodies into the stakes.")}

  {creature(
    sb("The Whistler", "Tier III &middot; the tune that takes you off the trail", "&mdash;", 36, "unseen; fast", "+9", "+9", "+11",
       "its whistle (Will DC 16 or follow it into bog, cliff, or worse); strikes only the lost and alone",
       "<strong>Do not answer.</strong> A near and a far whistle both mean death; the closer it sounds, the farther it is, and to whistle back is to be marked.",
       "DC 16, 1d6",
       "Stop your ears, hold to the rope and the group, and never answer; salt and a steady fire keep it off till dawn."),
    lore=[
      "You hear it first as a tune on the night wind, a whistle from somewhere out in the dark, almost familiar, almost beckoning. The Whistler is never seen &mdash; only heard &mdash; and its tune is a lure that walks the lost and the lonely off the safe trail and into the bog, off the cliff, into the deep water, into whatever waits in the dark it leads you to. The old hands know the rule: the closer it sounds, the farther away it truly is, and the farther it sounds, the closer it has crept.",
      "And you never, ever whistle back. To answer it is to be marked, to tell it your exact location and your willingness to play its game. The travelers who survive a Whistler are the ones who stop their ears, hold tight to the rope and to each other, keep the fire built up, and wait out the dark without ever once answering that tune from the night."],
    found="The lonely night trails, the moors and bogs and mountain passes, the dark stretches between safe places. It works the isolated traveler and the party that's split up; it cannot take the group that stays together.",
    keeper="The Whistler is an auditory haunting that preys on isolation and curiosity, and it runs almost entirely on dread and discipline. It targets only the lost and alone, so the meta-lesson is <em>stay together, stay on the trail, don't wander</em> &mdash; and the moment the party splits up or someone strays toward the sound, it has them. Run the sound design: the tune on the wind, the wrongness of near-sounding-far, the temptation to follow or to answer. The Will save is the hook &mdash; a character compelled to walk off toward the whistle, into the bog or off the cliff, while the others try to hold them back. The defenses are folk-discipline: stop your ears, hold the rope and the group, build the fire, never answer. Use it to make a night journey genuinely tense, to punish a party that fragments, and to reward one that keeps its head and its formation. The 'never whistle back' rule is a perfect bit of folklore to establish early and then test &mdash; let a player be tempted to answer, and let the table feel the dread when someone does.")}

  {creature(
    sb("The Lantern-Light", "Tier I &middot; the false light over the marsh", "&mdash;", 10, "drifts", "+5", "+9", "+6",
       "no attack of its own &mdash; it leads you to the drowning-pool, the cliff, the quicksand",
       "<strong>The lure.</strong> A friendly light just ahead in the dark that is never reached and never meant to be; only the trusting and the desperate follow.",
       "DC 10, 1",
       "Simply do not follow. Trust your rope, your fire, and the trail you know; it cannot harm what will not chase it."),
    lore=[
      "Lost in the dark, cold and afraid, you see it &mdash; a light, a lantern, a warm window just ahead, surely a homestead or a fellow traveler. You go toward it. It stays just ahead, never quite reached, drawing you off the trail and into the marsh, toward the drowning-pool, the quicksand, the cliff-edge waiting in the dark. The Lantern-Light is a lure and nothing more, a false hope with no body and no bite, that does its killing entirely by leading.",
      "It cannot hurt you. It has no claws and no grip. All it can do is shine, just ahead, and promise. Only the trusting and the desperate follow a light that never gets closer, and the cure is as simple as it is hard in the cold and dark: don't follow. Trust the rope, the fire, the trail you know. A light that recedes is not a light to chase."],
    found="Over marshes, bogs, moors, and the bad ground near cliffs and quicksand &mdash; anywhere there's a lethal hazard for it to lead the lost toward. It appears to travelers caught out in the dark, cold, and frightened.",
    keeper="The Lantern-Light is the gentlest hazard in the chapter and a pure test of discipline over instinct. It can't attack &mdash; its entire threat is the temptation to follow, and it leads only those willing to be led toward the real killer (the bog, the cliff, the quicksand). The 'fight' is psychological: the party is cold, lost, frightened, and here's hope, just ahead. Do they chase it? Run the pull of it &mdash; especially after the party's had a hard night and wants nothing more than to find shelter. The counter is simply refusing to follow, trusting known safe-conduct (the rope, the fire, the trail) over the seductive false light. It pairs naturally with the Whistler (another lure that preys on the lost) and works beautifully as a complication during a night journey or an escape. Use it to teach the party to distrust easy salvation in the dark, and to make a simple act &mdash; staying put, holding the line &mdash; into the heroic choice. A small creature with a sharp moral: out here, the warmest-looking light is often the one that wants you dead.")}

  {creature(
    sb("The Weeping Walls", "Tier II &middot; the house that bleeds", "&mdash;", 26, "fixed", "+8", "+4", "+9",
       "the room turns on you &mdash; binding, smothering, weeping blood from the plaster (2d6+3)",
       "<strong>A murder kept.</strong> A killing was done here and never answered; the house has held it ever since and shows it to all who enter.",
       "DC 13, 1d4",
       "Find the body in the wall or the well, give it burial and the truth aloud, and the weeping stops."),
    lore=[
      "A murder was done in this house and never answered &mdash; the killer never caught, the body never found, the truth never spoken &mdash; and the house has been holding it ever since. The Weeping Walls show the crime to everyone who enters: blood seeps from the plaster, the rooms turn cold and close, the air thickens until it smothers, and the house itself binds and crushes those who try to leave before they understand what it needs them to know.",
      "It is not malicious so much as insistent. It has a truth it cannot let go of, a body it cannot bury, a wrong it cannot stop reliving. The blood on the walls is the house pointing, over and over, at what was done here. Find the body &mdash; in the wall, down the well, under the floor &mdash; give it proper burial, speak the truth of the killing aloud, and the house finally, gratefully, stops weeping."],
    found="A house, room, or building where a murder was committed and concealed &mdash; the body still hidden on the premises, the crime unsolved and unspoken. The blood and cold mark the spot the house wants found.",
    keeper="The Weeping Walls is a murder mystery the building itself is begging the party to solve. The haunting's manifestations &mdash; bleeding plaster, smothering air, rooms that bind and crush &mdash; are both the danger and the clue: the house is showing the party the crime and pointing at the hidden body. It can't be fought (it's the building), only answered, and the answer is investigation plus mercy: find the concealed corpse, bury it properly, speak the truth of what was done. Run it as a haunted-house whodunit where the environment is evidence &mdash; the blood flows heaviest where the body lies, the cold deepens near the truth. The party progresses by reading the house's grief, not by surviving waves of combat. It pairs with the Cold Spot (small unanswered death) and the House That Hungers (a place gone fully wrong) on a spectrum of how badly a building can be marked by what happened in it. A satisfying, investigation-forward haunting where solving the cold case <em>is</em> the exorcism, and the house's relief when the truth is finally spoken is its own reward.")}

  {creature(
    sb("The Mourner", "Tier II &middot; the wail before a death", "&mdash;", 20, "drifts; unbidden", "+7", "+6", "+10",
       "no attack &mdash; her keening names the one marked to die (Will DC 14 or Frightened 2)",
       "<strong>An omen, not a foe.</strong> She does not kill; she announces. To hear her wail your name is to have little time to set things right.",
       "DC 13, 1d4",
       "She cannot be fought or fled, only heeded; the death she calls can sometimes be cheated by those who move at once."),
    lore=[
      "She comes before a death, not after, and she comes to mourn it in advance. The Mourner is a keening, drifting figure &mdash; a woman in grey, a veiled shape, a wail on the wind &mdash; who appears unbidden to announce that someone is marked to die. She does not kill. She has never killed. She is the country's grief arriving early, naming the one whose time has come, and to hear her wail your own name is to know you have very little time left to set your affairs in order.",
      "You cannot fight her, because she is not the threat &mdash; she is the warning. You cannot flee her, because she has already found you. All you can do is heed her, and act. The deaths she calls are not always certain; the swift, the brave, and the lucky have sometimes cheated the reckoning she announces, but only by moving at once, and only by understanding that her wail is not a curse but a final, sorrowful kindness."],
    found="She appears wherever death is coming, to whoever is marked &mdash; a homestead before a tragedy, a trail before an ambush, a sickroom before the end. She is drawn by approaching death, not bound to a place.",
    keeper="The Mourner is an omen to interpret and race against rather than a monster to defeat, and she's one of the most useful tools in the chapter. When she appears and names someone, you've handed the party a ticking clock and a mystery: <em>who's about to die, how, and can it be stopped?</em> She can't be fought or fled, so the entire scenario becomes about heeding the warning &mdash; identifying the coming death and acting to cheat it. Sometimes it can be averted (the ambush avoided, the illness cured, the accident prevented); sometimes it can't, and the party has to sit with that. Use her to open a scenario with dread and urgency, to foreshadow a threat, or to give a doomed NPC weight. The Frightened effect is minor; her real power is narrative. Be fair with the cheating-death option &mdash; reward a party that moves fast and cleverly &mdash; but don't make her warnings empty. She works best as a recurring harbinger whose appearance makes the whole table go quiet, because they've learned what it means. The country's grief, arriving early, asking only to be heard.")}
</section>
"""

# ============================================================ VI. THE WILD & THE WEATHER
WILD = f"""<!-- VI -->
<section class="page" id="wild">
  {runhead('VI. The Wild &amp; the Weather')}
  <h1 class="chapter">VI. The Wild &amp; the Weather</h1>
  <p class="chapter-sub">The country itself, when it takes a shape and a hunger.</p>
  <div class="divider"></div>
  {quote("The country is the oldest monster, and the patientest. The weather is only its temper showing.", "N. Ashby")}
  <p class="dropcap lead">Some horrors have no body to bury because they are the land, the cold, the fire, the hunger of
  empty places. You do not kill these so much as outlast them, turn them, or give them what they came for.</p>
  <p class="note"> <strong>Signs of the kind:</strong> weather that comes too fast or will not move on, a heat or a cold the season does not own, water that recedes as you near it, and a stillness with no birds in it.</p>

  {creature(
    sb("The Wendigo", "Tier IV &middot; the deep winter given a body", 20, 72, "very fast; the storm moves with it", "+15", "+13", "+9",
       "antler and claw +13 (2d8+6, two a round); a crit carries a soul off into the white",
       "<strong>Killing cold &amp; the call.</strong> A blizzard rides with it; any who have eaten the dead or starved past reason hear it call by name (Will DC 18 nightly or walk to it).",
       "DC 20, 1d10",
       "Cold cannot touch it &mdash; only fire, and the nerve to use it close. Cut out its frozen heart and burn it to ash.",
       mark="Answering the hunger willingly is +1 Mark and the Wendigo's notice forever."),
    lore=[
      "It is the hunger of the deep winter given a body, and the body is wrong &mdash; gaunt past starvation, antlered, frost-rimed, taller than a man and faster than a horse, with a hunger that the eating of whole homesteads will not fill. The Wendigo is what the starved and the cannibal become when the cold and the appetite finish their work, and a blizzard rides with it wherever it goes, so that the storm and the monster arrive together and no one can tell where one ends.",
      "Worst of all is the call. Any soul who has eaten the dead, or starved past the edge of reason, hears the Wendigo speak their name on the wind, night after night, calling them out into the white to join it. The cold cannot harm it &mdash; it <em>is</em> the cold &mdash; and only fire touches it, and only the burning of its frozen heart ends it. Until then it walks, and calls, and feeds, and the winter walks with it."],
    witness=("&ldquo;It called my name in my mother&rsquo;s voice, from past the firelight, all the second night. On the third night I wanted to answer. That&rsquo;s when I ran.&rdquo;", "a pass survivor, found half-frozen"),
    found="The deep-winter country &mdash; the snowbound mountains, the frozen north, the high passes &mdash; especially where starvation or cannibalism has happened. The blizzard that rides with it can bring its season anywhere.",
    keeper="The Wendigo is the apex of this book's cold-and-hunger horror and the payoff of the Wendigo-Touched and the Hunger That Walks &mdash; run all three across a campaign and let the dread compound. Its numbers are brutal and the cold is unbeatable, so the fight is about fire and the frozen heart: cold cannot touch it, only flame, and the kill is to cut out and burn its heart of ice. The call is its signature terror &mdash; any party member who's eaten the dead or starved past reason (and the frontier creates such people) hears it nightly, and must save or walk out into the storm. This turns survival itself into the threat and can turn a party member into a liability or a casualty. Run the blizzard as part of the monster &mdash; the storm is its body and its cover. The Mark warning makes the hunger a moral abyss: answer it willingly and you're marked forever, and noticed. Use the Wendigo when you want winter itself to become a predator, and when the party's past choices (who did they leave to starve? who ate what to survive?) come back wearing antlers and calling their names.")}

  {creature(
    sb("The Hunger That Walks", "Tier III &middot; a wendigo new-made", 17, 42, "very fast", "+11", "+9", "+6",
       "frost-claws +9 (2d6+4 cold); the cold deepens around it",
       "<strong>Not yet whole.</strong> A man lately turned, still half himself, still nameable &mdash; and for a little while yet, still possible to save.",
       "DC 16, 1d6",
       "Fire and iron put it down; faster, a true name and a held warmth may yet call the man back from it &mdash; once.",
       mark="As the Wendigo."),
    lore=[
      "Between the man and the monster there is a window, and the Hunger That Walks lives in it. This is a wendigo new-made &mdash; a soul lately turned, the cold not yet finished with him, still half the person he was and still answering, for a little while, to the name he was given at birth. He is fast and frost-clawed and the cold deepens around him, but he is not yet the towering thing of the deep storm. He is a man losing the fight, and not quite lost.",
      "And because he is not yet whole, he can still &mdash; for a little while, and only once &mdash; be called back. Fire and iron will put him down like any of the cold things. But a true name spoken with love, a warmth held out and not withdrawn, may yet reach the man still drowning inside the hunger and pull him back to himself. The window is narrow. It closes fast. But it is there, and a party that knows it is there has a choice the deep-winter Wendigo never offers."],
    found="The edges of the deep-winter country, near where a man was lost to starvation or the cold &mdash; a recently-stricken camp, cabin, or pass. He often still haunts the place and people he knew in life.",
    keeper="The Hunger That Walks is the Wendigo's tragedy made personal and salvageable, and it gives the party a wrenching choice the full Wendigo denies them. Mechanically it's a lesser cold-thing &mdash; killable with fire and iron &mdash; but the entry offers a second path: a true name and held warmth can call the man back, <em>once</em>. This is the emotional core. If the new-made wendigo is someone the party knew (and it should be, when possible), the question becomes: do you put him down, safe and certain, or do you risk reaching the man still inside, knowing the window is closing and failure means the cold gets you too? Run the half-state with pathos &mdash; flashes of the person, the name, the memory &mdash; alongside the genuine danger. It pairs directly with the Wendigo-Touched (the human stage) and the Wendigo (the lost end), letting you run a three-act tragedy of a single soul. Don't make the rescue easy or guaranteed; make it a real gamble with a real cost. The party that saves him earns one of the campaign's great victories. The party that fails, or chooses the bullet, earns one of its great sorrows. Either way, they'll remember it.")}

  {creature(
    sb("The Dust Devil", "Tier II &middot; the whirlwind with a will", 16, 24, "very fast; the wind", "+9", "+10", "+4",
       "flaying grit +6 (1d8+3 and blinds, Fort DC 14); flings the small and unanchored",
       "<strong>No center to strike.</strong> A spinning column of grit and spite that scours flesh and steals breath; it cannot be cut, only weathered.",
       "DC 13, 1d4",
       "Get behind stone or below the ground and let it spend itself; water and a still place break it apart."),
    lore=[
      "Most dust devils are just wind playing in the heat. This one has a will in it &mdash; a spinning column of grit and spite that picks its targets, follows a fleeing man across open ground, and scours the flesh from his bones with a thousand stinging grains while it steals the very breath from his lungs. The Dust Devil is the desert's small malice made mobile, and it cannot be cut, shot, or grappled, because there is no center to strike.",
      "It is all motion and grit, and the only answer to it is the oldest one: get out of the wind. Behind stone, below the ground in a wash or a dugout, in any still and sheltered place, it cannot reach you, and it spends its spite against the rock and comes apart. Water breaks it. Stillness defeats it. A man caught flat in the open with nowhere to shelter is the only man it can truly kill."],
    found="The open desert and dry plains, the flat exposed country where the wind has room to spin. It rises in the heat of the day and chases what moves across the bare ground.",
    keeper="The Dust Devil is a hazard-creature that teaches the party to fight the environment, not the monster. There's nothing to shoot &mdash; it's a spinning column with no center &mdash; so the entire encounter is about finding shelter: stone to get behind, ground to get below, a still place that breaks its spin. Run it as a scramble across exposed ground toward cover, with the flaying grit and blinding and breath-stealing raising the pressure each round they're caught in the open. It's a great way to make a desert crossing dangerous and to reward terrain awareness and quick thinking over firepower. Use it as a complication during a chase or a journey, or as the desert's warning shot before a bigger threat. The lesson is small but useful: some of this country's monsters can't be beaten at all &mdash; you survive them by knowing where to hide. Pair it with the Thirst and the Singing Sand for a desert that's actively, patiently trying to kill anyone crossing it.")}

  {creature(
    sb("The Red Wind", "Tier III &middot; the prairie-fire that hunts", 16, 40, "very fast; spreads", "+11", "+9", "+3",
       "a wall of flame +9 (2d6+5 fire, all in its path); leaps breaks and gullies that fire should not",
       "<strong>It chooses.</strong> A wildfire with a malice in it, turning against the wind to take the fleeing and spare the still &mdash; or the reverse, to herd them.",
       "DC 16, 1d6",
       "A backfire, a wide break, or a river robs it of ground; find and quench the cursed thing at its origin &mdash; a brand, a body, a burned wrong."),
    lore=[
      "A prairie fire is terror enough when it's only fire. The Red Wind is worse, because it chooses. It turns against the wind when it should die down, leaps firebreaks and gullies that no honest fire could cross, and it picks &mdash; running down the man who flees and sparing the one who stands still, or the reverse, herding a fleeing party toward the cliff or the box canyon where it means to finish them. There is a malice in it, a will, a hunger that uses flame the way other things use teeth.",
      "It was born of a wrong &mdash; a brand thrown in spite, a body burned, a curse worked into the dry grass &mdash; and that origin is its heart. The ordinary fire-fighting tricks buy time: a backfire, a wide break, the far side of a river. But the Red Wind keeps coming until the cursed thing at its source is found and quenched, and only then does it become, at last, just a fire, that ordinary means can finally put out."],
    found="The dry grasslands and prairies in the burning season, spreading from the cursed origin-point where the wrong was done. It ranges as far as there's grass to burn and prey to hunt.",
    keeper="The Red Wind is a wildfire with intent, and it runs as a moving, choosing hazard that the party can't simply outfight. Its malice is the key distinction from natural fire &mdash; it turns wrong, leaps breaks, and herds the fleeing toward worse ground, so a party that just runs gets driven into a trap. The firefighting measures (backfire, break, river) buy time and space but don't end it; the win is finding and quenching the cursed origin (the brand, the burned body, the worked wrong). Build the scenario as a desperate fighting-retreat while someone works out <em>where the fire is coming from</em> and what's keeping it alive. Run the dread of a fire that thinks &mdash; the flames that turn to follow, the way it spares the still and takes the running, or vice versa, so the party can't even trust the obvious survival instinct. It pairs with the Drought-Bringer (a curse that withers) as the land's two great elemental punishments. Use it to turn a prairie into a death-trap and to make the party fight a force of nature with a grudge.")}

  {creature(
    sb("The White Death", "Tier III &middot; the blizzard with a face", 17, 44, "fast; rides the storm", "+13", "+9", "+6",
       "a freezing grip +9 (2d6+4 cold and Drained); the cold itself bleeds the unsheltered each round",
       "<strong>It seeks the warm.</strong> A blizzard-spirit that hates a living fire and comes for the heat of bodies and hearths, snuffing both.",
       "DC 16, 1d6",
       "A great fire that will not be smothered drives it back; it cannot abide a hearth held against it through the night."),
    lore=[
      "The blizzard has a face, and it hates you for being warm. The White Death is a storm-spirit of the deep cold, and what it wants is heat &mdash; the warmth of a living body, the glow of a hearth, the small defiant fire a stranded party builds against the night &mdash; and it comes to snuff all of it. Where it passes, fires gutter and die, breath freezes in the chest, and the unsheltered bleed warmth into the white until there's none left to give.",
      "It is not subtle and it is not clever. It is the cold itself, given hunger and a will, and it lays siege to anything warm enough to notice. The only thing it cannot abide is a great fire held against it &mdash; a blaze big enough and tended hard enough that the storm cannot smother it through the long night. Keep that fire alive until dawn, and the White Death moves on, hungry, to find easier warmth elsewhere."],
    found="The deep-winter mountains and northern country, the high passes in storm season. It rides the blizzard and lays siege to any shelter, camp, or homestead with warmth and life in it.",
    keeper="The White Death turns a winter night into a siege, and the siege is the encounter. It can't be meaningfully attacked &mdash; it's the storm &mdash; so the party's task is to <em>hold a fire through the night</em>. Run it as a survival scenario: the cold bleeding the unsheltered each round, the storm trying to smother the flames, the desperate work of keeping the fire fed and big enough while the White Death claws at it. This makes fuel, shelter, and endurance into the mechanics that matter. The dread is the relentlessness &mdash; the cold that gets in everywhere, the fire that keeps guttering, the long hours till dawn. It pairs with the Wendigo as the chapter's two faces of killing cold (the hunger that walks vs. the cold that besieges). Use it to make a winter crossing genuinely deadly, to put the party's resource management and teamwork under real pressure, and to teach that against some forces the only victory is to outlast them. A great bottle-episode threat: one night, one fire, one storm with a face, and dawn a very long way off.")}

  {creature(
    sb("The Thirst", "Tier II &middot; the water that isn't there", "&mdash;", 26, "drifts ahead, always ahead", "+9", "+7", "+8",
       "no blow &mdash; it shows you water and drinks you dry as you chase it (Fort DC 14/day, Drained and worse)",
       "<strong>The mirage.</strong> A desert thing that wears the shape of the water you need and leads you out past any hope of the real thing.",
       "DC 13, 1d4",
       "Do not follow water that recedes; trust your map and your canteen, turn your back on it, and walk the line you know."),
    lore=[
      "Dying of thirst in the desert, you'll see water &mdash; everyone does &mdash; shimmering just ahead, a lake, a river, salvation. The Thirst is what happens when that mirage has a will. It wears the exact shape of the water you need most, always just ahead, always receding as you stumble toward it, leading you off your route and out past the last real water and any hope of reaching it, drinking you dry a day at a time as you chase the promise of a drink.",
      "It has no claws and strikes no blow. It kills by leading, by hope, by the terrible logic of a dying man who can <em>see</em> the water right there. The only defense is the hardest thing in the world to do when your throat is closing: turn your back on the water you can see, trust the map and the canteen and the line you know, and walk away from the only thing you want."],
    found="The deep desert and the dry crossings, where real water is scarce and a dying traveler's hope can be turned against him. It preys on the lost, the stranded, and the desperately thirsty.",
    keeper="The Thirst is a psychological hazard that weaponizes hope and the body's own desperation. It can't attack &mdash; it lures, showing the party the water they're dying for and leading them away from the real thing. The 'fight' is the agonizing discipline of refusing to chase visible water, trusting navigation over the eyes, walking away from salvation. Run it during a desert crossing when the party is genuinely low on water, so the temptation is real and the stakes are survival. The Fort save each day (Drained and worse) represents the body failing as it chases the mirage. It pairs with the Lantern-Light (another lure that preys on the lost and desperate) and the Dust Devil and Singing Sand as the desert's arsenal. Use it to make water itself a story element &mdash; to turn a crossing into a test of nerve and trust, where the party's enemy is their own thirst and the false hope the desert dangles. The lesson is brutal and true to the country: out here, the thing you want most can be the thing that kills you, and survival sometimes means turning your back on it and walking the hard line you know.")}

  {creature(
    sb("The Flood-Serpent", "Tier IV &middot; the river risen up", 19, 70, "swim very fast; is the flood", "+15", "+13", "+8",
       "a wall of water +13 (2d8+6 and sweeps away, Athletics DC 18); drowns whole bottoms overnight",
       "<strong>It is the rising.</strong> The spirit of a river that means to take back the valley; the flood is its body and cannot be fought, only diverted.",
       "DC 20, 1d10",
       "An offering at the old ford, a broken dam, or the bones it wants returned to the water turn it back to a river."),
    lore=[
      "The river was here first, and it remembers. When men dam it, divert it, build their town in its old floodplain and forget to ask its leave, the Flood-Serpent rises &mdash; the spirit of the river itself, come to take back the valley. Its body is the flood: a wall of water that sweeps away fences and barns and bridges, that drowns whole bottoms overnight, that rises faster than anything living can outrun and means to put the valley back under water where it belongs.",
      "You cannot fight a flood. Bullets vanish into it; there's nothing to strike but the rising water itself. But the river can be answered, because the river has a grievance: an offering left at the old ford, a dam broken to let it run its true course, the bones it wants returned to the water it took them from. Give the river what it came for, and the Flood-Serpent subsides into a river again, and the valley drains, and the survivors rebuild &mdash; this time, perhaps, asking leave."],
    found="River valleys and floodplains, especially where men have dammed, diverted, or built against the water's old course. It rises with the spring melt, the great rains, or whenever its grievance comes due.",
    keeper="The Flood-Serpent is a disaster with a grievance, and it runs as a race against a rising flood rather than a battle. Its body is the water &mdash; unfightable, unstoppable by force &mdash; so the party's task is twofold: survive the flood (evacuate, reach high ground, save who they can) and answer the river's grievance (the offering at the old ford, the dam to break, the bones to return). Build the scenario around discovering <em>why</em> the river has risen: what did the town do, what does the river want, what wrong needs righting? Run the flood as a mounting environmental threat &mdash; the water rising, the bottoms drowning, the desperate rescues &mdash; while the party works out the cause. It pairs with the Horned Serpent (a thing <em>in</em> the water) as the chapter's water-horrors, and with the Drought-Bringer as the land's revenge for how it's been used. Use it to make a flood epic and meaningful, to put the party in the role of disaster-responders and investigators at once, and to comment on what settlement takes from the country without asking. Give the river its due, and it becomes a river again. Ignore it, and it takes the valley.")}

  {creature(
    sb("The Stone Giant", "Tier IV &middot; the mountain that stirs", 21, 78, "slow; unstoppable", "+16", "+8", "+10",
       "a fist of granite +13 (3d6+6 and knocks flat); steps that shake the ground",
       "<strong>Old and sleeping.</strong> A thing of the high rock that wakes rarely and ruinously; it is slow, but nothing the frontier owns will stop it once roused.",
       "DC 20, 1d10",
       "You do not fell it &mdash; you flee it, lead it astray, or lull it back to its long sleep. Do not wake it again."),
    lore=[
      "There are mountains that are not only mountains. The Stone Giant is a thing of the high rock, old beyond the reckoning of men, that sleeps for ages as a ridge or a crag or a tor. A mine driven too deep, a charge set wrong, a greed that dug where it should have left the rock alone &mdash; and the mountain stirs, and stands, and steps, and the ground shakes with every footfall. It is slow. It is also utterly unstoppable, and nothing the frontier owns will so much as scar it.",
      "You do not fell a mountain. The whole question, once it's roused, is how to survive it and how to put it back to sleep &mdash; to flee it, to lead it astray over ground that doesn't matter, to lull it back into the long dreamless rest it was woken from. And then, the hard part, the part men never seem to learn: to leave it alone, and never, ever wake it again."],
    found="The high mountains and ancient rock, where it sleeps disguised as the landscape itself. It wakes only when disturbed &mdash; by deep mining, by disrupted ground, by some greed or folly that won't let the old rock lie.",
    keeper="The Stone Giant is the book's lesson that some things are too old and too vast to fight, only to survive and to let lie. Its numbers and unstoppability make combat a non-starter &mdash; you cannot fell a mountain &mdash; so the encounter is about flight, misdirection, and the deeper goal of lulling it back to sleep. Run it slow and apocalyptic: each step shakes the ground, each granite fist flattens what it hits, and the party's cleverness (leading it astray, finding what will quiet it) matters far more than their guns. The framing is pointed &mdash; it was woken by greed or folly (a mine driven too deep, ground disrupted), which ties it to the cost of how men use the country. Build the scenario around what woke it and what will quiet it, and let the resolution be restoration and restraint rather than victory. It pairs thematically with the Thunderbird (another ancient thing not meant to be killed) as the chapter's reminders of the party's smallness. Use it to humble, to awe, and to teach that the oldest monster is the country itself, and the wisest course is sometimes to put a thing back to sleep and walk very quietly away.")}

  {creature(
    sb("The Drought-Bringer", "Tier III &middot; the curse on the land", "&mdash;", 40, "fixed to the country it withers", "+11", "+5", "+11",
       "no blow &mdash; the land dies around it, wells fail, stock falls, and folk turn on each other (Will saves vs. despair)",
       "<strong>A withering.</strong> Where it settles, the rain forgets to come and the ground gives up; it feeds on the slow ruin and the strife it breeds.",
       "DC 16, 1d6",
       "Lift the curse at its root &mdash; the broken oath, the poisoned well, the wronged dead &mdash; and the rain returns; the gun is useless against a dry sky."),
    lore=[
      "Where it settles, the rain forgets the way. The Drought-Bringer is a curse on the land made manifest &mdash; not a thing you can see crossing a field, but a withering that spreads from a poisoned center, drying the wells, killing the stock, cracking the ground, and turning neighbor against neighbor as the country starves and the despair sets in. It feeds on that slow ruin, on the strife and the dying hope, growing stronger the longer the land suffers.",
      "There is no shooting a dry sky. The Drought-Bringer has no body to fight, only a curse to lift, and the curse has a root: a broken oath, a poisoned well, a wronged dead that was never answered, some wrong done to the land or on it that festered into this withering. Find that root and set it right &mdash; honor the oath, cleanse the well, lay the wronged to rest &mdash; and the rain remembers the way, and the country comes back to life, and the despair lifts like a fever breaking."],
    found="A region withering under unnatural drought, spreading from the cursed root-cause &mdash; a poisoned well, a betrayal, an unavenged death tied to the land. The whole afflicted country is its body.",
    keeper="The Drought-Bringer is a slow apocalypse and a mystery, and it makes the entire afflicted region the 'monster.' There's nothing to fight &mdash; the gun is useless against a dry sky &mdash; so the encounter is pure investigation and restoration: find the root of the curse (the broken oath, the poisoned well, the wronged dead) and set it right. Run the creeping ruin as the pressure: the failing wells, the dying stock, the community fraying as despair takes hold (the Will saves vs. despair can affect the party too, and certainly the NPCs around them). This is a scenario about a whole region in crisis and the party as the ones who diagnose and heal it. Build the history into the land &mdash; what wrong was done here, who did it, what was promised or poisoned or buried &mdash; so the cure is a piece of detective work and moral reckoning. It pairs with the Flood-Serpent as the land's two revenges (too little water, too much) and with the Scalp-Taker's Ghost as the country remembering an old wrong. Use it to slow the campaign down into something somber and humane, where heroism means restoring a dying land rather than killing a monster, and where the rain returning is the most satisfying victory the party can earn.")}

  {creature(
    sb("The Singing Sand", "Tier II &middot; the dunes that hum and swallow", "&mdash;", 28, "the desert itself", "+9", "+6", "+8",
       "shifting ground (Reflex DC 15 or sink and be buried, Fort DC 15/round); the song draws sleepers to lie down",
       "<strong>The song.</strong> A low hum off the dunes at dusk that lulls travelers to rest where they will be swallowed by morning.",
       "DC 13, 1d4",
       "Stop your ears against the song, keep to the rock and the hard pan, and never make camp where the sand sings."),
    lore=[
      "At dusk the dunes begin to hum &mdash; a low, droning, almost musical sound that rises off the sand as the heat leaves it, and that gets into a tired traveler's bones and tells him, gently, that this would be a fine place to lie down and rest. The Singing Sand is the desert's lullaby and its grave both. Those who heed the song and bed down on the singing dunes sink as they sleep, the sand shifting and swallowing, so that by morning there's nothing left but smooth dune and a hump that the next wind erases.",
      "The song is the lure and the shifting sand is the jaws. A man who keeps his wits, stops his ears, and beds down on hard rock or packed pan instead of the soft singing dunes wakes up fine. A man who lets the desert sing him to sleep where it wants him does not wake up at all. The old hands have one rule, and they keep it: never, ever make camp where the sand sings."],
    found="The deep desert and the great dune-fields, where the sand is soft and deep enough to swallow a sleeping man. The song rises at dusk; the danger is greatest to the exhausted traveler looking for a place to rest.",
    keeper="The Singing Sand turns the simple act of making camp into a deadly choice, and it preys on exhaustion and trust. The song lulls travelers to bed down on the dunes, where the shifting sand swallows them as they sleep &mdash; so the threat lands at the most vulnerable moment, when the party is tired and looking for rest. The defense is folk-wisdom and discipline: stop your ears against the song, refuse the soft inviting dunes, camp on hard rock or packed pan. Run the temptation &mdash; the party's exhausted, the dunes are soft and close, the song is so soothing &mdash; and the dread of waking to find the ground itself swallowing a friend. The Reflex save (sink and be buried) and the smothering Fort saves make rescue a desperate scramble. It pairs with the Thirst, the Dust Devil, and the Lantern-Light as the desert's patient arsenal, all of which prey on the lost and weary. Use it to make a desert crossing's nights as dangerous as its days, to reward the party that respects local knowledge, and to teach the unsettling lesson that out here even the ground you sleep on can be hungry, and the sweetest-sounding rest can be the last.")}
</section>
"""

# ============================================================ VII. THE OLD DARK
OLD = f"""<!-- VII -->
<section class="page" id="olddark">
  {runhead('VII. The Old Dark')}
  <h1 class="chapter">VII. The Old Dark</h1>
  <p class="chapter-sub">The things that were never men, and never meant for here.</p>
  <div class="divider"></div>
  {quote("Do not read the part that comes after this. I am leaving it in only so you will know I was warned, and went on.", "sealed testimony, Calvary Wells")}
  <div class="narr">Here the field-book runs out of field. What follows was never a man, was never a
  beast, and was never made by the country &mdash; the country only holds the door. The compiler offers
  no advice for this chapter, because there is none to offer: there is only the knowing, and the price
  of the knowing, which you have been paying a page at a time since you first opened this book. Turn
  the page or do not. It has already noticed you reading.</div>
  <p class="dropcap lead">These are the deep things &mdash; the Patrons and their reaching hands, the wrong that comes from
  outside the world. You rarely kill them. You close the door, and you hope it stays closed.</p>
  <p class="note"> <strong>Signs of the kind:</strong> angles that will not add up, dreams shared between strangers, a word everyone has lately begun to use that no one taught them, and a wrongness the eye keeps sliding off of.</p>

  {creature(
    sb("Servant of the Deep Dark", "Tier IV&ndash;V &middot; a Patron's reaching hand", 21, 90, "it is nearer than it was", "+15", "+13", "+19",
       "reaching limbs +17 (3d8+8 and Fort save or wither); the geometry of it is wrong and hard to strike",
       "<strong>Not meant for here.</strong> Lead and steel close like water around it; to behold it fully is the DC-25 sight.",
       "DC 20 glimpsed, DC 25 beheld; 1d10 (+Affliction if beheld)",
       "You do not kill it &mdash; you close the door: break the rite, cleanse the ground, end the bargain that thinned the veil.",
       mark="Any plea or working aimed at it or its Patron is +1 Mark at least."),
    lore=[
      "It is a hand reaching through from somewhere that is not anywhere, the local instrument of a Patron &mdash; one of the vast, indifferent things that wait outside the world and occasionally extend a piece of themselves into it. The Servant of the Deep Dark does not belong here, and the world knows it: the geometry of the thing is wrong, its limbs reach from angles that aren't there, and it is never quite where the eye says it is, so that lead and steel close around it like water around a stone and find nothing to break.",
      "To glimpse it is bad. To behold it fully &mdash; to let the eye actually resolve what it's looking at &mdash; is to risk the mind coming apart. And it is always nearer than it was, drawn through by some rite, some bargain, some thinning of the veil that a fool or a desperate man performed. You do not kill a reaching hand. You close the door it reached through, and you pray the rest of the thing doesn't notice the door is gone."],
    found="Wherever the veil has been thinned &mdash; a site of dark ritual, a place where a bargain was struck, ground that's been soaked in the wrong kind of attention. It manifests near the rite or the bargain that called it.",
    keeper="The Servant of the Deep Dark introduces the chapter's iron rule: <em>these are not killed, they are shut out</em>. Its wrongness is mechanical &mdash; weapons close like water around it, it's nearer than it was, beholding it fully courts an Affliction &mdash; so a party that tries to win by damage will fail and lose their minds trying. The win is to close the door: find and break the rite, cleanse the ground, end the bargain that thinned the veil. This makes the encounter an investigation under terrible pressure: what opened this door, and how do we shut it, before the hand pulls more of itself through? Run the dread of the wrong geometry and the thing that won't stay where it's looked at. The Mark warning is central to the whole chapter &mdash; any attempt to plead with or work upon it or its Patron corrupts. Use it to establish that the party has crossed into territory where their guns are nearly useless and their wits, nerve, and restraint are all that stand between them and something that was never meant to be here. It's the gateway to the deep dark, and it should feel like a door closing behind them.")}

  {creature(
    sb("The Whisperer's Mouth", "Tier III &middot; a vessel for the Patron's words", 16, 38, "normal", "+9", "+7", "+13",
       "no blow &mdash; it speaks (Will DC 16 each round heard or take 1d6 and lose the thread of your own mind)",
       "<strong>It only talks.</strong> A person or thing hollowed to carry a voice from outside; the words are true, and that is the harm of them.",
       "DC 16, 1d6",
       "Silence it &mdash; deafen yourself, gag or end the vessel &mdash; and do not, whatever it promises, listen for the rest.",
       mark="Heeding what it says is +1 Mark."),
    lore=[
      "Something out beyond the veil has things it wants said, and it needs a mouth to say them. The Whisperer's Mouth is a person &mdash; or what's left of one &mdash; hollowed out and made into a vessel for a voice from outside. It does nothing but talk. It raises no hand, makes no attack. And it is one of the most dangerous things in this book, because the words it speaks are <em>true</em>, and that truth is the harm of them: secrets that unmake you to know, answers to questions you should never have asked, the shape of things the mind is not built to hold.",
      "Hear it long enough and you lose the thread of your own mind, unspooling as the true and terrible words wind into you. The only defense is silence &mdash; stop your ears, gag the vessel, end it if you must &mdash; and the discipline never to listen for the rest, no matter what it promises to tell you, no matter how badly you want to know."],
    found="Wherever a Patron wants a message delivered &mdash; the vessel may be a captured person, a corpse, a cultist who volunteered, set in a place the Patron means to influence. It speaks to whoever comes within earshot.",
    keeper="The Whisperer's Mouth weaponizes knowledge and curiosity, and it's a fight the party wins by <em>refusing to engage</em>. It has no attack but speech, and the speech is true &mdash; which is exactly why it's deadly. The mechanical pressure is the per-round Will save for anyone who keeps listening, eroding their mind. The defenses are about silence and discipline: deafen yourself, gag or destroy the vessel, and crucially, don't listen for more even though it offers true and tantalizing answers. The horror is the temptation &mdash; it knows things, real things, things the party desperately wants to know (about the plot, about their pasts, about the dark itself), and listening is how it kills you. The Mark warning is sharp: heeding what it says corrupts. Run the agonizing pull of forbidden truth, and reward the player who has the discipline to clap their hands over their ears and cut the vessel's throat rather than hear one more sentence. It's a test of a party's restraint and a pure distillation of cosmic horror's central idea: some knowledge costs you the mind that holds it.")}

  {creature(
    sb("The Star-Spawn", "Tier V &middot; the thing that fell", 23, 110, "crawls; flies wrong", "+19", "+15", "+19",
       "lashing limbs +17 (3d8+8, several a round); a gaze that boils the mind (Will DC 20)",
       "<strong>From the cold sky.</strong> It came down with the falling star and the crater is its making; the land around it is already changing to suit it.",
       "DC 25, 1d10 + Affliction",
       "It cannot truly be killed by the living &mdash; bury it again under stone and salt, flood the crater, or seal the place and never speak of it."),
    lore=[
      "It came down with the falling star, and the crater is the first thing it made. The Star-Spawn is a thing from the cold between the stars, fallen to earth and broken loose, and the country around its landing is already wrong &mdash; the plants growing in colors that have no names, the animals changed, the water gone strange, the very ground beginning to reshape itself to suit a thing that was never meant to touch this world. It crawls and it flies in ways that flight should not work, and its gaze alone can boil a man's mind in his skull.",
      "You cannot kill it, not really, not with anything the living own. It is too far from the rules that govern dying things. All you can do is put it back &mdash; bury it again under stone and salt, flood the crater it made, seal the place and walk away and never speak of it again &mdash; and hope that what you've sealed stays sealed, and that the land it's already changed can someday be changed back."],
    found="At the crater where it fell &mdash; a blast-site, a scar on the land, a valley gone wrong. The corruption spreads outward from there; the longer it's loose, the larger the changed country grows.",
    keeper="The Star-Spawn is full cosmic horror &mdash; a Tier V thing that cannot be killed, only contained, and that's already remaking the world around it. Its numbers are overwhelming and the mind-boiling gaze makes even approaching it deadly, so frame the encounter entirely around containment: bury it under stone and salt, flood its crater, seal the place. The spreading corruption is the clock &mdash; the changed land grows, the wrongness deepens, the window to seal it closes. Run the alien landscape as dread in itself: the wrong colors, the changed animals, the strange water, the country becoming something else. The party's victory is small and grim &mdash; not slaying it but burying it again and walking away &mdash; which is the genre's whole point. It pairs with the Eye Between Stars and the Wound in the World as the chapter's apex cosmic threats. Use it when you want to confront the party with something genuinely beyond them, where the heroic act is sealing a door rather than winning a fight, and where the best possible outcome is that the thing goes back to sleep and the land slowly forgets. There is no clean victory here. There is only containment, and the hope it holds.")}

  {creature(
    sb("The Veinwork", "Tier IV &middot; the wrong that runs through the rock", 20, 70, "spreads through stone", "+15", "+6", "+13",
       "lashing ore +13 (2d8+6); the walls themselves reach and crush in the deep galleries",
       "<strong>In the mountain's blood.</strong> A living, geometric corruption threading the ore; the deeper the mine, the more of it, and it is the mine now.",
       "DC 20, 1d10",
       "Collapse and seal the workings; it cannot be cut out, only walled off forever &mdash; and the vein must never be followed."),
    lore=[
      "The miners followed the vein deeper than was wise, because the ore was rich and strange and it gleamed in patterns that drew the eye, and somewhere down in the dark they realized the vein was following them back. The Veinwork is a living corruption threading through the rock itself &mdash; a geometric wrongness in the ore, growing through the mountain's stone like a sickness through blood, and the deeper the workings go, the more of it there is, until the mine is not a mine anymore but a body, and the men in it are inside the thing.",
      "The walls reach. The ore lashes out. The tunnels rearrange in the dark. You cannot cut it out, because it <em>is</em> the rock now, all the way down. The only answer is to collapse the workings and wall it off forever, to seal the mountain and abandon the wealth and never, ever let anyone follow that vein again &mdash; because it goes down farther than anyone has lived to map, and something is down there at the bottom of it, waiting for the digging to reach."],
    found="Deep mines that struck a strange, rich vein and followed it too far. The corruption is worst in the lowest galleries and spreads upward through the stone as the digging continues.",
    keeper="The Veinwork turns a mine into a monster and greed into the trigger. It can't be fought conventionally &mdash; it's the rock itself, lashing and crushing and rearranging in the deep galleries &mdash; so the only victory is to collapse and seal the workings, abandoning the wealth that drew everyone down. That's the moral knife: the rich strange vein is the lure, and walking away from a fortune to wall the thing off forever is the hard, correct choice. Run it as a descent into a mine that becomes increasingly, geometrically wrong the deeper it goes, with the dread of realizing the tunnels are alive and the way out is changing behind them. The escalating depth is the structure: each level down is more corrupted, and somewhere at the bottom is the source the party must never reach. Use it for an underground horror crawl about the cost of digging too deep and wanting too much, and let the resolution be sealing and renunciation rather than conquest. It pairs with the Stone Giant (the mountain that wakes) as the deep earth's two warnings against greed, and it's a perfect cosmic-horror frame for the very Western theme of the strike that's too good to be true.")}

  {creature(
    sb("The Pallid Herald", "Tier IV &middot; the one who comes before the worse", 20, 68, "drifts", "+13", "+13", "+16",
       "a touch that unmakes color and warmth +13 (2d8+6 and Drained); its message is itself a curse",
       "<strong>An announcement.</strong> It arrives to tell a place that its end is coming; where it has spoken, the Old Dark follows within the season.",
       "DC 20, 1d10",
       "Driving it off only delays its master; the true answer is to undo whatever drew its master's eye in the first place.",
       mark="Hearing its message in full is +1 Mark."),
    lore=[
      "It drifts into town like a fog with a shape inside it, pale and cold and draining the color from everything it passes, and it has come to deliver a message: that this place has been noticed, that its end is coming, that the Old Dark has turned its attention here and will arrive within the season. The Pallid Herald is an announcement made flesh, and its very message is a curse &mdash; to hear it in full is to be marked, to be part of the ending it foretells.",
      "Driving it off is easy enough and accomplishes nothing; it is only the messenger, and killing the messenger does not unsend the message. Its master's eye is already on the town, and the Herald's coming means the clock has already started. The only real answer is to find out <em>why</em> &mdash; what did this place do, what drew the deep dark's attention, what bargain or rite or buried wrong invited the worse thing the Herald announces &mdash; and undo it before the season turns."],
    found="A town or settlement that has drawn the Old Dark's attention &mdash; usually through a rite, a bargain, a buried wrong, or simple bad luck. The Herald arrives first; the worse thing follows within the season.",
    keeper="The Pallid Herald is a harbinger and a deadline, and its purpose is to start a clock. When it arrives and delivers its message, you've told the party that something far worse is coming and given them a season to prevent it. Driving off the Herald itself is a trap &mdash; it's just the messenger, and its master's attention is already fixed. The real work is investigation: <em>why</em> has the deep dark noticed this place, and how do you make it stop noticing? Build the scenario around uncovering and undoing the cause (the rite performed, the bargain struck, the wrong buried) before the worse thing arrives. The Mark warning &mdash; hearing the full message corrupts &mdash; means even receiving the warning has a cost. Run the Herald's coming as creeping dread: the color draining from the world, the cold, the sense of a countdown beginning. It's a scenario-opener that hands the party a mystery, a deadline, and high stakes all at once, and it sets up a back-half confrontation with whatever the Herald announced. Use it to make the party feel time pressing on them, and to frame a whole adventure as a race to un-draw the eye of something vast before it finishes turning toward them.")}

  {creature(
    sb("The Crawling Congregation", "Tier III &middot; the faithful, fused", 16, 44, "slow; tireless", "+11", "+4", "+9",
       "a hundred hands and mouths +9 (2d6+4 and grab, drawing you in); grows with each soul it takes",
       "<strong>One body of many.</strong> A whole congregation given over and melded into a single crawling mass around the relic they could not stop touching.",
       "DC 16, 1d6",
       "The relic at its heart is the binding; take it, break it, or burn it, and the mass comes apart into its poor dead.",
       mark="Touching the relic is +1 Mark."),
    lore=[
      "They were a congregation once &mdash; a church, a commune, a tent-revival full of the faithful &mdash; and they found a relic, or were given one, and they could not stop touching it. One by one they melded to it and to each other, flesh fusing to flesh around the thing at the center, until the whole congregation became a single crawling mass of a hundred hands and mouths, dragging itself across the country and pulling in every soul it can reach to add to itself.",
      "It is slow but it is tireless, and it grows with each person it takes. The hands reach and grab and draw you in toward the heaving center, and if they pull you in, you become another part of it. But the relic at its heart is the binding that holds the whole horror together &mdash; take it, break it, burn it &mdash; and the mass comes apart at last into what it always was underneath: a great many poor dead people, finally released, finally still."],
    found="Wherever a congregation found the wrong relic and could not let go &mdash; an isolated church, a religious commune, a revival camp. The mass crawls slowly outward from there, growing as it takes in more souls.",
    keeper="The Crawling Congregation is a swarm-with-a-heart (kin to the Gravecaller and the Carrion Cloud) given a tragic, cosmic-horror frame. The mass grows with every soul it takes, so it's a clock and a threat at once &mdash; the longer it's loose, the bigger it gets. The win is the relic at its center: take, break, or burn it, and the whole horror falls apart into its component dead. So the encounter is about reaching the heart through the grabbing, drawing mass without being pulled in and added to it. The pathos is heavy &mdash; it's made of fused, melded people, victims all, and freeing them (by destroying the relic) is a mercy as much as a victory. Run the dread of the crawling mass of hands and mouths, the horror of a grabbed character being drawn in toward fusion, the recognition of familiar faces in the heaving whole. The Mark warning &mdash; touching the relic corrupts &mdash; makes the kill-switch itself dangerous, so the party must find a way to break it without succumbing to it. Use it for body-horror with a moral core, and to show what blind devotion to the wrong thing does to ordinary faithful people.")}

  {creature(
    sb("The Wound in the World", "Tier V &middot; a place where the veil tore", "&mdash;", 110, "fixed; it is a hole in everything", "+19", "+19", "+19",
       "reality fails near it &mdash; flesh, distance, and time come apart (3d8+8, no save to halve within it)",
       "<strong>Not a creature.</strong> A tear where something pushed through; things crawl out of it, and it widens while it is open.",
       "DC 25, 1d10 + Affliction",
       "Sew it shut: undo the rite that tore it, restore what was sacrificed, or close it with a willing life given right &mdash; nothing less will hold.",
       mark="Working near it, or feeding it, is +1 Mark or more."),
    lore=[
      "It is not a creature at all. It is a hole &mdash; a tear in the fabric of the world where something pushed through from the other side and left the veil ripped open behind it. Near the Wound in the World, reality simply fails: flesh comes apart, distance stops meaning anything, time runs wrong or stops or doubles back. Things crawl out of it, drawn or birthed or vomited from whatever is on the far side, and the tear widens the longer it stays open, the hole in everything growing toward the day it can't be closed at all.",
      "You cannot fight a hole. You can only sew it shut, and that costs. Undo the rite that tore it open. Restore what was sacrificed to make it. Or close it the old, terrible way &mdash; with a willing life, given right, in full knowledge of what it buys. Nothing less will hold the wound closed, and the longer the party waits, the higher the price climbs, and the more of the far side bleeds through into here."],
    found="At the site of a catastrophic rite or sacrifice &mdash; a place where a bargain went too far and tore reality open. It's fixed in place but its effects spread outward as it widens; things from beyond emerge around it.",
    keeper="The Wound in the World is the chapter's purest containment scenario: there is no monster to shoot here &mdash; only a tear in the world, and the entire encounter is about closing it before it widens past closing. Its 'attack' is reality failing in its vicinity (no save to halve, within it), making proximity itself lethal, while things crawl out of it as ongoing threats. The win is sewing it shut, and the options carry escalating moral weight: undo the rite (investigation), restore what was sacrificed (a quest), or close it with a willing life given right (the terrible last resort). That final option is one of the heaviest choices the book offers &mdash; a sacrifice play, ideally one a party member might volunteer for. Run the widening as a relentless clock and the bleed-through as mounting chaos. The Mark warning notes that working near it or feeding it corrupts, so even the act of closing it is fraught. Use it as a campaign climax, a point-of-no-return crisis where the stakes are the world bleeding into something else and the cost of saving it may be one of their own. It's cosmic horror at its most demanding: no monster to kill, only a catastrophe to contain, and a price that someone has to pay.")}

  {creature(
    sb("The Faceless Rider", "Tier IV &middot; it rides ahead of ruin", 20, 68, "very fast; always just ahead", "+15", "+15", "+13",
       "a scythe of cold +13 (2d8+6); rides down stragglers and messengers",
       "<strong>The outrider of catastrophe.</strong> Where it passes, disaster follows &mdash; flood, fire, plague, war; it cannot be stopped, only outrun and warned-of.",
       "DC 20, 1d10",
       "You cannot kill the warning. Outrace it to carry word ahead, or turn aside the ruin it heralds before it arrives."),
    lore=[
      "It rides ahead of the ruin, faceless under its hat, always just ahead on the road no matter how fast you ride, and where it passes, disaster comes behind it &mdash; the flood, the fire, the plague, the war, the catastrophe that's already coming and cannot now be stopped. The Faceless Rider is the outrider of ruin, and to see it on the road ahead of you is to know that something terrible is bearing down on wherever it's headed.",
      "You cannot kill it. It is not the disaster, only its herald, and it cuts down the stragglers and the messengers who fall behind &mdash; the ones who might have carried warning, the ones who might have outrun the ruin to alert the town ahead. The only thing to be done is to beat it: outrace it to carry word ahead of the catastrophe, or find a way to turn aside the ruin it heralds before the Rider's road runs out and the disaster arrives."],
    found="On the road ahead of an oncoming catastrophe, always one step in front of the ruin it heralds. It rides toward whatever place disaster is coming for; outpacing it means outpacing the disaster.",
    keeper="The Faceless Rider turns a catastrophe into a race, and that's its whole design. It can't be killed &mdash; it's the herald, not the disaster &mdash; and it hunts the messengers and stragglers specifically to stop warning from outrunning ruin. So the encounter becomes a desperate ride: beat the Rider to the threatened town to raise the alarm and evacuate, or find and turn aside the disaster it heralds before it lands. Run it as a chase with mounting stakes &mdash; the Rider always just ahead, cutting down anyone who falls behind, the ruin gaining behind <em>them</em>. The drama is the clock and the cost: who rides hard enough, who might fall behind to the scythe of cold, can word reach the town in time? It pairs with the Pallid Herald and the Mourner as the book's harbingers (this one the most kinetic of the three). Use it to frame an entire disaster scenario as a race against time, to give a flood or fire or plague a terrifying avatar, and to let the party be heroes not by fighting but by <em>outrunning doom to warn the doomed</em>. The Rider can't be beaten in combat &mdash; only beaten to the finish line.")}

  {creature(
    sb("The Thing in the Well", "Tier III &middot; what answers when you draw", 15, 40, "in the deep water", "+11", "+7", "+11",
       "a long pale reach up the shaft +9 (2d6+4 and drags down); fouls the water it lives in",
       "<strong>Down the dark.</strong> Something came up the water-table into the well, and now the town drinks from its lair; it takes those who lean too far.",
       "DC 16, 1d6",
       "Do not draw from the well. Fill it with stone and salt, or burn it out with oil and fire, and dig your water elsewhere."),
    lore=[
      "Something came up through the deep water-table and into the town well, and now the town has been drinking from its lair without knowing it. The Thing in the Well lives down the dark shaft, in the cold water at the bottom, and it reaches up &mdash; a long pale arm out of the black, grasping for whoever leans too far over the lip to draw the morning water, dragging them down into the deep where it lives. The water tastes wrong, lately. People have started to go missing at the well.",
      "It fouls the water it lives in, so the town that drinks from it sickens slowly even as it loses people one by one. You cannot easily fight a thing at the bottom of a well-shaft. The answer is to stop drawing from it &mdash; fill the well with stone and salt, or pour in oil and burn it out, and dig the town's water somewhere else &mdash; and to do it before the thing in the dark decides to come up the shaft on its own."],
    found="A town well, especially in an isolated settlement that depends on it. The creature came up through the deep water and claimed the shaft; the town's dependence on the well is the trap.",
    keeper="The Thing in the Well is intimate, claustrophobic cosmic horror &mdash; a small-scale entry that makes a town's most ordinary necessity into a deathtrap. The well is the town's water and its dependence, which is the cruel hook: they need it, they drink from it, and it's killing them slowly while taking them one by one. The horror builds through investigation: the wrong-tasting water, the people missing from the well, the slow sickness, the realization of what's down the shaft. It can't easily be fought (it's at the bottom of a well, reaching up), so the answer is denial and destruction: stop drawing, fill it with stone and salt or burn it out with oil, dig water elsewhere. The drama is convincing a desperate town to abandon and destroy its only water source on the word that something lives in it. Run the dread of the pale reach up the dark shaft, the lean over the lip, the grab. It's a tighter, smaller-scale piece than the chapter's apex threats &mdash; use it for a focused village-horror scenario about a community poisoned by the thing it depends on, and about the hard cost of giving up something you need because it's been taken from you by the dark.")}

  {creature(
    sb("The Sermon Made Flesh", "Tier IV &middot; a doctrine given a body", 20, 70, "normal", "+13", "+9", "+16",
       "the Word as a weapon +13 (2d8+6 and Will DC 18 or convert for a round); converts the slain to its choir",
       "<strong>An idea, embodied.</strong> A belief grown so dark and so believed that it took a shape; killing the body does not kill the belief.",
       "DC 20, 1d10",
       "Unmake the idea &mdash; prove the lie at its center, break its hold on the faithful &mdash; and the flesh has nothing left to hold it together.",
       mark="Speaking its creed aloud, even to refute it, risks +1 Mark."),
    lore=[
      "A belief can grow so dark, and be believed so hard by so many, that it stops being merely an idea and takes on a body of its own. The Sermon Made Flesh is a doctrine incarnate &mdash; a creed walking around in a shape, preaching itself, its Word a weapon that converts the very people it strikes, folding the slain into its growing choir. It is not a person who believes a thing; it is the thing itself, the belief, given hands and a voice and a terrible momentum.",
      "You cannot kill an idea by shooting the body it wears &mdash; the belief just finds new flesh, new mouths, new believers. The only way to end it is to unmake the idea itself: prove the lie at its center, break its hold on the faithful, show the doctrine to be the falsehood it is. Do that, and the flesh has nothing left to hold it together, and the Sermon Made Flesh comes apart for want of anyone left to believe it."],
    found="Wherever a dark doctrine has taken deep root &mdash; a corrupted church, a fanatical movement, a town that gave itself over to a terrible creed. It manifests where belief in it is strongest and preaches to spread.",
    keeper="The Sermon Made Flesh is a war of ideas dressed as a monster, and it can't be won with bullets. Its Word converts those it strikes (and the slain become its choir), so a straight fight only feeds it &mdash; every casualty joins the other side. The win is unmaking the <em>idea</em>: prove the lie at the doctrine's center, break its hold on the faithful, expose the falsehood that gives it power. So the encounter is really a battle for belief &mdash; an investigation into the creed's lie, a confrontation that's argued and proven as much as fought, a effort to deconvert the faithful out from under it. The Mark warning is sharp: even speaking its creed aloud to refute it risks corruption, so the party must fight the idea without being infected by it. Run the dread of a belief that walks and preaches and grows, of friends or townsfolk converting mid-fight. Use it to explore fanaticism, dangerous ideas, and the way a creed can outlive any believer. It pairs with the Flock of the Open Eye and the Hollow Prophet as the book's studies of belief weaponized. The lesson: some enemies are ideas, and you beat an idea by proving it false, not by killing the mouth that speaks it.")}

  {creature(
    sb("The Devourer's Tongue", "Tier IV &middot; one reaching part of a greater hunger", 20, 66, "lashes from below", "+15", "+11", "+10",
       "a vast tongue +13 (2d8+6 and grab, drawing prey down a throat you cannot see); retreats when hurt, and returns",
       "<strong>Only a piece.</strong> What you fight is a single appendage of something far larger and still buried; the rest of it is listening.",
       "DC 20, 1d10",
       "Sever the tongue to escape, but the thing itself cannot be killed from here &mdash; leave, seal the place, and do not dig."),
    lore=[
      "What lashes up out of the ground to seize a man and draw him down into a throat no one can see is not the monster. It is the monster's <em>tongue</em> &mdash; a single reaching part of something vast and buried and patient, so large that the tongue is all of it the world will ever see, the rest of it sleeping down in the deep dark beneath, listening through the part it sends up to taste the surface. You are not fighting the Devourer. You are fighting one small reaching piece of it, and the piece is enough.",
      "You can sever the tongue. That buys escape, that ends the immediate danger &mdash; but the tongue grows back, and the thing it belongs to cannot be killed from up here, not with anything men own, because most of it is somewhere you cannot reach and do not want to. The only wisdom is to take the warning the tongue gives, leave the place, seal it behind you, and never, ever dig down toward the rest of it."],
    found="Above the buried body of something vast and old &mdash; a particular patch of ground, a cave, a sinkhole, a dig that went too deep. The tongue lashes up from there; the rest of it is below, and best left there.",
    keeper="The Devourer's Tongue is built on implied scale &mdash; the party fights an appendage and is meant to understand, with dread, that it's only a piece of something far larger and still sleeping below. The tongue can be severed (which buys escape) but regrows, and the thing itself can't be killed from the surface, so the only victory is restraint: take the warning, leave, seal the place, don't dig toward the rest. That's the whole point &mdash; the heroic act is <em>not</em> pursuing it, recognizing that some things are too big to fight and the smart move is to wall them off and walk away. Run the dread of the reaching tongue and the slowly dawning horror of how large the thing it belongs to must be &mdash; the ground that shifts, the sense of something vast listening from below. Resist any urge to let the party 'win' by digging down to the source; the source is unkillable and the descent is suicide. Use it to teach the chapter's hardest lesson &mdash; that wisdom sometimes means leaving the monster alive and sealed rather than dying to prove you could face it &mdash; and to seed a vast, sleeping threat the campaign need never fully reveal. The best Devourer is the one the party walks away from, looking back over their shoulders.")}

  {creature(
    sb("The Cold Deep's Child", "Tier III &middot; spawn of a drowned god", 16, 42, "swim fast; crawls", "+11", "+9", "+9",
       "barbed limbs +9 (2d6+4); a keening that calls more of its kind from the water",
       "<strong>It calls its kin.</strong> A lesser thing born of something vast and sleeping beneath the water; alone it is dangerous, in numbers it is a drowning.",
       "DC 16, 1d6",
       "Salt and fire end the child; but kill it away from deep water, lest its keening bring the rest &mdash; or the parent."),
    lore=[
      "Beneath the deep water &mdash; the great lake, the drowned valley, the cold sea-mouth where the river meets something older &mdash; something vast and divine and drowned lies sleeping, and it has children. The Cold Deep's Child is one of the lesser spawn: barbed and pale and wrong, swimming fast and crawling onto land to hunt, dangerous enough alone. But it keens. And the keening calls its kin up out of the water, more and more of them, until a single child becomes a drowning tide of them &mdash; and if the keening goes on long enough, it may call something far worse than kin.",
      "Salt and fire end a child easily enough, one at a time. The danger is the calling. Kill it near the deep water and its dying keen brings the rest boiling up from below, and behind them, perhaps, the slow stirring of the drowned parent that should never, ever be woken. The wisdom is to take the child away from the water first, somewhere its keening calls nothing, and end it where the deep cannot hear it die."],
    found="The shores of deep water that hides something vast and sleeping &mdash; a great lake, a drowned valley, a cold inlet. The children come ashore to hunt; the parent stays below, and must stay below.",
    keeper="The Cold Deep's Child is a swarm-caller with a buried god behind it, and the tactical heart is the keening: kill it near deep water and it summons its kin (and risks waking the parent), so the party must learn to draw it away from the water before finishing it. That's the clever-play lesson &mdash; where you kill it matters as much as that you kill it. Individually they're manageable (salt and fire), but the calling can escalate a single encounter into a drowning tide, and the implied parent below gives the whole thing a Lovecraftian floor of dread. Run the escalation as a threat the party can prevent by thinking: lure it inland, isolate it, end it where the deep can't hear. Let a party that fights one carelessly at the water's edge face the consequence of the keening bringing more. The sleeping parent should stay a dread implication, never fully seen &mdash; the reason you don't want the keening to go on. It pairs with the Devourer's Tongue as the chapter's 'this is only a piece of something vast' threats, this one in water. Use it for coastal or deep-lake horror, and to teach that against the deep dark, <em>where</em> and <em>how</em> you fight can be the difference between a skirmish and an awakening.")}

  {creature(
    sb("The Unmade", "Tier V &middot; the thing that erases", "&mdash;", 100, "drifts; unhurried", "+19", "+15", "+19",
       "a touch of un-being +17 (3d8+8, and the slain are forgotten utterly); what it takes was never there",
       "<strong>It eats the record.</strong> Those it unmakes vanish from memory, from paper, from the world; the party may not recall who they came in with.",
       "DC 25, 1d10 + Affliction",
       "Write everything down and trust the writing over your own mind; it can be bound only to a thing it cannot unmake &mdash; a true name, a holy anchor &mdash; never killed.",
       mark="To bargain with it to restore one unmade is +2 Mark."),
    lore=[
      "It does not kill. It <em>unmakes</em>. Where the Unmade touches, a thing stops having ever been &mdash; not dead, but erased, gone from memory and from paper and from the world as if it had never existed at all. It drifts, unhurried, certain, and the people it takes don't leave bodies or graves or grieving friends, because no one remembers there was ever anyone to grieve. The party that walks in five strong may walk out four, and not one of them able to say who the fifth was, or that there ever was a fifth.",
      "You cannot kill a thing that erases. The only defenses are desperate: write everything down, every name and face and fact, and trust the writing over your own unraveling memory, because the page may remember what the mind has lost. And it can be <em>bound</em> &mdash; never killed, only bound &mdash; to a thing it cannot unmake: a true name spoken with enough power, a holy anchor old enough to predate it. Bargaining with it to restore even one of the unmade is a deeper damnation than letting them stay gone."],
    found="It drifts where it will, unhurried and patient. There's no lair, no territory &mdash; it goes where there are things to unmake, and the party may not remember encountering it, or what it cost them, at all.",
    keeper="The Unmade is the most conceptually unsettling thing in the book, and running it well means embracing the erasure mechanic fully. When it takes someone, they're <em>gone</em> &mdash; removed from memory, from the party's records, from existence &mdash; which you can dramatize by having the players literally cross a character off, and roleplaying the wrongness of the gap no one can name. The defense (write everything down, trust the page over your mind) makes record-keeping a survival mechanic and creates eerie play where the notes remember what the characters can't. It can't be killed, only bound to something it can't unmake (a true name, a holy anchor), which is the win condition. The Mark warning is the deepest in the book &mdash; bargaining with it to restore an unmade person costs +2 Mark, a damnation &mdash; so even the temptation to undo its work is a trap. Use it sparingly and carefully (erasing a beloved PC is a heavy move &mdash; consider buy-in), and lean into the existential dread: a thing that doesn't kill you but makes you never-have-been, that the survivors won't even remember to mourn. It's cosmic horror at its most abstract and most disturbing, and the rare monster whose victory is measured in the silence where someone used to be.")}

  {creature(
    sb("The Long Trail's End", "Tier IV &middot; the collector of the living", 20, 68, "always one day ahead", "+15", "+13", "+15",
       "the cold hand on the shoulder +13 (2d8+6, ignores armor); marks the next to be taken",
       "<strong>A psychopomp gone wrong.</strong> It was meant to guide the dead and now gathers the living before their time, one to a town, by an old and broken bargain.",
       "DC 20, 1d10",
       "Honor the debt that bound it &mdash; bury its own forgotten dead, or send on the soul it could not &mdash; and it returns to its proper road."),
    lore=[
      "It was meant to be a kindness once &mdash; a guide for the dead, a shepherd to walk the newly-passed gently down the long trail to wherever the dead are meant to go. But a bargain was broken, a debt left unpaid, a soul it was supposed to carry was somehow lost, and the Long Trail's End went wrong. Now it gathers the <em>living</em> before their time, one soul to a town, laying a cold hand on the shoulder of the next to be taken and walking always one day ahead on the road, patient and certain, collecting what was never owed.",
      "It cannot be fought to a standstill &mdash; it ignores armor, it's always just ahead, it does not tire or relent. But it can be set right, because underneath the wrongness it is still, in its ruined way, dutiful. Honor the debt that bound it &mdash; bury its own forgotten dead, find and send on the lost soul it could not carry, pay the price the broken bargain left unpaid &mdash; and the collector of the living remembers its proper office, lets the living go, and returns at last to the road of the dead where it belongs."],
    found="Working its slow way through the towns along a road or region, taking one soul from each before moving on. It's always one day ahead; following its trail means following a line of untimely deaths.",
    keeper="The Long Trail's End is a psychopomp gone wrong &mdash; a death-guide that's started taking the living &mdash; and it's beaten by setting right the old wrong that broke it, not by force. It can't be fought to a stop (always ahead, ignores armor, relentless), so the encounter is a pursuit-and-investigation: trail it through the towns it's harvesting, work out the broken bargain or unpaid debt that twisted it (its own forgotten dead left unburied, a soul it failed to carry), and honor that debt to restore it to its proper road. The structure is a mystery with a ticking cost &mdash; one soul per town, marked by the cold hand, until the party uncovers and pays what's owed. Run the dread of the inexorable collector, the cold hand on the shoulder marking the next to die, the sense of a thing that will not stop until it's set right. It pairs with the Mourner and the Faceless Rider as the book's death-heralds, but this one is itself the taker, not just the warning. Use it for a somber, investigative scenario about an old kindness corrupted, where the party saves lives not by fighting death's shepherd but by healing the wound that made it cruel &mdash; and lets it go home.")}

  {creature(
    sb("The Eye Between Stars", "Tier V &middot; the apex; the thing that watches back", "&mdash;", 120, "it does not move; it regards", "+19", "+19", "+23",
       "to be seen by it is the harm &mdash; merely beheld, hold against the DC-25 truth or be unmade in mind",
       "<strong>It only looks.</strong> Older than the country, older than the dark, it opens somewhere in the night sky and notices you; nothing the living own can wound a thing so far and so vast.",
       "DC 25, 1d10 + Affliction (each scene under its regard)",
       "Close the sky &mdash; end the rite, the alignment, the open door that let its gaze fall here &mdash; and pray it forgets the small bright thing it saw.",
       mark="To seek its gaze, or speak to it, is +2 Mark and the beginning of the end of you."),
    lore=[
      "It is the oldest thing this book knows, older than the country, older than the dark, and it does only one thing: it looks. Somewhere in the night sky it opens &mdash; a regard, an attention, an eye between the stars &mdash; and it notices you, and the noticing is the whole of the harm. To be seen by the Eye Between Stars is to be held against a truth too vast for the mind to survive, to feel a gaze fall on you from a distance and an age that makes the whole of the living world a small bright mote, and to come apart inside under the weight of being <em>regarded</em> by it.",
      "Nothing the living own can touch it. It is too far, too vast, too old, and it does not move and does not reach &mdash; it only watches, and being watched is enough. The only thing to be done is to close the sky: end the rite, break the alignment, shut the door that drew its gaze down to this small world in the first place &mdash; and then to pray, with everything left in you, that the eye between the stars forgets the small bright thing it briefly saw, before it decides to look a little closer."],
    found="It opens in the night sky over wherever a rite, alignment, or open door has drawn its attention. It is everywhere and nowhere &mdash; a gaze from beyond the stars, falling on one small place that did something to be noticed.",
    keeper="The Eye Between Stars is the apex of the entire bestiary &mdash; the thing that cannot be fought, reached, or harmed in any way, that does nothing but <em>look</em>, and whose look is annihilating. There is no combat here in any normal sense: being under its regard inflicts an Affliction each scene, and the party's only goal is to close the sky &mdash; end the rite, break the alignment, shut the door that drew its gaze &mdash; and then hope it forgets them. This is cosmic horror in its purest, most absolute form: the party are motes, the Eye is incomprehensibly vast and old and indifferent, and survival means becoming un-noticed, not victorious. Run it as a desperate race to shut the door under a sky that's looking back, with the dread mounting each scene the gaze remains. The Mark warning is the book's most dire &mdash; to seek its gaze or speak to it is +2 Mark and 'the beginning of the end of you.' Save it for a campaign's ultimate crisis, the thing behind the things, the final door that must be closed. There is no killing it. There is only closing the sky and praying. Use it to end a campaign on the genre's truest note: humanity's whole brave struggle reduced to hoping that something vast looks away in time, and that it forgets the small bright thing it saw.")}
</section>
</section>
"""

INDEX = f"""<!-- INDEX -->
<section class="page" id="index">
  {runhead('Appendix: The Roll, by Tier')}
  <h1 class="chapter">Appendix: The Roll, by Tier</h1>
  <p class="chapter-sub">Every thing in this book, sorted by how badly it wants you.</p>
  <div class="divider"></div>
  {quote("I have arranged them by danger, as a man arranges his debts &mdash; smallest first, so as to keep his nerve.", "from the field-books of N. Ashby")}
  <p>A creature is a fair, hard fight for a party of <strong>twice its Tier</strong> in levels. Two Tiers over the
  party is a thing to run from.</p>
  <table class="lvl">
    <thead><tr><th>Tier</th><th>The Things of That Danger</th></tr></thead>
    <tbody>
      <tr><td><strong>I</strong> <span class="sub">(1st&ndash;2nd lvl)</span></td><td>The Risen, The Mummied Prospector, The Chupacabra, The Devil's Coyote, The Bonepicker, The Cold Spot, The Lantern-Light</td></tr>
      <tr><td><strong>II</strong> <span class="sub">(~4th lvl)</span></td><td>The Boneyard Host, The Gallows-Hung, The Drowned, The Cold Bride, The Plague-Dead, The Ash Child, The Restless Herd, The Pale Wolf, The Ghost Cat, The Carrion Cloud, The Razorback Shoat, The Hodag, The Pale Crawler, The Skinned Stallion, The Glutton, The Cursed Man, The Hexer, The Resurrectionist, The Wendigo-Touched, The Possessed, The Flock of the Open Eye, The Throwing Spirit, The Shadow That Lags, The Dollmaker's Children, The Hangman's Echo, The Weeping Walls, The Mourner, The Dust Devil, The Thirst, The Singing Sand, Road Agents, The Hexed Beast, The Dark Cultist</td></tr>
      <tr><td><strong>III</strong> <span class="sub">(~6th lvl)</span></td><td>The Weeping Woman, The Scalp-Taker's Ghost, The Grave-Wight, The Revenant, The Nightwalker, The Gravecaller, The Hidebehind, The Snallygaster, The Horned Serpent, The Bewitched Grizzly, The Rattlewyrm, The Skin-Walker, The Hollow Prophet, The Witch, The Hanging Judge, The Mesmerist, The Bruja, The Deathless Gun, The Tallyman, The Mirror-Dweller, The Whistler, The Hunger That Walks, The Red Wind, The White Death, The Drought-Bringer, The Whisperer's Mouth, The Crawling Congregation, The Thing in the Well, The Cold Deep's Child</td></tr>
      <tr><td><strong>IV</strong> <span class="sub">(~8th lvl)</span></td><td>The Thunderbird, The Crossroads Man, The House That Hungers, The Wendigo, The Flood-Serpent, The Stone Giant, The Servant of the Deep Dark, The Veinwork, The Pallid Herald, The Faceless Rider, The Sermon Made Flesh, The Devourer's Tongue, The Long Trail's End</td></tr>
      <tr><td><strong>V</strong> <span class="sub">(~10th lvl &amp; beyond)</span></td><td>The Star-Spawn, The Wound in the World, The Unmade, The Eye Between Stars &mdash; and the Servant of the Deep Dark, at its worst</td></tr>
    </tbody>
  </table>
  <div class="divider"></div>
  <p class="note" style="text-align:center;">Blood &amp; Grit &middot; The Bestiary &middot; Name them if you must. They already know yours.</p>
</section>
"""

GROUNDS = f"""<!-- GROUNDS -->
<section class="page" id="grounds">
  {runhead('Appendix: The Grounds')}
  <h1 class="chapter">Appendix: The Grounds</h1>
  <p class="chapter-sub">Every thing in this book, sorted by where it waits &mdash; roll or choose.</p>
  <div class="divider"></div>
  {quote("Know the country and you know the company. A river keeps different dead than a mine, and both keep better books than a bank.", "from the field-books of N. Ashby")}
  <p class="lead">The Roll sorts the country's horrors by danger; this appendix sorts them by <em>ground</em>, for the
  night the players turn their horses somewhere you haven't prepared. Roll on the table that matches the ground, or
  run a finger down it and pick. <strong>The safe-table rule:</strong> if the roll turns up a thing two or more Tiers
  above the party, it arrives as sign and spoor, not in the flesh &mdash; the tracks, the kill, the survivor's account
  &mdash; and becomes a thread instead of a funeral.</p>

  <h2>The Ordinary Country <span class="sub">(d20 &mdash; the night nothing is wrong)</span></h2>
  <p class="note">Roll here for the sessions before the horror, and for every session after one, when the table needs
  the country to be only a country again. Nothing on this table costs a point of Nerve or moves the Mark. Used for a
  month of play, it does more work than any other table in this book: it teaches the party that the frontier is
  dangerous on its own, so that the first time something is genuinely wrong, they have nowhere to file it.</p>
  <table>
    <tbody>
      <tr><td>1</td><td>The Rustlers (I)</td><td>11</td><td>The Hornet Swarm (I) &mdash; and the horses</td></tr>
      <tr><td>2</td><td>The Drunk with a Gun (I)</td><td>12</td><td>The Peccary Band (I)</td></tr>
      <tr><td>3</td><td>The Bad Water (I)</td><td>13</td><td>The Elk Bull (II) &mdash; in the rut</td></tr>
      <tr><td>4</td><td>The Prairie Dog Town (I)</td><td>14</td><td>The Horse Thieves (II)</td></tr>
      <tr><td>5</td><td>The Mad Dog (I)</td><td>15</td><td>The Lynch Mob (II)</td></tr>
      <tr><td>6</td><td>The Saloon Brawl (I)</td><td>16</td><td>The Norther (II)</td></tr>
      <tr><td>7</td><td>The Tinhorn (I)</td><td>17</td><td>The Prairie Fire (II)</td></tr>
      <tr><td>8</td><td>The Claim-Jumpers (I)</td><td>18</td><td>The Hired Gun (II)</td></tr>
      <tr><td>9</td><td>The Turkey Buzzard (I) &mdash; go and look</td><td>19</td><td>The River Crossing (III)</td></tr>
      <tr><td>10</td><td>The Skunk (I)</td><td>20</td><td>The Stock-Killer Wolf (III) &mdash; a whole season's work</td></tr>
    </tbody>
  </table>

  <h2>The Trail &amp; the Open Range <span class="sub">(d12)</span></h2>
  <table>
    <tbody>
      <tr><td>1</td><td>The Devil's Coyote (I)</td><td>7</td><td>The Glutton (II)</td></tr>
      <tr><td>2</td><td>Road Agents (I&ndash;II)</td><td>8</td><td>The Dust Devil (II)</td></tr>
      <tr><td>3</td><td>The Hexed Beast (I&ndash;II)</td><td>9</td><td>The Mourner (II) &mdash; an omen</td></tr>
      <tr><td>4</td><td>The Pale Wolf (II)</td><td>10</td><td>The Skinned Stallion (II)</td></tr>
      <tr><td>5</td><td>The Ghost Cat (II)</td><td>11</td><td>The Whistler (III)</td></tr>
      <tr><td>6</td><td>The Restless Herd (II)</td><td>12</td><td>The Faceless Rider (IV) &mdash; ruin follows</td></tr>
    </tbody>
  </table>

  <h2>Rivers, Lakes &amp; Swamps <span class="sub">(d10)</span></h2>
  <table>
    <tbody>
      <tr><td>1</td><td>The Lantern-Light (I)</td><td>6</td><td>The Cold Deep's Child (III)</td></tr>
      <tr><td>2</td><td>The Drowned (II)</td><td>7</td><td>The Thing in the Well (III)</td></tr>
      <tr><td>3</td><td>The Hodag (II)</td><td>8</td><td>The Flood-Serpent (IV)</td></tr>
      <tr><td>4</td><td>The Weeping Woman (III)</td><td>9</td><td>The Bull Gator (a living beast)</td></tr>
      <tr><td>5</td><td>The Horned Serpent (III)</td><td>10</td><td>The Old Man of the Swamp (a living beast)</td></tr>
    </tbody>
  </table>

  <h2>Towns, Homesteads &amp; Haunted Houses <span class="sub">(d12)</span></h2>
  <table>
    <tbody>
      <tr><td>1</td><td>The Cold Spot (I)</td><td>7</td><td>The Weeping Walls (II)</td></tr>
      <tr><td>2</td><td>The Chupacabra (I)</td><td>8</td><td>The Possessed (II)</td></tr>
      <tr><td>3</td><td>The Bonepicker (I)</td><td>9</td><td>The Mirror-Dweller (III)</td></tr>
      <tr><td>4</td><td>The Throwing Spirit (II)</td><td>10</td><td>The Skin-Walker (III)</td></tr>
      <tr><td>5</td><td>The Cold Bride (II)</td><td>11</td><td>The Nightwalker (III)</td></tr>
      <tr><td>6</td><td>The Dollmaker's Children (II)</td><td>12</td><td>The House That Hungers (IV)</td></tr>
    </tbody>
  </table>

  <h2>The Lamplit City <span class="sub">(d12 &mdash; Dodge, Kansas City, Frisco, Butte)</span></h2>
  <p class="note">A city is not thinner ground for the dark; it is richer. A missing stranger in a town of two hundred is
  a manhunt, and in Kansas City it is a filing. Roll here for the terminus &mdash; the yards, the quarter, the works
  below &mdash; and see the Keeper's Book, Ch. XIV, for running a night there without losing the tone.</p>
  <table>
    <tbody>
      <tr><td>1</td><td>The Saloon Brawl (I) &mdash; and a stove</td><td>7</td><td>The Possessed (II) &mdash; with standing</td></tr>
      <tr><td>2</td><td>The Bonepicker (I)</td><td>8</td><td>The Mesmerist (III) &mdash; a subscription hall</td></tr>
      <tr><td>3</td><td>The Hired Gun (II) &mdash; an agency now</td><td>9</td><td>The Skin-Walker (III) &mdash; a new face each month</td></tr>
      <tr><td>4</td><td>The Resurrectionist (II) &mdash; with a price list</td><td>10</td><td>The Nightwalker (III)</td></tr>
      <tr><td>5</td><td>The Lynch Mob (II) &mdash; a whole ward of it</td><td>11</td><td>The Tallyman (III) &mdash; he holds the paper</td></tr>
      <tr><td>6</td><td>Dark Cultist &amp; the Hollow Prophet (II) &mdash; chartered</td><td>12</td><td>The Thing in the Well (III) &mdash; the waterworks</td></tr>
    </tbody>
  </table>

  <h2>Graveyards &amp; Battlefields <span class="sub">(d10)</span></h2>
  <table>
    <tbody>
      <tr><td>1</td><td>The Risen (I)</td><td>6</td><td>The Carrion Cloud (II)</td></tr>
      <tr><td>2</td><td>The Gallows-Hung (II)</td><td>7</td><td>The Grave-Wight (III)</td></tr>
      <tr><td>3</td><td>The Plague-Dead (II)</td><td>8</td><td>The Gravecaller (III)</td></tr>
      <tr><td>4</td><td>The Boneyard Host (II)</td><td>9</td><td>The Revenant (III)</td></tr>
      <tr><td>5</td><td>The Hangman's Echo (II)</td><td>10</td><td>The Scalp-Taker's Ghost (III)</td></tr>
    </tbody>
  </table>

  <h2>Mines &amp; Under the Earth <span class="sub">(d8)</span></h2>
  <table>
    <tbody>
      <tr><td>1</td><td>The Mummied Prospector (I)</td><td>5</td><td>The Thing in the Well (III)</td></tr>
      <tr><td>2</td><td>The Pale Crawler (II)</td><td>6</td><td>The Veinwork (IV)</td></tr>
      <tr><td>3</td><td>The Rattlewyrm (III)</td><td>7</td><td>The Devourer's Tongue (IV)</td></tr>
      <tr><td>4</td><td>The Grave-Wight (III)</td><td>8</td><td>The Stone Giant (IV)</td></tr>
    </tbody>
  </table>

  <h2>Winter &amp; the High Country <span class="sub">(d10)</span></h2>
  <table>
    <tbody>
      <tr><td>1</td><td>The Wolf Pack (a living beast)</td><td>6</td><td>The Bewitched Grizzly (III)</td></tr>
      <tr><td>2</td><td>The Wendigo-Touched (II)</td><td>7</td><td>The Snallygaster (III)</td></tr>
      <tr><td>3</td><td>The Glutton (II)</td><td>8</td><td>The Thunderbird (IV)</td></tr>
      <tr><td>4</td><td>The White Death (III)</td><td>9</td><td>The Stone Giant (IV)</td></tr>
      <tr><td>5</td><td>The Hunger That Walks (III)</td><td>10</td><td>The Wendigo (IV)</td></tr>
    </tbody>
  </table>

  <h2>Desert &amp; the Badlands <span class="sub">(d10)</span></h2>
  <table>
    <tbody>
      <tr><td>1</td><td>The Rattlesnake (a living beast)</td><td>6</td><td>The Singing Sand (II)</td></tr>
      <tr><td>2</td><td>The Devil's Coyote (I)</td><td>7</td><td>The Rattlewyrm (III)</td></tr>
      <tr><td>3</td><td>The Chupacabra (I)</td><td>8</td><td>The Bruja (III)</td></tr>
      <tr><td>4</td><td>The Dust Devil (II)</td><td>9</td><td>The Red Wind (III)</td></tr>
      <tr><td>5</td><td>The Thirst (II)</td><td>10</td><td>The Great Serpent (a living beast)</td></tr>
    </tbody>
  </table>

  <h2>The Old Places <span class="sub">(d8 &mdash; tread carefully)</span></h2>
  <table>
    <tbody>
      <tr><td>1</td><td>The Whisperer's Mouth (III)</td><td>5</td><td>Servant of the Deep Dark (IV&ndash;V)</td></tr>
      <tr><td>2</td><td>The Crawling Congregation (III)</td><td>6</td><td>The Star-Spawn (V)</td></tr>
      <tr><td>3</td><td>The Cold Deep's Child (III)</td><td>7</td><td>The Wound in the World (V)</td></tr>
      <tr><td>4</td><td>The Pallid Herald (IV)</td><td>8</td><td>The Unmade (V)</td></tr>
    </tbody>
  </table>
  <p class="note">On the old ground, the safe-table rule is not a suggestion. Most of what this table turns up should
  arrive as evidence and dread long before it arrives in person.</p>

  <h2>The Hand Behind It <span class="sub">(d10 &mdash; when the mystery needs an author)</span></h2>
  <p>Half this book's horrors were <em>sent</em>. When the players ask who is behind the trouble, roll or choose:</p>
  <table>
    <tbody>
      <tr><td>1</td><td>The Hexer (II) &mdash; hired, and in over his head</td><td>6</td><td>The Hanging Judge (III) &mdash; the law itself, dead and wrong</td></tr>
      <tr><td>2</td><td>The Resurrectionist (II) &mdash; a trade in the dead</td><td>7</td><td>The Bruja (III) &mdash; the night roads are hers</td></tr>
      <tr><td>3</td><td>The Witch (II&ndash;III) &mdash; an old slight, patiently repaid</td><td>8</td><td>The Deathless Gun (III) &mdash; a bargain still being spent</td></tr>
      <tr><td>4</td><td>The Mesmerist (III) &mdash; other people's hands</td><td>9</td><td>The Tallyman (III) &mdash; a debt come due</td></tr>
      <tr><td>5</td><td>Dark Cultist &amp; the Hollow Prophet (II&ndash;III)</td><td>10</td><td>The Crossroads Man (IV) &mdash; somebody dealt, and lost</td></tr>
    </tbody>
  </table>
</section>
"""

BUILD = f"""<!-- BUILD -->
<section class="page" id="build">
  {runhead('Appendix: Building Your Own Dead')}
  <h1 class="chapter">Appendix: Building Your Own Dead</h1>
  <p class="chapter-sub">The whole workshop on two pages, so this book need never leave your hands.</p>
  <div class="divider"></div>
  {quote("Any fool can invent a monster. The craft is inventing the way it dies.", "from the field-books of N. Ashby")}
  <p class="lead">Chapter I taught you to bend these entries; this page is for building fresh. A new horror needs five
  parts, and the numbers are the least of them. Work the list in order and you will have a creature worthy of the
  country in a quarter hour.</p>

  <h2>The Anatomy of an Entry</h2>
  <ul>
    <li><strong>1. The wrong at its root.</strong> Every horror here was made by something &mdash; a murder, a bargain,
    a greed, a grief. Name the wrong first; it will hand you the lore, the ground, and usually the weakness.</li>
    <li><strong>2. The ground it keeps.</strong> Where is it found, and when? A monster with an address is a mystery
    the players can solve; one that appears anywhere is only an ambush.</li>
    <li><strong>3. The numbers, off the shelf.</strong> Pick its Tier and read the row below. Do not agonize; the row
    is balanced and the fiction does the rest.</li>
    <li><strong>4. One Special.</strong> A single signature trick that makes it more than its row &mdash; the thing the
    players will name it by. One. A monster with five tricks is a puzzle with no answer.</li>
    <li><strong>5. Putting It Down.</strong> The secret. It should be discoverable in play (the lore, the locals, the
    pattern of its kills all point to it), it should ask more than damage &mdash; a place, a truth, a rite, a mercy
    &mdash; and the gun alone should never be the whole answer above Tier I.</li>
  </ul>

  <h2>Threat by Tier</h2>
  <p>A creature is a fair, hard fight for a party of <strong>twice its Tier</strong> in levels.</p>
  <table class="lvl">
    <thead><tr><th>Tier</th><th>Defense</th><th>Attack</th><th>Blood</th><th>Saves (high/low)</th><th>Damage</th><th>Dread DC</th></tr></thead>
    <tbody>
      <tr><td><strong>I</strong></td><td>13</td><td>+4</td><td>12</td><td>+6 / +2</td><td>1d6+2</td><td>&mdash; / 10&ndash;13</td></tr>
      <tr><td><strong>II</strong></td><td>15</td><td>+6</td><td>22</td><td>+8 / +3</td><td>1d8+3</td><td>13</td></tr>
      <tr><td><strong>III</strong></td><td>17</td><td>+9</td><td>40</td><td>+11 / +5</td><td>2d6+4</td><td>16</td></tr>
      <tr><td><strong>IV</strong></td><td>20</td><td>+13</td><td>70</td><td>+15 / +8</td><td>2d8+6</td><td>20</td></tr>
      <tr><td><strong>V</strong></td><td>23</td><td>+17</td><td>110</td><td>+19 / +11</td><td>3d8+8</td><td>25</td></tr>
    </tbody>
  </table>
  <p><strong>The encounter budget:</strong> 4 points per player character. An even-Tier foe costs 4; a mook (a Tier
  or two down, dies to a solid hit) costs 1; a standout (a Tier up, or a Lieutenant from Chapter I) costs 8. Spend the
  budget and the fight is fair; overspend and you had better mean it.</p>

  <h2>The House Rules of the Dead</h2>
  <ul>
    <li><strong>Dread follows Tier.</strong> DC 10&ndash;13 for the unsettling, 16 for the terrible, 20 for the
    wrong, 25 for the things not meant to be beheld. Nerve lost runs 1, 1d4, 1d6, 1d10 up the same ladder.</li>
    <li><strong>The Mark is for choices.</strong> A creature moves the Mark only when a soul <em>chooses</em> its
    power &mdash; a bargain, a rite, a heeding. Never for a bad roll, never for merely being wounded.</li>
    <li><strong>Honest animals stay honest.</strong> An ordinary beast costs no Nerve and never moves the Mark, no
    matter how big you make it. The moment it does either, it belongs in an earlier chapter of this book, and it
    should have a wrong at its root.</li>
    <li><strong>Familiarity is the death of dread.</strong> The second meeting with any horror costs no Dread Check
    for the same sight &mdash; so escalate: a new behavior, a new ground, a new face. Or reskin (Chapter I) and let
    them start over.</li>
  </ul>
  <div class="keeper-note"><span class="kn-tag">The quarter-hour monster</span>Name the wrong. Pick the ground. Read
  the Tier row. Give it one trick and one true death. Write the Found line and two sentences of what the locals say.
  Done &mdash; and if the table loves it, this book has a blank page at the back that is not blank by accident.</div>
</section>
"""

# ===========================================================================
# The 25 ordinary beasts, the per-section tier/name sorter, and the generated
# Roll-by-Tier appendix (formerly bestiary_extra.py, merged 2026-07-18).
# ===========================================================================
# Bestiary additions: 25 ordinary (natural) beasts as a new section, plus a
# build-time pass that sorts every creature section by (tier asc, name asc) and
# regenerates the appendix index from the actual stat blocks (so it never drifts).
import re
from collections import defaultdict

ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}


def primary_tier(tier_str):
    head = tier_str.split("&middot;")[0]
    romans = re.findall(r'\b(I|II|III|IV|V)\b', head)
    return ROMAN[romans[0]] if romans else 9


def name_key(name_html):
    t = re.sub(r'<[^>]+>', '', name_html)
    t = (t.replace('&amp;', '&').replace('&mdash;', '-')
           .replace('&ndash;', '-').replace('&rsquo;', "'").replace('&middot;', ' '))
    t = re.sub(r"^(the|a|an)\s+", "", t.strip(), flags=re.I)
    return t.lower()


def _spans_for_marker(s, marker):
    """Return (start,end) spans of top-level divs opened by `marker` (depth-matched)."""
    spans = []
    i = 0
    while True:
        st = s.find(marker, i)
        if st == -1:
            break
        depth = 0
        j = st
        while j < len(s):
            if s.startswith('<div', j):
                depth += 1
                j += 4
            elif s.startswith('</div>', j):
                depth -= 1
                j += 6
                if depth == 0:
                    break
            else:
                j += 1
        spans.append((st, j))
        i = j
    return spans


def extract_statblocks(s):
    """Return (start,end) spans of each creature unit, depth-matched.

    A creature unit is a top-level <div class="creature"> wrapper when present
    (it carries the lore + stat block + keeper note as one sortable unit); the
    function falls back to bare <div class="statblock"> for any creature that
    has not yet been wrapped. The two never overlap because a wrapped stat block
    lives *inside* its wrapper, so we exclude bare blocks that fall within a
    wrapper's span.
    """
    wrappers = _spans_for_marker(s, '<div class="creature">')
    bare = _spans_for_marker(s, '<div class="statblock">')

    def inside_wrapper(st):
        return any(w0 <= st < w1 for (w0, w1) in wrappers)

    spans = list(wrappers) + [(st, en) for (st, en) in bare if not inside_wrapper(st)]
    spans.sort()
    return spans


def sort_sections(body, ids):
    for sid in ids:
        m = re.search(r'(<section class="page" id="' + sid + r'">)(.*?)(</section>)', body, re.S)
        if not m:
            continue
        inner = m.group(2)
        spans = extract_statblocks(inner)
        if not spans:
            continue
        first, last = spans[0][0], spans[-1][1]
        prefix, middle, suffix = inner[:first], inner[first:last], inner[last:]
        items, leftover = [], middle
        for (st, en) in spans:
            blk = inner[st:en]
            leftover = leftover.replace(blk, "", 1)
            tier = re.search(r'<span class="sb-tier">(.*?)</span>', blk, re.S).group(1)
            name = re.search(r'<span class="sb-name">(.*?)</span>', blk, re.S).group(1)
            items.append((primary_tier(tier), name_key(name), blk))
        assert leftover.strip() == "", f"section {sid}: non-statblock content between creatures: {leftover.strip()[:80]!r}"
        items.sort(key=lambda x: (x[0], x[1]))
        new_inner = prefix + "\n  ".join(b for *_, b in items) + suffix
        body = body[:m.start()] + m.group(1) + new_inner + m.group(3) + body[m.end():]
    return body


def gen_appendix(body, ids):
    tiers = defaultdict(list)
    for sid in ids:
        m = re.search(r'<section class="page" id="' + sid + r'">(.*?)</section>', body, re.S)
        if not m:
            continue
        inner = m.group(1)
        for (st, en) in extract_statblocks(inner):
            blk = inner[st:en]
            tier_str = re.search(r'<span class="sb-tier">(.*?)</span>', blk, re.S).group(1)
            name = re.search(r'<span class="sb-name">(.*?)</span>', blk, re.S).group(1)
            head = tier_str.split("&middot;")[0]
            romans = re.findall(r'\b(I|II|III|IV|V)\b', head)
            if not romans:
                continue
            if '/' in head:  # dual stat block (e.g. flock / prophet): list in each tier
                for r in dict.fromkeys(romans):
                    tiers[ROMAN[r]].append(name)
            else:            # single or range: place at its lowest (first) tier
                tiers[ROMAN[romans[0]]].append(name)
    sub = {1: "(1st&ndash;2nd lvl)", 2: "(~4th lvl)", 3: "(~6th lvl)",
           4: "(~8th lvl)", 5: "(~10th lvl &amp; beyond)"}
    lbl = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}
    rows = []
    for t in (1, 2, 3, 4, 5):
        names = sorted(dict.fromkeys(tiers[t]), key=name_key)
        rows.append(f'      <tr><td><strong>{lbl[t]}</strong> <span class="sub">{sub[t]}</span></td>'
                    f'<td>{", ".join(names)}</td></tr>')
    new_tbody = "<tbody>\n" + "\n".join(rows) + "\n    </tbody>"
    m = re.search(r'(<section class="page" id="index">.*?)<tbody>.*?</tbody>(.*?</section>)', body, re.S)
    return body[:m.start()] + m.group(1) + new_tbody + m.group(2) + body[m.end():]


# ---- 25 ordinary beasts, 5 per tier. sb signature:
# (name, tier, defense, blood, speed, fort, ref, will, attacks, special, dread, down)
N = "&mdash;"
LIVING_CREATURES = [
    # ---- Tier I ----
    ("The Coyote", "Tier I &middot; the trickster of the waking world", 14, 10, "very fast", "+5", "+8", "+2",
     "bite +5 (1d6+1)",
     "<strong>Wary and clever.</strong> Hunts the lone and the weak; a few will harry but rarely commit, and all break for the dark the moment a gun speaks true.",
     N, "It is a coyote. A shot, a shout, or a fire turns it; only hunger or madness makes one truly press a man."),
    ("The Rattlesnake", "Tier I &middot; the coil in the dust", 13, 8, "slow; strikes a blur", "+5", "+7", "+0",
     "bite +6 (1d4 plus venom: Fort DC 13 or 1d6 and sickened a day)",
     "<strong>Venom.</strong> It would as soon be left alone and rattles to say so; step wrong and it answers from arm's length before the eye can follow.",
     N, "Watch the ground and the warm rocks. A hoe, a heel, or a load of shot &mdash; and carry a remedy for the bitten."),
    ("The Badger", "Tier I &middot; a low temper in a hole", 14, 12, "slow; burrows", "+7", "+4", "+1",
     "claws &amp; bite +5 (1d6+2)",
     "<strong>Will not quit.</strong> Cornered or dug at, it fights with a fury far past its size and does not flee, yield, or learn fear.",
     N, "Leave it be and it leaves you. If it must die it will make you spend for it &mdash; many guns, or none."),
    ("The Bobcat", "Tier I &middot; the small cat that waits above", 15, 9, "fast; leaps; climbs", "+5", "+8", "+2",
     "claws +5 (1d6+1, rake)",
     "<strong>Ambush.</strong> Drops from a ledge or a limb onto the straggler; the first strike from hiding lands with a vengeance, and then it is simply gone.",
     N, "It rarely presses a fight it cannot win; one hard answer and it quits the field."),
    ("The Stray Pack", "Tier I &middot; dogs gone back to the wild", 13, 12, "fast", "+6", "+6", "+2",
     "bite +4 (1d6+1, drag down)",
     "<strong>Pack.</strong> Surrounds a lone traveler and pulls him down by weight and number; bolder than wolves, for they have lost their fear of men.",
     N, "Drop the boldest and the rest remember they are only dogs; fire and a raised voice scatter them."),
    # ---- Tier II ----
    ("The Gray Wolf", "Tier II &middot; the hunter of the long winter", 15, 20, "very fast", "+8", "+8", "+3",
     "bite +6 (1d8+3, trip)",
     "<strong>Pack hunter.</strong> Harries, hamstrings, and waits; a lone wolf weighs the odds and slips away, but a pack in a hard winter does not.",
     N, "Fire and a steady gun earn its respect; break the pack's nerve and the rest follow the leader off into the trees."),
    ("The Mountain Lion", "Tier II &middot; the cat you never see", 17, 18, "very fast; leaps far", "+7", "+9", "+3",
     "pounce +6 (1d8+3, knocks prone, then rake)",
     "<strong>Silent ambush.</strong> Takes the last man in line from above or behind, drops him, and is at his throat before the others can turn.",
     N, "Stay together and watch the high rocks. It hunts the straggler; deny it one and it goes hungry."),
    ("The Wild Boar", "Tier II &middot; the razorback out of the bottoms", 16, 26, "fast", "+9", "+5", "+2",
     "tusks +6 (1d8+3, gore)",
     "<strong>Charge.</strong> Comes head-down and does not feel the first wound; a hide like a plank turns light shot, and a temper that turns toward the gun, not from it.",
     N, "A tree, a high seat, or a heavy ball square in the shoulder. Do not let it close, and do not wound it by halves."),
    ("The Black Bear", "Tier II &middot; the raider of the camp", 15, 24, "fast; climbs", "+8", "+5", "+3",
     "claws +6 (1d8+3)",
     "<strong>Mostly wants your supper.</strong> Bluster and noise usually turn it &mdash; unless it is cornered, starving, or a sow with you between her and the cubs, and then it is all teeth.",
     N, "Make yourself big and loud and it likely quits. Never step between sow and cub; that bear has no quit in it."),
    ("The Range Bull", "Tier II &middot; a ton of bad temper", 14, 28, "fast in a charge", "+9", "+4", "+2",
     "horns +6 (1d8+4, toss)",
     "<strong>Charge and trample.</strong> A longhorn that has decided he hates you; gores, tosses, and comes around for another pass while you are still in the dirt.",
     N, "The fence, the gate, a fast horse, or a red rag thrown wide &mdash; or drop him where he stands, which is a great deal of dropping."),
    # ---- Tier III ----
    ("The Grizzly Bear", "Tier III &middot; the lord of the high country", 17, 44, "fast (briefly, faster than a horse)", "+11", "+5", "+4",
     "claws +9 (2d6+4; a hit rakes with both)",
     "<strong>Takes the lead and keeps coming.</strong> Shrugs off the first solid wound, runs down a fleeing man over short ground, and does not stop for pain.",
     N, "It takes more lead than seems possible &mdash; aim true behind the shoulder. A tree is no help; a grizzly will simply wait you out."),
    ("The Bison Bull", "Tier III &middot; a hill of muscle and horn", 16, 48, "very fast in a straight line", "+13", "+4", "+4",
     "horns &amp; trample +9 (2d6+5)",
     "<strong>Unstoppable in a line.</strong> A ton and a half at a dead run; it neither swerves nor tires before you do.",
     N, "A big-bore rifle behind the shoulder &mdash; or simply not be where it is going. Turning it is easier than killing it."),
    ("The Bull Gator", "Tier III &middot; the log that was not a log", 18, 42, "slow on land; fast in water", "+11", "+6", "+4",
     "bite +9 (2d6+4, grab and roll under)",
     "<strong>Death roll.</strong> Explodes from the shallows, clamps on, and rolls to drown and dismember; on its own water, nothing the frontier owns can hold it.",
     N, "Stay back from the cut bank and the still water. The eye and the soft of the throat &mdash; and never wade where one might wait."),
    ("The Wolf Pack", "Tier III &middot; the winter pack, of one mind", 16, 40, "very fast", "+10", "+9", "+4",
     "bite +9 (2d6+4, all who stand close)",
     "<strong>Run as one (a swarm).</strong> A single pool of Blood and a single will; it surrounds, drags down, and thins as it bleeds rather than dropping man by man.",
     N, "You cannot kill a pack a wolf at a time. Fire, high ground, and breaking their nerve &mdash; take the leader and the rest may scatter."),
    ("The Bull Moose", "Tier III &middot; a thousand pounds in a foul mood", 16, 46, "fast", "+12", "+5", "+3",
     "antlers &amp; hooves +9 (2d6+4, trample)",
     "<strong>Fears nothing in the rut.</strong> Charges horse, man, or locomotive without a second thought; enormous, untroubled by a wound, and quick for its size.",
     N, "Give it the road and the right of way. It tires of you sooner than you tire of it &mdash; if you live the first charge."),
    # ---- Tier IV ----
    ("The Great Bear", "Tier IV &middot; the man-killer of legend", 20, 72, "fast", "+15", "+8", "+8",
     "claws &amp; bite +13 (2d8+6; the hit rakes twice)",
     "<strong>Has learned men.</strong> Wears the scars of every gun that failed to stop it; a wound only makes it worse, and it has killed enough hunters to be careful, and cruel.",
     N, "It has survived a dozen hunts. It takes a small army or one perfect shot; men have spent their whole lives, and their lives, on less."),
    ("The Stampede", "Tier IV &middot; the herd, run as a wall", 18, 70, "very fast", "+15", "+6", "+6",
     "trample +13 (2d8+6, everything in the lane)",
     "<strong>A flood with hooves.</strong> A moving wall of the herd that cannot be reasoned with or fought, only outrun, turned, or survived; it fills the draw and takes all within it.",
     N, "You do not kill a stampede. Ride out of the lane, gain high ground, or turn the lead with fire &mdash; and pray the ground is not a box canyon."),
    ("The Man-Eater", "Tier IV &middot; the cat that learned to hunt men", 20, 64, "very fast; leaps", "+13", "+13", "+7",
     "pounce +13 (2d8+6, drops and pins)",
     "<strong>Hunts you in turn.</strong> Takes the sentry and the straggler by night, patient and learned; never seen until it strikes, and it never strikes a fair fight.",
     N, "It must be hunted as it hunts &mdash; with bait, patience, and an iron nerve. Stand watch in pairs, and never sleep where it can come from above."),
    ("The Old Tusker", "Tier IV &middot; the boar that breaks the dogs", 19, 74, "fast", "+15", "+7", "+6",
     "tusks +13 (2d8+6, gore and throw)",
     "<strong>A hide like a plank, a temper like the devil.</strong> Has broken dogs, horses, and the men on them; charges clean through what would stop anything smaller and comes back for the rest.",
     N, "Men hunt it for years and bury friends doing it. A tree, a wall, and a heavy enough ball &mdash; and never on foot in the open."),
    ("The Pale Stallion", "Tier IV &middot; the wild horse no man rides", 20, 66, "very fast", "+13", "+13", "+8",
     "hooves &amp; teeth +13 (2d8+6, strike and trample)",
     "<strong>Suffers no rider.</strong> Leads its band and kills to keep it; strikes with hooves and teeth, runs men down, and is as cunning as any outlaw and twice as proud.",
     N, "It cannot be broken, only outlasted or shot, and many a wrangler has died learning which. Cut it from the band first, if you can."),
    # ---- Tier V ----
    ("The Mountain That Walks", "Tier V &middot; the primeval bear of the old tales", 23, 112, "fast", "+19", "+11", "+11",
     "claws &amp; bite +17 (3d8+8; rakes twice and seizes)",
     "<strong>Bigger than a bear has the right to be.</strong> The high-country legend made flesh; it takes wounds the way a hillside takes rain, and has outlived every hunter ever sent for it.",
     N, "A thing out of the grandfather-tales. It will take everything you brought and everything you are &mdash; and may yet walk away."),
    ("The White Bison", "Tier V &middot; the great pale buffalo, omen and terror", 22, 108, "very fast", "+19", "+11", "+12",
     "horns &amp; trample +17 (3d8+8)",
     "<strong>Sacred and cursed both.</strong> Huge beyond reason; the people count it holy and the hunters count it doom, and the herd follows where it leads &mdash; a thousand head at its back.",
     N, "Many will tell you it must not be killed at all. If you must, it is a mountain of muscle and wrath, and the herd behind it is the rest of your trouble."),
    ("The Great Serpent", "Tier V &middot; the snake grown long as a wagon-train", 21, 100, "fast; burrows", "+18", "+13", "+9",
     "bite +17 (3d8+8 plus venom: Fort DC 18 or 2d6 and weakened)",
     "<strong>Long as a fence-line, thick as a barrel.</strong> Strikes from the dust with the reach of a tall man and more; its venom answers to no remedy the frontier carries.",
     N, "Keep to high rock and open ground where you can see it come. The head must be taken &mdash; and getting close enough is the whole of the danger."),
    ("The Carcajou", "Tier V &middot; the devil-bear of the north woods", 22, 104, "fast; climbs; tireless", "+18", "+12", "+10",
     "claws &amp; bite +17 (3d8+8; never lets go)",
     "<strong>The wolverine of legend, grown vast.</strong> Drives bears off their kills, fears nothing that lives, and pursues a grudge for days without rest or quit.",
     N, "It does not stop and it does not tire. You cannot outlast it; you must end it all at once, or keep moving until one of you is dead."),
    ("The Old Man of the Swamp", "Tier V &middot; the gator that owns the bayou", 23, 110, "slow on land; fast in black water", "+19", "+10", "+10",
     "bite +17 (3d8+8, takes a horse under whole)",
     "<strong>Older than the parish.</strong> Longer than a flatboat and patient as the tide; it takes a man or a mount under without a ripple, and the water is all its own.",
     N, "The black water is its kingdom and your grave. Draw it onto dry land or never face it at all; in the water you will simply be gone."),
    # ---- Tier I, second rank: the small country, which does most of the killing ----
    ("The Mad Dog", "Tier I &middot; the hydrophobia, walking", 13, 10, "fast; crooked and tireless", "+6", "+5", "&mdash;",
     "bite +5 (1d6+2, and Fort DC 15 or take the hydrophobia)",
     "<strong>The bite that kills late.</strong> Runs a straight line at whatever moves, jaws working on nothing, and cannot be called off, bought off, or frightened. A man it opens walks away fine, and stays fine for a month, and then the water starts to frighten him.",
     N, "Shoot it at distance and burn the carcass. Then watch every man and every animal it touched, and know what you will have to do."),
    ("The Skunk", "Tier I &middot; a small argument you have already lost", 14, 5, "slow", "+4", "+6", "+1",
     "spray +7 (no Blood; Fort DC 13 or blinded a minute and sickened a day)",
     "<strong>Warns you twice.</strong> Stamps its front feet, then raises the tail, and a man with any sense takes both hints; the range is longer than anyone expects and the effect outlasts the week.",
     N, "Nothing needs putting down here. Back away slow, and if you were slower than that, bury the clothes."),
    ("The Peccary Band", "Tier I &middot; javelinas out of the thicket", 14, 16, "fast", "+6", "+6", "+1",
     "tusks +5 (1d6+2, everyone standing close)",
     "<strong>Poor eyes, bad tempers, and a dozen of them.</strong> A band feeds shoulder to shoulder in heavy brush and cannot tell a man from a bear at ten feet; startled, it scatters straight through whatever is standing there, cutting as it goes.",
     N, "Get behind something or get above something. They mean to be elsewhere; the wounds are what they leave on the way."),
    ("The Gila Monster", "Tier I &middot; the beaded lizard that will not let go", 15, 8, "very slow", "+6", "+2", "+2",
     "bite +5 (1d4 and holds; venom Fort DC 13 or 1d6 and sickened a day)",
     "<strong>Chews, and keeps chewing.</strong> Slow enough that only a careless hand ever meets one, and once it has that hand it locks on and works the venom in rather than striking and letting go.",
     N, "Prying the jaws takes a knife blade and patience. It never chased anybody in its life &mdash; watch where you reach in rock country."),
    ("The Hornet Swarm", "Tier I &middot; the ground nest you just stepped on", 16, 9, "fast; flies", "+3", "+9", "&mdash;",
     "stings +6 (1d6, everyone within reach, again each round they stay)",
     "<strong>The horses go first.</strong> A nest in a stump or a bank empties in a heartbeat, and a stung horse does not care what the rider wants; more men are hurt by the bolting than by the stinging.",
     N, "Run, and keep running further than feels necessary. Smoke clears a nest at night; nothing clears one at noon."),
    ("The Prairie Dog Town", "Tier I &middot; a half-mile of broken legs", "&mdash;", "&mdash;", "still; and it waits", "&mdash;", "&mdash;", "&mdash;",
     "the hole underfoot +5 against anything at a run (rider thrown for 2d6; the horse's leg usually ends the horse)",
     "<strong>Ground, not an animal.</strong> Thousands of burrows worked into good grass, invisible from the saddle at any speed worth riding; the little dogs themselves are harmless and the town they built is not.",
     N, "You do not put down a prairie-dog town. Walk the horses through it, or ride around and lose the hour."),
    ("The Turkey Buzzard", "Tier I &middot; the bird that finds the dead first", 13, 6, "clumsy afoot; tireless aloft", "+4", "+6", "+1",
     "beak +2 (1d3, and only if you corner it)",
     "<strong>Reads the country for you.</strong> Has no interest in a fight and none in a living man; a wheel of them turning slow over a far ridge is the plainest message the frontier sends, always about something already finished.",
     N, "Leave it to its work. Killing one tells you nothing and costs you the next message it would have carried."),
    ("The Porcupine", "Tier I &middot; slow trouble in the low branches", 12, 10, "slow; climbs", "+6", "+2", "+1",
     "quills (no attack of its own; anything that closes takes 1d6 and a bad evening)",
     "<strong>Punishes the curious.</strong> Waddles off with its back turned and its business plain, and asks nothing except distance; a dog that has never met one learns in a single lunge and remembers for life.",
     N, "Tie the dogs. Pulling quills takes pliers, a firm hand, and somebody sitting on the animal."),
    # ---- Tier II, second rank ----
    ("The Elk Bull", "Tier II &middot; seven hundred pounds in the rut", 15, 24, "fast", "+9", "+6", "+3",
     "antlers +6 (1d8+3, and drives you back a rod)",
     "<strong>Out of his right mind till the snow.</strong> Bugling, sleepless, and looking for something to fight; through the rut he will take on a horse, a wagon, or a man who happened to be standing in the wrong meadow.",
     N, "Give him the meadow. He is defending a harem you cannot see, and he will quit the moment you are plainly gone from it."),
    ("The Wolverine", "Tier II &middot; the small devil of the deep snow", 16, 20, "fast; climbs; tireless", "+9", "+7", "+4",
     "claws &amp; bite +6 (1d8+3, worries the wound)",
     "<strong>Drives bears off a kill.</strong> Forty pounds that has never once counted the odds; it robs traplines, tears into a cabin's stores, and answers a threat by coming straight at it, snarling, and staying.",
     N, "Everything about it is out of proportion but its size. Give it the carcass; the carcass is cheaper than the fight."),
    ("The Water Moccasin", "Tier II &middot; the snake that comes toward you", 15, 14, "slow; swims well", "+7", "+6", "+1",
     "bite +6 (1d6+2 plus venom: Fort DC 14 or 2d6 and the flesh goes bad)",
     "<strong>Holds its ground, and then some.</strong> Stands with its white mouth open instead of fleeing, and has been known to swim a deliberate line at a wading man; the venom rots what it touches and a bad bite costs a hand or a foot.",
     N, "Stay out of the still water and off the log you meant to sit on. Get the bitten man to a doctor while the arm is still worth saving."),
    ("The Golden Eagle", "Tier II &middot; the shadow that takes the lamb", 17, 16, "slow afoot; very fast in a stoop", "+6", "+10", "+3",
     "talons +6 (1d8+3 from a stoop, and it does not come back for a second pass)",
     "<strong>Comes down out of the sun.</strong> Takes lambs, kids, and the occasional dog off open ground at a speed that leaves the herder with nothing to shoot at; it will strike a man only to drive him off a nest.",
     N, "It wants the stock and not the shepherd. Watch the sky over a lambing ground, and keep the young ones under something."),
    ("The Feral Horse Band", "Tier II &middot; the mustangs, and the stallion who runs them", 15, 26, "very fast", "+8", "+9", "+3",
     "hooves &amp; teeth +6 (1d8+3; the band tramples what the stallion knocks down)",
     "<strong>Takes your horses with it.</strong> The stallion cuts saddle stock out of a picket line and runs it off with his mares, and a party that argues about it gets caught in forty head turning at once.",
     N, "Hobble everything and stand a watch. Losing the fight to a wild band is survivable; losing the horses in that country is often not."),
    ("The Rutting Buck", "Tier II &middot; the deer that buries more men than the bear", 16, 18, "very fast", "+7", "+9", "+2",
     "antlers +6 (1d8+3, and hooks upward)",
     "<strong>The animal nobody respects.</strong> Two hundred pounds of muscle behind a rack of points, in the season when it has stopped being careful; men who would never walk up on a bear walk up on a downed buck every autumn, and some of them do not walk back.",
     N, "Never approach one that is down until it has been down a while. A buck that seems finished has killed a great many hunters who agreed."),
    ("The Sow and Cubs", "Tier II &middot; the one bear with no quit in it", 16, 26, "fast; climbs", "+9", "+6", "+4",
     "claws +6 (1d8+3, and she does not stop at driving you off)",
     "<strong>No bluff in her at all.</strong> An ordinary black bear will bluster and leave; a sow who believes you are between her and the cubs commits at once, presses past wounds that would turn any other bear, and follows you as far as it takes.",
     N, "Back out the way you came the second you hear a cub. Do not run, do not climb, and never put yourself uphill of the noise."),
    # ---- Tier III, second rank ----
    ("The Boar Sounder", "Tier III &middot; the whole family, in heavy brush", 17, 42, "fast", "+11", "+6", "+3",
     "tusks +9 (2d6+4, from three directions at once)",
     "<strong>Twenty of them, and they know the thicket.</strong> Sows, shoats, and a pair of old boars moving as one through cover a man cannot see ten feet into; they cut, wheel, and come back, and there is no high ground in a bottom.",
     N, "The thicket is the whole problem. Get to open country or a tree; fighting a sounder in its own brush is how the dogs die and then the men."),
    ("The Snake Den", "Tier III &middot; the winter den, opened", 15, 38, "slow; the ground moves", "+9", "+8", "&mdash;",
     "bites +9 (2d6+4 to everyone in the rocks, plus venom: Fort DC 16 or 2d6 and sickened a week)",
     "<strong>A hundred of them in one hole.</strong> Rattlers winter together in the deep rock by the score, and a man who breaks into that in a cold spring finds the whole floor of the place alive and slow and thoroughly annoyed.",
     N, "Get out the way you came in, one careful step at a time. Nobody has ever won this by fighting; count the bitten and start riding."),
    ("The Wild Cattle of the Brasada", "Tier III &middot; the ladinos of the brush country", 17, 44, "fast in cover", "+11", "+6", "+3",
     "horns +9 (2d6+4, gore and toss)",
     "<strong>Cattle that went wild and got clever.</strong> Longhorns bred out of strays in the thorn brush, nocturnal, six feet of horn wide, and possessed of a genuine hatred for horses and the men on them; they lie up in the thickets by day and charge anything that comes in after them.",
     N, "Men rope these out of the brasada for money and count the broken bones as part of the wage. Take them at night on open ground, or leave them the brush."),
    ("The Longhorn Herd", "Tier III &middot; three thousand head, and one bad noise", 16, 46, "fast, and all together", "+12", "+5", "+2",
     "the press +9 (2d6+4 to whatever is caught among them)",
     "<strong>Not yet a stampede &mdash; and one lightning-crack from it.</strong> A trail herd bedded down is a hill of nerves; it mills, drifts, and swallows a man on foot without ever meaning to, and everything the outfit does at night is done to keep it from becoming the other thing.",
     N, "Ride the circle and sing to them, which is what the singing was always for &mdash; and on most outfits the hand who taught the rest of them how is the segundo. Once it breaks, see The Stampede, and pray for room."),
    ("The Stock-Killer Wolf", "Tier III &middot; the wolf with a name and a price on it", 18, 36, "very fast; tireless", "+10", "+11", "+6",
     "bite +9 (2d6+4, throat and hamstring)",
     "<strong>Has beaten every man sent for it.</strong> One old wolf, usually running alone or with a single mate, that kills far past hunger &mdash; a dozen head in a night, left where they dropped. It springs traps with a stick, refuses poisoned bait, and knows the range better than the ranch does.",
     N, "It cannot be trapped by anyone it has already outsmarted, which by now is everyone. Take the mate first; grief makes it careless, and that is the only opening it has ever given."),
]


def build_living(sb, runhead, quote, creature):
    blocks_list = []
    for c in LIVING_CREATURES:
        stat = sb(*c)
        lore, found = LIVING_LORE.get(c[0], ("", ""))
        if lore:
            blocks_list.append(creature(stat, lore=lore, found=found, keeper="", kn_tag=""))
        else:
            blocks_list.append(stat)
    blocks = "\n  ".join(blocks_list)
    return f'''<!-- VIII -->
<section class="page" id="living">
  {runhead('VIII. Beasts of the Living World')}
  <h1 class="chapter">VIII. Beasts of the Living World</h1>
  <p class="chapter-sub">The honest dangers &mdash; flesh, blood, tooth, and no curse at all.</p>
  <div class="divider"></div>
  {quote("Folk ask me which of the territory's animals are the dangerous ones. I tell them: the hungry ones, and the ones you have cornered. That is the whole of the list.", "from the field-books of N. Ashby")}
  <p class="dropcap lead">Not everything that kills a man on the frontier came back from a grave or down from the stars. The country is full of plain animals that will end you for plain reasons &mdash; hunger, fear, a calf to guard, a trail you had no business riding &mdash; and between them they bury more men than all the horrors in this book combined.</p>
  <p class="note"> <strong>Signs of the kind:</strong> tracks in the mud and scat on the trail, a kill cached under brush, the birds gone quiet at the treeline, stock that will not settle &mdash; the plain sign any frontiersman learns to read, or dies not reading.</p>
  <div class="keeper-note"><span class="kn-tag">No Nerve, no Mark</span>These beasts cost the party <em>no Nerve</em> &mdash; there is no Dread Check against an honest animal, and their <strong>Dread</strong> line is marked &ldquo;&mdash;&rdquo; to say so. Nor do they ever move the Mark. Run them straight off the numbers. Their place in this book is to make the country real, to bloody a party grown careless &mdash; and to set the moment a thing that looks like an ordinary wolf turns its head, and its eyes are wrong.</div>
  {blocks}
</section>
'''


# ---- Field-guide lore for the ordinary beasts. Honest animals get a concise
# treatment (one descriptive paragraph + a 'Found' line); their how-to-fight
# already lives in the stat block's Special and Putting-It-Down lines, and the
# section keeper-note covers the no-Nerve/no-Mark rule, so no per-beast keeper
# note is added. Keyed by the creature's name (LIVING_CREATURES[n][0]).
LIVING_LORE = {
  "The Coyote": (
    "The trickster of the waking world, and mostly a coward with a clever face. A coyote wants the easy meal &mdash; the lame calf, the unguarded chickens, the carcass already cooling &mdash; and it weighs every risk with a gambler's care. A few may shadow a lone traveler, yipping in the dark to unsettle him, but they rarely commit, and the speech of a gun sends them flowing back into the brush like water. Only hunger past reason, or the froth of madness, makes one truly press a man.",
    "Open range, brush country, and the edges of every settlement; wherever there's carrion, stock, or scraps. Heard far more than seen, especially at dusk and the small hours."),
  "The Rattlesnake": (
    "The coil in the dust, and the most honest killer on this list &mdash; it tells you plainly to leave it be, and only answers when you don't. It would far rather not waste its venom on a thing too big to eat, and the dry buzz of its rattle is a courtesy, a warning given before the strike. But step wrong in the warm rocks, reach a hand where you can't see, and it answers from arm's length faster than the eye can follow, and the venom it spends will cost you a bad day or a worse week.",
    "Sun-warmed rocks, woodpiles, brush, and the shade under any ledge in dry country. Most dangerous in the cool of morning and evening when it lies out, and at any time a careless hand or boot finds it first."),
  "The Badger": (
    "A low temper in a hole, and pound for pound about the meanest thing the honest country has to offer. The badger asks only to be left alone in its diggings, and grants the same courtesy in return &mdash; but corner it, dig at it, press it where it cannot flee, and it fights with a berserk fury far past its size, all claw and muscle and a refusal to quit that no wound seems to teach. It does not flee, does not yield, and does not learn fear.",
    "The open grasslands and dry country where it digs, riddling a hillside or a pasture with burrows. Encountered when something disturbs its den &mdash; a horse's leg in a hole, a dog gone to ground after it, a careless boot."),
  "The Bobcat": (
    "The small cat that waits above, patient and silent and gone before you've finished flinching. A bobcat hunts the straggler and the small &mdash; it drops from a ledge or a low limb onto whatever passes beneath, and its first strike from hiding lands with a startling vengeance for so modest a creature. But it has a cat's clear sense of a losing fight, and one hard answer usually convinces it the meal isn't worth the trouble.",
    "Rocky country, broken timber, and brushy draws where it can climb and lie up unseen. It favors the high ground and the ambush; watch the ledges and the low branches along a narrow trail."),
  "The Stray Pack": (
    "Dogs gone back to the wild, and the sadder and more dangerous for once having known the hearth. A stray pack has lost a dog's fear of men but kept a dog's boldness and a dog's understanding of them, which is a poor combination to meet on a lonely road. They surround a lone traveler and pull him down by weight and number, snapping and dragging, bolder than wolves because they remember that men are not gods after all.",
    "The margins of failed homesteads, ghost camps, and any place men have come and gone and left their dogs behind. They work the lonely roads and the edges of struggling settlements, especially in hard seasons."),
  "The Gray Wolf": (
    "The hunter of the long winter, and a creature of pure, patient calculation. A lone wolf weighs the odds coldly and slips away from a fair fight nearly every time; it is the pack in a hard winter, hungry and coordinated, that buries men. They harry, they hamstring, they wait, testing a quarry's strength and nerve before they ever commit, and they commit only when the arithmetic favors them.",
    "The deep timber, the high country, and the open winter range. A pack hunts a wide territory and follows game and weakness; the danger climbs with the snow and the lean months."),
  "The Mountain Lion": (
    "The cat you never see, until the last man in the line is simply gone. A cougar is the perfect ambush &mdash; it takes its prey from above or behind, drops it, and is at the throat before the rest of the party can turn at the sound. It hunts the straggler, the lone rider, the one who wandered from the fire, and it almost never strikes a fight it hasn't already won by surprise.",
    "Rocky, broken country and timbered slopes with high ground to stalk from. It haunts the game trails and the narrow passes; watch the rocks and the ledges above, and never let the line straggle out."),
  "The Wild Boar": (
    "The razorback out of the bottoms, all bad temper and worse hide. A wild boar comes head-down and does not feel the first wound, or the second; a hide like a plank turns light shot, and a temper that turns toward the gun rather than away from it makes it the rare animal that will charge a man who's already firing. Get it angry by halves and you've made a bad problem worse.",
    "The brushy bottoms, swamps, and thickets where it roots and wallows. Most dangerous in close cover where it can charge before you've a clear shot, and worst when wounded, cornered, or guarding young."),
  "The Black Bear": (
    "The raider of the camp, and mostly a thief rather than a killer &mdash; which is no comfort if you're between it and what it wants. A black bear usually wants your supper, not your life, and bluster and noise will turn most of them. But corner one, starve one, or step between a sow and her cubs, and the genial robber becomes all teeth and terrible speed, and there is no quit in a frightened or furious bear.",
    "Timber and brush country near food &mdash; berry patches, salmon runs, and especially the careless camp or the unsecured larder. Bold around settlements that have taught it men mean easy meals."),
  "The Range Bull": (
    "A ton of bad temper on four legs, and a reminder that not every deadly animal is a predator. A longhorn that has decided he hates you will gore, toss, and come around for another pass while you're still picking yourself out of the dirt, and there is a great deal of him to stop. He is slow to anger and unstoppable once roused, and a fence is worth more than a gun.",
    "The open range and the holding pens, anywhere cattle run half-wild. Most dangerous in the press of a herd, guarding cows, or simply in a foul mood with a rider who got too close."),
  "The Grizzly Bear": (
    "The lord of the high country, and the animal that has ended more confident hunters than any other on this list. A grizzly takes the lead and keeps coming &mdash; it shrugs off the first solid wound, runs down a fleeing man over short ground faster than a horse, and does not stop for pain. It takes more lead than seems possible, and a tree is no help, for a grizzly will simply wait you out.",
    "The high mountains, the open slopes, and the river bottoms in salmon season. It ranges widely and fears nothing; encountered on its own terms, which are always bad ones for a man on foot."),
  "The Bison Bull": (
    "A hill of muscle and horn, and unstoppable in a straight line. A ton and a half at a dead run neither swerves nor tires before you do; a bison bull in a temper or a stampede is less an animal to fight than a force to be elsewhere from. Turning one is easier than killing it, and not being in its path is easier than either.",
    "The open plains and grasslands where the great herds run. Most dangerous in the bull's rutting temper or the blind momentum of a moving herd; the lone old bull cut from the herd is a cussed and dangerous thing."),
  "The Bull Gator": (
    "The log that was not a log, and the undisputed master of its own black water. A bull gator explodes from the shallows, clamps on, and rolls to drown and dismember &mdash; on its own water, nothing the frontier owns can hold it. On land it is slow and beatable; in the water it is simply death with teeth, and the cut bank and the still pool are its kingdom.",
    "The swamps, bayous, slow rivers, and still backwaters of the hot country. Lies up along cut banks and in the murk; never wade or water stock where one might wait."),
  "The Wolf Pack": (
    "The winter pack run as one mind &mdash; not several wolves but a single will with many mouths, a swarm of fang and patience. It surrounds, drags down, and thins as it bleeds rather than dropping man by man; you cannot kill a pack a wolf at a time. Fire, high ground, and breaking their nerve are the only answers, and taking the leader may scatter the rest &mdash; or may not, in a hard enough winter.",
    "The deep winter range and the high lonesome country, far from help. The pack follows game and weakness across a wide territory; the threat is greatest in the lean cold months when hunger overrides caution."),
  "The Bull Moose": (
    "A thousand pounds in a foul mood, and afraid of nothing in the rut. A bull moose will charge a horse, a man, or a locomotive without a second thought, enormous and untroubled by a wound and far quicker than its bulk suggests. Give it the road and the right of way; it tires of you sooner than you tire of it, if you live the first charge.",
    "The northern timber, the willow bottoms, and the marshy lakeshores. Most dangerous in the autumn rut and when a cow defends her calf; a moose on the trail is a thing to wait out, not push past."),
  "The Great Bear": (
    "The man-killer of legend, a grizzly grown old and cunning and cruel on the failures of every hunter sent against it. It wears the scars of a dozen guns that did not stop it, and a wound only makes it worse; it has killed enough men to have learned them, to be careful and patient and savage all at once. Men have spent their whole lives, and their lives, hunting one.",
    "The deep wild high country, far from any help, where a legendary bear has reigned long enough to earn a name and a body count. It knows men and their tricks, and it does not make the mistakes a younger bear would."),
  "The Stampede": (
    "The herd run as a moving wall, a thing that cannot be reasoned with or fought, only outrun, turned, or survived. A stampede fills the draw and takes everything in the lane, a thousand head of blind panic and pounding hooves, and the only counsel is to ride out of its path, gain high ground, or turn the lead with fire and pray the ground ahead is not a box canyon.",
    "The open range and the trail-drive country, anywhere a great herd can be spooked by lightning, a gunshot, a cut bank in the dark. The terrain decides whether a stampede is a danger or a death sentence."),
  "The Man-Eater": (
    "The cat that learned to hunt men, and now hunts you in turn. A cougar or other great cat that has acquired the taste takes the sentry and the straggler by night, patient and learned, never seen until it strikes and never striking a fair fight. It must be hunted as it hunts &mdash; with bait, patience, and an iron nerve &mdash; for it has all three and the dark besides.",
    "The country around a settlement, camp, or trail where a great cat has turned to taking men. It works by night and from above; stand watch in pairs, and never sleep where something can come from the rocks overhead."),
  "The Old Tusker": (
    "The boar that breaks the dogs, a wild hog grown old and vast and malicious, with a hide like a plank and a temper like the devil. It has broken dogs, horses, and the men on them, and charges clean through what would stop anything smaller before coming back for the rest. Men hunt it for years and bury friends doing it.",
    "The deep brush and bad bottoms where an old boar has ranged long enough to grow huge and hateful. Most dangerous in close cover and never to be faced on foot in the open; a tree and a heavy ball, or nothing."),
  "The Pale Stallion": (
    "The wild horse no man rides, and kills to keep it so. A great wild stallion leads its band and suffers no rider and no rival &mdash; it strikes with hooves and teeth, runs men down, and is as cunning as any outlaw and twice as proud. It cannot be broken, only outlasted or shot, and many a wrangler has died learning which.",
    "The open range and the high desert where the wild bands run. Encountered guarding its mares or running off a rival; cut it from the band first, if you can, for in the band's midst it is the least of your troubles and the worst."),
  "The Mountain That Walks": (
    "The primeval bear of the old tales, the high-country legend made flesh &mdash; bigger than a bear has any right to be, and older. It takes wounds the way a hillside takes rain and has outlived every hunter ever sent for it; a thing out of the grandfather-stories that will take everything you brought and everything you are, and may yet walk away unbothered.",
    "The deepest, highest, least-traveled country, where a thing can grow vast and ancient with no man left alive who's seen it twice. A legend with a territory; you do not find it so much as trespass on it."),
  "The White Bison": (
    "The great pale buffalo, omen and terror both, sacred to some and doom to others. Huge beyond reason, it leads a herd a thousand head strong wherever it goes; the people count it holy and the hunters count it cursed, and many will tell you it must not be killed at all. If you must, it is a mountain of muscle and wrath, and the herd at its back is the rest of your trouble.",
    "The great plains where the herds run, moving at the head of its following. As much a sign as a creature; where the white bison walks, men's beliefs and fears walk with it, and that is half its danger."),
  "The Great Serpent": (
    "The snake grown long as a wagon-train and thick as a barrel, a thing that strikes from the dust with the reach of a tall man and more. Its venom answers to no remedy the frontier carries, and getting close enough to take its head &mdash; which is the only way to end it &mdash; is the whole of the danger. Keep to high rock and open ground where you can see it come.",
    "The badlands, the rocky desert, and the broken sun-baked country where a serpent can grow monstrous and burrow deep. It lies up in the rocks and the dust; the warm hours bring it out to hunt."),
  "The Carcajou": (
    "The devil-bear of the north woods, the wolverine of legend grown vast and tireless and full of grudge. It drives bears off their kills, fears nothing that lives, and pursues a wrong for days without rest or quit. It does not stop and it does not tire; you cannot outlast it, and must end it all at once or keep moving until one of you is dead.",
    "The deep northern timber and the high cold country, ranging a vast territory with relentless appetite. It follows a trail or a grudge tirelessly; once it has fixed on a party or a trapline, it does not simply wander off."),
  "The Old Man of the Swamp": (
    "The gator that owns the bayou, older than the parish and longer than a flatboat, patient as the tide. It takes a man or a mount under without a ripple, and the black water is all its own; draw it onto dry land or never face it at all, for in the water you will simply be gone. The swamp is its kingdom and your grave.",
    "The deepest, oldest black water of the great swamps and bayous, where a gator has reigned long enough to grow legendary. It knows every channel and cut bank of its domain; on its own water, it is undefeated and undefeatable."),
  # ---- the second rank: the small country, and what it actually does to people ----
  "The Mad Dog": (
    "The hydrophobia, walking, and the only honest animal in this chapter that kills a man weeks after it has finished with him. A dog with the madness in it runs a crooked line at whatever moves, jaws working on nothing, and it cannot be whistled back, bought off, or scared away by any noise a man can make. The bite itself is a small thing &mdash; a torn sleeve, a bad afternoon, a wound that scabs over clean. Then the month turns, and the bitten man finds he cannot drink, and every soul who has seen it before knows exactly how the rest of it goes.",
    "Anywhere dogs run loose and something wild has bitten one &mdash; ranch yards, mining camps, the edges of town in high summer. Coyotes, foxes, and skunks carry it too, and a fox that walks up to a man in daylight is telling him something."),
  "The Skunk": (
    "A small argument you have already lost. The skunk is a decent, unhurried animal that wants beetles and eggs and no conversation, and it announces itself twice before it does anything &mdash; a stiff-legged charge that stops short, then a stamp of the front feet, then the tail comes up. Men who ignore all three deserve the education. The range is longer than anyone expects, the aim is better, and a man who takes it square is unwelcome in any bunkhouse in the county for a fortnight.",
    "Everywhere there is garbage, grubs, or a hen house &mdash; camp middens, barns, hollow logs, and under the porch. Works the dusk and the dark, and is met most often by whoever went out to see what the dogs were carrying on about."),
  "The Peccary Band": (
    "Javelinas out of the thicket, and one of the few animals on the range that hurts people mostly by accident. A band feeds shoulder to shoulder in brush a man cannot see into, with weak eyes, a strong nose, and a standing assumption that anything close is trouble. Startled, they do not scatter away &mdash; they scatter through, twelve or fifteen of them at a dead run in whatever direction they were already pointed, and the tusks are self-sharpening and take a horse's leg open to the bone.",
    "The thorn brush, the mesquite flats, and the dry washes of the hot country, usually near prickly pear. Met at close range by definition; you are in the band before you know the band is there."),
  "The Gila Monster": (
    "The beaded lizard that will not let go. It is a slow, heavy, black-and-orange thing that spends most of its life underground and has never in recorded history chased anybody, which means every bite it has ever given was to a hand that went somewhere careless. Once it has that hand it does not strike and release like a snake; it locks its jaws and works, chewing the venom in along grooved teeth while a man tries to get a knife blade between them.",
    "Rock crevices, pack-rat nests, and the shade under ledges in the desert country. Out and moving after the spring rains and on warm evenings; encountered by reaching where you did not look."),
  "The Hornet Swarm": (
    "The ground nest you just stepped on, and the reason the trail boss rides slow through a stump field. A nest in a bank or a rotten log empties in a heartbeat and comes out angry at everything within a rod, and the stings themselves are the least of it. A horse taking a dozen of them does not consult its rider about what happens next, and most of the graves this chapter fills were dug for men who came off in rough country at a full gallop.",
    "Bank holes, stumps, hollow trees, and barn eaves, worst in late summer when the nests are at their full strength and shortest of temper. Found by a hoof, a wheel, or an axe."),
  "The Prairie Dog Town": (
    "A half-mile of broken legs, and the only entry in this chapter that is not an animal at all. The dogs themselves are harmless, sociable, and rather good company from a distance; what they build is thousands of burrows worked into the best grass on the flat, mouths hidden in the sod, invisible from the saddle at anything above a walk. Cavalry has lost horses here. Cattle outfits budget for it. A rider who takes a town at a gallop learns the arithmetic of a horse's cannon bone against a six-inch hole.",
    "The short-grass plains, always on good ground &mdash; which is precisely where a herd is being pushed and a rider is in a hurry. A town may cover a section or a county, and the far edge is never where you thought it was."),
  "The Turkey Buzzard": (
    "The bird that finds the dead first, and the most useful animal in this book to a party that pays attention. It has no fight in it and no interest in the living, and cornered it will do nothing worse than throw up on your boots. Its value is that it is always right. A wheel of them turning slow and low over a ridge two miles off is the plainest message the frontier ever sends, and every experienced hand reads it the same way: something out there is finished, and it is worth going to look at, or worth riding wide around.",
    "Aloft over everything, all day, in any open country. On the ground at a carcass, at a battlefield, at a horse that went down in the night, and at whatever the party has not found yet."),
  "The Porcupine": (
    "Slow trouble in the low branches, and the finest teacher of dogs the country has. It has no speed, no cunning, and no interest in anybody; it turns its back, raises the quills, and lets the world make its own mistake. The quills are barbed and work deeper with every hour, and an animal that takes a face full of them will not eat, cannot be handled, and needs pliers, daylight, and two men sitting on it. A dog learns this once. A young dog sometimes learns it twice.",
    "Timber and brush country, in the low branches and at the base of trees it has been girdling. Slow enough to be avoided by anyone who sees it, which excludes every dog and most horses at night."),
  "The Elk Bull": (
    "Seven hundred pounds in the rut, and out of his right mind from September to the snow. Through the season he does not eat, does not sleep, and bugles all night for the pleasure of picking a fight; he is defending a harem of cows a man on the trail cannot even see, and he takes any moving thing in that meadow as a rival who has come to take them. He has fought a wagon. He has fought a locomotive. He will certainly fight a horse, and the rack he carries is five feet across and comes at the chest.",
    "High meadows and timber edges through the autumn rut, and the winter range in the hard months. Heard long before he is seen &mdash; that whistling scream across a park at dusk is an address, directed at you."),
  "The Wolverine": (
    "The small devil of the deep snow, and forty pounds that has never once counted the odds. It will drive a bear off a kill by sheer sustained outrage, tear the roof off a trapper's cache and foul what it cannot carry, and follow a trapline for a season out of what looks a great deal like spite. Threatened, it comes straight at the threat, snarling, and it does not have the sense or the inclination to break off. Everything about it is out of proportion except its size.",
    "The deep timber and high snow country of the north, and any trapline, cache, or cabin left standing through the winter. Met at a carcass it has decided is now its own."),
  "The Water Moccasin": (
    "The snake that comes toward you. No other snake on the continent does that. A cottonmouth threatened holds its ground and gapes &mdash; that white throat is where the name comes from &mdash; and there are enough sober accounts of one swimming a deliberate line at a wading man that the country has stopped arguing about it. The venom is the ugly kind: it kills the flesh around the bite, and a hand that takes a bad one in swamp country a hundred miles from a doctor is often not a hand much longer.",
    "Still and slow water in the hot country &mdash; sloughs, backwaters, rice ditches, cypress swamps. On the bank, on the log, and in the water with you; met while wading, and while sitting down where a log looked convenient."),
  "The Golden Eagle": (
    "The shadow that takes the lamb, and the one predator on the range that a herder can never do a thing about. It works from a height no rifle honestly reaches, folds, and arrives at better than a hundred miles an hour, and the first the flock knows of it is a lamb going sideways in the grass. It has been known to take a fawn, a fox, and now and again a small dog off open ground. Against a man it does nothing at all unless he has climbed to the nest, at which point it becomes a different proposition entirely.",
    "Open country with cliffs or high timber to nest in &mdash; canyon rims, buttes, and mountain fronts. Over lambing grounds in the spring, and there lies the trouble."),
  "The Feral Horse Band": (
    "The mustangs, and the stallion who runs them, and the reason a careful outfit hobbles everything and stands a watch besides. A band stallion is a working thief with two hundred years of practice: he cuts saddle stock out of a picket line in the dark, drives it off among his mares, and is four miles gone before the camp is properly awake. Argue with him over it and you are not fighting one horse but standing in the middle of forty head turning at once, which the ground does not survive and neither does a man on it.",
    "Open range and broken country with water and grass, anywhere the wild bands still run. Comes to the picket line at night; the trouble is always discovered at dawn, and always too late."),
  "The Rutting Buck": (
    "The deer that buries more men than the bear, for the plain reason that nobody is afraid of a deer. Two hundred pounds of muscle behind eight points of hard antler, in the one season of the year when it has stopped being careful about anything, will drive a man into the dirt and stand over him working. Worse is the buck that has been shot and gone down and been walked up on by a hunter who thought that settled it &mdash; every autumn produces a handful of those, and the coroner writes them up the same way every time.",
    "Brush, timber edges, and field margins through the autumn rut; anywhere a buck has cows and an opinion. Most dangerously, at the end of a blood trail, where something is lying still and is not finished."),
  "The Sow and Cubs": (
    "The one bear with no quit in her. An ordinary black bear is a burglar and a bluffer &mdash; noise turns most of them and a thrown rock turns the rest. A sow who has decided that a man is between her and her cubs skips all of that. She commits on the first stride, presses through wounds that would send any other bear up a hill, and keeps coming as long as she believes the cubs are wrong-side of you. The cubs are the whole story, and they are usually the thing you did not see.",
    "Timber, brush, and berry country in spring and early summer, when the cubs are small and the sow is thin and short-tempered. Met on a blind trail, at close range, and announced by a sound up in a tree that you will wish you had understood sooner."),
  "The Boar Sounder": (
    "The whole family, in heavy brush &mdash; a very different animal from the lone razorback. A sounder runs to twenty head &mdash; sows, shoats, and a pair of old boars on the edges &mdash; through cover a man cannot see ten feet into, and it moves like one thing. They cut across, wheel in the thicket, and come back through from a direction nobody was watching, and they do this in country where a rifle is worth less than a good knife and a stout tree.",
    "Bottomland thickets, cane brakes, and swamp margins, rooting at dawn and dusk. Found by the dogs. That is how most of these fights start, and how a good many dogs finish."),
  "The Snake Den": (
    "The winter den, opened, and the single worst place a man can put his foot in a cold spring. Rattlers pass the winter in company &mdash; scores of them, sometimes hundreds, coiled together deep in the same rock fault year after year for longer than the county has had a name. Break into that in March, when they are stiff with cold and slow and thoroughly disinclined to move, and the floor of the place is alive and the walls are too, and every step out is another chance.",
    "Deep rock faults, talus slopes, and old mine cuts on south-facing ground, used generation after generation. Dangerous from the first warm days until the den empties for the summer; dynamite and prospecting have opened more than a few."),
  "The Wild Cattle of the Brasada": (
    "Cattle that went wild and got clever. The ladinos of the thorn brush are longhorns bred out of a hundred years of strays, and the brush has made them nocturnal, solitary, and genuinely hostile in a way ordinary range stock never is. Six feet of horn tip to tip, a bull will lie up in a thicket all day and charge anything that comes in after him, and he has a settled hatred of horses and the men on top of them. The brush poppers who rope them out of the brasada for money are mostly vaqueros, working in leather from throat to boot, and they count broken bones as part of the wage.",
    "The thorn brush of the south country &mdash; mesquite, prickly pear, and catclaw so thick a rider works it in leather from throat to boot. Moving to water at night, lying up in the thickets by day."),
  "The Longhorn Herd": (
    "Three thousand head, bedded down, and one bad noise from being something else entirely. The outfit holding it is eleven or twelve hands, and on the great drives three of those are Black or Mexican as a matter of plain arithmetic &mdash; the night guard that keeps this from becoming a disaster is worked in shifts by whoever can sing and stay awake. A trail herd at rest is not a peaceful thing; it is a hill of nerves that mills and drifts and swallows a man on foot without ever intending him any harm, and every single thing an outfit does at night &mdash; the night guard, the slow circle, the singing that the singing was always actually for &mdash; is done to keep it from turning into the entry four pages back.",
    "The bed ground, every night of a drive, and any holding pasture where a big herd is gathered. Worst on a close night with lightning in it, on the first week out, and anywhere the ground ahead is broken."),
  "The Stock-Killer Wolf": (
    "The wolf with a name and a price on it, and the only honest animal in this book that a party can spend a whole campaign failing to kill. One old wolf, running alone or with a single mate, that kills far past any hunger &mdash; a dozen head in a night, throats opened and the carcasses left where they dropped. It springs traps with a stick and eats around the pan. It refuses poisoned bait it has never encountered before. It knows the range better than the ranch does, and it has already beaten every man the ranch has sent. Ranchers name these. That is how you know.",
    "One range, one river drainage, one outfit's grass &mdash; a stock-killer works a territory and stays in it for years. Found by its work at dawn: the dead cattle, and the one set of tracks that walks straight past the trap line."),
}


LIVING = build_living(sb, runhead, quote, creature)


# ---- Chapter IX: the mundane frontier. Ordinary men with ordinary reasons, and the
# country itself, which kills more people than everything in chapters II-VII combined.
# Same no-Nerve/no-Mark rule as Chapter VIII: these are the slow-burn half of the book,
# the material a Keeper runs for whole sessions before anything gets up that shouldn't.
# Tuple layout matches LIVING_CREATURES, plus (lore, found, keeper) on the end.
HARD_CREATURES = [
    # ---------------------------------------------------------------- Tier I
    ("The Drunk with a Gun", "Tier I &middot; a man who is going to regret this", 12, 11, "unsteady", "+4", "+1", "&mdash;",
     "revolver +2 (1d8+2, and he may hit whoever he did not aim at)",
     "<strong>No plan and no aim.</strong> Loud, weeping or furious by turns, and holding a loaded gun in a room full of people he mostly likes; the danger is entirely in what he does by accident.",
     "&mdash;", "Talk, or the barkeep's bung starter across the back of the head. Killing him makes an enemy of a town that was on your side an hour ago.",
     "A man who is going to regret this, assuming he lives to. Whiskey on the frontier is served by the water glass, and a payday, a grievance, and a Colt make a combination the country produces reliably every Saturday night. He is not a gunman. He could not hit the far wall on purpose. That is exactly the problem: he is waving a loaded revolver in a crowded room, his finger is inside the guard, and the man he actually wants is standing behind you.",
     "Saloons, dances, paydays, and funerals, in every settlement with liquor in it. Most reliably at the end of a trail drive, when three months of wages meet a town for the first time.",
     "Run him as a social problem with a firearm attached, and let the table solve him with talk, drink, or a chair. Then let the consequences land: the man he shoots by accident has a brother, and that brother is a perfectly ordinary fellow who will follow the party for a year."),
    ("The Rustlers", "Tier I &middot; men who do their work at night", 13, 13, "mounted", "+5", "+5", "+2",
     "rifle +4 (1d8+2, from cover, and only if pressed)",
     "<strong>Would much rather ride off.</strong> Three or four men altering brands by lantern light; they came for cattle, they will run at the first real resistance, and they will kill without hesitation if running stops being an option.",
     "&mdash;", "They break the moment the odds turn. Follow them and you are in their country; corner them and you have made this a killing that neither side wanted.",
     "Men who do their work at night, and the commonest crime in the cattle country by a distance. Rustling is a business: a running iron, a wet blanket, a hot fire, and a brand redrawn into a different brand by men who know exactly which alterations the county will not look at twice. They are cowhands, mostly &mdash; often the same men who worked the outfit last season &mdash; and they are not killers by trade or by preference. But a man caught at it hangs, and every one of them knows it, which makes a cornered rustler a far worse proposition than a bold one.",
     "Holding pastures, night camps, the far edge of a big range, and any brush country within a day's push of a border. The sign is on the ground: too few head, a cold fire, and a brand that reads wrong to anybody who looks.",
     "The rustler is the Keeper's best early antagonist because he is negotiable. He can be bought, warned off, deputized, or turned into an informant, and every one of those choices makes the country more complicated. Hang one, and the party has taught the range something about themselves."),
    ("The Claim-Jumpers", "Tier I &middot; men with your paper in their pocket", 13, 12, "afoot", "+5", "+4", "+3",
     "shotgun +4 (1d8+2 close) or the county clerk (worse)",
     "<strong>Half of this happens on paper.</strong> They have your claim recorded under another name, a lawyer in town, and four men on the ground who only need to hold the hole until the filing goes through.",
     "&mdash;", "The courthouse, if the courthouse is honest, and a hard question about who paid the clerk if it is not. Shooting them proves their case for them.",
     "Men with your paper in their pocket, which is a worse thing to face than men with guns. A claim is a piece of ground and a piece of writing, and the writing is where the theft is done: a filing altered, a witness bought, an assessment work requirement quietly missed and quietly noticed. By the time anyone rides out to argue, there are four men on the ground who need only sit there, do very little, and be extremely lawful about it until the paper catches up. And the law is a great deal easier to bend against some claimants than others &mdash; a Chinese company that worked a bar for six years and paid the foreign miners' tax on every ounce of it, or a New Mexican family whose grant is older than the territory, can find the whole apparatus of the recorder's office quietly arranged against them.",
     "Placer diggings, lode claims, homestead sections, and water rights &mdash; anywhere the ground has value and the record of who owns it lives sixty miles away in a wooden building.",
     "This is a fight the party mostly cannot shoot its way out of. That is the point of putting it early. Let them discover that the recorder is the real antagonist, and that riding to town is more use than riding to the claim. If the wronged claimant is one the county is already inclined to rule against, do not make that the lesson of the scene &mdash; make it the reason the paper matters, and let the claimant be the one who knows exactly which filing to pull and which date will hang them."),
    ("The Saloon Brawl", "Tier I &middot; thirty men and no plan at all", 12, 20, "the whole room", "+5", "+3", "&mdash;",
     "whatever is to hand +4 (1d6+2 to anyone still standing in it)",
     "<strong>Nobody is in charge.</strong> It began between two men over something neither will remember; it now involves the room, the furniture, and a stove nobody is watching.",
     "&mdash;", "Get out, get behind the bar, or get to the door. A drawn gun ends the brawl and starts something the town will remember for twenty years.",
     "Thirty men and no plan at all. It starts between two of them over a card, a woman, a slur, or a debt, and stays a fistfight for about four seconds. Then somebody swings at somebody who was not involved, and the room discovers it has opinions. Tables go over, the lamps come down, and the stove &mdash; there is always a stove &mdash; goes over with a load of coals into a floor that has been soaked in whiskey since 1868.",
     "Any saloon, dance hall, or bunkhouse with enough men and enough liquor in it, most reliably on a payday or the last night of a drive.",
     "Run it as terrain rather than as an enemy: the room is the threat, and each round asks where a character is standing rather than who they are fighting. The fire is the real clock. A party that puts the stove upright before it puts anybody down has just bought itself a town full of friends."),
    ("The Tinhorn", "Tier I &middot; the cheat, and the friends he keeps", 13, 11, "seated, mostly", "+3", "+6", "+5",
     "derringer +4 (1d6+2, at the table, from a sleeve) &mdash; and two men at the bar",
     "<strong>Reads the table better than the cards.</strong> Marked deck, cold deck, a mirror in the cigar case, and a pair of friends drinking nearby who have never met him in their lives.",
     "&mdash;", "Catching him is easy; proving it in a room where he has stood a round for everybody is the trick. Take the money back quietly, or take the whole room's word away from him first.",
     "The cheat, and the friends he keeps, which are always the actual difficulty. A tinhorn does not beat a table with cards; he beats it with preparation &mdash; a deck stacked before he sat down, a shiner set in a ring or a cigar case, and a partner across the room who signals every hand the party holds. He is unfailingly pleasant, he loses just often enough, and he has bought drinks for four men who will swear he has been square all evening.",
     "Faro layouts, poker tables, and any game running in a boom camp with money moving through it. Thickest where the money is newest &mdash; end of a drive, a strike, a payroll.",
     "The interesting scene is the accusation, not the fight. Make the table roll to spot the tell, then make them decide what to do in a room that likes him. If they simply shoot him, the two friends at the bar are a Tier I fight, and the town has watched the party kill an unarmed man over cards."),
    # ---------------------------------------------------------------- Tier II
    ("The Hired Gun", "Tier II &middot; a man paid to be wherever you are", 16, 22, "unhurried", "+7", "+9", "+6",
     "revolver +6 (1d8+3, twice, and both where he meant them)",
     "<strong>Does this for wages.</strong> Practiced, unbothered, and entirely without grudge; he will give warning once because a warning is cheaper than a fight, and he will not give it twice.",
     "&mdash;", "Find out who is paying and pay them more, or make the job cost more than the fee. He has no personal stake and is the last man on this list who wants to die over one.",
     "A man paid to be wherever you are. He is not an outlaw and he is careful about the distinction: he works for a cattle association, a mine, a railroad, or one large landowner, and there is usually a badge somewhere in the arrangement to keep the whole thing tidy. He practices, which almost nobody does. He is polite to women, good with horses, and will drink with the party the night before. The work is the work, and he has no more feeling about it than a farrier has about a shoe.",
     "Where big money has a small problem &mdash; a range in dispute, a strike being broken, a witness who has not yet testified. He arrives on the stage, takes a room, and is seen at breakfast.",
     "He is the frontier's cleanest lesson that money is the monster. Give him manners and a name and let the party like him. If they kill him, the association simply sends the next one, and that one has read the first one's notes."),
    ("The Lynch Mob", "Tier II &middot; the town, with a rope", 14, 30, "one mass, moving", "+8", "+3", "&mdash;",
     "hands, hooks, and axe handles +6 (1d8+3 to whoever stands in the way)",
     "<strong>No one in it would do this alone.</strong> Forty neighbors carrying a decision none of them made; it has a rope, a tree already chosen, and about ninety minutes before it comes apart on its own.",
     "&mdash;", "Names. Say enough of them out loud and the back of the crowd remembers it has to live here tomorrow. Firing into it makes it a riot and makes the party the thing it came for.",
     "The town, with a rope. Every man in it is somebody the party has already met &mdash; the liveryman, the storekeeper, two hands off the Bar T, the fellow who fixed their wagon &mdash; and not one of them would do this by himself, or is entirely sure how he came to be doing it now. It has no leader, exactly. It has three or four loud men near the front and a great many quiet ones behind who are waiting to see. That back half is the whole of the party's opportunity.",
     "Outside a jail, at the livery, on the courthouse steps &mdash; wherever a prisoner is being held and the crime was against someone the town loved. Forms in the evening; hardest to break after full dark.",
     "This is a talking encounter with a clock on it, and the clock is the only thing that makes it dangerous. Track it as a countdown the party can push back with each successful appeal. Let them win it, once, in front of everybody &mdash; and let the loud men at the front remember them for it. Know before you start whether the man in that cell is guilty, because the crowd does not know and will not ask; and know that in this country a mob assembles a great deal faster when the accused is Black, Mexican, or Chinese, which is a fact the party's Keeper should use to raise the stakes and never to stage a spectacle. The prisoner gets a name, a trade, a family in the crowd, and something to say."),
    ("The Deserters", "Tier II &middot; soldiers who quit the army and kept the guns", 15, 24, "mounted; disciplined", "+8", "+6", "+3",
     "carbines +6 (1d8+3, volleyed, from cover on both flanks)",
     "<strong>Trained, and out of anything to lose.</strong> They move like a squad because they were one; they post pickets, they use the ground, and they cannot surrender to anybody, ever.",
     "&mdash;", "They fight better than they have to and quit harder than they should. Take the horses, or make it look like cavalry has found them; nothing else moves them.",
     "Soldiers who quit the army and kept the guns, the horses, and the habits. That last part is what makes them worse than ordinary road agents: they scout, they post pickets, they take the high ground without discussing it, and they lay a crossfire because a sergeant somewhere taught them to and it never wore off. What they have lost is the part of a soldier that can be talked to. A deserter taken alive is a hanged deserter, so there is no arrangement on offer and no reason for them to consider one.",
     "The far country between posts &mdash; the Territories, the border, the long stretches where the army's writ is a rumor. Living off the road, the stage line, and any ranch too small to answer them.",
     "Play them tactically and let the party feel the difference between men with guns and men with training. The tragedy is available for free: one of them is nineteen, and would go home if going home were possible."),
    ("The Comancheros", "Tier II &middot; traders in what should not be traded", 15, 23, "mounted; wagons", "+7", "+7", "+5",
     "trade guns +6 (1d8+3) &mdash; and whatever they sold last month, pointed back at you",
     "<strong>Everyone's friend and nobody's.</strong> They carry powder, lead, whiskey, and rifles out to the plains and bring back cattle, horses, and now and then people; they are neutral in every war they supply.",
     "&mdash;", "They deal, always. The question is only what you have that is worth more than what they are already carrying, and whether you can live with the trade.",
     "Traders in what should not be traded. Comancheros are New Mexican &mdash; families out of the Pecos and the Canadian who have worked the old routes onto the llano for four generations, speak Comanche and Kiowa as well as they speak Spanish, and are trusted on that plain in a way no Anglo trader has ever managed. They go out with mule trains of powder, lead, whiskey, iron, and repeating rifles, and they come back with cattle that had brands, horses that had riders, and sometimes with captives to be ransomed to whoever wants them most. They are scrupulously neutral. They will guide the party, feed them, sell them exactly what they need, and sell the same to whoever the party is riding against, and see nothing at all inconsistent in it.",
     "The llano and the deep plains, the old trading grounds, the borderlands. Met on the road with a wagon train and an unhurried, friendly manner that is entirely genuine.",
     "Make them useful before making them a problem. A Comanchero the party has bought from twice is a far better complication than one they simply fight, and the ransom conversation &mdash; where the captive is real, and the price is real &mdash; is the best scene the entry has in it."),
    ("The Horse Thieves", "Tier II &middot; men who leave you afoot", 15, 20, "very fast; mounted", "+7", "+9", "+3",
     "rifle +6 (1d8+3, at a distance, while riding away)",
     "<strong>The theft is the attack.</strong> They rarely want a fight at all; they want the picket line, and in that country a party on foot has already lost more than the fight would have cost.",
     "&mdash;", "Getting the horses back matters more than getting the men. Hobble, sidehobble, and stand a watch &mdash; and know that the country hangs these faster than it hangs killers.",
     "Men who leave you afoot, which on the high plains in August is a sentence with a delay in it. A good horse thief never fires a shot: he comes in on the picket line in the last dark hour, cuts what he wants, and is over the county line before the coffee is on. The frontier hangs these men faster and with less discussion than it hangs murderers, and every one of them knows the arithmetic, so the ones who are caught fight like the cornered thing they are.",
     "Night camps, remudas, livery corrals, and any picket line within a hard ride of a border or a broken country. Worst in a moonless week.",
     "Do not stage this as a fight. Stage it as a morning: the party wakes, and the horses are gone, and everything they intended to do that week is now a different problem. What they do next &mdash; track, buy, steal in turn, or walk &mdash; will tell you more about them than a battle would."),
    # ---------------------------------------------------------------- Tier III
    ("The Outlaw Gang", "Tier III &middot; road agents with a leader and a name", 17, 40, "mounted; well armed", "+10", "+9", "+7",
     "rifles &amp; revolvers +9 (2d6+4, from three positions they chose yesterday)",
     "<strong>Somebody is thinking.</strong> Eight to twelve men who have done this before under a leader who plans, scouts the ground, buys the telegraph operator, and has a place to go afterward.",
     "&mdash;", "Break the leader and the rest are Road Agents again. Kill the leader and the smartest of the rest becomes the leader, and he has learned from watching you.",
     "Road agents with a leader and a name &mdash; the whole difference between this entry and the one in Chapter IV. A gang is a business with a payroll and a plan: the ground is scouted a week ahead, the telegraph operator has been paid, there are fresh horses cached at twelve miles and again at thirty, and there is a valley somewhere full of people who will swear the whole gang was at a dance. They are locally popular. That is not sentiment &mdash; they spend their money in that valley, and the bank they robbed foreclosed on it.",
     "The stage road, the bank town, the payroll car, and the county that shelters them afterward. Found in the papers long before they are found on the ground.",
     "Nothing else in this chapter carries a campaign as far, because the gang is a mirror: it does what the party does, with the same skills, for reasons the party can understand. Give the leader one virtue the party has to respect, and the campaign writes itself."),
    ("The Bounty Killer", "Tier III &middot; a patient man with your description", 18, 36, "unhurried; never far", "+9", "+11", "+8",
     "rifle +9 (2d6+4, at four hundred yards, once)",
     "<strong>Chooses the ground and the day.</strong> Works alone, sleeps cold, and has followed men for a season without being seen; the paper says dead or alive and he has done the arithmetic on the difference.",
     "&mdash;", "He can be paid, but only by someone who can outbid the paper, and he does not take a job he cannot finish. Break the warrant and you have broken him.",
     "A patient man with your description folded in a coat pocket, and the only entry in this chapter that hunts the party rather than being found by them. He does not brawl, does not drink much, and has no interest whatever in a fair fight; he takes a season if a season is what it takes, and he is content to ride the same stage as his man for two days without saying anything at all. The paper says dead or alive, and he has quietly worked out that alive is a great deal more trouble to feed.",
     "Wherever the party has been and has been noticed &mdash; a stage station, a hotel register, a livery book, a telegraph office. He is usually behind them by four days, and once by about forty feet.",
     "Never fight him first. Let him be seen at a distance three times over three sessions, doing nothing, and let the party understand who it is. Then make the confrontation a conversation about the warrant, because the warrant is the only part of him that can actually be beaten."),
    ("The Cattle Baron's Men", "Tier III &middot; the range war, in shirtsleeves", 17, 42, "mounted; many", "+10", "+8", "+6",
     "rifles +9 (2d6+4, and there are always more of them tomorrow)",
     "<strong>Backed by everything.</strong> Twenty riders, the association's money, the sheriff's tolerance, and a stack of eviction paper &mdash; and the standing instruction to make the small outfits sell.",
     "&mdash;", "You cannot shoot an association. Newspapers, a territorial governor, and one honest judge have ended more of these than all the gunfights combined.",
     "The range war, in shirtsleeves. A big outfit decides the small ones are rustling &mdash; sometimes they are &mdash; and hires twenty men to go and settle it, and the county's law is either on the payroll or wisely absent. What follows is not a battle. It is fence cutting, a dead dog on a porch, a barn burning at three in the morning, a homesteader's name on a list nailed up outside a store, and then one killing done in daylight to make the point that daylight is available.",
     "The open range wherever wire, sheep, or homesteaders have arrived &mdash; which by now is everywhere. Announced by a list, a notice, or a rider who says something polite on the way past.",
     "This is the campaign frame rather than an encounter: run it over months, mostly with paper and pressure, and let violence be the thing the party is trying to prevent. The Keeper's real material is the neighbors, and which way each of them jumps."),
    # ---------------------------------------------------------------- Tier IV
    ("The Regulators", "Tier IV &middot; a private army, with the law's blessing", 19, 66, "mounted column; supplied", "+14", "+9", "+8",
     "volleys +13 (2d8+6, disciplined, at whatever they have surrounded)",
     "<strong>Fifty men and a list.</strong> Hired invaders with a wagon of supplies, a doctor, a newspaperman brought along to write it up favorably, and warrants signed by a judge who left town.",
     "&mdash;", "Nothing the party owns stops fifty men. Outlast them: the country turns, the territory wires the army, and the whole expedition ends with everyone arrested and nobody punished.",
     "A private army with the law's blessing, and the point at which a range war stops pretending. Fifty hired men come in by train with horses, supply wagons, a surgeon, and a list of seventy names &mdash; and a list like that is never sorted by evidence. The small outfits on it are the ones with the least standing to object: homesteaders, Mexican families holding grant land the association would like reassigned, anyone the county courthouse has learned it can rule against without consequence. They carry warrants signed by a judge who has since gone east on business. They are competent, they are supplied, and they intend to work down the list in order. What actually stops them is never a gun &mdash; it is the county, three hundred neighbors, and a telegraph key.",
     "One county, once, and it becomes the thing everybody in the Territory talks about for a generation. The party will be somewhere on the list, or will be asked to be.",
     "Do not run this as a fight the party can win. Run it as a siege and a scramble: get the names warned, get to the telegraph, hold a ranch house for two days until help comes. The ending is deliberately unjust &mdash; everyone is arrested, the case is moved, nobody hangs &mdash; and that injustice is worth more to a campaign than a victory."),
    # ---------------------------------------------------------------- hard country
    ("The Bad Water", "Tier I &middot; the alkali seep and the poisoned well", "&mdash;", "&mdash;", "still; and it waits", "&mdash;", "&mdash;", "&mdash;",
     "the drink (Fort DC 13 or 1d6 and sickened for a week; stock may simply die)",
     "<strong>Looks exactly like water.</strong> Alkali flats, gypsum seeps, a spring gone foul, a well with something dead in it &mdash; it is wet, it is the only wet thing for a day's ride, and a thirsty outfit will argue itself into drinking it.",
     "&mdash;", "Test it on the stock or on a tin cup and wait. Boiling helps a little; the smell and the white crust around the edge tell you everything, if anyone is still cautious enough to look.",
     "The alkali seep and the poisoned well, and the reason experienced hands drink coffee. It looks like water. It is, in every way that matters to a man who has been dry since dawn, water. The white rim around a playa, the milky green of a gypsum spring, the well at an abandoned place with something at the bottom of it &mdash; each of these will empty a man out for a week, and each of them has killed whole strings of horses that had less say in the matter than their riders did.",
     "Alkali flats, sinks, gypsum country, and any abandoned well or tank. Worst in the dry months, when the good water is gone and the bad water is all that is left showing.",
     "This is the entry that teaches a party the country is a character. Put it two days out from anywhere, after their canteens have run low, and let them make the choice knowingly. Then let a horse die rather than a person, the first time."),
    ("The Norther", "Tier II &middot; sixty degrees, in an afternoon", "&mdash;", "&mdash;", "faster than a horse", "&mdash;", "&mdash;", "&mdash;",
     "the cold (Fort DC 14 each hour exposed, or 1d8+3 and the hands stop working)",
     "<strong>Arrives as a blue line.</strong> A wall of cloud low in the north at noon, and by dark the temperature has fallen sixty degrees, the rain is ice, and the cattle are walking south ahead of it whether anybody is ready or not.",
     "&mdash;", "Shelter, on the south side of anything, before it arrives. Once it is on you the only question is whether you are moving toward a wall or away from one.",
     "Sixty degrees in an afternoon. A blue norther announces itself as a hard dark line low across the northern sky in the middle of a warm day, and there is perhaps an hour between seeing it and being in it. Then the wind comes around, the rain turns to sleet and the sleet to ice, and the whole country is suddenly thirty below what it was at dinner. Cattle drift ahead of it for a hundred miles and pile against the first fence they meet, and men who were in shirtsleeves at noon are in serious difficulty by dark.",
     "The plains, from autumn through spring. The warning is always the same and always brief: a blue line in the north, and every experienced hand in sight suddenly working faster.",
     "Give the party the warning and let them decide whether to believe it. The drama is in the hour before, not the storm; whoever says we can make the next place is the one the table will remember."),
    ("The Prairie Fire", "Tier II &middot; the country, burning toward you", "&mdash;", "&mdash;", "faster than a horse, downwind", "&mdash;", "&mdash;", "&mdash;",
     "the front (1d8+3 a round to anything caught, and the smoke comes first)",
     "<strong>Outruns a horse.</strong> A front of flame in dry grass moves with the wind at better than a good horse can carry a man over broken ground, and the smoke takes the horses' nerve long before the fire arrives.",
     "&mdash;", "Burn your own ground and stand on it, get to a river, or ride crosswind &mdash; never straight ahead of it. A wet blanket and a plowed furrow have saved more outfits than courage has.",
     "The country, burning toward you. Dry grass and a wind will carry a fire front faster than a horse can go over ground it cannot see, and the smoke arrives well ahead of the flame to take the horses' nerve and the riders' bearings at the same time. It is started by lightning, by a campfire, by a locomotive's stack, and now and then deliberately by somebody who wanted a neighbor gone. What it leaves is forty miles of black ground, dead stock, and an outfit with nothing to feed anything on.",
     "The grass country in late summer and autumn, after the cure and before the rains. Seen first as a brown smudge on the horizon that is in the wrong place for weather.",
     "The correct answer &mdash; set a backfire and stand in the burn &mdash; is a thing a frontier character would know and a player might not. Let a hand suggest it. Riding crosswind is the other answer; riding away is the one that kills them."),
    ("The River Crossing", "Tier III &middot; brown water, and a herd that will not swim", "&mdash;", "&mdash;", "moving; and it does not stop", "&mdash;", "&mdash;", "&mdash;",
     "the water (Ref DC 16 or swept; a swept rider takes 2d6+4 and loses the horse)",
     "<strong>Deeper and faster than it reads.</strong> Quicksand on the bar, a cut bank on the far side, a bottom nobody has seen, and a thousand head that will mill in the middle of it the instant the lead animal turns.",
     "&mdash;", "Swim it above the herd, never below. Cut the lead steer loose to the far bank and the rest follow; let it mill and the river keeps whatever it takes.",
     "Brown water and a herd that will not swim, which together have killed more trail hands than every outlaw in this book. A river in flood reads flat and slow from the bank and is neither. There is quicksand on the inside bar, a cut bank on the far side that a swimming horse cannot climb, driftwood coming down that nobody sees until it arrives, and a bottom that changed last week. And there is the herd: a thousand head that will string across beautifully until the lead animal loses its nerve, turns, and starts the whole mass revolving in deep water with men in it.",
     "Every crossing of every drive, and worst in the spring rise. The Red, the Brazos, the Canadian, the Platte &mdash; each has a reputation, and each earned it.",
     "Do not roll once. Roll for the scout, the point, the swing, and the drag, and let the party choose the order they go in. Drown a horse before you drown a person, and if somebody must go, make it the young hand everybody at the table liked."),
    ("The Flash Flood", "Tier III &middot; the dry wash, suddenly full", "&mdash;", "&mdash;", "very fast; arrives before the rain does", "&mdash;", "&mdash;", "&mdash;",
     "the wall (2d6+4 and swept under, to everything in the channel)",
     "<strong>From a storm you cannot see.</strong> Comes down a bone-dry arroyo under a clear sky, carrying trees and boulders, out of rain that fell twenty miles upcountry an hour ago.",
     "&mdash;", "Get up the bank &mdash; any bank, immediately, before deciding whether it is necessary. There is no swimming this. An hour later it is dry again, and that is what fools the next party through.",
     "The dry wash, suddenly full, out of a sky directly overhead that is doing nothing at all. Rain that fell twenty miles up the country an hour ago gathers into a channel that has been bone dry for a season, and it arrives as a moving wall four feet high with trees and boulders rolling along inside it. The sound comes perhaps thirty seconds ahead of the water. An arroyo is the flattest, easiest, most sheltered ground in that whole country. People camp in it for exactly that reason.",
     "Desert washes, arroyos, slot canyons, and dry creek beds in the thunderstorm season. Announced by a sound like a train and by nothing else whatever.",
     "The warning is thirty seconds long, so put it in the fiction and not in a roll: describe the sound, and give the table one round to act. Whoever spends that round saving the gear instead of climbing is the object lesson."),
    ("The Blizzard", "Tier IV &middot; three days of white", "&mdash;", "&mdash;", "settled in; it has nowhere to be", "&mdash;", "&mdash;", "&mdash;",
     "the cold (Fort DC 18 an hour exposed, 2d8+6 and the extremities go; the stock dies first)",
     "<strong>Takes the country away.</strong> Wind, and snow moving sideways, and no horizon and no direction &mdash; men have died forty feet from a lit house because the world stopped having a shape.",
     "&mdash;", "Stop. Build or find shelter and stay in it three days. Every soul lost to one of these was moving when it happened, and was sure of the way.",
     "Three days of white, and the entry that ended the open-range cattle business in a single winter. Wind at fifty miles an hour with snow going sideways in it takes the horizon away, then the direction, then any notion of distance; there are sober, well-documented accounts of men freezing to death within sight of their own lit windows, having walked in a circle in a farmyard. The stock goes first &mdash; drifting before the wind, piling against fences, and standing there until they are part of the drift.",
     "The northern plains and mountain country from November to April. The warning is a falling glass, a still grey morning, and old hands putting up a rope line between the house and the barn.",
     "The rope between house and barn is the whole entry in one image; use it. Run the blizzard as three days of decisions in a small room with finite fuel, food, and patience, and let the horror be what the party has to choose about the animals outside."),
]


def build_hard(sb, runhead, quote, creature):
    blocks_list = []
    for c in HARD_CREATURES:
        stat = sb(*c[:12])
        lore, found, keeper = c[12], c[13], c[14]
        blocks_list.append(creature(stat, lore=lore, found=found, keeper=keeper))
    blocks = "\n  ".join(blocks_list)
    return f'''<!-- IX -->
<section class="page" id="hard">
  {runhead('IX. Hard Men &amp; Hard Country')}
  <h1 class="chapter">IX. Hard Men &amp; Hard Country</h1>
  <p class="chapter-sub">The ordinary frontier &mdash; which buries more people than everything before it.</p>
  <div class="divider"></div>
  {quote("I have written up seventy-one deaths in this county in eleven years. Two of them were strange. I would like the record to show what the other sixty-nine were: water, weather, whiskey, horses, and men with a reason.", "Coroner's ledger, Perdition Basin")}
  <p class="dropcap lead">Every chapter before this one is the reason a party rides out. This chapter is what actually happens to them on the way. Men rustle cattle because cattle are worth money. A river is high because it rained in the mountains. A hired gun steps off the stage because somebody with an account wrote a draft against it. None of it has a curse in it anywhere, and between them these twenty things will cost a posse more Blood, more horses, and more friends than the whole of the Old Dark.</p>
  <p class="note"> <strong>Signs of the kind:</strong> a brand that reads wrong, a list nailed up outside the store, a stranger who was at breakfast and is at supper, a blue line low in the north, a smell of smoke with no camp under it, and a wash that is the flattest ground for a mile.</p>
  <div class="keeper-note"><span class="kn-tag">Whose country this is</span>The men in this chapter are drawn from every people on the frontier, because every people on the frontier is here. The trade itself came north with the vaquero, and a quarter of the hands on any drive worth the name are Black or Mexican; the Ninth and Tenth Cavalry ride the Territory; the Chinese who laid the Central Pacific are in the mines and the market gardens and the cook tent; New Mexican families have worked their grant land since before there was a Congress to doubt the deed; and the peoples who were here first are a dozen nations who agree on nothing. Run them as what they are &mdash; the county &mdash; and give the competence in every scene to whoever has actually earned it. The Keeper's Book, Chapter VIII, has the names and the handling.</div>
  <div class="keeper-note"><span class="kn-tag">No Nerve, no Mark &mdash; and the whole point of them</span>Like the beasts of the living world, nothing here costs the party a point of Nerve or moves the Mark, and every <strong>Dread</strong> line reads &ldquo;&mdash;&rdquo; to say so. That is what makes this chapter the most useful one in the book. Run these for the first stretch of a campaign and the table learns that the country is dangerous on its own terms, that guns work, that a plan works, and that the Keeper is playing fair. Then, one night, a herd will not settle and the horses will not go near the water, and the table will find it has nowhere left to put that feeling &mdash; because it has spent eight sessions learning that everything out here has an ordinary explanation.</div>
  {blocks}
</section>
'''


HARD = build_hard(sb, runhead, quote, creature)
BODY = CONTENTS + HOWTO + DEAD + BEASTS + MEN + SPIRITS + WILD + OLD + LIVING + HARD + INDEX + GROUNDS + BUILD
_CSEC = ["dead", "beasts", "men", "spirits", "wild", "olddark", "living", "hard"]
BODY = sort_sections(BODY, _CSEC)   # each section: tier asc, then name asc
BODY = gen_appendix(BODY, _CSEC)    # appendix regenerated from actual stat blocks

# ---- splice into the shell ----
start_marker = "<!-- ===================== CONTENTS ===================== -->"
si = H.find(start_marker)
assert si != -1, "contents marker not found"
sci = H.find("<script>")
assert sci != -1
div_close = H.rfind("</div>", si, sci)
assert div_close != -1
new_html = H[:si] + BODY + "\n</div>\n" + H[sci:]

from nav_tools import add_detailed_toc, build_index
BEST_INDEX = [
    ("How to Read the Dead", "howto"),
    ("Reading a stat block", "howto"),
    ("Tier (a creature's)", "howto"),
    ("Dread DC (a creature's)", "howto"),
    ("Found (a creature's sign)", "howto"),
    ("Putting It Down (a creature's bane)", "howto"),
    ("The Restless Dead", "dead"),
    ("Cursed Beasts &amp; Wild Things", "beasts"),
    ("Men, and the Shapes of Men", "men"),
    ("Spirits &amp; Hauntings", "spirits"),
    ("The Wild &amp; the Weather", "wild"),
    ("The Old Dark", "olddark"),
    ("Beasts of the Living World", "living"),
    ("Hard Men &amp; Hard Country", "hard"),
    ("The Roll, by Tier <span class=\"note\">(appendix)</span>", "index"),
    ("The Grounds <span class=\"note\">(encounters by terrain)</span>", "grounds"),
    ("Encounters by terrain", "grounds"),
    ("The Hand Behind It (villain picker)", "grounds"),
    ("The safe-table rule", "grounds"),
    ("Building Your Own Dead", "build"),
    ("Threat by Tier (workshop)", "build"),
]
new_html = build_index(
    new_html, curated=BEST_INDEX, creatures=True,
    subtitle="Every thing that walks, and the page where it waits.",
    intro="Creatures are listed by the name they carry in the flesh; a leading "
          "&ldquo;the&rdquo; is ignored in the ordering. For a reckoning by Tier, see that appendix.")
new_html = add_detailed_toc(new_html)
open("bestiary.html", "w", encoding="utf-8").write(new_html)
# count creatures
print("spliced. statblocks:", new_html.count('class="statblock"'), "| imgs:", new_html.count("<img"), "| size:", len(new_html))
