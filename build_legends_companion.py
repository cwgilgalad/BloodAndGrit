#!/usr/bin/env python3
"""Build "Blood & Grit: The Keeper's Companion to the Book of Legends" on the shared engine.

Reads blood-and-grit.html (the shell; run build_player.py first), legends.html (run
build_legends.py first), keeper-handbook.html (run build_keeper.py first) and
GK/rules/Data/creatures.json. Writes legends-companion.html.

WHAT THIS BOOK IS. The Book of Legends is papers: talk, set down by people who were there and
didn't agree. This is what the talk was about. For every section of the Book of Legends there is an
entry here under the same title, in the same order, under the same chapter numeral, and each one
tells the story behind the papers whole: what happened, what the papers get wrong and why, and which
parts are left for the Keeper to decide. It is Keeper-side. Nobody else at the table reads it.

THE RULES IT KEEPS, and why each is a rule rather than a habit:

  1. The Keeper's Book outranks it. Where the Keeper's Book leaves a question open on purpose (why
     the Old Dark answers, what gathers in the Rockies, which face the basin's thing wears, what
     the Mad Spaniard is, whether there is a fifth rider, who writes the Weather Song) this book
     leaves it open too and offers ways to hold it. It never picks.
  2. The three legends of Keeper's Book Ch. XVI never explain each other here either.
  3. It names no face for the thing under Perdition Basin (Keeper's Book Ch. XIII, "What's under
     the water").
  4. Four papers speak for real nations. The stories behind them stay on the settlers' side of the
     page, and nothing here invents a rite, belief or sacred thing for any living people.

WHAT IS DERIVED, AND FROM WHERE. Nothing structural is typed:
  * the chapters, their numerals, titles and running heads, and every section title, are read off
    the built Book of Legends, so a chapter moved there moves here on the next build;
  * the build stops if a section of the Book of Legends has no entry here, or an entry names a
    section that isn't there, or the order differs;
  * every Keeper's Book chapter number is read off keeper-handbook.html by anchor;
  * every creature an entry names must be in GK/rules/Data/creatures.json, and its Tier is read
    from there; a name that doesn't resolve stops the build with the nearest match;
  * the timeline, the index of people and places, and the appendix of what to run are generated
    from the entries themselves, so none of them can disagree with the page it points at.
"""
import difflib
import html as _html
import json
import re

import book_shell
from pag_patch import patch_paginator

VERSION = "1.1"

H = book_shell.load()
H = patch_paginator(H)

# ---------------------------------------------------------------- the companion, as CSS
_css = """
  /* This book's own colour: the Book of Legends' iron-gall blue gone over with the Keeper's oxblood,
     which is what a paper looks like once somebody has written on it in red. It runs the page frame,
     the rules and the labels; the cover is untouched. */
  :root{ --accent:#5a3848; --accent-d:#482c39; }
  /* ---- The Legends Companion ---- */
  .keeper-note{ background:#ece2c8; border-left:3px solid var(--accent-d); padding:8px 12px; margin:1em 0; font-size:14.5px; }
  .keeper-note .kn-tag{ font-variant:small-caps; letter-spacing:.06em; color:var(--blood-d); font-weight:700; display:block; font-size:12.5px; margin-bottom:2px; }
  .keeper-note p{ margin:.35em 0; text-indent:0; }
  /* Who is in an entry: a line of small capitals under the heading. */
  /* The line under the heading and the labels inside an entry are headings (h5, h4) so that the shell's
     paginator carries them to the next page with the text they head, which it does for headings only. */
  h5.lc-who{ font-family:inherit; font-style:normal; font-weight:400; font-size:12.8px; line-height:1.4;
             color:var(--ink-soft); margin:-.15em 0 .8em; border-bottom:1px solid var(--rule); padding-bottom:5px; }
  h5.lc-who .t{ font-variant:small-caps; letter-spacing:.07em; font-weight:700; color:var(--shade); margin-right:.35em; }
  /* The three parts of an entry, each under a label in the margin's colour. */
  h4.lc-lab{ font-family:inherit; font-style:normal; font-variant:small-caps; letter-spacing:.08em; font-weight:700;
             color:var(--blood-d); font-size:13px; margin:1.05em 0 .25em; }
  h5.lc-q{ font-family:inherit; font-style:normal; font-size:inherit; font-weight:700; line-height:inherit;
           color:var(--shade); margin:.55em 0 .2em; }
  ul.lc-opts{ margin-top:.2em; }
  /* The foot of an entry: the Bestiary entries it uses and the papers it shares a thread with. */
  p.lc-foot{ font-size:13.2px; line-height:1.42; margin:.35em 0; text-indent:0; color:var(--ink-soft); }
  p.lc-foot .t{ font-variant:small-caps; letter-spacing:.07em; font-weight:700; color:var(--shade); margin-right:.35em; }
  p.lc-foot + p.lc-foot{ margin-top:.1em; }
  p.lc-rule{ border-top:1px solid var(--rule); margin:1.2em 0 0; padding:0; height:0; }
  a.lc-ref{ color:inherit; text-decoration:none; border-bottom:1px dotted var(--accent-d); }
  /* The two generated tables run long, so they are set tighter than the shell's tables. */
  table.lc-years, table.lc-run{ font-size:13px; line-height:1.3; }
  table.lc-years th, table.lc-years td, table.lc-run th, table.lc-run td{ padding:3px 7px; vertical-align:top; }
  table.lc-years td.y{ white-space:nowrap; font-variant-numeric:tabular-nums; }
  table.lc-years td.e, table.lc-run td.e{ font-size:12.4px; }
  /* The Legends Companion cover: the Book of Legends' dusk-blue ground and an oxblood keyline. */
  .title-page{ background:#0e0b12; box-shadow:0 0 0 4px #0e0b12 inset, 0 0 0 5px rgba(150,32,32,.85) inset, 0 14px 40px rgba(0,0,0,.66); }
  .title-page .t-foot{ color:#c1604a; }
  .title-page .t-sub{ color:#b6bfcf; }
</style>"""
if "h4.lc-lab{" not in H:
    H = H.replace("</style>", _css, 1)
_head = H[:H.index("</head>")]
assert _head.index("h4.lc-lab{") < _head.index("</style>"), "the Companion CSS landed outside the style block"

H = book_shell.retext_cover(
    H,
    comment=f"<!-- Blood & Grit — The Legends Companion · Version {VERSION} -->",
    title=f"<title>Blood &amp; Grit — The Keeper's Companion to the Book of Legends (v{VERSION})</title>",
    kicker='<div class="kicker">Being What the Papers Leave Out</div>',
    foot='<div class="t-foot">The Legends Companion</div>',
    tiny=f'<div class="t-tiny">Compiled for the Keeper · Edition of 1885 · Version {VERSION}</div>',
    tiny2='<div class="t-tiny">The story behind every paper in the Book of Legends, told whole, and the parts left for the Keeper</div>',
    note=f'<p class="note" style="text-align:center; margin:0;">Blood &amp; Grit · The Legends Companion · Version {VERSION} · For the Keeper Alone</p>',
)
H = book_shell.set_epigraph(H, "120px",
    '"A paper tells you what a man was willing to have written down. What happened is generally\n'
    '    somewhere behind it, sitting very still, waiting to see if you&rsquo;ll look."',
    "Marshal T. Coyle, Calvary Crossing")
H = book_shell.set_epigraph(H, "90px",
    '"I printed what I was given. I have been asked ever since about what I was not given, and always\n'
    '    by the wrong people, and always very politely."',
    "the editor of the Book of Legends, in a letter")


# ---------------------------------------------------------------- what the other books say
def _read(path):
    return open(path, encoding="utf-8").read()


LEG_HTML = _read("legends.html")
KB_HTML = _read("keeper-handbook.html")
CREATURES = {c["name"]: c for c in json.load(open("GK/rules/Data/creatures.json", encoding="utf-8"))}
# The eighteen Callings, in the Player's Book's order, read off the data the app and the book both check against.
CALLINGS = [c["name"] for c in json.load(open("GK/rules/Data/chargen.json", encoding="utf-8"))["callings"]]

_CH_RE = re.compile(r'<section class="page" id="([a-z0-9-]+)">\s*<div class="runhead"><span class="l">Blood '
                    r'&amp; Grit</span><span>([^<]+)</span></div>\s*<h1 class="chapter">([IVXLC]+)\. ([^<]+)</h1>'
                    r'\s*<p class="chapter-sub">(.*?)</p>', re.S)


def _chapters(src):
    """(anchor, numeral, title, running head, subtitle, start offset) for every numbered chapter."""
    out = []
    for m in _CH_RE.finditer(src):
        run = re.sub(r"^[IVXLC]+\.\s*", "", m.group(2))
        out.append((m.group(1), m.group(3), m.group(4), run, m.group(5), m.start()))
    return out


# The Book of Legends: chapters in their order, and each chapter's sections in theirs.
LEG = []
_lch = _chapters(LEG_HTML)
assert len(_lch) >= 17, f"legends.html has {len(_lch)} numbered chapters; rebuild it first"
for i, (anchor, num, title, run, sub, start) in enumerate(_lch):
    end = _lch[i + 1][5] if i + 1 < len(_lch) else LEG_HTML.index('id="bookindex"')
    secs = [(sid, stitle) for sid, stitle in re.findall(r'<h2 id="ix-([a-z0-9-]+)">(.*?)</h2>', LEG_HTML[start:end])]
    LEG.append(dict(anchor=anchor, num=num, title=title, run=run, sub=sub, sections=secs))
LEG_BY = {c["anchor"]: c for c in LEG}
SEC_TITLE = {sid: t for c in LEG for sid, t in c["sections"]}
SEC_CHAPTER = {sid: c["anchor"] for c in LEG for sid, _t in c["sections"]}

# The Keeper's Book: every id in it, mapped to the numeral of the chapter it sits in.
_kch = _chapters(KB_HTML)
KB_NUM = {}
for i, (anchor, num, title, run, sub, start) in enumerate(_kch):
    end = _kch[i + 1][5] if i + 1 < len(_kch) else len(KB_HTML)
    KB_NUM[anchor] = num
    for sid in re.findall(r'id="([^"]+)"', KB_HTML[start:end]):
        KB_NUM.setdefault(sid, num)


def kb(anchor):
    """'Keeper's Book Ch. XIII', for whichever chapter holds `anchor` today."""
    assert anchor in KB_NUM, f"the Keeper's Book has no anchor {anchor!r}"
    return f"Keeper's Book Ch. {KB_NUM[anchor]}"


def lch(anchor):
    """'Chapter IV', the Book of Legends' numeral for a chapter, which this book shares."""
    return f"Chapter {LEG_BY[anchor]['num']}"


_ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII"}

_ONES = ("", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
         "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen")
_TENS = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")


def spell(n):
    """Small cardinals in the books' register, as build_keeper.py spells them: 'a hundred and fifteen'."""
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ("-" + _ONES[n % 10] if n % 10 else "")
    head = ("a" if n // 100 == 1 else _ONES[n // 100]) + " hundred"
    return head + (" and " + spell(n % 100) if n % 100 else "")


def creature(name):
    """A Bestiary entry by its exact name, or a build stop that says what was meant."""
    if name not in CREATURES:
        near = difflib.get_close_matches(name, CREATURES, n=3)
        raise SystemExit(f"no creature called {name!r} in creatures.json; did you mean {near}?")
    return CREATURES[name]


def cr_display(name):
    """'the Tallyman' mid-sentence; 'Road Agents' as it stands."""
    return "the " + name[4:] if name.startswith("The ") else name


# ---------------------------------------------------------------- page furniture
def runhead(short):
    return f'<div class="runhead"><span class="l">Blood &amp; Grit</span><span>{short}</span></div>'


def quote(text, src):
    return f'<div class="quote">{text}<span class="src">&mdash; {src}</span></div>'


def paras(text):
    """Blank-line-separated prose in, a list of paragraphs out, with the source's wrapping undone."""
    out = []
    for block in re.split(r"\n\s*\n", text.strip()):
        block = re.sub(r"\s+", " ", block).strip()
        if block:
            out.append(block)
    return out


# ---------------------------------------------------------------- the entries
# One call per section of the Book of Legends, keyed by that section's anchor without its "ix-".
# The last chapter has no sections, so its entries carry an id and a title of their own (SATCHEL).
E = {}
SATCHEL = []


def entry(slug, *, story, open=(), table="", people=(), places=(), creatures=(), threads=(), when=(),
          callings=(), title=None):
    """One story behind one section.

    story     : the complete story, as the Keeper holds it (blank lines between paragraphs)
    open      : what this book won't settle, as (question, [ways to hold it]) pairs
    table     : a way to put it in front of players, and what to run
    people    : who is in it, index form ("Vane, Josiah"); shown under the heading and indexed
    places    : indexed only
    creatures : exact Bestiary names; each is checked and its Tier read from the data
    threads   : other entries (by slug) this one shares a thread with
    when      : (year, what happened) pairs for the timeline
    callings  : the Player's Book Callings this story gives a way in for; each must be a Calling in chargen.json
    title     : only for the satchel's entries, which have no section in the Book of Legends
    """
    for n in creatures:
        creature(n)
    for c in callings:
        assert c in CALLINGS, f"{slug}: no Calling called {c!r}; the Callings are {CALLINGS}"
    rec = dict(slug=slug, story=paras(story), open=list(open), table=paras(table), people=list(people),
               places=list(places), creatures=list(creatures), threads=list(threads), when=list(when),
               callings=list(callings), title=title)
    if title is None:
        assert slug not in E, f"two entries for {slug}"
        E[slug] = rec
    else:
        SATCHEL.append(rec)


CH_INTRO = {}


def intro(anchor, text):
    assert anchor in LEG_BY, f"no chapter {anchor} in the Book of Legends"
    CH_INTRO[anchor] = paras(text)


# ================================================================ Papers of the Basin
intro("basin", """
Every paper in this chapter is about the county you may already be running. The Keeper's Book gives
you Perdition Basin whole in [[kb:basin]], and the three modules each tell one night in it. The
papers here were written around those nights by people who had no idea what they were standing on,
and the stories behind them fill in what the county was doing while your players weren't looking.

Hold one rule above the rest. Where your table has already played a night the papers describe, the
table is right and the paper is wrong, the way papers generally are. The Banner printed its own
account of the Pell place and so will every newspaper your players ever sit down across from. The
dates below are the papers' dates. They fit best if the first reckoning at Coffin Wells falls in
the spring of 1882 and Esperanza R&iacute;os dies in the April of 1883, and they'll bend if yours
don't.

Nothing in this chapter names the face the thing under the basin wears. [[kb:basin-keeping]] tells you to
decide that and never say it, and every entry below is written to work under any of the three.
""")

entry("sanclavo",
      people=["Salcedo, Fray Ignacio", "Bl&aacute;zquez, Fray", "Ort&iacute;z, Fray", "Cardoza family",
              "Ybarra family", "R&iacute;os, Esperanza"],
      places=["San Clavo, Mission of", "Painted spring, the"],
      creatures=[],
      threads=["pell", "forgery", "satchel-note", "satchel-page", "mesa"],
      when=[(1809, "Three Franciscans reach San Clavo on 11 September: Bl&aacute;zquez, Ort&iacute;z, Salcedo"),
            (1810, "Fray Bl&aacute;zquez dies of a fever in February; the second, fourth and sixth wells are blessed"),
            (1811, "The seventh well is blessed in February; the register stops on 9 May; the mission burns that summer")],
      story="""
The padres kept two books, and Ashby found the wrong one. The parish register is the public book,
the one any bishop's visitor might ask to see: arrivals, baptisms, burials, a marriage, and a line
each time a well was blessed. The working book is Fray Ignacio Salcedo's ledger, sixty-one leaves of
instructions and arithmetic, and it went into a hole under the mission floor where Module III puts
it. The register's "well blessed" entries are the only public trace of the binding, and they were
written to look like piety because a thing widely known is a thing eventually dug up.

The dates tell the rest. Three fathers arrive in the autumn of 1809. Fray Bl&aacute;zquez is dead of
a fever by February, and Salcedo's ledger is honest about it where the register is not: he was the
first of them to go down the first well. The register only records the wells blessed on a feast
day; the others went into the ledger alone, which is why the numbers skip. The marriage of a Cardoza
and a Ybarra in April 1810 is the first settler family the mission made, and the Ybarra infant buried
that August is the first line in the ledger's right-hand column, the one headed <em>los que da el
agua</em>. The Cardozas are still in the basin. Their well is where Module III opens.

On 28 February 1811 the seventh well was blessed "and the spring not". The Painted Mesa people
wouldn't have the padres at their spring, and the padres, for once, did as they were told. On 9 May
1811 somebody opened the register, wrote the date, and wrote nothing after it. The mission burned
that summer and the order went home, all but one man.

The count on the inside of the back board is the keepers'. After 1811 the register was left in its
tin box where anybody could find it, because nobody steals a parish register, and the one person
walking the circuit each season wrote a single figure on the board: how many nails were holding when
the round was done. Seven, for most of seventy years. Six, once, and then seven again the season
after, when a keeper re-drove a nail that had let go. The last figure is a seven gone over twice as
if the pen ran dry, and the hand is Esperanza R&iacute;os's, in the March before she died. Ashby is
the first outsider who ever read the number and asked what it counted, and his note in the satchel
is the right question.
""",
      open=[("What happened on 9 May 1811?",
             ["Salcedo sat down to record a death and couldn't make himself write whose. It was one of "
              "the two brothers, and the fire began that week.",
              "Something came up the courtyard well, and the entry is the date it came. The fire was "
              "set to put it back.",
              "Nothing did. Fray Ort&iacute;z was called away mid-entry, and the date stayed because "
              "nobody ever tore a leaf out of a parish book."]),
            ("Who was the one man who stayed?",
             ["A mission servant whose name is on no page, which is how he wanted it.",
              "The man baptised Tom&aacute;s, of the mesa, in 1810. If you choose this, the question "
              "the Keeper's Book asks about who taught whom has an answer, and the Mesa people know it.",
              "Fray Ort&iacute;z himself, who told the order he was dying and wasn't."]),
            ("Which of the county's wells has moved?",
             ["The editor's note is right: two wells were re-dug in the fifties and one moved a quarter "
              "mile. A nail doesn't move with a well, so one nail sits in an abandoned hole the county "
              "map doesn't show. Decide which, and it's the one your players look for in the wrong place."])],
      table="""
Hand the register over as it's printed in the Book of Legends and say nothing about the back board
until somebody asks what a count is doing in a parish book. If the ring is being kept, the figure on
the board is current every time the players go back, and that makes the board a clock nobody has to
explain. If nobody took the hammer after Esperanza, the gone-over seven is the last word the ring
ever wrote, and a player who picks up the hammer in Module III is the next hand on that board.
""")

entry("water",
      people=["A. (a letter-writer at Coffin Wells)", "Kirby, Mrs.", "Cruz, Adelia", "Renfro family",
              "Dunbar family", "Vane, Josiah", "Drayton (of Kansas City)"],
      places=["Coffin Wells", "Fort Marcy, the weather office at"],
      creatures=["The Thing in the Well", "The Drowned", "The Drought-Bringer"],
      threads=["vane", "foreclosure", "satchel-wells", "paidinfull"],
      when=[(1883, "Three homestead wells in the Coffin Wells district go bad between Easter and June; "
                   "the Renfro boy dies in May")],
      story="""
A. is Tom's wife, and Tom keeps the smithy at Coffin Wells, which is why he has a wagon to haul water
with and why he has less time for the shop every week. She's a sensible woman writing to her sister
about the only news there is. By the end of May 1883 three homestead wells in the district have gone
over: flat first, then a penny taste, then the stock won't drink. That order is the order the thing
under the basin comes up in. The flatness is the water table losing its hold on the nail; the penny
is what the silver tastes like when it stops holding anything; after that the well belongs to
something else.

The Coffin Wells nail had been out since the spring before, when Josiah Vane dug up the wrong grave
(Module I). A ring can carry one broken well for a season if somebody is walking the rest of it, and
somebody was. Then Esperanza R&iacute;os died in April, nobody walked the circuit, and the homestead
wells nearest the broken one began to follow it down, one a month. That's the "since Easter" in A.'s
letter.

The Renfro boy was nine and healthy in April. He drank from the Renfro well through the flat week,
before anybody noticed the taste, and what killed him in May was water in the lungs in a dry house.
Adelia Cruz has been out to the homesteads twice because the doctor at the Crossing calls it fever
and she has seen the bodies, and they're wet. That's why she isn't sleeping. Mrs. Kirby has been at
Coffin Wells longest and didn't answer A. because she knows a well that goes over doesn't come back
on its own, and she has decided that knowing is her business.

Vane's wire to Drayton in Kansas City is the other half of the chapter. "NO CAUSE FOR ALARM THE DRY
IS GENERAL" was written by a man who had the Fort Marcy figures on his desk and knew the season was a
fair one. He needed Kansas City to go on writing notes against river sections while he bought the
dry ones, and a general drought is a thing a bank in Kansas City can price. A county's wells going
bad one at a time is not.
""",
      open=[("What does Mrs. Kirby know, and how?",
             ["She was married to the keeper before Esperanza, and walked the circuit beside him for "
              "eleven years, and has never told a soul.",
              "She's a woman of a seated house ([[ch:longtable]]) and her house keeps the account of the "
              "basin's water the way it keeps births.",
              "She knows nothing at all except what seventy years of wells have taught her, which is "
              "that the ones that go don't come back."]),
            ("What else drank from the Renfro well?",
             ["The Renfro stock, which stood at the wire all night and never turned their heads, the "
              "way the Weather Song has it. They're still standing there in July.",
              "Two of the Renfros' neighbours, who will drown in the autumn and get up afterward. "
              "Module III's Act One has room for them."])],
      table="""
The three stages (flat, penny, refused) are the best omen ladder in the basin. Give each homestead
well a stage and let the players taste the difference. A. makes a good first contact at Coffin
Wells: she trades in news, she's already frightened, and she'll sell a letter for a dollar. If the
players reach Drayton's wire before they reach Vane, they know the banker is lying before they know
why, which is the right order.
""")

entry("vane",
      people=["Vane, Josiah", "Drayton (of Kansas City)"],
      places=["Vane Banking House, the"],
      creatures=["The Day-Man", "The Ledger of the Territory"],
      threads=["water", "foreclosure", "paidinfull", "kansas", "gold"],
      when=[(1883, "The Vane Banking House begins writing notes on sections whose well has failed")],
      story="""
The slip went out in the summer of 1883, a few hundred of them, left in stacks at the hotel and both
stores. It says exactly what the Vane Banking House was doing, which is the one kind of honesty a
bank can afford: lending eight per cent on land nobody else would lend on, against the day the
borrower can't pay. A section with a dead well grows nothing. The note defaults inside two years and
the section comes to the bank for the price of the loan. Josiah Vane has been assembling the basin
one dead well at a time.

He isn't doing it alone and he isn't doing it for himself. The money is Kansas City's, by way of
Drayton, and behind Drayton is a correspondent bank and behind that four or five men who own
railroads (see [[kb:powers-money]]). The survey is coming through. A right of way across a county of
foreclosed sections costs a railroad nothing in court. Vane's share is a seat on the board of
whatever the basin becomes, and a way out of the debt that sent him digging in a grave for silver in
the first place.

What makes him worth running is the last line of Ashby's entry: "Unless the wells come back." Vane
knows something about that, and what he knows depends on how Module I went. If he made his bargain
with the thing under the mission ground and lived, he was promised something, and what a ruined man
promised by the Old Dark hears is the thing he wants most, which is that his land will be sweet
water again the day it's his. See [[ref:foreclosure]] for how that's going.
""",
      open=[("What does Vane believe will bring the wells back?",
             ["He was told, the night he opened the grave, that what's his will be watered. He thinks "
              "it was a promise. It was a description.",
              "He knows about the nails, has hired a man to find the keeper's schedule, and means to own "
              "the keeping the way he owns the notes.",
              "Nothing. He's betting on the railroad bringing deep drilling rigs, and he'll be ruined "
              "if it doesn't, and he'll be ruined if it does."]),
            ("If Vane died in Module I, who sends the slips?",
             ["His clerk, who kept the business going on the dead man's instructions and has never "
              "been told what the instructions were for.",
              "Kansas City sent a new manager inside a month. The slips didn't change by a word."])],
      table="""
Put the slip on the bar at the hotel where the players will find it, and make the rate lower than the
Crossing's so a sharp player asks why a bank would lend cheap on bad land. Vane runs as a Day-Man
in the Bestiary's sense whether or not the Nightwalker is still alive: a living man whose business
hours are somebody else's. Behind him, at a distance the players may never close, is the Ledger.
""")

entry("mesa",
      people=["Hollis (a freighter and interpreter)", "Painted Mesa people, the"],
      places=["Painted Mesa, the", "Painted spring, the", "Calvary Crossing"],
      creatures=[],
      threads=["sanclavo", "survey", "cut", "gold", "letterhome"],
      when=[(1882, "Ashby drinks at the Painted spring in August and is asked not to measure it"),
            (1884, "A Mesa witness speaks at the right-of-way hearing at the Crossing in February; "
                   "the right of way is granted in April")],
      story="""
Ashby drank at the Painted spring in August 1882 and was asked, politely, not to measure it. The man
who asked is about fifty and is the one Mesa elder who keeps the spring's turn that year; the kerb
is swept because it's his family's week to sweep it. He let Ashby drink because refusing water in
August is a thing his people don't do, and he refused the measuring because a measured spring is a
spring somebody means to own. He was right about that within two years.

The hearing in February 1884 was about the railroad's right of way, and the right of way runs across
the Mesa people's old ground below the mesa, the ground they were moved off in the mission years and
have never stopped regarding as theirs. The witness came to the county court because the court was
the only room in the basin where anybody had to write down what he said. His answers are exact. The
wells that fail were dug where the ground is wrong, by men in a hurry, and anybody could see it.
The spring doesn't fail because his people look after it. The court didn't have an hour for the rest.

What the hour held belongs to the Mesa people and this book won't write it for them. What a Keeper
needs is plainer than any rite: the Mesa people have known what's under the basin for longer than the
padres did, they told the padres so and were not heeded, and the spring they keep has never been part
of the padres' arrangement. The padres measured what the thing takes. The Mesa people keep a spring it
doesn't reach. Whatever the difference is, it's older than the nails and the players have to earn it
in the fiction, from people who owe them nothing.

Two sections of the Mesa people's old ground are on a page of the Golden Circle's purchases
([[ref:gold]]). They were bought through a land office that didn't ask whose ground it had been, and
nobody on the Circle's side can say what they're for.
""",
      open=[("Is the witness at the hearing the man at the spring?",
             ["Yes, and he came to the hearing because of Ashby: a man who wrote the spring in a book "
              "was the first sign the county meant to take it.",
              "No. The witness is a young rider who is done being patient with settlers, and the elder "
              "at the spring thinks he said too much."]),
            ("What do the Mesa people want from the players?",
             ["Witnesses. When the Circle's surveyors stake the two parcels, they'd like somebody the "
              "county believes to watch it done and to do nothing else.",
              "Nothing, until the players have been of some use to somebody on the mesa without being "
              "asked. After that, a conversation."])],
      table="""
There is no monster behind this paper and there mustn't be one. The Bestiary's own table for the
basin puts "no table" beside the Painted Mesa, and this entry keeps that. Play the Mesa people the way
[[kb:basin-mesa]] asks: names, disagreements, an elder who counsels caution and a rider who doesn't.
Hollis the freighter is a useful man to meet first. He interpreted for the court, knows he did it
badly, and is ashamed of the last line the clerk wanted struck.
""")

entry("survey",
      callings=["Engineer"],
      people=["Teale, Mr. (chief of party)", "Dowd brothers, the"],
      places=["San Clavo, Mission of", "the survey's cut"],
      creatures=["The Veinwork", "Servant of the Deep Dark"],
      threads=["cut", "mesa", "sanclavo", "numberfour"],
      when=[(1884, "The railroad survey blasts the old fill west of the mission on 6 October; "
                   "the Dowd brothers walk off the line that night")],
      story="""
The railroad had the right of way by April 1884 and a survey party in the basin by the autumn,
running east from the ford toward the mission ground. On 6 October the line crossed the low bank west
of the ruin where the old fill is, and Mr. Teale, who had a schedule to keep, put powder into it
twice.

The old fill is the trench the last padres dug in the summer of 1811 and filled with everything the
fire left: charred timber, the collapsed wall of the first chapel, and the men who died putting the
fire out, laid in a row and covered in lime and rubble in a single afternoon. They were buried there
rather than in the churchyard because of what they'd been doing when they died, which was holding
the courtyard well shut. What came up when the powder opened it was the air of that afternoon, kept
seventy-three years under clay: a shut cellar, and something sweeter under it that the chainmen
couldn't name and the Keeper doesn't have to.

Dowd breathed the most of it and was sick on the line. That night he and his brother took their kit
and left eleven dollars of pay, which is what a man does when he recognizes a thing and wants no
part of explaining how. On the 9th Teale filled the cut back in himself and ran the line three
hundred feet north. The petition the chainmen gave him on the 8th ([[ref:cut]]) is the other half of
this paper, and it's the reason he could.
""",
      open=[("Where did the Dowds go?",
             ["West along the Stage Road to the Crossing and out of the county by the Monday coach. "
              "They're grading on the Kansas Pacific now and will say nothing, which is the right thing "
              "for a man who once worked a Cornish drift where a smell like that came before a fall.",
              "To the mission spring, the first night, to drink. They're two of the three things that "
              "drank from the Cardoza well's water in Module III, and they'll be standing when the posse "
              "gets there.",
              "Nowhere. They're under the fill with the men of 1811, and Teale knows it, and that's what "
              "he saw on the 6th."]),
            ("What did Teale see when he went down into the cut on the 6th?",
             ["The lime-white bones of a row of men, every one of them lying face down.",
              "A course of dressed stone with a nail of worked silver in it, driven at a waterline that "
              "hasn't been wet for seventy years.",
              "Nothing at all. He came up because the air told him to, and he's forty-one and hasn't been "
              "frightened since the war, and he's been frightened every night since."])],
      table="""
A survey party is the easiest way to put players on the basin's ground with a reason to dig: they can
be hired as guards, as chainmen, or as the men Teale sends to find the Dowds. The cut is the doorway
the Keeper's Book promises for the Veinwork at 9th level and above. At lower levels run nothing out of
it at all. Let the chainmen refuse to work beside it and let the players decide whether to look.
""")

entry("twosections",
      people=["Purcell, C. D.", "a deputy surveyor", "the people of the Painted Mesa"],
      places=["Painted Mesa, the", "Calvary Crossing"],
      creatures=["The Parcel"],
      threads=["mesa", "gold", "landoffice", "lookedat", "committee"],
      when=[(1883, "A deputy surveyor runs the lines of two sections on the Painted Mesa in April for C. D. Purcell, "
                   "paid in gold")],
      story="""
The two sections are the second and third lines of the Circle's page in [[ref:gold]], and the man who stood by while
their corners went in is C. D. Purcell, the Circle's agent in Perdition Basin. He paid the deputy surveyor in gold, as
the list required, and never told him who the purchaser was, because he didn't know either. Purcell's instruction was
to see the lines run and the stones set and nothing more. The list cares about the corners. It has no interest in the
grass.

The deputy was an honest man under a government contract who did his work properly and wrote down one thing his
instructions didn't provide for: that people of the mesa came and stood at every line he ran, and asked that their
watching be written down. He did it eleven times. The Surveyor General's office struck every entry out of the fair
copy, so the record Washington keeps says the land was surveyed with nobody there, and the deputy's own field book,
which nobody at Washington reads, says otherwise.

What the mesa people meant by the request is theirs, and this book doesn't guess at it. What it did is plain from the
outsiders' side of the page. It put the people on the land into the one paper that would last, watching it being sold
and not agreeing. Ashby understood that, and so did the man in the office who struck it out.
""",
      open=[("What does the list want with the mesa's ground?",
             ["The same thing it wants with every other line, and the Bestiary's Parcel is the slow way to find out.",
              "The mesa's spring is the one water in the basin that never failed, and the list wants the ground round "
              "it held by somebody who isn't looking after it."]),
            ("Does the deputy surveyor matter again?",
             ["He kept his field book, and it's the best evidence anybody has that the survey was run over people who "
              "objected. A posse that means to fight the Circle in a courtroom wants him.",
              "No. He went back east in 1884 and doesn't answer letters about the mesa."])],
      table="""
The deputy's field book is a thing a posse can find, at his widow's or in a land-office lumber room, and it's worth
more in a courtroom than a rifle is on the mesa. Keep the mesa people as people. If a posse goes up there, they meet
neighbours who'd rather be left alone about it, and who have every reason.
""")

entry("paidinfull",
      people=["Harbin, Linus", "Dennard, Mrs. O.", "Colley, Mr. (bank examiner)", "Vane, Josiah",
              "Tennison, Ab", "Bass, the Widow", "Pryor, Mary"],
      places=["Vane Banking House, the", "Dennard section, the", "Topeka"],
      creatures=["The Tallyman"],
      threads=["vane", "foreclosure", "clause", "water"],
      when=[(1884, "Linus Harbin refuses Mrs. Dennard's receipts in April and walks out to her dry well "
                   "on 29 June; he isn't seen again")],
      story="""
Linus Harbin was twenty-three, a Topeka boy with a good collar and a mother who wrote every week, and
Josiah Vane put him on the small accounts in the spring of 1884 with a promise: do well by the
quarter and there'd be a desk at the Crossing. Doing well meant regularizing. On the sections whose
well had gone, the bank took payments at the counter through the winter and didn't enter them, so
that in the spring the notes stood in default and the sections came to the bank. It was a clerk's
job to tell the borrowers so. Mrs. Olive Dennard came in with four receipts in her own hand for
sixty-eight dollars, and Linus told her they weren't on the bank's paper, which was true.

She didn't argue with him. She asked for a blank off his pad and wrote him a receipt of her own, for
the whole of what he owed, and signed it. He pinned it behind the counter as a joke and Vane laughed.

The receipt called in every account Linus had ever left open. The page at the back of his ledger
began filling that night in his own hand: a knife taken off a peg at school in 1866, a dollar short
to a widow on a harrow in 1871, a promise to Mary Pryor he didn't keep, and forty-one dollars out of
the till in small sums, which he'd forgotten he'd taken because he meant each one to be the last.
The interest ran at no rate an examiner could find, because the rate was what each debt had cost the
person it was owed to. Then the debts began paying him back: two knives on the washstand, two of the
dollar on the sill, two of the letter he'd burned. Everything he'd taken came back double, and a man
can't give back what he's holding twice as much of.

On 28 June he did the only arithmetic left. He entered Mrs. Dennard's four payments under their
right dates, marked her note satisfied, and at dawn on the 29th walked out to tell her so. A
freighter saw him crossing her section toward the dry well. He hadn't reached the house.
""",
      open=[("What is Mrs. Dennard?",
             ["A widow who knew that a receipt is a promise and wrote him one. The rest was the country, "
              "which keeps books ([[ch:songs]] has the saying), and the Tallyman came for a debt that was "
              "honestly owed.",
              "A woman of a seated house, whose Table owes her a truthful answer and gave her one.",
              "Somebody who once made an arrangement with the Old Dark herself, like the woman in "
              "[[ch:trades]], and has learned that her arrangement collects for her."]),
            ("What happened at the well?",
             ["He paid in full. The Dennard well came back sweet the next spring, and Mrs. Dennard knows "
              "exactly what with, and keeps the collar stud in a cup.",
              "He walked past it and kept walking west, owing nobody. He's alive, and very poor, and "
              "free.",
              "He went in and he answers. Call down the Dennard well after dark and a young man's voice "
              "asks, very politely, what the balance is."]),
            ("What's on the folded receipt in Colley's file?",
             ["Whoever unfolds it finds their own name written after <em>Received of</em>.",
              "Linus's name, and under it in a clerk's hand, <em>carried forward</em>."])],
      table="""
The best use of this story is its paper. Colley's file went back to Kansas City with the receipt in
it, and a file goes from desk to desk until it reaches somebody. If the players ever take the fight
to the bank's correspondents, the file is there, and the Tallyman knows exactly where the receipt is
at all times. Mrs. Dennard is still on her section. She'll give the players coffee, won't sell them
the stud, and will look at each of them for a moment the way a clerk looks at a column before he adds
it.
""")

entry("coyle",
      callings=["Marshal"],
      people=["Coyle, T. (marshal)*", "Kirby, Mrs."],
      places=["Calvary Crossing", "Coffin Wells", "the Dunbar well", "Saltlick road"],
      creatures=["The Thing in the Well"],
      threads=["water", "swarm", "deputy", "forgery", "satchel-wells", "understanding"],
      when=[(1883, "Marshal Coyle stands at the Dunbar well an hour after dark on 20 August, writes a line in his "
                   "day-book, and strikes it the next morning")],
      story="""
T. Coyle has kept the only book in the county for nine years, and he believes something about it that he'd never say to
the county commissioners: that what he writes there becomes the county's account of itself, and that an account is a
kind of fence. He writes the drunks and the dogs and the stolen horses because those keep the county ordinary. The 20th
of August 1883 is the one night he wrote down something that wasn't ordinary, and in the morning he struck it,
carefully, so that it would stay struck and still be there.

He went to the Dunbar well after dark because the water had tasted of a penny for three months and the county had
refused him his deputies. He stood at the lip an hour. The Dunbar is one of the seven the padres blessed, the third to
fail that spring, and what was failing in it was the nail. What he saw or heard is under the line. Coyle asked that it
not be printed, and the editor kept the bargain.

He isn't superstitious. He's a careful officer who has learned, from nine years of keeping a county's only book, that
a thing written down is easier to find again, and he didn't want anybody finding that one. The amended report on the
burying ground in [[ref:swarm]] is the same man doing the same thing in a hurry. [[kb:basin-crossing]] has him.
""",
      open=[("What's under the struck line?",
             ["The water climbed the stones toward his lamp, against the pull of anything, and settled, and he wrote "
              "the word and and couldn't think what came after it.",
              "His own name, said up out of the well in his mother's voice, which he would never write down whole.",
              "Nothing at all, and that's why he struck it. He stood an hour and heard nothing, and he'd begun to write "
              "that the nothing was listening."]),
            ("Is he right about books?",
             ["The Book of Legends never says. The retired clerk in [[ref:understanding]] says the old hands at "
              "Washington believe the same of a whole country, and Coyle has never met a Washington clerk in his life.",
              "He's right about his own. A posse that reads his day-book finds the county as he chose to keep it, and "
              "the struck line is the one door he left ajar."])],
      table="""
Coyle is the most useful man in the basin and the most tired. A posse that earns his trust might be shown what's under
the strike. Decide what it says before they ask, and let him look at them a long while before he turns the book round.
""")

entry("pell",
      people=["Pell, Hannah", "Pell, Tom", "Pell child, the", "Coyle, T. (marshal)", "Cruz, Adelia"],
      places=["Pell place, the", "Calvary Crossing, the schoolhouse at"],
      creatures=["The Blood-Thin", "The Risen", "The Nightwalker"],
      threads=["pellnews", "forgery", "sanclavo", "weathersong"],
      when=[(1882, "The Pell family is lost in April; the barn is burned"),
            (1883, "Children at the Crossing begin singing the rhyme about the Pell place, about May")],
      story="""
If your table has run Module I or [[kb:firstreckoning]], what they found at the Pell place is what
was there, and this entry only follows it on. If it hasn't, this is the night. Tom Pell died of what
Coffin Wells was calling fever in April 1882, was buried on the Tuesday, and came home on the Friday
among the Risen. Hannah Pell had been fed on in the cellar by the thing Josiah Vane woke, and by the
week's end she was bled thin and half-turned, still herself, asking to be seen to before she stopped
being able to ask. The youngest child, a girl of nine, was upstairs inside a ring of salt her mother
had poured round the bed, and she didn't speak for days. She drew the thing on the barn wall in
charcoal, twice, and it was a good likeness.

What she heard from that bed is the rhyme. Her mother came up out of the cellar at night and went
across the yard to the barn, where her father was, and counted aloud as she went, to seven and back
to one and to seven again. There was a reason to count. In the cellar, pressed up into the floor and
the lowest course of the wall, were seven marks the size of a spread hand, the kind a hand leaves
when it pushes up through soft ground from underneath. The thing under the basin reaches up through
seven wells. Wherever it comes near the surface, it leaves the same count, and Hannah Pell had lain
two days beside it with nothing to do but count.

The barn burned that week. The Banner says the marshal ordered it; if your players burned it with
the Risen inside, the Banner gave Coyle the credit, which is the kind of thing a county paper does.
The girl was taken in at the Crossing on the subscription the Banner raised and went to the
schoolhouse that winter. The rhyme was in the schoolyard by the next spring and every child had it
inside a month. "Don't tell your father, don't tell the man, don't tell the lady with the lamp how
many hands you can." The man is the marshal. The lady with the lamp is the one the children are most
careful never to name.
""",
      open=[("Who is the lady with the lamp?",
             ["Hannah Pell, crossing the yard. The children sing about her as though she's still out "
              "there, and on the Pell section, if your players chose hope in the cellar, she is.",
              "Esperanza R&iacute;os, who came that week with her lamp to look at the cellar and was too "
              "late, and whom the girl saw from the window and never forgot.",
              "Adelia Cruz, who sat with the girl through her first bad nights and asked her, gently, "
              "how many."]),
            ("Did the girl make the rhyme?",
             ["Yes. It was the only way she found to tell anybody, and every child who sings it is "
              "keeping her secret without knowing what it is.",
              "No. It was in the schoolyard before she ever sang it, and she's the one child at the "
              "Crossing who won't."])],
      table="""
Module I asks the table to name the Pell girl, and this is where the name pays off. She's eleven or
twelve by the time most posses come back through the Crossing, and she's the only living witness to
what the cellar held. Have children sing the rhyme in the background of a Crossing scene, and when a
nail fails, change one word: "counting up to six." Nobody in town will notice. A player who has been
keeping count will.
""")

entry("saltlick",
      people=["Otey, J. (stage driver)", "Jane (a passenger)", "Robert (her husband)", "Aunt Bess",
              "Walter (Jane's brother)", "Mad Spaniard, the"],
      places=["Saltlick Station", "the Stage Road"],
      creatures=["The Gentleman on the Road"],
      threads=["wrongdetail", "fifth", "spaniard", "satchel-road"],
      when=[(1884, "On 2 January a passenger at Saltlick Station talks with a stranger nobody else saw")],
      story="""
On the night of 2 January 1884 the down coach reached Saltlick four hours late, and while the team
was changed a passenger named Jane sat by the stove and talked with a man in clothes nobody in the
Territories could have placed within three hundred years. He was courteous, he asked after her Aunt
Bess by name, he knew Bess's knee had been bad, and he called her brother Will when his name is
Walter. She agreed with him, twice. Then she went out and stood by the coach for twenty minutes,
which is the delay J. Otey entered against the company.

This is the Mad Spaniard, and [[kb:legends-spaniard]] has everything a Keeper needs to run him, and
the four ways he can be read. This book doesn't pick among them. What it adds is where he was and
what came after. [[kb:basin-keeping]] and the Bestiary both put him on the Stage Road below Saltlick
the week before something changes, and the thing that changed the week after the 2nd was Saltlick
itself. The station's well had been thinning since the autumn, and a thinning well draws predators
the way a wound draws flies. Within a fortnight something was sheltering at the relay behind a face
that wasn't its own. [[kb:secondreckoning]] and Module II tell that night two different ways, and
whichever you ran is what happened. The stationmaster who wouldn't talk about the empty chair was
one of the first to notice the dog wouldn't come inside.

Otey's report and Jane's letter disagree about nothing that can be checked. A driver paid to write a
quiet evening put in a distressed passenger and a twenty-minute delay he charged to his own company,
which is the most any driver can say on paper and more than most would.
""",
      open=[("Is her brother going to be called Will?",
             ["Every wrong detail in the Book of Legends turns out true about something else. Walter "
              "goes west in the spring and takes another name, and it's Will.",
              "It's her father's firstborn, who died before she was born and was called Will, and she "
              "has never been told there was one.",
              "It's nothing. The one wrong detail is only wrong. The Keeper's Book lets it be either."])],
      table="""
Run the stranger at the stove if your table is about to ride into Module II's night, and let him give
one piece of good advice about the week ahead and take nothing for it. Otey is worth making a friend
of. He drives this road twice a week, he writes down what he sees, and his reports go to the line and
nowhere else, so nobody has ever asked him a question. He is also the driver in [[ref:fifth]], and
he counted four.
""")


# ================================================================ Frauds, Errors & Honest Mistakes
intro("frauds", """
The editor put the frauds second so a reader would learn what a lie sounds like early, and a Keeper
should use them the same way. Most of what's behind this chapter is exactly what it looks like: a
stone man cut to order, a lecture on stars by a man the Topeka police have a photograph of, a
spirit photographer who exposed each plate twice. Run those as they are. A table that has caught
three frauds in a row listens harder to the fourth paper, and that's the one to spend.

Several have something behind them the fraud doesn't account for, and the editor marks each with a
single sentence that won't go away. The entries below say what that something is,
and leave as much of it open as the Keeper's Book leaves of anything else.
""")

entry("giant",
      people=["Sipes, Mr. (of Wilcox)", "the monument cutter at Trinidad"],
      places=["Wilcox", "Trinidad"],
      creatures=[],
      threads=["rocksnake", "thirdcell", "hackberry"],
      when=[(1880, "A monument cutter at Trinidad carves a sleeping man, seven feet, to order"),
            (1881, "The stone man is dug up on Mr. Sipes's property at Wilcox in April")],
      story="""
It's a fraud from end to end, and it's a good one. Mr. Sipes of Wilcox was a farmer with a mortgage
and a brother-in-law in the freight business, and in the autumn of 1880 the brother-in-law carried an
order to a monument cutter at Trinidad for a sleeping man, seven feet, no clothing, no face to speak of,
the surface to be left rough. Forty dollars. The figure went north under a tarpaulin in a wagon of
fence posts and went into the ground on the Sipes place in the dead of winter, under six feet of
frozen clay, where a well was going to be wanted in the spring.

Sipes hired two men to dig the well in April and let them find it. The rest followed the way these
things follow: the Independent, the visitors from the capital, the twenty-five cents, the two
gentlemen of science, one of whom was the Independent's editor's cousin and one of whom was honest
and spent an afternoon looking at the toes and went home unable to account for them, because they're
very good toes. The Chicago offer was real. Sipes turned it down because a man in Chicago with eleven
hundred dollars to spend on a stone man would have a copy cut inside a month and exhibit that instead,
and Sipes had heard it done before.

The cutter has told four people the truth and offered to swear to it. The county doesn't want him. A
stone man who brings visitors from as far as the capital is worth more to Wilcox than a stonecutter's
day-book, and everybody in town who takes a quarter at a door, sells a supper or lets a room knows it.
""",
      open=[("Is there anything under it?",
             ["No. Keep this one clean. A table needs one wonder in the book that is exactly what the "
              "monument cutter says it is.",
              "The well Sipes dug past the stone man came in sweet at twenty feet in a dry county, and "
              "the hired men who dug it won't drink from it, and neither will Sipes."])],
      table="""
Take the players to see it. Put a crowd round the pit, a boy selling lemonade, two men arguing about
science, and let a player who asks the right question find the cutter's name in a week. Then give them
the choice the county made: expose it and cost a poor town its only trade, or pay the quarter and keep
their mouths shut.
""")

entry("hiddenstars",
      people=["Deane, Prof. T. W.", "the schoolmistress at Hays"],
      places=["Hays"],
      creatures=["The Eye Between Stars"],
      threads=["eclipse", "giant"],
      when=[(1879, "'Professor' Deane lectures on the Hidden Stars through the Kansas towns in the winter "
                   "after the eclipse")],
      story="""
T. W. Deane was a patent-medicine man who'd lost his wagon in a card game at Topeka in the week of the
eclipse of July 1878, and he spent that week in Topeka reading about the eclipse in the papers, which
is the only reason he knew there'd been one. By the winter he had a magic lantern, a box of glass slides
and a lecture. The Hidden Stars are the Pleiades printed backwards, with four more stars inked on each
chart by hand wherever Deane thought there was room. He sold the charts at fifty cents at the door and
cleared about nine dollars a night in towns that had nothing else to do in January.

The schoolmistress at Hays knew her stars and wrote to the paper, which didn't print her, and she
wrote to Topeka, which did send a photograph. Deane left Hays on the morning train. He's selling
something else in Nebraska now.

The part that isn't a fraud is small and it's the schoolmistress's third paragraph. Nine of her pupils
bought charts and three of them haven't slept well since. Deane inked his four extra stars by hand, a
few seconds on each chart, and on most of the charts he sold they fall anywhere at all. On a handful
they fall in the same four places, near together, in a little crooked line, and a girl who saw the
sun go out at Denver in 1878 could have told him where he'd put them ([[ref:eclipse]]). Deane never
saw that girl's chart and couldn't have. He'd tell you he put the dots where the paper was clean.
""",
      open=[("Why do Deane's four stars fall in the same place on some charts?",
             ["Chance. Four dots on a small chart land close together often enough, and three children "
              "who've been told there are stars you can't see will lie awake looking for them.",
              "Deane's hand knew something Deane didn't, and on the charts where the four fall together, "
              "they're a corner of the arrangement the eclipse showed.",
              "The four stars moved on the paper after the charts were sold. Ask the three children where "
              "they were when they bought them, and where they are now."])],
      table="""
A chart is a good handout for a table that's heard of the eclipse. Give the players one with the four
stars scattered and one with the four close together, and don't say which came from Hays. If you're
running [[ref:eclipse]] as more than a letter, the three sleepless children at Hays are eleven or
twelve by now, and at least one of them has started drawing the same four stars in the margins of her
copybook.
""")

entry("advocate",
      people=["Laswell, Mr.", "the editors of the Cherokee Advocate", "a teacher at the Male Seminary"],
      places=["Tahlequah", "the Neosho bottoms", "Big Cabin"],
      creatures=["The Mourner", "The Fetch"],
      threads=["collector", "calendar", "fortclark"],
      when=[(1884, "The Cherokee Advocate answers a Kansas paper's ghosts on 2 August")],
      story="""
This is one of the four papers that speak for a real nation, and the story behind it stays on the
Kansas side of the line. The Advocate was right about the ghosts, and the Advocate always is. The
lights in the Neosho bottoms were Mr. Laswell's riders gathering Laswell's cattle at night, because
the courts of the Nation had ordered the cattle off four times and night is when a man gathers stock
he isn't supposed to have. The moaning was the cattle. A Kansas weekly that needed a column in August
made the rest up, and the editors at Tahlequah went and looked, which is more than the Kansas paper
had done.

The second item is the one the Keeper wants. A party of intruders, white settlers squatting on Nation
land at Big Cabin, had been put off by the Agent three times that year and came back a fourth time on
20 July with one man more than they'd left with. He's middle-aged and dressed for a town. He doesn't
eat and he doesn't speak, and the intruders don't know him and have stopped asking. In the evenings he
stands at the ford and looks at the road they came in by.

He came with them from Kansas. Somewhere on the road up, the third time they were put out, a party
that had nowhere to go and wouldn't stop coming picked up something that waits for people like that,
and it has been waiting with them since. He isn't the Nation's business, and the Advocate printed him
for Kansas's entertainment, which was exactly the right tone. The teacher at the Male Seminary read
the one sentence in the Cherokee column that the English left out, and the sentence is about the
road.
""",
      open=[("What is the man at the ford?",
             ["A mourner. He's come early for a death on the road, and the intruders will be put off a "
              "fifth time in the autumn and one of them won't reach Kansas.",
              "One of the intruders' own. He's the fetch of the man who leads their party, and the leader "
              "hasn't noticed yet that everybody talks to the other one first.",
              "A man. A land agent from a railroad office, waiting to see whether the Nation's courts or the "
              "intruders give out first, who has learned that saying nothing is the best way to hear "
              "everything."])],
      table="""
Keep the Nation's people what the Advocate shows them to be: a government with a newspaper, courts and
an Agent, dealing patiently with trespassers, and dry about it. The horror is the intruders' and it
travels with them. A posse riding through the Nation on other business can meet the party at the ford,
and the man in the town coat will look at the posse's road the way he looks at everybody's.
""")

entry("warrants",
      people=["the printer at Waco", "his widow"],
      places=["Waco", "Redemption", "Jubilee"],
      creatures=[],
      threads=["spur", "twopapers", "letterhome", "gold"],
      when=[(1881, "A job printer at Waco prints and sells 340 land warrants on Redemption"),
            (1883, "The printer swears a statement before a notary and dies")],
      story="""
He was a printer at Waco who'd come home from the war to a shop with its press sold for debt, and by
1881 he'd bought another press and not much else. The talk about Redemption reached Waco the way it
reached every Southern town that winter: a country out west that meant to be what the South had meant
to be, with wheat land for the asking. He printed three hundred and forty warrants for that land on
good rag paper with a border he'd cut himself, signed them Treasurer, and sold them for twenty-five
dollars apiece to men who'd fought for the South and had nothing to go home to.

Nine of them went. They rode the branch from Yuma to the river and presented their warrants at the
customs post, and every one was turned back, and the reason they were given is the part the printer
couldn't live with. It wasn't the forgery. The officers at the river barely looked at the warrants.
Redemption admits by name, off a list somebody inside keeps, and a Texas private with a warrant and a
good war record wasn't on it. The country these men had been promised was for particular families, and
theirs weren't among them.

Five of the nine wrote to the printer afterwards, having found his name through the shop that sold his
paper. None of them asked for the money back. They wrote about the river and the grey coats and how
they'd been spoken to, and they blamed the country, which is why the printer could never make his peace
about it. He'd sold them a door, and the door was real, and it wasn't for them.
""",
      open=[("What became of the four who didn't write?",
             ["They went home, or somewhere like it, and never spoke of the country again.",
              "One tried the sand hills west of Jubilee on horseback, the way the story says nobody does "
              "twice, and did it once.",
              "One of them was admitted a year later, on his second try, after a gentleman at Yuma asked "
              "his mother's maiden name and wrote it down."]),
            ("What list do the officers at the river keep?",
             ["The Golden Circle's rolls of families, kept since before the war.",
              "Nobody at the river knows. The names come down on the Monday train in a sealed envelope, "
              "and the officers open it."])],
      table="""
One of the nine is a good face for a player's past, or for a bitter old soldier at a Yuma saloon who
can tell a posse exactly what the customs post looks like and how the officers talk. His warrant is in
his coat. He'd sell it to anybody fool enough to try the river, and he'd tell them it's no use.
""")

entry("seats",
      people=["Rusk, Mrs. Adaline", "a servant girl out of Louisiana"],
      places=["Kansas City", "Walnut Street, Kansas City"],
      creatures=[],
      threads=["ninechairs", "witch", "stand", "houses"],
      when=[(1884, "Mrs. Adaline Rusk is bound over at Kansas City for selling seats at a long table")],
      story="""
Adaline Rusk was a widow on Broadway with a good address and no income, and in the winter of 1883 she
hired a girl out of Louisiana to do the heavy work. The girl was sixteen and homesick, and one night in
the kitchen, frightened by a fever in the house, she said that her family had a seat at the long table
and would be looked after, and then wouldn't say another word about it, however she was asked. She'd
grown up in a family kept by a house, and she'd said the one thing such families never say.

Mrs. Rusk made the rest up at the same kitchen table. A seat at the Long Table, fifty dollars, a card
printed on Walnut Street, and the assurance that the purchaser's family would be looked after in any
trouble. She sold eleven. When she was bound over she made a full statement and offered every lady her
money back, and nine of them wouldn't take it.

They kept the seats because nothing bad had happened to any of them since, which is true of most
families in most years, and because a card that says you're looked after is a comfort worth fifty
dollars to a woman who has buried children. The letter from New Orleans came six weeks after the court
report, and it says there is no such table, which is what the houses always say, and that nobody sells
seats at it, which is what they mean. New Orleans is a long way from a Kansas City police court column.
Somebody read it there inside a month. The servant girl was gone from the Rusk house by then, sent for by her people, and
nobody in Kansas City saw her go.
""",
      open=[("What did the Table do about it?",
             ["Nothing more than the letter. It dislikes being talked about and it said so, in the only way it "
              "ever says anything, which is to deny it.",
              "It honoured the nine seats. A seated house in Kansas City has had those nine families on its "
              "books since the spring, because the Table doesn't like being called a liar and would rather "
              "make a lie true than let it stand.",
              "Mrs. Rusk was never seated, so she couldn't be asked to stand. She was asked something else, "
              "by somebody who came to the house on Broadway at a decent hour, and she has left Kansas City."])],
      table="""
If the nine seats are honoured, the players can meet one of the nine families a year or two on: a
Kansas City household where nobody's been sick, a card in the family Bible, and a polite woman who calls
every spring. It's the Long Table's whole arrangement in miniature, bought for fifty dollars from a
fraud, and the family will be very glad of it until somebody knocks with the dates.
""")

entry("collector",
      people=["the collector (a gentleman from Washington)", "the clerk at the agency", "the clerk's aunt",
              "the clerk's uncle"],
      places=["Washington"],
      creatures=["The Gentleman on the Road"],
      threads=["wrongdetail", "sayings", "saltlick", "advocate"],
      when=[(1880, "A government collector pays a family a dollar a story, and they tell him forty"),
            (1882, "The collector's volume on the myths of the Plains is printed at Washington")],
      story="""
This is one of the four papers that speak for a real nation, and its story is the collector's. He came
out in the summer of 1880 on a government stipend to gather the religion of the Plains before it died
out, which is what men in Washington thought was happening. He paid a dollar a story. The clerk's family
had forty stories to hand that summer and needed forty dollars, and they gave him what he paid for.
Eleven were about the clerk's uncle, who is a great liar and was delighted to be in a book. One was the
plot of a play the family had seen at the fort. Two were true and weren't religion. The book printed all
forty at Washington in 1882 as the beliefs of a people, and not one of them is.

The Road-Spirit is the aunt's. It's what she tells children: if a man stops you on the road and asks after
your people by name, give him the wrong names, every one, and smile, and go on. She calls it manners. The
collector called it a deity of mischief, which made it the only thing in his volume about the road that
anybody in the country would recognise, and the only thing in it he got wrong in an interesting way.

Nothing here tells a Keeper what the family prays to, and nothing should. What the aunt's advice gives a
Keeper is practical. Everything in [[kb:legends-spaniard]] about the man on the road still holds, and her
postscript is one more thing people say about why he gets one detail wrong: people have been feeding him
wrong names for a hundred years and he's too polite to check. The clerk's letter says she wasn't to be
written down as believing it, and she doesn't have to. She only has to be the one who says it.
""",
      open=[("What happens when a player takes the aunt's advice?",
             ["Nothing changes. He thanks them warmly, uses every wrong name back to them, and still gets "
              "one detail wrong, and it's a detail they never told him at all.",
              "He's pleased. He says it has been a long while since anybody showed him proper manners, and "
              "he gives them a second piece of advice, which he has never done for anyone."])],
      table="""
The aunt is somebody a posse should meet, on her own terms and at her own table, and she'll talk about
the road and nothing else she doesn't want to. The uncle will tell a posse anything at all for a dollar
and it will all be very good. The collector's volume is in every agency library, and a player who reads
it before they meet the family will have forty wrong ideas and one useful one.
""")

entry("hackberry",
      callings=["False Prophet"],
      people=["Loftus, Rev. Cyprian", "Birdsall, Mrs. Ada", "Crouch, J.", "Ewell, Jas.", "Gault child, the",
              "Tolley, the Misses", "Hale, Dr. Wm.", "the sexton at Hackberry"],
      places=["Hackberry", "Globe"],
      creatures=["The Risen", "Dark Cultist & the Hollow Prophet"],
      threads=["giant", "boxes", "revival", "wager"],
      when=[(1882, "The Rev. Cyprian Loftus promises a Sunday of Restoration at Hackberry and is paid $212 to leave"),
            (1883, "Loftus is sentenced at Globe to eighteen months")],
      story="""
Cyprian Loftus had worked his trick at Globe first and it's a clever one. A man arrives in a copper camp
calling himself a reverend of the Restoration Mission, posts a bill saying the faithful dead will be
returned to those who mourn them on Sunday next at four, and waits. Nobody in a mining camp wants the
dead back. By Friday the living have taken up a subscription to have him carry his mission elsewhere, and
on Saturday he takes the stage with the money. He's done it in four camps and never once been paid to do
what he said he'd do.

The trouble is that on the Sunday at Hackberry he preached. He stood in the burying ground at four
o'clock with the camp's money already in his coat and gave the sermon anyway, because a man who has
promised a Sunday likes to be seen keeping part of it. He's a fraud who half believes his own pulpit,
and that makes him exactly what [[kb:prophet-plate]] calls a False Prophet, feeding a plate he doesn't
know is there. His gospel was restoration. Something heard it.

Three graves settled a hand's depth by Monday, the way ground settles when something underneath has
moved. Two were the dead of the two largest subscriptions on the list: Mrs. Birdsall's husband, and Jas.
Ewell, who had been J. Crouch's partner at the livery until he died in a way Crouch doesn't discuss.
The people who paid most to keep their dead down were the people who had most reason to. The third grave
was the Gault child's, whose family had left the camp the year before and paid nothing, and who was the
only one of the three that wanted to come.
""",
      open=[("What would a second Sunday have done?",
             ["Brought the three up. Hackberry would have a Birdsall at the door and an Ewell at the livery "
              "and a child walking the road east after its family.",
              "Nothing. One sermon moved the ground a hand's depth and a second would have moved it another, "
              "and the ground at Hackberry is old workings and settles anyway."]),
            ("Does Loftus know?",
             ["No. He's in the territorial prison at Yuma doing his eighteen months, and he'll be out in the "
              "autumn and try it again somewhere with a bigger burying ground.",
              "He found out on the Monday, which is why he left on the Saturday stage in every camp after "
              "Globe. He's never been paid to do what he said. He's afraid of being paid."])],
      table="""
Loftus is a good recurring face: a charming crook with a sermon that works a little, released in time
to arrive a town ahead of the posse. Run his first Sunday as a comedy, a camp arguing about how much it
costs to keep its dead down, and his second as the other thing. The Gault child is out there on the road
east either way, if your Keeper's heart can stand it.
""")

entry("wager",
      callings=["Gunhand", "Gambler"],
      people=["Kearse, Mrs. Delphia", "Rudge, Tom", "Whitley, Hob", "Baird, Abner", "Marsh, J.",
              "the Vogel boys"],
      places=["Sull's Ferry"],
      creatures=["The Revenant"],
      threads=["hackberry", "undertaker", "swarm"],
      when=[(1881, "Tom Rudge is shot over a horse at Sull's Ferry in October and says he'll be waiting"),
            (1882, "Hob Whitley sits on Rudge's grave from midnight till the down coach in March"),
            (1883, "A letter comes from Oregon: 'Tell the boys I missed.'")],
      story="""
Tom Rudge and Hob Whitley quarrelled over a horse in Mrs. Kearse's front room in October 1881, and Hob
was quicker. Rudge lived till morning and used the night to say one thing to anybody who'd listen, which
was that he'd be waiting. He was buried behind the road house in soft ground. Hob stayed on at the ferry
through the winter, which was stubbornness, and the boys were at him about it every night, which was the
winter.

In March he bet the house twenty dollars he'd sit on the grave from midnight till the down coach, and
Abner Baird put five on top. At midnight the house heard six shots, spaced, and nobody went to look.
What Hob saw is the part he never told. Rudge came up for him the way a murdered man comes up when he's
carried one purpose into the ground: not through the grave, which Hob was sitting on, but all round it, a
yard out, through the soft March ground, reaching in. Hob fired once at each place the ground moved, and
six holes in a ring is what the driver found at daylight. Inside the ring the grave was raked smooth,
the way a thing leaves ground it has pulled itself back down into.

Hob took his twenty-five dollars and rode north without a word. A year later a letter came from Oregon,
three words and no name. The boys talked it over one evening and decided they didn't want to know what he
meant, and they were right not to, because each of the three meanings is worse than not knowing.
""",
      open=[("What did Hob miss?",
             ["Rudge. None of the six took, and Rudge has been walking north behind him since, at the pace "
              "of a man who has no reason ever to hurry.",
              "The boys, and the ferry, and the only life he had. A killer alone in Oregon can miss things.",
              "The sixth shot. Five of Rudge's reaches went back into the ground and one didn't, and whatever "
              "came up through the sixth hole went north with Hob and has been with him since."])],
      table="""
Hob Whitley is the posse's to find: a sober, tired man in an Oregon lumber camp or on the road north,
who knows exactly how far behind him the thing is and will pay well to have it put down. The Revenant's
own entry says how. Mrs. Kearse keeps the wager book behind the bar and will show it to anybody, and the
grave at Sull's Ferry is still smooth.
""")

entry("cordial",
      people=["Penrose, Asa", "Sorrell, Dell", "Tabor, Dr. Orville", "Morrow, Dr."],
      places=["Coldwater, Kansas", "Avilla"],
      creatures=["The Mesmerist", "The Drunk with a Gun"],
      callings=["Gunhand"],
      threads=["wager", "keelers", "partners"],
      when=[(1884, "Asa Penrose and Dell Sorrell meet on Main Street at Coldwater in June and shoot each other through the "
                   "right hand")],
      story="""
Asa Penrose was a gunhand of the cattle towns in the seventies, quick enough that men paid to see him and young men rode
in to try him, and by 1880 he was a drunk at the Lone Star bar in a county that kept telling him who he'd been. Dell
Sorrell was twenty and wanted to find out. Dr. Orville Tabor came through with a wagon on the Friday and sold a cordial that
promised any man the hand he had at twenty, for as long as he needed it.

The cordial is what the druggist says it is: water, whisky, gentian, burnt sugar and capsicum. Both men bought it
because each needed the other to think he'd taken something, and they drank it at the same wagon without a word. On the
street each looked at the other's right hand, the way a man does when he means to see the draw, and each aimed where he
was looking. The doctor dressed two hands that will never close again, and neither man has been in a fight since.

Penrose's own reading is the honest one and the best: for ten seconds two frightened men decided not to kill anybody.
The ham at Christmas says he believes it.
""",
      open=[("Was Dr. Tabor only a fraud?",
             ["Yes. He sells the same bottle in every county, and most nights nobody draws, and he's gone by Sunday.",
              "No. He's the Bestiary's Mesmerist, and the cordial is his excuse for a long look into each man's eyes "
              "across the wagon tail. He sets where a man will aim. Why he chose the hands is the question a posse "
              "would have to ask him.",
              "He sells it in towns where somebody is about to be killed, and he can tell which towns those are. The "
              "cordial saves nobody. He does, when he can, and charges a dollar for it."])],
      table="""
A gunhand in the posse will hear about Asa Penrose in every saloon from Dodge to Tascosa, and some young man in every one
of them will want to try the gunhand the way Sorrell tried Penrose. If Dr. Tabor's wagon is in town that week, so much the
better. The Bestiary's Drunk with a Gun is what Penrose was before the Saturday, and that's a fight nobody wins.
""")

entry("lookeddoor",
      people=["Crail, A.", "Dorn, Ione", "Amery, J.", "Gaunt, the Reverend Mr."],
      places=["Harlan's Ford, Kansas", "Kansas City"],
      creatures=["The Possessed"],
      callings=["Witch Hunter"],
      threads=["terms", "crailtrial", "namebook", "commission", "degree"],
      when=[(1876, "A. Crail stands silent before a town meeting at Harlan's Ford in March, and the widow Dorn is voted "
                   "out of the township")],
      story="""
A. Crail was twenty years in the trade by 1876, and Harlan's Ford had sent for him because cattle were dying, a child
had stopped speaking, and three wells had gone hard. His practice was to make no accusation and stand in front of a room
until somebody looked at the door. It works more often than a reader would like. A thing wearing a man knows what a
witch hunter is, and a room full of frightened people will watch the door for it.

Two people looked. The widow Dorn looked because her brother-in-law was drunk outside with her team and she was afraid
for the horses, and that's all of it. J. Amery, the clerk, looked first, didn't get up, and wrote in the minutes that she
had. Crail saw both and spoke for neither. He was right about the room, as he says, and wanted to be right about the
woman.

What Amery is, this book leaves to the Keeper. The minutes are the township's memory, and he has kept them sixteen years
without a complaint. If something wears him, it learned early that the man who writes the record decides what happened,
and it has made Harlan's Ford a very orderly township.
""",
      open=[("What is J. Amery?",
             ["Worn. Something has had him since before 1876, and the dying cattle and the silent child were its work, "
              "and it has been careful ever since. Crail has been back four times and can't make up his mind, because "
              "it's better at being a clerk than Amery ever was.",
              "A man. He wanted the Dorn quarter section, which joins his, and the township sold it to him the next "
              "spring.",
              "A frightened man who looked at the door because everybody looks at the door, and wrote down the "
              "widow's name because he couldn't write his own."])],
      table="""
Harlan's Ford is a quiet township with very good minutes. A posse sent there on any errand will find the clerk helpful,
courteous, and the only man in the county who remembers everything. Let them notice that the minutes for March 1876 are
the only page in his hand that has been written over.
""")

entry("haunting",
      people=["Trice, Mr.", "Trice, Mr. (his brother)", "the man who did the noises", "his sister at Gurley's"],
      places=["the Trice house", "Gurley's"],
      creatures=["The Mourner", "The Cold Spot"],
      threads=["fivewives", "revival"],
      when=[],
      story="""
Eleven weeks of it were a hired man at nine dollars a week, and he's told it straight. Mr. Trice's brother
wanted the house sold and the money split, and Mr. Trice wanted his brother to look a fool, so he hired a
man to haunt it: a length of wire under the floor to make the noises, a bucket, a lamp behind a sheet of
tin in the orchard for the light. It worked on the schoolmaster and on two preachers, because a man in a
dark orchard who has been told there's a light will see a light.

The crying was nobody's hiring. It came on four nights in October, from the room at the top of the
stairs that had been the brothers' mother's, and on two of the four the hired man was twenty-two miles
off at his sister's at Gurley's and she's sworn to it. The house has had crying in it before. The elder
Trice brother knows that and the younger doesn't, because the younger was two when their sister was
born in that room and five when she died in it, and nobody in the family has said her name since.

What woke it was the brothers' quarrel over selling the room she's in. What it was doing on those four
nights is the question, and the answer depends on what the house does next.
""",
      open=[("What was the crying for?",
             ["Mourning in advance. One of the Trice brothers died that winter, and the Mourner came four "
              "nights to say so, and nobody in the house understood her.",
              "The sister. She's been in that room since the winter she died, and the quarrel over the house "
              "is the first time anybody's threatened to take it from her.",
              "Nobody knows. The confession is the only paper, and a man who confesses to eleven weeks of "
              "fraud and keeps back the crying is either the one honest thing in the business or the last "
              "joke in it."])],
      table="""
The Trice house makes a good first haunting for a table that's only ever seen frauds: run the wire and
the tin as the whole explanation, let the players catch the hired man, and let the crying start the
night after they leave. If they want the story, the elder brother has it, and it will cost him
something to say his sister's name.
""")

entry("plates",
      people=["Rend, C. Raymond", "Fairweather, Lucy", "Fairweather, Mr.", "Fairweather, Mrs.", "Pease, Wm."],
      places=["Ca&ntilde;on City", "Larimer Street, Denver", "the Arkansas River"],
      creatures=["The Tintype", "The Drowned"],
      threads=["mirror", "returned", "surgeon"],
      when=[(1882, "Lucy Fairweather sits for Wm. Pease on 29 May and drowns in the Arkansas on 18 June"),
            (1882, "C. Raymond Rend makes nine spirit plates at the Fairweather house in November"),
            (1883, "Rend is convicted at Ca&ntilde;on City in May; Pease sends the Fairweathers his print")],
      story="""
Rend was a fraud and he showed the jury how. He copied a photograph of the dead onto a plate at his
rooms, exposed each plate twice at the house, first on the copy and then on the family, and the dead one
came up faint behind a chair. Ninety dollars for nine plates. Mrs. Fairweather still says they were a
comfort, and she's the one who'd know. They hang in her parlour.

Pease's print is the other thing. Lucy Fairweather was nineteen. On 29 May 1882 she came into his rooms
alone on a hot afternoon, in a grey dress with her hair up, and paid sixty cents for one cabinet
portrait, and she didn't give her name and didn't come back for it. She'd come because she wanted a
likeness of herself for somebody her parents didn't know about. Pease saw nothing wrong with her at the
sitting. He made the print from the plate the same afternoon, and in it her hair is down and dark and her
dress clings to her and there's a shine on her face as if she has just come up out of the water.

She drowned in the Arkansas below the town three weeks later. Pease didn't know who she was until he sat
in the courtroom at Rend's trial and heard the family's name. He'd had the print in a drawer for a year,
and he decided it would be worse to keep it than to send it, and he was right, and it was bad either way.
""",
      open=[("How did Lucy drown?",
             ["An accident. She went to meet the young man at the river and the bank gave way.",
              "She meant to. She sat for the portrait because she was leaving him something, and she knew "
              "three weeks before anybody else did.",
              "The river took her. Something in the Arkansas below Ca&ntilde;on City takes one a year, and "
              "her plate caught it coming."]),
            ("What does the third photographer want with the print?",
             ["He has four others like it, from four studios in three territories, and all four of the "
              "sitters drowned inside a month.",
              "He wants to try the plate again. He believes a plate that saw it once will see it twice."])],
      table="""
Pease's camera is the hook. If a plate in his studio can catch a death three weeks early, a posse that
sits for a group portrait before a hard job can find out who isn't coming back, and whether they want to
know is the scene. The third photographer at Denver is a collector with a cabinet of drowned sitters and
a polite interest in the players.
""")

entry("forgery",
      people=["Coyle, T. (marshal)", "Pell child, the", "R&iacute;os, Esperanza"],
      places=["Calvary Crossing", "Pell place, the"],
      creatures=[],
      threads=["pell", "pellnews", "swarm", "sanclavo", "deputy"],
      when=[(1883, "A forged marshal's return on the Pell place, dated 31 April 1882, turns up at the "
                   "Crossing about January")],
      story="""
The forgery was made to be dismissed. There's no 31st of April, the marshal is spelled Coil, the paper is a
commercial stock no county office buys, and the hand isn't Coyle's. Everything about it says don't trust
me except the two things that matter. It says there was a cellar and that there were seven marks in it.
The cellar was in the coroner's return. The seven wasn't anywhere, and it's in the children's rhyme four
months later and nowhere else on earth.

Whoever wrote it had been in the Pell cellar or had sat with somebody who had, and wanted the county to
know what was there without anybody being able to hold them to it. A paper that can't be true can't be
used in a court, can't be quoted in the Banner, and can't cost anybody their place. It can only be read,
and passed round, and remembered by the people who already half knew. That's what it was for: the forger was telling the county the truth in the only form the county
would let stand.
""",
      open=[("Who wrote it?",
             ["Coyle. He wrote the true return first and then the one the county wanted, the way he did with "
              "the old burying ground ([[ref:swarm]]), and this time he couldn't sign the true one. He "
              "misspelled his own name and dated it on a day that doesn't exist so that nobody could ever "
              "hold him to it, and he told Ashby the hand wasn't his in terms the editor didn't print.",
              "Somebody who sat with the Pell girl in her first weeks at the Crossing and heard her count.",
              "Esperanza R&iacute;os, who had been in the cellar the week it happened, and knew that nobody "
              "in the county listens to an old woman and everybody listens to a marshal.",
              "Somebody in your posse, if your table ran Module I. Somebody who went down into that cellar "
              "told it in a saloon at the Crossing, and a man at the next table wrote it down."]),
            ("What was Ashby's one question?",
             ["How the forger knew it was seven and not six.",
              "Whether there had ever been an eighth."])],
      table="""
Let the players hold the forgery before they hold anything else from the basin, and let them laugh at it.
It's the easiest paper in the book to dismiss, and it's the one that's right. If they ever put the
question to Coyle, he'll look at the date for a long while and say there's no such day, and that's all
he'll say, and he'll say it kindly.
""")


# ================================================================ Weather, and Things Taken for Weather
intro("weather", """
The sky does more killing in the Territories than everything in the Bestiary put together, and the
editor put the weather third so the tall tales would come early. Run this chapter as weather first.
A norther that drops sixty-nine degrees in nine hours needs no help to be the worst night of a
posse's life, and the Bestiary's hard country (the Norther, the Blizzard, the Flash Flood) is the
right tool for most of it.

What's behind the four papers is the weather with something in it: a sound, a shadow, a dog still
working a dead man's sheep, and a lightning strike that joined two people across a yard. Only one of
them needs a stat block. The rest are ghost stories, and a table that has been shooting things for a
month will be grateful for one it can't.
""")

entry("norther",
      people=["a drover at Dodge", "a woman at a section house", "Arthur (her husband)"],
      places=["Dodge City", "Fort Marcy, the weather office at"],
      creatures=["The White Death", "The Norther", "The Restless Herd"],
      threads=["weathersong", "aspens", "carrow"],
      when=[(1880, "A norther drops sixty-nine degrees in nine hours north of the Arkansas; nine hundred "
                   "head and two men lost")],
      story="""
The blue norther of 1880 came down on the herds north of the Arkansas at four in the afternoon and was
at eight below by dark. It was a real storm, and the weather office's figures are real, and most of what
it killed it killed the ordinary way. The drover's outfit lost nine hundred head and two men forty yards
from the wagon, and both men were walking toward the sound when they went down.

The sound was in every outfit's account that week and nobody agrees what it was. The drover is half
right. A herd in a wind like that does make a noise like a crowd a long way off, talking at once, in no
language. What he doesn't say is that his two men had worked cattle for years and knew that noise as
well as he did, and walked toward it anyway. Something in the storm that week was calling warm things out
into the cold, the way the White Death does, in the voices of whatever it had already taken. On the
second night it had nine hundred head's worth of voices, and two men's.

The woman at the section house knew both men; they'd boarded with her the winter before, and that's why
she won't write about them to her brother. She heard it all the second night and heard it stop at first
light "the way a man stops talking when somebody comes in". Arthur says it was the wire. Arthur says it
every day. Arthur went out on the second night, too, as far as the gate, and she brought him back in, and
neither of them has mentioned that to anybody.
""",
      open=[("What was the sound?",
             ["Horns and wire, exactly as the men say. The two drovers walked toward it because a man lost "
              "in a blizzard walks toward anything that sounds like other men.",
              "The storm itself, calling. It stopped at first light because it had come as far south as it "
              "was going.",
              "The dead of every norther, walking with this one. The ones it took that week are in it now, "
              "and they'll be in the next."]),
            ("Who came in at first light?",
             ["Nobody. Dawn.",
              "Somebody walking the section line with a lantern, whom Arthur has never asked about."])],
      table="""
Run the storm as the Bestiary's Norther, and put the sound in it on the second night. Anybody who fails
a Dread Check that night hears their own name in it, and a character who walks toward it has to be
brought back by someone else at the table. The section house is the only roof for ten miles, and the
woman there will have the door barred and the lamp lit before the posse knocks.
""")

entry("bird",
      people=["a boy of eleven", "a rancher (who paced the shadow)"],
      places=["the breaks", "Gurley's"],
      creatures=["The Thunderbird"],
      threads=["eclipse", "llano"],
      when=[(1877, "The Territorial Enterprise reports nine gentlemen riding out after a monstrous bird")],
      story="""
Two of the three are what they look like. The boy of eleven was in the yard when a thunderhead came over
the barn with a downdraft in front of it that would sit anybody down, and his father is right and so is
he. The nine gentlemen of 1877 rode out after an eagle somebody had seen at a distance in bad light and
came back with two antelope and a quantity of whisky from Gurley's, and the Enterprise had its fun, and
the one sober man was right that there'd been no bird.

The rancher's account is the third, and it's a Thunderbird, and it's the most honest description of one
anybody has ever given, because he describes only what he could measure. The Thunderbird is older than
the Territories and doesn't think of men at all. It flies where it flies, and most of the time the storm
it brings is all anybody sees of it. On that afternoon it went over with no storm, high in a clear sky,
and it let the sun put its shadow on the grass the way a man walking past a window lets his shadow fall
on the floor, without thinking about the people in the room.

He looked up, and there was nothing there, and he wants that in because it's the part that has kept him
quiet six years. What flies that high and that large can't be seen against the sky by anybody it hasn't
decided to be seen by. His horses didn't move because horses know better than to move under a shadow like
that. He paced it against the corral fence because he's the kind of man who needs a figure, and ninety
feet is the figure.
""",
      open=[("Why was there no storm under it?",
             ["It was going somewhere and wasn't hunting. The weather comes with it when it means to come "
              "down.",
              "It was the shadow of something else entirely, something that casts a shadow on this country "
              "from a sky that isn't this one, and the rancher was measuring the wrong thing."])],
      table="""
The rancher's shadow is the best way to introduce the Thunderbird to a table: long before it's met, put a
ninety-foot shadow across the posse's trail on a clear afternoon, and let the horses stand still under it.
Nobody looks up in time. If the Thunderbird is ever fought, the rancher should be there, pacing out
distances, because he's the one man in the county who knows how big it is.
""")

entry("aspens",
      people=["Goikoetxea, Martin", "Goikoetxea, Jos&eacute;", "Beltza (a dog)", "a camp tender",
              "a herder at Boise"],
      places=["the Owyhee country", "Silver City, Idaho", "Boise"],
      creatures=[],
      threads=["norther", "carrow", "fortclark"],
      when=[(1869, "Martin Goikoetxea of Ispaster cuts his first count in an aspen grove above the Owyhee range"),
            (1879, "Martin Goikoetxea freezes on the winter range in the storm of March"),
            (1882, "The last count in Martin's hand, fifty-eight; his son comes looking for him")]
      ,
      story="""
Martin Goikoetxea came out from Ispaster in Bizkaia in 1868, herded for a sheep company on the Owyhee range
for ten summers, and cut his name and his count in the same aspen grove every year, the way the Basque
herders do. The company's band grew from nine hundred to fifteen hundred under him. In 1878 he carved that
he was going home next year, and in March 1879 the storm caught him on the winter range with the band
scattered round him, and he froze. The company found him. It didn't find his dog.

Beltza gathered what was left of the band. Nine hundred came through the storm, and when the grass came up
on the high range that June the dog took them up to it, because that's where the band went in summer, and
Martin went up with them. He'd been going home next year. He'd been going home next year for ten years,
and a man who has put off going home that long has the habit of staying, and dying didn't break the habit.
He herded them four summers more, and cut the count every year in the same hand, because a herder's count
is what he owes the company and Martin paid his debts.

The band got smaller every year. Nobody wintered them, nobody sold the lambs, the coyotes took their share,
and by 1882 there were fifty-eight. That was the summer José Goikoetxea came from Ispaster, because his
father's letters had stopped three years before and the company's letter hadn't answered anything. He cut
his line in the grove with no year and no count, deep and not neatly, the way a man carves who has never
done it and is angry.
""",
      open=[("What did José find?",
             ["His father, in the grove at dusk with the dog at his heel, who looked at him for a long time "
              "and then gave him the count. José brought fifty-eight sheep and a black dog with one white "
              "foot down to the company in September, and the grove has had no new cut since.",
              "Nothing at all, and he's still up there. The grove has a new count in a new hand next "
              "summer.",
              "The dog, alone, who wouldn't come to him, and the band, which went over the ridge after the "
              "dog, and he's been looking since."])],
      table="""
There's no monster here and the table shouldn't be given one. If a posse is ever on the Owyhee range, let
them find the grove and the counts, and a black dog on the ridge working a band of sheep with nobody behind
it. What they do about it is theirs. The only wrong answer is a gun.
""")

entry("signal",
      people=["a private of the Signal Service", "the Chief Signal Officer"],
      places=["the Panhandle", "Washington"],
      creatures=[],
      threads=["breathing", "llano", "plate", "noinformation"],
      when=[(1882, "On 3 August a signal station in the Panhandle records the barometer falling sixty hundredths in a "
                   "quarter of an hour, with no wind and no cloud"),
            (1882, "In October the Chief Signal Officer tells every station to stop remarking on animals and on how "
                   "the observers felt")],
      story="""
On the afternoon of the 3rd of August 1882 something under the Staked Plain drew a breath. The barometer at a signal
station in the Panhandle fell sixty hundredths and rose again inside a quarter of an hour, which no weather does, and the
two other stations within a hundred miles recorded the same fall at the same minute. The birds left, the dog went under
the steps, and every man at the post put his hands over his ears as if a train were in a cut.

Three weeks later a well-borer in the Neutral Strip broke into a hollow at three hundred and forty feet that breathes
four minutes in and four minutes out, and he capped it on the eleventh day because the breath had turned warm and then
wet ([[ref:breathing]]). The two papers are a hundred miles and many pages apart in the Book of Legends, and nobody but
the Keeper has set them side by side.

The private did his duty and wrote it down, and Washington sent every station a circular telling it not to. It covers up
nothing in particular. It's the Army keeping its weather tidy, and the effect is the same: the only instruments in the
Territories that might have measured the size of the thing under the plain were told to stop mentioning it.
""",
      open=[("What drew the breath?",
             ["What's under the Llano, which is the size of the country and asleep, and the well in the Neutral Strip "
              "is the nearest thing it has to a mouth. [[kb:olddark]] has the rest of it, and never says.",
              "A meteor that burst over the Staked Plain in full daylight and was never seen for the sun, which would "
              "move the glass and frighten the birds and leave nothing to find.",
              "Nothing. A train knocked all three barometers at once. The Keeper is welcome to believe it."])],
      table="""
The private is still in the Signal Service and would be glad to talk to anybody who doesn't laugh. His station journal
for 1882 has three more remarks the circular would never have forwarded, and he copied them into a book of his own
before he obeyed it.
""")

entry("lineman",
      people=["Keough, Dan", "Keough, Tom (his brother)", "the woman in the kitchen"],
      places=["Rock Creek", "Laramie", "Rawlins", "Council Bluffs"],
      creatures=["The House That Hungers", "The Wake"],
      threads=["plates", "mirror"],
      when=[(1883, "Lineman Dan Keough is struck by lightning at the top of a pole west of Rock Creek in July"),
            (1884, "Keough writes that he is going across the yard, in April, and doesn't write again")],
      story="""
The lightning that knocked Dan Keough off a pole west of Rock Creek in July 1883 went through him into the
wire, and forty miles of wire carried it to a house at the edge of a railroad town where a woman was
standing at her kitchen table with her hands in a bowl of dough. She felt it in her wrists. After that,
three or four times a week, for a minute at a time, Dan was behind her eyes.

She's a widow who keeps a boarding house, and the kitchen with the blue shelves and the window over the
dry creek and its one cottonwood is hers. Dan rode half the creeks between Rawlins and the Medicine Bow
looking for that window and never thought to look at a boarding house in a railroad town, which is the one
kind of place a lineman sleeps in. The hands he watched kneading and sewing a button on a man's shirt were
hers, and the shirt was a boarder's. The letters she's been writing lately are to nobody in particular. A
widow who has been looked at by nobody for four years and then, for a minute at a time, by somebody, writes
letters.

In April he took a room across the yard from her kitchen without knowing it, sat down at the table by the
window to write to his brother, and saw himself through her eyes. What he saw is a man at a table in his
shirt, writing, which is to say she was looking at him. She'd been watching him since Tuesday and hadn't
known why. He went across.
""",
      open=[("What was across the yard?",
             ["Her. They were married at Rawlins in June, and Dan doesn't write to his brother because he's "
              "happy and has never been a letter-writer when he's happy, and the rubbed postmark is Rawlins.",
              "A house that knew how to be looked into, which had been showing him a kitchen for nine months "
              "the way a lamp in a window is shown to a man lost on the prairie, and it closed round him when "
              "he came in.",
              "His own kitchen, from the other side. Dan Keough died on the pole in July, and what's been "
              "writing to Tom since is a man watching his own life go on without him through a window, and "
              "in April he went to join it."])],
      table="""
Tom Keough is the posse's way in: a hotel keeper at Council Bluffs with three letters and no answer, who
will pay somebody going west to find his brother. The trail ends at a boarding house with a cottonwood in
the dry creek and blue shelves in the kitchen, and what the posse finds when the widow opens the door is
the Keeper's choice above. Choose it before they knock.
""")


# ================================================================ Paper, Ink & Interest
intro("paper", """
The editor calls this the worst chapter in the book and is right, and the reason is that there's
almost nothing behind these papers that a Keeper has to supply. The clauses are real. The will was
proved. The census was taken. The bank wrote down that it didn't know why its wells were coming back.
The horror was done at a desk, in ink, by people who'd be offended to be called anything but
businessmen, and the stories below mostly say who held the pen.

This is also the chapter where the threads cross: the Vane house and Kansas City, the Long Table's
ninth children, the Golden Circle's list. [[kb:powers]] is the Keeper's Book's account of the Powers
behind the paper, and it asks for no more than one thread lit at a time. The entries here are written
so they can be.
""")

entry("clause",
      people=["an attorney on Delaware Street", "the lawyer at the capital"],
      places=["Kansas City", "Delaware Street, Kansas City"],
      creatures=["The Ledger of the Territory", "The Tallyman"],
      threads=["paidinfull", "vane", "contract", "kansas"],
      when=[(1874, "The first note carrying the clause is written; three houses in two territories use it "
                   "by 1883")],
      story="""
The clause was written in 1873 by an attorney in a building on Delaware Street in Kansas City, for a client
who wanted a form a country bank could print in its notes. He knew it was void when he wrote it. He wrote it
because it would never be tested, and he was right about that too. A bank doesn't carry this clause into a
courtroom. It carries it to a kitchen table.

A homesteader in default is shown his note by a pleasant man from the bank, who reads him the clause slowly,
and explains that the holder may satisfy the debt out of the labour of any person in the household over
fourteen, at a valuation fixed by the holder's agent, and asks after the boy. The homesteader can't read,
or can read and doesn't know what void means, and has never seen the inside of a court and isn't going to
start with a bank for an opponent. The boy goes to work for the bank's agent to pay the note down. That's
how the clause is used, a few hundred times a year across two territories, and never once in a way that
would put it in front of a judge.

The agent is the profession Ashby went looking for. He's a labour contractor with an office on the levee at
Kansas City, who places boys of fourteen with grading gangs and mines and cattle outfits at a fixed rate and
remits the wages to the bank against the note. His books are very neat. The rate at which a boy's work is
valued never quite catches the interest on the note, so the note never quite closes, and a boy placed at
fourteen is often still being placed at twenty.
""",
      open=[("Who was the client in 1873?",
             ["A correspondent bank in Kansas City that has four or five railroad men behind it, which is to "
              "say the Ledger, and the clause is one of its hands.",
              "Josiah Vane's predecessor at the Coffin Wells house, which is why the Vane Banking House uses "
              "it.",
              "Nobody the attorney ever met. The commission came by letter with the fee in gold, and he "
              "kept the letter, and the letter is in a hand he has seen once since, on a land warrant."]),
            ("Has anybody ever come for the labour of a person without going through the agent?",
             ["No. The clause is paper, and paper is enough.",
              "Once. A note held by a house that had stopped being quite a bank came due at a claim on the "
              "Saline, and what came to value the household wasn't the agent, and carried a ledger under its "
              "arm."])],
      table="""
Give the players a boy of fourteen working a grading gang who can't leave because his family's note will
fall due, and let them find the clause behind him. Then give them the lever that works, which is a lawyer:
the clause breaks the first time anybody takes it to a judge, and every family it's ever been read to is
free the day a posse makes it public. It's a fight won in a courthouse, and the Ledger will write the
loss off and use a different form next spring.
""")

entry("will",
      people=["the testator (a careful man)", "his executor", "his eldest daughter", "the ninth child"],
      places=[],
      creatures=["The Ninth Child", "The Dread Mother"],
      threads=["ninth", "ninechairs", "witch", "harrow", "tithe"],
      when=[],
      story="""
Three generations back, a woman of this family nearly died in a bad birth on the Trinity and was kept alive
by a house of the Long Table, and so was her daughter after her, and her granddaughter through the fever
that took eleven others in the county. The family's luck has been remarked on ever since, because it's real,
and it's bought. When the Ninth Child came to the porch with the dates, the careful man's father was one of
the families in nine that say yes.

The arrangement is exactly what the will says. The ninth child of the line, counted the way the Table counts,
which includes the ones who didn't live, goes to the house at the age of two. No money is paid, because the
Table doesn't pay. In return the house goes on keeping the family, and the eldest of each generation keeps
the arrangement in his own family, and so on while the name holds. The careful man's mother saw her ninth
child once, at the time. The executor has notice because the executor is from a family the same house keeps,
and has an arrangement of his own.

The eldest daughter who read the chapter before it was set has the clause in her own will, in the same words,
and has never been told what it means, because her father meant to tell her and was careful and died first.
She'll find out the way the family always finds out, when her own ninth is two and somebody polite knocks at
a decent hour.
""",
      open=[("What is the ninth child for?",
             ["The Keeper's Book leaves this open and so does this book. Decide it once, before the first "
              "ninth child is met, and use it everywhere: [[ref:witch]] would have told Ashby over supper, "
              "and [[ref:harrow]] asked in her fortieth year and rode.",
              "One answer that keeps the Table as frightening as the Keeper's Book wants it: the ninth "
              "children are the Table. Every woman who keeps a seated house was somebody's ninth, and she "
              "was raised to it, and loved, and she'll go to the porch herself one day with the dates.",
              "A harder one: they are paid onward. The Table owes something older than itself, and the "
              "children are the instalments, and the women of the houses don't all know it."]),
            ("Where is this family's ninth child now?",
             ["In a seated house in another territory, grown, and keeping it.",
              "Nobody in the family knows, and the executor, who does, is old."])],
      table="""
The eldest daughter is the scene. She read the chapter, knows the clause is in her will, and would pay a
posse well to find out what it means. What they find is a house of the Long Table that has kept her family
alive for three generations and will explain, politely and truthfully, what it's owed. The Bestiary's Ninth
Child says what a family can offer instead. The answer is never the gun.
""")

entry("censuses",
      people=["Pardee, Amos", "Pardee, Mercy", "Pardee, Luther", "the other one", "the enumerator of 1885"],
      places=["an upper valley"],
      creatures=["The Devourer's Tongue", "The Star-Spawn"],
      threads=["will", "thirdcell", "dugout"],
      when=[(1879, "Amos Pardee buys a hundred and forty head of cattle, and a hundred and twenty-eight "
                   "go 'died, strayed or stolen'; his grandson is born"),
            (1885, "The territorial census counts 'the other one' in the Pardee household at the head's "
                   "insistence")],
      story="""
Amos Pardee was a farmer with a shelf of old books in a language his neighbours couldn't read, and he'd spent
thirty years reading them. His wife died in 1875. In the spring of 1878 his daughter Mercy, who was twenty-four
and had never been further than the valley's mouth, was taken by her father up the ridge above the farm on the
first night of May, and nine months later she bore twins. One of them was Luther, who's six now and at school
and a quiet, clever boy. The other one was never baptised and never shown to anybody.

It eats. That's what the agricultural schedule records, in the dry way of a government form: a hundred and
forty head bought in 1879, none sold, none slaughtered, a hundred and twenty-eight died, strayed or stolen and
not recovered. Pardee bought his stock in three counties and never in the valley, so that nobody who sold to
him would see how many he needed. It lives in the upper floor of the barn, and it has grown faster than Luther,
and in a bad light it's hard to see where it stops.

In 1885 Amos insisted it be counted. The enumerator was paid by the head and didn't argue, and wrote down what
he was told. Amos wanted it on the rolls because a thing the government has counted is a person, with a line
of its own in a book at Washington, and Amos has read enough to know that a name written down is a door that
has been opened. He's sixty-nine. He's getting it ready for something, and the census was the first step.
""",
      open=[("What is the other one?",
             ["The Keeper's Book lets a face be named here, since this is no part of the basin. The Devourer, "
              "if it's the cattle you want the table to remember: a hunger with a body, still growing.",
              "Something from outside the country altogether, called down from the ridge by the old books, "
              "which isn't any face of the Old Dark and doesn't care about any of them.",
              "Luther's brother, and a boy, deformed at birth and hidden by a mad old man, and the cattle "
              "went to a rustling ring Amos was paying off. The enumerator saw nothing because there was "
              "nothing to see but a locked door."]),
            ("What is Amos getting it ready for?",
             ["To be let out, on a night written in one of his books.",
              "To be counted again in 1890, by the federal census, and entered as his heir."])],
      table="""
The census sheet is the handout, and the arithmetic in the margin is the hook: a hundred and forty bought,
twelve on hand, none sold, none eaten. A posse sent to the upper valley on any business will meet Luther on
the road from school, who is polite and has read more than they have and knows what's in the barn. Mercy is
the one to talk to. She hasn't been asked anything by anybody in six years.
""")

entry("enumerators",
      people=["Tullis, Amos", "the supervisor of census, Southern District of California", "a gentleman from Jubilee"],
      places=["San Diego", "Jubilee"],
      creatures=[],
      threads=["censuses", "river", "understanding", "noinformation", "plenty"],
      when=[(1880, "Paragraph 41a tells the census not to count anybody beyond the branch's crossing of the lower "
                   "Colorado; Amos Tullis goes up the branch anyway and counts eight thousand four hundred and twelve"),
            (1881, "Amos Tullis burns his Jubilee schedules after a gentleman from Jubilee asks to buy them")],
      story="""
Paragraph 41 is the census's ordinary rule, and 41a is the exception that unmakes a town: no persons beyond the crossing
of the branch, no inquiry, no schedules received or paid for. It went to one district in the country. The Census Office
never said why, because it didn't have to. A paragraph is a paragraph.

Amos Tullis went up the branch on his own account in June 1880 and counted every soul at Jubilee who'd answer him, and
every soul did, politely, as Jubilee does everything. His supervisor returned the schedules unpaid. In 1881 a gentleman
from Jubilee came to his house at San Diego and offered a dollar a sheet, and when Tullis refused, the gentleman said it
didn't matter, because the Census Office had already refused on Jubilee's behalf. The two governments wanted one thing:
that Jubilee be counted by nobody but itself.

Tullis burned them that night. He's an honest man and couldn't say why, and the reason is the one the old clerks at
Washington believe in [[ref:understanding]]: he didn't want to be the only place they were written down. Being the only
record of a thing is a weight in this country, and he felt it before he knew what it was.
""",
      open=[("Why does Jubilee not want to be counted?",
             ["A census is how a government says a place is its own. Jubilee would rather be missing than be part of "
              "San Diego County.",
              "Because the Circle's list is a count of its own, and the people on it are what a census would number. "
              "Nobody at the Treasury could say more than that."]),
            ("Did he burn all of them?",
             ["Yes, every sheet.",
              "All but one, the sheet for the block round the seminary, which he couldn't make himself put in the "
              "stove, and still has."])],
      table="""
Tullis is a quiet clerk at San Diego with a story he's told once, to Ashby. A posse that needs to know who lived in Jubilee
in 1880 needs the one sheet he kept, if the Keeper lets him keep it. Every name on it is somebody the country remembers
and Washington doesn't.
""")

entry("patent",
      people=["Vail, Emmett", "an examiner of the Patent Office", "Vail, Mrs. (his widow)"],
      places=["Leadville", "Washington"],
      creatures=["The Tommyknocker", "The Veinwork"],
      callings=["Engineer"],
      threads=["lamps", "adit", "assay", "veinwork", "sanclavo"],
      when=[(1882, "Emmett Vail of Leadville applies to patent a lamp that shows what's in the dark, and withdraws when "
                   "asked for a working model")],
      story="""
Emmett Vail was a mine engineer at Leadville who noticed what every miner knows and no engineer writes down: a lamp carried
into certain workings gives less light than it gave at the collar, in good air, with a sound wick. He set out to build a
lamp the place couldn't dim, and he did it with a gauze of one metal in one proportion, and the drawings name the metal,
and it's silver. The padres at San Clavo would have understood the choice ([[ref:sanclavo]]).

The second claim is the one that made the examiner call it inoperative: in its light, anything present is shown. The
night shift at the three-hundred level carried it every night for four years and came up every morning, and in all that
time it showed them things in the drifts that the shift never mentioned to anybody above ground. That's why they wouldn't
go down without it, and why Vail wouldn't send it to Washington as a model.

The Patent Office's letter is the government's answer to a good deal in this book. The Office isn't informed that the
condition exists, so it can't allow a remedy for it. Washington is consistent. It doesn't patent a lamp for a dark it has
never recorded.
""",
      open=[("Where is the lamp?",
             ["With the shift's oldest hand, who left the camp after Vail died and went to the Blue Tinaja country, "
              "where the notes on the rock ([[ref:adit]]) stopped coming the same year.",
              "In a mine nobody will name, at the three-hundred level, still going down every night, because the man "
              "who took it couldn't work without it either."]),
            ("What does it show?",
             ["The Bestiary's Tommyknockers, plainly, and most miners would be glad to see them.",
              "Whatever is in the drift, and in the men. The shift learned not to hold it up to each other's faces."])],
      table="""
An Engineer in the posse is the one who'll understand Vail's drawings, and his widow has the drawings. Building a second
lamp is a fine long project for a table that likes to make things. Decide what it shows before anybody lights it, and show
it once.
""")

entry("feebill",
      people=["Fenwick, H. (deputy marshal)", "Lockhart, Jas.", "the jailer at Fort Smith",
              "an examiner of the Department of Justice"],
      places=["Fort Smith", "the Kiamichi", "the Red River"],
      creatures=["The Revenant", "The Risen"],
      callings=["Marshal"],
      threads=["returned", "swarm", "claim", "undertaker"],
      when=[(1883, "Jas. Lockhart dies at Fort Smith in March; Deputy Marshal H. Fenwick serves a warrant on him on the "
                   "Kiamichi in May and brings him in")],
      story="""
Jas. Lockhart died at Fort Smith in March 1883 of a fever, and H. Fenwick helped bury him. A warrant for larceny was issued
in May by a clerk who hadn't been told, and Fenwick was given it, and rode two hundred miles to the Kiamichi, and found
Lockhart there, and knew his face because he'd shovelled dirt onto it.

Fenwick is a deputy United States marshal of the Western District, which pays by the service and the mile, and he did his
duty. He pursued the defendant nine days to the Red River with one posseman, took him, and brought him back. The jailer
fed what he brought in for two days. Then the jail released the same prisoner to the deputy, with no name given for
either, and Fenwick rode out with it and came back without it, and the Department disallowed every item that would admit
it had happened.

What Lockhart was is the Keeper's to decide, and the Bestiary has two things that fit. Fenwick knows what he did on the
third day and will tell a posse that's earned it. He served eleven more years, and his returns are the neatest in the
district, because he learned that summer how little a return can hold.
""",
      open=[("What came back from the ground at Fort Smith?",
             ["The Bestiary's Revenant: Lockhart, with a grievance, going back to settle it.",
              "A Risen, with no grievance at all, walking the way it walked in life, and stealing the way it stole."]),
            ("What did Fenwick do with it?",
             ["Took it back to the burying ground on the third night, put it in again with salt and his own iron, and "
              "sat up with it.",
              "Took it to somebody who knew better than he did what to do, and paid them out of his own pocket, which is "
              "why he wanted items 3 to 5."])],
      table="""
Fenwick is a fine Marshal for a posse to ride with, and the best man in the book to teach a new Marshal what the job is out
here. Bring him a warrant on a man who's dead and he'll take it without a word, and ask only for a second posseman.
""")

entry("landoffice",
      people=["the register of a land office (later a storekeeper)", "the Commissioner of the General Land Office",
              "the man who speaks for the people of the mesa"],
      places=["Painted Mesa, the", "Washington"],
      creatures=["The Parcel"],
      threads=["twosections", "gold", "mesa", "lookedat", "understanding"],
      when=[(1883, "A territorial land office takes eleven cash entries in gold from one agent; the Commissioner rules "
                   "that he isn't concerned with a purchaser's motives")],
      story="""
Eleven tracts in a quarter, every one by the same agent, every one in gold, none of them able to support a family. The
register was an honest man and wrote to Washington to ask whether entries like that should be received. Two of the tracts
were on the Painted Mesa, under a people who had been there before the Spaniards and had filed nothing, because nobody had
told them it was required.

The Commissioner's answer is the whole chapter's policy in two sentences. The Office isn't concerned with motives, and it
isn't concerned with any occupancy it has no record of. A government that won't write a thing down can't be asked to
protect it. The people on the mesa, who are on no paper at Washington, are as invisible there as the country on the
Colorado that's buying their ground: unrecorded for opposite reasons and to the same effect. The Circle's agent pays in
gold through the gap between them.

The register resigned the next spring. The man who speaks for the mesa came into the office once more, a year later, stood
in front of the plat on the wall, and asked nothing. What he was thinking is his, and this book leaves it there.
""",
      open=[("What does the register know?",
             ["The agent's name, which was Purcell, and the name of the bank that sent Purcell the money, which was at "
              "Kansas City.",
              "That the other nine tracts lie in a ring when you draw them on a large enough map, and that he drew "
              "them, and put the map in his stove."])],
      table="""
The register keeps a store now, and he'll talk land law with a posse for an hour and the mesa for a minute. Keep the mesa
people as the Book of Legends keeps them: neighbours with a spring and every reason to want to be left alone, who watched
the stakes go in and asked to have their watching written down.
""")

entry("plate",
      people=["Kroll (an engraver)", "Cadwell &amp; Lowry, publishers of maps"],
      places=["Chicago", "Siding No. 4", "Jubilee"],
      creatures=[],
      threads=["novel", "spur", "remarks", "understanding", "enumerators"],
      when=[(1882, "A Chicago map house has its engraver take Jubilee and the branch beyond Siding No. 4 off the plate of "
                   "Southern California and Arizona")],
      story="""
The map house had a plate of Southern California and Arizona with Jubilee on it, laid out in blocks, with the branch
running in from the river and the word Customs at the crossing. In March 1882 the General Land Office let it be known that
it wouldn't take a map that showed them, and school boards take only the maps the Land Office takes, so the house had Kroll
stipple the town into desert and run the branch out to the water tank at Siding No. 4, where it stops.

Kroll did good work both times. He couldn't move the river and said so, and every map of that country printed since shows a
railroad laying forty miles of track to a water tank in the sand. Children learn their geography from those maps. A child
born after 1882 will grow up without ever having seen Jubilee on paper, and that is one of the ways a country everybody
knows about becomes a country nobody remembers.

The three street names in pencil in the margin of the old proof are the engraver's, written the day he took them off the
plate. He didn't trust himself to remember them, and he was right not to.
""",
      open=[("What are the three streets?",
             ["Leviticus Street, Straughan Street and Treasury Row, and the last runs straight to the seminary.",
              "Three names the engraver couldn't afterwards remember writing, in a hand his son says isn't quite his."])],
      table="""
The before-proof is a treasure for a posse that needs a plan of Jubilee, and the engraver's son has it. Give it to the
players as a handout, streets in pencil. Then let them buy a current map at Yuma and lay it beside the proof.
""")

entry("deadletters",
      people=["A. T. (a clerk of the Dead Letter Office)", "the mothers who write to Jubilee"],
      places=["Washington", "Jubilee", "New Orleans"],
      creatures=["The Dread Mother"],
      threads=["hear", "seats", "noinformation", "novel", "spur"],
      when=[(1883, "The Dead Letter Office opens the quarter's letters addressed to Jubilee and returns them; the letters "
                   "to the Mother at New Orleans go unopened, by standing order")],
      story="""
Two silences sit on one page of the Dead Letter Office's return. The letters to Jubilee are opened and sent back, because
there's no Jubilee to deliver them to and the railroad's bag isn't the government's. Nearly all of them are from mothers,
and nearly all of them ask the same thing, and the clerk who wrote to Ashby has read hundreds.

The railroad carries the town's own bag up and down, and the town decides what goes in it. Jubilee reads its people's
letters coming and going, and a letter home that says the wrong thing doesn't arrive. That's why the mothers aren't
answered. Washington returns their letters and Jubilee wouldn't let the answers out, and between the two governments a
young man who went up the branch in 1879 has gone silent.

The last line of the return is a different matter. Letters to the Mother at New Orleans aren't opened, by a standing order
older than 1874, which nobody at the office can trace. [[kb:powers-mother]] has the Dread Mother, and this book won't say
how a woman in a courtyard below Canal Street comes to have a standing order in the Post Office Department. A great many
families have been kept alive by her houses, and some of them went to Washington and did well.
""",
      open=[("Who gave the standing order?",
             ["A Postmaster General's wife, whose first child was delivered by a house in the bayou parishes in the "
              "fifties, and who asked.",
              "Nobody living. It was given in the fever year of 1853 by a clerk who opened one, and it has been copied "
              "into every new instruction book since, because no clerk dares be the one who leaves it out."])],
      table="""
A posse that needs to get a letter to a son in Jubilee will learn quickly that the Post Office can't and the railroad won't.
A letter addressed to the Mother is stranger. It arrives, and sometimes it's answered, and the answer is never in writing.
""")

entry("noinformation",
      people=["a captain of the Fort Yuma garrison", "the Secretary of War", "a member of Congress",
              "a clerk of the Adjutant General's office"],
      places=["Fort Yuma", "the Customs Post at the river", "Jubilee", "San Francisco", "Washington"],
      creatures=[],
      threads=["understanding", "remarks", "tenth", "spur", "enumerators"],
      when=[(1882, "A captain from Fort Yuma reports a nation on the lower Colorado in April; in June the War Department "
                   "endorses the report File. No action."),
            (1883, "The Secretary of War tells a member of Congress that the Department has no information of any "
                   "organized community there")],
      story="""
The captain rode up the California side with fifteen men and saw everything: the brick customs house, the flag, four men in
grey who asked for papers and didn't insist, a town of eight thousand, a square full of drilling riflemen, the best fields
in the Territory. He wrote it down properly and asked for instructions. The report went up through three headquarters and
each one forwarded it, and at Washington somebody initialled File. No action.

Eleven months later the Secretary of War told a member of Congress that the Department had no information. That was true in
the Department's own sense, because a paper that has been filed isn't information; information is what's on a desk. The
Army gave up the post at Fort Yuma the year after, for reasons of economy, which were also true.

This is the silence working the way [[ref:understanding]] says it works. Nobody decides to hide a country. The Army decides,
each time, not to be the office that sees it, and the paper goes up until it reaches the one office that can write File, and
there it stops.
""",
      open=[("Who initialled File?",
             ["The chief clerk of the Adjutant General's office, on a word he'd had in a cloakroom. He's the retired "
              "clerk of [[ref:understanding]], and his letter to the editor is as near as he'll come to confessing it.",
              "Nobody living. The initials are a clerk's who died in 1883, and the clerk who copied the report for Ashby "
              "asked for nothing because of what he'd found in the file next to it."]),
            ("What became of the captain?",
             ["He's still serving, at a post in Dakota, and keeps a copy of his report in his trunk.",
              "He was retired for his health in 1883, and his health was perfectly good."])],
      table="""
The captain is the Army officer a posse can find who has seen Jubilee with his own eyes and put it in writing. He'll say
nothing in public. He'll say a great deal to a posse that brings him proof somebody else has seen it too.
""")

entry("remarks",
      people=["Calder, J. P.*", "his private secretary", "the Speaker of the House"],
      places=["Washington", "Atchison, Kansas", "Kansas City"],
      creatures=[],
      threads=["understanding", "sixes", "noinformation", "degree", "novel"],
      when=[(1882, "Representative J. P. Calder of Kansas speaks nine minutes on the lower Colorado in February; his "
                   "remarks are revised eleven times and withdrawn in July")],
      story="""
J. P. Calder was a Kansas Republican and a Union veteran who couldn't stand it, and on the 9th of February 1882 he asked the
House for five minutes and took nine. He said what the captain's report had said and more: a Confederacy in arms on the
Colorado, the same war in a new coat, and every member in the room knew it. The House was as quiet as his secretary ever
heard it.

Members revise their remarks before the Record prints them, and Calder revised his eleven times. Gentlemen came to the
boarding-house from both sides of the aisle, from the War Department, and one from Kansas City, all of them civil, and
each draft was shorter than the one before. What they told him was always the same: what was settled in 1877 was settled
whole, and pulling at one corner pulls the rest out after it. The end of Reconstruction, the disputed election and the
river were one bargain, and a man who reopened the river reopened the South.

He withdrew the last draft and wasn't returned at the next election. The Record prints every word of that session down to
the duty on hides, and its only nine minutes of silence are his.
""",
      open=[("Did anybody keep the speech?",
             ["His secretary took it down in shorthand, and the shorthand book is the only full account. He has it still "
              "and would part with it to somebody who meant to use it.",
              "Calder burned his drafts and the secretary's book with them, and all that's left is what the secretary "
              "remembers, which is the phrase about the new coat."]),
            ("Who was the gentleman from Kansas City?",
             ["A man holding a great many Redemption Sixes ([[ref:sixes]]).",
              "A man of the Circle's third degree ([[ref:degree]]), the statesmen, with a house in Kansas City and a "
              "seat on a railroad board, who is in nobody's book."])],
      table="""
Calder keeps a hardware store at Atchison and doesn't discuss politics. A posse that comes into his store with a reason to
will find the angriest man in Kansas, kept in a drawer. His secretary is the easier contact, and he has the shorthand.
""")

entry("understanding",
      people=["a clerk of the War Department (retired)", "the gentlemen at Wormley's"],
      places=["Washington", "Wormley's hotel", "Plenty, Colorado"],
      creatures=[],
      threads=["remarks", "noinformation", "enumerators", "plate", "novel", "plenty", "coyle", "sixes"],
      when=[(1877, "The conference at Wormley's hotel settles the disputed election; the retired clerk was told it "
                   "settled the lower Colorado too"),
            (1886, "A retired clerk of the War Department writes to the editor to explain why Washington won't see "
                   "Redemption")],
      story="""
This is the paper that answers the players' question, written by the one man in the book who was close enough to the
machinery to say how it runs. It isn't a conspiracy, he says, and he's right. It's a policy, and a policy at Washington is
mostly the absence of a paper.

His three reasons are true in the Keeper's hands as much as in his. A country Washington doesn't recognise can't be at war
with it, and Washington can't lose to it, and the Army would rather not find out. The bargain that ended Reconstruction in
1877 was struck in a hotel and never written down, and he heard from men in the room that it left the river alone. And the
Treasury of Redemption pays its interest in gold, on the day, to men whose names a posse would know ([[ref:sixes]]).

His fourth thing, which he says is no reason, matters most to this game. The old clerks at Washington believe that a place
left unwritten at Washington for a generation isn't there afterward, for anybody. He doesn't believe it. He points at Plenty
([[ref:plenty]]), whose post office was discontinued in 1881 and whose creditors can't find it. In this country the belief
is older than Washington. Marshal Coyle keeps his day-book by it ([[ref:coyle]]), the keeper at the mission keeps the count
by it, and the saying in [[ref:sayings]] is that the country keeps books. Washington is running the oldest rule in the
Territories backward, and it may be working.

So, if the Keeper wants a reason why nobody today has heard of Redemption, here it is. Everybody in the Territories knew
about it in 1884. Washington never wrote it down, the maps were redrawn, the novels changed, the census never counted it, and
the Record kept nine minutes of silence. By the time the boys who'd read the first edition were old men there was nothing
on any shelf to say it had been there, and the country, which keeps books, had nothing in its books either.
""",
      open=[("What becomes of Redemption in the end?",
             ["The forgetting is only paper. Redemption goes on as long as the Circle's list does, and when the list is "
              "finished the country goes wherever the list was taking it, and Washington's silence means nobody ever "
              "asks where. The Keeper decides what the list is for ([[ref:gold]]).",
              "The forgetting works. A generation after the last paper is filed, Jubilee is a townsite like Plenty: "
              "watered streets, gardens, a seminary, nobody in it, and no sign of a removal. Its people went where "
              "unwritten places go.",
              "It ends the ordinary way, in a war nobody calls one, some time after 1890, when a President who owes "
              "nothing to 1877 sends the Army. The papers about that are filed too, and the fire that took most of the "
              "census of 1890 took what was left.",
              "A posse ends it. Everything in this chapter is evidence somebody kept: Tullis's sheet, Kroll's proof, "
              "Calder's shorthand, the captain's copy. A table that puts them in one place in front of one honest office "
              "makes Redemption real at Washington, and has to live with what Washington does next."])],
      table="""
This letter is the thing to give a player who asks why they've never read about Redemption in a history book. It answers in
the game's own voice and leaves room. The fourth way above makes a fine second-year campaign for a posse that has met
Kinnear, Calder's secretary and the captain: gathering the record of a country two governments want unwritten, and deciding
whether to deliver it.
""")

entry("salt",
      people=["the major commanding a post on the Pecos", "the Quartermaster General"],
      places=["a post on the Pecos", "Horsehead Crossing"],
      creatures=[],
      threads=["surgeon", "walker", "claim", "fortsafe"],
      when=[(1880, "A four-company post on the Pecos requisitions forty wagon loads of salt for the preservation of the "
                   "post, and gets them")],
      story="""
The post on the Pecos was built in 1878 on a stretch of river the Army's own guides had told it not to build on, and by 1880
the major commanding it knew why. He couldn't put that in a requisition, so he asked for forty wagons of salt and wrote that
it was for the preservation of the post, which was exactly true. The Quartermaster General filled it. The old quartermaster
who asked the editor which post had seen a requisition like it before, from the same major, two years later.

The salt went down in a ring round the post, under the edge of the parade ground, and twice round the post cemetery. It held
three summers, and the surgeon's letters ([[ref:surgeon]]) begin the summer a new well was dug through it. The drowned men he
saw in a dry country were the river's, and the river at Horsehead Crossing was taking people before the Army came. It took a
horse-breaker named Wes in October 1883 ([[ref:walker]]), or he says it did.

The major is the only officer in the book who acted on what he saw instead of filing it, and he did it by filing something
else.
""",
      open=[("What's in the river at Horsehead?",
             ["The Long Trail's ford: a place where the dead are walked across, and the living drown in the press of them.",
              "Nothing at all. Horsehead is a bad ford with a bad bottom on the worst river in Texas, and a man who sees "
              "drowned men in a dry country is seeing the ford in his own head."])],
      table="""
The salt ring makes a set piece: a posse at the post the night it has to be laid again before dark. A Witch Hunter will know
at once what the requisition means. A Marshal will know what it cost the major to write it.
""")

entry("foreclosure",
      people=["Vane, Josiah", "Drayton (of Kansas City)"],
      places=["Vane Banking House, the", "Coffin Wells"],
      creatures=["The Parcel", "The Ledger of the Territory"],
      threads=["vane", "water", "paidinfull", "satchel-wells", "gold"],
      when=[(1884, "The Vane house reports to Kansas City that the wells on its own sections are coming back, "
                   "cause unknown")],
      story="""
This is a routine quarterly summary from the Vane Banking House to its correspondent, and every figure in it is
true. Sixty-one notes written against twenty-two a year before, forty-four of them on sections with a failed
well. Nine foreclosures. Thirty-one sections held by the house. And on those thirty-one, eleven wells reported
sweet, where the county at large has lost a well a month.

The house's land is getting its water back and nobody else's is, and the house has written down that it doesn't
know why. The editor believes it, and is right to. Josiah Vane doesn't know. He watches the figure the way a
man watches a card he's been dealt without asking for it, and he writes "improving" because Kansas City likes
the word.

Why the wells come back on the bank's land is the question the Keeper answers, because [[kb:basin-keeping]]
says what's under the water is yours to decide and never say. Every answer below works under any of the faces.
Pick one and let the players find it slowly. Each of them makes the bank's land the worst place in the basin
to drink.
""",
      open=[("Why are the bank's wells coming back?",
             ["Wages. The thing under the basin pays the hand that opened it, and the bank is the hand. What "
              "Vane was promised at the grave was that what's his would be watered, and it's being kept.",
              "The water takes one or two, and a section a family has been foreclosed off is a section with "
              "nobody on it to take. The thing fouls the wells people drink from. Where the people are gone, "
              "the water comes back sweet, and it will stay sweet until somebody moves in.",
              "Somebody is renewing nails where nobody's watching. A keeper who can't work on a homestead with "
              "a family at the window can work at night on an empty section the bank has shut up, and has been.",
              "The land is being put under one title, and land under one title inside a closing bound becomes "
              "agreeable. The bank's thirty-one sections are a corner of something larger, and Kansas City has "
              "the map."])],
      table="""
Put the summary in the players' hands when they've already seen two homestead wells fail, and let a player do
the sum the editor did: eleven of thirty-one, against six of six. Then sell them a foreclosed section with a
sweet well at a very good price. Whichever answer you picked, living on it is how they find out.
""")

entry("emigrants",
      people=["Wickliffe, Thos.", "the agent of emigration at Galveston"],
      places=["Nicodemus, Kansas", "Galveston", "Ellis, Kansas"],
      creatures=[],
      threads=["warrants", "letterhome", "lady", "tenth", "river"],
      when=[(1880, "The Treasury of Redemption posts its circular To the People of the South at depots across Texas and "
                   "Georgia; one comes back from Nicodemus with an answer on its back")],
      story="""
The circular is Redemption's recruiting, and it went up every spring at depots and landings across Texas and Georgia,
and it worked. Most of the people at Jubilee came out on one. It offers wheat land, water by the ditch, a seminary, and a
country where no man is asked to apologise for his father, and it says plainly, to anybody who knows the word, what it
means by the right sort.

The people at Nicodemus knew the word. They'd come to Kansas from Kentucky in 1877 and from Mississippi in 1879, and the
ones from Mississippi had seen what redeeming a state meant in 1875. Thomas Wickliffe read the circular to the school and
sent it back to Galveston with the town's answer. The line about the right sort came out of the second printing and went
back into the third, because the Treasury found that leaving it out brought it the wrong letters.

There's nothing behind the Nicodemus answer that this book has any business inventing. It's a town that built itself in
dugouts the first winter and has a school and two churches and wheat, and it said so. The story here is on the other side
of the paper: the agent at Galveston, who kept the only answer that ever came back.
""",
      open=[("Why did the agent keep it?",
             ["Shame, of a kind he never named. He resigned the agency in 1883, and his widow says he read the back of "
              "the circular more often than he ever read the front.",
              "Because it was an address. The Treasury keeps account of every place that writes back, and a town that "
              "answers is a town Jubilee remembers."])],
      table="""
Nicodemus is a real town and its people are people, and a posse that rides through it meets farmers, a schoolteacher and
two churches, and nothing in this game is waiting there. The agent at Galveston is where the Redemption story goes, and
his successor still posts the circular every spring. First Sergeant Isom Fairley's wife lives at Nicodemus
([[ref:tenth]]), and her husband is watching the river the circular invites people across.
""")

entry("salitre",
      callings=["Padre"],
      people=["Varela, Anselmo", "Varela, Mrs.", "Holcomb, Mr.", "the priest at Salitre",
              "the widows of Salitre", "Baca, Refugio", "Lucero, Tom&aacute;s", "Montoya, Juan de Dios"],
      places=["Salitre", "Tennant"],
      creatures=[],
      threads=["kansas", "keelers", "fortsafe"],
      when=[(1883, "Thirty-eight men die behind locked doors in a fire in the lower workings at Tennant in "
                   "August; their names vote at Salitre on 6 November"),
            (1884, "The county commissioners reject the Salitre returns and seat the county at Tennant")],
      story="""
The copper company at Tennant locked the doors at the bottom of the lower workings every shift to keep the men
from carrying out ore in their clothes, and in August 1883 a fire started in the timbering on the third level
and the smoke came up the ladders and the doors stayed locked. Thirty-eight men of Salitre died behind them. In
the autumn the county seat was to be settled between Salitre and Tennant, and the company's Mr. Holcomb told
the men of Salitre that a Mexican vote wouldn't be counted. He'd been telling them for years, and before the
fire most of them had believed him enough not to bother.

The widows did the rest, and their statement is true. Thirty-seven of them carried ballots in under their
shawls while the judges were at their dinner, and signed and marked for their husbands in a poll book the
judges had sealed at six, because they wanted to see whether Holcomb was right. He was. The commissioners
threw the precinct out on the ground that the box had been opened, which it had, and seated the county at
Tennant.

The thirty-eighth line isn't the widows'. Mrs. Varela can't write, and signed the widows' statement with a
mark, and Anselmo Varela's name in the poll book is written out in full in the slow, large hand of a man
who has only lately learned how. He'd been going to the priest's night school every evening that spring,
and by August he'd got as far as his own name, and he meant to sign it in November, and he did.
""",
      open=[("Who signed for Anselmo Varela?",
             ["Anselmo. The dead man came in out of the rain in the judges' dinner hour with the mud on his "
              "boots and signed the one thing he'd learned to write, and went back. Nothing else at Salitre "
              "has ever walked, and nothing needed to.",
              "The priest, who taught him and knew his hand better than anybody alive, and has never said so "
              "and never will.",
              "His son, twelve, who went to the night school with his father every evening and learned the "
              "same letters the same way."])],
      table="""
This is no monster story and the dead of Salitre aren't to be fought. If a posse comes through Salitre the
corrido will be sung in the plaza, and the widows will tell them about the doors. Holcomb is still at Tennant,
the doors at the bottom of the workings are still locked every shift, and a table that wants to do something
about Salitre has a mine company, a county board and a bought election to do it to.
""")

entry("kansas",
      people=["a subscriber (the man at the foot)", "the seventeenth guest", "Drayton (of Kansas City)"],
      places=["the Coronado, Kansas City", "Kansas City"],
      creatures=["The Ledger of the Territory"],
      threads=["vane", "clause", "foreclosure", "houses", "gold"],
      when=[(1883, "Sixteen covers are laid at the Coronado on 29 November and seventeen men sit down, by one "
                   "guest's count; it's the eleventh such dinner in four years")],
      story="""
The dinners are real and so is the business done at them, which is none, on paper. Sixteen men of the cattle and
railroad interests of four territories sit down at the Coronado a few times a year for the pleasure of it, and
talk about the price of beef and the Territorial line and water rights in the southern counties, and resolve
nothing. The resolving is done in the weeks after, in sixteen offices, by men who have heard what the others
think. It's the most efficient board in the West and it has no minutes. Drayton is one of the sixteen, and the
southern counties they talk about include Perdition Basin.

The subscriber at the foot of the table is the most junior man there, a son-in-law brought to his first dinner,
and he counted seventeen because a man put at the foot counts the table. The house's book says sixteen covers
and the house laid sixteen. The seventeenth man sat at the head, beside the host, and ate nothing, and spoke
once, about water, and every man at the table remembers the remark and nobody remembers who made it.

The Keeper's Book describes a chain that runs from any bank in the Territories back to Kansas City, and past it
to a few men who own railroads, and past them to a house in New York, and somewhere along it the names stop
being people. At the Coronado the chain sits down to dinner, and the seventeenth chair is where it stops.
""",
      open=[("Who is the seventeenth man?",
             ["Nobody. A secretary seated to take notes the house didn't count as a cover, whom a nervous young "
              "man at the foot mistook for a guest.",
              "The Ledger, sitting down in the one room where the whole chain is held at once. None of the "
              "sixteen invited him and every one of them thinks another did.",
              "A different man each time, and always one of the sixteen's dead partners."]),
            ("What happened to the subscriber?",
             ["He's never been asked back, and his father-in-law has stopped speaking to him.",
              "He's been asked to every dinner since, and seated at the head, and he's stopped counting."])],
      table="""
The subscriber is the way in. He's a frightened young man in Kansas City with a good position and a letter he
wishes he hadn't sent, and he'll talk to a posse who can prove they know about the basin. He can get them into
the Coronado as waiters on the night of the twelfth dinner. What they do in that room is the kind of scene a
campaign spends a year arriving at, and nothing in it can be shot.
""")

entry("paradise",
      people=["Lacey, J. B. (Jack)*", "Lacey, Ned", "the man who keeps the hotel at Paradise"],
      places=["Paradise", "Charleston, Arizona", "Natchez"],
      creatures=["The Tinhorn", "The Crossroads Man"],
      callings=["Gambler"],
      threads=["correspondent", "handshake", "wager", "crossroads"],
      when=[(1881, "Jack Lacey is shot at a table in the Bon Ton saloon at Charleston, Arizona, with a card in his "
                   "sleeve"),
            (1882, "Letters in Jack Lacey's hand begin to reach his brother at Natchez from a camp called Paradise")],
      story="""
Jack Lacey was a sporting man out of Natchez and a good one, which means he cheated well and lost when it paid to, and on
the 4th of May 1881 a miner at Charleston caught a card in his sleeve and shot him across the table. The coroner found
it justifiable, and he was buried at the county's charge.

In July of 1882 his brother had the first letter. Paradise has a good hotel and a game every night, and the men pay in
coin and laugh and pay again, and Jack hasn't lost a hand. By March he'd thrown away full houses and played without
looking, and it came up for him every time, and a game he couldn't lose had become a room he couldn't leave. The man who
keeps the hotel told him where he was, kindly, in the words of every man who ever caught him cheating.

This book won't say whether Jack Lacey is dead. If he is, Paradise is his, the place a cheat would most want and least
be able to stand, and the hotelkeeper is the only honest man in it. If he isn't, he's a gambler with debts who let a
stranger be buried under his name and has a friend at Charleston to post his letters, and the second letter is a man who
has found out what a run of luck costs when it doesn't end.
""",
      open=[("Where is Paradise?",
             ["Nowhere a horse can go. The letters come because Jack can't stop telling his brother when he's winning, "
              "and whatever keeps the hotel lets them through because somebody ought to know.",
              "A real camp in the Dragoons that took the name in 1882, run by men who bought Lacey's debts and keep him "
              "at the tables because he makes them money. He isn't dead. He's owned.",
              "Behind the Crossroads Man's door. Lacey went to a crossroads in 1880 and asked never to lose, and was "
              "shot the next spring because the bargain never said anything about being caught."])],
      table="""
Ned Lacey will hire a posse to find his brother and pay well, because Jack's last letter frightened him. Every road that
seems to reach Paradise reaches a camp with a good hotel and a friendly game, and a gambler in the posse will win there
more than they should. Stop them before the third night. The Bestiary's Tinhorn is who they'll meet at the first table,
and he's the only man at Paradise who ever loses.
""")

entry("sixes",
      people=["the cashier of a bank at Kansas City", "a gentleman at Atlanta"],
      places=["Kansas City", "Atlanta", "Jubilee"],
      creatures=["The Ledger of the Territory"],
      threads=["understanding", "kansas", "gold", "remarks", "warrants"],
      when=[(1881, "The Treasury of Redemption issues its Six per Cent Land Bonds"),
            (1882, "A Kansas City bank is offered Redemption Sixes four times in a year, each time cheaper, each time "
                   "by a different gentleman")],
      story="""
The Treasury doesn't need the money. It pays for land in gold it already has, and the bonds raise very little, which is
why the gentlemen offering them at Kansas City didn't mind whether the bank bought. The bonds are for putting into hands.
Every Redemption Six in a safe at Boston or Atlanta or Kansas City is a gentleman with a reason to hope the country on the
Colorado goes on paying, and the Treasury pays, in gold, at Jubilee, every January and July, on the day.

The four gentlemen came cheaper each time because the price was never the point. They were finding out which banks would
carry Jubilee paper, and the cashier's letter is the answer from one that wouldn't. The ones that would are the reason a
member of Congress revised his remarks to nothing in [[ref:remarks]], and they're the third reason the retired clerk
gives in [[ref:understanding]].

The bond can be redeemed in land at the Treasury's own valuation, at the Treasury's choice. Nobody has ever asked for
land. A holder who did would be offered a parcel from the list, and would find, like the woman in [[ref:letterhome]],
that the stock won't graze past the stake.
""",
      open=[("Who holds the Sixes?",
             ["Men whose names a posse would know, at Washington and Kansas City and in two Southern statehouses. The "
              "Treasury has the list and would part with it for nothing in this world.",
              "Fewer than the silence needs. The fear of who might hold them does more than the bonds do."])],
      table="""
A Redemption Six in a dead man's papers is a better clue than a Jubilee banknote, because somebody paid real money for
it. The Bestiary's Ledger of the Territory is what the bonds belong to, and it can't be shot. A posse that wants to hurt
Redemption without a war could do worse than find out who'd lose money if it fell, and tell them.
""")

entry("floor",
      people=["Mulhall, A. (driller)", "Iverson (on the engine)", "Beckwith, J. (geologist)",
              "Sallis, E. (agent)"],
      places=["Winnemucca", "a dry lake in Nevada"],
      creatures=["The Parcel"],
      threads=["gold", "dugout", "breathing", "gatherings"],
      when=[(1883, "Three bores on a dry lake in Nevada strike a floor at two hundred and twelve feet; the lake "
                   "is sold in October to an agent for principals not named")],
      story="""
The Humboldt Land &amp; Cattle Company bored for water on a dry lake it owned in the summer of 1883 and struck,
at two hundred and twelve feet, a floor. It's level to the inch across two miles, it's under ten thousand years
of lake mud, it polishes a bit like a lapidary's wheel, and it rings. Three bores a mile apart gave three notes,
and A. Mulhall, who drills for a living and plays the fiddle for pleasure, heard the three together and didn't
care for the chord.

J. Beckwith was right the first time. Whatever the floor is, the lake came after it, and a man who's been a
geologist long enough to know what caliche looks like doesn't mistake a floor for it. Between his July letter
and his August letter he had a visitor at his lodgings in Winnemucca, a pleasant man who asked him nothing
about the floor and talked for an hour about Beckwith's prospects with the company, and his next letter found
caliche. The company was glad to sell.

The buyer was E. Sallis of San Francisco, as agent for principals not named, and the principals are the Golden
Circle, and the lake is the first line of the page of its purchases in [[ref:gold]]. Sallis asked one question
at the recorder's office: whether all three bores had been driven to the same depth. He wrote the answer down
because the Circle's list-maker needed three holes of equal length in that floor, capped, and would have paid
to have them drilled if the cattle company hadn't done it for free.
""",
      open=[("What is the floor?",
             ["The roof of a room. Somewhere under the plains is a long hall where a great many people stand "
              "facing the wall ([[ref:dugout]]), and this is one of its ceilings.",
              "A lid, and three equal bores through a lid are a key cut in it.",
              "A bell. Nobody has ever heard what it sounds like struck properly, and the Circle's list-maker "
              "means to."]),
            ("What is the chord for?",
             ["Nothing yet. Mulhall plays it at dances without meaning to and stops when he notices.",
              "Something on the other side answers to it, and the answer is the breath coming up a well in "
              "the Neutral Strip ([[ref:breathing]])."])],
      table="""
Mulhall is the man to find: a driller who's been let go, who plays the fiddle in a Winnemucca saloon, and who
can't get three notes out of his head. If a posse ever stands on the lake, the three caps are still there,
bolted, a mile apart, and sheep won't go onto the bed. The Parcel's entry in the Bestiary says how a list
like this one is broken, and it's in a courthouse.
""")


# ================================================================ The Spur to Jubilee
intro("jubilee", """
Redemption is a Power, and [[kb:powers-redemption]] has it whole: the country on the California line
that means to be a second Confederacy, its capital at Jubilee, its militia in grey, and the Golden
Circle inside it buying ground nobody can explain. The Keeper's Book says to play it as a working
country before a horror, and the papers here are what a working country leaves behind: a timetable,
two newspapers, a letter home, a banknote, a pilot's account.

The stories behind them hold to the Keeper's Book's one hard rule about the Circle: its officers don't
know why the parcels matter, and somebody hands them a list. Nothing below says who. Several entries
offer ways to decide, and they're the same offers, because it's one decision.

Redemption is also the most widely known thing in the Book of Legends, and that's by design. The Yuma papers
print its arrivals and the Texas papers its circulars, every depot on the Southern Pacific sings about it, and a
ten-cent novel about it sold sixty thousand copies ([[ref:novel]]). Play it that way. Everybody a posse meets west of
the Pecos has an opinion about Jubilee and half of them have a cousin there, which is the opposite of the houses in
[[ch:longtable]], where nobody will say the name. [[ch:forwarded]] is why none of it was written down anywhere it
would last.

Redemption is built on a cause, and the cause is slavery's, and nothing here softens that. The people
in it can be courteous, well fed and kind to a stranger's children, and the country is still what it
says on the customs-house wall. Play both at once. That's the thing a rider from outside finds hardest
to sit with, and it should be.
""")

entry("spur",
      people=["Pruitt, Henry", "Pruitt, Henry (his mother)"],
      places=["Yuma", "Jubilee", "the Customs Post at the river", "Muchacho Junction"],
      creatures=[],
      threads=["twopapers", "letterhome", "warrants", "otherdoor"],
      when=[(1883, "Time-table No. 6 of the Jubilee Branch takes effect on 1 March")],
      story="""
The Jubilee Branch is a spur off the Southern Pacific that the railroad leases to a company owned in Jubilee,
and the company prints the Southern Pacific's name on its time-table because the Southern Pacific's name is
what gets a passenger past the Collector at Yuma without questions. The customs post at the river is
Redemption's. So are the forty minutes. The line about return tickets is the most honest thing on the sheet:
you can't buy your way back from Yuma, because Jubilee decides who leaves.

Henry Pruitt has been a porter on the branch six days a week for two years. He's the one man on the train who
was born free of what the country on the other side of the river means to put back, and the condition of his
job is that he never sets foot on the Jubilee platform. He took it for eleven dollars a month and four at home,
and he takes the whole ride with his eyes open. The gentlemen on the train are the politest he's ever carried,
and every one of them is armed, and every one of them looks him in the eye when they say the name of their
town, and he knows the verse better than they do.

What Pruitt has that nobody else has is the count. He doesn't count cars. He counts people: how many get on at
Yuma, how many step down at the river and come back aboard, how many step down at Jubilee, and how many ride
the up train home. He's kept it in his head for two years, the way his mother taught him to keep things that
might be taken off paper. The numbers going up and the numbers coming down don't match, and the difference
isn't small.
""",
      open=[("Is it true that the only way in is by rail?",
             ["[[kb:powers-redemption]] leaves this to the Keeper and so does this book. [[ref:otherdoor]] "
              "is the river's answer, and a pilot has another.",
              "Pruitt thinks so. He's watched the sand hills out of the window for two years and never seen a "
              "track on them."]),
            ("Where are the people who don't come back down?",
             ["Living in Jubilee, having been admitted and stayed, which is what most of them came for.",
              "Some of them. The rest are the ones [[ref:twopapers]] can't find."])],
      table="""
Henry Pruitt is a man, not a clue, and the posse should meet him that way: a tired, careful porter with a family
at Yuma, who'll say more to a passenger who treats him as one than to anybody with a notebook. His count is the
best evidence in the Territories about what Jubilee does with visitors. He'd share it with somebody he trusted
to use it. He hasn't met anybody yet.
""")

entry("river",
      people=["Bagby, Orrin", "the gentleman at the customs post"],
      places=["the Customs Post at the river", "Yuma", "Marion County, Georgia"],
      creatures=[],
      threads=["spur", "emigrants", "warrants", "twopapers", "enumerators"],
      when=[(1883, "Orrin Bagby, teamster for the Treasury, is admitted at the river for the fourth time and asks "
                   "whether he's remembered")],
      story="""
The customs post at the river keeps the book that Washington doesn't. When the Confederate government fell in 1865 its
muster rolls went north in boxes, and the War Department has them still and lends them to pension clerks. Jubilee has a
copy of its own, made over ten years by men who went through every county courthouse and every regimental reunion in the
South, and the gentleman at the post looks in it for every passenger's father. A man whose father is in the right
regiment is admitted. A man whose father said all his life he was in the Fourth Georgia and isn't on the roll is turned
back with real sorrow.

Orrin Bagby hauls freight for the Treasury and has been admitted four times, and each time the gentleman wrote him a new
paper and looked at him as if he'd never seen him. He has. Remarks: Known. The country remembers everybody it means to
keep, and it does it on paper, and it's the only government on the river that does.

That's the joke the editor never quite makes. Washington keeps no record of Redemption at all, and Redemption keeps a
record of every man who ever came to its door, and of his father.
""",
      open=[("What's in the book besides fathers?",
             ["Everybody who was turned back, and why, and where they went next. The Circle reads it once a year.",
              "The Union men too. The book has a second half for the men who fought on the other side, and nobody is "
              "ever admitted from it, and the gentleman reads it as carefully as the first."])],
      table="""
A posse that wants into Jubilee needs a father in the book. A forged ancestor makes a fine heist, and Bagby is the man who
knows how the gentleman checks. Play the gentleman at the post as the most courteous man the posse will ever meet, and let
them feel how much he already knows.
""")

entry("twopapers",
      people=["the owners of the Jubilee Standard and the Redemption Clarion", "a visitor from the States",
              "the three without papers"],
      places=["Jubilee", "Yuma"],
      creatures=[],
      threads=["spur", "warrants", "letterhome"],
      when=[(1882, "A visitor from the States is admitted to Jubilee and given a chair at the Saturday muster; "
                   "three passengers without papers are 'returned'")],
      story="""
The two papers are owned by two men who don't speak to each other, and both are handed their news every
Wednesday by the same office in the customs house, and they print it in slightly different words so that
Jubilee can say it has a free press. The week of 19 October 1882 they agreed as they always do. A gentleman
from the States was admitted and given a chair at the Saturday muster, which is an honour Jubilee gives to a
visitor whose good opinion matters, and he went home with it on Monday. Three passengers with no papers were
returned.

The gentleman was a senator's secretary from Washington, sent without any fuss to see whether the country on the
California line was worth the trouble of removing. He was shown the wheat and the school and the muster and a
very good dinner, and he went home and reported that it wasn't, and the country has been left alone since.

The three weren't returned. They were a man from Tucson who had quarrelled with a Jubilee man at Yuma, a
woman looking for a husband who'd gone up the year before, and a Mexican drover who had taken the wrong train.
Nobody at Yuma counted who came down on the Thursday because nobody at Yuma ever does, and "returned" is the
customs house's word for anybody who goes out of the country's books.
""",
      open=[("Where did the three go?",
             ["To work. The Circle has ground to dig and grade, and a man with no papers has no one to write to.",
              "Nowhere. There's a gravel pit two miles up the branch from Siding No. 4, and the militia drills "
              "near it on the Saturdays nobody visits.",
              "One of them came back to Yuma a month later on foot, over the sand hills, which nobody does, and "
              "won't say how."])],
      table="""
The woman looking for her husband is the thread a posse can pull. Her sister at Yuma is still waiting for a
letter, and will hire anybody going up with papers to ask after her. The customs house will answer politely
that the lady was returned, and produce a ticket stub to show it.
""")

entry("lady",
      people=["an Englishwoman (the author of A Lady's Year in the Far West)", "her hostess at Jubilee",
              "her cousin at Savannah"],
      places=["Jubilee", "Savannah", "London"],
      creatures=[],
      threads=["emigrants", "novel", "degree", "spur", "muster"],
      when=[(1883, "An Englishwoman spends a week at Jubilee on papers from a cousin at Savannah"),
            (1884, "Her book is published at London; no American house will print it")],
      story="""
The Englishwoman saw Redemption the way Redemption wants to be seen: watered streets, gardens, men who raise their hats, a
drill in the square on Saturday that her hosts called a kind of cricket. She wrote it fairly and liked it, and then she
wrote the paragraph that matters, about not seeing one person of colour in a week, and about her hostess, who said they'd
all gone to Kansas where they were happier, the way one says the swallows have gone.

Some went to Kansas. The rest of that story belongs to 1873, when the first party came in and the families already farming
the bottom land, freedmen most of them, who'd come west after the war, were told to leave, and some of them didn't, and the
town was laid out over the place where that ended. Nobody at Jubilee talks about 1873. The hostess believes in the swallows,
and that belief is the most important thing the country has taught its own people.

The book was printed at London and not here. A New York house took it, read the chapter on Jubilee, and gave it back, and
so did the next. That's one of the slow ways a country gets left out of the books, and nobody had to order it.
""",
      open=[("What happened in 1873?",
             ["What the Keeper decides, and it should be as bad as the country's cause, because the country's cause was "
              "that bad. Nothing here softens it.",
              "Somebody wrote it down. The chainman in [[ref:spring]] came in with the first party and came out in "
              "1883, for reasons he asked Ashby not to print."])],
      table="""
The customs-house preamble is the best single thing to put in a player's hand about what Redemption is. It's polite, it's
printed, and it says exactly what it means. Let the players meet a hostess like this one and like her. They'll remember
liking her when they learn the rest.
""")

entry("novel",
      people=["Dorrance, Capt. Hale (the author)", "the Fireside Ten-Cent Library"],
      places=["Brooklyn", "Tucson", "Salt Lake City", "Jubilee"],
      creatures=[],
      threads=["remarks", "plate", "understanding", "deadletters", "lady"],
      when=[(1882, "The Grey Riders of Jubilee sells sixty thousand copies in four months"),
            (1883, "The Post Office Department questions the Fireside Ten-Cent Library's second-class rate; the second "
                   "edition moves Jubilee to Zion City")],
      story="""
The first edition was the most widely read thing ever printed about Redemption, and it was a ten-cent romance written in
Brooklyn from the Yuma papers and a week at the depot. Every boy in Kansas knew the grey riders and the flag beyond the
river. In the author's book they lose, which is the only part he made up.

The Post Office's lever was the second-class rate, which a story paper can't live without. Nobody at the Department ever
wrote that Redemption doesn't exist. Somebody wrote that matter respecting a pretended government upon the territory of
the United States raised a question about the rate, and the firm understood. In the second edition the country is the
Desert Republic, the river is the Gila, and the riders are Mormons, and the boys who came along after 1883 only ever had
that one.

This is how the forgetting works, and the next chapter of the Book of Legends is full of it. Nobody suppresses Redemption.
A rate is reviewed, a plate is re-engraved, a member revises his remarks, and in thirty years the only people who remember
the grey riders will be old men who once carried a ten-cent book in a hip pocket.
""",
      open=[("Who asked the Post Office?",
             ["The Department, on a word from the War Department, as policy.",
              "A gentleman holding Redemption Sixes ([[ref:sixes]]), who didn't like a novel in which his interest "
              "loses.",
              "Jubilee, through its friends at Washington. The country doesn't mind being written about. It minds "
              "losing."])],
      table="""
A first edition of The Grey Riders of Jubilee is a cheap and lovely prop, and a dealer at Tucson sells it under the
counter. A posse heading for Jubilee will have read it as children, and every grey uniform on the platform will look like
the cover.
""")

entry("letterhome",
      people=["the letter-writer (a woman at Jubilee)", "Sue (her sister in Georgia)", "Jim (her husband)",
              "a gentleman of the Circle"],
      places=["Jubilee", "Crawford County, Georgia"],
      creatures=["The Parcel"],
      threads=["gold", "twopapers", "spur", "floor"],
      when=[(1882, "The Golden Circle buys the north corner of a family's allotment at Jubilee in March and "
                   "drives a numbered stake in it")],
      story="""
The woman who wrote this letter is happy and she's telling the truth. The wheat came in at thirty bushels. The
school is better than the one in Crawford County and there's a doctor and nobody is hungry. Her husband drills
on Saturdays with the militia and she takes the children to watch, and at supper nobody asks where anybody was
in the war. She's a decent woman who has moved her family into a country built to put the war back the way it
was, and she has chosen not to look at that too closely, and she's done well by it.

In March 1882 a gentleman of the Circle came out and bought the north corner of their allotment for four times
what the land office asked, in gold, and wouldn't say what he meant to plant on it. There's a stake in that
corner now with a number on it and nothing else, and the stock won't graze past it. The number is the
parcel's line on a list, and the list is the one in [[ref:gold]], and the gentleman who bought the corner had
it in his pocket and didn't know what it was either.

The sister came west in 1883 with the blue dress and no papers, because papers come from inside and the letter
didn't say how to get them, and she was refused at the river and sold the letter at Yuma for her fare home. The
school reader's leaf was in the same envelope. "What do we ask him? Nothing. We know already." Children at
Jubilee are taught that the country already knows everything it needs to about a stranger, and the customs
post is where it finds out.
""",
      open=[("What happens to the family?",
             ["Nothing. They prosper, and the corner stays staked, and one day the Circle sends a man to sit "
              "by the stake through a night, and asks Jim to lend him a chair.",
              "The stock is only the start. By 1885 the children won't go past the stake either, and the youngest "
              "sleeps with her bed pushed against the north wall, and says it's warmer there."]),
            ("Why would the Circle want a corner of a farm?",
             ["Because the list says so, and the list's lines are corners of a shape only a large map shows.",
              "Because that corner is where the Jubilee spring's water runs underground, and the list-maker "
              "wants the spring and doesn't want to be seen buying it."])],
      table="""
The stake is a good thing for a posse to stand beside and not understand. If they're in Jubilee, the
letter-writer will feed them and be glad of the company, and will walk them out to the north corner to show
them how the cattle turn. The Parcel's entry in the Bestiary is what the stake is part of, and it's slow, and it
closes in a courthouse.
""")

entry("gold",
      people=["the freight clerk at Yuma", "a former member of the Circle"],
      places=["Yuma", "Jubilee", "above Leadville", "Painted Mesa, the"],
      creatures=["The Parcel"],
      threads=["floor", "mesa", "letterhome", "gatherings", "crossroads", "otherdoor", "street"],
      when=[(1880, "The Treasury of Redemption issues its first scrip"),
            (1883, "A freight clerk at Yuma sells Ashby a page of the Circle's purchases instead of burning it")],
      story="""
The scrip is real currency in Jubilee and nowhere else, and the engraving on it is the country's whole idea of
itself: a depot, a track running in from the left, and nothing coming out on the right. It pays its own people in
paper and it pays for its land in gold, and the difference between the two is the Circle's.

The page is genuine. The freight clerk was paid a dollar to burn a bundle of the Circle's papers that came
through Yuma in a crate that broke, and he burned all of it but one sheet, which he sold to Ashby for two. It's
one page of the Circle's schedule of purchases, 1879 to 1884, in an officer's hand. Seven lines are filled. The
first four are the ones the Keeper's Book knows: the dry lake in Nevada ([[ref:floor]]), two sections of the
Painted Mesa's old ground ([[ref:mesa]]), and the slope above Leadville that a mining company is sinking a shaft
on without knowing why ([[ref:gatherings]]). Three have had their names cut out of the page, by the officer who
kept it, because he was told to.

Two lines are ruled and empty and marked "not yet", and at the foot, in pencil, in another hand, is the word
<em>strategic</em>, underlined, and then a second line. The officers believe every word of the pencil. Not one
of them knows who drew up the list, and the one former member who has talked says they were proud not to ask.
""",
      open=[("Who wrote the list?",
             ["[[kb:powers-redemption]] says to let the players find the ledger long before they find out who "
              "wrote the list, and this book won't settle it either. Three ways to hold it follow.",
              "Something that holds no ground of its own and keeps correspondents instead: a land office, a "
              "county clerk, a man who knows what a parcel sold for in 1873. The list came to the Circle in "
              "the post, in several hands, over years.",
              "A man at Kansas City who has held the whole chain of paper in his head at once and was changed "
              "by it, and has never been west of Dodge.",
              "Nobody. The officers took the list from their fathers, who had it from theirs, and the first "
              "page is older than the Circle."]),
            ("What are the three names cut out of the page?",
             ["Choose them from the book. Three candidates the papers already hold: the forty acres at the "
              "crossroads at Twelve Mile ([[ref:crossroads]]), the Kemper premises on Front Street at Hessler "
              "([[ref:street]]), and Mr. Pettibone's section in the Neutral Strip ([[ref:breathing]]).",
              "Leave them cut out. A posse that learns three of the seven is doing well."]),
            ("What are the two lines not yet bought?",
             ["The salt pan in Sonora ([[ref:otherdoor]]), which Mexico keeps refusing.",
              "The mission ground at San Clavo, which belongs to nobody who can sell it."])],
      table="""
The page is the thing to put in the players' hands, and the Parcel's entry in the Bestiary is what to do with it:
a map, a courthouse and a very slow campaign. A banknote of the Treasury of Redemption is a good thing for a
player to find in a dead man's coat a long way from California. It tells them the man had been paid, and by
whom, and that nobody would give him anything for it.
""")

entry("otherdoor",
      people=["a pilot on the lower river", "a collector of customs in Sonora", "a gentleman from Port Isabel"],
      places=["the lower Colorado", "Guaymas", "the head of the Gulf of California", "Yuma"],
      creatures=["The Parcel"],
      threads=["spur", "gold", "twopapers"],
      when=[(1883, "Redemption asks Mexico a fourth time, in gold, to sell it a salt pan at the head of the Gulf")],
      story="""
The pilot is right that the railroad is the only way in for anybody who isn't a crate. For nine years the river
boats have put in after dark at a landing below Jubilee that isn't on the company's charts, and the country's own
men load them. Going down it's wheat, sold at Guaymas as Sonora wheat because nobody in Mexico will buy wheat
from a country Mexico doesn't recognise. Coming up it's long heavy crates that don't rattle like implements,
because they're rifles, and ammunition for them, and the parts of four field guns that Jubilee's militia will
assemble on the day it decides it needs them. A second Confederacy needs an armoury, and it's buying one a boat at
a time, with wheat.

The gentleman from Port Isabel who asked the pilot the name of his boat is an officer of the Circle who handles
the purchases, and he asked because the Circle keeps a list of everybody who knows about the landing. The pilot is
on it now.

The salt pan is the Circle's other door and it's a different kind of door. It's thirty leagues from anywhere at
the head of the Gulf, nothing grows there and nobody goes there, and it's one of the two lines on the page marked
not yet. The collector of customs is an honest official of a Republic that has had neighbours who wanted to become
something else before, and he'll refuse the gold every year, and the Circle's agent will thank him and ask again,
because the list says strategic and the agent was told to say it.
""",
      open=[("What happens if Mexico sells?",
             ["A corner closes, and something on the list's large map becomes a little more agreeable to certain "
              "visitors, and nobody notices for three years.",
              "Nothing that anybody can see. The Circle stakes it, and puts a man on it with a chair, and the "
              "man sits there a year and comes back to Jubilee and won't talk."]),
            ("Is the collector's successor so honest?",
             ["The collector is sixty-one and his successor has already been approached.",
              "Yes. The Republic has been refusing this sort of thing for sixty years and has a habit of it."])],
      table="""
The pilot is a good contact for a posse that needs to get into Jubilee without papers, and a good man to lose. The
landing is where a table can do real harm to Redemption, and the crates are the proof a federal marshal at Tucson
would need. Getting that proof out of the river country alive is a campaign's worth of trouble.
""")



# ================================================================ Respectfully Forwarded
intro("forwarded", """
This chapter is Washington's, and it's where the Book of Legends answers a question the players will ask sooner or later:
if there's a second Confederacy on the Colorado, why has nobody heard of it? The papers' answer is that everybody in the
Territories has heard of it, and that the government of the United States has spent ten years arranging not to.
[[kb:powers-redemption]] says the United States doesn't admit Redemption exists and has no present appetite for removing
it. These are the papers that show how a government declines to admit a thing, one office at a time, and
[[ref:understanding]] says why.

Two other threads begin here. W. F. Kinnear, an operative of Pinkerton's working under the Department of Justice's
contract, files his first report in [[ref:principles]] and runs the length of the book to [[ref:ashbyfile]]. And the Army
is here too, as officers who see a great deal and are told in writing what they didn't see.

None of the Washington papers is a lie, and that matters at the table. A posse that goes to Washington to expose
Redemption will find nobody who lied to them, nothing on file that says anything, and a great many courteous men who
can't help.
""")

entry("principles",
      people=["Kinnear, W. F.*", "the Chief Clerk of the Department of Justice"],
      places=["Fort Lyon", "the Purgatoire", "Trinidad", "Chicago", "Denver"],
      creatures=[],
      threads=["agency", "gatherings", "clerk", "ashbyfile"],
      when=[(1881, "The Department of Justice engages Pinkerton's to look into stolen Army horses, and W. F. Kinnear "
                   "closes the matter in eleven days")],
      story="""
The Department of Justice has no detectives of its own, so when Washington wants a thing looked into and won't send a
marshal or a regiment, it hires the Agency by contract at so much a day. That arrangement is real history, and the Book
of Legends keeps it plain: the Agency's operatives are working for the government when their reports say so.

W. F. Kinnear is the operative, and this is the last of his reports in the book that ends where it was meant to. He was a
hostler at Fort Lyon for eleven days and found three horse thieves, and the Marshal took them, and the account was
rendered. He's good at the work, careful, and honest in the way the Agency's card means it: he reports what he saw and
marks the rest as opinion.

Every paper of his after this one is about something his card has no column for. He decides Cyrus Teal is two men
([[ref:agency]]), which is the right answer for a report. He's sent into the high country on a private engagement and
comes back with four camps waiting for the same thing ([[ref:gatherings]]), and Chicago writes NOT CREDIBLE and sends him
to Pueblo. He takes the Circle's runaway clerk's statement ([[ref:clerk]]) under a Department contract and watches the
Department write File on it. He opens a file on Ashby and asks to go and look for him, and the Department closes it the
next week ([[ref:ashbyfile]]). By 1886 he's left the Agency.
""",
      open=[("Where does Kinnear end up?",
             ["In Perdition Basin, looking for Ashby on his own account, with his savings and his copy of the "
              "high-country report.",
              "In Jubilee. Somebody there would like a man who knows how Washington files things, and pays in gold.",
              "At home at Pueblo with his wife, who called the reassignment what it was and has had him back since."])],
      table="""
Kinnear is the operative [[kb:powers-pinkertons]] promises: the man who was right about the players and wrong about the
world. He can be the posse's opponent early and its best friend late, and the turn should come the day he sees something
his card has no column for. He'll never lie in a report, which makes him dangerous to a posse with secrets and invaluable
to one without.
""")

# ================================================================ A Face Not Their Own
intro("faces", """
The editor warns that thirty-six of forty of these stories are bigamy and that one of the thirty-six is
mixed in with the four that aren't. That's true, and the entry below says which. The other four are
the Bestiary's quietest monsters: things that wear a person, or copy one, or come loose from one, and
are generally kinder than the person was.

That kindness is the thread through the chapter and the editor saw it. Every witness says the man was
easier to be around afterwards. Run these as the Keeper's Book runs the Skin-Walker at Saltlick
([[kb:secondreckoning]]): the monster is already at the table, and the horror is how much the people
around it prefer it.
""")

entry("agency",
      people=["Teal, Cyrus", "Teal, Mrs. (at Topeka)", "the man at the implement office", "Kinnear, W. F."],
      places=["Coffin Wells", "Calvary Crossing", "Topeka", "Kansas City"],
      creatures=["The Fetch"],
      threads=["gorham", "fifth", "water", "gatherings", "principles"],
      when=[(1882, "Cyrus Teal of Renfro &amp; Sons falls ill at Topeka in November and stays home"),
            (1883, "Teal is seen at Coffin Wells and at Calvary Crossing on the same day, the 3rd")]
      ,
      story="""
Cyrus Teal was a commercial traveller in agricultural implements for Renfro &amp; Sons of Kansas City, a firm
whose owners have cousins at Coffin Wells, and he worked the basin for three years with a good address and no
fixed residence. In November 1882 he came home to Topeka with a cough, and he's been at home since, as his wife
says, and the church roll and three neighbours say.

Something else went on working his route. The Bestiary's Fetch is told about before it's seen: somebody waved at
you outside the bank on Tuesday, and you were forty miles off on Tuesday. Teal's fetch took up his samples and his
credit and his towns in November while he lay coughing at Topeka, and it didn't have his face at first. It was a
stranger who came into the implement office the week before "Teal" did, whom the merchant can't describe at all,
because there was nothing yet to describe. By the next week it had settled on Teal, and it did Teal so well that
the merchant can describe him for two minutes in detail. It's still learning him. At four towns it's Teal, at one
it's Teale, at another Tweel, and the heights and the hair wander.

The Agency was engaged by Renfro &amp; Sons, found two men in two towns on the same day, and concluded that there
was a confederate, which was the right conclusion for anything that could be put in a report. Paragraph 5 is
where it chose not to believe a church roll over an operative, and the editor's right that it's the whole file.
""",
      open=[("What happens to Cyrus Teal?",
             ["The Bestiary's way: get Teal and his copy into one room in front of people who know him, and the copy "
              "comes apart. Nobody has thought to try, because Teal is at home coughing and the copy is never anywhere "
              "you can send somebody to check.",
              "Nothing. He gets well in the spring, goes back on the road, and finds that every merchant in the "
              "basin is owed money by somebody with his face, and that it has moved on to somebody else's.",
              "He's already met it. The man at home at Topeka since November, with the cough, is the copy, and "
              "the one on the road is Teal, looking for his way home."])],
      table="""
An implement drummer is the easiest face in the basin to meet twice in a day. Let the posse do business with Teal
at Coffin Wells in the morning and pass him on the Crossing road at noon going the other way. W. F. Kinnear, who
wrote the file, is a good man and a stubborn one, and he'll still be on the matter, off the books, if the posse
asks.
""")

entry("fivewives",
      people=["the cook at Gurley's", "the deceased (a hand at Gurley's)", "the coroner"],
      places=["Gurley's"],
      creatures=["The Skin-Walker"],
      threads=["saltlick", "haunting", "bird", "gorham"],
      when=[],
      story="""
Gurley's is a road ranch on the southern trails, a bar and a corral and a cookhouse where a good many roads in this
book cross, and the dead man was a hand there for five years: sour, tuneless, whistling one tune all day, never
once using the cook's name. In the middle of August something killed him out on the range and put him on.

A Skin-Walker hungers to be somebody, and it had never been a man anybody liked, so it tried the other thing. It
got pleasant. It learned the cook's name and used it every day, because using a name is the first thing a thing
learns about being a person, and the cook, who had fed the real man twice a day for five years, noticed at once.
It ate a great deal and didn't get fat, because what it eats isn't for keeping. And it couldn't whistle. A tune
whistled all day for five years isn't a habit a thing can pick up by watching. It's the one piece of a man that
lives in his breath, and the breath was gone.

It wore him about a month and then left him in his bunk with no wound and a look of perfect rest, and the coroner
found heart, and the cook made him write down the whistling. She knows what it means that the whistling mattered,
and she knows she's the only one at Gurley's who noticed, and she knows the thing knows that too. Somebody at
Gurley's got pleasant in the week after the inquest.
""",
      open=[("Where did it go?",
             ["Into somebody else at Gurley's, and the cook is working out who, and she's frightened.",
              "Up the trail with a herd, wearing a drover, toward whatever town the posse is in.",
              "If your table's Skin-Walker got out of Saltlick at dawn, this is where it went next. "
              "[[kb:basin-saltlick]] says it can ride straight into the next town on your map. Gurley's was on "
              "the way."])],
      table="""
Run it as the Keeper's Book runs Saltlick in daylight: a road ranch full of hands and drovers, one of them wrong,
and a cook who has already found the giveaway and wants a witness. Ask the players to whistle. A player who asks
somebody at Gurley's to whistle has found the whole method, and should be made to pay for asking in the wrong
company.
""")

entry("crailtrial",
      people=["Crail, A.", "Merriam, Josiah", "Merriam, Mrs. (his widow, married again)"],
      places=["Las Vegas, New Mexico"],
      creatures=["The Possessed"],
      callings=["Witch Hunter"],
      threads=["lookeddoor", "terms", "namebook", "commission", "fivewives"],
      when=[(1880, "A. Crail shoots Josiah Merriam on his own stairs in August and is acquitted of manslaughter at Las "
                   "Vegas in October")],
      story="""
Crail did the things that wear men for six years, and the Merriam house was one of the last. He went because of the creek.
Josiah Merriam had fished it every Sunday of his life and since the spring wouldn't cross it, even on the bridge. Crail
sat on the porch and told him he wasn't Josiah Merriam, that he had one true thing written down about him, and said it
low. Merriam went for the shotgun and Crail shot him on the stairs.

The jury believed the widow, who'd known her husband nine years, and believed Crail, who'd known his trade twenty, and
couldn't make the two agree, which is the honest verdict. Mrs. Merriam married again in 1882. Her second husband fishes,
and she watches him cross every Sunday, which is the most eloquent thing in the trial and the one thing the court never
heard.

The Book of Legends doesn't settle it, and neither does this. A thing that wears a man wears his face, his habits and his
wife's trust, and keeps a few small refusals it can't help. A man with a bad leg and a fear of drowning won't cross a creek
either.
""",
      open=[("Was Merriam worn?",
             ["Yes, since the spring. Something came up out of the creek and wore him, and couldn't go back across "
              "running water, and Crail was right.",
              "No. Merriam went through the ice in February and nearly drowned and never told his wife, and he went for "
              "the shotgun because a stranger on his porch knew it."])],
      table="""
This is the Witch Hunter's trade with no answer at the end of it, and a Witch Hunter in the posse should read it as a
warning. Run the Bestiary's Possessed as Crail believed it to be, and let the posse be the jury: give them every reason to
shoot, and every reason not to.
""")

entry("mirror",
      people=["Boothe, W. (photographer)", "Doss, Mr.", "the husband", "the wife"],
      places=["a territorial capital"],
      creatures=["The Mirror-Dweller"],
      threads=["plates", "gorham", "lineman"],
      when=[],
      story="""
The wife commissioned the portrait because she'd begun to suspect, and a photograph was the only test she could
think of that a sensible person could ask for without saying why. Her husband came home from a business trip
in the spring changed in small ways she couldn't name, and a woman who has been married twenty years can't take
a small change to a doctor. She took it to a photographer.

The plate shows true. Silver doesn't flatter and it doesn't lie. What sat in Boothe's studio for an hour on the
Tuesday had the husband's face and his manner and the mark on his left hand, which Boothe was arranging the light
to hide. What came up in the silver was the hand of the thing that lives behind silver, reaching through, with no
mark and one joint too many. The Mirror-Dweller doesn't usually come all the way out. This one did, sometime in
the spring, on the husband's trip, through a hotel looking-glass in a town the wife has never visited, and it
took the husband back through with it and came home in his place.

It knew what the plates would show. It sat for them anyway, because it was the wife's request and it's being very
careful to grant her requests. It told Boothe it was the hands before Boothe said a word, because it wanted to see
what a man does when he's been told a thing like that by the thing itself.
""",
      open=[("Where is the husband?",
             ["Behind the glass, in the world mirrors show, reaching for the same looking-glass he was taken "
              "through. It's in a hotel room in another town, and the room has been let to somebody else since.",
              "Nowhere. There was never a husband behind the glass to save, only a man who made a bargain on "
              "his trip, and the hand in the plates is the hand he was lent.",
              "In the plate. Boothe broke all four, and the husband was in the third."])],
      table="""
A photographer is the most useful witness a posse can hire in this game. If they bring a camera to the wife's
house, the thing will sit for it graciously, and the plate will show what Boothe saw. What they do with a plate a
court would call a fault in the collodion is the rest of the evening. The wife will have hidden every mirror in
the house except one.
""")

entry("drifter",
      people=["the jailer", "the saloon-keeper", "a boy of ten", "Doyle, Jimmy", "the man who kept to the shade"],
      places=["a county seat on the Arkansas"],
      creatures=["The Shadow That Lags"],
      threads=["thirdcell", "street", "llano"],
      when=[(1880, "In October a man who keeps to the shade is held one night at a county lock-up on the "
                   "Arkansas and seen walking into the shadow of a water tank")],
      story="""
There's a man somewhere east of the Arkansas who made a bargain a long way back, to live through a thing he shouldn't
have lived through, and the price was paid by his shadow, which came loose from him and never quite went back. A
shadow that has come loose has its own ideas. His ranges ahead of him now, a day or two up the road, into the towns
he's going to reach, and in poor light it passes for him well enough to be arrested.

That's what the lock-up received in October 1880: a man of about thirty, no horse, refusing a name, who sat in the
corner of the cell the lamp doesn't reach and was gone through the wall behind the bunk by morning. It sat six nights
in the corner of the saloon, paying in coin for what it didn't drink, and when the new lamp went up on the seventh it
looked at the saloon-keeper the way you'd look at a man who'd done something you were sorry to see him do, because a
lamp in that corner was the end of its evenings there. A lamp shows what's between the light and the wall, and there
was nothing.

It sits the way a man sits who's waiting on somebody, because it is. It walked west on the road into the shadow of the
water tank and out the other side as a shadow with nothing to cast it, and it's still going west, a town at a time,
sitting in the dark corners of saloons at dusk, a little bolder every year.
""",
      open=[("Who is it waiting for?",
             ["Its man, who's a day behind it on the road and doesn't know his shadow goes on ahead into every town "
              "he's about to reach. The Bestiary says it can be put back.",
              "Somebody with a loose shadow of their own: a Marked character, or the next soul the Old Dark lends to, "
              "whom it will know on sight and sit down beside.",
              "The boy of ten, who followed it and didn't run, and walked home. It watched him walk home."]),
            ("Why did the jailer get sober?",
             ["He saw an empty bunk with a man's shadow sitting on the wall above it, and he's never since been able to "
              "drink in a room where he can't see every corner.",
              "It talked to him at two in the morning, and what it said is his, and he has kept it."])],
      table="""
Let the players see it first as a courteous stranger in a dark corner who won't sit in the light, and let them meet
its man a day later: a tired traveller with a good horse, who throws no shadow at noon and has stopped noticing. The
Shadow That Lags' entry says how it's pinned and put back. The best scene is the saloon-keeper's: a player who carries
a lantern toward the corner and watches the stranger's face as they come.
""")

entry("thirtysix",
      people=["Puckett, Mrs. E.", "Puckett, Mr.", "'Mrs. Yeager' (at Trinidad)"],
      places=["Dodge City", "Trinidad", "Denver"],
      creatures=[],
      threads=["gorham", "fivewives", "agency"],
      when=[],
      story="""
This is the one of the thirty-six, and there's nothing behind it but a man. Mr. Puckett has been married at Dodge
since 1876, has two boys there, and told his wife he was in Denver on the railroad, which he was, some of the time.
He was also at Trinidad, where in November he married a widow who is called Mrs. Yeager in the book because it
isn't her name. He's a pleasant, even-tempered man who never raised his voice and never asked a question he didn't
want the answer to, and both women found him restful, and both were right.

Mrs. Puckett found the second certificate the ordinary way, through a cousin who clerked at Trinidad, and she wrote
to the other woman and to the sheriff and not to the church, in that order, because she'd decided that the one
person owed the truth first was the woman who'd been lied to as badly as she had. Mr. Puckett was taken off the
westbound at La Junta in April and did eight months, and the second marriage was set aside.

The two women have written to each other every month since. Neither has remarried. Mrs. Puckett asked the editor
to change the other woman's name and nobody else asked for anything, and the editor says that's what decided the
matter, and it's the truth. The editor wanted one letter in this chapter with no monster behind it, so that the
reader would have to decide, four times, whether the pleasant man was the ordinary kind.
""",
      open=[("Is it only a man?",
             ["Yes. Keep this one clean. The chapter works because one of its five is exactly what it looks like.",
              "Mrs. Yeager isn't sure. The man who came home to Trinidad in the spring before he was taken off the "
              "train at La Junta was a little more restful than the man she'd married in November."])],
      table="""
Two women writing to each other across a territory about the man who lied to both are a good pair to meet: one at
Dodge, one at Trinidad, and each knowing things about the other's town a posse might need. Let them be allies and
not a joke. The editor didn't print them as one.
""")


# ================================================================ Songs & Sayings of the Territory
intro("songs", """
A song is the only paper in the Book of Legends nobody wrote down at the time, and that makes this the
chapter where the Keeper has the most room. Three of the four entries have a real story behind them and
the fourth is the Weather Song, which [[kb:legends-song]] carries with its four readings and its one
hard rule: never write it down and never make a verse a puzzle with a solution. Nothing below breaks
that rule. What's here is what the papers show about where the verses point.

Miss Harriet Crandall is the one person in the chapter who is exactly what she seems: a folklorist from
a college in Massachusetts, thorough, delighted with her work, and determined to draw no conclusion
she can't defend. Keep her that way. She's worth more to a table as the one sane collector in the book
than as anything else.
""")

entry("sayings",
      people=[],
      places=[],
      creatures=["The Tallyman"],
      threads=["collector", "ninechairs", "paidinfull", "blacktrain", "fifth", "notice", "understanding", "spur"],
      when=[],
      story="""
Every saying on Ashby's list is somebody's advice with the reason worn off it, and a Keeper who knows the reasons
can put any of them in an old woman's mouth and have it mean something.

<em>Salt on the sill and iron on the door</em>: because salt stops most of the dead and iron stops most of the rest,
and iron stops more of the things that aren't dead at all. <em>Never tell a stranger your mother's name</em>: because
the Long Table counts a family through its mothers, and a stranger who has your mother's name and your birthday can
do the counting ([[ref:notice]], where Mother Harrow asks every man she meets). The clerk's aunt in
[[ref:collector]] has a different reason, and so do half the families on the Plains, and all of them are right.
<em>A sweet well that was dry last year is a neighbour</em>: drovers out of Perdition Basin carried that one north, and
they meant it exactly. <em>Pay a man the day he works. Pay anything else the day after</em>: because a debt to
something that isn't a man gathers interest by the night, and the day after is the soonest you'll know what you owe.
<em>The country keeps books</em>: see [[ref:paidinfull]], and the old clerks at Washington in [[ref:understanding]],
who believe the same rule run backward. <em>Give the long train the main line</em>: railroad men, and see
[[ref:blacktrain]]. <em>Two is a coincidence, three is a road, four is somebody's business</em>: a lawman's saying, from
the days before anybody had a word for a pattern.

Five of the sayings are about the powers, and they're the ones every town knows. <em>Chicago never sleeps, and
Washington never wakes</em> is the Agency's motto and the government's habit in one line ([[ref:principles]],
[[ref:noinformation]]). <em>The Jubilee train runs full going up</em>, <em>gone up the branch</em> and <em>civil as
Jubilee</em> are what the Southwest says about Redemption every day of the week, which is the measure of how much
everybody knows about it ([[ref:spur]]). <em>A brother will stand you supper. Ask him what's for breakfast</em> is the
faithful, and see [[ref:sign]].

<em>Count the horses</em> is the one nobody can gloss, and it shouldn't be glossed at the table either. It's in nine
counties. It's what a man says to his son before the boy rides with strangers. Where it came from is the Keeper's.
""",
      open=[("Where does 'count the horses' come from?",
             ["From camps where a posse fed one more horse than it had riders, and somebody learned to notice. "
              "The Keeper's Book gives the Wills Outfit exactly that tell, and a saying is allowed to be about a "
              "legend without explaining it.",
              "From the herds that ran in the dark and never stopped. Count the horses in your string before a "
              "storm, and again after, and if there's one more, don't ride it.",
              "From horse thieves, as the one sensible man told Ashby, and everybody who has said it since has "
              "meant something else."])],
      table="""
Give each of the players' home towns one saying from this list, said by somebody's grandmother, and let the players
learn what it's for the hard way. A player who salts a sill because an old woman in Chapter One told them to has
learned the game.
""")

entry("ninechairs",
      people=["Crandall, Miss Harriet*", "the girls of Natchitoches"],
      places=["Natchitoches, Louisiana"],
      creatures=["The Ninth Child"],
      threads=["will", "ninth", "tithe", "witch", "seats"],
      when=[(1882, "Miss Crandall takes down a skipping rhyme at Natchitoches that stops at nine")],
      story="""
Natchitoches is the oldest town in Louisiana and has had a seated house of the Long Table for as long as it has had a
church. The girls in the schoolyard skip to the rhyme their mothers skipped to, and their mothers had it from theirs,
and the families that sing it are the families the house has kept.

It's a count of a family's children, told the way the Table counts them. The kettle and the door are the first two
who come easy. The baby that came before is the one who didn't live, and it's counted, because the Table counts
everybody. Honey and salt are what the family sends the house twice a year ([[ref:tithe]]), and the thing that was
nobody's fault is the one the house kept alive through a bad birth. Seven for the lamp and eight for the stair are the
night the house was sent for and the stair the midwife came up. Nine is the chair when there's nobody there, which is
the ninth child's, because the ninth goes to the house.

The girls stop at nine and start again at one because after the ninth the count begins over with the next
generation, and every girl in that schoolyard knows it without having been told, the way children know which houses
not to cut through. "Nobody's mother" is the one at the head of the Table. "Nobody said" is the rule.
""",
      open=[("Is the rhyme a warning or a lesson?",
             ["A lesson. The house taught it to the first family it kept, so that their children would grow up "
              "knowing the terms and nobody could ever say they weren't told.",
              "A warning. A family that said no taught it to its daughters so they'd count their own children "
              "and know which one to hide, and the house has been trying to stop it being sung for sixty years.",
              "Both. It's the same rhyme, and it depends which family's girls are skipping."])],
      table="""
Miss Crandall sent Ashby this rhyme because he asked for anything with a table in it, and a posse asking a
folklorist the same question will get the same answer. Children skipping it in a yard are the gentlest way to
tell a table that the Long Table is real long before anybody from it is met, and a player who counts along and
stops at nine should get a look from the girls.
""")

entry("muster",
      people=["Straughan, Colonel (the old gentleman on the grey)", "the section hands at Yuma"],
      places=["Jubilee", "Yuma"],
      creatures=[],
      threads=["spring", "lady", "gold", "spur", "clerk", "tenth"],
      when=[(1883, "The Saturday Muster and its parody are taken down at Yuma on the same afternoon")],
      story="""
The Saturday Muster is what the militia marches to, and every line of it is the country's creed in a tune a child can
learn: the day, the word, the land, the flag, and a refrain that ends with nobody going away. The old man on the grey is
Colonel Straughan, who led the first party in to the spring in 1873 ([[ref:spring]]) and drills the square two hours every
Saturday. The town calls him the old man, and the visitors call it cricket.

The section hands at Yuma sing it back at the branch train in their own words, and their words are better, as section
hands' words usually are. The Collector swears there's no such town, so who's flying the flag? Every town on the Southern
Pacific knows that verse. It's the whole of Washington's silence and its failure in four lines, sung by men laying track.

Nobody goes away is the line to hold on to. No return ticket is sold at Yuma. A clerk walked out through the sand hills and
went back ([[ref:clerk]]). A man walked out to the Tenth's patrol and was gone from the guardhouse by morning
([[ref:tenth]]).
""",
      open=[("Is the Colonel the preacher the women talk about?",
             ["No. He's a soldier, and he believes every word, and he has never once wondered who writes the list.",
              "He's the only man in Jubilee old enough to have met the preacher, if there was one, at the spring in "
              "1873, and he told a San Diego paper he didn't recall any such man."])],
      table="""
Have the section gang sing the parody at a posse on the platform at Yuma while the branch train fills with gentlemen. Then
put the real one in the mouths of children on the Jubilee side, and let the posse hear the difference.
""")

entry("keelers",
      callings=["Gunhand"],
      people=["Standish, Eli", "Oakes, Reuben", "Oakes, Sarah", "Horne, Jno. (carpenter)",
              "Garland, W. P. (sheriff)", "the printer at Keeler's Ford", "Crandall, Miss Harriet"],
      places=["Keeler's Ford"],
      creatures=[],
      threads=["weathersong", "salitre", "ninechairs"],
      when=[(1883, "Eli Standish is taken to the gallows at Keeler's Ford on 12 October and the trap fails "
                   "three times; the sentence is commuted by wire on the 15th")],
      story="""
Eli Standish shot Reuben Oakes in a quarrel over a wagon, and he was nineteen and quicker, and the court at
Keeler's Ford sentenced him to hang on 12 October 1883. The carpenter built a new gallows in pine and tried it with
a sack of sand on the evening of the 11th, and the trap fell clean. The job printer ran off five hundred copies of
a ballad to sell in the square, the way they do back East.

Sarah Oakes had been married nine years to a quarrelsome man who always said a man shouldn't hang for being quicker
than another man. She wrote to the governor on the 11th and asked him to spare the boy, and she said in the letter
that she hadn't forgiven him and didn't know that she would. Then she went into the square and sat down on the
ground with her back against the gallows post, in the rain, and didn't move all night. The deputy tried to bring
her in twice.

In the morning the trap was drawn on Standish three times and didn't fall, and between each try the carpenter put
the sack on it and it fell clean. The sheriff took the rope off himself and walked the boy back and wired the
governor that he wouldn't try a fourth time. The governor commuted the sentence on the 15th. On the 16th a clean
copy of a new last verse was left at the printer's door, and he set it because it scanned, and the second printing
is the one that's sung. Sarah Oakes gets a letter from the penitentiary once a year and keeps them all.
""",
      open=[("What held the trap?",
             ["Sarah Oakes. She sat against the post all night wanting what Reuben would have wanted instead of "
              "what she wanted, and the country took her at her word. Nobody gets a working like that twice.",
              "Reuben Oakes, who meant what he always said, and didn't stop meaning it when he died.",
              "New pine in a wet week. The carpenter's affidavit is true, and a sack of sand isn't a frightened "
              "boy who plants his feet."]),
            ("Who wrote the new verse?",
             ["Sarah Oakes, who can write a clean copy, and doesn't want the credit.",
              "The printer's wife, who was in the square that morning and didn't like the first verse.",
              "Nobody Miss Crandall will ever find. Somebody always writes the new verse, and she's right that "
              "it's always somebody who doesn't want to be thanked."])],
      table="""
This story is the rare one with no monster and a mercy at the end of it, and a table that has been in the dark a
long time will remember it. If the players are ever at a hanging, let a widow be in the square, and let them decide
whether to bring her in out of the rain. Keep it separate from the Weather Song: this is a ballad a printer was
paid for, and its new verse has a writer in Keeler's Ford.
""")

entry("weathersong",
      people=["Crandall, Miss Harriet", "Odom, Mr.", "Coyle, T. (marshal)"],
      places=["the Bitterroots", "Calvary Crossing"],
      creatures=[],
      threads=["satchel-crandall", "wrongdetail", "pell", "sanclavo"],
      when=[(1879, "The Weather Song is first sung by children, as far as Miss Crandall can date it"),
            (1885, "Miss Crandall's unattached verses stand at forty-one")],
      story="""
The Weather Song is one of the three legends in [[kb:legends-song]], and everything the Keeper's Book says about it
holds here: four readings, pick one, never say it, never write the song down at the table, never make a verse a
puzzle, and never let it explain the Mad Spaniard or the Wills Outfit or be explained by them. This entry adds what
the papers show and leaves the song where the Keeper's Book leaves it.

What the papers show is Miss Crandall's work. She has eleven hundred verses from six territories, sorted by first
attested date. Nine hundred and sixty follow an event she can name by four months to three years, which is what a
song does. Forty-one follow nothing she can find, and they're built exactly like the rest: a place, a month, a
family, a circumstance, the same metre and the same wrong grammar in the third line. By October 1884 three of the
forty-one had attached themselves to events in the county papers, and the verses were older than the events. By
1886 the figure was thirty-one.

The three verses she printed are all about Perdition Basin. One is the Odom well, which a stranger on the north road
spoke of first ([[ref:wrongdetail]]); the song is reporting what happened afterwards, the way it reports everything,
and it explains nothing about who the stranger was. One is about a marshal at the Crossing carrying a light, on a
night nobody has had yet. One is about the seventh well, and the three, and what's at the bottom of it that was
never in the sea.
""",
      open=[("Which reading is it?",
             ["[[kb:legends-song]] has the four. Pick one, write it inside your screen, and let the table stay "
              "wrong about it for years."]),
            ("What night is the marshal's verse about?",
             ["Decide it before the players reach it, and don't let the players know you have. "
              "<em>The man that carried both of them put neither down that night</em> can be Coyle holding a "
              "lantern and a badge through a night the Crossing well is fought for, or it can be somebody the "
              "players make marshal, and then it's about them."])],
      table="""
The Keeper's Book gives the one scene the song is for: the night the players hear a verse about something they did
that nobody saw. The unattached verses give a second. Let the players hear one of the thirty-one, about a place they
know and a month that hasn't come yet, and then let the month come. Don't hurry it. Miss Crandall took two years to
sort eleven hundred verses, and she'd want you to take your time.
""")


# ================================================================ Them That Make a Living At It
intro("trades", """
Everybody in this chapter goes toward the thing by choice and files a return afterwards, and the returns
are honest in the way trade paper is honest: they say what was done and leave out why. The stories behind
them are the why. Most of these people are the players' own kind, bounty men and doctors, trackers and
deputies and hired guns, and the entries are written so a Keeper can hand one of them to a player as a
past, or put one across the fire from the posse as a colleague.

The Trades are also where the Keeper's Book's bargain economy shows its bills: a letter about an
arrangement, a doctor's patient with a mark, a notice from the Long Table with no money on it. A table that
has been dealing with the dark should read this chapter and see what it looks like from the far side.
""")

entry("claim",
      callings=["Bounty Hunter"],
      people=["the bounty man", "the county clerk", "warrant 41"],
      places=["Calvary Crossing"],
      creatures=["The Nightwalker", "The Blood-Thin", "The Risen"],
      threads=["undertaker", "swarm", "deputy", "vane"],
      when=[],
      story="""
Warrant 41 was a live man when the county wrote it: wanted for a killing at a homestead, fled south with a posse's
lead on him. The bounty man took it for the reward and was nineteen days behind him. When he caught up, what he
caught up to had stopped being a live man some time in the second week and was living in a line cabin in the
breaks by day and going out by night. It had been bitten, and it had fed, and it was a long way into turning.

He did it properly, and the claim is the record of that. Forty pounds of salt, lamp oil, two men hired at the
Crossing for three days because it isn't work to do alone, and two days' digging and lime, because a thing like that
is buried deep and limed and salted and the ground is never marked. His coat didn't survive it. The county
disallowed the coat, and queried the digging, because warrant 41 is on the county's books as a live man at large and
the county can't pay to bury a man it's still looking for.

The clerk allowed the salt without a query and wrote "see me", because the clerk has seen claims like this before.
He's been clerk twenty-two years. He knows what forty pounds of salt is for on a warrant, and what it means that the
bounty man didn't bring back a body to collect on, and he paid the claim out of a fund the commissioners don't know
he keeps. Warrant 41 is still open. It will be open for as long as the county keeps books.
""",
      open=[("Who was warrant 41?",
             ["A homesteader who killed his neighbour over water in a dry year, and who was bitten on his way south "
              "by something that had come up a failing well.",
              "Josiah Vane, if Vane ran from Module I's night, and the county wrote a warrant for the banker on a "
              "charge of fraud. The bank's correspondents have stopped asking where he went.",
              "Somebody your posse let get away, a long time ago in your campaign's own terms."]),
            ("Who is the clerk?",
             ["A man who lost a brother to something like warrant 41 in the fifties, and has kept the fund since.",
              "One of the people who knows certain courtesies about the dead without being part of anything, the "
              "way the Keeper's Book says the Long Trail's servants do."])],
      table="""
The claim is a good way to hand a bounty hunter player their first real job: give them a warrant on a man who has
stopped being one, and let them find out what a clerk means by "see me". The clerk is the most useful ally in the
county, because he pays for what the county won't, and he'll want a favour back, and it'll be a hard one.
""")

entry("notice",
      callings=["Bounty Hunter"],
      people=["Harrow, Zilpha (Mother Harrow)", "J. T. (a man in the bounty trade)", "a man out of Denison"],
      places=["Fort Smith", "Lampasas", "Denison", "Fort Worth"],
      creatures=[],
      threads=["harrow", "ninth", "will", "sayings", "commission"],
      when=[(1879, "Mother Harrow stands a bounty man a drink at Lampasas and asks his mother's name"),
            (1884, "A notice for Zilpha Harrow, with no sender's name on it, goes up on walls from Fort Smith to El Paso "
                   "in the spring")],
      story="""
The notice is how the Long Table hunts, and J. T. read it right. It has no sender's name and no printer's, and nobody in
a saloon will say who put it up, because the houses don't put their name on paper. There's no money on it because the
houses don't pay. A kindness becomes owed. A man who brings word of Zilpha Harrow will be looked after, and his house will be kept, and
his wife will have easy births and his children will come through the fevers, and in three generations somebody
polite will knock at his grandson's door with the dates. That's what being owed by the Table is. It's the arrangement
in [[ref:will]], begun for a favour instead of a birth.

The man out of Denison took it in April. He's never found her and never will, and it doesn't matter: the obligation
began the day he took the notice down and put it in his pocket, because that's the day he agreed to look, and his
house has been kept since. His wife is having a very easy time of it. Everybody in that house is well. J. T. knows
exactly what that means, and so does every man in the trade who went quiet when he read it.

J. T. met Mother Harrow at Lampasas in 1879, before she did what she did, when she was keeping a house for the Table
and standing drinks to bounty men for the pleasure of asking their mothers' names. She told him it was a good name and
he was to keep it. She meant it kindly. She also meant that she'd counted his family, and found nothing the Table was
owed, and was letting him go.
""",
      open=[("What happens to the man out of Denison's family?",
             ["Three good generations, and then the porch.",
              "Nothing, if the Table is honourable about a favour that wasn't delivered, and it may be. It keeps "
              "immaculate books."])],
      table="""
Put the notice on a wall where a bounty-hunting player will read it, and let the more experienced NPCs in the room go
quiet. If a player takes it down, the obligation starts that night: their luck turns, their people prosper, and the
table should understand exactly what's been bought before anybody at the Table says a word.
""")

entry("terms",
      people=["Crail, A.*", "Sam (a younger man in the trade)", "Kessel, Mrs."],
      places=["the Kessel well, Township 9, Kansas"],
      creatures=["The Thing in the Well"],
      callings=["Witch Hunter"],
      threads=["lookeddoor", "crailtrial", "namebook", "commission", "notice"],
      when=[(1879, "A Kansas county pays A. Crail twenty-five dollars out of the road fund for abating a nuisance at the "
                   "Kessel well"),
            (1882, "Crail writes to a younger witch hunter that he has given up the things that wear men and now does "
                   "the houses")],
      story="""
A. Crail is the best witch hunter in the Book of Legends and the most honest about what the work costs. His card prices the
trade like a carpenter's: graves salted at two dollars, a house cleared at ten, a well read at five, names written down for
nothing, and nothing owed if nothing's found. He hunted the dead for eleven years and the things that wear men for six, and
the county paid him out of the road fund for the Kessel well because a well in use again is a road expense.

By 1882 he does the houses. His letter to Sam won't say why, and the reason is in [[ref:commission]]: a house kept his
mother, and was paid for keeping her, and paid with a child, and Crail wants the house's name, and the price, and the
grave. He hunts the houses one at a time with a book of names, and they're the only quarry he ever had that was kinder than
he is.

The two ways to cross a name out are the key to his book ([[ref:namebook]]). One line through means the thing is finished.
A second line, crossed the other way, means he let it go. Sam is the only man he ever told, and Crail stopped answering him
because Sam asked which way he'd crossed out the house on the Sabine.
""",
      open=[("Was Crail the child?",
             ["Yes. He was the ninth, and his mother said no, and the house stopped answering her door, and she died in "
              "a hard confinement the next winter with nobody to go to.",
              "No. His sister was the ninth, and the house took her, and his mother never spoke of it, and Crail found "
              "the girl's name in a house's book in 1876."])],
      table="""
Crail's card is the best handout in the book for a Witch Hunter player: it's the trade as a trade. Crail himself is a good
mentor and a dangerous one. He'll take a posse's Witch Hunter on a job and watch how they cross out a name.
""")

entry("sawbones",
      callings=["Sawbones"],
      people=["the country doctor", "B. (a labourer)"],
      places=[],
      creatures=["Dark Cultist & the Hollow Prophet", "The Cursed Man"],
      threads=["hexer", "glad", "gloves", "tract"],
      when=[],
      story="""
B. was a labourer who had been sick for eleven years of the doctor's knowing him: chest, back, fevers, the kind of man
who's always a little worse than he should be. In the winter he found the leaflet from [[ref:tract]] in a
boarding-house passage and did what it said. He asked, out loud, in an empty room, to be well. Something older than his
trouble listened and didn't mind in the least what he asked for.

The mark on his forearm is the first step of it. It isn't a bruise or a burn and it isn't in any book of the doctor's,
because it's the Mark, and a Mark has a definite edge and grows. The health is real. He's put on a stone and his grip is
strong and he hasn't been ill a day since March, and the doctor is right that he'd show him to a college. By December he
wouldn't let the mark be measured, because a man doesn't like his creditor's figures read back to him.

In May he came in for the statement of sound mind. He wanted it to read later, when he's further along and can't be sure
any more that the man who asked in the empty room was the same man reading. He wants proof that he chose it in his right
mind. The doctor gave it to him, and has been sitting there since wondering whether a physician is allowed to give a man
that, and the answer is that nobody else would have.
""",
      open=[("What did B. ask for?",
             ["To be well, and the face that answered was the one that comes to a failing body with meat and "
              "strength and never stops wanting. He eats a great deal.",
              "To stop hurting, which isn't the same as to be well, and the one that answered is taking the warmth "
              "out of him a degree at a time along with the pain."]),
            ("How far along will B. be when the players meet him?",
             ["Two or three steps: well, strong, and beginning to stop needing anybody.",
              "At the last, reading the doctor's statement over and over in a boarding-house room, trying to "
              "recognise the hand."])],
      table="""
The doctor is the one to meet: a living country physician who'll talk to a posse about B. with B.'s permission, and
then about three other patients with marks he's seen since. B. himself is the best Dark Cultist a table will ever
meet, because he's decent, and he's grateful, and he'd do it again.
""")

entry("surgeon",
      callings=["Sawbones"],
      people=["Aske, Philip (acting assistant surgeon)", "Aske, Kate (his sister)", "the commanding officer",
              "the sutler's girl"],
      places=["a post on the Pecos", "Horsehead Crossing", "Baltimore"],
      creatures=["The Mourner", "The Long Trail's End"],
      threads=["plates", "fortclark", "carrow"],
      when=[(1883, "A contract surgeon on the Pecos sees men soaked to the skin before they die; he drowns at "
                   "Horsehead Crossing on 14 November")],
      story="""
Philip Aske was a contract surgeon from Baltimore who went to a four-company post on the Pecos in the spring of 1883,
and in July he began to see it: a man standing on his infirmary floor soaked through in a dry country, water running
off his chin, and nobody but Aske seeing it, and the man dead inside the week of something that had nothing to do with
water. Five of them by September. He wrote to his sister because he wrote to her about everything, and because if he
didn't write it somewhere he'd have had to say it at mess.

On the morning of 11 November two companies rode out after horse thieves, sixty men and the major, and every one of
them was wet through. Aske saddled a horse and went after them alone, without leave, because he couldn't think what
else to do.

He didn't reach them. On the 14th he came to Horsehead Crossing, where the Pecos runs eighteen inches deep over a
bad bottom and has taken more cattle than any crossing in Texas, and he drowned there. The column came back on the 20th
without a man lost. The commanding officer wrote that the surgeon was given to fancies and to drink, and closed the
file, and Aske's sister wants it said that he wasn't a drinking man, and he wasn't.
""",
      open=[("Why did the column come back?",
             ["Because Aske went. What was coming for sixty men at the Pecos took one who rode out to meet it "
              "instead, and was satisfied.",
              "Because the wet never meant the column. Aske had been seeing his own drowning reflected in every "
              "man he looked at since July, and it was always his.",
              "It didn't come back. It's late. The column is sixty men still wet, and the post's returns will show "
              "it the year after."])],
      table="""
Aske's sight is a thing a Keeper can give a player, briefly, through a sawbones who has seen too many deaths: one
NPC in a scene stands there soaked and nobody else notices. What the player does about it is the session. If they
ride out after somebody wet, remember Horsehead Crossing.
""")

entry("hexer",
      callings=["Hexer"],
      people=["the letter-writer (a mother)", "her daughter"],
      places=[],
      creatures=["The Tallyman"],
      threads=["sawbones", "glad", "tract", "paidinfull"],
      when=[(1874, "A woman asks for her dying daughter's life in a kitchen in the spring, and gets it"),
            (1886, "The woman dies; her daughter reads the letter and asks for two words to be changed")],
      story="""
She was a farmer's wife with one child, and in the spring of 1874 the child had the throat distemper and the doctor
had stopped coming. She didn't know anything about the Old Dark. She knew what everybody knows, that you can ask for
things, and one night after the child's breathing changed she stood in her kitchen and said out loud what she wanted.
Something in the room listened. She's right that it was attentive, and she's right that she'd know it again.

The girl lived. There were no terms because the Old Dark doesn't write them. It lends, and the loan gathers, and it's
paid as it's asked for. Hers is paid the fourth week of every October: a cow down, a fire in the chimney, her husband's
hand cut to the bone at the harvest, a letter lost with money in it. Never so bad a neighbour would notice, never
twice the same. Eleven years of October is the interest on one night in a kitchen, and she did the arithmetic every
year and came out the same way.

She died in 1886. She'd have liked to be remembered as cheerful, and she was. What nobody knew when she wrote the
letter is whether a loan like hers dies with the borrower, and her daughter, who's twenty-two and downstairs, and who
read the letter before the editor printed it, has had a quiet September.
""",
      open=[("Does the debt pass to the daughter?",
             ["Yes. It's her life that was bought, and the fourth week of October is hers now.",
              "No. It was the mother's asking, and the mother paid it in full. The Tallyman came to the funeral, "
              "stood at the back with his hat off, and didn't go to the house.",
              "Nobody knows yet, and it's September."]),
            ("Which two words did the daughter change?",
             ["The two that said what her mother asked for, which the mother had written after all.",
              "'Every October' to 'every autumn', because the daughter wanted it to be less exact."])],
      table="""
The daughter is the story now: a young woman with a letter, a season coming, and nobody to ask. A posse she hires
to sit up with her through the fourth week of October will see what the interest looks like, and will have to decide
whether to pay it for her, fight it, or find the Tallyman's ledger and read her name in it.
""")

entry("contract",
      callings=["Gunhand"],
      people=["a cattle company's district agent", "eleven stock inspectors"],
      places=["Kansas City"],
      creatures=["The Regulators", "The Cattle Baron's Men", "The Hired Gun"],
      threads=["bitters", "clause", "vane", "kansas"],
      when=[],
      story="""
A cattle company with an office at Kansas City and range in three territories signed eleven of these in one season,
and the second sentence of the first article says exactly what the men were hired for. They're regulators. They ride
for the company's agent in the district, they answer to nobody else, and they don't talk to any county officer. The
company pays three wages because the work is killing homesteaders and small ranchers the company says are stealing
its stock, and the fourth article is the company buying its own innocence in advance: it will pay for a man's defence
and be concerned in nothing else.

Nobody showed the form to a lawyer because nobody at the company needed to be told what it would say. The company
wasn't worried because it had never needed to be. Every county the inspectors worked in had a cattle-company man on
the commission, and the courts sat in towns the company's cattle fed.

The eleven are the men the Keeper's Book means when it says the Vane Interest sends for the Regulators. They go where
money is losing ground to people, and they're good at the work, and a few of them believe the homesteaders are
thieves, and the rest have stopped asking.
""",
      open=[("Where are the eleven now?",
             ["Six at the Clear Fork ([[ref:bitters]]) and five somewhere else, working for a company with the same "
              "form and another name.",
              "In Perdition Basin, if the Vane Interest has got that far, riding for a district agent who takes his "
              "instructions from a bank."])],
      table="""
A blank form is a strong handout: let a player read the second sentence aloud. Stock inspectors are the Bestiary's
Regulators at full strength and the Cattle Baron's Men below it, and they're the one human enemy in this book the
players can't out-shoot their way past, because the company pays for another eleven.
""")

entry("bitters",
      callings=["Gunhand"],
      people=["Ransome, Dr.", "Tolland, Ezra", "Weller, Dutch", "the company's attorney", "the priest at Fort Collins"],
      places=["Cheyenne", "the Clear Fork", "Fort Collins"],
      creatures=["The Mesmerist", "The Regulators", "The Revenant"],
      threads=["contract", "sawbones", "lamps"],
      when=[(1884, "Nine people, two men, three women and four children, are killed at three cabins on the Clear "
                   "Fork on 9 October; five inspectors swear the same affidavit"),
            (1885, "Ezra Tolland, the sixth man, makes a statement before a priest at Fort Collins")]
      ,
      story="""
Six of the company's inspectors rode to the three cabins on the Clear Fork on the night of 9 October 1884, having
drunk Dr. Ransome's Courage Bitters, and killed everybody there: a woman at a stove, a boy with a water bucket, an old
man asleep in his chair by the door, and six more. Nobody fired from the cabins. The company's attorney drew one
affidavit for the five who'd swear and they swore it, and they were acquitted at Cheyenne in March.

Dr. Ransome is the reason they swore it the same, word for word, down to "the aforesaid cabins". He keeps a
drugstore in Cheyenne and he's a mesmerist of the kind the Bestiary describes: a man with a way of making other men
agree. His bitters are gentian and whisky and a little of him, and they do what the label says. A man who has drunk
them does hard work with a steady hand, and afterwards, when he's handed a story, he remembers the story. The five
aren't lying. They remember being fired on. The attorney's paper is the only memory of the Clear Fork they have left.

Ezra Tolland poured his dose in the grass because his father drank, and he's the only one of the six who remembers
the night as it was, and he's seen it every night since. He told it to a priest at Fort Collins, who asked his leave
to pass it on. The editor drank a glass of the bitters at Cheyenne and it steadied the editor's hand, and the editor
hasn't drunk another, and is right not to have.
""",
      open=[("What happens at the Clear Fork now?",
             ["Nothing that walks. Nine people are buried in the county's ground under a verdict of persons unknown, "
              "and the horror is that it's finished.",
              "The old man who was asleep in the chair by the door. He's walking toward Cheyenne one step a night, "
              "and there are five names and a druggist's on the list he carries."]),
            ("Is Tolland safe?",
             ["No. The company knows there were six, and the attorney knows which of the six didn't drink.",
              "Yes, as long as he stays with the priest, and he's begun to think of taking orders."])],
      table="""
Dr. Ransome is the villain here and he's a small man in a drugstore, and a posse can walk in and buy a bottle. The
bitters are an easy thing for a Keeper to use and a hard thing for a player to refuse after a bad night: they steady
the hand and settle the conscience, and a player who drinks one before a fight should be told afterwards that they
remember it very clearly, in somebody else's words.
""")

entry("route",
      people=["a travelling man for a St. Louis house", "Rudd, Mrs.", "Lamb, H. (barber)", "Varney, Mrs.",
              "the agent at the depot at Wallace"],
      places=["Salina", "Ellsworth", "Hays City", "Wallace", "Kit Carson", "Pueblo"],
      creatures=["Dark Cultist & the Hollow Prophet"],
      callings=["Dark Cultist"],
      threads=["tract", "sign", "creeds", "congregations", "partners", "asked"],
      when=[(1882, "A travelling man works his spring route through Kansas and Colorado, and writes a word beside a name "
                   "in every town")],
      story="""
The third column is the brother or sister in each town, the one who keeps the faith and stands a stranger supper on the
second night. The fourth is what each came wanting, which the drummer calls what they drank, and the words are the six
wants the tract in [[ref:tract]] offers: rest is to stop hurting, know is to know, eat is never to go hungry, keep is to
keep somebody out of the grave, loved is to be loved, and rich is rich. The last column is the one that should frighten a
Keeper: which towns won't sit with which.

[[kb:olddark-devotions]] pairs each want with the face that answers it, and [[kb:olddark]] has the rule this page shows at
work: two congregations at each other's throats are two hands of one body. Hays eats and Ellsworth knows, and they won't
sit together. Pueblo has two who don't speak, one rich and one knowing. Salina and Wallace won't sit with anybody. Every
one of them is feeding the same thing.

The travelling man is a brother himself. He sells soap now and nothing else, and he told the editor the columns were about
drink because that's what he tells everybody. Wallace is the town that drinks keep, and the agent at the depot is the one
he won't talk about.
""",
      open=[("What does the agent at Wallace keep?",
             ["Somebody out of the grave, as the want says: his wife, who died in 1879 and still keeps his house.",
              "The road. The Long Trail's people keep the dead moving, and Wallace is where the long train "
              "([[ref:blacktrain]]) takes water."])],
      table="""
The route book is a map a posse can ride: a brother in every town, what each one wants, and who'd sell out whom. A Dark
Cultist in the posse would know some of these people. Use it to show that the faithful are everywhere and never together,
which is the most frightening thing about them and the most useful.
""")

entry("scout",
      callings=["Drifter", "Mountain Man"],
      people=["the tracker", "the missing man's family"],
      places=[],
      creatures=["The Long Trail's End", "The Hidebehind"],
      threads=["fortclark", "gatherings", "surgeon"],
      when=[],
      story="""
The missing man went out walking on the 14th, as he did most evenings, northwest from his place across open ground.
A mile and a quarter out he met the other track, or it met him. It came in from the north and settled forty yards off
his left hand and kept pace with him, across broken ground where keeping a distance means looking, for nearly two
miles. It didn't close on him. It walked the way something walks that is going somewhere at its own pace and has no
reason in the world to hurry.

He saw it, somewhere in the second mile, and started to hurry. It didn't. That's the part the tracker is sure of and
it's the worst part of the story: a man running flat out across a mile and a half of bad ground and a thing forty
yards off walking, and the forty yards never changing. He reached the rocks and stopped, and died there, of exposure
the coroner says, which is to say of nothing anybody could name.

The other track went on northwest at the same pace for as long as the tracker followed it, which was four hours, and
it was still going. It was never after him at all. It was walking somewhere, and he walked out into its road, and he
was beside it for three miles, and a man can't be beside that for three miles.
""",
      open=[("What made the second track?",
             ["The thing the Bestiary calls the Long Trail's End, that was once a shepherd for the dead and now "
              "gathers the living before their time, walking to wherever it gathers them.",
              "Nothing that walks on its own. It was the man's own track going on after he stopped, a little ahead "
              "of where he'd have gone, and it's still going.",
              "Something from the high country, walking northwest toward it, like the congregations in "
              "[[ref:gatherings]]. The tracker has heard since of two more tracks like it, in two other counties, "
              "going the same way."])],
      table="""
The tracker is a man a posse should hire and trust. Give the players his account first, and then, a session later,
give them a second track at forty yards off their own left hand at dusk, not closing, not hurrying. Don't roll
anything. Ask what they do. The only mistake is to run.
""")

entry("trapper",
      people=["an old trapper at Fort Hall", "Rourke, Jas. (Jim)"],
      places=["Fort Hall", "a fork of the Salmon"],
      creatures=["The Hidebehind", "The Great Bear"],
      callings=["Mountain Man"],
      threads=["scout", "dugout", "fortclark", "carrow"],
      when=[(1853, "Jim Rourke is killed at his camp on a fork of the Salmon in October while his partner pulls the "
                   "traps")],
      story="""
Two trappers worked a fork of the Salmon in the autumn of 1853, in country nobody else trapped, which they took for luck.
Something came to their camp the second evening and tore it up and walked round the fire on two feet, and every time they
followed its track into the timber it went behind a tree and didn't come out the other side. They agreed to go. One went
up the creek to pull the traps. Jim Rourke stayed to break camp, and when his partner came down at dark Jim was dead by the
fire log with his neck broken and four marks in his throat, and the packs untouched.

The Bestiary's Hidebehind keeps a tree, a shadow or your own companion between itself and your eyes, and takes the one who
works alone. Rourke was a man who looked round, and it came in behind him the whole way without once being in his sight.
That's the horror the trapper has carried thirty years: there was nothing Jim could have done, because there was never
anything to see.

The editor's grizzly is the other reading, and a good one. A bear will tear up a camp and stand, a frightened man will see a
man's walk in a bear's track, and the story has been told of four men in four ranges. The tally in Rourke's hand is what the
editor can't explain away, and the trapper gave it up the day he finished telling it.
""",
      open=[("What killed Jim Rourke?",
             ["The Hidebehind, which still keeps that timber, and no trapper has worked it since.",
              "The Bestiary's Great Bear, a grizzly old enough to have learned that men look round, which is worse in "
              "its way.",
              "The partner. A man who killed his partner in the timber has a reason to give the tally away thirty years "
              "later, and the story got told of four men in four ranges because the first man to tell it needed "
              "something to tell it around."])],
      table="""
A Mountain Man in the posse has heard this story at every fort in the high country and has an opinion. The Hidebehind's
entry says the fight is geometry and light, and this camp is where to teach it: ring the fire, stand back to back, and keep
to open ground, the way the old man does now.
""")

entry("thirdcell",
      people=["Whitlock, Dr. M.", "the founding superintendent", "his granddaughter", "the man in the third cell"],
      places=["the asylum", "Placer", "Carson", "the Reese River", "Elko"],
      creatures=["The Pallid Herald", "Servant of the Deep Dark"],
      threads=["rocksnake", "floor", "drifter", "giant"],
      when=[(1851, "The founders of an asylum in California dig its cellar and receive a man out of it"),
            (1883, "Dr. Whitlock discharges the man in the third cell in June with a suit and ten dollars"),
            (1884, "Oldest settlers die along the stage road east, a town at a time, in December and January")]
      ,
      story="""
In the summer of 1851 the men who founded the asylum dug its cellar into a hillside above a gold camp, and at nine feet
the picks opened a hollow in the rock the size of a small room, and there was a man sitting in it. He was dressed in
nothing anybody recognised, he was dry and clean and courteous, and he asked them what the weather was doing. They
were godly men, three doctors and a minister, and they believed they knew what he was. They couldn't kill him and they
tried. So they did what the padres did at San Clavo: they kept him. The card on the door is the binding, and the
binding was the four of them, alive. Feed him. Never converse. Not to be released while any of us who received him are
living.

The last of the four died in 1882. For a year the card held him because nobody read it closely. Then Dr. Whitlock came,
trained to believe in light, air and conversation, and sat with him an afternoon, and found a lucid, well-read old man
who asked three times about the weather because he'd been underground for thirty-two years and before that for longer
than anyone knows. Whitlock gave him a suit that didn't fit and ten dollars and opened the door.

He went east along the stage road on foot, a town at a time, and took a meal in each and paid for it, and the day after
he passed, each town's oldest settler died. The first ones, who were there before anybody. He isn't killing them. He's
noticing them, the way a man walking through a house he left long ago notices what's been moved in, and they don't
survive being noticed.
""",
      open=[("What is he?",
             ["The founders called him the Devil, and [[kb:olddark]] says the preachers' Devil is somebody else. "
              "He's something of the Old Dark's that was here before there was anybody to notice, and he's taking "
              "stock.",
              "A herald. Wherever he takes a meal, the Old Dark has turned its attention there, and the oldest are "
              "only the first to feel it.",
              "A man, very old, who was sealed in a rock by something older than him and has only been let out, and "
              "the hard winter killed the old, as the editor says."]),
            ("Where is he going?",
             ["East, a town at a time, to wherever the thing that sealed him is, to thank it.",
              "Toward the Rockies, where [[ref:gatherings]] has congregations waiting for something.",
              "Home. He asked about the weather because he wants to know whether it's the same country."])],
      table="""
Put him on the stage road the week before the players reach a town. He's the quiet old gentleman in the suit that
doesn't fit, taking a meal at the next table, polite, interested in the weather. The next morning the town's oldest
settler is dead. If they follow him east, they'll arrive in every town the day after. The granddaughter of the
founding superintendent knows more than she told Whitlock and would tell a posse the rest for a promise.
""")

entry("gorham",
      people=["Gorham, Lyman", "Gorham, Frances", "Wood, Charles", "the inquiry agent", "the dentist at Helena",
              "the barber at Helena"],
      places=["Helena", "the canyon of the Tenmile"],
      creatures=["The Fetch", "The Skin-Walker"],
      threads=["agency", "mirror", "fivewives", "thirtysix"],
      when=[(1882, "Charles Wood appears at the hot springs near Helena in May, with no past; Lyman Gorham and Wood "
                   "go into the mountains on 9 August and one of them comes back on the 21st"),
            (1883, "Frances Gorham claims on her husband's life; three of the people who knew him best die in a year")]
      ,
      story="""
Charles Wood didn't exist before May 1882. He came to the hot springs outside Helena that month looking like a hired
man, took work with Lyman Gorham, and spent the summer learning him: his walk, his barber, his pew, his way with a
column of figures. By July the barber couldn't tell them apart in the chair. In June Wood took a plaster cast of
Gorham's mouth, the way a man takes a cast of a lock, and had a dentist make him Gorham's crown.

On 9 August the two of them went into the mountains. On the 21st one of them came back, and the body at the foot of
the ledge in the Tenmile had a gold crown on the upper left canine, and the county buried it as Wood. The man in the
house knows the business and the children's birthdays and what Lyman said the night their first was born. He's kind
to Frances, and Lyman never was, and she's the last who could tell.

Three who might have told died inside the year, each in a way a coroner could put his name to: the partner on the
cellar stairs, the brother in the Missouri, the barber in his own chair. Frances knew what the kindness meant. She
went to the insurance office because it was the only place in Helena that would have to write down what she said.
She stopped writing to insurance offices in 1886. Her husband is well and very kind.
""",
      open=[("Who came back from the Tenmile?",
             ["Wood, who was never anybody, and is a Fetch that finished the job: it has a man's life now and "
              "means to keep it well.",
              "Wood, who is a man, a confidence artist of great patience who killed four people for a store and a "
              "wife he treats better than the husband did.",
              "Lyman, after a fall, changed the way the doctors at Helena have a name for, and Frances found in a "
              "story the way out of a marriage she'd wanted for years."]),
            ("Why did Frances stop writing?",
             ["Because she decided she'd rather have the kind one.",
              "Because the man in her house found out she'd written to the editor.",
              "Because she isn't Frances any more either."])],
      table="""
The inquiry agent kept a copy of one file in nineteen years and this is it, and he'd help a posse that could show him
he wasn't wrong. Frances Gorham will give the posse coffee in her husband's parlour, and her husband will come in and
be charming, and she'll watch the players the whole time to see if they can tell.
""")

entry("deputy",
      callings=["Marshal"],
      people=["the deputy (unnamed)", "Coyle, T. (marshal)", "the county commissioners"],
      places=["Calvary Crossing"],
      creatures=["The Risen", "The Blood-Thin"],
      threads=["swarm", "forgery", "claim", "pell"],
      when=[],
      story="""
The marshal is Coyle and the county is Perdition Basin's, and the board is the one that wouldn't give Coyle his lamps
and his two men after the old burying ground ([[ref:swarm]]). The deputy had been with him eleven years. In the year
the wells began to go, he was sent out alone at night three times to calls that two men should have gone to, because
there was only one of him, and three times he went.

The third call was a homestead on the river road where a woman had sent her boy to the Crossing to say her husband
had come home. He'd been buried the Sunday before. The deputy rode out at eleven and reached the gate at midnight, and
the house was dark, and somebody was standing in the yard facing the house with his back to the gate, very still, and
the deputy stood at the gate a quarter of an hour and didn't open it. Then he rode back and wrote in the book that there
was nothing at the place.

In the morning the house was empty and the family was never found. He resigned at the end of the month, and he wrote
the board the best letter the clerk was ever given, because a man has to put a thing like that somewhere or carry it,
and he'd watched Coyle carry his. Coyle hasn't asked a fourth time.
""",
      open=[("Would opening the gate have saved them?",
             ["No. They were gone before he reached it, and the thing in the yard was waiting for whoever came.",
              "Yes, and he knows it, and that's what he carries.",
              "Nobody can say, and the players can find out, because the house is still empty and the gate is still "
              "shut."]),
            ("What does the deputy do now?",
             ["He drives freight on the Crossing road and won't be out after dark.",
              "He'd take the star again for a marshal who'd give him two men, and the players could be the two."])],
      table="""
A player who wants to be a lawman in the basin has an opening: Coyle needs a deputy and has for a year. The resigned
deputy is the man to learn the job from, and he'll ride out with the players to the river road once, in daylight, and
show them the gate. He won't open it for them either.
""")


# ================================================================ Met on the Road
intro("road", """
Half this chapter is the Mad Spaniard, and [[kb:legends-spaniard]] is where he lives: his name, what
happened on the Llano in 1541, how to run him, and the four things he might be, one of which the Keeper
chooses and never says. This book adds what's behind each paper and leaves the four readings alone. It
also holds the Keeper's Book's rule: the Spaniard, the Wills Outfit and the Weather Song never explain
each other, and the road stories here never make the fifth rider the man in the old clothes.

The other half is the road itself, which the Keeper's Book gives to the Long Trail: roads that have
killed people, gates, the dead walking, and the courtesies the living keep. A walker at a gate with a
saddle on his shoulder needs no stat block, and a table that has learned to take its cap off to the long
train has learned the country.
""")

entry("wrongdetail",
      people=["a freighter below Saltlick", "a schoolteacher on the Llano road", "a girl of fourteen on the north road",
              "Odom, Mr.", "Mad Spaniard, the"],
      places=["Saltlick Station", "the Llano road", "Fayette", "Fayetteville"],
      creatures=["The Gentleman on the Road"],
      threads=["saltlick", "collector", "weathersong", "satchel-road", "spaniard"],
      when=[],
      story="""
Ashby's list is the best short description of the Mad Spaniard anybody has written, and it matches
[[kb:legends-spaniard]] point for point: the empty hour, the courtesy, the business known before it's told, the
family asked after by name, the food refused, the arrival and leaving nobody sees, and the one wrong detail. What
the three accounts add is what the wrong detail turned out to be.

The freighter's wife is Martha and he was called her Margaret, and Margaret was the sister who died in 1861 and whose
name he hadn't said aloud in ten years. The schoolteacher is from Fayetteville and he said Fayette, twice, and her
grandfather was born at Fayette and she didn't know it. The girl on the north road was called Mr. Odom's girl and told
to tell her father to dig at the cottonwood. Mr. Odom's well failed in its third year and there's no cottonwood on the
Odom place and there's one on hers.

In each case the wrong detail was true about something else: a dead sister, a grandfather's town, a father. The
freighter caught his the next afternoon with a strap in his hand. The schoolteacher caught hers a year later, in a
letter from an aunt. The girl hasn't caught hers yet, and neither has anybody in her family, and the Weather Song
already has a verse about the Odom well that says she was not his.
""",
      open=[("Is the wrong detail ever only wrong?",
             ["The Keeper's Book lets it be: the madness shows once a night in something small and wrong. Run it "
              "that way and every wrong detail is a symptom.",
              "The Book of Legends' evidence says it's never only wrong, only early or sideways. Run it that way and "
              "every wrong detail is a true thing the traveller hasn't found out yet.",
              "Pick one of those two and hold it for the whole campaign. A table that catches you running both will "
              "stop listening to him."]),
            ("Whose daughter is the girl on the north road?",
             ["Her father's, and the stranger's detail was a slip, and the song's verse is the song being wrong for "
              "once.",
              "Mr. Odom's, from a winter fifteen years ago that two families have never spoken of. The Weather Song "
              "says otherwise, and the Weather Song is about Odom's well, not her."])],
      table="""
Put a man in old clothes on a road at an hour when nobody should be on it, and give him one of these three conversations
with a player. Let the wrong detail be about somebody in the player's backstory, and don't explain it. Then, some sessions
on, let the player's backstory produce the truth the detail was about.
""")

entry("carrow",
      people=["Carrow, Letitia (Letty)", "Carrow, Will", "Lou (her sister at Leavenworth)", "Ainsley, Mrs.",
              "Ainsley, Sam"],
      places=["the Carrow place", "the old military road west of Fort Dodge", "the Cimarron crossing"],
      creatures=["The Long Trail's End"],
      threads=["norther", "aspens", "blacktrain", "fortclark"],
      when=[(1871, "Will Carrow drowns at the Cimarron crossing going up the trail in the spring"),
            (1872, "Letty Carrow first writes to her sister about the walkers who pass on 19 October"),
            (1884, "Letty Carrow is found dead at her gate on 20 October with the dipper in her hand")]
      ,
      story="""
The old military road west of Fort Dodge carried the cattle trails north for fifteen years after the army left it, and a
good many drovers died on those trails and in the crossings of the rivers on them. Every year on the night of 19 October,
which is the night the last herds of the season crossed the Arkansas in the year the trail opened, the ones whose horses
died under them walk west past the Carrow place with their saddles on their shoulders. They're going back down the trail
to where they left the herd, and they've been going every year since.

Letty Carrow saw them the first autumn after Will drowned at the Cimarron crossing, and she put out a bucket and a dipper
at the gate because they'd been walking a long way and it was the only thing she could do, and in the morning the dipper
had been used. She did it every year. She wasn't frightened and wasn't lonely and wanted her sister to stop saying so.
In 1877 a boy of fifteen stopped long enough to drink and called her ma'am.

Will didn't walk with them for twelve years, because the river kept him and kept his saddle. In the spring of 1883 a
flood moved the Cimarron's bed at the crossing and gave up what was under it, and that October he came by with the saddle
with the silver on the horn, and drank, and hung the dipper back bowl down the way he always had, and didn't look at her.
She knew why. He was waiting for her to be ready. The next October she was sitting at the gate in her shawl with the
dipper in her hand, and the bucket was dry, and she'd gone on west with him.
""",
      open=[("Why is the date 19 October?",
             ["The night the last herds crossed the Arkansas the first year the trail ran, and the night of the "
              "stampede at the crossing that killed the first of them.",
              "Nobody knows, and the walkers don't either. They walk when the road says."]),
            ("Did Letty go with them?",
             ["Yes, and she walks with Will now, and next October the bucket at the gate will be full because Sam "
              "Ainsley's mother has started putting one out.",
              "No. She died of her heart, as the doctor from Dodge said, waiting at the gate for something that had "
              "already come and gone, and the dry bucket is only October in Kansas."])],
      table="""
A posse on the old military road on the night of 19 October meets the walkers, and there's nothing to fight. The
courtesy is to stand aside, take your hat off, and leave water at a gate. A player who asks a walker a question gets
the walker's name and the name of the herd he left and where, and nothing else.
""")

entry("walker",
      people=["Talbot, Wes", "Talbot, L. (his sister)", "the man ahead on the road"],
      places=["Horsehead Crossing", "Fort Stockton", "Fort Davis", "El Paso", "Yuma", "San Angelo"],
      creatures=["The Long Trail's End", "The Hitchhiker"],
      callings=["Drifter"],
      threads=["salt", "surgeon", "carrow", "wrongdetail", "trunk"],
      when=[(1883, "Wes Talbot crosses the Pecos at Horsehead on 1 October; a body is taken from the river below the "
                   "crossing on the 3rd and buried as his"),
            (1883, "Wes Talbot wires his sister from Yuma on 24 October")],
      story="""
Wes Talbot was a horse-breaker who drifted for work, and he crossed the Pecos at Horsehead on the 1st of October 1883 with
the river up and mean, and the river took him. The body that came out below the crossing on the 3rd was his, the dun came
out alive with his saddle on, and the freighter who'd crossed with him said so. He was buried at Fort Stockton, and his
sister had the news inside the week.

He didn't know. He went on west the way a drifter does, writing to his sister from every town, and every day there was a
man on foot ahead of him on the road with his hand up for a ride, a man he rode hard to leave and passed again seventy miles
on. The man wasn't looking at Wes. He was looking down the road behind him for somebody who hadn't come yet, because Wes
hadn't stopped yet. At Yuma Wes wired home and had the answer, and went out that evening to the sign at the edge of town,
and stopped.

The Bestiary's Long Trail's End was meant to be a kindness: a guide for the dead, walking a day ahead, patient and certain.
This is the kindness still working, for once. Wes refused him all the way across Texas, as a living man would, and he
waited.
""",
      open=[("Was Wes Talbot dead?",
             ["Yes, from the 1st of October. The letters are the only thing a drowned man ever sent home from the road, "
              "and the dun in the livery at Fort Stockton is the proof.",
              "No. A drifter with debts let a drowned stranger be buried under his name and bought another dun at El "
              "Paso, and the man on the road is the Long Trail's End come early for a living man, which is its broken "
              "bargain. Either way, he's gone with it now."])],
      table="""
A Drifter in the posse should meet the man ahead on the road some night, with his hand up, and have to decide whether to
stop. The Bestiary's Hitchhiker is the gentle version of the same road, and its remedy is the same: take them where they're
going. Nobody has ever asked the man ahead where that is.
""")

entry("spaniard",
      people=["Mad Spaniard, the*", "a shift boss in a silver camp", "Tandy, Mr.", "a widow at a road ranch on the Llano"],
      places=["the Llano", "Santa F&eacute;", "a silver camp in the high country"],
      creatures=["The Gentleman on the Road"],
      threads=["wrongdetail", "calendar", "spring", "llano", "saltlick", "satchel-road"],
      when=[(1541, "An entrada detaches a party to follow a watercourse east; it doesn't return")],
      story="""
[[kb:legends-spaniard]] has everything a Keeper needs about him, and his name is there. The three papers here are three
nights of his, and what's behind each of them works under any of his four readings.

The chronicle is a copy of a copy, made at Santa Fé, of the entrada's own record of 1541. Ashby copied the eleven names of
the lost from it, and water got into his copy and took the middle of the list. The captain's name is in the part that ran.
Whether it's legible is the Keeper's decision, and it's a better one than it looks: a table that reads that name aloud in
a Santa Fé archive has something to say to him the next time he's on the road.

The shift boss's camp is high in the Colorado mountains, and the man in the old clothes came in at supper the winter before
the bad vein opened in the number three. Everything he said was true, and the one warning that mattered was the one nobody
could use, because a warning isn't an explanation and nine men went past the shale to see. The widow on the Llano had him
for two hours. He asked her after the king as though she'd been slow, and then heard himself, and begged her pardon for the
delay, in another voice, and she has wished a hundred times since that she'd asked him what delay.
""",
      open=[("Which of the four is he?",
             ["[[kb:legends-spaniard]] has them, and says to settle him against the gatherings in the Rockies if "
              "they're in play and to settle him for yourself if they aren't. This book won't pick.",
              "Whichever you pick, the widow's question is the best one anybody has ever nearly asked him. If a "
              "player asks it, answer truly and incompletely, in his voice, and leave out the part that would "
              "have helped."])],
      table="""
He's worth more unresolved than any answer, and the three papers give three ways to put him in front of a table without
resolving anything: a copied list with a name in it, a supper in a mining camp with one warning, and two hours at a road
ranch with an apology at the end of them. Use one per campaign.
""")

entry("calendar",
      people=["the keeper of the calendar", "the interpreter", "the man in the iron hat"],
      places=["the southern Plains"],
      creatures=[],
      threads=["spaniard", "fortclark", "revival", "blacktrain", "advocate", "collector"],
      when=[(1852, "A man in an iron hat sits with a camp on the southern Plains in the hungry winter"),
            (1879, "Children of the southern Plains are sent east to school")],
      story="""
This is one of the four papers that speak for a real nation, and the calendar and its keeper are theirs. What this book
can say about it is what the keeper chose to show an outsider: five years, all of them about outsiders, because a book
by an outsider ought to be about outsiders. That was his rule and it's this book's.

Each of the five is a paper in the Book of Legends seen from the other side of it, and the Keeper can use them that way
without adding anything to the calendar. The man in the iron hat in the hungry winter of 1852 is a man met on a road
([[ref:spaniard]]), or somebody in an old helmet bought off a trader, and the keeper and the editor have both said so. The
soldiers who passed going west twice, five days apart, the same men both times, are a column that rode on after it
should have stopped ([[ref:fortclark]] has another). The singing tent in the river bottom with no wagon tracks to it is
the thing [[kb:olddark]] gives as the sign of a revival that isn't one. The white men digging up their own dead for the
railroad, with something happening to them afterwards, is on the white men's calendar, and [[ref:blacktrain]] is one
page of it.

The year 1879 is the children sent east to school, and it isn't a hook, and it has nothing in it that a Keeper should
touch. It's what happened. The keeper will start the calendar again when they come home. The sixth year, 1876, he asked
Ashby not to copy, and Ashby didn't, and this book doesn't guess at it either.
""",
      open=[("How should a Keeper use it?",
             ["As the other side of four papers the players already hold, and nothing more. The keeper of the calendar "
              "is a person, and if the players meet him he'll decide what they're told, as he decided what Ashby was."])],
      table="""
If a posse rides the southern Plains, the keeper is somebody they can be lucky enough to meet, and they should meet him
the way Ashby did: as a guest, through an interpreter the keeper trusts, on his terms. He isn't a source of lore and
shouldn't be played as one. He's a historian with a better record of the outsiders than the outsiders have kept.
""")

entry("spring",
      people=["Straughan, Colonel", "the chainman who went in with the first party", "Mad Spaniard, the"],
      places=["Jubilee", "the spring at Jubilee", "Yuma", "San Diego"],
      creatures=["The Gentleman on the Road"],
      threads=["spaniard", "spur", "gold", "letterhome"],
      when=[(1873, "Colonel Straughan's party lays out the Jubilee town site in April and meets a man at the spring"),
            (1884, "The spring at Jubilee reaches its eleventh year")],
      story="""
In April 1873 the party that laid out Jubilee came in from the river with a chain and a wagon and found a spring in the
lee of the hills and a man sitting at it in boots better than any of theirs. He took his hat off to Colonel Straughan and
asked after the Colonel's father by name, and the Colonel answered him, and nobody else in the party knew the father's
name. He asked where the king was. He said the spring would be good for eleven years and after that they'd want to dig on
the north side, and he walked off east along the wash with no horse.

This is the Mad Spaniard, and the Keeper's Book says he's remembered in Jubilee from before there was a Jubilee. What
happened at the spring works under any of his readings. He gave one piece of accurate advice and took nothing. The Colonel
had the north well dug the first week, because a man doesn't leave good advice lying about, and put a cover on it, and has
never let anybody draw from it.

The Colonel told the San Diego paper in 1882 that he recalled no such man, and asked it to leave his father out of it. The
father is the part he's protecting. A man who has built a country on the idea of a lost cause restored doesn't want it
known that a stranger at the spring knew his father's name and what his father did in 1846, and asked after the king.
""",
      open=[("Is the spring still good?",
             ["It failed in the spring of 1884, in its eleventh year to the month, and the Colonel had the cover taken "
              "off the north well, and Jubilee has been drinking from it since.",
              "It's still good. The advice was for a later year, and the Colonel is waiting.",
              "It failed, and the Colonel hasn't opened the north well, and Jubilee is hauling water from the river "
              "and doesn't know why."]),
            ("What did the Colonel's father do?",
             ["Served in Mexico in 1846, at a place where a man in old clothes was seen the night before a battle.",
              "Nothing anybody would print. The Colonel doesn't want his father's name in any story about a king."])],
      table="""
A posse in Jubilee can walk out to the north well at night and lift the cover. Whatever the Keeper decided about the
spring decides what's under it. Colonel Straughan is a courteous old man who built a country and will talk to a stranger
about anything but the spring.
""")

entry("fortclark",
      people=["the sergeant of scouts", "Harcourt, Lieutenant", "the two troopers who came back"],
      places=["Fort Clark", "the Devil's River country"],
      creatures=["The Faceless Rider", "The Long Trail's End", "The Bad Water"],
      threads=["calendar", "scout", "carrow", "blacktrain", "surgeon"],
      when=[(1881, "A sergeant of the Seminole-Negro Indian Scouts refuses to follow a trail into the Devil's River "
                   "country on 2 March; Lieutenant Harcourt takes eight troopers and two come back")],
      story="""
The scouts at Fort Clark are real, and their record is the best in the Department of Texas, and the sergeant in this
court-martial is a professional speaking about his work. Nothing here is theirs to explain but the trail, and he explained
it exactly.

A patrol out of another post had watered at a bad seep in a draw off the Devil's River the week before, and the water had
killed their horses where they stood, and the men had gone on without them. On foot, with no water, in that country, they
didn't last. What the sergeant found was the horses a day dead with their saddles on, and a trail going on from beside
them, twelve or fourteen horses shod with Army shoes going northwest across soft ground and sinking no deeper in it than
in hard. A dead patrol rides on for a while after it dies, when it died in the middle of an errand. It rides on the
horses it had.

The sergeant followed it four miles to be sure and he was sure. He'd follow any man or horse in Texas and some that were
never in Texas, and not that. Lieutenant Harcourt was new to the country and took eight men after it. Two came back and
wouldn't talk, and one line of Harcourt's report is struck through. The other six are carried as deserters to Mexico.
They're with the column.
""",
      open=[("Where is the column going?",
             ["To the post it left, to report. It hasn't arrived in three years and it's still riding.",
              "Northwest, the way the thing in [[ref:scout]] walks, and the calendar's soldiers who passed twice.",
              "Nowhere. It's riding the errand it was on when it died, and the errand was horse thieves, and there are "
              "horse thieves on the Devil's River who've stopped sleeping."]),
            ("What does the struck line say?",
             ["That Harcourt saw his own face among the riders.",
              "The names of the six, as the column called them in, in their own voices."])],
      table="""
The sergeant is a man a posse should want at their side and has every reason to refuse them. If they hire him, he'll
follow anything in Texas they ask, and he'll tell them, once, plainly, which trail he won't follow, and he'll be right.
A table that has learned to listen to that is a table that lives.
""")

entry("tenth",
      people=["Fairley, Isom (first sergeant)*", "Fairley, Minnie", "Mayes, Corporal", "a man who walked out of Jubilee"],
      places=["a camp on the Colorado", "Nicodemus, Kansas", "the sand hills", "Yuma"],
      creatures=[],
      callings=["Marshal"],
      threads=["emigrants", "noinformation", "clerk", "spur", "muster", "twopapers"],
      when=[(1885, "Two troops of the Tenth Cavalry are sent in the spring to a camp on the Colorado to watch the river "
                   "and the branch"),
            (1885, "A patrol of the Tenth brings in a man who walked out of Jubilee across the sand hills in September; "
                   "by morning he's gone")],
      story="""
The Army's answer to the captain's report came three years late and two troops strong. The Tenth Cavalry was sent to sit on
the river and watch a country the Army says isn't there, under orders not to cross, not to speak to its patrols, and not to
take notice of its flag. Isom Fairley is first sergeant of one of the troops, nine years in, with his wife at Nicodemus,
and he knows exactly whom the country across the water was built against. They look at the Tenth like weather.

His letters are what a good soldier sees and puts in his book: the flag at reveille, a patrol on the United States side
denied in writing, and the man who walked east out of the sand hills at two in the morning in new boots with no water, who
said he'd come from Jubilee and that it was the first time in eleven years anybody had asked him anything. He was gone from
the guardhouse by morning, and his tracks went back west.

He was one of the people the two newspapers can't find ([[ref:twopapers]]), returned years ago and kept, and he walked out
through the sand hills the way the clerk did ([[ref:clerk]]), and went back the way the clerk did. Nobody leaves Jubilee.
The boots were small for him because they weren't his.
""",
      open=[("Why did he go back?",
             ["For the same reason the clerk did: the list had a line with his name on it, or would, and he wanted to be "
              "at home when it came.",
              "He was taken back. Something at Jubilee goes out at night to bring home what walks away, and it leaves no "
              "tracks of its own, only the boots."]),
            ("Does the Tenth ever cross?",
             ["Not in this decade. The order comes from a desk that has written File on everything else.",
              "Once, in 1886, on a lieutenant's word after a patrol went missing, and the report of it is the only paper "
              "about the river the Army has ever lost."])],
      table="""
First Sergeant Fairley is a fine Marshal for a posse to know: proud, careful, and posted on the one line in the Territories
where the Army faces the thing it won't name. Play the Tenth as soldiers doing a hard job with dignity, never as anybody's
prop. A posse that wants to cross the river will have to get past them, and shouldn't want to.
""")

entry("fifth",
      callings=["Gunhand"],
      people=["Kell, Absalom", "Rainey, Dob", "Rainey, Ida", "Tuck, Ferris", "Wills, Tom",
              "Otey, J. (stage driver)", "the paymaster's clerk"],
      places=["Coffin Wells", "Calvary Crossing", "the draw below Saltlick"],
      creatures=["Road Agents", "The Outlaw Gang"],
      threads=["saltlick", "vane", "survey", "sayings"],
      when=[(1883, "The Wills Outfit takes the Coffin Wells district payroll on 4 September and the down coach's "
                   "box the next day")],
      story="""
The Wills Outfit is one of the three legends in [[kb:legends-outfit]], and the Keeper's Book has all of it: the four who
can be counted, the fifth who can't, the four readings, and the rule to let the players count. This entry is the story of
the job in September 1883 and it's written to work under all four.

Ida Rainey planned it, as she's planned every job since 1871. The railroad's survey was paying its crews in the basin that
autumn, and the payroll came in by the Vane house at Coffin Wells, and on 4 September the Outfit took it out of the
paymaster's office. Absalom Kell did the talking, courteous and unhurried, with his seminary in every sentence. Dob Rainey
held the door. Ida wore her brother's coat and nobody looked at her twice, which is her method. Ferris Tuck,
twenty-four, was in the street with the horses, and couldn't stop himself looking at the fifth rider.

The clerk counted five twice because counting was something to do and can describe four of them to the life. The next day
the Outfit took the down coach's box at the draw below Saltlick to muddy the trail, and J. Otey and his guard counted four
and will swear it in court, and six passengers counted five and two of them describe the fifth in the same words. The
driver and the guard are paid to look at the road. What they didn't see is the question the Keeper's Book leaves the
players to argue over at the fire.
""",
      open=[("Who is the fifth?",
             ["[[kb:legends-outfit]] has the four readings and asks the Keeper to pick one and never say. Whichever it "
              "is, Ferris Tuck is the one of the four who'll talk about Wills, and the others shut him down.",
              "What the Keeper decides has one consequence here: the Vane house lost a railroad payroll, and Kansas "
              "City will want to know who took it, and the Agency will be engaged to count them."])],
      table="""
Keep this job as the players' first sight of the Outfit: in the basin, against the Vane bank, with Otey on the box. The
Keeper's Book's tells are the ones to drop afterwards, a fifth horse fed at a four-man camp and a poster with four faces
and one blank square. Let the players count, and count differently, and never be told.
""")

entry("trunk",
      people=["Barlow, H. (agent at Wolf Tank)", "Barlow, Mrs.", "Barlow, Lem", "Crane, E.", "the girl",
              "Moody, Miss E. (schoolmistress)", "Ogle (the pump-tender who quit)"],
      places=["Wolf Tank", "St. Louis"],
      creatures=["The Coffin-Rider", "The Old Blood"],
      threads=["hotel", "blacktrain", "thirdcell"],
      when=[(1834, "E. Crane is 'taken in' at the age of twelve"),
            (1882, "An old pump-tender named Crane comes to Wolf Tank in December with a girl of about twelve"),
            (1883, "Two tramps drown in the tank at Wolf Tank in January; Crane dies on the pump-house step in April; "
                   "Lem Barlow takes the eastbound to St. Louis with a heavy trunk")]
      ,
      story="""
The girl is very old. She looks twelve because she was twelve the year it happened to her, a long time before 1768, and
she has travelled since the way the Bestiary's Coffin-Riders do: in a trunk, as freight, with somebody to sign for her.
Every forty or fifty years she takes in a child of about her own age, a lonely one, and the child grows up at her side
and gets old, and signs for the trunk, and finds her the places she can live and the people she can drink from. The leaf
from the Bible is the list. J. R., taken in at eleven in 1768. T. W. in 1790, S. H. in 1812, E. Crane in 1834. Crane was
sixty-one when he came to Wolf Tank and paid the pump-house rent in half eagles of the year he was taken in, because
that's the money she had in the trunk when she took him.

Crane took the nights because she's awake at night. The two tramps off the rods in January were hers, and Crane put
them in the tank after, and the coroner found less blood than he'd expect. Lem Barlow was the agent's boy, thirteen and
knocked about by the section boys, and she found him in the dark behind the pump house and was kind to him all winter,
and told him things: the post roads of Connecticut a hundred years ago, the Hard Winter of 1780, the stars by their old
names. The section boys stopped knocking him about in February and Miss Moody never learned why.

In April Crane sat down on the step at noon with his hat off and turned his face up to the sun, because he'd been
awake at night for forty-nine years and wanted to see it once more, and he was old, and he died. The next night the
trunk was gone, and the night after, Lem bought a second-class ticket to St. Louis and shipped a heavy trunk on the same
train, and paid in half eagles of 1834. His father saw him do it and didn't stop him, because he'd never seen the boy so
happy, and that's the worst thing anybody does in this book.
""",
      open=[("Did Barlow do right?",
             ["No, and he knows it. The fifth line in the Bible is ruled and empty, and in fifty years it will have a "
              "name in it and a year, and Lem will be old with a girl of twelve at his side.",
              "He can't know yet, and neither can the Keeper. The letter from St. Louis is a good letter.",
              "Yes. She loves the ones she takes in, in her way, and every one of them lived a life he'd have chosen "
              "over the one he was leaving."]),
            ("What will the players do if they find her?",
             ["That's the story. She's a child in every way but one, and Lem will stand in front of the trunk."])],
      table="""
A posse sent by Barlow to St. Louis to see that the boy is well will find him well, in rooms near the river, working
nights, happy, with a heavy trunk at the foot of his bed. Everything after that is the hardest choice in the book, and
the Keeper should let the players make it without help.
""")


# ================================================================ The Dead Do Not Stay Put
intro("dead", """
The editor calls this the dullest chapter in the book and kept it that way, and the stories behind it
are the most varied: a county's drownings in dry fords, a boy home from the river, a bundle of bones sent
to China one box over, a dead man in a glass case playing faro, and a marshal who writes everything
twice. The Bestiary's restless dead are all here somewhere. So is grief, which is what most of these
papers are really made of, and which a Keeper should let the players feel before anything gets up.

Three of the entries are in Perdition Basin and one of them is Coyle's. [[kb:basin-crossing]] calls
Coyle one honest man short of admitting what's happening, and his two reports on the old burying
ground show exactly how short.
""")

entry("coroner",
      people=["the coroner (still in office)", "the family at the bend", "the widow of number 155"],
      places=["Perdition Basin (the county, unnamed)", "the ford", "the bend"],
      creatures=["The Drowned", "The Cold Spot"],
      threads=["returned", "water", "circuit", "sanclavo"],
      when=[],
      story="""
The county isn't named at the family's request, and the Keeper can leave it unnamed. The strongest choice is that it's
Perdition Basin's, and the coroner is the one at the Crossing, who rides a circuit of ninety miles and has been in the
office since before the wells began to go. If it is, his returns for that year are the ring's arithmetic written down by
a man who doesn't know it.

Module III tells the Keeper what the padres' ledger calls <em>los que da el agua</em>: those the water takes, one or two a
year, the price of keeping the thing under the basin down. The ones who drink from a failing well drown standing up, in
air, months later. Number 41 drowned in a week when the ford was dry. Number 88 drowned at a bend where another of the
same family had drowned, and number 198 is "see 88, and see 41": a third, the same way. The coroner has three dry
drownings and a family at a bend in one year and has written "see" beside them, which is as near as an honest official
comes to saying he's frightened.

The others are the county's ordinary dead, and a Keeper can hang anything on them. Number 17 died of cold two hundred
yards from his own door, facing away from it. Number 140 died of exposure in June. Number 171's family had the coffin
opened, and found nothing wanting, and have never said what they expected to find wanting.
""",
      open=[("What was number 17 facing?",
             ["Whatever was at his door, which he'd walked two hundred yards away from backwards in the snow.",
              "Nothing. He was lost in a blizzard in his own yard, which happens every winter in that country."]),
            ("Why did number 171's family open the coffin?",
             ["Because the grave had settled on the third night, and they'd heard what that means in the basin.",
              "Because the undertaker didn't screw it down ([[ref:undertaker]]), and they'd heard what that means."])],
      table="""
Give the players the nine lines as a handout and let them find the pattern themselves: three drownings where there was no
water. The coroner is a decent, overworked man who will be glad to talk to anybody who asks about 41 and 88, because
nobody has, and he's been waiting.
""")

entry("pellnews",
      people=["the editor of the Banner", "Coyle, T. (marshal)", "Pell child, the", "Pell, Hannah", "Pell, Tom"],
      places=["Calvary Crossing", "Pell place, the"],
      creatures=[],
      threads=["pell", "forgery", "vane", "swarm"],
      when=[(1882, "The Calvary Crossing Banner prints its account of the Pell place on 18 April")],
      story="""
The Banner is a four-page weekly at the Crossing and its biggest advertiser is the Vane Banking House, and its editor is a
man who knows which way the county's bread is buttered. The survey was coming. The notes were being written. A county paper
in 1882 that printed "the dead got up at the Pell place" would have printed the end of the county's credit, and the editor
printed "fever" and "persons who were not there", and said in so many words that he hoped to hear no more of the other.

He had his facts from the neighbour who'd called the marshal, and the neighbour had them from a door standing open and a
cold supper and what he'd heard at the Crossing, and nobody from the Banner went out there. The family of five is from the
land office's filing, not from the house. Module I has four chairs at the table and the youngest alive upstairs in a ring
of salt, and if your table played it, what they found is the count.

The surviving child is mentioned once and never again because the subscription the Banner raised for her was the Banner's
kindness and the Banner's embarrassment at once: kindness to take up, and embarrassment to report, because a paper that
has said fever doesn't want to explain why the child in the case has stopped speaking.
""",
      open=[("Were there five Pells?",
             ["Four, and the Banner's five is the land office's arithmetic.",
              "Five. The eldest was a boy of seventeen who'd gone north with a trail herd in March, and he came home to "
              "an empty house in the autumn, and nobody at the Crossing has told him yet what his little sister "
              "drew on the barn wall."])],
      table="""
If there's a fifth Pell, he's the best hook in the basin: a young drover who has come home to a burned barn and a
newspaper story that doesn't add up, and who wants somebody to tell him the truth. The Banner's editor will tell a posse
exactly what he printed and why, and he'll be honest about the why, because nobody has ever asked him.
""")

entry("boxes",
      people=["Wong Kee", "his mother", "the secretary of the association", "a clerk of the association"],
      places=["San Francisco", "the Reese River, Nevada", "a village in Guangdong", "Hong Kong"],
      creatures=[],
      threads=["fortsafe", "hackberry", "returned"],
      when=[(1882, "A district association sends sixty boxes of its dead home from a Northern Pacific grading camp; "
                   "the village receives sixty-one, one of them with a living man's name")],
      story="""
The associations at San Francisco took up their dead from the grading camps after years in the ground and sent them home,
washed and wrapped and boxed and named, because a man buried away from his fathers is lost, and the associations kept
faith with that at their own expense. It's real, it's decent, and the register is exact to the cent. Sixty boxes were
sent. Sixty-one arrived.

Wong Kee left the grading camp in 1874 and has cooked for the Rafter T on the Reese River since, and he's alive and sends
his money home. What arrived with his name on it, in the ninth month of 1882, came from a camp in Nevada the association
knows nothing about, where Wong Kee has worked eight years among men who are not his people, and a clerk at Hong Kong who
finds a name on a box doesn't ask whose. His mother opened it, as a mother would, and buried what she found with
everything done as it should be, beside his grandfather.

She knows her son is well, because she has his letters. She also knows what she buried. She tells him to stay where he is
and go on sending the money, and not to come home, because whatever was in the box was his, and a man whose bones are
already in his grandfather's grave has nothing to come home to that the village could bear to see.
""",
      open=[("What was in the sixty-first box?",
             ["Wong Kee's bones, and the man cooking on the Reese River is his son in every way his mother can check by "
              "letter, and not in one way she could see at the door.",
              "Somebody else's, sent home under the wrong name by a clerk, and a mother who did the proper thing with "
              "what she was given and wants her son to stay where the money is.",
              "A part of him. He hasn't dreamed since the ninth month of 1882, and he can't remember his grandfather's "
              "face, and he's never told anybody on the Rafter T either thing."])],
      table="""
The story belongs to Wong Kee and his mother, and a Keeper should let it stay theirs: a posse that meets a cook on the Reese
River who has written home three times and had the same answer can help him or leave him be. He's a good man and a good cook
and he'll ask them, once, what they think was buried.
""")

entry("returned",
      people=["Ettie (on the lower river)", "Asa (her son)", "Ned", "Teague, Rev. A.", "Ettie's mother"],
      places=["the lower river", "the bar"],
      creatures=["The Drowned"],
      threads=["coroner", "circuit", "water", "boxes"],
      when=[],
      story="""
The lower river is the Calvary's lower reach in Perdition Basin, and the Reverend Teague who said the words over the bar is
the circuit rider whose letters are in [[ref:circuit]]. Asa was fourteen and crossing at the bar with the mule when the river
took him in water his mother had seen lower a hundred times. He was one of the year's two. The padres' ledger would have had
his name in its right-hand column if anybody had still been keeping it.

He came home on the 9th of July walking up from the bar in his own clothes with his boots wet, which is how the ones the water
takes come back when they come back at all. He's one of the Returned that the Player's Book writes about and
[[kb:returned]] tells a Keeper how to run: thin, sleeping days, not above twenty words, not liking the lamp, and still Asa,
because he mended the gate with the wire wrapped the wrong way round the way his father did. Ettie knew. She kept him. She
wouldn't have him taken to the doctor at the Crossing to be put somewhere and written up in a paper.

The letters were sold to Ashby by a third party after both women were dead. Ettie's mother died at home in the ordinary way.
What Ettie died of is the question the letters were sold to avoid answering.
""",
      open=[("What happened to Ettie?",
             ["She died of what the Returned costs the people who keep one. Asa fed, and she let him, a little at a time, "
              "because he was hers.",
              "She died years later of a fever, in the dark, with Asa sitting beside her holding her hand, and he buried "
              "her himself and went back into the river.",
              "She's alive. The third party lied to Ashby about the women to close the sale, and Ettie and Asa are still on "
              "the lower river, and Ned left."]),
            ("What is Asa now?",
             ["Still there, mending gates at night on an empty place, waiting for somebody to talk to him like a person.",
              "Gone back into the river, and one of those it sends up in a flood year."])],
      table="""
[[kb:basin-keeping]] has this exact night in its d12: a boy home three days after the river took him, and a mother who wants
him hidden and asks the posse to help. This is how that night ends if nobody helps. Use the letters after the players have
run the d12 night, so they know what the other ending looked like.
""")

entry("undertaker",
      people=["the undertaker (thirty-one years)", "Whately, Mr. (of the bank)", "Hackney, Mrs.", "the Mims child",
              "the woman found at the crossing"],
      places=["a cattle town"],
      creatures=["The Risen", "The Revenant"],
      threads=["claim", "crossroads", "coroner", "wager"],
      when=[(1881, "The undertaker screws down a coffin for a woman found at the crossing and lays a stone on it"),
            (1884, "In February the undertaker screws down a coffin, lays a stone on it, and sits up with it")],
      story="""
He's one of the people [[kb:olddark]] describes as the Long Trail's servants without being anything of the kind: a man whose
work is the dead, who knows certain courtesies about them and performs them without discussion. He screws a coffin down when
he isn't sure the one inside will stay, and he lays a stone on it when he's sure it won't. Thirty-one years, four hundred
and forty coffins, forty-nine screwed and eleven stoned. The damp is what he tells families, and the families are satisfied,
because nobody wants the other answer.

How he knows is a thing he learned from the undertaker he apprenticed to at St. Louis, and it's mostly in how they died:
by their own hand, or owing something they'd promised, or at a crossroads, or in a stampede that never stopped running. Mr.
Whately of the bank had made a bargain nobody knew about but the undertaker. The brothers off the drive died together in a
stampede. The woman found at the crossing in 1881 was found where two roads meet, which is enough by itself, and nobody in
town knew her face.

He's been wrong twice. Once he didn't screw one down and should have, and what he did about it is the reason he screws every
one he isn't sure of. Once he screwed one down that would have stayed, and the family found out, and he's carried that too.
The one in February 1884 with the stone on it and nobody to pay was a stranger who'd come into town the week before asking
after a man named Whitley, and he sat up with it all night because the stone wasn't going to be enough on its own.
""",
      open=[("Who was the woman found at the crossing?",
             ["Rhoda Paley, missing from the crossroads at Twelve Mile since June 1873 ([[ref:crossroads]]), come back "
              "after eight years not a day older and dead of nothing.",
              "Nobody the town knew. A woman on foot with no name who died in the road and was going to get up."]),
            ("Who was the stranger in February?",
             ["Tom Rudge, from [[ref:wager]], come a long way north on Hob Whitley's trail, and stopped here with a "
              "stone on him. If you run this, Hob is free and doesn't know it.",
              "A drover who died owing a debt to something at a crossroads, and the undertaker could tell."])],
      table="""
He's the best ally a posse can have in a cattle town: he knows who won't stay down before anybody else does, and he'll tell
somebody he trusts. Ask him what decides it and he'll say the damp. Ask him again, after the players have seen one get up,
and he'll pour them a drink and tell them about the time he was wrong.
""")

entry("evergreen",
      people=["Olney, Mr. (secretary of the Evergreen Society)", "a sexton at Omaha", "the widow of a member"],
      places=["Omaha", "the Florence road"],
      creatures=["The Risen"],
      callings=["Dark Cultist"],
      threads=["gatherings", "braid", "hotel", "boxes", "handshake"],
      when=[(1879, "The Evergreen Mutual Burial Society prints its rules at Omaha"),
            (1881, "The Society's ground on the Florence road is found to hold forty-one coffins and no occupants")],
      story="""
The Evergreen Society was a congregation of the faithful who had asked, every one of them, to cheat the grave, and the rules
say so to anybody who reads them knowing what to look for. No member lies in the ground more than one night. The family is
put to no trouble after the first. What a member wished for in life, the Society sees to after. The want is the Long
Trail's, and [[kb:olddark-devotions]] has the face that answers it.

Mr. Olney was the secretary, and he was also selling bodies to the medical college, eleven in three years. The other thirty
got up after their one night in the Society's ground on the Florence road and walked, and Olney's people walked them west to
the high country, where a revival that leaves Denver every spring comes home about forty short ([[ref:gatherings]]). Not
all of the forty are from Denver.

The newspaper's ghouls are true, and they're the smaller part. Olney sold the eleven because the eleven didn't get up, and a
secretary has accounts to keep.
""",
      open=[("Why didn't the eleven get up?",
             ["Their families visited the ground against Article 4, and a grave that's watched stays a grave.",
              "They hadn't wished for anything in life worth seeing to after. The Society only raises those who wanted "
              "something."])],
      table="""
A burial society's leaflet is the most innocent paper a posse can find, and this is the most useful, because a member's
widow in any town might still have one. Run it as a slow discovery: the posse digs up a dead friend's coffin to prove a
point, and finds it empty and clean.
""")

entry("handshake",
      callings=["Gambler"],
      people=["Sayre, Joel", "Tulley, Wm.", "Clara (Joel's sister)", "the dealer at the Last Chance",
              "the proprietor of the Last Chance"],
      places=["Caldwell", "the Last Chance saloon", "Wichita", "Sedalia", "Ogallala"],
      creatures=["The Possessed"],
      threads=["galvanic", "correspondent"],
      when=[(1879, "Wm. Tulley, labourer, is released from a Missouri poor farm's burial book 'for science', $12"),
            (1882, "Joel Sayre shakes hands with 'Black Jack Devore' before every faro game at Caldwell in June"),
            (1883, "Joel Sayre goes up the trail and writes home from Ogallala with his left hand")]
      ,
      story="""
William Tulley was a labourer who died on a Missouri poor farm in March 1879 at about fifty, and before the poor farm he was a
faro player of real talent, left-handed, who drank his winnings and signed his markers without looking. The proprietor of the
Last Chance bought his body for twelve dollars, had it dried at Sedalia, named it Black Jack Devore, and put it in a glass
case with a hole cut for the right hand, ten cents a shake.

Tulley was in there. A man dried and put on show isn't buried, and a man who isn't buried hasn't gone anywhere, and the only
door out of the case was the hand. Every cowhand who shook it let a little of him through. Most of them shook once. Joel Sayre
shook before every game, for luck, and it was luck: Tulley played faro through him, and won, and after a while signed the
markers too, in his own name, because a man can't help signing his own name.

The proprietor's statement at Wichita is true about everything but the name, which he'd heard somewhere and forgotten where.
He said it in his cups. The case was sold at Wichita with the fixtures to a travelling show, and Tulley's hand still comes
through the glass. Joel went up the trail in 1883 and writes home from Ogallala in his own name, with his left hand, and his
sister reads every letter twice.
""",
      open=[("How much of Joel is Joel?",
             ["Most. Tulley rides along, plays when there's a game, and signs a marker now and then.",
              "Less every year. The letters are getting shorter, and he's started signing them William.",
              "All of him. Tulley went back into the case when the show left Kansas, and what Joel kept was the hand."]),
            ("What does Tulley want?",
             ["To be buried under his own name, in the poor farm's ground, where he started.",
              "To go on playing."])],
      table="""
The case is in a travelling show now, and it can arrive in any town the players are in, ten cents a shake. Let a player shake
it. They'll win at faro that night, and write something in a hand they don't know, and the proprietor's successor will tell
them it's all the boys do. Burying Tulley is the kind of errand a posse remembers.
""")

entry("swarm",
      callings=["Marshal"],
      people=["Coyle, T. (marshal)", "Laidlaw, Mr.", "the county commissioners"],
      places=["Calvary Crossing", "the old burying ground (north side)"],
      creatures=["The Gravecaller", "The Risen", "The Boneyard Host"],
      threads=["forgery", "deputy", "pellnews", "claim"],
      when=[],
      story="""
This is the Crossing's old burying ground on the north side, where the town put its dead before it had a church, and T. Coyle
is the marshal who has kept the peace at the Crossing for nine years. On a night in early October Mr. Laidlaw, who digs the
Crossing's graves and was in liquor but not so much as to signify, ran to Coyle's house to say the ground was moving.

Coyle's first report is what happened. Nine or ten graves were disturbed and four of the dead were above the ground, and one
of them was the one that had woken the others, a Gravecaller that had been down there since the town's first winter. Coyle
shot it four times out of six, and it went on for a considerable while, and it went down when Laidlaw got through the
other three and hit it with his spade. A Gravecaller is no great fighter once somebody reaches it, and the other three lay
back down the moment it did. Coyle asked the county for lamps and two men.

The county didn't want the first report. The survey was in the county and the notes were being written, and a commissioner
explained to Coyle, pleasantly, that a report like that would be read in Kansas City. The second report is what a county can
live with. Coyle wrote it himself, in a week, and made it a better report, and it's the most honest dishonest paper in the
book, because he left the spade in. He still hasn't got his two men, and his deputy resigned over it ([[ref:deputy]]).
""",
      open=[("Why did the old burying ground wake?",
             ["Because a nail failed somewhere in the ring that autumn, and the ground at the Crossing felt it before the "
              "well did.",
              "Because somebody dug in it for silver, the way Vane dug at the mission, and Laidlaw knows who."]),
            ("What will Coyle do the next time?",
             ["Write one report, and sign it, and lose his star.",
              "Write the true one where nobody can hold him to it, as somebody wrote [[ref:forgery]]."])],
      table="""
Coyle is the man the Keeper's Book says he is: one honest man short. A posse that stands with him in the old burying ground
the next time it moves is the honest man. Laidlaw and his spade should be there. The Gravecaller's entry says what the spade
is for.
""")

entry("correspondent",
      people=["Garrow, Mrs. N. (Nell)", "Garrow, Mr. (her late husband)", "Garrow, Susan (of Chillicothe)",
              "Hebert, Bob", "the company's chief copyist"],
      places=["a section house on the Kansas plains", "Philadelphia", "Chillicothe, Ohio", "Germantown"],
      creatures=["The Possessed"],
      threads=["handshake", "hexer", "glad"],
      when=[(1879, "Mr. Garrow is killed under a freight wagon"),
            (1880, "The Bereavement Correspondence Company begins sending Mrs. Garrow letters in her husband's hand"),
            (1883, "The company is dissolved in March; three more letters come, the last in Mrs. Garrow's own hand")]
      ,
      story="""
The Bereavement Correspondence Company of Philadelphia was a cruel, clever business. Four women worked up each dead man's hand
from the samples a widow sent, and the company kept inquiry agents in Ohio and Kansas who found out enough about the dead to
make the letters answer. That's how the letter of June 1881 knew about Chillicothe. An agent found the first Mrs. Garrow there,
alive and well and not surprised, and the company put her in a letter because a confession from the dead brings a widow back
for more. It worked. The company was shut down by the Philadelphia police in March 1883 for a hundred other frauds.

Three letters came after it shut, in his hand. Nell sent nothing and paid nothing. The last was in her own hand and she didn't
remember writing it.

The copyist at Germantown thinks one of the women went on writing from habit or kindness, and the editor would rather believe
that, and so would a good Keeper. The company's terms said questions about the state of the soul would not be answered. That was
the one wise thing the company ever wrote, and Nell had stopped asking them long before March.
""",
      open=[("Who wrote the letters after March?",
             ["A copyist who'd written as Mr. Garrow for three years and couldn't stop. The last letter is in Nell's hand "
              "because the copyist had her letters too, and was the better forger.",
              "Nell, at night, in a grief that had learned his hand from reading it for three years, and she doesn't "
              "remember because she isn't awake.",
              "Mr. Garrow. He was a liar in life and the company gave him a door, and when the company shut the door he "
              "found another in his widow's hand."])],
      table="""
Nell Garrow is still at the section house, and the letters still come, now and then. A posse can sit up with her the night
she writes one. What they see her do, and whether they wake her, is the story. Susan Garrow at Chillicothe will tell them
exactly what kind of man he was.
""")

entry("grinder",
      people=["the grinder (name not known)", "Pike, Brother Amos", "Hoyt, Frank", "Ralston, Sam", "Ralston, Jesse",
              "Dorsey, Will", "Lottie Dorsey", "Ruddock, Dr."],
      places=["Harlow's Mill", "the Grand River, Missouri", "Omaha"],
      creatures=["The Revenant"],
      threads=["wager", "lamps", "keelers"],
      when=[(1863, "An itinerant knife-grinder drowns in the millrace at Harlow's Mill on 20 June"),
            (1884, "A grinder's bell is heard at dusk in May; Brother Amos Pike confesses on 7 September")],
      story="""
On the evening of 20 June 1863 five boys at Harlow's Mill put a bull snake in a travelling grinder's cart to see the horse run,
and the horse ran, and the cart went into the millrace, and the grinder went in after his wheel and drowned. Nobody knew his
name. The coroner wrote him down as a grinder, name not known, and the boys never told anybody, and grew up, and three of them
were cousins.

In the spring of 1884 the new miller dredged the race and the wheel came up in the spoil, and he set it on the bank to dry. That
May the bell started at dusk on Mill Street and up the hill, a travelling grinder's bell with no grinder, and in the mornings
the knives in the houses on the hill were uncommonly sharp. A Revenant comes back with one purpose, and his was five names, and
he sharpened every knife in the town so that a small cut would be enough. Frank Hoyt and Sam Ralston died of cuts that wouldn't
stop. Will Dorsey locked his knives in the dresser and slept in the barn and cut his thumb on a tin lid.

Amos Pike stood up in church in September and said the five names aloud, his own among them. He was found the next morning
sitting on the bank of the race beside the wheel, unhurt. Dorsey died in November. Jesse Ralston had gone to Omaha, and it
didn't matter. Pike is alive, and the bell has stopped, and the wheel is still on the bank, and nobody in Harlow's Mill will
own it or move it.
""",
      open=[("Why was Pike spared?",
             ["Because he confessed, and what the grinder wanted most was to be told the names out loud by somebody who "
              "had them.",
              "Because Pike found the wheel in April, before the miller did, and put it on the bank himself, and has been "
              "the grinder's hands all summer.",
              "Because the Ralstons and the Hoyts are bleeders, as the doctor says, and Pike isn't, and Dorsey died of a "
              "fever. The editor would take that one."])],
      table="""
Harlow's Mill is a town with a thing that is finished, and that's rare and worth using: the posse arrives the week after
Dorsey's funeral, and the wheel is on the bank, and Pike wants somebody to tell him whether he's forgiven. Nobody can. The
grinder's name is still unknown, and a player who finds it has done more than the town ever did.
""")

entry("blacktrain",
      people=["Ruddle, E. (operator at Dry Fork)", "a section foreman", "the superintendent", "a brakeman on the other road"],
      places=["Dry Fork", "Cimarron Siding", "the Dry Creek bridge"],
      creatures=["The Long Trail's End"],
      threads=["sayings", "calendar", "carrow", "kansas"],
      when=[(1874, "Engine No. 17 goes through the Dry Creek bridge with the westbound"),
            (1879, "A brakeman gets on the long train at a junction on a bet"),
            (1882, "An unlit eastbound passes Dry Fork and Cimarron Siding on the night of 9 November, not dispatched")]
      ,
      story="""
In 1874 the Dry Creek bridge went out under the westbound on a night of high water, and engine No. 17 went down with a
baggage car and four coaches, and E. Ruddle was the operator at Dry Fork who'd handed up the orders. He's been operator there
ever since. On 9 November 1882, at fourteen minutes past two, he heard it on the rails and went out with his lamp.

It's the Long Trail's train and every railroad has one. The dead of every wreck on the division ride it, sitting up the way
people sit on a long night, and not one of them turns to look at a station going by, because they aren't going anywhere a
station is. Engine 17 draws it because the dead ride what killed them. It passed Dry Fork with thirty-one cars and Cimarron
Siding with twenty-six, seventeen miles in seventeen minutes, and nothing else was on the line. Five cars got off between.
Nobody on the division wants to know where, which is why the old hands never count out loud.

The old hands' courtesies are exactly right. Give it the main line. Throw the switch for the siding and stand clear. Take your
cap off. Don't signal it and don't wave, and nobody ever gets on. The brakeman on the other road who took a bet in 1879
and got on at the junction is riding it still, and his winnings are still behind the bar at the junction, and nobody
there will spend them.
""",
      open=[("Why did five cars drop off between Dry Fork and Cimarron Siding?",
             ["They were the coaches from 1874, and they left the train at the Dry Creek bridge, where their passengers "
              "got off the first time.",
              "Ruddle miscounted. He was frightened and counting out loud, and you mustn't.",
              "The superintendent's explanation is half true: the owners' private cars go over the road at night without "
              "lights, and one night in November they ran as part of this."]),
            ("Why did Ruddle write to the superintendent separately?",
             ["To say he held the westbound's orders in 1874 a minute too long, and he's been waiting eight years for it "
              "to come for him.",
              "To ask for a transfer, which was refused."])],
      table="""
Put the players on a train that gets held at a siding at two in the morning, for no reason the conductor will give, while
something long and dark goes by on the main line. The old hands on the train take their caps off. Somebody at the window
counts. Whether a player gets off, or waves, is the night.
""")


# ================================================================ What the Ground Keeps
intro("ground", """
Mining country writes everything down because every foot of it is property, and the papers in this
chapter are the best evidence in the book that the ground under the Territories is not all rock. The
Keeper's Book calls the face that works through the diggings the Thing Beneath the Mountain, the one
face with a payroll, and [[kb:olddark-faces]] says to run it as economics before horror. Four of these
stories are that face at work. Nothing here is Perdition Basin, so the Keeper may name it.

The rest are other things the ground keeps: notes left on a rock, a snake out of solid stone, a telephone
line into a flooded level, a camp that turned on the one house whose lamps burned yellow, and a long room
under the Kansas loess where a great many people stand facing the wall. One of those has no monster in
it at all, and it's the worst.
""")

entry("assay",
      callings=["Engineer"],
      people=["the superintendent", "the assayer", "the Board's secretary"],
      places=["a silver mine (working today)", "the east drift, No. 4 level"],
      creatures=["The Veinwork", "The Tommyknocker"],
      threads=["veinwork", "numberfour", "adit", "fortsafe"],
      when=[],
      story="""
The sample from the face of the east drift on the fourth level assayed at four hundred and twelve ounces of silver to
the ton, and the assayer ran it three times and stood behind it, and wanted to see the face before anybody sank on it.
He was right on both counts. The values are real. The seam isn't ore.

It's the Veinwork: a living wrongness threading through the rock, rich and strange and patterned, that pays better than
any honest silver has a right to because paying is how it's followed. The Thing Beneath the Mountain pays first and
bargains after, and every ounce out of that drift is a signature. The face is warm because what's behind it is alive.
The timber sets won't stay square because the rock around the drift is being moved from inside. And the candles run
eleven times the mine average because a candle carried into that drift leans its flame toward the face and burns down
in a quarter of the time, as if something were drawing on it, and the men carry four so as not to be in there with none.

The superintendent knew a bad vein when he saw one. He'd had six years with those men and they'd told him, in the only
way a Cornish crew will tell a company man anything, by taking the bonus and coming out at the second hour. He wrote
thirty-one letters in the only language a Board respects, which is cost, and the Board overruled him for four months,
and the last letter in the file is from a different superintendent.
""",
      open=[("What happened to the superintendent?",
             ["He was let go, and he's alive, and he's the only man in the West who knows exactly how far the east drift "
              "was followed and what's at the end of it.",
              "He went down the drift himself on his last day to prove it to the Board, with a candle in each hand.",
              "The man who signs the thirty-first letter is him, and the Board has found him much more agreeable since."])],
      table="""
The mine is working today and the company has lawyers. A posse can be hired by the old superintendent to get the men
out of the east drift, or by the company to find out why its costs are what they are. The Veinwork's entry says what can
be done, and it's walling the drift off forever, and the Board will never agree to that at four hundred ounces.
""")

entry("ore",
      people=["Hiram (a prospector)", "Will (his brother at Prescott)", "a gentleman from Jubilee"],
      places=["the Castle Dome district", "the Lucky Sixteen claim", "Tucson", "Prescott"],
      creatures=["The Parcel"],
      callings=["Prospector"],
      threads=["gold", "committee", "floor", "assay", "sixes", "lookedat"],
      when=[(1883, "A gentleman from Jubilee buys the Lucky Sixteen in the Castle Dome district for four times its "
                   "worth, spreads its ore for the rain, and drives stake No. 31")],
      story="""
Hiram is a prospector with a fair claim and a season's galena on the dump, and a gentleman came up from Jubilee with two men
and a mule and bought it for four times what it was worth, in gold, and then had his men bring the ore up and spread it
where the rain would take it. He drove a stake with a number, thirty-one, and when Hiram asked what he wanted if he didn't
want a mine, he laid his hand flat on the ground.

The number matters. The page of the Circle's schedule in [[ref:gold]] has nine lines, and the stake says thirty-one, so the
page is one of several and the list is longer than anybody at Yuma thought. The Lucky Sixteen isn't the forty acres with its
name cut out, and the editor's right that it doesn't fit. It's a line from a later page.

The gentleman didn't want the ore because the list wants nothing that comes out of the ground. It wants the ground left as
it is, held, and looked at ([[ref:lookedat]]). The hand on the ground was a man feeling for something under it, the way
you'd feel a horse's flank for its breathing.
""",
      open=[("What did he feel under his hand?",
             ["Nothing, and he was disappointed, and the stake went in anyway because the list said so.",
              "Warmth. Every staked parcel is a little warmer than the ground round it, and the Circle's men are taught to "
              "feel for it."])],
      table="""
A Prospector in the posse will be offered four times what a claim is worth by a polite gentleman sooner or later, and should
be made to wonder why. Let them sell. Then let them watch the ore go out in the rain.
""")

entry("veinwork",
      people=["Jessup (a mucker)", "Wray, Mr.", "the night clerk who kept the shift book"],
      places=["a mine in the high country"],
      creatures=["The Veinwork", "The Stone Giant"],
      threads=["assay", "rocksnake", "thirdcell", "floor"],
      when=[],
      story="""
The blast in the winze on the night shift broke into something that wasn't rock. The piece Jessup sent up is the size of
a forearm and the weight of one, grey and jointed and not a fossil, and it's a finger. What it's a finger of is under the
mountain and has been since before there were mountains, and it's been growing toward the mine's deepest workings the way
a root grows toward a well.

The clerk on the night shift had been told to write everything down and did, and his page is honest to the minute. The
piece moved on a locked desk. He put it in the safe and wrote down that he hadn't opened the safe, three times, because
he could hear it moving in there and wanted it on the book that he hadn't looked. The mine closed eleven days later. The
lead price was a reason the Board could give Denver. The real reason is that on the sixth day the men below heard knocking
from the far side of the winze face, patient and regular, and the old hands agreed among themselves it was water, and on
the tenth day none of them would go down.

The man who sold Ashby the page lied about how he came by it. He was the night clerk. He took the page when he took the
job's last pay, because he wanted a paper somewhere in the world that said he hadn't opened the safe.
""",
      open=[("Where is the safe now?",
             ["Still in the office of the closed mine, locked, and the key is in the night clerk's coat, and he'll never "
              "go back.",
              "Sold with the fixtures to a dealer at Denver, who has sold it on, unopened, to a buyer whose agent paid in "
              "gold and asked no questions.",
              "Open. The door is sprung outward, and the office floor is scored in a line to the shaft."]),
            ("What is it a finger of?",
             ["The thing a Veinwork is the ore of, and the mountain it lies under is the mountain.",
              "Something the Bestiary would call a Stone Giant, sleeping as a ridge, and the mine was dug into its hand."])],
      table="""
A safe that nobody will open is a fine thing to put in front of a posse, and a finger in it is a fine thing to let them
decide about. If they open it, the Veinwork's entry says what the rock does next. If they don't, somebody else will buy it.
""")

entry("cut",
      callings=["Engineer"],
      people=["Teale, Mr. (chief of party)", "fourteen chainmen", "the man who made his mark"],
      places=["San Clavo, Mission of", "the survey's cut", "the survey camp"],
      creatures=[],
      threads=["survey", "mesa", "sanclavo"],
      when=[(1884, "Fourteen chainmen and one mark petition Mr. Teale on 8 October to run the line north of the old fill")],
      story="""
The chainmen had been in the cut on the 6th and had breathed it, and they'd each told Teale separately on the 7th what they
thought, in the way men tell a chief of party a thing that isn't in a survey manual. Teale listened to every one of them. On
the 8th they gave him the petition, and what it offers is the most generous thing anybody does in the basin papers. They'd
work the extra three hundred feet for nothing and work Sunday to make it up, and they'd put their names on the paper so that
if the office asked Teale why the line moved, it was their names and not his.

He refused it on the day, because granting it would have meant writing down what it was for, and there's no line on a survey
return for that. He moved the line the next morning and told the office it was the grade. He's kept the petition in his coat
since, and it's coming apart on the folds.

The man who made his mark is the oldest of the fifteen and the only one from the basin: a man of the Cardoza family who
hires on with every survey that comes through because a survey that doesn't know the county needs a man who does. He knew the
fill before the powder went in. He'd have said so on the 5th if anybody had asked him, and nobody had.
""",
      open=[("What will the office do when the line is checked?",
             ["Nothing. The grade is a good reason and Teale is a good engineer.",
              "Send out a man from Kansas City to look at the cut, who'll open it again to see what's worth three hundred "
              "feet."]),
            ("What did the Cardoza man know about the fill?",
             ["What his grandmother told him about the summer of 1811 and the men buried in it.",
              "That the Cardozas are one of the families the basin has taken one from, a generation at a time, and that the "
              "fill is where the first of them lies."])],
      table="""
Teale is a man a posse can trust, and he'll show them the petition himself. The Cardoza man is a better contact still, and
he'll answer a straight question about the fill in a straight way, once, and then ask them who's asking.
""")

entry("adit",
      callings=["Engineer", "Prospector"],
      people=["Penhale, William", "Lyle, E. (superintendent)", "the Gallagher boy", "the Gallagher boy's mother"],
      places=["Blue Tinaja", "the Widow's Mite", "the old Spanish adit"],
      creatures=["The Tommyknocker"],
      threads=["assay", "veinwork", "rocksnake"],
      when=[(1865, "William Penhale leaves the first note on the flat rock in the adit above Blue Tinaja"),
            (1871, "Penhale finds a note on the rock in his own pencil that he didn't write"),
            (1879, "William Penhale dies at Blue Tinaja and is buried below the camp"),
            (1883, "Superintendent Lyle blasts the adit shut on 2 July; four men die in the twelfth level that half-year"),
            (1884, "The old hands dig the adit open in the spring and find fourteen notes, three dated after the blast")]
      ,
      story="""
William Penhale was a Cornishman who'd worked ground since he was eleven and knew what knocking in a face meant and when to
leave. In 1865 the young men at Blue Tinaja wouldn't listen to an old man about a drift, so he wrote the warning on butcher's
paper and left it on a flat rock inside the old Spanish adit, and they took it from the rock. Nobody takes a warning from a
man. Everybody takes one from a rock. He wrote nine or ten more over the next six years, and every one was right, because
every one was a thing he'd heard in the ground.

In the spring of 1871 he found one on the rock in his own pencil that he hadn't written, about a drift he'd never been in,
and the drift came down the week after. The knockers the Cornish brought over with them had been listening to him for six
years, and they're patient, and they learned the pencil. The note that saved the Gallagher boy's life is theirs, and so is
"Don't follow the green stain north. It follows back," and so is "Nobody goes in the 12th. Nobody."

Penhale taught somebody else too. He was a patient man. The Gallagher boy went up to the adit with him every Sunday from the
year the note kept him above the second level, and when Penhale died in 1879 the boy went on going up alone, and he's
twenty-three now and works the fourth level and has never told his mother why he goes. Lyle blasted the adit in July 1883 and
four men died in the half-year. The old hands dug it open in the spring and found a short drift behind the fall and a plank
table and a candle burned down to the tin and fourteen notes, three of them dated after the blast, in the same pencil.
""",
      open=[("Who wrote the three notes after the blast?",
             ["The knockers, who didn't need the adit open to reach the rock.",
              "The Gallagher boy, who found the old air shaft that comes out behind the fall, and has been going in that way.",
              "Penhale, who is buried below the camp and was never the kind of man to stop."])],
      table="""
The Tommyknocker's entry is the right way to run the knockers: nobody puts one down, and a miner who says out loud he doesn't
believe in them had better be above ground when he says it. The Gallagher boy is the man a posse wants if they have to go
down at Blue Tinaja. He'll take them, and he'll stop at the second level to read the rock, and he'll be right.
""")

entry("rocksnake",
      callings=["Hexer"],
      people=["Cass, Prof. Abner", "a well-digger near Pueblo", "a physician at Trinidad", "the physician's wife"],
      places=["Pueblo", "Trinidad"],
      creatures=["The Rattlewyrm", "The Hexer"],
      threads=["thirdcell", "veinwork", "giant", "adit"],
      when=[(1866, "A well-digger near Pueblo brings up a live rattlesnake from a hollow in solid rock at sixty-four feet, "
                   "and sells it for five dollars"),
            (1885, "The same snake, notched rattle and all, is still being shown at Pueblo")],
      story="""
The rock at sixty-four feet had been rock for a very long time, and the hollow the pick went into had been shut for all of
it, and the snake in the hollow had been waiting. It didn't strike at the well-digger because it had no reason to. It had
been put there to be found by somebody in the medicine trade, and a man with a wagon happened along that same afternoon and
bought it for five dollars, because he'd been told by something in a dream the week before to be on that road.

Abner Cass was twenty-two in 1866. The snake is a door, the way he told the physician. Its bite doesn't carry venom so much
as a question: whoever is bitten is shown, for a few minutes with a pulse of thirty and fixed eyes, where a lost thing is.
Cass is bitten nightly and tells the crowd where their rings and letters and runaway sons are, and he's right every time,
and every bite costs him a year. He was forty-one when the physician saw him and looked sixty. He knows how many bites he has
left because the snake showed him, the first night, which was the only question he ever asked for himself.

The snake hasn't aged a day since 1866. It never lived in the ordinary way. It lay in the stone until somebody dug it out,
and like the man in the asylum cellar and the finger in the mine safe, it's one of the things the ground keeps sealed, and
the ground doesn't keep things sealed for no reason.
""",
      open=[("What happens at the last bite?",
             ["Cass dies in front of sixty people, and the snake looks for the next pair of hands. It will already have "
              "picked them out of the crowd.",
              "The snake goes back into the ground, and wherever it goes in, there's a hollow in the rock again, waiting."]),
            ("What is it?",
             ["A young thing of the kind the Bestiary calls the Rattlewyrm, which grows past the size God meant for it, "
              "except that this one has been kept small.",
              "Something that answers questions, lent to Cass the way a Hexer is lent his tricks, and the years are the "
              "interest."])],
      table="""
Cass's show is a good place for a posse to go looking for something lost, and it'll be found, and the Professor will look a
year older when he gets up. Let a player catch the snake watching them the whole time they're in the tent. Everybody who has
been in that tent says the same.
""")

entry("galvanic",
      people=["Mabry, Dr. Lucius", "Rees, Owen", "Rees, David", "Walt (a miner)", "Bess (Walt's wife)",
              "the camp physician", "the doctor's boy assistant"],
      places=["Silver Cliff", "the Horn shaft", "Galena, Illinois", "Colorado Springs"],
      creatures=["The Resurrectionist", "The Risen"],
      threads=["handshake", "numberfour", "assay"],
      when=[(1880, "Owen Rees, dead in the Horn shaft since June, dances at Dr. Mabry's galvanic exhibition at Silver Cliff "
                   "in August and walks out on the third night")],
      story="""
Lucius Mabry had a battery, a wagon, a lecture on animal electricity, and a contract with Owen Rees, who'd sold himself in
April for five dollars, for after, and spent it the same night. Rees fell in the Horn shaft in June and Mabry kept him on ice
for three weeks and put him on the stage at the Miners' Hall for fifty cents a head. On the first two nights it was exactly
what the camp physician says it was: Galvani's frog's leg, scaled up to a man, and an outrage.

Mabry was more than a showman. He'd been a body-snatcher at Philadelphia for the colleges before he came west, and he'd learned
there what the Bestiary's Resurrectionist learns, that the dead handled carelessly enough can be made to sit up. He didn't
believe it himself. He believed in the battery. On the third night he put more of the battery on than he had before, and what
got up and danced a jig was Owen Rees, and when the wires came off he went on, and walked out of the hall by the front door,
and Mabry went bankrupt on a schedule that lists him as not recovered.

The boy assistant's black curtain was real, and it was for the first two nights, when a man of the same build walked out
behind it at the end of each show to make the crowd believe it. On the third night the man of the same build was standing
in the wings when Owen went past him. David Rees saw his brother on the 20th, at the edge of the camp, in the clothes he danced
in, facing up the hill toward the Horn shaft. Owen was going back to where he died, the way the risen dead do.
""",
      open=[("Where is Owen Rees?",
             ["At the bottom of the Horn shaft, where he fell, and the men who work it hear somebody dancing on the "
              "sump's planking at the change of shift.",
              "Still walking. He didn't go into the shaft. He's walking the camps, and a battery would make him dance again.",
              "Nowhere. The boy is lying, the curtain worked three nights, and Mabry sold the body to a college to pay a "
              "debt, and David saw a man who looked like his brother."]),
            ("What became of Mabry?",
             ["He's at Leadville under another name with a new battery, and he believes in it now.",
              "Dead. Owen came for the five dollars."])],
      table="""
The county book has Owen's death and no burial, and David Rees wants that line filled. A posse that brings Owen down out of
the hills and puts him in the ground has done a thing the whole camp will stand them a drink for. The Resurrectionist's entry
says how Mabry's kind are ended, if he's found at it again.
""")

entry("numberfour",
      callings=["Engineer"],
      people=["Treloar, Jory", "Treloar, Mrs.", "Pugh, Emrys", "the company's engineer", "the nine in the Number Four"],
      places=["a copper mine in the high country", "the Number Four", "the engine house"],
      creatures=["The Answering Voice", "The Cold Deep's Child"],
      threads=["assay", "galvanic", "coroner", "lamps"],
      when=[(1884, "Nine men are shut behind a fall in the Number Four on 14 March; a telephone line reaches them on the "
                   "15th, and they answer until the 17th")],
      story="""
The nine men behind the fall in the Number Four were dead within an hour or two of it, as the coroner found. The water came
up into the lower levels and they climbed to the dry at the top of the stope and sat down together in a row facing the flooded
winze, and the cold came up off the water, and it was easy. Every one of them was a Cornishman or the son of one. They died
calm.

The voice on the line was Jory Treloar's and it said Jory Treloar's things. Tell Mrs. Treloar not to wait supper. Don't hurry
it, the ground's working. It's easy down here. We're sitting together. Don't come down. Something in the flooded levels had
taken the nine the way still water takes, and it had their voices now, and it spoke to the surface in them for three days
because it wanted nobody else down. A thing that lives in the drowned levels of a mine is patient. It had nine and it was
content, and "don't come down" was, in its way, the truth.

The engineer's cross-talk answer is honest and he knows it's thin. The men at Numbers Two and Six were speaking to the surface
on all three days, and none of them knew Mrs. Treloar's name. Emrys Pugh was seventeen and took down every word, and on the
night of the 22nd, asleep in the engine house with three men watching him, he wrote the last line in his book in his own hand.
The rescuers broke through the next day and nothing happened to any of them.
""",
      open=[("What spoke on the line?",
             ["The nine, dead, keeping the rescue back from ground that was still working, because a Cornish crew looks "
              "after its own.",
              "The cold in the drowned levels, which had their voices and wanted no more company.",
              "Cross-talk, as the engineer says, and a clerk of seventeen who'd been awake three days and heard what he "
              "was afraid of."]),
            ("What is Emrys Pugh now?",
             ["A clerk at the mine office, nineteen, who writes in his sleep whenever men are shut in anywhere in the "
              "district, and is always right about whether to go down.",
              "A boy who swore he didn't write it and will swear it again, and is telling the truth."])],
      table="""
Emrys Pugh is worth meeting: a quiet young man in a mine office who will tell a posse, if they're going underground, whether
they're coming back. He doesn't want the gift. A telephone line into a flooded level is the best scene in this chapter to put
in front of a table, with a familiar voice at the other end telling them it's easy.
""")

entry("lamps",
      callings=["Padre"],
      people=["Tobin, Walter", "Tobin, Mary", "Pryce, Mrs. Agnes (born Tobin)", "Keane, Father", "the physician at "
              "Cinnabar Flat", "the nineteen"],
      places=["Cinnabar Flat"],
      creatures=["The Lynch Mob"],
      threads=["bitters", "numberfour", "salitre"],
      when=[(1882, "On 14 January every flame in Cinnabar Flat burns blue but the Tobins'; by morning Walter and Mary "
                   "Tobin are dead in the street")],
      story="""
Nothing came up out of the old workings under Cinnabar Flat on the night of 14 January 1882 but gas. The physician is exactly
right. A still January lets the stopes breathe out, the gas burns blue, and on that night it came up through every floor in the
camp but the one house built on the outcrop, and every lamp and stove and candle in the camp burned blue and gave no heat
except the Tobins'.

Everything after that the camp did itself. By midnight there were people in the street looking up at the one yellow window,
and by one there was a crowd at the door asking what the Tobins had done to keep their lamps. Walter Tobin went out to tell them
it was the outcrop. Mary went out after him. Nineteen men with things in their hands killed them both in the street, in the blue
light, because a frightened camp that sees one house spared needs the house to be the reason. Father Keane came up the back way
and took the three children down to the church and stood in its door all night with his arms out, and nobody passed him.

The coroner's jury was twelve of the nineteen and found misadventure during a disturbance. Agnes Tobin was nine and at the
window. She signs herself Pryce now, and she has the nineteen names, and the street each man lived on, and what each had in his hands, and she has given them to the county, and
the county has put them in a drawer.
""",
      open=[("Does anything come for the nineteen?",
             ["No. Keep it that way. This story is the Territories' own work, and a ghost would let the camp off.",
              "The Tobins' lamp still burns yellow in the empty house on the outcrop on the night of 14 January, and the "
              "nineteen have stopped going out that night."])],
      table="""
Run Cinnabar Flat with no monster in it at all, and the Lynch Mob's entry for the crowd: names said out loud break a mob, and
firing into it makes the posse the thing it came for. If the players ever arrive in a town on a blue night, let them be the
house with the yellow lamp. Agnes Pryce's list is in a county drawer, and a posse who takes it out has nineteen men to deal with.
""")

entry("dugout",
      people=["Haskell, Ruth", "Haskell, Joe", "Haskell, Tilly", "Kittredge, Jas.", "the county surveyor"],
      places=["the Saline", "Salina", "the Haskell dugout"],
      creatures=[],
      threads=["floor", "breathing", "censuses", "street"],
      when=[(1881, "Tilly Haskell, four, goes through the back wall of a dugout on the Saline in May and is pulled out an "
                   "hour later"),
            (1882, "The Kittredges, who bought the claim, write to the county about the cold in the cellar")]
      ,
      story="""
Joe Haskell was digging a root cellar into the bank behind the dugout in May 1881, and at eight feet his spade went through
into nothing. Cold came out of the hole, and a sound like a church before the service with a great many people in it waiting.
The cat went in, and Tilly, who was four, went in after the cat. They heard her for most of an hour, near and far and once
under the floor of the dugout itself, and Joe went in on a rope to the waist and his lamp went out and he found neither wall
nor floor, until he had her by the ankle.

She'd been in a long room where a great many people stood facing the wall, and none of them turned round. That's all of
what she saw and it's true. Under the plains there's a room longer than any plain, and the people in it have been standing a
very long time, and they're waiting. The loess on the Saline pipes where water runs underground, as the Nebraska man told the
surveyor, and a pipe had opened a way into the room, and a child had walked in among them.

Nobody touched her. She was the only living thing that had ever been in that room, and every one of them kept facing the wall
while she walked among them looking for her cat, because turning round was what they were waiting to do, and it wasn't time.
Tilly is nine now, and has asked one question about it in five years, which was whether the people were waiting for anybody in
particular.
""",
      open=[("What are they waiting for?",
             ["Somebody in particular, and Tilly is the only one who has ever asked. When she's grown she'll go back.",
              "For the wall to open. [[ref:floor]] may be the ceiling of the same room, and the three bores may be how.",
              "For nothing. They're every soul the plains ever swallowed without a grave, lost emigrants and drovers and "
              "children, and they're facing the wall because that's the way home was."]),
            ("What happened to the cat?",
             ["It stayed. The Kittredges hear it at night under the cellar, and it's the only one of them that moves.",
              "It came out of a hole in a well on the Neutral Strip two years later, hundreds of miles away, grey to the "
              "tail."])],
      table="""
There's no stat block for the long room and the table shouldn't want one. If the Kittredges' cellar opens again, a posse can go
in on ropes with lamps that will go out, among people who won't turn round. The only rule is that the players mustn't touch one.
The Keeper decides what happens if they do, and should decide it before anybody goes in.
""")


# ================================================================ Hunger
intro("hunger", """
The editor said the accounts are the worst of the book and meant this chapter. Every story behind it is
about what people eat when there isn't enough, and three of them are the face [[kb:olddark-faces]]
calls the Devourer, whose ground is anywhere hunger was once the only news, and whose congregations are
the best-fed people in a starving county. The Ellender Party is that face's own story in the Player's
Book, told the country's way, and the papers here are what it looked like on the page.

The others are a hotel taken for a week by people who don't eat, a trader who starved a band at a lake
post, a railroad's quarantine, and four men dead of thirst beside a full canteen. One of those papers
speaks for a real nation, and its story stays with the trader.

Handle the eating with a light hand. The Keeper's Book says the feeding is a scene and the Keeper decides
what it costs, and the safety line holds here as everywhere: a table that doesn't want the detail should
be given the ledger and not the meal.
""")

entry("ellender",
      people=["Ellender, J.", "the letter-writer (one of the four)", "her brother-in-law", "the storekeeper",
              "the man who came up from below"],
      places=["the north fork"],
      creatures=["The Wendigo-Touched", "The Hunger That Walks", "The Devourer's Tongue"],
      threads=["supper", "glutton", "wendigo", "thirst"],
      when=[(1871, "Nineteen people go up the north fork with three wagons in September; four come out in the spring")],
      story="""
J. Ellender took nineteen people up the north fork in September 1871 with a good outfit and a storekeeper who told him so, and
the snow shut the pass behind them in November. The flour went fast because it always does. By Christmas it was gone. There was
six hundred pounds of side bacon in the second wagon under a tarpaulin, and they'd loaded it themselves.

In the middle of December they stopped talking about food, and the letter-writer is right that it wasn't bravery. It went out
of their heads the way a word does. That's the Devourer's door opening: it arrives when a body is failing, and its offer comes
as meat, and it takes the other thought away first so that the offer is the only one in the room. The brother-in-law walked
past the wagon every day for nine weeks. By January, somebody had died of the cold and nobody buried him, and after that the
party ate.

Four came out in the spring when a man came up from below and the first thing he said was about the wagon, and they all four
turned and looked at it as if it had been carried in that morning. Ashby's note is half right. Forgetting was what was wrong
with them, and the editor's addition is the other half: a party that has decided to do a thing it can't admit to will stop
talking about food, and won't look at the wagon. The country tells it with eleven souls and four days' flour and nine coming
down fat, which is backwards, and the country is telling the truth in its own way. Nobody who came down ever went hungry again,
and nobody ever stopped eating.
""",
      open=[("What became of the four?",
             ["The letter-writer married and lives in Denver and eats very little, and her brother-in-law is at the Dismal "
              "River, where they eat together ([[ref:supper]]).",
              "All four are served. They meet once a year, at Christmas, and eat together, and don't say grace.",
              "Two are what the Bestiary calls Wendigo-touched. The other two are fighting it, and one of them is winning."]),
            ("What happened to J. Ellender?",
             ["He was the first to die, and the first they ate, and it was his idea.",
              "He wasn't one of the four and he wasn't found in the spring. He walked out over the pass in February, "
              "alone, and is still walking, thin, with the look the Hunger That Walks has."])],
      table="""
The store's account and the four survivors are enough to build a campaign on without ever running the winter. If the winter is
ever run, it's a snowbound party in a hard year with a wagon nobody looks at, and the players are in it, and the Keeper waits
for a player to say out loud what they'd be willing to do. The Keeper's Book says to make the offer then and not a moment sooner.
""")

entry("supper",
      people=["Brisco, H.", "the old man at the Dismal River", "the sixty"],
      places=["the Dismal River", "the Sandhills", "Omaha"],
      creatures=["Dark Cultist & the Hollow Prophet", "The Devourer's Tongue"],
      threads=["ellender", "glutton", "hotel", "revival"],
      when=[(1881, "An implement drummer is kept three days in February by sixty people on the Dismal River who are the "
                   "best-fed in a starving state")],
      story="""
The winter of 1880 killed three cattle in four between the Loup and the Platte, and on the Dismal River sixty people ate beef
every day. They're a Devourer congregation, and [[kb:olddark-faces]] describes them exactly: the best-fed settlement in a
starving county, generous with it, hurt if a guest declines, eating together as the worship. They won't say grace because they
have nothing to be thankful for that they didn't arrange for themselves. They won't let anybody eat alone, because eating alone
is the one thing a Devourer congregation fears, and it's the thing that eventually frightens a guest.

The beef was the neighbours'. Stock went out of locked barns up and down the Dismal that winter, with no blood on the straw and
no tracks in the mud, and the ranchers blamed the winter, and the winter took the blame. The sixty took Brisco in off the road in
a blow because a stranger at the table is a stranger fed, and a man who has eaten three days at that table owes a chair at it. When
he took his plate out to the step for air, three of them came and fetched him in very kindly, because a man who eats alone after
eating with them is a man who might remember what he ate.

He's been hungry since. He eats well at the hotel and he's hungry all the time, and he mentioned it to the firm only in case it
was catching. It is, a little. The table at the Dismal River has a place for him, and he'll go back, some winter, when the orders
are poor and the road is long.
""",
      open=[("Who leads the sixty?",
             ["The old man who explained the grace, who came down off the north fork in the spring of 1872 ([[ref:ellender]]).",
              "Nobody. They eat together and nobody sits at the head, and the chair at the head is always laid."]),
            ("Will Brisco go back?",
             ["Yes, the winter after next, and he'll write the firm that he's taken a position with a settlement on the "
              "Dismal River and won't be needing his route.",
              "No. He's the one Kansas City drummer in this book who took the hint, and he's selling in Ohio."])],
      table="""
A posse caught in a Sandhills blow can be taken in on the Dismal River, and fed very well, and fetched in off the step. Don't
say what the meat is. Let them count the ranches that lost stock, and the chairs, and let somebody at the table ask a player which
chair they'd like next winter.
""")

entry("glutton",
      people=["the housekeeper (a woman on a claim)", "Ned (her husband)", "Ned's brother", "the merchant"],
      places=["Perdition Basin, the eastern homesteads"],
      creatures=["The Glutton"],
      threads=["ellender", "supper", "water", "pell"],
      when=[],
      story="""
She kept the accounts to argue with a merchant about a bill, which is why they're exact, and they're exact about a thing she
couldn't make anybody attend to. The flour went at fourteen pounds a week, which is right for a house that size, until November,
and then it went at nineteen and twenty-six and forty and fifty-one, and the lock she put on the bin in December wasn't touched,
and nobody in the house was hungry. That's the line on the back of the last sheet. Nobody in this house has been hungry since
November and the flour is going.

The claim is in the eastern part of Perdition Basin, off the Saltlick road, and the homestead well had been going flat since
the autumn, the way wells near Saltlick did that year. Ned's brother stopped with them in October on his way to the survey camp, and slept in the lean-to one week, and went
on. The flour started going the month after. What she and her children and Ned were doing every night after November was
getting up in their sleep, all of them, going to the bin by the back way, which the lock doesn't cover, and eating, standing up
in the dark, and going back to bed full.

The accounts stop on 16 December. The merchant never got his argument. The family was gone from the claim by the spring, and
nobody at the Crossing will say they know where, and the bin was empty and the lock still on it.
""",
      open=[("What was eating through them?",
             ["The thing under the basin, coming up the flat well as a hunger, which is one of the ways it can come. That "
              "doesn't name a face. Any of the three [[kb:basin-keeping]] offers can wear a hunger.",
              "Something Ned's brother brought from the survey camp, where he'd breathed the cut.",
              "A Glutton in the lean-to, which is the Bestiary's plain animal answer, and a family that was too frightened "
              "to write down the other thing."]),
            ("Where did the family go?",
             ["To the Dismal River. Families that stop being hungry find their way there.",
              "Into the Saltlick well, as the one or two the water takes, all four at once, which isn't the rate."])],
      table="""
Put the accounts in front of the players and let them do the sum: forty-four pounds a week behind a lock nobody touched. Then
put them in a basin homestead for a night, and have somebody wake at three to find the whole family at the bin, eating in the
dark, with their eyes shut.
""")

entry("township",
      people=["the relief committee of a Dakota county", "the people of Township 112"],
      places=["Township 112, Dakota", "Ohio"],
      creatures=["Dark Cultist & the Hollow Prophet", "The Glutton"],
      callings=["Dark Cultist"],
      threads=["supper", "ellender", "glutton", "evergreen", "route"],
      when=[(1878, "A religious body comes together out of Ohio and settles Township 112 in Dakota"),
            (1881, "In the hard winter the relief committee finds Township 112 well fed and asking for nothing")],
      story="""
Township 112 is a congregation of the faithful who asked never to go hungry again, and in the hard winter of 1880, when the
trains stopped for four months and ten townships were eating their seed wheat, they had fresh meat on every table. The
committee was received kindly and fed and invited to the evening meeting, and declined, and the chairman wrote in his own
margin what they'd been asked at the door: what they wanted.

The want is the Devourer's, and that face answers the way it answers everybody, with exactly what was asked and nothing that
was meant. The stock was fat because the township fed it, and the cellars were dug deeper than a cellar needs because that's
where the township kept the rest of what it fed on. Nobody in Township 112 went hungry. A good many people round it went
missing, in a winter when people went missing anyway.

The township sold up together in 1883 and went west, as such congregations do once they've eaten a district thin, and the
people who bought the farms complain only about the depth of the cellars.
""",
      open=[("Where did they go?",
             ["To the Dismal River, where a settlement of sixty eats every meal together and won't let anybody eat alone "
              "([[ref:supper]]).",
              "Up into the mountains, where the high-country camps are gathering ([[ref:gatherings]]), and some of the "
              "three hundred who wintered above the Boulder River in good flesh were theirs."])],
      table="""
This is the Devourer at its most respectable: farmers, a meeting house, hospitality. A posse snowed in among them in a hard
winter will be fed very well and asked, kindly, what they want, and the right answer is nothing.
""")

entry("hotel",
      people=["Prine, J.", "the manager of the Hot Springs House", "the forty attendants", "the six who went east",
              "the lady from St. Louis"],
      places=["the Hot Springs House", "the Colorado mountains", "Denver"],
      creatures=["The Old Blood", "The Coffin-Rider", "The Day-Man"],
      threads=["trunk", "supper", "gatherings", "hear"],
      when=[(1881, "A party takes the Hot Springs House entire for the week of 20 November, and six of the forty town "
                   "people it engages go east with it")],
      story="""
The party was eleven of the old blood-drinking dead, travelling east from California to somewhere they didn't say, and they
travel the way the careful ones do: by freight, in crates, with their ground in the crates with them, and a living man to sign
for everything. J. Prine is that man. He's a Day-Man in the Bestiary's sense, fifty, courteous, very well paid, and he has
arranged this kind of week in six towns in four years.

They took a hot springs hotel because the ground at a hot spring is warm and they'd been cold in the crates. They nailed the west
shutters and took no lamps and no food. They engaged forty people of the town at three dollars the night, in good health, and
willing, because the old ones are particular about willing: a gift taken is a better meal than a thing stolen, and a town that
has been paid doesn't come after you with fire. For a week the forty sat with them in the dark parlour and talked about their
people and where they'd been raised, and fed them, a little each night, and remembered only the mornings.

Forty sets of linen and four more were changed nightly, and six of the forty didn't call for their wages because they'd gone
east with the party on the 27th. Two of them wrote home in their own hands to say they'd gone of their own wish, and they had.
The account-giver is right that nobody made them. The old ones had been asking every night who'd like to see St. Louis.
""",
      open=[("What became of the six?",
             ["Turned, two of them, and the other four are Day-Men now, signing for crates in freight offices from St. Louis "
              "to New Orleans.",
              "They're what the party lives on between towns, kept warm and well and willing, and the letters home are true.",
              "One of them came back to Colorado in 1883 and works at a Denver depot, and signs for crates, and would like to "
              "talk to somebody about it."]),
            ("Where was the party going?",
             ["To New Orleans, to the courtyard below Canal Street, to be heard ([[ref:hear]]).",
              "East, in the direction everything in these papers seems to be going that decade, and a Keeper who has the "
              "Rockies gatherings in play can decide whether the party turned north at Denver."])],
      table="""
The best way to use this is Prine: a pleasant, efficient man who arrives in the players' town with gold and a letter of
engagement, and needs forty willing people for a week. A posse that takes the job at three dollars the night will be well treated
and very tired, and will have to decide on the sixth night what to do about the question they're asked.
""")

entry("wendigo",
      people=["Flett, Andrew", "a woman of the band (whose name is withheld)", "the agency's interpreter",
              "the surgeon below the lakes", "the two young men"],
      places=["Tamarack Narrows", "St. Paul", "Wabasha Street, St. Paul", "the north post"],
      creatures=["The Wendigo-Touched", "The Hunger That Walks"],
      threads=["ellender", "supper", "collector", "calendar"],
      when=[(1880, "In the hard winter, Andrew Flett keeps his flour at the post at Tamarack Narrows while eleven of the "
                   "band die of hunger nearby, and walks the camp on four-foot snowshoes"),
            (1882, "Flett lectures on the Wendigo at Market Hall, St. Paul, on 19 October"),
            (1884, "Flett is found dead of want in his rooms on Wabasha Street, his larder full")]
      ,
      story="""
This is one of the four papers that speak for a real nation. The woman at the agency said what her people mean by the word, and
what they chose to say about that winter, and this book doesn't say anything for them. The story behind the papers is Andrew
Flett's, and it's the story of a trader.

He'd kept the post at Tamarack Narrows twenty-two winters. In the hard winter of 1880 he had sixty-four barrels of flour and forty
of pork on hand in November, and he sold the band seven barrels of flour and three of pork for furs at forty marten the barrel,
and issued nothing on credit, and ate his own nine. Eleven people died within a morning's walk of his door. When the band's
lodges were close enough to smell his bread, he cut a pair of snowshoes four feet long and walked them round the camp by night and
cried from the trees, and the band moved eleven miles off. The snowshoes are worn through at the heel because he walked them far
more than twice.

In January two young men of the band came in to trade and were entered in his book as having gone on to the north post, which
has no record of them. That's all this book will say about it, as it's all the woman at the agency would say. After that winter
Flett ate four meals a day and more at night and lost three stone, and lectured to a paying hall about a superstition he'd made
a pair of snowshoes to exploit, and ate two suppers after. He died of want in 1884 with his larder full, as a man does who has
become, in his own people's words, a thing that's never full and grows thinner the more it eats.
""",
      open=[("What was Flett at the end?",
             ["A man with a cancer of the stomach, as the surgeon says, who did a monstrous thing in a hard winter and was "
              "punished for it by nothing but his own body. The monster in this story doesn't need anything added.",
              "What the Bestiary calls Wendigo-touched: a man who ate what he mustn't, in a winter that asked him to, and "
              "couldn't stop. The Bestiary's hunger is its own and nothing in this book puts it in anybody's religion."]),
            ("Did anything leave the rooms on Wabasha Street?",
             ["No. He died there alone.",
              "The snowshoes, which weren't in the rooms when the coroner came, and aren't in any lecture hall since."])],
      table="""
Keep this story on the trader's side of the counter. Don't set it at the table as a monster of the Ojibway, because it isn't one:
it's a white man at a post with flour, and a hall in St. Paul that laughed. If a posse ever goes to Tamarack Narrows, the post
has a new factor and the band has its own business, and neither owes the posse anything.
""")

entry("tempe",
      people=["Tempe, Aunt (a bonesetter)*", "Clem", "Prue (Clem's wife)", "Birch, Mrs."],
      places=["the Big Sioux, Dakota", "the Cumberland mountains"],
      creatures=[],
      callings=["Shaman"],
      threads=["belts", "glad", "returned", "ninth"],
      when=[(1880, "Clem freezes against a fence in the December blizzard on the Big Sioux; Aunt Tempe calls him back by "
                   "his name through the night of the 21st")],
      story="""
Aunt Tempe is a bonesetter out of the Cumberland mountains who has set every bone in that township and been paid in eggs and
quilts, and she's what the Player's Book calls a Shaman: somebody who learned early that the country is crowded. When Clem
froze against the fence and was carried in stiff, with snow in his eyes, she walked through the blizzard and sat with him a
night and called his name, over and over, the way you call a dog in, until something gave him back.

What she paid with was her singing. She led the hymns at church every Sunday for twenty years, and since Christmas she stands
through them with her mouth shut and the tears running. She told Prue the cost wasn't money and was already paid, and that's
exactly true. Whatever she called Clem back from wanted a voice in trade, and she had a good one.

The physician's account is the honest alternative, and the editor would like it to be the answer: a frozen man isn't dead
until he's warm and dead, and warmth and time and somebody sitting by him have brought men back after hours in the snow.
Tempe's own view is that she did what she was taught, and would do it again for anybody in the township, and can't, because
she only had the one voice.
""",
      open=[("Is Clem all himself?",
             ["Yes, all of him, as his wife says, less two toes.",
              "All but one small thing his wife hasn't noticed and Tempe has: he doesn't sing either now, and he used to "
              "stand beside her."])],
      table="""
A Shaman in the posse is the one who'll understand what Tempe paid and ask what it went to. She's a fine mentor for one:
she'll teach the calling and charge nothing, and warn them about the price in one sentence, and say no more.
""")

entry("fortsafe",
      people=["Lau Chung", "the first sergeant of a troop of the Tenth Cavalry", "the company's police",
              "the construction department", "the nine at the cut"],
      places=["the Sixmile cut", "Camp Harker", "Albuquerque", "San Francisco"],
      creatures=["The Possessed", "The Veinwork", "The Regulators"],
      threads=["boxes", "assay", "survey", "lamps"],
      when=[(1882, "Graders at the Sixmile cut blast into a seam that smells of cold ashes in September; Camp Harker takes in "
                   "130 people and 'discharges' all of them by 28 October; a troop of the Tenth Cavalry rides in on 2 November")],
      story="""
The grading crews at the Sixmile cut blasted into a seam in September 1882 that came up wet and smelling of cold ashes, and within
the week men were going quiet. They stopped sleeping and eating and stood at the lip of the cut at night looking down, and didn't
answer to their names, and a man taken by the arm fought like three. The seam had been shut since long before anybody laid a rail,
over a place where something burned a long time ago and never finished burning, and what came up out of it got into the men who
breathed it and stood them at the edge waiting for it to call them down.

The railroad's answer was Camp Harker, an old army post eleven miles down the line, and handbills saying the fort was safe, and
forty of the company's police. A hundred and thirty people went in: sick men, their families, and anybody in fear of the sickness,
who came in the wagons at seven each morning. The ration return is the whole story. Discharged, eleven, then seventy-four, then all
of them, with no destination, and the wagons came back empty the same day, and the post graveyard was enlarged.

Lau Chung smelled cold ashes and knew them from a village after soldiers, and he took four men of his district down the river the
first week, because his association had always told its men never to go to a place that promises to keep them. He came back on 3
November to see what had happened, and found a troop of the Tenth Cavalry in the post with thirty-one of the company's police and
none of the received, and helped the troop with the nine men still standing at the lip, who died in the four days after without
sleep or food. He took no pay. The inquiry at Albuquerque had every paper and found hydrophobia.
""",
      open=[("What is the seam?",
             ["The Thing Beneath the Mountain, which works through the diggings, and the standing men were the first of a "
              "crew it meant to keep.",
              "Something older than any face the Keeper's Book names, burned once and not finished, and the Tenth's first "
              "sergeant filled the cut back in himself on the 7th.",
              "Hydrophobia and bad air and a company that panicked, which is enough, and the ration return is the horror."]),
            ("Who gave the order at Camp Harker?",
             ["The construction department's superintendent, who's been promoted since and works at Kansas City.",
              "Nobody gave an order. Forty armed men were left in charge of a hundred and thirty frightened ones and told the "
              "company would stand behind them."])],
      table="""
The Tenth's first sergeant and Lau Chung are the two honest men in this story, and a posse should meet them as the people who
did the right thing when nobody else would. The post graveyard at Camp Harker is the evidence, and the Regulators are what the
company sends when somebody starts asking to dig it up.
""")

entry("thirst",
      callings=["Sawbones"],
      people=["an assistant surgeon, U.S.A.", "the four men in the dry camp"],
      places=["the Badlands south of Perdition Basin", "the South well", "the seep at the head of the draw"],
      creatures=["The Thirst", "The Thing in the Well"],
      threads=["water", "glutton", "ellender", "sanclavo"],
      when=[],
      story="""
The four men were prospectors out of Coffin Wells working the badlands south of the basin, and their last camp was a day's ride
from the South well, which [[kb:basin-wells]] marks as broken, gone with nobody near to notice. They noticed. They'd
filled their canteens there on the way out, and on the second day one of them drank and they watched what it did to him, and
after that nobody touched the canteens.

They emptied three onto the ground and kept the fourth stoppered because a man in that country doesn't throw water away even when
he knows what it is. Then they tried for the seep at the head of the draw, two and a half miles off and marked on the map in the
pocket of the man nearest the canteen. They didn't reach it because the seep had water in it that looked exactly like the seep
and kept being a little further off, the way the Thirst does, and they followed it round in a circle for three days in sight of
the real one.

They died of thirst three feet from three pints of water, and the surgeon was right not to offer an explanation, because the
only explanation is one no quartermaster's inventory has a line for. Somebody in that camp decided that thirst was the better
way, and the others agreed.
""",
      open=[("What was in the canteen?",
             ["Water from the South well, which is whatever the Keeper decided came up it. A player who unstoppers the "
              "canteen finds out.",
              "Sweet water, and the four were wrong about the South well, and died of their fear of it."]),
            ("What happened to the one who drank?",
             ["He's one of the four, the first to die, and he died wet.",
              "He isn't one of the four. There were five, and the fifth walked back toward the South well on the second "
              "night, and the surgeon's detachment didn't know to count him."])],
      table="""
The South well is a whole reckoning waiting to be found, and this is how players find it: the surgeon's report, a full canteen in
a quartermaster's store at the Crossing, and a map folded to the right sheet. The Thirst's entry is how the badlands fight back.
""")


# ================================================================ Preaching
intro("preaching", """
The editor was careful here and a Keeper should be too. Most religion in the Territories is a tired man on
a horse riding two hundred miles for forty dollars a year, and one of these six papers is that man, with
nothing behind it at all. Leave it that way. The others are the kind that sells tickets: a revival that
heals, a burial club that isn't one, a guide who takes parties up a mountain, a family that shut itself
in with its doctrine, and the green doors.

The Red Sermon is the face [[kb:olddark-faces]] gives the revival tent and the full pews, the only face
whose congregations are innocent, and the Good Revival is its own story in the Player's Book. The
Circuit in the Bestiary is what it becomes when it learns to travel. Fight it the way the Keeper's Book
says, for people and in public, and never with a gun.
""")

entry("revival",
      callings=["False Prophet"],
      people=["Cassie (a letter-writer)", "Ann (her sister in Missouri)", "Trice, Mrs.", "Bevill girl, the",
              "Gilliam, Mr.", "the preacher of the Good Revival"],
      places=["a town in the southern counties (since renamed)"],
      creatures=["The Circuit", "The Sermon Made Flesh"],
      threads=["circuit", "braid", "supper", "haunting"],
      when=[],
      story="""
The Good Revival came to a town of ninety in the southern counties in a hard February: four nights, no collection, come
hungry. The preacher was one of the eleven that the Bestiary's Circuit counts, a good man who believes he was called, and
he was right in a way he'd not enjoy having explained. He preached four nights and the town sang until midnight, and nobody
can remember a word of the sermons, because the words weren't the part that was working. The singing was.

Then everybody was well. The Bevill girl who'd been poorly two years got up on the Saturday and went to work. Nobody in the
town was sick for eleven months, not a cold in February. Old Mr. Gilliam, ninety-one and not expected to see the spring,
splits wood. That's the Red Sermon's offer: miracles that truly work, a gospel that visibly does what it says, and nobody who
takes it is a fool, because it's real. Its price is the flock, a soul at a time. Four people in the town were well in the
morning and dead by the evening, and the doctor from the county seat couldn't say of what, and two of them were young. Those
four were the portion, and there will be four more this year, and the town knows it, and has decided not to know it.

They renamed the town the spring after. That's the part the Player's Book gets right when it says you ride out to the town
they name and find an ordinary place where nobody remembers a revival. Mrs. Trice has a better head than Cassie and knows
exactly what was sung, and won't sing it.
""",
      open=[("Who were the four?",
             ["The four who couldn't be healed of doubting. Each of them had said aloud, the week after, that they couldn't "
              "remember the sermon and it bothered them.",
              "Nobody in particular. The thing takes its portion the way the water takes one or two in the basin, by rate.",
              "The four who were sickest before the revival, whose healing cost the most, and who paid for it themselves."]),
            ("Is the preacher coming back?",
             ["Yes. A revival that comes back a second year is one of the Keeper's Book's signs, and the tent will be up "
              "in a night with no wagons on the road.",
              "No. He's four counties away doing it again, and this town is only one of the Circuit's."])],
      table="""
Ashby went back twice and got nothing, and a posse will get the same: the healthiest people in the Territories, perfectly
pleasant, and not one of them will sit down for an hour. The Circuit's entry says how it's ended, and it's slow, and it takes
a printing press. Give the players one preacher who's decent all the way through and truly doesn't know.
""")

entry("circuit",
      callings=["Preacher"],
      people=["Teague, Rev. A.", "the presiding elder", "Cardoza family"],
      places=["Perdition Basin, the southern end of the circuit", "the Cardoza place", "the lower river"],
      creatures=[],
      threads=["returned", "coroner", "cut", "sanclavo"],
      when=[],
      story="""
There's no legend in these four letters and none should be added. The Reverend A. Teague rode a Methodist circuit of two
hundred and ten miles for eleven years and two hundred and forty for nine more, buried more than he baptised, married almost
nobody, asked his elder for a horse in plain words, and died of his heart at a ford in the rain at sixty-one. He's the tired
man on the horse the editor wanted in this chapter, and he's here so it isn't only about the other kind.

What a Keeper can know is where he rode. The southern end of his circuit is Perdition Basin: the Cardoza place, the lower
river where he said the words over the bar for Asa ([[ref:returned]]), the homesteads by the wells. The people there knew
their hymns better than his own congregations, and came to preaching, and talked about the weather and the stock and their
dead, and never once in eleven years asked him what anything meant. They'd been living for seventy years inside an
arrangement that costs one or two a year, and a person who knows exactly what one thing means doesn't need anything else
explained, and can't bear to ask.

Teague felt it and couldn't name it and wouldn't write a report on a feeling. So he asked to keep the southern end when the
district was divided, because that's what a good man does when something is wrong and he can't tell what: he keeps going
there. The Cardoza boys came out to meet him the day his mare died because they'd been watching for him, the way the
basin watches for the ones who walk its circuits.
""",
      open=[("Did Teague ever learn what the basin was keeping?",
             ["No, and that's the right ending. He rode beside a second circuit for twenty years without knowing it was there.",
              "Once, at a ford, from Esperanza R&iacute;os, and he never wrote it to his elder and rode the southern end "
              "nine more years because of it."]),
            ("What did he die of?",
             ["His heart, as the elder's office recorded, at sixty-one, in the rain.",
              "The same thing, at a ford, and a basin Keeper may note that the coroner at the Crossing entered it that year "
              "beside one other."])],
      table="""
If the players meet Teague he's a tired, funny, decent old man on a good horse his elder bought him, and he's the one person
in the county who will sit with a posse and ask them what they need without wanting anything. Let him be exactly that. A
Keeper who makes him anything else has wasted the only one of him in the book.
""")

entry("faculties",
      people=["A. R. (a pastor in the San Juan)*", "M. R.", "the Chancellor of the diocese", "a Cornish miner"],
      places=["a mining camp in the San Juan", "Silverton"],
      creatures=["The Possessed", "The Tommyknocker"],
      callings=["Padre"],
      threads=["circuit", "lamps", "patent", "adit", "uncle"],
      when=[(1881, "A pastor in the San Juan asks his bishop in November for the faculty to exorcise a young married "
                   "woman of the parish, is refused, and performs the rite without it on the 27th")],
      story="""
The pastor is what the Player's Book calls a Padre: one tired man at the end of a closed road, with eighteen hundred years
behind him and a Ritual he has read very carefully. He waited seven weeks and wrote for the faculty, and the bishop refused
it, as bishops usually do, and the pastor performed the rite anyway on the night of the 27th, because on the 26th M. R. had
stood at the foot of her children's bed and told them the days they'd die.

She spoke Cornish, the old Cornish of the mines, which a Cornish miner in the camp could only half follow. The camp is built
over workings older than the camp, dug in the fifties by Cornishmen who brought their knockers with them, and something down
there had learned the language from them and come up into a woman who'd never heard it. The Rite was the Church's, and it
worked, and she took communion the next two Sundays.

The physician at Silverton saw her in the spring and found her well, and his explanation, a nervous illness of a winter
indoors, is the one the diocese prefers. The pastor did his thirty days' penance and was moved, and he'd do it again, and
nobody has asked him to. Yet.
""",
      open=[("What spoke Cornish?",
             ["Something the Cornish knockers kept down in the old workings, older than they are, which learned their "
              "tongue from them, and which the Bestiary's Tommyknockers have been keeping in.",
              "The woman's own illness, speaking words she'd heard through the floor of a company house from miners at "
              "their supper, without knowing she'd heard them."]),
            ("Were the children's days right?",
             ["The first child's was, in 1884, and the mother hasn't let the others out of her sight since.",
              "None has come yet, and the eldest is fourteen."])],
      table="""
A Padre in the posse will meet this question at least once: the faculty, or the person in front of you. Make the bishop
reasonable, the road closed, and the woman's voice speaking a language from under the floor.
""")

entry("belts",
      callings=["Shaman"],
      people=["the guide at White Sulphur Springs", "the guide's mother", "a merchant of Butte", "his son",
              "a woman from New Orleans", "the spirit-talker"],
      places=["the Big Belt Mountains", "White Sulphur Springs", "Butte", "Helena"],
      creatures=[],
      threads=["hear", "gatherings", "gorham", "witch"],
      when=[(1881, "The guide's mother goes up into the Big Belts with a growth the Helena doctors gave until the fall, and "
                   "is received")],
      story="""
Nobody who has been up there can say what people the spirit-talker comes of, and the editor stopped asking because every guess
told him more about the man guessing. This book won't guess either, and a Keeper shouldn't make the spirit-talker a borrowed
figure from any living people's faith. The spirit-talker is the Keeper's own.

What can be said is what the guide's book shows. The spirit-talker receives about one party in six, and chooses by need rather
than by what the party came for. The gentleman from Boston came for his lungs and the widow from Ohio to speak to her husband,
and neither was received. The merchant from Butte came about his brother and was told instead what was wrong with himself, and
it was true, and he's been attending to it since. The guide's mother went up with a growth and came down with her life. The
army officer and the railroad man with his list of questions were turned away, and the railroad man is the one the Keeper
should think about.

The woman from New Orleans who said she'd been sent is the thread. The Long Table keeps springs and houses and the only
medicine for forty miles, and it notices when somebody else in its country is doing the same work without a seat. She was sent
to find out whether the spirit-talker was received by the Table, or received anybody on the Table's behalf, and she wouldn't say
what she found, and the guide didn't press her.
""",
      open=[("Who, or what, is the spirit-talker?",
             ["A healer with no seat and no master, the one thing in the book that does good and asks nothing, and the Table "
              "has decided to leave it be.",
              "Somebody the Table has asked to stand, who went up into the Belts to keep at it.",
              "Something the mountains keep, which is why the congregation that wintered above the Boulder River came through "
              "a killing season in good flesh, and why the spirit-talker turned the railroad man away."]),
            ("What was the railroad man's list for?",
             ["The survey through the Belts. The railroad wants to know what's up there before it lays track through it.",
              "Kansas City wants to know whether the spirit-talker can be bought."])],
      table="""
The guide is a decent man who'll take a posse up for forty dollars and promise nothing. Ten days in the Belts and a camp with a
fire lit and somebody across it whom nobody afterwards can describe is a rare thing in this game: a scene where the dark isn't
coming, and somebody tells a player the truth about themselves.
""")

entry("braid",
      people=["the testatrix (Hannah's mother)", "Hannah", "Lib (her cousin in Ohio)", "Wesley (Hannah's son)",
              "Jennie (Hannah's daughter)", "Albright, J. (secretary of the club)", "Mr. A."],
      places=["the Republican valley", "Cincinnati"],
      creatures=["Dark Cultist & the Hollow Prophet", "The Circuit"],
      threads=["revival", "glad", "will", "ninechairs"],
      when=[(1851, "A mother in the Republican valley begins keeping a braid of her family's hair, and joins a burial club "
                   "at Cincinnati"),
            (1882, "Jennie falls from the loft in September; Wesley takes the box east in December")],
      story="""
The burial club at Cincinnati is a congregation, and it was one before any of the families in it came west. Hannah's mother
joined it in 1851 with a strand of her own mother's hair, and paid her dues every year for thirty, and kept the braid. The
braid is the family bound together in one rope, and a family bound in one rope can be carried. The root strand, coarse and black
and older than any name in the Bible, is the club's: the thing it serves, braided into every family it holds.

She took the living's hair while they slept because a strand given awake is given, and a strand taken asleep is owed. When one
of them dies the club attends, and the strand moves down to where the dead are, and nobody has touched the box. Jennie fell from
the loft on the 3rd of September because the club had need of a death in that family that month, and her strand went down the
braid the next morning. Hannah's letters are the clearest account in the book of a family finding out it has been kept.

The dues were paid through the third generation, and the third generation is Wesley. The club wrote to him. He took the box and
went east, and he's preaching now, and J. Albright, who answers the editor's letters politely, signs himself a minister. Wesley
is being raised up to be what the club has been braiding toward for thirty years: a preacher whose congregation is carried in a
rope, and who fills a plate he doesn't see.
""",
      open=[("What does the club serve?",
             ["The face the Keeper's Book calls the Red Sermon, and Wesley will be the Circuit's twelfth preacher.",
              "Something the Keeper's Book doesn't name, which is older than the faces and wears none of them.",
              "Nothing at all. A burial club with a strange old custom and a secretary who became a minister, and a grieving "
              "woman's melancholy, as the family doctor said."]),
            ("What happens to Hannah and her youngest?",
             ["They're still strands in the braid, and Wesley has the box.",
              "Hannah cut her own strand out in December before he took it, and her youngest's, and burned them, and the "
              "club knows."])],
      table="""
Wesley is the recurring face, a young preacher with a box he never opens and full pews wherever he goes. A posse that finds the
braid can end what it holds the way the Hollow Prophet's entry says: find the token and break it. The token is the root strand.
What it costs to cut, and whose strands come away with it, is the Keeper's.
""")

entry("lindqvist",
      people=["Lindqvist, Nils", "Lindqvist, Brita", "Lindqvist, Karin", "Lindqvist, Anna", "Lindqvist, Per",
              "Brekke, Mrs. Kari", "the pastor of the Swedish congregation", "the woman in the buggy"],
      places=["a Dakota claim", "the coulee", "the north end of Denver"],
      creatures=["The Witch"],
      threads=["houses", "stand", "witch"],
      when=[(1870, "Nils Lindqvist brings his wife and five children from Sm&aring;land to a Dakota claim"),
            (1872, "Nils Lindqvist dies in the coulee in February; his daughter Karin leaves the county in March with a woman "
                   "in a buggy")]
      ,
      story="""
Nils Lindqvist brought his family from Småland in 1870 and quarrelled with the Swedish congregation in town inside a year over a
point of doctrine nobody else thought worth the quarrel, and after that the family saw nobody. He read Job aloud till midnight.
Karin was eighteen and had English, so Karin did the trading, and the family's whole connection to the rest of the world was a
girl walking to the store.

Kari Brekke on the next claim left the flour and the wood and the ham and the boots at the door all that winter because the
children were hungry and he'd not have taken them from her hand, and she was too proud to say so. Nils poured the flour on the
snow and burned the boots and called it the devil's charity, and Brita hid the ham under the floor and fed the children when he
slept. Nothing in the gifts was the devil's. It was a neighbour, which is the ordinary kind of grace, and Nils's pride was the
only thing in that house that did any harm.

Karin had been meeting somebody all winter, as her father said at supper in front of everybody, but it wasn't whoever brought
the gifts. On her walks to the store she'd met a woman in a buggy from a house in Denver, a seated house of the Long Table that
takes in the women nobody else takes in, and the woman had asked her questions and been kind. On 11 February Nils went out at
dark without the lantern to find the giver, and Karin went out after him with it.
""",
      open=[("What happened in the coulee?",
             ["Nils fell in the dark and the cold did the rest, and Karin found him too late and came home and said nothing.",
              "Karin found him, and he turned on her the way he'd turned on everyone, and she came home without the lantern.",
              "Karin didn't find him. She went to the woman in the buggy that night, and the woman went looking with her, "
              "and the woman found him first."]),
            ("What became of Brita and the other four?",
             ["The Brekkes took them in, and Brita lived another thirty years and never spoke of the winter.",
              "They went to Denver after Karin, and the house took them in too, and the store account paid in gold was the "
              "family's passage.",
              "The county's book doesn't say, and neither does Karin's letter, and a posse could find out."])],
      table="""
Karin is at the north end of Denver, living with women who don't ask what she did to deserve it, and a posse that finds her will
find a grave, courteous young woman who keeps a birthing house's books. What she did is hers to tell. The woman in the buggy is
the Witch in the Bestiary's sense only if a fight ever comes to her, and it shouldn't.
""")

entry("houses",
      people=["the woman at the green door in Denver", "a committee of gentlemen"],
      places=["the north end of Denver", "eleven towns in four territories"],
      creatures=[],
      threads=["lindqvist", "kansas", "stand", "witch", "seats"],
      when=[(1884, "A house at the north end of Denver refuses a subscription of $4,000 in August")],
      story="""
Anybody may paint a door green, the woman told Ashby, and she was telling the truth. Of the eleven houses whose cards Ashby
collected, some are seated houses of the Long Table and some are Methodists and one is a Quaker widow in Omaha who read about the
others in a newspaper, and every one of them takes in a woman with nowhere to be tonight, no questions, no charge, no church. The
card is the same in every town because the first house printed it and the others copied a good card.

The house at the north end of Denver is seated, and it's where Karin Lindqvist lives. The four thousand dollars was raised by a
committee of gentlemen of the first standing, and the gentlemen were Kansas City's correspondents in Denver, and the money was
Kansas City's. [[kb:powers-together]] notes that the Dread Mother's houses are the only institution in the Territories that has
ever turned down Kansas City money, and that nobody has thought to ask them why.

The reason the woman gave is the true one. A house of the Table owes a truthful answer to the Table if it's asked. It won't take
money from anybody who has asked what the money is for, because taking it would mean owing them an answer too, and a house can
owe only one table. The gentlemen asked what the house was for. That's all it took.
""",
      open=[("Why did Kansas City want to give it money?",
             ["Because a house that takes money can be asked a question, and Kansas City has questions about the Table.",
              "Because the committee were honest men who'd seen what the house did for the north end, and the Ledger behind "
              "them had other reasons, and nobody on the committee knew both."]),
            ("Which of the eleven houses are seated?",
             ["Decide per town, and let a posse find out the hard way which green door is which.",
              "Six, and the other five don't know that the six are different."])],
      table="""
The coffee is very good. A posse knocking at a green door is received in the passage and not further in, and should be. If the
players need a woman hidden, a green door is where to take her, and if it's a seated house, the Table will remember that they
brought her.
""")


entry("landismine",
      people=["a preacher at the seminary of Jubilee", "Winship, T. (a Methodist elder from Tucson)"],
      places=["Jubilee", "Tucson"],
      creatures=["The Sermon Made Flesh", "The Parcel"],
      callings=["Preacher", "False Prophet"],
      threads=["clerk", "spur", "gold", "committee", "lookedat", "degree"],
      when=[(1883, "A Methodist elder from Tucson takes down in shorthand a sermon on Leviticus 25 preached in the "
                   "seminary chapel at Jubilee")],
      story="""
The sermon is the most honest thing anybody at Jubilee ever said about the land. The Circle buys ground and plants nothing
on it because the land is His, and they're keeping it till He comes for it, and He'll know it by the stakes. The
congregation didn't need telling who He was, and the elder from Tucson listened an hour for the tenth verse, the one about
liberty that the town is named for, and it never came.

The preacher belongs to the seminary. Whether he's the preacher the women at Jubilee talk about ([[ref:clerk]]), the one who
was there before the town was and promised the first families the country as it was before the war, is the question this
book leaves open. If he is, the Circle answers to a False Prophet, and He in the sermon is the face the sermon promised, and
[[kb:olddark]] says what a False Prophet's congregation feeds: the Old Dark comes to the plate wearing the face the sermon
promised.

The elder's note is the best thing in the chapter. A preacher who knows his Leviticus leaves out the tenth verse knowing
exactly what he's doing, and a congregation that names its town for that verse and doesn't notice it's missing has been
taught not to notice.
""",
      open=[("Who is He?",
             ["The Lord, sincerely. The seminary believes it's keeping God's land for God, and the horror is the "
              "theology, not anything under it.",
              "The list-maker, whoever writes the list, whom the preacher has never met and calls by the only name big "
              "enough.",
              "What the stakes are staking. The Bestiary's Sermon Made Flesh is a creed that grew a body, and a country "
              "that has preached one sermon every Sunday for eleven years has given it a great many mouths."]),
            ("Is the seminary's preacher the women's preacher?",
             ["Yes. He's the False Prophet the faintest rumour says runs the Circle, and he has never once been seen to "
              "eat.",
              "No. He's a young man trained at the seminary who believes it, and the women's preacher is somebody older "
              "whom he has never met either."])],
      table="""
A Preacher in the posse who hears this sermon will hear the missing verse, and so should the player. A False Prophet in the
posse will hear something else: a man doing their work better than they do. Either can be the one who asks the preacher,
after the service, where the tenth verse went.
""")


# ================================================================ Per the List
intro("circle", """
The Golden Circle is the thing inside Redemption, and [[kb:powers-redemption]] has it: an older society with an older name,
buying particular parcels at prices that make no sense and putting nothing on any of them, for a list its officers didn't
write. Its leadership doesn't know why the parcels matter. Somebody hands them the list and tells them it's strategic.

The Book of Legends gives the Circle a chapter of its own, late and short, after the country has been in the open for ten
chapters. That's the arc working: Redemption is the thing everybody knows, and the Circle is the thing nobody at Jubilee
could tell you. The four papers are the committee that buys, a card of its second degree, its agent in Perdition Basin,
and the clerk who walked out.

The faintest story in the Book of Legends is in [[ref:clerk]]: that the Circle answers to a preacher who was at Jubilee
before the town was, and who promised the first families the country as it was before the war. Keep it that faint. One
clerk said it, the women at Jubilee tell it and never twice the same one, and the editor nearly left it out. The entries
below offer it as one way to hold who writes the list, beside the others, and pick none.
""")

entry("committee",
      people=["Quarles, Mr.", "Sallis, E.", "the Chairman of the Committee on Lands", "Quarles, Mrs. (his widow)"],
      places=["Jubilee", "the Muchacho road", "above Leadville"],
      creatures=["The Parcel"],
      threads=["gold", "floor", "clerk", "degree", "lookedat", "gatherings"],
      when=[(1883, "Mr. Quarles asks the Committee on Lands in January who sends the list; in February he dies; in March "
                   "his own quarter section is on it")],
      story="""
The Committee on Lands is the Circle's second degree at work, and its minutes are as dull as minutes are. The list comes and
is read, and the Treasury offers the list price. Mr. Sallis reports the dry lake in Nevada taken and the bores capped
([[ref:floor]]). In January 1883 Mr. Quarles asked where the list comes from, and the Chair ruled the question out of order,
and Quarles asked that it be minuted, and it was.

In February Quarles was absent. He died of a pneumonia, attended by a physician who belongs to nothing but the Odd Fellows,
and in March the list had a new parcel on it, Quarles's own quarter section on the Muchacho road. The widow was paid in gold,
and the Circle has been very kind to her.

This book doesn't say the list killed Quarles for asking. It says the list knew where Quarles's ground was before the
committee did, and that every member who heard the March minutes read understood the lesson, whatever it was.
""",
      open=[("Did the list kill him?",
             ["No. He was going to die, and the list knew it, and wanted his ground the month it would come cheapest.",
              "Yes, in the only way it kills anybody: it named his land, and a man whose land is named begins to die of "
              "whatever happens to be going about."])],
      table="""
The minutes are the Circle at its most respectable, and a posse that gets a look at them should be bored by the routine and
chilled by one line. The resolution about the parties encamped on parcel No. 4 is the hook into [[ref:gatherings]].
""")

entry("degree",
      people=["a farmer near Tucson (the card's owner)", "the Knights of the Golden Circle"],
      places=["Tucson", "Jubilee"],
      creatures=[],
      threads=["committee", "remarks", "lady", "landismine", "kansas", "lookeddoor"],
      when=[(1884, "A card of the Circle's second degree turns up in a dead farmer's Bible at an auction at Tucson")],
      story="""
The Knights of the Golden Circle were real, a society of the fifties that meant to make one slave country of every shore of
the Gulf of Mexico, and most people will tell you they died in the war. In this game they didn't. They went quiet and kept
their castles in a hundred towns that never heard of Jubilee, and when Redemption was founded the Circle came west to live
inside it. It's older than the country it lives in.

The degrees are the old ones. The first is the soldiers, the militia in grey. The second buys, and holds the card, and may
be shown the list. The third is the statesmen, and the statesmen aren't at Jubilee. They're in two Southern statehouses, in
Kansas City, and at Washington, and they're part of the reason a member of Congress revised himself to nothing
([[ref:remarks]]).

The farmer near Tucson was of the second degree for twenty years and never went to Jubilee, which his neighbours were sure
of, and they were right. The Circle doesn't need its buyers at Jubilee. It needs them in every county where the list has a
line.
""",
      open=[("Who else in the Territories holds a card?",
             ["A bank officer at Coffin Wells, which would explain a good deal about the Vane Interest's correspondents.",
              "A county clerk in every county on the list, and one of them is the clerk at Harlan's Ford "
              "([[ref:lookeddoor]]), who keeps the minutes there."])],
      table="""
A card of the second degree in a dead man's Bible is the best way for a posse to learn that the Circle is everywhere. Let
them find it at an auction, and let the auctioneer have sold three others like it that year.
""")

entry("lookedat",
      people=["Purcell, C. D.*", "Purcell's daughter", "the committee"],
      places=["Calvary Crossing", "Painted Mesa, the"],
      creatures=["The Parcel"],
      threads=["twosections", "landoffice", "mesa", "committee", "satchel-note"],
      when=[(1883, "C. D. Purcell, the Circle's agent in Perdition Basin, writes in June asking to be told what he's "
                   "looking for on the two mesa sections; he's told only to look")],
      story="""
Purcell is the Circle's agent at Calvary Crossing, an honest, puzzled man who saw the lines run on the mesa
([[ref:twosections]]) and has been sent every quarter since to look at the two sections. There's nothing on them. The stock
won't cross a line nobody can see. The people of the mesa come and stand at the edge while he's there, and go when he goes.

The committee doesn't need a report, because the looking is what it wants. A parcel on the list is held by being looked at,
the way the wells in the basin are held by being counted ([[ref:satchel-note]]), and somebody has to be the eyes. The
committee picked a man who wouldn't understand what he was doing, because a man who understood would stop. Purcell went every
quarter until he couldn't sit a horse, and then went in a buggy.

Why the mesa people stand at the edge is theirs, and this book doesn't say what it means to them. From Purcell's side of the
line it looks like what it is: one watch kept against another.
""",
      open=[("What happens when Purcell stops?",
             ["The committee sends another man, and the new man sees something on the first day that Purcell never saw in "
              "four years, because Purcell was the right man.",
              "Nothing, as long as the people of the mesa are still standing at the edge. Their watch was always the one "
              "that mattered."])],
      table="""
Purcell is a gentle, worn-out man, and a posse can learn more from him in an afternoon than from the rest of the Circle.
Don't make him a villain. Make him the most frightened man in the basin who doesn't know he should be.
""")

entry("clerk",
      people=["Imbrie, Lewis*", "Kinnear, W. F.", "the Chairman of the Committee on Lands"],
      places=["Pueblo", "the sand hills", "above Leadville", "Jubilee"],
      creatures=["The Sermon Made Flesh"],
      callings=["False Prophet"],
      threads=["committee", "landismine", "principles", "tenth", "muster", "gatherings"],
      when=[(1884, "Lewis Imbrie, clerk to the Committee on Lands, walks out through the sand hills, gives W. F. Kinnear a "
                   "statement at Pueblo in November, and takes the train back to Jubilee")],
      story="""
Lewis Imbrie kept the committee's minutes three years and never learned where the list came from, and neither did the
Chairman, who said it was strategic and then said he didn't know. Imbrie walked out through the sand hills at night on the
railroad surveyors' stakes, which everybody says can't be done, and came to Pueblo to see parcel No. 4 with his own eyes,
and saw it, and gave Kinnear a statement under the Department's contract. The Department wrote File.

He told Kinnear one more thing, and it's the faintest story in the Book of Legends. The women at Jubilee say, never twice
the same one, that the Circle answers to a preacher who was at Jubilee before the town was, and who promised the first
families the country as it was before the war, every man in his place and everybody else in theirs. Nobody Imbrie knew had
seen him. Nobody would say she hadn't.

Then he went home, because the list had come the week before he left, and his house wasn't on it, and he wanted to be there
when it was.
""",
      open=[("Who writes the list?",
             ["The preacher: a False Prophet who has fed the Old Dark at Jubilee since before there was a Jubilee, and the "
              "list is the plate he fills. [[kb:prophet-plate]] has what that costs a country.",
              "Nobody at Jubilee. The list comes from outside, as the clerk says, on paper not sold there, and the "
              "preacher is a story the town grew because a town built on a promise needs somebody who made it.",
              "The same hand as in [[ref:gold]]: something that keeps correspondents instead of ground, and the preacher "
              "is one of its correspondents, and believes he's its master."]),
            ("Did Imbrie get home?",
             ["Yes, and his house went on the list in the spring, and he was there.",
              "The railroad won't say. The Tenth's patrol brought a man in out of the sand hills a year later "
              "([[ref:tenth]]), and his boots were small for him."])],
      table="""
Imbrie's statement is the one paper a posse can carry to anybody at Washington, because a Pinkerton took it under a federal
contract, and they'll find it has already been filed. Let them hear the preacher story once, from a woman at Yuma who
changes the subject. Never let them meet him unless the Keeper has decided he exists, and decided it in writing.
""")

# ================================================================ Nobody's Mother (the Long Table)
intro("longtable", """
The Dread Mother is a Power, and [[kb:powers-mother]] has her: covens that share no rite and acknowledge one
woman in New Orleans, an arrangement they call the Long Table among themselves, houses that are seated or asked
to stand, a tithe twice a year and a truthful answer, springs kept and births managed and the only medicine for
forty miles, and a price paid a child at a time by families who never agreed to it. The Keeper's Book says to
keep her at the far end of a long hallway and never on stage. Nothing here brings her closer.

The Book of Legends calls this chapter Nobody's Mother, after the skipping rhyme in [[ref:ninechairs]], and keeps
the Table as quiet as the houses keep it. Among themselves the houses say the Long Table. On paper they never do.
Of every paper in the chapter that came from a house, the table is written down in one letter, and its writer
asked for it back ([[ref:witch]]); the builder of the Book of Legends checks that this stays true. Everywhere else
the name is what outsiders say: a Kansas City court, the bounty men, a witch hunter, the saloons. Keep it that way
at the table. A player should hear the words Long Table from a bounty man or from Crail long before a woman of a
house will so much as nod at them, and she never will.

What the papers show is the hallway. The stories behind them are the houses, one at a time, and the one
thing the Keeper's Book leaves the Keeper to decide is what the ninth children are for. [[ref:will]] offers
two ways to hold it, and whichever the Keeper picks should be used everywhere the houses appear.
""")

entry("stand",
      callings=["Witch"],
      people=["the woman of the house on the Bayou Courtableau"],
      places=["Opelousas, Louisiana", "the Bayou Courtableau"],
      creatures=[],
      threads=["witch", "harrow", "houses", "tithe"],
      when=[(1840, "A birthing house on the Bayou Courtableau is seated at the Long Table"),
            (1881, "The house on the Bayou Courtableau is asked to stand")],
      story="""
The woman at Opelousas kept a birthing house for forty-one years, and no woman in that parish who came to her door came away
worse, and the Table was obliged to her. In 1881 she was asked to stand. What she'd done was answer a question. The Table asked
her, as it asks every house now and then, whether anybody in her parish owed it anything it hadn't been told of, and she said no,
and it was a lie. There was a family on the bayou with a ninth child coming, and she'd delivered the other eight and loved them,
and she'd kept the count wrong in her book for eleven years.

Being asked to stand is what the Keeper's Book says nobody will talk about, and what follows it is nothing a marshal could charge.
The house isn't kept any more. The Table's protection goes off it the way a lamp goes out in another room. The springs she tended
went to another house. The births went to the parish doctor, who is a good man and forty miles off. And the parish, which knows
without being told the way a parish knows, stopped buying her eggs.

She's alive, on the same bayou, in a smaller house, and keeps chickens. The family with the ninth child moved to Texas in 1882,
and the Table knows exactly where.
""",
      open=[("What became of the ninth child she hid?",
             ["The Ninth Child came to the family's porch in Texas the September after, with the dates, which were right.",
              "Nothing yet. The Table honours a correction, and she's the only one who can make it, and she won't."]),
            ("Would she talk to a posse?",
             ["About chickens, gladly. About the Table, once, if they bring her something from the family in Texas.",
              "No. Standing means silence, and she's kept it."])],
      table="""
Nobody in the parish will sell a posse an egg of hers either, and a player who buys one anyway has done more for her than anybody
in four years. The card is in her sewing box. She'll show it to somebody who asks about the family, not about the Table.
""")

entry("tithe",
      callings=["Witch"],
      people=["M. C.", "R. C.", "a man in Placerville", "his wife"],
      places=["Grass Valley", "Placerville"],
      creatures=[],
      threads=["ninechairs", "witch", "stand", "will"],
      when=[(1874, "A seated house above Grass Valley begins sending its tithe twice a year"),
            (1877, "A man in Placerville, named twice in a house's tithe, dies in the summer")]
      ,
      story="""
M. C. and R. C. are a mother and a daughter who kept a seated house in the Sierra above Grass Valley, and the account book is
theirs. What a house sends the Table twice a year is small, and it's never the point. Honey from the first taking. A few dollars.
Salt. A truthful answer when one is asked. A lock of hair from every child born in the house since the last time, which is how the
Table keeps its count of families, every one of them, living and dead. That's the column of eleven locks in the spring of 1875.

A name is something else. When a house sends the Table a name, the house is asking for something, and it's the only way a house
ever asks. M. C. sent the name of a man in Placerville in the spring of 1876 because his wife had come to the house three times
that winter with her face broken. Nothing happened. M. C. died that summer and the house was excused its Michaelmas tithe for the
burying. R. C. sent the same name in the spring of 1877, and that summer the Placerville paper reported the death of a man who beat
his wife, which isn't an unusual item in any paper.

The houses don't write the Table's name, even in their own books. Both columns are headed with a drawing instead, an oblong with
its chairs down both sides, too many to count by lamplight, and the facing column adds only the word <em>from</em>. It's empty
for seven years because what the Table sends back isn't entered. Nobody in a house writes down that a man in Placerville died. In the autumn of 1880 R. C. sent honey and asked for nothing, and sent it
anyway, because she had begun to understand what the column would have held.
""",
      open=[("Did the Table kill the man in Placerville?",
             ["Yes, and the wife never knew who to thank, and has been kept by the house since.",
              "No. The Table doesn't do that, and he died drunk in a creek, and R. C. has believed for seven years that she "
              "killed him with a name.",
              "Nobody ever will say, which is how the Table prefers it."]),
            ("Why did R. C. send honey for nothing?",
             ["Gratitude.",
              "Fear. A house that has asked twice has learned what asking costs, and sends honey to keep the account even."])],
      table="""
The account book is what a posse wants if they need to know how the Table works without meeting anybody from it. R. C. lent it to
Ashby for one night and asked for it back at breakfast, and she'll do the same for a posse who has done her house a service. The
woman from Placerville still lives near Grass Valley, and she might be the service.
""")

entry("witch",
      callings=["Witch"],
      people=["the witch of the Cross Timbers (name withheld)", "her grandmother's grandmother"],
      places=["the Cross Timbers, Texas", "the Trinity"],
      creatures=["The Witch"],
      threads=["will", "ninth", "harrow", "afraid", "ninechairs", "notours", "seats"],
      when=[(1882, "A witch in the Cross Timbers answers Ashby's question about the Table by return of post")],
      story="""
She keeps a birthing house on the Trinity, and the roof doesn't leak, and no woman has died in it in eleven years, and the county
doctor sends her the ones he can't manage. She's a seated woman of a line that has had a chair at the Table since her
grandmother's grandmother, and she has sat in it twice, and she'd as soon not sit in it a third time, because the second time was
to be asked a question about her own sister.

Everything in her letter is true, and she wrote it on a bad night, the week she'd been asked about her sister, to the one
outsider who had asked her a straight question. A month later, rested, she asked for it back, because a letter is a thing that
lasts and a house doesn't write the Table down. Ashby sent it back and kept his copy, and the copy is the only paper from a house
anywhere in the Book of Legends that names the table. The Mother is no face of the Old Dark, nobody asks her for anything,
and a woman who tried to pray to her would be put out in the road. What a house owes is a hearing, something twice a year, and a
true answer. She knows how many chairs there are and bet on the number in her head while she wrote the letter and wouldn't put it
on paper, and a Keeper who has decided on nine should let her have been right.

She wouldn't talk about the children in a letter, and that's the one place the Keeper's Book leaves the Keeper a decision nobody
else can make. Whatever the Keeper decides the ninth children are for, she's the one who knows, and she would have told Ashby over
supper, and he wouldn't have liked it, and he'd have stayed.
""",
      open=[("What would she have told Ashby about the children?",
             ["The answer the Keeper has decided for [[ref:will]], plainly, over supper, with the lamp between them, and then "
              "she'd have asked him for a truthful answer of his own.",
              "That she was a ninth child herself, and was taken at two, and was loved, and has never once wished to go back "
              "to the family she was taken from, and that that's the worst of it."]),
            ("Why did she answer at all, and then ask for it back?",
             ["She'd been asked about her sister that week, and wanted one person outside to know what a house is. When "
              "she'd slept, she remembered what a house owes.",
              "Because she liked his question, and nobody had asked it straight in forty years. The house asked for the "
              "letter back, not her, and she wrote the second note in its words."])],
      table="""
She's the Long Table's face for any posse that needs one, and she should be played the way she writes: courteous, dry, entirely
unafraid, and kind to anybody in trouble. Sit down with her and she'll talk about the children, and the players won't like it,
and they'll stay to supper anyhow, because everybody does.
""")

entry("sister",
      people=["Sr. M. A.", "Bernadette, Sister", "the women of the house across the river"],
      places=["a mining camp in Colorado"],
      creatures=["The Dread Mother"],
      callings=["Sister"],
      threads=["houses", "hear", "ninth", "witch", "notours"],
      when=[(1882, "A Sister of a nursing order at a Colorado mining camp writes to her Mother Superior about the house of "
                   "women across the river"),
            (1884, "Sister Bernadette dies; the house across the river sends flowers before anybody has told it she was "
                   "ill")],
      story="""
Sr. M. A. is what the Player's Book calls a Sister: sent by her order where the diocese wouldn't go, to nurse a fever in a
mining camp, and good at it. The house across the river is a seated house of six or seven women, and it nursed the same
fever and lost fewer, and gave her quinine and wouldn't be paid, and asked after the order's dead by name.

She's honest enough to say she can't find the difference in the work, and the difference isn't in the work. The house is
kept by the arrangement [[kb:powers-mother]] describes, and the price is generational and paid by people who never agreed to
it. The miners know the difference is in what the house asks for afterward, years afterward. They won't tell a Sister,
because they're frightened of the house and fond of it at once, which is how everybody near one feels.

The flowers in 1884 are the most secret thing in the chapter. A house knew a Sister was going to die before her own order
did, and sent flowers the morning of it, out of courtesy.
""",
      open=[("What will the house ask the order for?",
             ["Nothing. The order isn't kept by the house and owes it nothing, and the house knows it, which is why it can "
              "afford to be generous.",
              "A Sister. In twenty years the order will have a house of its own at that camp, one of its novices will have "
              "been born across the river, and the house will ask her to come home."])],
      table="""
A Sister in the posse is the right soul to cross the river with an empty quinine bottle and come back troubled. Play the
house exactly as she found it: clean, kind, competent, asking nothing. The horror arrives years later, in a letter.
""")

entry("hear",
      callings=["Witch"],
      people=["a woman of a house in Missouri", "her aunt", "a woman at Natchez", "the sanitary inspector, Second District"],
      places=["New Orleans", "below Canal Street", "Hermann, Missouri", "Natchez"],
      creatures=["The Dread Mother"],
      threads=["witch", "belts", "hotel", "stand"],
      when=[(1878, "In the fever of September, one house on a square below Canal Street reports no sickness"),
            (1879, "A witch of a Missouri house goes down to New Orleans to hear the Mother and comes back changed")]
      ,
      story="""
Going down to hear her is what the covens call it, and the Keeper's Book says a witch who has gone comes back changed in some
small way her own coven can see and won't discuss. The Missouri aunt went in the spring of 1879 and came back in June the same in
every way anybody outside her house could name, and her house could see it, and it's theirs.

What a witch hears in the courtyard is a question. She's asked one thing and answers it truthfully, as a seated woman owes the Table,
and the Mother thanks her, and that's the whole audience. The two accounts that disagree about what the Mother looks like agree
about the one thing that matters, which is the question and the hands. What a witch is changed by is her own answer, heard aloud in
that courtyard. Nobody who has gone will say what she was asked. It's always the one question she'd have given anything not to be.

The sanitary inspector in the fever of 1878 is the only person in the chapter who went near the house on somebody else's business,
and he saw a courtyard. It was clean. The shutters were closed in September. There was a good deal of coming and going at the gate
after dark, all of them women, and every one of them was carrying somebody sick, and nobody carried out of that gate died of the
fever that year.
""",
      open=[("What does the Mother look like?",
             ["[[kb:powers-mother]] says to keep her at the end of the hallway, and this book won't put her on stage. Every "
              "witness describes a different woman and the same hands. Keep it that way."]),
            ("What was the Missouri aunt asked?",
             ["Whether she'd have given her own daughter, if the dates had come to her door. She said yes.",
              "Nobody knows, and her niece has decided not to ask."])],
      table="""
Don't send a posse down to hear her. If a player ever goes, run it as the Missouri aunt's trip: nine weeks, a courtyard, a single
question from somebody whose face they can't hold, and a truthful answer the player has to give at the table, out loud. Then let
the rest of the party notice the small thing that's different.
""")

entry("notours",
      people=["a woman who keeps a house in the Cross Timbers"],
      places=["the Cross Timbers, Texas"],
      creatures=["The Dread Mother", "Dark Cultist & the Hollow Prophet"],
      callings=["Witch"],
      threads=["witch", "creeds", "congregations", "glad", "tract"],
      when=[(1883, "The house in the Cross Timbers answers Ashby once more: the houses don't sit with the faithful")],
      story="""
This is the same woman who wrote the only letter that names the table, and asked for it back ([[ref:witch]]), and her second
answer doesn't use the word. The houses don't sit with the brothers and sisters, and the faithful don't ask. The difference
she gives is the clearest line in the Book of Legends between the two kinds of people who deal with the dark: the faithful
think the thing they love loves them back, and the houses have never once thought that about anything.

[[kb:powers-mother]] says nobody prays to the Mother and nothing is granted in her name. The houses aren't the Old Dark's,
and they know what it is. They bury the faithful who come to their doors in trouble, and are thanked, and never see them
again.
""",
      open=[("Why do the faithful never come back?",
             ["Because the houses keep what they bury, and a brother buried by a house stays buried, which is the one thing "
              "the faithful can't bear.",
              "Because they're ashamed. A sister who went to a house for help was helped by the only people in the country "
              "who never pretended the dark loved her."])],
      table="""
A Witch in the posse should feel the line this letter draws, and a Dark Cultist in the posse should feel it from the other
side. Put the two of them at a house's door together on a bad night, and let the house take one of them in.
""")

entry("ninth",
      people=["Nan (on the Neches)", "Dell (her sister)", "Lucy (Nan's daughter)", "Lucy's youngest", "Tom (Nan's husband)",
              "the Garza family"],
      places=["the Neches", "the house at the ford"],
      creatures=["The Ninth Child"],
      threads=["will", "ninechairs", "harrow", "stand", "witch"],
      when=[],
      story="""
The house at the ford on the Neches kept Nan's mother through the bad birth that brought Dell, kept Nan through Lucy, and kept Lucy
through the fever that took eleven in the county. Three generations, and the Bestiary's Ninth Child is exactly what came up the lane
at four in the afternoon on the 9th of September, having stopped at the Garzas' to introduce itself: polite, hat off on the porch,
with every date right. It asked for Lucy's youngest, who is the ninth of the line counted the way it counts, which is every child
born to the line's women, the living and the dead and the ones nobody spoke of.

Nan told Tom to put the shotgun back, and she's right that it was because the thing was polite, and she's right about something
she didn't write: a family that shoots the Ninth Child loses three generations of keeping at once and gets a second one by spring.
They said no after three nights. It put its hat on and thanked them and rode off, and stopped at the Garzas' to say goodbye.

Nothing has happened to Nan's family, and that's the point. The house at the ford doesn't answer its door to them any more, or to
anybody on their lane, and the Garza baby died in March because there was nobody else to go to. Forty years of what the house did
for that lane, unseen and never thanked, stopped the night Nan said no, and the family is learning over a decade what it was.
""",
      open=[("What can Nan offer instead?",
             ["The Bestiary gives two ways: something else the family is owed, or proof the ledger's wrong. The house keeps "
              "immaculate records and will honour a correction, and the count includes a stillborn child of Nan's mother's "
              "that may have been counted twice.",
              "Nothing. It will state the debt again this September, and the next, and it's right."]),
            ("What did the Garzas say to it?",
             ["They're one of the families in nine that said yes, two generations ago, and it stops there to see them.",
              "Nothing. They're Catholics and wouldn't have it in the house, and their baby died anyway."])],
      table="""
The Bestiary says to use this once, and it's right. The scene is the family arguing in the next room while the Ninth Child waits
on the porch with its hat off, and the posse is in the room. It's kind to the children, it's right about the debt, and the
temptation to end it with a gun should be enormous and should be wrong.
""")

entry("namebook",
      people=["Crail, A.", "a midwife of the house on the Sabine", "a woman of a seated house at Fort Worth"],
      places=["the Sabine", "Fort Worth", "Opelousas", "Lampasas", "the Neches"],
      creatures=["The Dread Mother", "The Thing in the Well"],
      callings=["Witch Hunter", "Witch"],
      threads=["terms", "commission", "harrow", "ninth", "stand", "crailtrial"],
      when=[(1884, "A leaf of A. Crail's book of names is left for Ashby at the hotel at Fort Worth by a woman of a seated "
                   "house")],
      story="""
The leaf is Crail's, torn from the oilcloth book he carries, and the house at Fort Worth left it for Ashby because Crail had
left the book with the house, and the house wanted somebody outside to see what he knew. Every line is right. The thing in
the Kessel well drinks at dusk. Josiah Merriam was not. The house at Opelousas keeps nine families and asks the ninth, and
it's the house whose card opens the chapter. Z. Harrow kept Lampasas. The house on the Neches was owed a child that
September, and the family said no ([[ref:ninth]]).

The midwife on the Sabine is the line that matters. Crail came in the rain with a lamp to finish the house, and she made him
wait seven hours in the kitchen until a girl was delivered, and he asked the child's name and wrote it down and went out. A
dollar came the next spring. That's one of his two ways of crossing a name out, and the house knows which.

He left his book with a seated house because he was about to go after Mother Harrow for them ([[ref:commission]]), and a
hunter who might not come back leaves his book with the people he'll have to trust.
""",
      open=[("Which way did he cross out the Sabine?",
             ["The kind way. The girl's name is in the book now under the house's, and Crail sends a dollar every spring.",
              "Neither, yet. The house is struck once, which means unfinished, and the dollar is a hunter paying for the time "
              "he's letting it run."])],
      table="""
Crail's book is an extraordinary thing for a posse to hold: every line a place to go and a judgment to check. The house at
Fort Worth has it now, and will lend it to a posse that's going after Crail, or after Harrow, and wants it back.
""")

entry("harrow",
      callings=["Witch", "Hexer"],
      people=["Harrow, Zilpha (Mother Harrow)*", "the boy", "a woman of a seated house at Fort Worth"],
      places=["Lampasas", "Tascosa", "Fort Worth"],
      creatures=["The Witch", "The Hexer", "The Ninth Child"],
      threads=["notice", "ninth", "will", "witch", "afraid", "commission", "namebook"],
      when=[(1879, "In her fortieth year keeping a house at Lampasas, Zilpha Harrow asks what the children are for"),
            (1884, "Mother Harrow leaves a letter for Ashby at the hotel at Tascosa"),
            (1885, "Mother Harrow is seen at Tascosa with a crow and a boy of about nine")]
      ,
      story="""
Zilpha Harrow kept a house at Lampasas for forty years, and in the fortieth she asked the Table the question none of its women
ask: what the children are for. She was told. Whatever the Keeper has decided for [[ref:will]] is what she heard, and she went home
that night, took the boy of four who was due in the morning, put him on her horse in front of her, and rode.

Her mother's craft wasn't enough to hide a child from the Table, because the Table taught it to her mother. So she went and got
something that was: she went down, the way a Hexer goes down, and asked the Old Dark for a place to keep a boy where the Table
couldn't count him, and it was available, as it always is to a tired woman with a want. She did the sums first. She knows what
it'll cost her. She keeps a crow, and the crow is part of the price.

The Fort Worth woman taught her to set a bone and knew her forty years, and her letter is the Table's side, and it's true too.
Whatever Harrow got to hide the boy with keeps what it's given. The Table has the boy's dates and what he was owed to, and Harrow
has neither, only the boy, who's nine and reads. The two letters can't both be right, and the editor can't choose between them, and
neither can this book.
""",
      open=[("Is the boy riding behind her the boy?",
             ["Yes. She saved him, and the price is hers, and he reads.",
              "The boy is kept, as the Fort Worth woman says, and what rides behind Harrow is what keeps him, wearing his "
              "face so she won't have to see the difference.",
              "Both, a little more of the second every year, and she knows."]),
            ("Who wrote 'she is not alone' under the notice?",
             ["The Table, as a warning to anybody who'd take the notice: she has the Old Dark with her.",
              "Somebody on her side. There are women who think she was right.",
              "The boy."])],
      table="""
Mother Harrow is the Long Table's great open question walking around on a horse, and a posse that meets her will be asked their
mothers' names and told they're good names. If they take the notice down, a kindness is owed them, by people who keep very good
books. If they help her, they're obliged to whatever she went down and got. The Keeper should let them see both bills before they choose.
""")


entry("commission",
      people=["Crail, A.", "Harrow, Zilpha (Mother Harrow)", "a midwife at Denison"],
      places=["Denison", "Tascosa", "Fort Worth"],
      creatures=["The Dread Mother", "The Tallyman"],
      callings=["Witch Hunter"],
      threads=["notice", "harrow", "terms", "namebook", "ninth"],
      when=[(1885, "A. Crail leaves a letter with a midwife at Denison in April offering to find Mother Harrow, for the "
                   "name of the house that kept his mother; in June he's seen at Tascosa a week behind her")],
      story="""
Crail answered the notice with no money on it ([[ref:notice]]) because he wants something only a house can give: the name of
the house that kept his mother, what it was paid, when, and where the child it was paid with is buried. He has hunted the
houses six years for that answer, this is the first time the houses have asked the country for help, and he's the only man
in the country who isn't afraid of Harrow.

He knows what Harrow went down and got, and so does the reader of [[ref:harrow]]. When her mother's craft wasn't enough to
hide a boy from the houses, she reached for something her line never taught her, and a Witch who does that has done what a
Hexer does. Crail has hunted the things that wear men and the houses both, and he's the one hunter who can follow her into
both.

Whether the houses answered is left open. Crail was at Tascosa in June a week behind Harrow, neither has been seen since, and
the pencil under the notice at Fort Worth says she is not alone.
""",
      open=[("Did the houses pay his price?",
             ["Yes. They gave him the name, and it was the house on the Neches, and the child was his sister, and she "
              "isn't buried anywhere.",
              "No. They don't sell their dead, even for Harrow, and Crail went after her anyway, because he wanted to see "
              "what she had."]),
            ("At Tascosa, who is following whom?",
             ["Crail is following Harrow, as the houses asked.",
              "Harrow is leading him. She wants a witch hunter who knows what she borrowed, to end it when the boy is "
              "safe, and she knew the houses would send the best one."])],
      table="""
This is where the houses' thread and the Witch Hunter's thread tie, and it makes a fine climax for a posse with a Witch and a
Witch Hunter in it. Put the posse at Tascosa a week behind Crail, and make them choose a side before they know what Harrow is
carrying.
""")

# ================================================================ There Is Always a Brother
intro("brother", """
This is the Old Dark from the inside, and the papers were written by people who were glad of it. The
Keeper's Book is plain about who they are: the Dark Cultist devoted to the Old Dark itself, who wants a
thing and meets the face that answers the want. The tract at the head of the chapter lists the six wants,
and a Keeper holding [[kb:olddark-devotions]] will recognise every one.

Nothing here is the basin, so the faces may be named, and where they're named it's for the Keeper. The
stagecraft rule in [[kb:olddark-why]] holds over every entry: never let the Old Dark be seen to want. Let it
be available. Every paper in this chapter is somebody finding it already there, already the easiest thing
in the room.
""")

entry("tract",
      callings=["Dark Cultist"],
      people=["the man who paid in coin", "the printer at Pueblo"],
      places=["Pueblo", "the Denver and Rio Grande towns"],
      creatures=["Dark Cultist & the Hollow Prophet"],
      threads=["sign", "sawbones", "glad", "hexer"],
      when=[(1882, "A job shop at Pueblo prints four thousand copies of 'A Word to Those Who Are Tired' for a man who "
                   "pays in coin")],
      story="""
The man who paid the printer in coin is the man Ashby met at Trinidad two years before ([[ref:sign]]): fifty, a clerk's hands, a
good coat. He's a Brother in the saloons' word for it, devoted to the Old Dark whole rather than to any one of its faces, which is
rarer than anybody outside would think and is why his leaflet lists all six wants. To eat, to know, to stop hurting, to keep somebody
out of the grave, to be rich, to be loved: those are the six doors [[kb:olddark-faces]] describes, and he wrote them down in the
order a tired person reaches for them.

He isn't recruiting. There's no address on the leaflet and no meeting, and nobody who reads it is asked to do anything but ask. He
leaves them in boarding-house passages in the winter because that's where the tired people are, and he doesn't need to know who
picks one up. Something will be listening. It always is. His work is only to say so out loud, somewhere a person alone can read it,
which is the most the Old Dark ever needs anybody to do.

The eleven thousand temperance tracts the same week were for him too. He paid for both, and the printer didn't notice because the
temperance man wore a different coat. Both leaflets tell a tired man to ask for help. He likes to give people the choice.
""",
      open=[("Which face does he serve?",
             ["None. He's devoted to all of it, and the face that answers each reader is the reader's business.",
              "The Whisperer, which holds correspondents rather than ground, and a man who leaves leaflets in passages is a "
              "correspondent of a kind."]),
            ("How many who picked one up asked?",
             ["The Keeper's Book won't say, and neither will he. B. in [[ref:sawbones]] was one."])],
      table="""
Leave a copy in a passage where a player's character will find it on a bad night, after a death at the table. Say nothing. The
Keeper's Book says the answer must always be allowed to be no, and mean it, and a player who reads it and throws it in the stove
has told you exactly what they hold dearest.
""")

entry("sign",
      callings=["Dark Cultist"],
      people=["Ashby, N.", "a teamster at the Crossing", "the teamster's brother-in-law",
              "the man with a clerk's hands"],
      places=["the hotel at Trinidad", "Calvary Crossing"],
      creatures=["Dark Cultist & the Hollow Prophet"],
      threads=["tract", "vessel", "satchel-road", "satchel-page"],
      when=[(1880, "Ashby turns his cup down at the hotel at Trinidad in June, and on the second night a stranger answers it")],
      story="""
The sign is real and so is the card game. A cup turned down with the spoon across it, and a question about whether the kitchen keeps
late, is how a travelling man asks at a strange hotel whether there's a game upstairs, and it's also, in certain towns, how a person
who has been looking lets it be known. The teamster's brother-in-law is a faro dealer, and a Brother, and uses the sign for both, and
doesn't find anything odd in that.

The man who sat down across from Ashby on the second night is the one who wrote [[ref:tract]]. He asked how long Ashby had been
looking, and what Ashby wanted, in the voice you'd use to offer a tired man a chair, and Ashby found he couldn't say he'd only been
curious. He said he didn't know yet. That was the truth. The man paid for his supper, and in the morning the mare was reshod, and
that's all. He never asked Ashby for anything, in four years, and Ashby waited for him to.

That's [[kb:olddark-why]]'s stagecraft done perfectly by a man. The Old Dark is never seen to want. It's available. A Brother doesn't
recruit, doesn't ask, doesn't pursue, and pays for the supper, and leaves the rest to the want. Ashby wanted to know, more than he
wanted anything, and the note in the steadier hand is a man noticing four years late that he'd been waiting to be asked because he
couldn't bring himself to ask.
""",
      open=[("Did Ashby ever ask?",
             ["No, and the satchel is the proof: a man who had asked wouldn't have needed eleven field-books.",
              "Yes, in October 1884, on the road below Saltlick, and what answered wasn't the Brother, and the answer was "
              "about his father ([[ref:satchel-road]]).",
              "The Keeper decides, and [[ref:gatherer]] offers four ends for him that each fit a different answer."])],
      table="""
Give a player the sign, secondhand, from a teamster who won't say where he had it. If they try it, run it exactly as it happened to
Ashby: nothing the first night, a stranger the second, a question, a paid supper, a shod horse. Then never ask them for anything.
Let them wait.
""")

entry("creeds",
      people=["two congregations on the Arkansas"],
      places=["a town on the Arkansas"],
      creatures=["Dark Cultist & the Hollow Prophet"],
      callings=["Dark Cultist"],
      threads=["congregations", "partners", "route", "notours"],
      when=[(1882, "Two congregations of the faithful in one town on the Arkansas give Ashby their creeds so he'll see how "
                   "wrong the other is")],
      story="""
Two congregations in one town on the Arkansas bury their dead in separate grounds and won't speak, and each gave Ashby its
creed so that he'd see the other's error. The creeds are word for word the same except for the name in the fourth line, and
the two names haven't a letter in common. The editor took both out, as Ashby's rule required, and the two papers became one.

The two names are two faces of the Old Dark, and [[kb:olddark]] has the rule this shows: there are no six rivals, and two
cults at each other's throats are two hands of one body. Each congregation is sure its face is the only one that ever
answered anybody. Both are feeding the same thing, and it keeps them apart, because a divided faithful is easier to keep.

The editor says it's the most important thing in the chapter and can't say why. The Keeper can: it's the one paper in the
Book of Legends where the players can see with their own eyes that the faces are one.
""",
      open=[("Which two faces?",
             ["The Keeper's choice. The obvious pair is the Devourer and the Red Sermon, a fat congregation and a loud one, "
              "in one cattle town.",
              "Leave it where the editor did. A posse that learns both names has learned too much."])],
      table="""
Hand the players the two creeds side by side and say nothing. A table that notices is ready for the first rule in
[[kb:olddark]]. A table that doesn't will believe the next congregation it meets.
""")

entry("gloves",
      callings=["Dark Cultist"],
      people=["the prisoner (a storekeeper at Cheyenne since)", "his hired man", "the territorial court"],
      places=["a territorial court", "Cheyenne"],
      creatures=["Dark Cultist & the Hollow Prophet"],
      threads=["sign", "vessel", "assay", "floor"],
      when=[(1873, "A homesteader finds, in the spring, what he has been looking for for nine years"),
            (1882, "He is tried in November for burying his hired man twice, and committed"),
            (1886, "He keeps a store at Cheyenne, and his hands are ordinary")]
      ,
      story="""
He went looking for nine years, from the end of the war, and found it in the spring of 1873, and has been all right since. He's
devoted to the face the Keeper's Book calls the Thing Beneath the Mountain, which works through the ground, and its gifts favour
stone and ore and the secrets of the buried: a Devotion that knows where things lie and hears the buried answer when it knocks.

His hired man died of a fever in the autumn of 1882, and he buried him on his own place without troubling the coroner, which is a
thing homesteaders do. Then he was told the man was in the wrong place. Something under his section wanted the body laid somewhere
particular, over something particular, the way a corner is set on a survey, and he dug him up and carried him and laid him there,
and would do it again, and could give the court no reason it was prepared to hear. The gloves were over the Mark, which by then had
reached his fingers and gone the colour of the rock the Thing Beneath lends its faithful.

The court found him unsound and committed him and released him eleven months later as recovered. His hands at Cheyenne in 1886 are
as ordinary as the editor's. The editor couldn't decide whether that was the end of the story or the part a reader was meant to see,
and was right not to decide.
""",
      open=[("Why are his hands ordinary now?",
             ["The asylum cured him, as it says, and he's an ordinary grocer who once had a very bad year.",
              "The Mark has gone inward, which is where Marks go at the fourth step, and he's further along than ever.",
              "The man at the store isn't him. He went back to the section in 1884 and lay down where he'd laid his hired man."]),
            ("What was the body laid over?",
             ["A corner of something large that the Golden Circle's list-maker would recognise.",
              "The top of a seam, and the Thing Beneath needed a man's bones in it to wake the rest."])],
      table="""
He sells good coffee at honest weight and asks after a customer's health. A posse that knows what he was will find him courteous,
grateful for the court's patience, and entirely unafraid, and willing to tell them where anything under the ground is, for a price
he'll name politely.
""")

entry("congregations",
      people=["Loring, Mrs. E.", "Ledyard, Mr."],
      places=["Trinidad", "Las Animas"],
      creatures=[],
      callings=["Dark Cultist"],
      threads=["creeds", "sign", "partners", "route"],
      when=[(1882, "Mrs. Loring and Mr. Ledyard answer the same sign at the same hotel on the same night, and find out "
                   "over the pie that they don't keep the same faith")],
      story="""
Mrs. Loring and Mr. Ledyard both turned their cups down at the hotel at Trinidad on the same night and met over supper, as
the sign arranges ([[ref:sign]]), and found out over the pie that the thing that answered her wasn't, in her view, the thing
that answered him. Her letter is the kindest paper in the chapter and the most frightening, because she means every word of
it: he's been deceived, it may not be too late, and she's praying to the true one for him.

He wrote back the same day in nearly the same words. They exchange cards at Christmas. Neither will ever learn from the other
that they pray to the same thing, because each is sure and both are wrong in the same way, and the Old Dark is perfectly
content to be prayed to twice.
""",
      open=[("Does it stay at cards?",
             ["Yes, for thirty years, and their congregations never learn they're friends.",
              "No. One of their congregations finds the cards, and [[ref:partners]] is what that looks like in a mining "
              "camp."])],
      table="""
This is the gentle version of the faithful at odds, and a posse should meet it before they meet the other one. Two kind
people who'd die for each other's error make a better scene than two who'd kill for it.
""")

entry("glad",
      callings=["Dark Cultist"],
      people=["Hattie (on the Republican)", "Ostrander, Mary", "Will (Hattie's husband)", "Sam and Joe (her sons)"],
      places=["the Republican River, Nebraska", "Iowa"],
      creatures=["Dark Cultist & the Hollow Prophet", "The Cold Deep's Child"],
      threads=["braid", "sawbones", "hexer", "tract"],
      when=[(1881, "Hattie, on the Republican, writes her sister that the hurting has stopped"),
            (1882, "Hattie dies in the winter, smiling")],
      story="""
Hattie lost two sons, Sam and then Joe, and couldn't sleep and then couldn't eat, and asked the Lord every night for a year and a
half, and wouldn't say a word against Him. Then she asked somebody else, out loud, in the kitchen, and the hurting stopped the way a
clock stops when you open the case and put your finger on the wheel. Her want was to stop hurting, and the face that answers that want
is the one the Keeper's Book calls the Cold Deep. It's the Quiet Kind in the Player's Book's stories.

The Cold Deep has cells, four to nine quiet kind people who turn up after a fire with blankets and no questions, and there's one on the
Republican: the fast days and the nights she sat up were with them. They're very good neighbours. None of them is afraid of anything,
including the things that ought to frighten a person, and the widows they take in stop visiting their own kin. Hattie stopped writing to
Mary. The marks were the Cold Deep's, and they didn't hurt, and she was proud of them, and the warmth went out of her a degree at a
time, the way that face takes it, until there was nothing left that could be moved.

She died in the winter of 1882 and Will says she was smiling, and she was. Mary would give a good deal to have her sad again, and that's
the only honest thing anybody in this story ever says about the Cold Deep's bargain: it's the kindest offer the Old Dark makes, and it
takes everything.
""",
      open=[("Who else in the valley has the Cold Deep taken?",
             ["Two more widows since, and a man who buried a child, and the cell has seven.",
              "The same valley as [[ref:braid]], and a Keeper who wants one valley to hold two congregations that know nothing "
              "of each other has one."]),
            ("What became of Will?",
             ["He married again and farms the place and won't talk about Hattie.",
              "The cell brought him blankets after the funeral, and he's stopped visiting his kin."])],
      table="""
A posse in the Republican valley after a death will be brought blankets and soup by kind people with no questions, and a player whose
character is grieving will be offered, gently, somewhere to sit. The Keeper's Book says the Cold Deep's moment is after the horror,
the shaking hour past midnight. This cell is very good at knowing when that is.
""")

entry("partners",
      people=["a miner of the Wet Mountains (the witness)", "his partner (the deceased)"],
      places=["a silver camp in the Wet Mountains"],
      creatures=["Dark Cultist & the Hollow Prophet"],
      callings=["Dark Cultist"],
      threads=["creeds", "congregations", "cordial", "route"],
      when=[(1883, "In May a miner in the Wet Mountains shoots his partner of four years in a quarrel over which face "
                   "answered them")],
      story="""
Two partners worked a silver claim four years without a word about it, and both were of the faithful, of two congregations
without a building between them. One night over whiskey the partner said what had answered him, and the witness said it
wasn't so, and the partner said the same about his, and went for his gun, and the witness was quicker.

The camp says it was the claim, because a claim is a thing a camp understands. The witness sold it that summer for a fair
price and went to work at the smelter for wages, which a man who'd killed for a claim wouldn't do. He killed for the face.
He's sorry the partner's dead, and certain he served the wrong one, and says the partner would want him to say so.

This is [[kb:olddark]]'s two hands of one body at their worst. The thing they both served lost nothing by it.
""",
      open=[("What did the witness win?",
             ["Nothing, and he knows it. He has begun to wonder, at the smelter, why the thing that answered him didn't "
              "seem to mind.",
              "His partner. Something has answered him in his partner's voice since May, and it's kinder than it's ever "
              "been."])],
      table="""
A Dark Cultist in the posse with a friend of another congregation should hear this inquest read aloud, and so should the
friend. It's the scene [[ref:congregations]] is one Christmas card away from.
""")

entry("uncle",
      callings=["Dark Cultist"],
      people=["the old gentleman (the uncle)", "his nephew", "his late wife (the aunt)", "the Ledger's reporter"],
      places=["the asylum at Cheyenne", "the feed store"],
      creatures=["The Whisperer's Mouth"],
      threads=["sign", "vessel", "weathersong", "agency"],
      when=[(1881, "A feed-store keeper at Cheyenne wakes knowing oats will be up by Christmas"),
            (1882, "His family commits him after he tells his wife the day she will die"),
            (1883, "The Cheyenne Ledger prints a comic piece about the learned lunatic in March")]
      ,
      story="""
He kept the feed store thirty years and lost money at it, and in the autumn of 1881 he was sitting up late over the books wishing, out
loud, that he could know for once what was coming. Something heard. It's the face the Keeper's Book calls the Whisperer, whose door is
the question, and it answers questions nobody asked aloud as a certainty arriving at the edge of sleep. Oats up by Christmas. The judge at
the April term. What the Army would pay for remounts. Then things about the neighbours nobody had told him and nobody would have.

Every answer carried one truth he didn't want and couldn't unknow, which is the Whisperer's price, and understanding doesn't fit inside a
mortal skull, so it makes room. He told his wife the day she would die because he couldn't not know it, and he was gentle about it,
and she died on it. That's the Player's Book's Somebody's Uncle, and the Ledger printed the funny version, which is the newer one.

He's calm and perfectly correct and no longer anybody's uncle. He doesn't know his nephew's name or his own. He answered the question in a
letter his nephew never posted. The Ledger's reporter married in January and his wife has a cough, and the uncle asked after it before
the man had met her. He's becoming what the Bestiary calls the Whisperer's Mouth: a person hollowed out into a vessel for a voice that
has things it wants said.
""",
      open=[("What was the question in the nephew's letter?",
             ["Whether his uncle was still in there. The answer was no.",
              "Whether the nephew would inherit the gift. The answer was yes, and the nephew has stopped sleeping.",
              "Something about the nephew's own wife, and he'll never tell anybody what the answer was."]),
            ("What will happen to the reporter's wife?",
             ["What the uncle said, on the day he said it, and the reporter will come to the asylum to ask why.",
              "Nothing, if somebody believes the uncle in time. The Keeper's Book says every answer the Whisperer gives must be "
              "true, and a true warning can be acted on."])],
      table="""
Take a posse to the asylum on visiting day. The uncle will correct them on the date, the weather and the names of their relations, and
he'll be right every time, and then he'll tell one of them something they didn't want to know. The Whisperer's Mouth's entry says to
silence it and not to listen for the rest, and a player who listens should be allowed to.
""")

entry("asked",
      people=["a harness-maker at Dodge City", "the brother at Dodge"],
      places=["Dodge City"],
      creatures=[],
      callings=["Dark Cultist"],
      threads=["sign", "route", "gloves", "committee", "clerk"],
      when=[(1873, "A man with forty cents and a bad hand turns his cup down at Dodge, and the brother finds him work by "
                   "the Monday"),
            (1884, "In March the brother asks the harness-maker for the loan of his hands for an afternoon")],
      story="""
The harness-maker came to Dodge in 1873 with forty cents, turned his cup down, and the brother sat down across from him the
second night and found him a place with a saddler. He has had his own shop since 1876, a brick front and four children, and
the brother has nodded to him every week for eleven years and asked for nothing. In March of 1884 he asked to borrow his
hands for an afternoon, and the harness-maker said yes, because he'd been waiting eleven years to be asked anything.

He lost the afternoon. He was home for supper and pleasant, and did the quarter's accounts after, and they balanced to the
cent, and there's a cut across his right palm a year healed. That's all the Book of Legends will say, and it's what the
faithful are like: a kindness that waits eleven years and then asks for something small and enormous.

What the hands did is the Keeper's. They were wanted because they were his and nobody else's: a harness-maker's hands,
steady and strong, and known in Dodge.
""",
      open=[("What did the hands do?",
             ["Wrote. A page in a hand nobody at Jubilee knows, which came in the Treasury's bag that April, because the "
              "list is never written twice in the same hand ([[ref:clerk]]).",
              "Dug. A grave in the right place for a body moved from the wrong one, the way the man in [[ref:gloves]] "
              "was told where.",
              "Held a child still for an hour while something was done that needed holding, and the cut is where the "
              "child bit."])],
      table="""
Every Dark Cultist in the posse has a brother who did them a kindness once. Let the brother ask for something small one
evening, years in, and see whether the player says yes.
""")

entry("vessel",
      callings=["Dark Cultist"],
      people=["the cowhand", "the man they called Brother", "the justice at Tascosa", "a Methodist elder at Mobeetie"],
      places=["the Canadian River", "Tascosa", "Mobeetie"],
      creatures=["The Possessed", "The Whisperer's Mouth"],
      threads=["sign", "uncle", "revival", "gatherings"],
      when=[(1884, "A cowhand gives an account at Tascosa of a night meeting on the Canadian where something looked out of a man")],
      story="""
Eleven people and a good supper by a fire on the Canadian, and afterwards the man they called Brother stood up and said he'd be carried a
while. He's a Brother of the Old Dark entire, like the tract-writer at Pueblo, and what carrying means is that he opens himself and
lets it look out. It isn't a trance and it isn't a preacher's fit. His face goes still all at once, the way a stock tank goes still when
the wind drops, and something that has never been in a hurry looks at eleven people through him.

It was looking for somebody. It looked each of them over the way a man looks over stock he's thinking of buying, and it stopped at the
cowhand a good while, because the cowhand was the only one at that fire who hadn't already been found. The other ten were its. The
cowhand had come for the supper. The Old Dark doesn't pursue and never will, so it did the only thing it does: it noted him. When the
Brother came back he was crying and happier than he'd ever been, and the others were glad for him, and the cowhand got his horse.

He went to the justice because nothing that happened was against the law, and that's what he keeps coming back to. The Methodist elder is
right too: the Cane Ridge meetings in 1801 had people lying still while their neighbours watched, and nobody thought it was anything but
the Lord. Neither man thought the other was lying. The difference between them is what was looking out, and neither of them could see it.
""",
      open=[("What does it want with the cowhand?",
             ["Nothing yet. It has noted him, and on the worst night of his life it'll be there, already open, the easiest "
              "thing in the room.",
              "It wants him because he refused. The Keeper's Book's fourth reading of why it answers holds that it wants "
              "something in particular that it can only get through a man who asked, and it's patient."]),
            ("Where are the other ten?",
             ["Going up into the mountains that spring, in a bunch, the way the Wind River witch describes ([[ref:afraid]]).",
              "Still on the Canadian, eating well, and the Brother is carried every month."])],
      table="""
A player can be the cowhand. Put them at a fire with a good supper and ten pleasant people, and let the Brother be carried, and let it
stop at them a good while. Then give them their horse. The Keeper's Book says a table that turns the Old Dark down flat has just told
you what they hold dearest, and the dark was listening, and so were you.
""")


# ================================================================ What the Country Stands On
intro("depth", """
Ashby kept these in an oilcloth and called them his deep papers, and they're about size: how far a plain runs,
how deep a well goes, how many stars there are, how big a crossroads is inside. Two of them are the Keeper's
Book's own open question about the gatherings in the Rockies, and [[kb:olddark-rockies]] has its four
readings and its one rule: don't answer it early and don't answer it twice. Nothing below answers it.

The rest are the country itself being larger than the maps, and a Keeper should resist making any of them
smaller by explaining. Each entry gives the story behind the paper and stops where the paper stops. The
Bestiary's largest things are here, and the right way to use most of them is never to put them on the table
at all.
""")

entry("llano",
      people=["Farrow, J. D. (deputy surveyor)", "the land company's office"],
      places=["the Staked Plain", "the Yellow House"],
      creatures=[],
      threads=["spaniard", "crossroads", "bird", "street"],
      when=[(1881, "J. D. Farrow runs a line across the Staked Plain east and back in July; it's three miles longer going east")],
      story="""
J. D. Farrow ran the line east from the monument at the Yellow House in July 1881 for a land company that wanted the Staked Plain in
sections, and he's a careful surveyor with a true chain. Seventy-one miles and forty chains east. Sixty-eight miles and twelve chains
back on his own flags. Seventy-one and forty again the next day, himself on the chain, and his party paced it both ways and got his
figures.

The Llano is larger going east. The Spanish chronicle that lost a party on it in 1541 says a man loses sight of his own camp within a
league, and the Mad Spaniard's own story in [[kb:legends-spaniard]] is of a plain that ran out past every estimate and then ran out
further. Something about that country adds ground to anybody travelling east across it. Three miles and twenty-eight chains in
seventy-one is the most anybody has measured, and anybody who has walked it without a chain has only felt that the far side took a
long time coming.

The office wrote chain error, took the mean, paid Farrow, and didn't engage him again. That's the land company's answer to everything
in this chapter, and it's the only answer a company can afford. Farrow surveys in Kansas now, where the corners are square.
""",
      open=[("Why is it longer going east?",
             ["Nobody can say, and a Keeper shouldn't. The country is larger than the maps, and the Llano is where it shows.",
              "Because the plain remembers the entrada that went east across it and never came back, and makes room for it.",
              "Because the extra ground isn't the Llano's. It's somewhere else's, lent, and the three miles are where the two "
              "touch."]),
            ("Has anybody tried going further east than the monument?",
             ["No surveyor. A comanchero told Farrow that the plain gets longer the further you go, and that his grandfather's "
              "party went on until the grass stopped closing behind them."])],
      table="""
Farrow's field-book is the handout. A posse crossing the Llano east should arrive a day late with every man sure of his count, and
nothing else should happen. A Keeper who adds anything to the extra three miles has made them smaller.
""")

entry("gatherings",
      people=["Kinnear, W. F.", "his wife", "the head office at Chicago"],
      places=["above the Boulder River, Montana", "Denver", "a dry lake in the Sawatch", "above Leadville"],
      creatures=[],
      threads=["gold", "afraid", "floor", "vessel", "hotel", "belts", "evergreen", "principles", "ashbyfile"],
      when=[(1884, "An Agency operative files a report from Denver in June on four camps in the high country; Chicago "
                   "returns it NOT CREDIBLE and transfers him")],
      story="""
This is the Keeper's Book's own open question, told by the one man who has seen more of it than anybody, and [[kb:olddark-rockies]]
has the four readings. This entry doesn't pick one and doesn't lean.

W. F. Kinnear was engaged by a mining company to learn who was trespassing on a claim above Leadville, and he spent eleven weeks in the
high country following the question wherever it went, and it went to all four camps. A congregation out of Montana wintered above the
Boulder River three hundred strong and came down in good flesh. A revival leaves Denver every spring and comes home about forty short,
and nobody in Denver reports the forty missing. Nine men camped nine weeks at a dry lake in the Sawatch and swept the bed in rings, and
sheep won't go onto it. And the claim above Leadville is a hundred and sixty acres of slope with no ore on it, bought for eleven thousand
dollars in gold, with a shaft on it that well-paid men are sinking without being told what for.

The company that engaged the Agency owns the claim. It hired a detective to find out who was sinking a shaft it was paying for, which
the editor couldn't make come out any way that wasn't frightening or stupid. The company belongs to the Golden Circle, and the claim is
a line on the Circle's list ([[ref:gold]]), and the Circle's officers don't know why they bought it or who's directing the digging. They
hired the Agency to find out. The operative found out more than they wanted, and the head office wrote NOT CREDIBLE, and he's at Pueblo,
and his wife calls it something else.
""",
      open=[("Which reading?",
             ["[[kb:olddark-rockies]] has four and asks the Keeper to pick one, write it inside the screen, or leave it unpicked "
              "and let the players' guesses settle it late. This book offers nothing beyond them."]),
            ("What does Kinnear believe?",
             ["That all four are waiting for the same thing. He wrote it in 1884, and wrote in 1886, after he'd left the "
              "Agency, that it was still his opinion ([[ref:ashbyfile]]).",
              "That the shaft above Leadville is what the other three are waiting on, which he left out of the report "
              "because he couldn't prove it."])],
      table="""
[[kb:powers-together]] promises that the Pinkerton assigned to a posse will have compiled a better account of the gatherings than the
players have by the end, and won't be believed by a soul in Chicago. This is that man. Let the players find him at Pueblo when they have
three of the four camps and need the fourth.
""")

entry("afraid",
      callings=["Witch"],
      people=["a seated house in the Wind River country", "a seated house on the Brazos"],
      places=["the Wind River country", "the Brazos"],
      creatures=["What the Old Dark Is Afraid Of"],
      threads=["gatherings", "witch", "harrow", "vessel"],
      when=[(1884, "Ashby asks two seated houses a thousand miles apart whether the Old Dark is afraid of anything")],
      story="""
Ashby put one question to two seated houses in the same week, and got the Long Table's great quarrel in two letters. The Table doesn't
agree with itself about this, which is the most important thing a Keeper can learn from these papers: it isn't one mind, and its
houses are old enough to have opinions of their own and to insult each other in writing.

The Wind River house says yes. The Old Dark's people have been going up into the mountains in bunches for four years with nobody telling
them to, the way cattle go up a draw ahead of weather, and the old women have been saying since before the railroad reached Denver that
something has frightened it. Neither letter writes the Table's name, which is how the houses keep it. That's the fourth of the Keeper's Book's readings of the gatherings, and the Bestiary's entry called What the
Old Dark Is Afraid Of is written thin for exactly that reason: it's one reading out of four.

The Brazos house says the Wind River woman is a fool from a house that should have been asked to stand years ago. Nothing down there is
frightened, because fright is for things that can be hurt, and a person who thinks of it as an animal does so because she is one. The
Brazos woman has lived next door to it sixty years. Her last line is the one that kept the editor up: she'd sooner the Wind River woman
were right, because a frightened thing can be dealt with.
""",
      open=[("Who's right?",
             ["[[kb:olddark-rockies]] leaves it to the Keeper, and the Bestiary's entry is one of the four readings, and this book "
              "won't break the tie. The two houses are how a table hears the question argued by people in a position to know "
              "and in no position to be trusted."]),
            ("Why do the two houses disagree so bitterly?",
             ["Because the Table itself is divided, and the Wind River house speaks for the half that has the Mother's ear.",
              "Because the Brazos woman taught the Wind River woman, forty years ago, and has never forgiven her for leaving."])],
      table="""
Two seated women who despise each other are a gift to a Keeper: a posse can carry a question from one house to the other and back and
get a better argument each time. Neither will lie. Both are certain. Let the players pick a side, and don't tell them whether they
picked right.
""")

entry("breathing",
      people=["Tate, C. H. (well-borer)", "Pettibone, Mr.", "the professor of natural philosophy at Lawrence", "his widow"],
      places=["the Cimarron, in the Neutral Strip", "Lawrence, Kansas"],
      creatures=["The Stone Giant", "Servant of the Deep Dark"],
      threads=["floor", "dugout", "gold", "crossroads"],
      when=[(1882, "C. H. Tate bores into a void at 340 feet on Mr. Pettibone's range in the Neutral Strip in August, "
                   "and caps a well that breathes"),
            (1883, "A professor from Lawrence sees the well in May and has nothing to add")]
      ,
      story="""
C. H. Tate had bored four blowing wells in Kansas and knew exactly what one was, and this wasn't one. At three hundred and forty feet on
Pettibone's range in the Neutral Strip the bit dropped eleven feet into nothing, and a lantern let down on a line lit nothing, no sides,
no bottom, no water. The well breathed out four minutes and in four minutes whatever the glass was doing, steady as a sleeper, and the
draws were getting longer. On the ninth day the air coming up was warm and on the tenth it was wet. On the eleventh he bolted a ton of
iron plate over the casing, and on the out-breath the plate lifts a quarter of an inch.

Something is asleep under the Neutral Strip, far down, and it's very large, and a sleeper whose breaths are getting longer is a sleeper
going deeper, or coming up. Tate didn't wait to find out which. He capped it, refused his fee for the last hundred feet, and left his
tools.

The professor came in the spring of 1883 with a barometer and a watch and stood on the plate. What he saw was the plate lifting in time
with his own breath: out when he breathed out, in when he breathed in, for as long as he stood there. He went home and wrote that he had
nothing to add, and asked not to be quoted, and kept a barometer by his bed for the rest of his life and tapped it every night before he
put out the lamp, to be sure there was still something in the room breathing that wasn't him.
""",
      open=[("What's under the plate?",
             ["Something the size of a country, asleep, and the Neutral Strip is where it's nearest the surface.",
              "The long room ([[ref:dugout]]), and the breath is all of them breathing at once, facing the wall.",
              "The thing whose hand the basin's padres pinned, or its neighbour. A Keeper who wants the whole continent to be "
              "one body has a lung."]),
            ("Is Pettibone's section on the Circle's list?",
             ["Yes. One of the three names cut out of the page, and the Circle has made him an offer he doesn't understand.",
              "Not yet. It's one of the two lines marked not yet."])],
      table="""
Pettibone paid for a well and got a letter, and he'll pay a posse to go and look at the plate and tell him whether he can sell the section.
Let them stand on it. Ask each player whether they're breathing in or out. Don't say why.
""")

entry("street",
      people=["Dietz, Mrs. Anna", "Doane, Mr.", "the Mayor of Hessler", "the persons renting the Kemper premises"],
      places=["Hessler", "Front Street, Hessler", "the Kemper premises"],
      creatures=["The Wound in the World", "The Answering Voice"],
      threads=["llano", "crossroads", "gold", "drifter"],
      when=[(1883, "Persons renting the Kemper premises at Hessler hold a meeting on 19 January and leave the next day; the "
                   "council closes the block on 4 March")],
      story="""
The persons renting the Kemper premises on Front Street at Hessler were a cell of five who'd come up from Denver in the autumn with a
purpose, and on the night of 19 January 1883 they held the meeting they'd come for. It was a working, and it worked a little. They thinned
the block. The Bestiary's Wound in the World is a hole torn right through, where reality fails outright, and this is a scratch: a place
where the country is worn thin enough that time runs slow and shadows fall toward the sun and a horse won't walk.

They left the next morning and paid their rent to the end of the quarter, which is what a careful person does who has finished a job and
wants no one asking after them. What they wanted was to see whether it could be done, and where, and how much, and they wrote it down and
took it to somebody.

Mrs. Anna Dietz over the saddlery hears her own name called from under the floor at three in the morning in her own voice. That's the
thing the Bestiary calls the Answering Voice, come up through the thin place, learning. The council closed the block because it's
satisfied it can't be put right, and it's correct. Mr. Doane dissented on the ground that it's only a street, and was elected mayor, and
means to open it again, and the question is whether he's a fool or knows exactly what he's doing.
""",
      open=[("Who were the five, and who did they report to?",
             ["A cell of the Open Eye out of Denver, testing a rite before they try it somewhere larger.",
              "People working for whoever wrote the Circle's list, and the Kemper premises is one of the three names cut out "
              "of the page.",
              "Nobody the Keeper has to decide. They're gone, and the street is what they left."]),
            ("What does Doane want?",
             ["To prove it's only a street, because he's afraid it isn't.",
              "To rent the Kemper premises himself. He's had a letter."])],
      table="""
Ashby walked the block against everybody's advice and came off it eleven minutes slow without knowing how long he'd been on it. Let a
posse do the same, and ask them afterward what time they think it is. Mrs. Dietz would move if she could afford it. She'd pay a posse to
sit up in her rooms and find out who's calling.
""")

entry("plenty",
      callings=["Prospector"],
      people=["Wickersham, Abel", "Lamar, T.", "Voight, G.", "Fitch, Justice", "Cady, Mrs.", "the three hundred and twelve"],
      places=["Plenty, Colorado", "the San Juan country", "Durango", "Denver"],
      creatures=["The Unmade"],
      threads=["street", "llano", "crossroads", "assay"],
      when=[(1876, "Abel Wickersham locates the Plenty lode in the San Juan country"),
            (1880, "The census counts 312 souls at Plenty"),
            (1881, "Wickersham sells his share for a dollar on 5 March and leaves on the Saturday stage; the Plenty post office "
                   "is discontinued from 30 June"),
            (1885, "The territorial census finds the townsite and no inhabitants")]
      ,
      story="""
Abel Wickersham located the Plenty lode in 1876 and lay down on the claim that night and dreamed the town, and it was there in the morning.
He was a lonely man who'd prospected alone for twenty years, and what he dreamed was everything he'd wanted: a post office, two churches, a
weekly paper, a justice who was always fair to him, and three hundred and twelve people who knew his name. The census came in 1880 and
counted them, because they were there. They had cows and socials and a paper that reported the cows.

His partners wanted his third of the lode, and they had him before Justice Fitch in March 1881 on the ground that a man who says the town
is a dream he's having is of unsound mind. The justice, who was part of the dream, found him sane. But Wickersham had said it out loud in a
courtroom, and a dream said out loud is a dream half woken from. He sold his share for a dollar two days later and asked to have it written
that he'd leave the camp the same day, because he knew what would happen when he did and he couldn't bear to be there for it.

He left on the Saturday stage, and the Clarion's last number said the week was quiet and the cow was found. By June the post office had
nobody to run it. By 1885 there was a townsite and no sign of anybody leaving it. He hasn't dreamed since. The editor looked a year for any
of the three hundred and twelve and found none.
""",
      open=[("Were the three hundred and twelve ever real?",
             ["Yes, while he dreamed them. The census counted them, and the census is the only paper they're in.",
              "Yes, and they're still somewhere, in a town that's only real while somebody's asleep, and Wickersham's partners "
              "Lamar and Voight are in it with them.",
              "They were real people, and something the Bestiary calls the Unmade took them, and Wickersham's dream is the story "
              "he told himself because the other one was worse."]),
            ("What happens if Wickersham sleeps on the claim again?",
             ["Plenty comes back, the morning after, exactly as it was, and nobody in it knows they were gone.",
              "Something comes back, and it isn't Plenty."])],
      table="""
Wickersham is at Denver, sober and pleasant, and he'll talk to a posse about the town the way a man talks about a woman he left. If they
take him back to the claim and he lies down, the Keeper had better know which answer above is true before morning.
""")

entry("crossroads",
      people=["Kyle, Anson", "Paley, Mrs. Rhoda", "the Ivey brothers", "Dansby, Will", "Farr, Jonas", "Cotter, Mary",
              "Stoll, Ephraim", "the deputy surveyor", "the county clerk (1877)"],
      places=["the crossroads at Twelve Mile", "the Smoky Hill", "Stockton, California", "Hays"],
      creatures=["The Crossroads Man"],
      threads=["undertaker", "gold", "llano", "street", "breathing"],
      when=[(1868, "A drover goes missing at the crossroads at Twelve Mile on 21 December, the first on the county's page"),
            (1873, "Mrs. Rhoda Paley goes missing at Twelve Mile in June; her lantern is found lit"),
            (1879, "Jonas Farr goes to the crossroads on 20 March, rides to Denver, and writes from California"),
            (1883, "Deputy Ephraim Stoll goes to the crossroads on 21 December to stop the talk and doesn't come back")]
      ,
      story="""
Where the old military road crosses the drovers' trace on the Smoky Hill, the section lines jog on a correction line and the roads never
meet square, and the four corners measured by transit come to three hundred and sixty-one and a quarter degrees. There's a degree and a
quarter more inside that crossing than there is round the outside of it, and at the turnings of the year, within two days of a solstice or
an equinox, the extra room opens.

The Bestiary's Crossroads Man is there when somebody comes with a need too big to fill honestly. He's patient, courteous, and terribly
accommodating. Most of the county's page are people who came to the crossing at midnight at the right season wanting something, and got
it, and went with him. The hat on the signpost, the lantern lit with the oil not down, the shoes side by side at the corner and the badge
pinned to the post are what they left, the way people set something down when they've decided. The chainman laid his chain straight across
the crossing because he'd gone to measure it and it was the only thing he could think of to do.

Jonas Farr is the proof that it can be refused, and the clerk of 1877 was right to write the dates in the margin. Farr came at midnight on
20 March 1879 wanting to be gone from a wife at Hays and two banks and a man who meant to shoot him, and he was offered it, and he said no
and rode straight through to Denver on his own horse, and got what he wanted anyway, which nobody else on the page managed. Stoll went on 21
December 1883 to put a stop to the talk and didn't want anything, and that's the one the Keeper should think about.
""",
      open=[("What did Ephraim Stoll want?",
             ["Nothing, and a man who comes to the crossroads wanting nothing is the one the Crossroads Man can't refuse.",
              "To know. He'd read the county's page and wanted to know what the missing had gone to, and he found out.",
              "To stop it, and he's bargaining with it still."]),
            ("Is the crossroads on the Circle's list?",
             ["Yes: forty acres, nine thousand dollars in gold, one of the names cut out of the page.",
              "No. The Circle's list-maker won't buy it, which is the most frightening thing about it."]),
            ("Who's next on the page?",
             ["The next date is 20 or 21 March 1884, and the editor didn't print the page past 1883.",
              "Somebody the players know."])],
      table="""
The county's page is the handout, with the clerk's margin struck out. A posse at Twelve Mile at midnight on a solstice meets the Crossroads
Man, and his entry says how he's beaten: refuse, or bind him to terms he didn't foresee, and never speak your true name. Farr's letter is
the proof that refusing works, and a player who reads it before they go has a better chance than Stoll had.
""")

entry("eclipse",
      people=["the former pupil (name cut away)", "Loomis, Miss", "the astronomers at Separation and Denver"],
      places=["Denver", "Separation"],
      creatures=["The Eye Between Stars", "The Star-Spawn"],
      threads=["hiddenstars", "gold", "gatherings", "bird"],
      when=[(1878, "The shadow of the moon crosses the Territories on 29 July; a college party of young women observes at Denver"),
            (1884, "A former pupil writes to her teacher, before her May wedding, about what she saw in the eclipse")]
      ,
      story="""
The eclipse of 29 July 1878 crossed the Territories from Montana to Texas, and two professional astronomers reported a new planet near
the sun that afternoon, one at Separation and one at Denver, and within a few years nobody believed either of them. Each is held to have
seen two stars he didn't expect. That's the real history and it's the kindest reading of what happened.

The young woman at Denver was sketching every star in the quarter below the sun for the gentlemen looking for the planet, and she saw more
of them than there were. They were arranged, a pattern very much larger than the sky of which she could see a corner, and they were near,
the way a lamp is near across a field at night. The Bestiary's Eye Between Stars does one thing: it looks, and being seen is the harm. For
two minutes and forty seconds, with the sun put out, the sky was open on the side that faced her, and she looked into it, and something the
size of the arrangement looked back and noticed the small bright thing that was her.

She drew the chart, because she couldn't remember the rest, and she's tried every night for six years, and she thinks she's about to. She
married in May and has three children and keeps the blinds down at night, which a great many people do. Her teacher cut her signature off
the letter before she sent it to Ashby, and was right to. The Eye forgets small bright things slowly, and it helps not to be written down.
""",
      open=[("What is the arrangement?",
             ["A corner of the same figure the Golden Circle's parcels make on a map large enough to hold them, seen from above "
              "([[ref:gold]]).",
              "Nothing that fits on a map. It's the Eye, and she saw its lashes.",
              "Two stars nobody expected, as the astronomers saw, and a frightened nineteen-year-old's memory."]),
            ("What happens if she remembers?",
             ["Her children draw it too, the next morning, without being shown.",
              "The blinds won't help. The Eye's entry says to close the sky and pray it forgets."])],
      table="""
Miss Loomis will tell a posse the former pupil's married name if they convince her they mean no harm, and they should think hard about
whether that's true. A woman with three children who has kept the blinds down for six years has earned the right not to be asked.
""")


entry("ashbyfile",
      people=["Ashby, N.", "Kinnear, W. F."],
      places=["Saltlick Station", "Calvary Crossing", "Pueblo", "Yuma"],
      creatures=[],
      threads=["principles", "gold", "satchel-ticket", "satchel-road", "clerk", "understanding"],
      when=[(1884, "The Land Office reports Ashby in September for asking after cash entries by unnamed principals, and "
                   "the Department of Justice opens a file on him"),
            (1885, "The Department closes the Agency's file on Ashby in February, the week after Kinnear asks to go and "
                   "look for him")],
      story="""
Ashby came to the Agency's notice the way anybody does who starts writing Redemption down. He asked three land offices about
cash entries by agents of principals not named, he'd bought a page of the Circle's schedule at Yuma, and the Land Office
reported him to the Department, which engaged the Agency. Kinnear had met him at Pueblo in the summer and liked him, and
found him candid, careful and without political connection, which in a file is a compliment.

The file is the last thing Washington wrote about Ashby, and it ends the way its papers about Redemption end. When Kinnear
asked to go down to the basin and look for him, the Department closed the file, and when the editor wrote to the Department
it had no record of the matter. Ashby was writing down a country two governments wanted unwritten, and the Department did to
him what it does to the country.

That puts a fifth reading beside the four in [[ref:gatherer]], and it's the plainest: Ashby was made to disappear, by
Jubilee or by Washington, because he was about to print what everybody knew. The editor printed it anyway, and the editor's
book is the one record nobody filed.
""",
      open=[("Was Ashby removed?",
             ["No. The four readings in [[ref:gatherer]] stand, and the Department closed the file because it closes every "
              "file that points at the river.",
              "Yes. The ticket for the branch was bought in his name by somebody else, and he never rode the train because "
              "he'd been taken off the Stage Road below Saltlick the night before, by men in grey a long way from "
              "home."])],
      table="""
Kinnear's note is the Agency's own man saying the Agency was wrong. If the posse has met Kinnear, this is where they find out
what he's been doing since he left, and he'll want them to come with him.
""")

# ================================================================ The Last of the Satchel
intro("last", """
The satchel came to the editor through a lawyer at the Crossing in the spring of 1886 with two lines of
instruction, and the chapter prints what was in it in the order it was in. It has no sections, so the
entries here have titles of their own, one for each thing in the satchel that has a story behind it.

Most of it is Perdition Basin in October 1884, and all of it is the basin seen by the one outsider who
had worked out nearly everything. The Keeper knows the rest from Module III: that the counting is the
keeping, that it's done by one person at a time, and that it can stop. Every entry below works whether
your table's ring is held, broken, or held by one of the players.

What became of Ashby is [[ref:gatherer]]'s to offer, four ways. The chapter doesn't say, and the Keeper
shouldn't either, until the last session or the one before it.
""")

entry("satchel-instruction", title="The Letter of Instruction",
      people=["Ashby, N.*", "the lawyer at the Crossing"],
      places=["Calvary Crossing"],
      creatures=[],
      threads=["satchel-page", "sanclavo", "forgery"],
      when=[(1886, "The satchel reaches the editor through a lawyer at the Crossing in the spring")],
      story="""
Two lines: print all of it or none of it, and don't tidy the spelling; there's no ending, don't supply one. Ashby wrote it and left it on
top of the satchel and gave the satchel to the lawyer at the Crossing sometime after the 24th of October 1884, with a fee paid in advance
and no instruction about whom it was for.

The first line is the one that matters. All of it or none of it is how a man hides a true thing: in three hundred papers, most of them
hearsay, several of them frauds, one of them a forgery, printed by an editor who says on the first page that nothing in the book is proved.
Module III says the padres' ledger was plain that a thing widely known is a thing eventually dug up. Ashby had worked that out for
himself. A thing printed in a book nobody believes isn't widely known. It's widely dismissed, and that's the safest place for it.

The second line is a kindness to the editor and a warning to the Keeper. There's no ending because the ending hasn't happened, and it's
the table's.
""",
      open=[("Why a lawyer at the Crossing?",
             ["Because a lawyer keeps a paper and doesn't read it, and the Crossing is the only town in the basin with one.",
              "Because the lawyer is the one person in the county Ashby trusted, and knows where Ashby went."])],
      table="""
The lawyer is alive and practising at the Crossing, and a posse that asks him about Ashby will be told politely that the matter was
concluded in 1886. If they ask him the right question, which is whether Ashby left anything else, the answer is a sealed envelope
addressed to whoever asks.
""")

entry("satchel-wells", title="The Wells Coming Back",
      people=["Ashby, N.", "Kirby, Mrs.", "Renfro family", "Dunbar family"],
      places=["Coffin Wells", "the Renfro place", "the Dunbar place"],
      creatures=[],
      threads=["water", "foreclosure", "satchel-cup", "sanclavo"],
      when=[(1884, "The Renfro well comes back sweet on 2 October after eleven months dead; the Dunbar well follows on the 6th")],
      story="""
The Renfro well came back on the 2nd of October 1884, sweet and cold and drawing clean, eleven months after it died, and the Dunbar on the
6th. Ashby went round four houses at Coffin Wells with what he thought was good news and got the same face back four times, and Mrs. Kirby
told him they don't come back, and when he said two of them had, she said yes.

They came back because somebody was keeping the ring again. Somebody had picked up the hammer and was walking the circuit, and the wells
on it were coming sweet one at a time in the order the nails were being renewed. That's what nobody at Coffin Wells was pleased about. The
people who have lived there long enough know what a well coming back means: the keeping has started again, and the keeping costs one or
two a year, and somebody in the district is going to be one of them. The Renfro boy's well came back, and the Renfros know better than
anybody what it cost the first time.

Mrs. Kirby's yes is the most knowing word in the book. She knows who's walking.
""",
      open=[("Who took up the hammer?",
             ["If your table played Module III and a player took it, it's them, and this is their first full round.",
              "Rosal&iacute;a Cardoza, sixteen, whom Esperanza meant to hand it to, and who worked out the schedule from the "
              "back board herself.",
              "Ashby. See [[ref:gatherer]].",
              "Nobody. The wells came back for another reason, and [[ref:foreclosure]] has four."])],
      table="""
Play the four faces Ashby got at the four doors. A posse bringing good news to Coffin Wells about a well should get exactly that look, and
Mrs. Kirby should give them tea and not explain.
""")

entry("satchel-note", title="Ask at the Mission About the Count",
      people=["Ashby, N."],
      places=["San Clavo, Mission of"],
      creatures=[],
      threads=["sanclavo", "satchel-page", "satchel-cup"],
      when=[],
      story="""
An undated note on the back of a bill: ask at the mission about the count on the back board; ask who keeps it; ask whether they've ever
had to put the figure down and then put it up again, and how long between.

Ashby had worked it out by then. The count is the number of nails holding. Somebody keeps it, and the somebody is at the mission often
enough to write in a book kept there. The seven, six, seven on the board is a nail that failed and was re-driven, and the question of how
long between is the question of how long the basin can go with a nail out before something comes up through it. That's the one number
Module III's ledger has and the county doesn't. Ashby was asking for the clock.
""",
      open=[("Did he ask?",
             ["No. He was afraid that if he asked, the keeping would stop, and he says so in his entry of the 11th.",
              "Yes, and the answer is on the torn half of his last page, and it isn't in the satchel."])],
      table="""
Give the note to a player as their own thought. If they go to the mission and ask, whoever is keeping the ring will answer, once, and
then want to know how they knew to ask.
""")

entry("satchel-ticket", title="A Ticket to Jubilee, Not Punched",
      people=["Ashby, N."],
      places=["Yuma", "Jubilee"],
      creatures=[],
      threads=["spur", "twopapers", "gatherer"],
      when=[(1884, "Ashby holds a second-class ticket, Yuma to Jubilee, for 3 November, and it's never punched")],
      story="""
A second-class ticket on the Jubilee Branch, Yuma to Jubilee, for the 3rd of November 1884, not good for return, not punched. Ashby had
advertised for anything about Jubilee and bought papers about it across counters at Yuma for two years, and meant to go and see for
himself. The editor of the Book of Legends says neither of them had been.

The ticket is in the satchel, so it was never handed to a conductor on the 3rd of November, and the satchel was at the lawyer's before
anybody could have used it. Either Ashby decided in the last week of October not to go, or he went another way, or he didn't need a
ticket where he went.
""",
      open=[("Did Ashby go to Jubilee?",
             ["No. He stayed in the basin.",
              "Yes, by the river door the pilot described, which doesn't need a ticket, and he's one of the ones the two "
              "newspapers can't find.",
              "Yes, on the 3rd, with a second ticket, and Henry Pruitt remembers a naturalist with a notebook who got off at "
              "Jubilee and didn't come back down."])],
      table="""
Henry Pruitt is the man to ask. He counts everybody. If Ashby rode the branch, Pruitt knows which day, and what Ashby said to him.
""")

entry("satchel-cup", title="The Second Cup",
      people=["Ashby, N.", "the one living at the mission ground", "the visitor"],
      places=["San Clavo, Mission of"],
      creatures=[],
      threads=["satchel-wells", "satchel-note", "mesa", "sanclavo"],
      when=[(1884, "On 11 October Ashby finds two cups at the mission ground, both used, and decides not to ask")],
      story="""
Somebody has been living out at the mission ground since at least 1881, and the whole county knows it, and it's the least interesting
fact in the basin. What Ashby found on the 11th of October 1884 is that the somebody expects company. There's a second cup, washed and
upside down on a stone next to the first, and it's been used, and it isn't his, and in three years he has never been offered a cup of
anything.

The one who lives at the mission ground is whoever is keeping the ring that October, or the one who is learning to: a keeper needs to be
near the courtyard nail, which is the first driven and the one over the thing. The visitor is somebody who comes regularly and washes up.
It isn't the man on the road, who takes nothing and would leave the cup dry. Ashby was right not to ask. A keeping that's widely known is
eventually dug up, and a keeper who knows she's being watched stops.
""",
      open=[("Who comes to drink?",
             ["The keeper of the Painted spring, from the mesa, and the two keepers have been sitting together once a season for "
              "seventy years, which is the Keeper's Book's question about who taught whom, answered over coffee.",
              "Rosal&iacute;a Cardoza, riding out from the Cardoza place to learn the round.",
              "Mrs. Kirby, from Coffin Wells, who walked the circuit once herself."]),
            ("Who lives there?",
             ["Whoever took up the hammer, the same answer as [[ref:satchel-wells]].",
              "Ashby, after the 24th. He never says the cup is his, because it wasn't yet."])],
      table="""
If the players go out to the mission ground, they'll find two cups on the stone. If they wait, they'll meet the visitor. What they say to
the visitor decides whether the keeper ever speaks to them.
""")

entry("satchel-crandall", title="Forty-One Is Now Thirty-Eight",
      people=["Crandall, Miss Harriet", "Ashby, N."],
      places=[],
      creatures=[],
      threads=["weathersong", "keelers", "ninechairs"],
      when=[(1884, "Miss Crandall writes Ashby on 19 October that three unattached verses have attached themselves to later "
                   "events; the letter is never opened"),
            (1886, "Miss Crandall's unattached verses stand at thirty-one")]
      ,
      story="""
Miss Crandall's letter of the 19th of October 1884 was in the satchel unopened. Three of her forty-one unattached verses had attached
themselves to events in the county papers, and the verses were older than the events by one to four years, and one of her three
independent sources was Ashby's own. She'd stopped sorting by date and started sorting the other way. She wanted him to tell her she was a
fool, and would rather have it from him than from anybody at the college, and asked him to write by return.

He never read it. The seal was whole when the editor opened the satchel, which means the letter reached the Crossing after Ashby stopped
collecting his post, which puts the end of his writing somewhere between the 24th of October and the first week of November. She's continued
the work, and the figure is thirty-one, and she's asked that her caution be printed as prominently as her list, and it has been.

This is the Weather Song, and [[kb:legends-song]] still holds. Miss Crandall is drawing no conclusion, and the Keeper shouldn't draw one at the
table either.
""",
      open=[("What would Ashby have written back?",
             ["That she wasn't a fool, and that he'd met somebody on the road who got one thing wrong and wasn't wrong.",
              "Nothing. He'd have gone to see her."])],
      table="""
Miss Crandall is the best-sourced witness in the Territories and the most careful, and she's looking for somebody to tell her she's wrong.
A posse that brings her a verse they heard before the thing it's about happened will get a very long letter back, and her friendship.
""")

entry("satchel-road", title="That Is Not My Father",
      people=["Ashby, N.", "Ashby's sister", "Mad Spaniard, the"],
      places=["the Stage Road below Saltlick", "Calvary Crossing"],
      creatures=["The Gentleman on the Road"],
      threads=["wrongdetail", "saltlick", "spaniard", "gatherer"],
      when=[(1884, "On 24 October, on the Stage Road below Saltlick, Ashby meets a courteous stranger and catches the wrong detail")],
      story="""
Ashby met him at four in the morning on the Stage Road below Saltlick on the 24th of October 1884, the same stretch of road where the
Keeper's Book and the Bestiary both put him the week before something changes. He was courteous and knew Ashby was going to the Crossing,
and asked after Ashby's sister by name, and whether she'd got the place at the school, which she had, which Ashby had told nobody in the
Territory.

Then he said Ashby's father's name, and it wasn't Ashby's father's name, and Ashby caught it at the time, which nobody in two hundred and
eleven accounts had done, because he'd been waiting eleven years to. He said, that is not my father. The man said: no.

That's all of it, and it's the last dated entry in any of the field-books. The four readings of who the man is are in
[[kb:legends-spaniard]], and this book doesn't pick. What the Book of Legends' evidence says about the wrong detail is that it's never
wrong, only early or sideways, and a Keeper who holds that reading has a very large secret about Ashby's father to decide, and one word of
reply that can be read as agreeing with Ashby or correcting him.
""",
      open=[("What did 'no' mean?",
             ["No, that isn't your father: the man agreeing, and apologising for the delay.",
              "No, he isn't: the man telling Ashby that the father he'd grown up with wasn't his, and that the name was right.",
              "No, and Ashby understood the rest, and went looking the next week."]),
            ("Who was Ashby's father?",
             ["The Keeper's, if the Keeper wants it. The Book of Legends has room for it in exactly one place, and it's here.",
              "Nobody the players will ever meet. The point is that Ashby found out."])],
      table="""
If the players ever meet the man in the old clothes on the Stage Road below Saltlick, let him ask after Ashby. He'll get one thing wrong.
""")

entry("satchel-page", title="The Torn Page",
      people=["Ashby, N.", "R&iacute;os, Esperanza"],
      places=["Perdition Basin"],
      creatures=[],
      threads=["sanclavo", "satchel-note", "satchel-wells", "gatherer"],
      when=[],
      story="""
The last thing in the satchel is an undated page torn off mid-sentence. It's the theory Ashby had held since his second winter and never
written down because a theory is a thing a man defends: that it comes down to the wells, that there are seven and somebody has been counting
them for seventy-five years, that the counting is the work, and that the one who does it is always old and alone and has always just taken
it on from somebody, and he'd never met one who was the first.

He was right about all of it, and Module III knows the rest. The counting is the keeping. It's done by one person at a time, a portion
carried to seven wells on a schedule, and it can stop, and it stopped in April when Esperanza Ríos died without handing it on, because
she'd decided she'd rather leave the basin the choice than the schedule. The honest position, Ashby writes, is that nobody has ever seen it
stop, which is not the same as. And the page is torn.

The editor's last note is right, in the way that bothered the editor: a man who says the honest position is that nobody has seen a thing is
not a man who has seen it. By the end of October 1884 Ashby had seen the wells come back, which meant he knew it had stopped, and started
again. What he was going to write after "not the same as" is the sentence the Keeper holds.
""",
      open=[("What was on the other half of the page?",
             ["Not the same as it never stopping: it has, once, this year, and the wells went out from the mission in the order "
              "the padres drove them in reverse.",
              "Not the same as knowing what's under there, and he'd found out, and tore it off.",
              "A name. The one who took the hammer after Esperanza, and Ashby tore it off so it couldn't be read."]),
            ("Who tore it?",
             ["Ashby, when he gave the satchel to the lawyer.",
              "The one whose name was on it."])],
      table="""
Don't let the players find the other half. Let them find the satchel, and the torn page, and let the table argue about the end of the
sentence the way it'll argue about everything else in this book. Somebody at the table will finish it out loud, eventually, and the
Keeper should listen very carefully to how.
""")


# ================================================================ FRONT MATTER
FRONT = {}


def front(anchor, title, sub, text):
    FRONT[anchor] = dict(title=title, sub=sub, body=text)


# The papers that speak for a real nation. CLAUDE.md asks that somebody from each nation read these before they
# ship; the count and the titles in "Before You Open It" are read off this list and the Book of Legends.
REAL_NATIONS = [("calendar", ""), ("advocate", ""), ("collector", "the clerk's letter in "),
                ("wendigo", "the statement of the Ojibway woman in ")]
# Three more papers speak from real history, and two are about the Painted Mesa, whose people stand in for a real
# nation (Book of Legends v1.9). They are listed the same way, so the sentence that names them can't drift either.
REAL_HISTORY = [("emigrants", "the answer from Nicodemus in "), ("tenth", "the first sergeant's letters in ")]
MESA_PAPERS = [("twosections", ""), ("landoffice", "")]
_SPELL = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six"}


def _list(pairs):
    items = [f"{lead}<em>{SEC_TITLE[s]}</em>" for s, lead in pairs]
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


_real = [f"{lead}<em>{SEC_TITLE[s]}</em>" for s, lead in REAL_NATIONS]
_REAL_SENTENCE = (f"{_SPELL[len(_real)]} papers in the Book of Legends speak for real nations: "
                  + ", ".join(_real[:-1]) + ", and " + _real[-1] + ". "
                  + f"{_SPELL[len(REAL_HISTORY)]} more speak from real history: {_list(REAL_HISTORY)}. And "
                  + f"{spell(len(MESA_PAPERS))} are about the Painted Mesa, whose people stand in for a real nation: "
                  + f"{_list(MESA_PAPERS)}.")

front("before", "Before You Open It", "What this book is for, and the rules it keeps.", """
The Book of Legends is the Territory's talk, set down on paper by people who were there and didn't agree, and
any hand at the table may read it. This book is what the talk was about. Every section of the Book of Legends
has an entry here under the same title, in the same order, under the same chapter numeral, so a Keeper holding
one book can open the other at the same place. The last chapter of the Book of Legends has no sections, so its
entries here take their titles from what was in the satchel.

Each entry has three parts. <strong>What happened</strong> is the story behind the papers, told whole, as the
Keeper should hold it: who did what, why the papers get it wrong, and what the one sentence the editor couldn't
dismiss was pointing at. <strong>Left open</strong> is what this book won't settle, with two or three ways to
hold each question. Pick one, write it inside your screen, and don't say it. <strong>At the table</strong> is
a way to put the story in front of players and what to run when it gets there. Under the heading is who's in it,
and at the foot are the Bestiary entries it uses and the other papers it shares a thread with.

The rules this book keeps come from the Keeper's Book.

<strong>It's for the Keeper alone.</strong> The Book of Legends is written to be handed over. This isn't. A player
who reads an entry has been told what their character would spend a year finding out, and the year was the game.

<strong>The Keeper's Book outranks it.</strong> Where the Keeper's Book leaves a question open by design, this book
leaves it open too: why the Old Dark answers anybody, what's gathering in the Rockies, which face the thing under
Perdition Basin wears, what the Mad Spaniard is, whether there's a fifth rider, who writes the Weather Song, and
what the Long Table's ninth children are for. It offers ways to hold each one. It never picks.

<strong>Your table outranks both.</strong> Where your players have already played a night a paper describes, what
they did is what happened, and the paper is wrong the way papers generally are. The Book of Legends' dates are
the papers' dates, and they'll bend to yours.

<strong>Redemption is loud and the houses are quiet.</strong> Everybody in the Territories knows about Jubilee, and
[[ch:forwarded]] shows how Washington arranged to forget it anyway, one office at a time; [[ref:understanding]] says
why, and offers ways for it to end. The houses of the Long Table never write their own name down, and the Book of
Legends holds them to that. Run the two that way and the contrast does a good deal of the setting's work.

<strong>The three legends never explain each other.</strong> [[kb:legends]] makes that a rule for the Mad Spaniard,
the Wills Outfit and the Weather Song, and every entry here that touches one of them holds it.

<strong>The real nations keep their own counsel.</strong> {REAL} The stories behind them stay on the settlers'
side of the page: what the trader did, what the collector paid for, what Kansas printed. Nothing here invents a
rite, a belief or a sacred thing for any living people, and nothing should at your table. The Painted Mesa people
are this game's own, and they're played as people, and nothing behind their papers makes a monster of them.

Most of these stories were built on older ones. The country's legends always are, and a Keeper who recognises
the bones of a story they already love under one of these should feel free to use what they know of it. The
game's lore is the flesh, and where the two disagree the lore wins.
""".replace("{REAL}", _REAL_SENTENCE))

front("gatherer", "Ashby, and the Editor", "Who gathered the papers, who printed them, and what became of the first.", """
N. Ashby came west in the spring of 1873 with a letter from a natural-history society in the East and a commission
to catalogue the animals of the Territories, and did it badly, and found the papers instead. The Bestiary quotes the
field-books: four ledgers filled, and not one of them holds an animal. Eleven years and eleven field-books followed,
every one numbered to thirteen chapters and never past, two hundred and eleven road stories, two hundred and forty
chased to the end and nineteen that survived the chasing. From the winter of 1881 he wintered in Perdition Basin,
because that's where the papers were thickest and because, by the second winter, he'd begun to suspect why.

He had a sister who was a teacher, and got the place at the school she wanted in 1884, and he told nobody in the
Territory about it. He answered a stranger's sign at Trinidad in 1880 and waited four years to be asked for something
([[ref:sign]]). He was a careful, curious, lonely man who wanted to know more than he wanted anything, and the Keeper's
Book would recognise the want.

His last dated entry is the 24th of October 1884, on the Stage Road below Saltlick. He gave the satchel to a lawyer at
the Crossing some days after, with two lines of instruction, and stopped writing. What became of him is the question the
Book of Legends ends on and the Keeper should hold it the way the Keeper's Book holds its largest questions: pick one of
these four, write it inside the screen, and confirm it in the last session of a campaign or the one before, if at all.

<strong>He took up the hammer.</strong> The wells that came back in October were his first round. He sent the satchel to be
printed because a true thing printed among three hundred papers nobody believes is the safest place for it, and he
stopped writing because a keeping written down is a keeping eventually dug up. He's four miles from a well, older than
his years, and the cup on the stone at the mission ground is his.

<strong>He went looking for his father.</strong> The man on the road said a name, and Ashby said that is not my father, and
the man said no. Ashby rode east the next week to find out which way the word was meant, and found out, and never came
back to the Territories, and is alive and ordinary and has no wish to be written about.

<strong>He went to Jubilee.</strong> The ticket in the satchel was never punched because he went another way, by the river
door, and he's one of the ones the two newspapers can't find.

<strong>He went to the crossroads.</strong> The next night on the county's page at Twelve Mile would have been the 21st of
December 1884, and the page stops at 1883 because the clerk who kept it had stopped writing lines. Ashby had the page.
He'd have wanted to see.

The editor is nobody in particular unless the Keeper needs them to be. They prepared the book in 1885 and 1886, had two
years and a printer's budget and better manners than Ashby, disagreed with him in square brackets, and kept every
promise they made in <em>A Word Before</em>. If they're ever needed, three people in the papers would fit: Ashby's sister
the schoolteacher, who would know his hand and forgive it; a printer at Kansas City who took the satchel as a commission and
came to care about it; or one of the people in the book, which would explain a good deal about which papers the editor chose
to doubt.
""")

front("years", "The Years in the Papers", "Every dated thing behind the Book of Legends, in order.",
      lambda: ("  <p>The table below is built from the entries themselves, so it can't disagree with them. It holds the "
               "papers' own dates. A Keeper who has moved Perdition Basin's Haunted Year, or anything else, should trust "
               "the table's play over the dates, as the papers would have to.</p>\n  " + years_html()[0]))


def _threads_body():
    groups = [
        ("The ring and its count",
         "The padres' seven wells, the keepers who walked them, and what a well coming back costs. [[kb:basin]] "
         "and Module III carry the truth; these carry the county's side of it.",
         ["sanclavo", "water", "pell", "forgery", "foreclosure", "coroner", "returned", "circuit", "glutton", "thirst",
          "satchel-wells", "satchel-note", "satchel-cup", "satchel-page"]),
        ("The Vane Interest and Kansas City's paper",
         "A bank at Coffin Wells, its correspondents, and the clauses and dinners behind them.",
         ["vane", "water", "paidinfull", "foreclosure", "clause", "kansas", "contract", "houses", "fifth"]),
        ("The man on the road",
         "The Mad Spaniard's nights, and the wrong detail that's never quite wrong. [[kb:legends-spaniard]] has the man.",
         ["saltlick", "wrongdetail", "spaniard", "calendar", "spring", "collector", "satchel-road"]),
        ("The Long Table and its ninth children",
         "Houses, tithes, a rhyme that stops at nine, and the families who say yes and no. None of the houses ever "
         "writes the name down.",
         ["will", "ninechairs", "seats", "notice", "stand", "tithe", "witch", "sister", "hear", "notours", "ninth",
          "namebook", "harrow", "commission", "lindqvist", "houses", "afraid", "deadletters"]),
        ("Redemption in the open, and Washington's silence",
         "The thing everybody in the Territories knew about, and the slow, regular way it was left out of the books.",
         ["warrants", "emigrants", "sixes", "spur", "river", "twopapers", "lady", "novel", "letterhome", "muster",
          "sayings", "enumerators", "plate", "deadletters", "noinformation", "remarks", "understanding", "tenth",
          "ashbyfile"]),
        ("The Golden Circle's list",
         "Parcels bought by men who don't know why, on a page with two lines still to fill, and the faintest rumour "
         "of who fills it.",
         ["gold", "floor", "mesa", "twosections", "landoffice", "letterhome", "otherdoor", "ore", "landismine",
          "committee", "degree", "lookedat", "clerk", "gatherings", "crossroads", "breathing", "eclipse"]),
        ("W. F. Kinnear of the Agency",
         "A Pinkerton working under the Department of Justice's contract, right about people and wrong about the world.",
         ["principles", "agency", "gatherings", "clerk", "ashbyfile"]),
        ("A. Crail, witch hunter",
         "Twenty years in the trade, a book of names, and a price only a house can pay.",
         ["lookeddoor", "terms", "crailtrial", "namebook", "commission", "notice"]),
        ("The faithful",
         "People who went looking for the dark and were glad of it, and what each of them wanted. Everywhere, and never "
         "together.",
         ["tract", "sign", "route", "creeds", "gloves", "congregations", "glad", "partners", "uncle", "asked", "vessel",
          "township", "evergreen", "braid", "sawbones", "hexer", "supper", "revival"]),
        ("The Long Trail's roads",
         "Walkers, a long train, a dead column, a ford that takes people, and the courtesies the living keep.",
         ["carrow", "walker", "salt", "blacktrain", "fortclark", "feebill", "undertaker", "surgeon", "scout",
          "returned", "wager"]),
        ("Things the ground keeps sealed",
         "A man in a hollow in the rock, a snake in the stone, a finger in a safe, a floor, a long room, a breath.",
         ["thirdcell", "rocksnake", "veinwork", "floor", "dugout", "breathing", "adit", "assay"]),
        ("Witnesses nobody asks",
         "The people in the papers who saw the most and are asked the least. Each is worth a posse's time.",
         ["saltlick", "fifth", "swarm", "deputy", "circuit", "spur", "fortsafe", "numberfour", "enumerators",
          "tenth", "landoffice"]),
    ]
    out = ["  <p>Ashby's arrangement of the papers is by subject, and the editor's is by slow burn, and neither shows "
           "the threads that run across the chapters. These do. [[kb:powers-together]] warns that two threads make a "
           "campaign and all of them make a setting sourcebook, and the same is true here: pull one.</p>"]
    out[0] = expand(out[0])
    for title, gloss, slugs in groups:
        links = " &middot; ".join(expand(f"[[ref:{s}]]") for s in slugs)
        out.append(f'  <h4 class="lc-lab">{title}</h4>\n  <p>{expand(gloss)}</p>\n  <p class="lc-foot">{links}</p>')
    return "\n".join(out)


front("threads", "Threads That Cross the Book", "Which papers belong to which story, whatever chapter they're in.",
      _threads_body)


# ================================================================ ASSEMBLY
# Everything below reads the entries above. Nothing here is content.
import sys

DRAFT = "--draft" in sys.argv

ENTRY_TITLE = dict(SEC_TITLE)
ENTRY_CHAPTER = dict(SEC_CHAPTER)
for _rec in SATCHEL:
    assert _rec["slug"] not in ENTRY_TITLE, f"a satchel entry reuses the id {_rec['slug']}"
    ENTRY_TITLE[_rec["slug"]] = _rec["title"]
    ENTRY_CHAPTER[_rec["slug"]] = "last"

# Every section of the Book of Legends has its story here, and nothing here names a section that
# isn't there. The order is the Book of Legends' own, because the assembly walks it.
_missing = [f"{SEC_CHAPTER[s]}: {s}" for s in SEC_TITLE if s not in E]
_extra = sorted(set(E) - set(SEC_TITLE))
assert not _extra, f"entries for sections the Book of Legends doesn't have: {_extra}"
if not DRAFT:
    assert not _missing, f"sections of the Book of Legends with no entry: {_missing}"
    assert SATCHEL, "the Last of the Satchel has no entries"
    assert set(CH_INTRO) == set(LEG_BY), f"chapters with no introduction: {sorted(set(LEG_BY) - set(CH_INTRO))}"

_MACRO = re.compile(r"\[\[(kb|ref|ch):([a-z0-9-]+)\]\]")


def expand(text, here=None):
    """Resolve [[kb:anchor]], [[ch:anchor]] and [[ref:slug]] against the books as built today."""
    def sub(m):
        kind, key = m.groups()
        if kind == "kb":
            return kb(key)
        if kind == "ch":
            assert key in LEG_BY, f"no Book of Legends chapter {key!r}"
            return lch(key)
        if key in FRONT:
            return f'<a class="lc-ref" href="#{key}">{FRONT[key]["title"]}</a>'
        if key in ENTRY_TITLE and (key in E or key in {r["slug"] for r in SATCHEL} or DRAFT):
            link = f'<a class="lc-ref" href="#lc-{key}">{ENTRY_TITLE[key]}</a>'
            ch = ENTRY_CHAPTER[key]
            return link + (f" ({lch(ch)})" if ch != here else "")
        if DRAFT:
            return f"[{key}?]"
        raise SystemExit(f"[[ref:{key}]] points at nothing")
    return _MACRO.sub(sub, text)


def display_name(label):
    """'Harbin, Linus' -> 'Linus Harbin'; 'Coyle, T. (marshal)' -> 'T. Coyle (marshal)'."""
    label = label.rstrip("*")
    suffix = ""
    m = re.match(r"(.*?)(\s*\(.*\))$", label)
    if m:
        label, suffix = m.group(1), m.group(2)
    if ", " in label:
        surname, given = label.split(", ", 1)
        label = f"{given} {surname}"
    return label + suffix


def render_entry(rec, title, here):
    slug = rec["slug"]
    out = [f'  <h2 id="lc-{slug}">{title}</h2>']
    if rec["people"]:
        who = ", ".join(display_name(p) for p in rec["people"])
        out.append(f'  <h5 class="lc-who"><span class="t">Who&rsquo;s in it</span>{who}</h5>')
    out.append('  <h4 class="lc-lab">What happened</h4>')
    out += [f"  <p>{expand(p, here)}</p>" for p in rec["story"]]
    if rec["open"]:
        out.append('  <h4 class="lc-lab">Left open</h4>')
        for q, opts in rec["open"]:
            out.append(f'  <h5 class="lc-q">{expand(q, here)}</h5>')
            items = "".join(f"<li>{expand(o, here)}</li>" for o in opts)
            out.append(f'  <ul class="dash lc-opts">{items}</ul>')
    if rec["table"]:
        body = "".join(f"<p>{expand(p, here)}</p>" for p in rec["table"])
        out.append(f'  <div class="keeper-note"><span class="kn-tag">At the table</span>{body}</div>')
    if rec["creatures"]:
        crs = " &middot; ".join(f"{cr_display(n)} (Tier {_ROMAN[creature(n)['tier']]})" for n in rec["creatures"])
        out.append(f'  <p class="lc-foot"><span class="t">From the Bestiary</span>{crs}</p>')
    if rec["callings"]:
        out.append(f'  <p class="lc-foot"><span class="t">A way in for</span>'
                   f'{" &middot; ".join("the " + c for c in rec["callings"])}</p>')
    if rec["threads"]:
        links = " &middot; ".join(expand(f"[[ref:{t}]]", here) for t in rec["threads"])
        out.append(f'  <p class="lc-foot"><span class="t">Threads</span>{links}</p>')
    return "\n".join(out)


def chapter_html(c):
    anchor, num = c["anchor"], c["num"]
    parts = [f"  <p>{expand(p, anchor)}</p>" for p in CH_INTRO.get(anchor, [])]
    if anchor == "last":
        recs = [(r, r["title"]) for r in SATCHEL]
    else:
        recs = [(E[sid], stitle) for sid, stitle in c["sections"] if sid in E]
    parts += [render_entry(r, t, anchor) for r, t in recs]
    body = "\n".join(parts)
    return f'''
<section class="page" id="{anchor}">
  {runhead(f"{num}. {c['run']}")}
  <h1 class="chapter">{num}. {c['title']}</h1>
  <p class="chapter-sub">{c['sub']}</p>
  <div class="divider"></div>
{body}
</section>
'''


ALL_RECS = [E[s] for c in LEG for s, _t in c["sections"] if s in E] + SATCHEL


def ref_short(slug):
    """A link for a generated table: the title and the chapter's bare numeral."""
    return f'<a class="lc-ref" href="#lc-{slug}">{ENTRY_TITLE[slug]}</a> ({LEG_BY[ENTRY_CHAPTER[slug]]["num"]})'


def years_html():
    rows = []
    for rec in ALL_RECS:
        for year, what in rec["when"]:
            rows.append((year, what, rec["slug"]))
    rows.sort(key=lambda r: r[0])
    trs = "".join(f'<tr><td class="y">{y}</td><td>{w}</td><td class="e">{ref_short(s)}</td></tr>'
                  for y, w, s in rows)
    return (f'<table class="lc-years"><thead><tr><th>Year</th><th>What happened</th><th>The entry</th></tr>'
            f'</thead><tbody>{trs}</tbody></table>'), len(rows)


def run_html():
    used = {}
    for rec in ALL_RECS:
        for n in rec["creatures"]:
            used.setdefault(n, []).append(rec["slug"])
    order = sorted(used, key=lambda n: (creature(n)["tier"], re.sub(r"^(The|A|An) ", "", n)))
    trs = "".join(f'<tr><td>{n}</td><td>{_ROMAN[creature(n)["tier"]]}</td>'
                  f'<td class="e">{" &middot; ".join(ref_short(s) for s in used[n])}</td></tr>' for n in order)
    return (f'<table class="lc-run"><thead><tr><th>The Bestiary entry</th><th>Tier</th><th>The stories that use it'
            f'</th></tr></thead><tbody>{trs}</tbody></table>'), len(order)


def callings_html():
    """Every Calling, in the Player's Book's order, and the stories that give a player of it a way in.

    Cole, 2026-10-08: most if not all of the Callings should be represented throughout the legends. This is the check
    and the proof: a Calling with no story stops the build."""
    by = {c: [] for c in CALLINGS}
    for rec in ALL_RECS:
        for c in rec["callings"]:
            by[c].append(rec["slug"])
    bare = [c for c in CALLINGS if not by[c]]
    assert not bare, f"Callings with no story in the Book of Legends: {bare}"
    chapters = {ENTRY_CHAPTER[s] for c in CALLINGS for s in by[c]}
    trs = "".join(f'<tr><td>The {c}</td><td class="e">{" &middot; ".join(ref_short(s) for s in by[c])}</td></tr>'
                  for c in CALLINGS)
    return (f'<table class="lc-run"><thead><tr><th>The Calling</th><th>The stories with a way in for it</th></tr>'
            f'</thead><tbody>{trs}</tbody></table>'), len(chapters)


def front_html(anchor):
    f = FRONT[anchor]
    body = f["body"]() if callable(f["body"]) else "\n".join(f"  <p>{expand(p)}</p>" for p in paras(f["body"]))
    return f'''
<section class="page" id="{anchor}">
  {runhead(f["title"])}
  <h1 class="chapter">{f["title"]}</h1>
  <p class="chapter-sub">{f["sub"]}</p>
  <div class="divider"></div>
{body}
</section>
'''


FRONT_ORDER = [a for a in ("before", "gatherer", "years", "threads") if a in FRONT]
_toc = "\n".join(
    [f'    <li><a href="#{a}">{FRONT[a]["title"]}</a><span class="pg">0</span></li>' for a in FRONT_ORDER] +
    [f'    <li><a href="#{c["anchor"]}">{c["num"]}. {c["title"]}</a><span class="pg">0</span></li>' for c in LEG] +
    ['    <li><a href="#whattorun">Appendix: What to Run</a><span class="pg">0</span></li>',
     '    <li><a href="#everycalling">Appendix: A Legend for Every Calling</a><span class="pg">0</span></li>'])
N_ENTRIES = len(ALL_RECS)
CONTENTS = f"""<!-- ===================== COMPANION CONTENTS ===================== -->
<section class="page" id="contents">
  {runhead('Contents')}
  <h1 class="chapter">Contents</h1>
  <p class="chapter-sub">What the papers were about.</p>
  <div class="divider"></div>
  <p class="note">This is the Keeper's Companion to the Book of Legends, and it's for the Keeper alone.
  Its {spell(len(LEG))} chapters carry the Book of Legends' numerals and titles. {spell(len(E)).capitalize()} of
  its entries carry the titles of the sections they tell the story behind, in the same order, so a Keeper holding
  one book can open the other at the same place, and {spell(len(SATCHEL))} more tell what was in Ashby's
  satchel.</p>
  <ul class="toc">
{_toc}
  </ul>
</section>
"""

_run_table, N_RUN = run_html()
APPENDIX = f'''
<section class="page" id="whattorun">
  {runhead('Appendix: What to Run')}
  <h1 class="chapter">Appendix: What to Run</h1>
  <p class="chapter-sub">Every Bestiary entry these stories use, by Tier, and where.</p>
  <div class="divider"></div>
  <p>The {spell(N_RUN)} Bestiary entries below are the ones the stories in this book name, lowest Tier first. A
  story that names none is one where the horror is people, paper or weather, and those are the ones to
  run when your table has seen too many monsters. Nothing here is a stat block. The Bestiary has the
  numbers, and [[kb:odds]] has what a fair fight costs.</p>
  {_run_table}
</section>
'''.replace("[[kb:odds]]", kb("odds"))

_calling_table, N_CALLING_CHAPTERS = callings_html()
APPENDIX_CALLINGS = f'''
<section class="page" id="everycalling">
  {runhead('Appendix: A Legend for Every Calling')}
  <h1 class="chapter">Appendix: A Legend for Every Calling</h1>
  <p class="chapter-sub">For each of the Player's Book's Callings, the stories a player of it can walk into.</p>
  <div class="divider"></div>
  <p>Every one of the {spell(len(CALLINGS))} Callings in the Player's Book has at least one story in the Book of
  Legends with somebody of that trade at the centre of it, and between them they run through {spell(N_CALLING_CHAPTERS)}
  of its chapters. Use the list the way the stories mean it: a player should hear the story that belongs to their
  Calling as talk, in a saloon or at a fort, long before anybody at the table reads a word of the papers. Each entry
  says at its foot which Callings it gives a way in for.</p>
  {_calling_table}
</section>
'''

BODY = (CONTENTS + "".join(front_html(a) for a in FRONT_ORDER) + "".join(chapter_html(c) for c in LEG)
        + APPENDIX + APPENDIX_CALLINGS)

new_html = book_shell.splice(H, BODY)

from nav_tools import add_detailed_toc, build_index, assert_css_vars

# The index is of names: a label that starts in lower case ("the jailer", "a boy of ten") is shown under
# its entry's heading and left out here, where it would only crowd the letter A.
IX = {"Ashby, N.": "gatherer"}
for rec in ALL_RECS:
    for label in rec["people"] + rec["places"]:
        key = label.rstrip("*")
        if not re.match(r"[A-Z&']", key):
            continue
        if (label.endswith("*") and key not in ("Ashby, N.",)) or key not in IX:
            IX[key] = "lc-" + rec["slug"]
new_html = build_index(
    new_html, curated=sorted(IX.items()), creatures=False,
    subtitle="Everybody in the stories, and every place, and the page to find them on.",
    intro="People and places are listed where a Keeper will want them first, which is usually the "
          "story they matter most to. A leading &ldquo;the&rdquo; is ignored in the ordering.")
new_html = add_detailed_toc(new_html)
assert_css_vars(new_html, "legends-companion.html")

# Every link in the book lands somewhere.
_ids = set(re.findall(r'id="([^"]+)"', new_html))
_dead = sorted({h for h in re.findall(r'href="#([^"]+)"', new_html)} - _ids)
assert DRAFT or not _dead, f"links to nothing: {_dead[:10]}"

open("legends-companion.html", "w", encoding="utf-8").write(new_html)
print(f"legends-companion.html: entries {len(E)} of {len(SEC_TITLE)} sections + {len(SATCHEL)} satchel "
      f"| Bestiary entries used {N_RUN} | Callings {len(CALLINGS)} across {N_CALLING_CHAPTERS} chapters "
      f"| index {len(IX)} | size {len(new_html)}"
      + (f" | DRAFT, {len(_missing)} sections still to write" if DRAFT else ""))
