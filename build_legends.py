#!/usr/bin/env python3
"""Build "Blood & Grit: The Book of Legends" on the shared engine (the Player's Book shell).

Reads blood-and-grit.html (run build_player.py first), writes legends.html.

WHAT THIS BOOK IS. Papers, not rules. Every page of it is something somebody in the Territories
wrote down: letters, depositions, clippings, a company file, a sermon taken in shorthand, songs,
a bank's terms, a child's rhyme. It is the fourth book and the only one a player may read cover to
cover without spoiling anything, because nothing in it is confirmed and a good deal of it is wrong.

TWO RULES THIS BOOK IS HELD TO.

  1. **It never names a Patron.** It is a player-side book, so the line the Player's Book keeps
     (Cole, 2026-09-19) applies here in full: a Dark Cultist picks a want and the Keeper says who
     answered. `verify_rules.py::check_patron_silence` reads this file too. Papers may circle a
     thing, disagree about it and be frightened of it. They may not name it.
  2. **Nothing settles.** Two papers about one night should not both be true, and the book never
     says which one is. Where a document could be read as a confirmation, another document nearby
     takes it back. The Keeper's Book has the answers and does not print them either.

WHY THIS BUILDER CARRIES ITS OWN COPY OF THE SHELL TRANSFORM. `build_keeper.py` and
`build_bestiary.py` do the same, because each is a one-of-a-kind book, while the three modules
share `modules_common.py`. This is the THIRD copy, which is one more than a pattern needs. If a
fifth book is ever made, lift the transform out of all three into `book_shell.py` and let the CSS
stay per-book: the transform is genuinely shared, the CSS genuinely is not (this book has no stat
blocks and wants none).
"""
import re

H = open("blood-and-grit.html", encoding="utf-8").read()

VERSION = "1.1"

# ---------------------------------------------------------------- the papers, as CSS
# Every document type is set apart by rule, indent and weight rather than by a colour wash, so the
# book prints on a home printer in black and white and still reads as a bundle of different papers.
_css = """
  /* ---- The Book of Legends: papers ---- */
  .paper{ margin:1.25em 0 1.45em; padding:10px 14px 12px; background:#efe6cf; border:1px solid var(--rule); }
  .paper > .pa-head{ display:flex; justify-content:space-between; gap:12px; align-items:baseline;
                     border-bottom:1.5px solid var(--gold-d); padding-bottom:4px; margin-bottom:7px; }
  .paper .pa-kind{ font-variant:small-caps; letter-spacing:.07em; font-weight:700; color:var(--blood-d); font-size:12.5px; white-space:nowrap; }
  .paper .pa-src{ font-style:italic; color:var(--ink-soft); font-size:12.5px; text-align:right; }
  .paper p{ margin:.42em 0; font-size:14.4px; line-height:1.45; text-indent:0; }
  .paper p.pa-sign{ text-align:right; font-style:italic; margin-top:.7em; }
  .paper p.pa-ps{ font-size:13.6px; font-style:italic; }
  /* A letter: a hand, on paper somebody paid for. */
  .paper.letter{ background:#f2ead6; border-left:3px solid var(--gold-d); }
  .paper.letter p{ font-size:14.6px; line-height:1.5; }
  /* A wire: capitals, no punctuation the operator was not paid for. */
  .paper.wire{ background:#ece4cc; }
  .paper.wire p{ font-family:'Courier New',Courier,monospace; font-size:13px; line-height:1.55;
                 letter-spacing:.03em; text-transform:uppercase; margin:.25em 0; }
  /* A clipping: a masthead, a deck of headlines, and small type under it. */
  .paper.news{ background:#eae2c9; border:1px solid var(--ink-soft); }
  .paper.news .nw-mast{ text-align:center; font-family:var(--western); font-size:18px; letter-spacing:.04em;
                        color:var(--ink); border-bottom:2px solid var(--ink-soft); padding-bottom:3px; margin-bottom:5px; }
  .paper.news .nw-deck{ text-align:center; font-family:var(--display); font-weight:700; line-height:1.18;
                        font-size:15.5px; margin:.35em 0; }
  .paper.news .nw-deck span{ display:block; font-weight:400; font-size:12.5px; font-variant:small-caps;
                             letter-spacing:.08em; color:var(--ink-soft); }
  .paper.news p{ font-size:13.4px; line-height:1.4; }
  /* Sworn testimony: the clerk's questions, the witness's answers, hanging indents. */
  .paper.depo{ background:#ece4cc; }
  .paper.depo p{ padding-left:2.1em; text-indent:-2.1em; font-size:14px; }
  .paper.depo p .q{ font-variant:small-caps; letter-spacing:.06em; font-weight:700; color:var(--shade); }
  /* A company file: numbered, confident, and not always right. */
  .paper.file{ background:#e9e1c8; border-left:3px solid var(--shade); }
  .paper.file p{ padding-left:2.4em; text-indent:-2.4em; font-size:13.8px; }
  .paper.file p .no{ font-weight:700; color:var(--shade); }
  /* A handbill, shouted. */
  .paper.bill{ background:#f2ead6; border:2px solid var(--ink); text-align:center; }
  .paper.bill p{ margin:.3em 0; }
  .paper.bill .bl-1{ font-family:var(--western); font-size:22px; line-height:1.1; letter-spacing:.02em; }
  .paper.bill .bl-2{ font-family:var(--display); font-weight:700; font-size:16px; }
  .paper.bill .bl-3{ font-variant:small-caps; letter-spacing:.1em; font-size:13px; color:var(--blood-d); }
  .paper.bill .bl-rule{ border-top:1px solid var(--ink); margin:.5em 2em; }
  /* A song, set the way a songbook sets one. */
  .paper.song{ background:#f0e8d2; text-align:center; }
  .paper.song p{ font-size:14.2px; line-height:1.5; font-style:italic; }
  .paper.song p.v{ margin:.55em 0; }
  .paper.song p.v em{ font-style:normal; }
  /* An account book. Numbers, and one line that is not about money. */
  .paper.ledger table{ width:100%; border-collapse:collapse; font-size:13.2px; margin:.3em 0; }
  .paper.ledger th{ text-align:left; font-variant:small-caps; letter-spacing:.05em; color:var(--shade);
                    border-bottom:1.5px solid var(--gold-d); padding:3px 6px; }
  .paper.ledger td{ border-bottom:1px solid var(--rule); padding:3px 6px; }
  .paper.ledger td.n{ text-align:right; white-space:nowrap; font-variant-numeric:tabular-nums; }
  /* Ashby's own field-book: narrow, hurried, written on a knee. */
  .paper.field{ background:#ece4cc; border-left:3px solid var(--blood); }
  .paper.field p{ font-size:14px; line-height:1.42; }
  .paper.field .fb-when{ font-variant:small-caps; letter-spacing:.06em; font-weight:700; color:var(--blood-d); }
  /* Where a paper came from, in the editor's hand. */
  .gloss{ font-size:13.4px; line-height:1.44; font-style:italic; color:var(--ink-soft);
          margin:1.1em 0 .35em; padding-left:11px; border-left:3px solid var(--gold-d); }
  .gloss .gl-tag{ font-variant:small-caps; font-style:normal; letter-spacing:.07em; font-weight:700;
                  color:var(--shade); margin-right:.4em; }
  /* The editor, interrupting. Square brackets, because that is what they mean in a printed text. */
  .ednote{ font-size:13.4px; line-height:1.42; color:var(--ink-soft); margin:.5em 0 1.1em; }
  .ednote .ed{ font-variant:small-caps; letter-spacing:.06em; font-weight:700; color:var(--shade); }
  /* The Book of Legends cover: a fourth sibling, dusk-blue ground and a faded indigo keyline. */
  .title-page{ background:#0b1018; box-shadow:0 0 0 4px #0b1018 inset, 0 0 0 5px rgba(96,122,166,.9) inset, 0 14px 40px rgba(0,0,0,.66); }
  .title-page .t-foot{ color:#9db3d6; }
  .title-page .t-sub{ color:#b6bfcf; }
</style>"""
if ".paper{" not in H:
    H = H.replace("</style>", _css, 1)

_head = H[:H.index("</head>")]
assert _head.index(".paper{") < _head.index("</style>"), "the Legends CSS landed outside the style block"


# ---------------------------------------------------------------- the paginator learns about papers
# A paper is a container like a stat block or a creature entry, and the shell's paginator only
# splits containers it has been told about. Untold, every document would move whole and strand a
# third of a page behind it. Two edits, both asserted: what to do with an oversized paper, and
# whether a paper may be split to fill a gap at all.
_TOOBIG_OLD = ("        else if(block.classList && block.classList.contains('creature')) "
               "splitContainer(block, ':scope > .cr-name');")
_TOOBIG_NEW = (_TOOBIG_OLD + "\n        else if(block.classList && block.classList.contains('paper')) "
               "splitContainer(block, ':scope > .pa-head');")
assert H.count(_TOOBIG_OLD) == 1, "the paginator's creature branch has moved"
H = H.replace(_TOOBIG_OLD, _TOOBIG_NEW, 1)

_SF_OLD = "        if(b.classList.contains('creature')) return b.children.length>1;"
_SF_NEW = _SF_OLD + "\n        if(b.classList.contains('paper')) return b.children.length>2;"
assert H.count(_SF_OLD) == 1, "the paginator's split-fill list has moved"
H = H.replace(_SF_OLD, _SF_NEW, 1)


# ---------------------------------------------------------------- cover / meta retext
# The Player's Book version is read off the shell rather than typed here. See build_keeper.py for
# what typing it cost, twice.
_PV = re.search(r"Edition of 1885 · Version (\d+\.\d+)</div>", H).group(1)
_meta = [
 (f"<!-- Blood & Grit — The Player's Book · Version {_PV} -->",
  f"<!-- Blood & Grit — The Book of Legends · Version {VERSION} -->"),
 (f"<title>Blood &amp; Grit — The Player's Book (Revised &amp; Expanded · v{_PV})</title>",
  f"<title>Blood &amp; Grit — The Book of Legends (v{VERSION})</title>"),
 ('<div class="kicker">Being a Field Manual for the Living</div>',
  '<div class="kicker">Being Such Papers as the Country Has Kept</div>'),
 ('<div class="t-foot">The Player\'s Book</div>', '<div class="t-foot">The Book of Legends</div>'),
 (f'<div class="t-tiny">Revised &amp; Expanded · Compiled in the Territories · Edition of 1885 · Version {_PV}</div>',
  f'<div class="t-tiny">Gathered in the Territories · Edition of 1885 · Version {VERSION}</div>'),
 ('<div class="t-tiny">Most rules herein are adapted from Pathfinder Second Edition, with some unique rules &amp; systems of its own</div>',
  '<div class="t-tiny">Letters, depositions, clippings, songs &amp; sworn lies, set down as they were found</div>'),
 (f'<p class="note" style="text-align:center; margin:0;">Blood &amp; Grit · The Player\'s Book · Version {_PV} · First Complete Edition</p>',
  f'<p class="note" style="text-align:center; margin:0;">Blood &amp; Grit · The Book of Legends · Version {VERSION} · For Any Hand at the Table</p>'),
]
for a, b in _meta:
    assert a in H, "the Player's Book cover no longer carries: " + a[:70]
    H = H.replace(a, b, 1)

_q_old1 = ('"We came west to be made new, and found instead that the country was older\n'
           '    than newness, older than God, and had been waiting a long while in the quiet for company."\n'
           '    <span class="src">— from the burned journal of Eliza Hart, Surveyor</span>')
_q_new1 = ('"I have put down what I was told, in the words I was told it in. Where two people told me\n'
           '    different I have put down both, and where I believed neither I have said so, and gone on."\n'
           '    <span class="src">— N. Ashby, from the front of the third field-book</span>')
_q_old2 = ('"Keep your powder dry, your salt close, and your accounts with the dark paid up.\n'
           '    The country settles every debt in the end."\n'
           '    <span class="src">— a saying common to the trail, author unknown</span>')
_q_new2 = ('"Everybody out here has a story and not one of them will swear to it. That is not because\n'
           '    they are liars. It is because they were there."\n'
           '    <span class="src">— Adelia Cruz, who keeps the peace at Coffin Wells</span>')
for a, b in [(_q_old1, _q_new1), (_q_old2, _q_new2)]:
    if a in H:
        H = H.replace(a, b, 1)


# ---------------------------------------------------------------- page furniture
def runhead(short):
    return f'<div class="runhead"><span class="l">Blood &amp; Grit</span><span>{short}</span></div>'


def quote(text, src):
    return f'<div class="quote">{text}<span class="src">&mdash; {src}</span></div>'


def paper(kind, src, body, cls="", sign=None, ps=None):
    """One document, printed as found. `kind` is what it is, `src` is where and when."""
    out = [f'<div class="{("paper " + cls).strip()}">',
           f'  <div class="pa-head"><span class="pa-kind">{kind}</span>'
           f'<span class="pa-src">{src}</span></div>']
    out += ["  " + line for line in body]
    if sign:
        out.append(f'  <p class="pa-sign">{sign}</p>')
    if ps:
        out.append(f'  <p class="pa-ps">{ps}</p>')
    out.append("</div>")
    return "\n".join(out)


def p(*paras):
    return [f"<p>{t}</p>" for t in paras]


def gloss(text):
    return f'<div class="gloss"><span class="gl-tag">Where this came from</span>{text}</div>'


def ednote(text):
    return f'<p class="ednote">[{text} <span class="ed">Ed.</span>]</p>'


def news(mast, when, deck, sub, paras):
    """A clipping: masthead, a deck of headlines stacked the way a frontier weekly stacked them."""
    heads = "".join(f'<div class="nw-deck">{h}{f"<span>{s}</span>" if s else ""}</div>'
                    for h, s in zip(deck, sub))
    return paper("From the press", when, [f'<div class="nw-mast">{mast}</div>', heads] + p(*paras),
                 cls="news")


def wire(when, lines):
    return paper("By wire", when, [f"<p>{ln}</p>" for ln in lines], cls="wire")


def depo(where, when, pairs, opening=None, closing=None):
    """Sworn testimony. A clerk writes down the question and the answer and nothing else."""
    body = list(p(opening)) if opening else []
    for q, a in pairs:
        body.append(f'<p><span class="q">Q.</span> {q}</p>')
        body.append(f'<p><span class="q">A.</span> {a}</p>')
    if closing:
        body += p(closing)
    return paper("Sworn testimony", f"{where}, {when}", body, cls="depo")


def filedoc(office, ref, paras, head=None):
    body = list(p(head)) if head else []
    body += [f'<p><span class="no">{i}.</span> {t}</p>' for i, t in enumerate(paras, 1)]
    return paper(office, ref, body, cls="file")


def bill(lines):
    body = []
    for cls, text in lines:
        body.append('  <div class="bl-rule"></div>' if cls == "rule" else f'<p class="{cls}">{text}</p>')
    return paper("Handbill", "posted where it would be read", body, cls="bill")


def song(title, stanzas, when):
    body = [f'<p class="v"><em>{title}</em></p>']
    body += [f'<p class="v">{"<br>".join(st)}</p>' for st in stanzas]
    return paper("A song", when, body, cls="song")


def ledger(what, when, headers, rows, foot=None):
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = ""
    for r in rows:
        cells = "".join(f'<td class="n">{c[1:]}</td>' if str(c).startswith("#") else f"<td>{c}</td>"
                        for c in r)
        body += f"<tr>{cells}</tr>"
    out = [f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"]
    if foot:
        out += p(foot)
    return paper(what, when, out, cls="ledger")


def field(when, where, paras):
    body = [f'<p><span class="fb-when">{when}</span>&ensp;{where}</p>'] + list(p(*paras))
    return paper("Field-book", "N. Ashby", body, cls="field")


def chapter(anchor, numeral, title, sub, runshort, body):
    return f'''
<section class="page" id="{anchor}">
  {runhead(runshort)}
  <h1 class="chapter">{numeral}. {title}</h1>
  <p class="chapter-sub">{sub}</p>
  <div class="divider"></div>
{body}
</section>
'''


# ---------------------------------------------------------------- Contents
CONTENTS = f"""<!-- ===================== LEGENDS CONTENTS ===================== -->
<section class="page" id="contents">
  {runhead('Contents')}
  <h1 class="chapter">Contents</h1>
  <p class="chapter-sub">What the country wrote down about itself.</p>
  <div class="divider"></div>
  <p class="note">This is the Book of Legends, the fourth of the Blood &amp; Grit books and the only one
  anybody at the table may read. There are no rules in it. It holds papers: letters, depositions,
  clippings, company files, sermons, songs, a bank's terms, a child's rhyme. Some of it is true. A
  good deal of it is wrong, and two or three pieces are lies told on purpose by people who are named
  here. Nothing in it is settled, and nothing in it will be.</p>
  <ul class="toc">
    <li><a href="#before">A Word Before</a><span class="pg">3</span></li>
    <li><a href="#basin">I. Papers of the Basin</a><span class="pg">6</span></li>
    <li><a href="#dead">II. The Dead Do Not Stay Put</a><span class="pg">16</span></li>
    <li><a href="#faces">III. A Face Not Their Own</a><span class="pg">24</span></li>
    <li><a href="#hunger">IV. Hunger</a><span class="pg">32</span></li>
    <li><a href="#ground">V. What the Ground Keeps</a><span class="pg">40</span></li>
    <li><a href="#road">VI. Met on the Road</a><span class="pg">48</span></li>
    <li><a href="#paper">VII. Paper, Ink &amp; Interest</a><span class="pg">56</span></li>
    <li><a href="#preaching">VIII. Preaching</a><span class="pg">64</span></li>
    <li><a href="#trades">IX. Them That Make a Living At It</a><span class="pg">72</span></li>
    <li><a href="#weather">X. Weather, and Things Taken for Weather</a><span class="pg">80</span></li>
    <li><a href="#songs">XI. Songs &amp; Sayings of the Territory</a><span class="pg">86</span></li>
    <li><a href="#frauds">XII. Frauds, Errors &amp; Honest Mistakes</a><span class="pg">93</span></li>
    <li><a href="#last">XIII. The Last of the Satchel</a><span class="pg">100</span></li>
  </ul>
</section>
"""


# ---------------------------------------------------------------- A Word Before
BEFORE = f'''
<section class="page" id="before">
  {runhead('A Word Before')}
  <h1 class="chapter">A Word Before</h1>
  <p class="chapter-sub">From the editor, who did not gather any of it.</p>
  <div class="divider"></div>
  <p>These papers were collected by N. Ashby over eleven years, in a satchel, with a pair of
  scissors and more patience than the work deserved. Ashby came west to catalogue animals, did it
  badly, and found this instead. The field-books say so in the first twenty pages and then stop
  apologising.</p>
  <p>The arrangement is mine, and so is everything inside square brackets. I have grouped the papers
  by what they are about, which is the only arrangement that made the book usable, and it has the
  fault every such arrangement has: it puts things side by side that were never near each other, and
  the reader will start seeing a pattern by page forty. I would rather warn you than tidy it.</p>
  <p>Some notes on what you are holding.</p>
  <p><strong>Nothing here is proved.</strong> Not one paper in this book would be admitted as
  evidence, and several of them were thrown out of a courtroom by a judge who is named in them. Where
  two accounts of a night disagree I have printed both and left the disagreement standing. Where a
  paper flatly contradicts Ashby's own note about it, I have printed the note anyway. Ashby was
  wrong in public often enough to have earned the right to be wrong in a book.</p>
  <p><strong>Some of it is lies.</strong> At least two of these documents are jokes played on
  Ashby by men who thought a naturalist with a notebook was fair sport, and I believe I know which
  two, and I have not marked them. One paper in Chapter XII is a forgery. I have printed it because
  the forger, whoever he was, knew a thing he had no way of knowing, and the lie is wrapped around
  it like paper around a fish.</p>
  <p><strong>The dull parts are the point.</strong> There is a page of a store's accounts in
  Chapter IV and a page of a bank's terms in Chapter VII, and readers who skip them will miss the
  worst thing in either chapter. The country does not do its damage in the exciting documents. It
  does it in the ones nobody reads twice.</p>
  <p><strong>Names.</strong> Living people are named where they gave permission and where the paper
  was public anyway. A few names have been left off, and one has been changed, and in that case I
  have said so on the page. Two families asked to be left out entirely and have been, which means
  there are three papers in Chapter II about a house with no name and a county with no name, and
  they read strangely, and I am sorry about it and would do the same again.</p>
  <p>Ashby stopped writing in the autumn of 1884. Chapter XIII is what was in the satchel, in the
  order it was in, and I have added nothing to it and taken nothing out. Readers who want a
  conclusion should stop at Chapter XII, which at least ends with somebody being proved a fraud.</p>
  <p class="note">A note on how to use this at a table: any page of this book can be handed to a
  player as a thing their character has read, been shown, or been sold. It is written to be handed
  over. What the Keeper knows about any of it lives in the Keeper's Book, and the Keeper is not
  obliged to tell you which of these papers is the honest one.</p>
</section>
'''


# ================================================================ I. Papers of the Basin
CH1 = chapter("basin", "I", "Papers of the Basin", "One county, and everything written about it.",
              "I. Papers of the Basin", "\n".join([

 """  <p>More of this book comes out of Perdition Basin than out of anywhere else, and that is an
  accident of where Ashby spent the winters rather than a judgement about the county. It is one
  county of a great many. What it has going for it, as a place to start reading, is that it is small
  enough to hold in the head: three towns, a burned mission, a river that quits in the sand, and
  seven or eight wells that everything else in the basin is arranged around.</p>
  <p>It also has more paper than most counties, because the railroad has been surveying it for two
  years and a surveyor writes everything down.</p>""",

 '  <h2 id="ix-sanclavo">The Register at San Clavo</h2>',
 gloss("Copied by Ashby from the register book at the burned mission, fifteen miles east of Coffin "
       "Wells. The book was in a tin box under a floor that no longer has a building on it. The "
       "Latin and the Spanish are Ashby&rsquo;s translation and are not always good."),
 ledger("Parish register", "Mission of San Clavo, 1809&ndash;1811",
        ["Date", "Entry", "Name"],
        [("11 Sept. 1809", "Arrival of the fathers, three", "Bl&aacute;zquez, Ort&iacute;z, Salgado"),
         ("2 Nov. 1809", "Baptism", "Mar&iacute;a, of the mesa, adult"),
         ("19 Feb. 1810", "Burial", "Fr. Salgado, of a fever"),
         ("4 April 1810", "Well blessed, the second", "&mdash;"),
         ("7 April 1810", "Marriage", "Cardoza and Ybarra"),
         ("1 June 1810", "Well blessed, the fourth", "&mdash;"),
         ("22 Aug. 1810", "Burial, an infant", "Ybarra"),
         ("3 Oct. 1810", "Well blessed, the sixth", "&mdash;"),
         ("14 Dec. 1810", "Baptism", "Tom&aacute;s, of the mesa, adult"),
         ("28 Feb. 1811", "Well blessed, the seventh, and the spring not", "&mdash;"),
         ("9 May 1811", "&mdash;", "&mdash;"),
        ],
        "The entry for 9 May 1811 has a date and nothing after it. The register stops there. The "
        "mission burned in the summer of that year and nobody has ever put a month to it."),
 gloss("On the inside of the back board, in a different hand and much later ink, somebody has kept "
       "a count. It reads <em>seven</em>, and under that <em>six</em>, and under that <em>seven</em> "
       "again, and the last figure has been gone over twice as though the pen had run dry."),
 field("Winter, &rsquo;81", "the mission ground",
       ["Three fathers come out in the autumn of 1809 and by the spring of 1811 they have blessed "
        "seven wells and not the spring on the mesa, and I'd give a good deal to know why not the "
        "spring. Asked at Coffin Wells. Was told the mesa people wouldn't have them, which may be "
        "so and doesn't explain the bookkeeping. A blessing isn't usually a thing you count.",
        "The count on the back board isn't a padre&rsquo;s hand. It's not even a good hand. It has "
        "been added to for a long while by somebody who didn't write much."]),
 ednote("Ashby&rsquo;s sixth well and Ashby&rsquo;s seventh well are not the same wells that the "
        "county calls the sixth and the seventh today. Two were re-dug in the fifties and one moved "
        "a quarter mile. I have not tried to reconcile them and I would not trust anybody who did"),

 '  <h2 id="ix-water">The Water Going Bad</h2>',
 gloss("A letter bought from a woman in Coffin Wells for a dollar, on the condition that her sister "
       "be called only by her initial."),
 paper("Letter", "Coffin Wells, 30 May 1883", p(
     "Dear M.,",
     "You will have had my last and I'm sorry to write again so quick with worse news but the "
     "Dunbar well has gone over now too and that's the third since Easter. It doesn't go bad all "
     "at once. It goes flat first, so you think it's only the dry, and then about a week later it "
     "comes up with a taste like a penny in your mouth, and then the stock won't drink it and "
     "after that neither will anybody.",
     "We are hauling from the town well which is still sweet thank God, but it is eleven trips and "
     "Tom has the wagon out more than he is in the shop. Mrs. Kirby says it is the dry and she has "
     "been here longest so I suppose she knows. But we had a dry in &rsquo;79 that was worse than "
     "this one and the wells held right through it, and I said so, and she didn't answer me, and "
     "that isn't like her.",
     "There have been two buryings this month and one of them was old Mr. Sipes who was eighty-one "
     "so that is nothing, but the other was the Renfro boy who was nine and healthy in April. Adelia "
     "Cruz has been out to the homesteads twice about the fever. She's a sensible woman and she "
     "isn't sleeping.",
     "Write when you can. Tell Ellen the dress came and it fits her cousin and she is to stop "
     "worrying about it."),
     cls="letter", sign="Yr. loving sister, A."),
 wire("Calvary Crossing to Kansas City, 6 June 1883", [
     "VANE TO DRAYTON",
     "THREE WELLS FAILED COFFIN WELLS DISTRICT SINCE APRIL STOP",
     "STOCK VALUES SOFT STOP ADVISE ON NOTES AGAINST RIVER SECTIONS STOP",
     "NO CAUSE FOR ALARM THE DRY IS GENERAL STOP",
 ]),
 ednote("The dry was not general. The weather office at Fort Marcy has the season at eleven inches, "
        "which is a fair year for that country. Mr. Vane is a careful man and I do not think he was "
        "mistaken, and I have printed the wire so the reader can decide what he was doing"),

 '  <h2 id="ix-vane">What the Bank Was Offering</h2>',
 gloss("A printed slip, one of several hundred, handed out at the Coffin Wells bank and left in "
       "stacks at the hotel and the two stores."),
 bill([("bl-3", "The Vane Banking House"), ("bl-1", "LAND MONEY"), ("rule", ""),
       ("bl-2", "Notes written on improved and unimproved sections"),
       ("bl-2", "in the Calvary River bottoms"),
       ("bl-3", "eight per cent &middot; five years &middot; no penalty for early payment"),
       ("rule", ""),
       ("bl-2", "WATER IS A RISK THAT CAN BE BOUGHT"),
       ("bl-3", "Ask about our terms for a section whose well has failed.<br>"
                "We write on the land. The water is your own affair."),
      ]),
 field("March, &rsquo;84", "Coffin Wells",
       ["Read that slip four times before I saw it. He isn't lending against the water. He's "
        "lending against land that has no water, at eight per cent, which is under the rate at the "
        "Crossing. A man whose well has gone will take that money because nobody else will give him "
        "any, and he won't pay it back, because nothing grows on a section with a dead well.",
        "So the bank ends up with the section. And a section with a dead well is worth nothing, "
        "which is what I said to Mr. Vane, and he agreed with me pleasantly and asked after my "
        "health.",
        "Unless the wells come back."]),

 '  <h2 id="ix-mesa">The Painted Mesa</h2>',
 gloss("Two entries from the fourth field-book, four days apart."),
 field("11 Aug., &rsquo;82", "up on the mesa",
       ["Best water I have drunk in this territory and I have drunk out of a good many holes. Cold "
        "in August. There is a stone kerb round it that is older than anything below and it is kept "
        "swept.",
        "Was asked to leave. Politely, by a man of about fifty who gave his name and told me I might "
        "write it down and then said he would rather I did not, so I have not. He said I could come "
        "back and drink and I could not come back and measure. I asked why. He said because I would "
        "write it in a book.",
        "I have written it in a book."]),
 field("15 Aug., &rsquo;82", "Calvary Crossing",
       ["Asked three men at the Crossing about the mesa spring. Got three answers and all of them "
        "were about what the mesa people will not tell, and none of them were about the spring.",
        "It occurs to me that everybody in this county has a theory about the mesa and not one of "
        "them has been up there. I have been up there. What's up there is a spring and a stone kerb "
        "and people who'd like to be left alone about it."]),
 gloss("A statement taken down at the county court at Calvary Crossing during the hearing on the "
       "survey&rsquo;s right of way, February 1884. The witness spoke in his own language and the "
       "court&rsquo;s interpreter is a freighter named Hollis whose command of it was described from "
       "the bench as adequate."),
 depo("County Court, Calvary Crossing", "12 February 1884", [
     ("You are asked whether your people have knowledge of the wells in the bottom of the basin.",
      "He says: we know where they are."),
     ("Knowledge as to why they fail.",
      "He says: they were dug in a bad place by men in a hurry."),
     ("Is that a tradition of your people or your own opinion.",
      "He says it is what anybody can see. The wells that fail were dug where the ground is "
      "wrong. He says there is no mystery in it at all. His grandfather could have told the fathers "
      "as much in 1809 if they had asked him, and they did not ask him."),
     ("The court has heard that your people hold a spring on the mesa which does not fail.",
      "He says: yes."),
     ("Can you say why it does not fail.",
      "[The witness spoke at some length. The interpreter renders it: because we look after it.]"),
     ("Is there more to the answer than that.",
      "The interpreter says there is more but that it is about the looking after and not about the "
      "spring, and that it would take an hour."),
     ("The court has not an hour.", "Then he says the answer is because we look after it."),
 ], closing="The witness was excused. The right of way was granted in April."),
 ednote("I have printed this exchange in full, including the last line of it, which the county "
        "clerk wanted struck and which the judge allowed to stand"),

 '  <h2 id="ix-survey">The Survey&rsquo;s Day-Book</h2>',
 gloss("Four entries from a chainman&rsquo;s day-book, bought at the Crossing for the price of a "
       "new one. The hand is bad and the spelling is his own."),
 paper("Day-book", "railroad survey, Perdition Basin, autumn 1884", p(
     "<strong>Oct 2.</strong> Run 4 mi 18 ch E from the stake at the ford. Ground good. Wind all "
     "day. Mr. Teale says we will be at the mission ground by Satturday.",
     "<strong>Oct 6.</strong> Cut through the low bank W of the mission where the old fill is. "
     "Powder twice. Smell come up out of it that took the men off the line for a half hour, like a "
     "root celler that has been shut, only sweeter, and Dowd was sick. Mr. Teale says it is gas and "
     "is common and I never smelt it before in 3 years.",
     "<strong>Oct 7.</strong> Two men gone in the night, Dowd and the other Dowd. Took their kit "
     "and not their pay which is 11 dollars betwene them and Mr. Teale is put out about the "
     "insult more than the men.",
     "<strong>Oct 9.</strong> Filled the cut back in on Mr. Teale&rsquo;s word and run the line "
     "north of it which is 300 ft longer and he will have to explain it to the office. He has not "
     "said why and I have not asked him. I would of filled it in myself."),
     ),

 '  <h2 id="ix-pell">The Pell Place</h2>',
 gloss("The Pell homestead is nine miles down the river from Calvary Crossing and has been empty "
       "since 1882. What happened there was in the papers at the time and Chapter II has the "
       "clipping. What follows is not about what happened. It is about the rhyme."),
 song("as the children at Calvary Crossing sing it", [
     ["Who&rsquo;s in the barn, who&rsquo;s in the barn,",
      "counting up to seven?",
      "Mother in the barn, mother in the barn,",
      "and she come up from the cellar."],
     ["Don&rsquo;t you tell your father,",
      "don&rsquo;t you tell the man,",
      "don&rsquo;t you tell the lady with the lamp",
      "how many hands you can."],
 ], "taken down at the schoolhouse, May 1884"),
 field("May, &rsquo;84", "Calvary Crossing",
       ["Nine children, four of them under seven. All of them have it. None of them can say who "
        "taught it to them and two of them told me, separately, that it is just a song, which is "
        "what a child says when a grown person asks a question in a certain voice.",
        "The trouble is the cellar. There was no cellar in the newspaper and there is no cellar in "
        "the marshal&rsquo;s report, which I have read. There is a cellar at the Pell place, and I "
        "have stood in it, and four people in this county know that and one of them is me.",
        "The teacher says they've had it about a year. Mrs. Pell died in the spring of &rsquo;82."]),
 ednote("Ashby&rsquo;s count is wrong here, and it matters how. The cellar is in the coroner&rsquo;s "
        "return, which was public from the first, and anybody in the county who wanted to read it "
        "could have. What is not in the coroner&rsquo;s return, or anywhere else I can find, is the "
        "number seven"),

 '  <h2 id="ix-saltlick">Two Nights at Saltlick</h2>',
 gloss("The same night, or two nights, at the stage relay on the road between the Crossing and "
       "Coffin Wells. The first is the driver&rsquo;s report to the line, which he was paid to "
       "write. The second is from a passenger&rsquo;s letter, written to her husband the next day, "
       "and came to Ashby through the woman herself, who thought the whole business was funny."),
 paper("Report to the line", "Overland &amp; Territorial, 3 January 1884", p(
     "Down coach, the 2nd, arrived Saltlick 8.40 in the evening, four hours behind on account of "
     "the ford. Changed team. Stationmaster reports the near well low and drawing muddy, which I "
     "have reported before.",
     "One passenger delayed our departure by twenty minutes and I have entered the delay against "
     "the company rather than the passenger as she was in distress. Departed 9.20 and arrived "
     "Coffin Wells 1.10 in the morning without further incident."),
     sign="J. Otey, driver"),
 paper("Letter", "Coffin Wells, 3 January 1884", p(
     "&hellip; and I wouldn't have written any of it down except you'll hear it from Cousin Ruth "
     "in a worse shape than it happened, so here it is straight.",
     "There was a man at the relay who came in off the road after us and sat by the stove and did "
     "not eat. He was dressed like a picture in a book, Robert, an actor is what I thought, and he "
     "was perfectly courteous and he asked after my family. Not in the way a stranger does. He asked "
     "after Aunt Bess by her name and asked whether her knee had mended, and it has, and I have not "
     "said one word about Aunt Bess in that country to any living soul.",
     "Then he said something about my brother that was wrong. He said Will, when it's Walter, and "
     "he said it twice, and the second time I heard myself agreeing with him. That's the part I "
     "haven't got over. I sat there and agreed that my brother is called Will.",
     "I went out and stood by the coach until Mr. Otey was ready and I was twenty minutes about it "
     "and I'm not sorry. When I looked back in he was gone and the stationmaster said there'd "
     "been no one at the stove all evening, and then he looked at the chair, and then he didn't say "
     "anything else."),
     cls="letter", sign="Your Jane",
     ps="Don't tell your mother. She'll want to write to somebody about it."),
 ednote("The driver was paid by the line and wrote what the line wanted, which is that the delay "
        "was the company&rsquo;s fault. I am not sure that makes him a worse witness than the lady. "
        "He puts a woman in distress at the relay for twenty minutes and he does not say why, and "
        "a man who is inventing a quiet evening does not put that in"),
]))


# ================================================================ II. The Dead Do Not Stay Put
CH2 = chapter("dead", "II", "The Dead Do Not Stay Put",
              "Burials that did not take, and the paperwork they generated.",
              "II. The Dead Do Not Stay Put", "\n".join([

 """  <p>This is the largest chapter and the dullest, and I have kept it that way. Almost
  everything in it is official. Coroners, marshals, undertakers and church registers write about the
  dead all the time in the ordinary way of business, and the interesting thing about the papers
  below is not that they are hair-raising. It is that they are not. A clerk who has decided to
  record a thing will record it in the same hand he uses for a drowned calf.</p>
  <p>Read the returns first and the letters after. The returns are what the county was willing to
  write down.</p>""",

 '  <h2 id="ix-coroner">A Coroner&rsquo;s Returns, One Year</h2>',
 gloss("Nine entries from the returns of a county coroner, out of two hundred and six for that "
       "year. The county is not named at the family&rsquo;s request and neither is the coroner, who "
       "is still in the office and would like to stay in it."),
 ledger("Coroner&rsquo;s returns", "one county, one year",
        ["No.", "Finding", "Note in the margin"],
        [("#17", "Exposure", "found 200 yds from his own door, facing away"),
         ("#41", "Drowning", "the ford was dry that week"),
         ("#62", "Heart", "&mdash;"),
         ("#88", "Drowning", "second of this family at the same bend"),
         ("#103", "Undetermined", "see 17"),
         ("#140", "Exposure", "in June"),
         ("#155", "Heart", "the widow disputes; see her letter filed herewith"),
         ("#171", "Undetermined", "coffin opened at the family&rsquo;s request, nothing wanting"),
         ("#198", "Drowning", "see 88, and see 41"),
        ],
        "Two hundred and six returns, of which eleven are marked <em>undetermined</em>. The "
        "state&rsquo;s average that year was two in a hundred."),
 ednote("Ashby made a great deal of the eleven. I would point out that this coroner rides a circuit "
        "of ninety miles and sees perhaps a third of his cases inside a week of death, and that "
        "<em>undetermined</em> in his hand very often means <em>I got there on Thursday</em>"),

 '  <h2 id="ix-pellnews">The Pell Place, as Printed</h2>',
 gloss("The clipping Chapter I mentions. It is the only account that was ever printed and the "
       "family had no hand in it."),
 news("THE CALVARY CROSSING BANNER", "18 April 1882",
      ["SHOCKING AFFAIR DOWN THE RIVER", "THE PELL FAMILY"],
      ["Three Dead and the House Standing Empty", "Marshal Coyle Attends"],
      ["A distressing business has come to light at the Pell homestead, nine miles below this "
       "town, where on Tuesday last Mr. Coyle, our marshal, was called by a neighbour and found "
       "the place deserted and the stock unwatered.",
       "Of the family of five, three are accounted for and lie now in the ground at this place. "
       "Mrs. Pell was found in the house. The two younger children are supposed to have gone to "
       "the river, which was high, and the search has been given over. Mr. Pell has not been "
       "found and the marshal is satisfied that he is not to be looked for in the county.",
       "We understand that a quantity of flour, salt and ammunition was left in the house "
       "untouched, which does not support the view, put about in this town by persons who were "
       "not there, that the family was set upon by parties unknown. Our own opinion is that the "
       "fever which has been among the homesteads is explanation enough, and we say so "
       "in the hope of hearing no more of the other.",
       "The barn was burned by the marshal&rsquo;s order on the Thursday, as a precaution against "
       "contagion. Subscribers who wish to assist the surviving child may leave their names at "
       "this office."]),
 ednote("The surviving child is not mentioned anywhere else in the paper, before or after, and "
        "there were five in the family and three are accounted for and two went to the river. The "
        "arithmetic in this notice does not work and it ran uncorrected for three years"),

 '  <h2 id="ix-returned">A Boy Who Came Back</h2>',
 gloss("Two letters, seven weeks apart, from a woman on the lower river to her own mother. Bought "
       "from a third party after both women were dead. Ashby paid two dollars and recorded that he "
       "felt poorly about it."),
 paper("Letter", "the lower river, 2 June", p(
     "Mother, the river took Asa on the Thursday. He was crossing at the bar with the mule and the "
     "water was not high, you have seen it lower a hundred times, and it took him anyhow. We looked "
     "four days. Ned found the mule.",
     "There's nothing to bury and that's the part I can't manage. Reverend Teague came out and "
     "was kind and said the words over the bar, which was good of him, and I stood there and "
     "thought, this is a river and I'm saying goodbye to a river.",
     "Do not come. The roads are bad and you would only be sad in a different house."),
     cls="letter", sign="Your Ettie"),
 paper("Letter", "the lower river, 21 July", p(
     "Mother, don't tell anybody what's in this letter, not Aunt Lou and not the Reverend.",
     "Asa come home on the 9th. He walked up from the bar in the evening, in his own clothes, and "
     "his boots were wet and nothing else was. He's thin. He doesn't eat much and he sleeps in "
     "the daytime, and he hasn't said above twenty words, but he knows me and he knows Ned and "
     "yesterday he mended the gate the way his father used to, with the wire wrapped the wrong way "
     "round, which is how I knew.",
     "Ned wants to take him to the doctor at the Crossing. I won't have it. They'll take him "
     "off me and put him somewhere and write about him in a paper. He's quiet and he's no trouble "
     "and he's mine.",
     "I know what you'll say. I've said all of it to myself already, at two in the morning, "
     "every night since the 9th. And then I go and look at him asleep and he's my son.",
     "Burn this."),
     cls="letter", sign="Ettie", ps="He don't like the lamp. We sit in the dark mostly and it's "
     "easier for everybody."),
 ednote("She did not burn it. I have thought about whether to print it more than I have thought "
        "about anything else in this book, and I have printed it because there are a great many "
        "women in this country in that house, at two in the morning, and not one of them thinks "
        "anybody else is"),

 '  <h2 id="ix-undertaker">The Undertaker&rsquo;s Book</h2>',
 gloss("Extracts from the day-book of an undertaker at a cattle town, kept for thirty-one years. "
       "The italics are his own, and he used them for exactly one purpose, which the reader will "
       "work out."),
 paper("Day-book", "an undertaker, 1868&ndash;1885", p(
     "<strong>1871, Mch.</strong> Coffin, plain, for the Mims child. Paid.",
     "<strong>1874, Aug.</strong> Coffin, lined, for Mr. Whately of the bank. <em>Screwed.</em> "
     "Paid by the estate.",
     "<strong>1878, Jan.</strong> Two plain, the brothers off the drive. <em>Screwed both.</em> "
     "Not paid, and I did not ask.",
     "<strong>1881, Nov.</strong> Coffin, plain, for the woman found at the crossing. "
     "<em>Screwed, and stone on it.</em> Paid by subscription.",
     "<strong>1884, June.</strong> Coffin, lined, Mrs. Hackney. <em>Screwed.</em> The family "
     "objected to the screws and I explained it was the damp and they were satisfied.",
     "<strong>1885, Feb.</strong> Coffin, plain. <em>Screwed, stone, and I sat up with it.</em> "
     "Not paid. Nobody to pay."),
     ),
 field("Sept., &rsquo;85", "a cattle town",
       ["He screws about one in nine. I counted it up: thirty-one years, four hundred and forty "
        "coffins, "
        "forty-nine screwed and eleven of those with a stone laid on as well.",
        "Asked him what decides it. He said, the damp. I said, in February. He said, the damp, and "
        "poured me a drink, and we talked about the price of lumber for an hour and he is a pleasant "
        "man and I liked him very much.",
        "On the way out I asked him one more, which was whether he had ever been wrong. He said he "
        "had been wrong twice in thirty-one years, and that he screws every one he is not sure of, "
        "and that is why he has only been wrong twice."]),

 '  <h2 id="ix-swarm">The Business at the Old Burying Ground</h2>',
 gloss("A marshal&rsquo;s report, filed with the county and afterwards amended. Both versions "
       "survive because the clerk bound the first one in before the amendment came."),
 paper("Marshal&rsquo;s report, first version", "filed 4 October", p(
     "Called out to the old burying ground on the north side at about eleven at night by Mr. "
     "Laidlaw, who was in liquor but not so much as to signify.",
     "Found the ground disturbed in nine or ten places and the fence down on the east. Found four "
     "persons deceased above the ground who had not been above the ground on the Sunday, which I "
     "know because I walked it on the Sunday.",
     "Was obliged to discharge my weapon. I state plainly that I do not know what I was shooting "
     "at and that I hit it four times out of six and that it went on for a considerable while "
     "after that and then went down when Mr. Laidlaw struck it with a spade.",
     "I have asked the county for lamps and for two men and I will ask again."),
     sign="T. Coyle, marshal"),
 paper("Marshal&rsquo;s report, as amended", "filed 11 October", p(
     "Called out to the old burying ground on the north side at about eleven at night by Mr. "
     "Laidlaw.",
     "Found the ground disturbed by animals and the fence down on the east. Four graves opened. "
     "The remains were re-interred on the Monday at county expense.",
     "Was obliged to discharge my weapon at an animal, which was afterwards destroyed by Mr. "
     "Laidlaw with a spade. I have asked the county for lamps and for two men."),
     sign="T. Coyle, marshal"),
 ednote("The second report is a better report. It is shorter, it is clearer, it accounts for "
        "everything, and a county commissioner reading it would have no questions, which was the "
        "idea. I would only note that the animal in it is destroyed with a spade after being shot "
        "four times, and that no one asked what kind"),
]))


# ================================================================ III. A Face Not Their Own
CH3 = chapter("faces", "III", "A Face Not Their Own",
              "People who were not who they were, and the professionals who explained them.",
              "III. A Face Not Their Own", "\n".join([

 """  <p>Every county in the Territories has one of these stories and most of them are about
  bigamy. A man turns up somewhere he is not supposed to be, under a name that is not the one on his
  church roll, and the explanation is nearly always that he has a second wife and a first wife and
  a schedule. I have read forty of these and thirty-six were exactly that.</p>
  <p>The four that were not are in this chapter, with one of the thirty-six put in among them, so
  that the reader has the experience of not knowing which.</p>""",

 '  <h2 id="ix-agency">The Agency File on Cyrus Teal</h2>',
 gloss("A copy of a detective agency&rsquo;s summary file, of the kind an agency sells to a client "
       "at the close of a matter. How Ashby came by it is not recorded and I have not enquired."),
 filedoc("Agency file", "matter of C. Teal, closed",
         ["Subject presents as a commercial traveller in agricultural implements, aged about "
          "forty, of good address and no fixed residence. Employed by Renfro &amp; Sons of Kansas "
          "City between 1879 and 1882.",
          "Client&rsquo;s complaint is that subject obtained goods and credit at four towns under "
          "the name Teal and at two further towns under the names Teale and Tweel, and that the "
          "descriptions given by the several merchants do not agree as to height, hair or age.",
          "This office finds the variance in descriptions unremarkable. Merchants are poor "
          "witnesses and describe the coat.",
          "Subject was observed by this office at Coffin Wells on the 3rd and at Calvary Crossing "
          "on the 3rd. The two towns are twenty-seven miles apart. This office concludes that "
          "there are two men and that the second is a confederate, and recommends the client "
          "proceed on that footing.",
          "Subject&rsquo;s wife at Topeka, interviewed, states that her husband has been at home "
          "since November and produces a church roll and three neighbours in support. This office "
          "considers the Topeka woman to be mistaken as to dates, women in such matters commonly "
          "being so.",
          "Matter closed. Recovery not recommended. Fee rendered."]),
 ednote("Paragraph 5 is the whole file in one line. Three neighbours and a church roll were set "
        "against an operative&rsquo;s opinion about women, and the operative&rsquo;s opinion won, "
        "and the client paid for it. I print this chapter partly because the Agency is very good at "
        "what it does and partly because of paragraph 5"),
 field("June, &rsquo;83", "Coffin Wells",
       ["Went to see the man at the implement office who sold to Teal. Asked him to describe the "
        "customer and he did it well and in detail and it took him two minutes.",
        "Then I asked him to describe the man who had come in the week before Teal, who was a "
        "stranger too, and he could not do it at all. Could not say hair, coat, age or business.",
        "So he is not a poor witness. He is a good witness who remembers one stranger out of two, "
        "and the one he remembers is the one the Agency says he made up."]),

 '  <h2 id="ix-fivewives">The Man at Gurley&rsquo;s</h2>',
 gloss("Testimony at a coroner&rsquo;s inquest. The deceased was a hand at a road ranch called "
       "Gurley&rsquo;s. The witness is the cook."),
 depo("an inquest, the road ranch at Gurley&rsquo;s", "September", [
     ("How long had you known the deceased.", "Five years, near enough."),
     ("Did you know him well.", "I fed him twice a day for five years."),
     ("Did you notice any change in him in the last month.",
      "He got easier to be around."),
     ("Explain that.",
      "He was a sour man. He had been sour five years. About the middle of August he got pleasant "
      "and he stayed pleasant and he remembered my name, which he had never used once in five "
      "years, and he used it every day after."),
     ("Is a man becoming pleasant a matter you would report to a coroner.",
      "You asked me what I noticed."),
     ("Did he eat as before.", "He ate more. He ate a great deal more and he did not get fat."),
     ("Anything further.",
      "He couldn't whistle. He used to whistle all day, one tune, and it drove us to distraction, "
      "and after the middle of August he never whistled once. I asked him to and he laughed and "
      "said he'd forgot how."),
     ("You are aware that a man may forget a tune.",
      "I am aware of it. I'm telling you what I noticed, and that's what I noticed, and you've "
      "written down the pleasant part and left out the whistling part, and I want the whistling "
      "part written down."),
 ], closing="[The coroner directed that the last answer be recorded in full. Verdict: heart.]"),

 '  <h2 id="ix-mirror">What the Photographer Would Not Print</h2>',
 gloss("A bill of account and a letter attached to it, from a portrait photographer at a territorial "
       "capital, to a customer."),
 paper("Letter with an account", "a portrait studio, 14 November", p(
     "Dear Madam,",
     "I return your deposit in full and I will not be taking the sitting further, and I would "
     "rather tell you the truth about it than invent a reason.",
     "The plates are good. I made four and all four are sharp and correctly exposed and I have "
     "examined them under the glass for three days. In every one of them your husband&rsquo;s "
     "hands are wrong. I do not mean poorly placed. I mean that the hands in the plate are not the "
     "hands that were in my studio, and I looked at his hands for an hour on the Tuesday while I "
     "was posing him, because he has a mark on the left one and I was arranging the light to keep "
     "it out of the picture.",
     "There is no mark in any of the four plates. There is no mark, and there is an extra joint in "
     "the third finger, and I have shown the plates to Mr. Doss who has been in this trade twenty "
     "years and he went white and asked me to take them off his counter.",
     "I have broken the plates. I am sorry about the deposit and I have returned it and I would "
     "be obliged if you did not recommend me to your friends for a while.",
     "I will say one more thing and then I have done. Your husband was perfectly agreeable "
     "throughout and he thanked me twice, and when I told him the sitting had failed he said, "
     "before I had said why, that it was the hands."),
     cls="letter", sign="Yr. obedient servant, W. Boothe"),

 '  <h2 id="ix-thirtysix">One of the Thirty-Six</h2>',
 gloss("A letter from a woman at Dodge to a woman at Trinidad, forwarded twice, ending up in a "
       "lawyer&rsquo;s file and thence to Ashby. This is the one I warned you about in the opening "
       "of this chapter, and I have not marked which of the four the impostor is, and I am not "
       "going to."),
 paper("Letter", "Dodge City, 7 March", p(
     "Mrs. Yeager,",
     "You do not know me and I am sorry to be the one. The man you married in November is my "
     "husband and has been since 1876 and we have two boys.",
     "I am not writing to make trouble for you. I have seen the description and I have seen the "
     "signature on the certificate and it is his hand and I would know it anywhere. I am writing "
     "because he told you he was a widower and he told me he was in Denver on the railroad, and "
     "one of us was going to find out and I would rather it was both of us at once and by letter.",
     "I have written to the sheriff at Trinidad. I have not written to the church.",
     "If he comes back to you before he comes back to me, do not tell him I wrote. He is not "
     "violent and I am not afraid of him. He is only a liar, and he is a very restful liar to live "
     "with, which is the part nobody believes."),
     cls="letter", sign="Mrs. E. Puckett"),
 ednote("Restful is the word that decided me to print it here rather than in Chapter XI. Every "
        "other witness in this chapter says the same thing in worse English: the man was easy to "
        "be around, the man was pleasant, the man thanked me twice. It proves nothing whatever. It "
        "is only that I noticed"),
]))


# ================================================================ IV. Hunger
CH4 = chapter("hunger", "IV", "Hunger",
              "Parties that went in with provisions, and what the store sold them.",
              "IV. Hunger", "\n".join([

 """  <p>There is a kind of story in this country that always comes with a list. Somebody totals up
  the flour and the bacon and the beans that went into the mountains with a party, and divides by
  the number of people and the number of days, and then says <em>so you see</em>. The arithmetic is
  meant to settle it one way or the other and it never does, because a list of provisions tells you
  what was bought and not what was eaten.</p>
  <p>I have put the lists in anyway. Chapter IV is the one with the accounts in it, and I said in
  the front of this book that the accounts are the worst of it, and I meant this chapter.</p>""",

 '  <h2 id="ix-ellender">The Ellender Party</h2>',
 gloss("The best-known of these and the one with the most paper. Nineteen people went up the north "
       "fork in the autumn of 1871 with three wagons. Four came out in the spring."),
 ledger("Store account", "outfitting of the Ellender party, 14 September 1871",
        ["Item", "Quantity", "&pound; s. d."],
        [("Flour", "1,400 lb.", "#$42.00"),
         ("Bacon, side", "600 lb.", "#$54.00"),
         ("Beans", "400 lb.", "#$12.00"),
         ("Coffee, green", "80 lb.", "#$16.00"),
         ("Sugar", "120 lb.", "#$13.20"),
         ("Salt", "200 lb.", "#$4.00"),
         ("Powder and lead", "&mdash;", "#$31.50"),
         ("Two stoves", "&mdash;", "#$44.00"),
         ("Sundries, per list", "&mdash;", "#$28.75"),
        ],
        "Total $245.45, paid in coin by Mr. J. Ellender. The store&rsquo;s own note at the foot of "
        "the account reads: <em>a good outfit, and I told him so.</em>"),
 field("Aug., &rsquo;79", "the north fork",
       ["Nineteen people, a hundred and sixty days, fourteen hundred pounds of flour. That is a "
        "little under half a pound of flour a day each with the bacon and beans on top of it, which "
        "is short commons and is not starvation, and the four who came out said they ran out at "
        "Christmas.",
        "Christmas is a hundred and two days. They ate a hundred and sixty days of flour in a "
        "hundred and two, which is a thing that happens to every party that ever went into "
        "mountains, and it is the dullest explanation in the world and I believe it.",
        "What I cannot make come out is the bacon. Six hundred pounds of side bacon was found in "
        "the spring, in the second wagon, under a tarpaulin, packed and sound and not touched.",
        "They starved forty feet from six hundred pounds of bacon."]),
 gloss("A letter from one of the four who came out, written eight years afterwards to a man who had "
       "asked her about it for a newspaper. She did not answer his questions and she answered "
       "something else."),
 paper("Letter", "9 February 1879", p(
     "Sir,",
     "You ask whether we knew about the second wagon and the answer is that of course we knew. "
     "We had loaded it in September.",
     "I will tell you the only thing about that winter that is worth your ink. In the middle of "
     "December we stopped talking about food. Not because we were being brave. Because it went "
     "out of our heads, the way a word will. My brother-in-law walked past that wagon every day "
     "for nine weeks to get to the wood and it never once occurred to him, and he was the one who "
     "packed it.",
     "In March a man came up from below and the first thing he said was about the wagon, and all "
     "four of us turned round and looked at it, and it was as if it had been carried in that "
     "morning. I have never been able to describe what that felt like to anybody who was not "
     "there, and I am not going to do a good job of it for a newspaper.",
     "I would rather you did not print my name. Print what you like about the rest of it, "
     "everybody else has."),
     cls="letter", sign="[name withheld at her request]"),
 ednote("Ashby wrote in the margin of this letter: <em>appetite is not the thing that was wrong "
        "with them. Forgetting was.</em> I let the note stand because he was pleased with it, and I "
        "will add that a party that has decided to do a thing it cannot admit to will also stop "
        "talking about food, and will also not look at the wagon"),

 '  <h2 id="ix-glutton">A Homestead&rsquo;s Winter Accounts</h2>',
 gloss("Kept by a woman on a claim in the eastern part of the basin. She was keeping them to argue "
       "with a merchant about a bill and they are exact for that reason."),
 ledger("Household account", "a homestead, October to January",
        ["Week ending", "Flour drawn", "Note"],
        [("Oct. 7", "14 lb.", "the usual"),
         ("Oct. 14", "14 lb.", "&mdash;"),
         ("Oct. 21", "15 lb.", "Ned&rsquo;s brother stopping"),
         ("Oct. 28", "14 lb.", "&mdash;"),
         ("Nov. 4", "19 lb.", "cannot account for this"),
         ("Nov. 11", "26 lb.", "&mdash;"),
         ("Nov. 18", "31 lb.", "asked the children. nothing"),
         ("Nov. 25", "40 lb.", "bin half down and it was full at Michaelmas"),
         ("Dec. 2", "44 lb.", "put a lock on"),
         ("Dec. 9", "44 lb.", "lock not touched"),
         ("Dec. 16", "51 lb.", "&mdash;"),
        ],
        "The account stops on 16 December. On the back of the last sheet, in the same hand: "
        "<em>we are none of us hungry. That is what I cannot get anybody to attend to. Nobody in "
        "this house has been hungry since November and the flour is going.</em>"),

 '  <h2 id="ix-thirst">The Dry Camp</h2>',
 gloss("From the report of an army surgeon attached to a detachment that came on the remains of a "
       "small party in the badlands south of the basin. The report was written for the "
       "quartermaster and is concerned mainly with the disposal of property."),
 paper("Surgeon&rsquo;s report", "detachment in the badlands, 21 July", p(
     "Four persons, adult, male, deceased not less than eleven days by my estimate and not more "
     "than sixteen. Cause in each case is thirst and exposure and I have so certified.",
     "Property: four horses, deceased; two rifles; one Bible; forty-one dollars in coin; two "
     "canteens, one of them full.",
     "I draw the quartermaster&rsquo;s attention to the second canteen. It holds three pints and "
     "it was stoppered and it was three feet from the nearest of the four. I have no explanation "
     "to offer and it is not my business to offer one. I record it because an inventory that "
     "leaves it out would be false.",
     "The party was two and a half miles from the seep at the head of the draw, which is marked on "
     "the map they were carrying, which was in the pocket of the man nearest the canteen, folded "
     "to the correct sheet."),
     sign="Asst. Surgeon, U.S.A."),
 ednote("This is the document in this book that I think about. Everything else here can be "
        "explained by fear, drink, grief or a bad map. Four men, a marked map, two and a half miles, "
        "and a full canteen. I have shown it to a doctor who says that a man far gone in thirst will "
        "do incomprehensible things, which is true, and which is not an explanation, and he agreed "
        "that it was not"),
]))


# ================================================================ V. What the Ground Keeps
CH5 = chapter("ground", "V", "What the Ground Keeps",
              "Mines, cuts, diggings, and the things that came up with the spoil.",
              "V. What the Ground Keeps", "\n".join([

 """  <p>Mining country generates more paper per man than any other work in the Territories, because
  every foot of it is somebody&rsquo;s property and property is written down. Assays, timber
  orders, shift books, coroner&rsquo;s findings, and the long courteous correspondence between a
  superintendent on the ground and an office two thousand miles away that does not believe him.</p>
  <p>The correspondence is the best of it. A superintendent cannot say what he means, because the
  office will take the mine off him, so he says it in the only language the office respects, which
  is cost.</p>""",

 '  <h2 id="ix-assay">The Assay and What Followed</h2>',
 gloss("An assayer&rsquo;s certificate and the first four letters of a correspondence that ran to "
       "thirty-one. The mine is not named because it is working today and the company has lawyers."),
 paper("Assay certificate", "a territorial assay office, 2 May", p(
     "Sample as received, marked <em>No. 4 level, east drift, face</em>, weight 11 oz.",
     "Silver: 412 oz. per ton. Lead: 61 per cent. Gold: trace.",
     "Remarks: I have assayed for this district eleven years and I have not had a sample like it. "
     "I ran it three times. The ore is clean and the values are real and I will stand behind the "
     "figures. I would want to see the face before I told anybody to sink on it."),
     sign="per the assayer"),
 paper("Superintendent to the office", "12 May", p(
     "Gentlemen, I enclose the certificate and I recommend we do not follow the east drift.",
     "I am aware of how that reads against 412 ounces. My reasons are these. The face is in a "
     "seam that does not run with the country rock and does not behave like any silver I have "
     "worked. It is warm. I have taken the temperature at the face on four days and it is nineteen "
     "degrees above the drift behind it, and there is no water and no dead air to account for that.",
     "The men will not work it past the second hour. I have paid a bonus and they took the bonus "
     "and came out at the second hour, and these are men I have had six years."),
     sign="Yrs., the superintendent"),
 paper("The office to the superintendent", "3 June", p(
     "Sir, your letter of the 12th ultimo.",
     "The Board has considered your reasons and finds them insufficient to set against an assay of "
     "412 ounces. You will proceed on the east drift.",
     "As to the men, the Board observes that a bonus which is taken and not earned suggests a "
     "want of firmness. You will please regulate it."),
     sign="per the Secretary"),
 paper("Superintendent to the office", "19 June", p(
     "Gentlemen, I am proceeding on the east drift as instructed.",
     "I am obliged to report the following costs against it, which I set out so the Board may have "
     "them before the next quarter. Timber in the east drift is running four times the mine "
     "average, and I will explain why. The sets do not stay square. I have re-timbered eighty feet "
     "twice in five weeks and the ground has not moved by the level and I cannot tell the Board "
     "what is doing it.",
     "Candles are running eleven times the mine average. I have looked into pilfering and there is "
     "none. The men are carrying four where they carried one because of what happens to a candle in "
     "that drift, which I will not set down in a letter to a Board, and which any of them will tell "
     "you for the price of a drink at the surface.",
     "I have hired nine men in five weeks and I have nine fewer men than I had in April.",
     "I remain willing to be overruled and I would like this letter kept."),
     sign="Yrs., the superintendent"),
 ednote("It was kept. All thirty-one were kept, and bound, and the Board went on overruling him for "
        "another four months, and the letter that closes the file is from a different "
        "superintendent"),

 '  <h2 id="ix-veinwork">The Thing in the Spoil</h2>',
 gloss("A single sheet, torn from a shift book, sold to Ashby by a man who said he had taken it out "
       "of the office at the time of the closure. Ashby noted that he did not believe the man about "
       "how he came by it and did believe him about the rest."),
 paper("Shift book", "night shift, a mine in the high country", p(
     "<strong>10.40.</strong> Blast in the winze. Good break.",
     "<strong>11.15.</strong> Mucking out. Jessup reports a piece in the spoil that is not rock "
     "and not timber. Sent it up.",
     "<strong>11.50.</strong> Piece is at the office. It is about the size of a forearm and the "
     "weight of one. It is grey and it is jointed and it is not a fossil, Mr. Wray has seen the "
     "fossils at Denver and says not.",
     "<strong>12.20.</strong> Two men off shift, no reason given, pay to follow.",
     "<strong>1.05.</strong> Piece has changed position on the desk. Office was locked and I have "
     "the key on me. I am writing this down because I have been told to write everything down and "
     "I am going to keep doing it.",
     "<strong>1.30.</strong> Put it in the safe.",
     "<strong>2.00.</strong> Nothing to report.",
     "<strong>2.30.</strong> Nothing to report.",
     "<strong>3.00.</strong> Nothing to report and I would like it on the book that I have not "
     "opened the safe."),
     ),
 ednote("The mine closed eleven days later and the closure is on the record as a fall in the "
        "price of lead, which was real, and was eleven per cent, and closed no other mine in that "
        "district that season"),

 '  <h2 id="ix-cut">A Petition from the Chainmen</h2>',
 gloss("Signed by fourteen men and one mark, and handed to a railroad survey&rsquo;s chief of party. "
       "It was refused and kept."),
 paper("Petition", "a survey camp, 8 October", p(
     "To Mr. Teale, chief of party.",
     "We the undersigned ask that the line be run north of the old fill at the mission and not "
     "through it. We are not asking for money and we are not asking for a day off.",
     "We know the north line is three hundred feet longer and we know that is a thing you will "
     "have to explain to the office and we are sorry for it. We will work the extra without extra "
     "pay and we will work Sunday to make it up and you may hold us to that.",
     "We are not able to say in writing why we are asking. Every man here has said it out loud to "
     "you separately and you have listened to us every time and we know you have. We are putting "
     "it in writing so that if the office asks you why the line moved, you have a paper, and it is "
     "our names on it and not yours."),
     sign="[fourteen signatures and one mark]"),
 field("Nov., &rsquo;84", "the survey camp",
       ["Teale showed it to me himself. He's kept it in his coat since October and it's coming "
        "apart on the folds.",
        "He refused it on the day and moved the line the week after and told the office it was the "
        "grade. He says if he'd granted the petition he'd have had to write down what it was for, "
        "and there's no line on a survey return for what it was for.",
        "I asked him what he thought was in the fill. He said it was not his business what was in "
        "the fill, and then he said, after a while, that he had been down in the cut on the sixth "
        "and that he had come up, and that he is forty-one years old and has not been frightened by "
        "anything since the war."]),
]))


# ================================================================ VI. Met on the Road
CH6 = chapter("road", "VI", "Met on the Road",
              "Travellers nobody could place, and the details they got wrong.",
              "VI. Met on the Road", "\n".join([

 """  <p>The road story is the commonest thing in this book and the hardest to do anything with. A
  man meets somebody at an hour when the road should be empty, they talk, and afterwards he cannot
  account for the conversation. There are hundreds of these. Ashby collected two hundred and eleven
  and thought about them for years and got no further than a list of what they have in common.</p>
  <p>Here is the list, in his hand, and then the papers.</p>""",

 field("undated", "the front of the seventh field-book",
       ["Things the road stories agree about, out of 211:",
        "He is met on a road, at an hour when nobody is on it, going the other way. He is courteous "
        "without exception. He knows the traveller&rsquo;s business before it is told him. He asks "
        "after the traveller&rsquo;s people by name. He takes nothing, is offered food and refuses "
        "it, and is never seen to arrive or to leave.",
        "And he gets one detail wrong. One, never two. Always a detail about the traveller&rsquo;s "
        "own family, and always one the traveller does not catch at the time.",
        "I don't know what to do with this. Two hundred and eleven people in nine counties are "
        "describing the same encounter, and either that's one thing on the roads, or it's what a "
        "story turns into when it has been passed along enough times, and I haven't found a way to "
        "tell those two apart and I've stopped expecting to."]),

 '  <h2 id="ix-wrongdetail">Three of the Two Hundred and Eleven</h2>',
 gloss("Chosen because the wrong detail is different in each, and because all three people were "
       "still alive when Ashby took the account and gave permission for it."),
 paper("Account", "a freighter, on the road below Saltlick", p(
     "He came up alongside about an hour before light and rode with me eleven miles and I never "
     "did see his horse properly.",
     "He asked after my mother, by name, and asked whether she still kept the grey cat. She does. "
     "He asked about my brother in Sacramento, and I have a brother in Sacramento.",
     "The wrong thing was my wife. He called her Margaret. Her name is Martha and has been for "
     "nineteen years, and I said yes when he said it, and I didn't think about it again until I "
     "was unhitching at the Crossing the next afternoon and I stopped with the strap in my hand.",
     "I have a sister called Margaret. She died in 1861 and I hadn't said her name out loud in "
     "ten years."),
     ),
 paper("Account", "a schoolteacher, on the Llano road", p(
     "It was the middle of the afternoon, which is the only thing in my account that does not fit "
     "the others, and I have been told so by three people who were not there.",
     "He was dressed old. I took him for an actor. He knew my father was a printer, which is true "
     "and is not a thing you can tell by looking.",
     "The wrong detail was the town. He said Fayette and I am from Fayetteville, and those are two "
     "different places six hundred miles apart, and I corrected him and he apologised very "
     "handsomely, and then a quarter of a mile later he called it Fayette again.",
     "My grandfather was born at Fayette. I did not know that until I wrote to my aunt about this "
     "business last year."),
     ),
 paper("Account", "a girl of fourteen, on the north road, given in the presence of her mother", p(
     "He asked was I Mr. Odom&rsquo;s girl and I said yes and he said tell your father the well "
     "will do another two years and then he is to dig at the cottonwood.",
     "That is all of it. He did not ask me anything else and he did not say anything else "
     "and he went on.",
     "The wrong part is my father isn't Mr. Odom. Mr. Odom has the place next to ours and he "
     "hasn't any children. I didn't say so at the time because I was frightened, and I've "
     "thought since that I ought to have."),
     ps="[Ashby&rsquo;s note: the Odom well failed in the third year, not the second. He did not dig "
     "at the cottonwood. There is no cottonwood on the Odom place and there is one on hers.]"),

 '  <h2 id="ix-spaniard">The Mad Spaniard</h2>',
 gloss("Four hundred miles of road know this one and nobody uses a name for him. Ashby has eleven "
       "accounts and I have printed two, with the chronicle extract that people in the mining camps "
       "will tell you is about him, and which may be about anybody."),
 paper("Extract from a chronicle", "translated by Ashby from a copy at Santa F&eacute;, 1541", p(
     "On the second day after the feast the captain-general detached a party under the alf&eacute;rez "
     "to follow the watercourse toward the east, it being thought that the grass would hold three "
     "days in that quarter.",
     "They did not return. On the ninth day the general sent out and nothing was found, the grass "
     "having closed behind them, and the country in that place being of such a kind that a man "
     "loses the sight of his own camp within a league.",
     "[Here the chronicle names the lost. Ashby copied eleven names and his copy is water-marked "
     "through the middle of the list and I will not print half of it. <span class=\"ed\">Ed.</span>]",
     "The general said a mass for them at the river and went on to the north, the season being "
     "far advanced."),
     ),
 paper("Account", "a shift boss, a silver camp in the high country", p(
     "He came into the camp at supper, in those clothes, and the boys gave him a bad time about "
     "the hat and he took it well.",
     "He said three things at that table. He said the price of lead would come up in the spring, "
     "and it did. He said Mr. Tandy&rsquo;s mother was unwell, and she was, and Tandy did not know "
     "it yet and the letter came in eleven days. And he said we were not to go past the shale in "
     "the number three, and we did, four days later, and I am the only one of that shift who is "
     "still working.",
     "He took nothing. He would not take a drink and he would not take a bed and he would not take "
     "the two dollars we made up for him, and he shook every man&rsquo;s hand and he thanked me by "
     "name and he went out into weather that would have killed a horse.",
     "I have been asked whether he warned us properly about the shale and the answer is that he "
     "did. A warning isn't the same as an explanation, and if he'd given us one of those we'd "
     "have gone past the shale anyway to see."),
     ),
 paper("Account", "a widow at a road ranch on the Llano", p(
     "He stopped for two hours and he was the best company I've had since my husband died and I "
     "won't hear a word against him.",
     "He asked after the king. I said which king and he said it as though I had been slow, and "
     "then he stopped and he put his hand up to his face and he said, in a different voice "
     "altogether, that he begged my pardon for the delay.",
     "I didn't ask him what delay. I've wished a hundred times that I had asked him what delay."),
     ),
 ednote("Ashby&rsquo;s eleven accounts span forty years and the man in them does not age, which is "
        "the thing everybody says about this story and which I would point out is also true of every "
        "story told about a man in a hat. What I cannot dispose of so easily is the lead price and "
        "Mrs. Tandy and the shale, all three in one evening, in front of nine men who were later "
        "asked separately"),

 '  <h2 id="ix-fifth">The Fifth Rider</h2>',
 gloss("Every poster says five. Every count says four. That's all the legend is, and it has "
       "been going twenty-odd years, and the papers below are the ones Ashby thought were the least "
       "embroidered."),
 bill([("bl-3", "Territory of &mdash;&mdash;&mdash;&mdash;&mdash;"), ("bl-1", "$2,000 REWARD"),
       ("rule", ""),
       ("bl-2", "For the apprehension of the persons who on the 4th instant"),
       ("bl-2", "robbed the payroll of the Coffin Wells district"),
       ("rule", ""),
       ("bl-3", "FIVE MEN, MOUNTED"),
       ("bl-2", "A. KELL, elderly, talks a great deal<br>"
                "D. RAINEY, the shooter<br>"
                "a WOMAN, riding as a man, not identified<br>"
                "a YOUTH, about twenty<br>"
                "and ONE OTHER, grey coat, brown horse, about forty"),
       ("rule", ""),
       ("bl-3", "Apply to the marshal at Calvary Crossing"),
      ]),
 depo("before the marshal, Calvary Crossing", "6 September 1883", [
     ("How many men came into the office.", "Five."),
     ("You are certain of five.", "I counted them. I counted them twice, because I was frightened "
      "and counting was something to do."),
     ("Describe the fifth.", "Grey coat. Brown horse. Forty or so. Quiet, he never said a word."),
     ("Describe his face.", "I have said. He was about forty."),
     ("His face.", "Ordinary."),
     ("Hair.", "Under the hat."),
     ("You looked at him for how long.", "The whole while. Four or five minutes. I looked at him "
      "more than the others because he was the one who was not doing anything, and that is the one "
      "you watch."),
     ("And you cannot describe him.",
      "No, and I've been sitting here an hour trying and I'm not a stupid man and I want you to "
      "write that down. I looked straight at him for five minutes and I could draw you the "
      "other four."),
 ]),
 paper("Report to the line", "Overland &amp; Territorial, 5 September 1883", p(
     "Four riders came up on the down coach at the draw below the station and took the box. I make "
     "it four and the guard makes it four and we have talked it over and it is four.",
     "The passengers say five. All six of them say five, and two of them have described the fifth "
     "man to me in the same words, and they were not sitting together and they have not spoken "
     "since.",
     "I put it in my report because the company will hear five from the passengers and I do not "
     "wish to be asked afterwards why my report said four. My report says four because I was on "
     "the box and I counted four and I will say four in a court."),
     sign="J. Otey, driver"),
 field("Oct., &rsquo;83", "Calvary Crossing",
       ["Otey is the best witness in this chapter and nobody has ever asked him anything. He's a "
        "driver, so his account goes to the line, and the line files it, and the marshal never sees "
        "it and the newspaper never sees it.",
        "Six passengers say five. The driver and the guard, who are the two men paid to look at the "
        "road, say four. Whatever else is true, the people who count four are the people whose "
        "living depends on counting."]),
]))


# ================================================================ VII. Paper, Ink & Interest
CH7 = chapter("paper", "VII", "Paper, Ink &amp; Interest",
              "Debts, deeds, wills and the fine print. The worst chapter in this book.",
              "VII. Paper, Ink &amp; Interest", "\n".join([

 """  <p>Nothing in this chapter has a monster in it. There are no lights on the prairie, nobody is
  met on a road, and not one of these documents would raise an eyebrow in a lawyer&rsquo;s office.
  Every one of them is a perfectly ordinary instrument of the kind that is signed a thousand times a
  week in the Territories.</p>
  <p>Read the clauses. That is the whole instruction for this chapter. Read the clauses, and then
  read who benefits, and then notice how few of these people could read.</p>""",

 '  <h2 id="ix-clause">A Clause, Copied from Four Instruments</h2>',
 gloss("Ashby found the same clause, word for word, in four notes written by three different "
       "houses in two territories between 1874 and 1883. He was a naturalist and he noticed it the "
       "way he noticed a bird in the wrong county."),
 paper("Extract from a promissory note", "one of four, otherwise unremarkable", p(
     "&hellip; and it is further agreed that in the event the maker shall die, remove himself "
     "beyond the Territory, or be adjudged of unsound mind before the date of maturity, the whole "
     "of the principal shall stand due upon the instant, and the holder may satisfy the same out "
     "of any property real or personal, and out of the labour or service of any person then of the "
     "maker&rsquo;s household who shall be of the age of fourteen years, at a valuation to be "
     "fixed by the holder&rsquo;s own agent &hellip;"),
     ),
 ednote("The clause is void. It has been void in every territory since before it was written and "
        "any judge would strike it in a minute. I asked a lawyer at the capital why a house would "
        "print a clause it cannot enforce, and he laughed and said because it is never tested, and "
        "then he stopped laughing and said that in nineteen years he had never once been brought a "
        "case under it, and that four notes should have produced at least one argument"),
 field("Feb., &rsquo;84", "the territorial capital",
       ["Three houses, two territories, one clause, identical to the comma. That is not custom and "
        "it is not a form book, because I have been through the form books. Somebody wrote it and "
        "sold it on.",
        "What I would like to know is who valued the labour. The clause says a valuation fixed by "
        "the holder&rsquo;s own agent, and an agent who values a person is a person with a "
        "profession, and a profession leaves paper. I have not found the paper."]),

 '  <h2 id="ix-will">The Will of a Careful Man</h2>',
 gloss("Proved without objection. One of a family whose luck in this country has been remarked on "
       "for three generations and who are not named here, at the request of the surviving daughter, "
       "who was helpful and who read this chapter before it was set."),
 paper("Extract from a will", "proved at the county court", p(
     "&hellip; To my eldest, the home place and the stock upon it.",
     "To my second, the sections along the creek and the note held against Hannaford.",
     "To my third, fourth, fifth, sixth, seventh and eighth, share and share alike, the residue of "
     "my estate whatsoever.",
     "To my ninth I give nothing, having provided for that child by an arrangement made before "
     "the child was born, of which my executor has notice and needs none from me. I direct that "
     "this clause be read aloud in the presence of the whole family and that no explanation be "
     "offered.",
     "And I charge my eldest that the arrangement be continued in the eldest&rsquo;s own family in "
     "the same terms, and I charge the eldest of that family likewise, and so on while the name "
     "holds."),
     ),
 depo("the county court, on the proving of the will", "October", [
     ("You are the executor.", "I am."),
     ("The will refers to an arrangement of which you have notice. What is the arrangement.",
      "I have notice of it. The will does not say I am to describe it and I would rather not."),
     ("The court is asking.", "Then I say that there is a ninth child, that the child is provided "
      "for, and that the child is not in this county and has not been since the age of two."),
     ("Is the child living.", "So far as I know."),
     ("Have you seen the child.", "No."),
     ("Has anybody in the family seen the child.",
      "The mother. Once, at the time."),
     ("Is any money paid under this arrangement.", "No money is paid."),
     ("Then in what does the provision consist.",
      "I decline, and I will take the consequence of declining, and I would point out to the court "
      "that no person is complaining and no person is out of pocket."),
 ], closing="The will was proved. No further enquiry was made."),
 ednote("I have read a great many wills for this book. Ninth children are provided for out of the "
        "estate, or they are cut off with a shilling and a reason, and in three hundred years of "
        "English probate I cannot find another that provides for one by an arrangement and forbids "
        "the executor to say what it is. The daughter who read this chapter told me the clause is "
        "in her own will, in the same words, and that she has never been told either"),

 '  <h2 id="ix-foreclosure">A Good Month at a Small Bank</h2>',
 gloss("A page from a bank&rsquo;s own summary of a quarter, of the sort a country house sends to "
       "its correspondent in a city. Entirely routine."),
 ledger("Quarterly summary", "a country bank, the Coffin Wells district",
        ["", "This quarter", "Same quarter, prior year"],
        [("Notes written", "#61", "#22"),
         ("Notes on sections with a failed well", "#44", "#3"),
         ("Foreclosures completed", "#9", "#1"),
         ("Sections now held by the house", "#31", "#6"),
         ("Wells on those sections reported sweet", "#11", "#6"),
        ],
        "The last line is the only one in the summary with a note against it, and the note reads: "
        "<em>improving. The house&rsquo;s sections are recovering ahead of the district and the "
        "cause is not known to us.</em>"),
 ednote("Eleven of thirty-one against six of six. In plain terms the house&rsquo;s own land is "
        "getting its water back and nobody else&rsquo;s is, and the house has written down that it "
        "does not know why. I believe that they do not know why. That is the part I would ask a "
        "reader to sit with"),

 '  <h2 id="ix-kansas">Gentlemen Who Dine Together</h2>',
 gloss("A newspaper item, and a letter written in answer to it by a man who was there and who "
       "wanted the record corrected in one particular only."),
 news("THE KANSAS CITY COMMERCIAL ADVERTISER", "3 December 1883",
      ["A PLEASANT EVENING", "CATTLE AND RAILROAD INTERESTS"],
      ["Sixteen Gentlemen Sit Down at the Coronado", None],
      ["A private dinner was given on Thursday at the Coronado at which sixteen gentlemen "
       "representing the cattle and railroad interests of four territories sat down together, the "
       "occasion being, we are told, no occasion at all.",
       "Our representative was not admitted and does not complain of it. We understand the "
       "conversation to have turned upon the price of beef, the extension of the Territorial "
       "line, and the question of water rights in the southern counties, and that nothing was "
       "resolved, these gentlemen being in the habit of meeting for the pleasure of it.",
       "It is the eleventh such dinner in four years and the same house is engaged each time."]),
 paper("Letter to the editor", "4 December 1883", p(
     "Sir,",
     "Your notice of yesterday is accurate except in one particular and I write to correct it "
     "because the particular is mine.",
     "There were seventeen at table. I sat at the foot and I counted, as a man does who has been "
     "put at the foot, and there were seventeen.",
     "I do not suggest any impropriety. I imagine your representative had his sixteen from the "
     "house&rsquo;s book and the house&rsquo;s book is kept by the house. But a paper that prints "
     "sixteen will be quoted at sixteen for twenty years, and I would rather it were right."),
     cls="letter", sign="Yr. obedient servant, a subscriber"),
 ednote("The Advertiser did not print a correction. Ashby wrote to the hotel and was told the "
        "engagement was for sixteen covers and that the house does not discuss its guests, which is "
        "a proper answer and tells you nothing, and is the only answer anybody has ever got about "
        "these dinners"),
]))


# ================================================================ VIII. Preaching
CH8 = chapter("preaching", "VIII", "Preaching",
              "Revivals, circuit riders, and houses that take women in.",
              "VIII. Preaching", "\n".join([

 """  <p>I want to be careful here and I will say why. There is more real religion in this country
  than there is anything else, and most of it is a tired man on a horse riding a circuit of two
  hundred miles for forty dollars a year. Nothing in this chapter is about that man, except the
  letters in the middle of it, which are, and which I have put in so that the chapter is
  not only about the other kind.</p>
  <p>The other kind is rarer than the papers make it look. It leaves more paper because it sells
  tickets.</p>""",

 '  <h2 id="ix-revival">The Good Revival</h2>',
 gloss("A handbill, a subscription list, and two letters. The revival was at a place in the "
       "southern counties which has since been renamed by its own people, and I have honoured "
       "that and left the name out."),
 bill([("bl-3", "Four Nights Only"), ("bl-1", "THE GOOD REVIVAL"), ("rule", ""),
       ("bl-2", "Preaching &middot; Singing &middot; Testimony"),
       ("bl-3", "Commencing at early candle-light"),
       ("rule", ""),
       ("bl-2", "NO COLLECTION WILL BE TAKEN"),
       ("bl-3", "Come hungry. You will not go away so."),
       ("rule", ""),
       ("bl-3", "All are welcome, and the sick especially, and those who have<br>"
                "buried somebody this year, and those who have nothing to bring."),
      ]),
 paper("Letter", "to a sister in Missouri, the week after", p(
     "Dearest Ann,",
     "I went on the Thursday only meaning to look and I went the other three nights as well and I "
     "am not ashamed of it.",
     "There was no collection. I want to say that first because you will assume it, and there "
     "was none, and on the last night a man tried to put money in and the preacher would not have "
     "it and gave it back in front of everybody and said the word <em>free</em> about nine times.",
     "I can't tell you what he preached. I've been trying all week. I remember the singing and "
     "I remember standing up and I remember being happier than I've been since Pa died, and when "
     "I try to get hold of the sermon there's nothing there at all. Mrs. Trice says the same and "
     "she has a better head than me.",
     "Everybody has been well since. That is the other thing. The Bevill girl who has been poorly "
     "two years got up on the Saturday and has been up ever since and is working, and nobody in "
     "this town has been sick for five weeks, not so much as a cold, and it is February.",
     "I know how that reads. I'm putting it down anyhow because it's true and because you'll "
     "hear a worse version."),
     cls="letter", sign="Your Cassie"),
 paper("Letter", "the same writer, eleven months later", p(
     "Ann,",
     "You asked and I will answer and then I would like us not to write about it any more.",
     "Nobody here has been ill in eleven months. Not one person in a town of ninety. Old Mr. "
     "Gilliam is ninety-one and was not expected to see the spring and he is splitting wood.",
     "Four have died. All four of them were well in the morning and dead by the evening and the "
     "doctor from the county seat could not say of what in any of the four, and two of them were "
     "young.",
     "We don't talk about it. I want you to understand that we aren't frightened. There is "
     "nothing to say, is the trouble. You can't go to your neighbour and say, we are all of us "
     "well. Nobody can make a complaint out of that.",
     "I would like you to stop asking."),
     cls="letter", sign="Cassie"),
 ednote("Ashby went to that town and came away with nothing. He wrote: <em>they are the healthiest "
        "people I have seen in eleven years and they are perfectly pleasant and not one of them will "
        "sit down with me for an hour.</em> He went back twice"),

 '  <h2 id="ix-circuit">A Circuit Rider&rsquo;s Letters</h2>',
 gloss("Four letters from a Methodist circuit rider to his presiding elder, out of a bundle of "
       "sixty. He rode a circuit of two hundred and ten miles for eleven years. I have chosen "
       "these four because they are the ones about the work."),
 paper("Letter", "to the presiding elder, March", p(
     "Dear Brother,",
     "The circuit stands at nine appointments and I am keeping them all, though the Cardoza place "
     "is now twenty-two miles off the round and I am there once in six weeks instead of once in "
     "four, and I have told them so and they were gracious about it.",
     "I have buried eleven this quarter and baptised four and married none, which is how "
     "the year goes out here.",
     "I need a horse. I am not going to dress it up. The mare is eleven and she has done six "
     "thousand miles on this circuit and she is finished, and I would rather ask you than borrow "
     "from the congregations, who have less than I have."),
     cls="letter", sign="Yr. brother in Christ, A. Teague"),
 paper("Letter", "to the presiding elder, October", p(
     "Dear Brother,",
     "You ask about the reports from the southern end of the circuit and I will answer plainly "
     "because you have always let me.",
     "I do not know. I have been out to that country four times this year. The people are civil, "
     "they come to preaching, they know their hymns better than my own people do, and there is "
     "something the matter and I cannot put my hand on it and I will not write a report saying "
     "there is when all I have is a feeling in a man of fifty who has been riding too long.",
     "What I will say is this. In eleven years on this circuit I have never been asked a question "
     "about doctrine by anybody in that district. Not one. They will talk about the weather and "
     "the stock and their dead and they will sing until midnight, and no one there has ever asked "
     "me what anything means.",
     "My own people ask me twice a visit and generally about hell."),
     cls="letter", sign="A. Teague"),
 paper("Letter", "to the presiding elder, January", p(
     "Dear Brother,",
     "The mare died at the ford on the 3rd. I walked the last nine miles and was met halfway by "
     "two of the Cardoza boys who had come out because I was late, which they had no way of "
     "knowing except that I was.",
     "I am told the district is to be divided. I would ask to keep the southern end if it is "
     "divided, and I know what I wrote in October, and that is the reason I am asking."),
     cls="letter", sign="A. Teague"),
 paper("Letter", "to the presiding elder, the following March", p(
     "Dear Brother,",
     "Kept the southern end. Nine appointments, two hundred and forty miles now.",
     "Nothing to report. I have decided that nothing to report is a thing worth writing down every "
     "quarter, so that when there is something, you will see it against eleven years of nothing.",
     "The new horse is a good one and I am obliged to you."),
     cls="letter", sign="A. Teague"),
 ednote("He rode it another nine years. The bundle ends with a note from the elder&rsquo;s office "
        "recording the date and the cause, which was his heart, at a ford, in the rain, at "
        "sixty-one. There is no legend in these four letters and that is why they are in this "
        "book"),

 '  <h2 id="ix-houses">The Houses That Take Women In</h2>',
 gloss("A printed card, and an item from a city paper about a refusal. Ashby collected eleven of "
       "these cards from eleven towns in four territories and they are identical but for the street."),
 paper("Card", "found in a boarding-house passage, and in ten other towns", p(
     "A woman with nowhere to be tonight may knock at the green door on ____________ Street at "
     "any hour.",
     "No questions, no charge, no church.",
     "Bring your children. Bring nothing else if there is nothing else.",
     "Do not bring a man, and do not send one."),
     ),
 news("THE DENVER EVENING CALL", "19 August 1884",
      ["A REFUSAL", "CHARITY THAT WILL NOT BE HELPED"],
      ["Local House Declines a Subscription of $4,000", None],
      ["A curious circumstance is reported from the north end of this city, where a house which "
       "has for some years sheltered women in distress without publicity has declined a subscription of "
       "four thousand dollars raised on its behalf by a committee of gentlemen of the first "
       "standing.",
       "The lady who received the committee is said to have heard them out with perfect courtesy, "
       "thanked them, and refused, and to have given as her reason that the house does not take "
       "money from anybody who has asked what it is for.",
       "The committee has expressed itself puzzled. We confess we share the sentiment. Four "
       "thousand dollars is four thousand dollars, and the house is by all accounts poor."]),
 field("Sept., &rsquo;84", "Denver",
       ["Asked at the green door. Was received politely in the passage and not further in, which "
        "was correct of them and I did not press it.",
        "Asked whether the eleven houses are one concern. Was told they are not a concern at all "
        "and that anybody may paint a door green.",
        "Asked whether they had ever turned money down before. She said they turn money down "
        "constantly and that it is the least interesting thing about the work, and that I had "
        "come a long way to ask about money like everybody else, and would I like some coffee. I "
        "would. It was very good coffee and I learned nothing and I have thought better of the "
        "afternoon every year since."]),
]))


# ================================================================ IX. The Trades
CH9T = chapter("trades", "IX", "Them That Make a Living At It",
               "Papers from people whose work is the work.",
               "IX. The Trades", "\n".join([

 """  <p>Most of this book is written by people the country happened to. This chapter is the other
  kind. Every paper in it was written by somebody who goes toward the thing by choice, for money,
  and who files a return about it afterwards, because that is what a trade is.</p>
  <p>They are the least frightened documents in the book and the hardest to read.</p>""",

 '  <h2 id="ix-claim">A Bounty Claim</h2>',
 gloss("Submitted to a county board, allowed in part, and kept in the county file with the "
       "clerk&rsquo;s pencil still on it."),
 ledger("Claim for expenses", "submitted to a county board, November",
        ["Item", "Days", "Allowed"],
        [("Pursuit and apprehension, per warrant 41", "19", "#$95.00"),
         ("Horse hire, second animal, the first being lamed", "11", "#$22.00"),
         ("Salt, 40 lb.", "&mdash;", "#$0.80"),
         ("Lamp oil", "&mdash;", "#$1.40"),
         ("Two men hired at the Crossing, 3 days", "3", "#$18.00"),
         ("Replacement of one coat", "&mdash;", "<em>disallowed</em>"),
         ("Board and lodging, self", "19", "#$28.50"),
         ("Digging, 2 days, and lime", "2", "<em>queried</em>"),
        ],
        "The clerk&rsquo;s pencil against the last line reads: <em>what digging? warrant 41 is a "
        "live man.</em> Against the salt, in the same pencil: <em>allowed, do not query, see me.</em>"),

 '  <h2 id="ix-sawbones">A Doctor&rsquo;s Case Notes</h2>',
 gloss("Four entries on one patient from a country doctor&rsquo;s case book. Printed with the "
       "consent of the doctor, who is living, and who asked that the patient be called B."),
 paper("Case notes", "a country practice, over fourteen months", p(
     "<strong>March.</strong> B., male, 34, labourer. Complains of sleeplessness and of a "
     "discolouration on the left forearm, which he has had six weeks and which does not itch. It "
     "is not a bruise and it is not a burn and it is not anything in Gross. It is about the size "
     "of a thumbprint. Advised rest. Charged nothing.",
     "<strong>June.</strong> B. again. Mark is larger and the edge of it is now definite, which "
     "no bruise does. General health excellent. Unusually excellent: he has put on a stone, his "
     "grip is strong, and he tells me he has not been ill a day since March, and B. has been a "
     "sickly man for the eleven years I have known him.",
     "<strong>December.</strong> B. He is the healthiest man on my list and I would show him to a "
     "college. He will not let me measure the mark any more and he was short with me about it, "
     "which is not like him, and he apologised at the door.",
     "<strong>May.</strong> B. came in and sat down and asked me, in the plainest way, whether I "
     "would write him a statement that he was of sound mind, which I would, and which I said so, "
     "and then he said he did not want it for a court, he wanted it for himself, to read later. I "
     "have given it to him. I am a physician and not a priest and I have been sitting here an hour "
     "wondering whether that is a defence."),
     ),

 '  <h2 id="ix-hexer">A Letter About an Arrangement</h2>',
 gloss("Given to Ashby by the woman who wrote it, who was alive when this book went to press and "
       "who read this page and approved it, and who asked to be called by no name at all."),
 paper("Letter", "to nobody, kept in a Bible, given to Ashby in 1883", p(
     "I am writing this down because I have nobody to tell and because if I say it out loud in "
     "this house I will have to explain it to my daughter.",
     "I asked for a thing in the spring of 1874 and I got it. I am not going to write what it was. "
     "Anybody who has ever wanted anything that badly will know what it was like, and anybody who "
     "has not will read it as a confession and I am not confessing to anything. My girl was going "
     "to die and she did not die and she is twenty-two and she is downstairs.",
     "Here is what I have to say about it, which is the whole of what eleven years has taught me.",
     "I do not know what I agreed to. I want that understood. There was no paper and there were no "
     "terms and there was nothing said. I asked, out loud, in a kitchen, and something in the room "
     "was listening, and the listening is the part I cannot get anybody to understand. It was not "
     "frightening. It was <em>attentive</em>. I have been attended to once in my life and it was "
     "in that kitchen and I would know it again anywhere.",
     "And I do not know what I am paying. That is the second thing. I know exactly when I am "
     "paying it, which is the fourth week of every October, because that is when things in this "
     "house go wrong and they have gone wrong every October for eleven years, and never so badly "
     "that a neighbour would notice, and never twice the same way.",
     "I would do it again. I want that written down last so that it is the last thing. I would "
     "do it again tomorrow and I would not ask one more question than I asked the first time. "
     "Nobody is to call that brave. It is arithmetic, and I have done the arithmetic every October "
     "for eleven years."),
     cls="letter"),
 ednote("She died in 1886. Her daughter is living. I wrote to the daughter before printing this "
        "and she has read it and has asked for two words to be changed, and they have been, and "
        "she has asked me to say that her mother was a cheerful woman and is remembered as one"),

 '  <h2 id="ix-contract">Articles of Employment</h2>',
 gloss("One of eleven identical agreements signed by a cattle company in a single season. Ashby "
       "obtained a blank."),
 paper("Articles of employment", "a cattle company, a blank form", p(
     "The undersigned is engaged as a <strong>stock inspector</strong> at seventy-five dollars the "
     "month and found, which is three times the wage of a hand, and the undersigned acknowledges "
     "that the difference is not for inspecting stock.",
     "The undersigned will provide his own arms.",
     "The undersigned will take instruction from the company&rsquo;s agent in the district and "
     "from no other person, and will not discuss the company&rsquo;s business with any officer of "
     "any county.",
     "In the event the undersigned is detained by any authority the company will pay for his "
     "defence and will not otherwise be concerned in the matter, and the undersigned agrees that "
     "the company&rsquo;s obligation under this article is discharged by the payment.",
     "This agreement may be ended by the company at any hour without notice or reason given. It "
     "may be ended by the undersigned on thirty days&rsquo; notice in writing delivered to the "
     "company&rsquo;s office at Kansas City."),
     ),
 ednote("Read the second sentence of the first article again. The company has written down, in an "
        "instrument it expects to be signed eleven times in a season, that it is paying a man three "
        "wages for something other than the work named. A lawyer would have struck that out in a "
        "minute, which tells you the company did not show it to one, which tells you the company "
        "was not worried"),

 '  <h2 id="ix-scout">A Tracker&rsquo;s Evidence</h2>',
 gloss("Given at an inquest. The witness is a hunter of forty years&rsquo; standing who was "
       "engaged by a family to find a missing man."),
 depo("an inquest", "the following spring", [
     ("You were engaged on the 14th.", "The 14th, in the evening. I was on the ground at first "
      "light on the 15th."),
     ("Describe what you found.",
      "His track, going out, easy, a man walking. It goes a mile and a quarter northwest and then "
      "it turns."),
     ("Turns where.",
      "Where the second track comes in."),
     ("Describe the second track.",
      "I would rather describe what it did than what it was, if the court will let me, because "
      "what it did I am sure of."),
     ("Go on.",
      "It comes in from the north and it does not close on him. It goes parallel about forty yards "
      "off for near two miles and it keeps the forty yards over broken ground, which a man cannot "
      "do without looking and which an animal does not trouble to do at all."),
     ("And then.",
      "And then his track changes. He starts hurrying. And the other one keeps its forty yards and "
      "keeps its pace, and it does not hurry, not one step of it, for another mile and a half."),
     ("Where does it end.",
      "His ends at the rocks. The other one goes on northwest at the same pace for as long as I "
      "followed it, which was four hours, and it was still going when I turned back."),
     ("Can you say what made the second track.", "No."),
     ("Can you say it was not a man.",
      "I can say it was no man in boots and no man barefoot and no man in moccasins. I've been "
      "doing this forty years and I have never once before said to a family that I don't know, "
      "and I said it to this family on the 16th and I'm saying it here."),
 ], closing="[The court thanked the witness for his plainness. Verdict: exposure.]"),

 '  <h2 id="ix-deputy">A Resignation</h2>',
 gloss("Handed in at a county office and kept by the clerk, who thought it was the best letter he "
       "had ever been given."),
 paper("Letter of resignation", "to the county commissioners", p(
     "Gentlemen,",
     "I resign the office of deputy from the end of this month.",
     "It is not the pay, which is what you will put in the minutes, and I would be obliged if you "
     "did not, because it will get back to the marshal and he has asked twice for an increase on "
     "my account and been refused twice by this board.",
     "I have been eleven years at this and I'll tell you why I'm going. Three times this year I "
     "have been sent out alone at night to a thing that two men should have gone to, and three "
     "times I went, and the third time I stood at a gate for a quarter of an hour and didn't "
     "open it, and then I rode back and wrote in the book that there was nothing at the place.",
     "There was something at the place. I'm putting that in writing to this board because if I "
     "don't put it somewhere I'll have to carry it, and I've watched the marshal carry his and "
     "I've seen what it costs him.",
     "Give him his two men. He won't ask a fourth time and you shouldn't make him."),
     sign="[signature]"),
]))


# ================================================================ X. Weather
CH9 = chapter("weather", "X", "Weather, and Things Taken for Weather",
              "The sky, which is the biggest liar in the Territories.",
              "X. Weather", "\n".join([

 """  <p>A man who has spent a winter out here will tell you the weather is trying to kill him, and
  he is right, and he does not mean anything by it. Nine in ten of the stories in this chapter are
  about a norther, a hailstorm or a dry lightning strike, told by somebody who was frightened and is
  entitled to be.</p>
  <p>I have kept the chapter short and put the tall ones in it for a reason, because a reader who
  has come this far in this book needs to be reminded what an ordinary lie sounds like.</p>""",

 '  <h2 id="ix-norther">The Norther of &rsquo;80</h2>',
 gloss("Two accounts of the same three days, and a note from the weather office, which is the only "
       "party to the business with an instrument."),
 paper("Account", "a drover, taken down at Dodge", p(
     "It come down on us about four in the afternoon and it was sixty-one degrees when it started "
     "and it was eight below by dark, and I have that from the man at the station who had a "
     "thermometer and looked at it because he could not believe it either.",
     "We lost nine hundred head and two men. The men were forty yards from the wagon.",
     "You will hear that we heard something in it. You will hear that from every outfit that was "
     "north of the river that week and I will tell you what it was, and then you may do as you "
     "please with it. In a wind like that a herd on the move makes a sound that is not the herd "
     "and is not the wind. Every man who has worked cattle knows it. It sounds like a crowd of "
     "people a long way off who are all talking at once and none of them in English.",
     "It is the wind in nine hundred sets of horns. That is all it is and I have heard it in a "
     "dozen blows, and I still got down off my horse in the middle of that one and stood there "
     "listening like a fool."),
     ),
 paper("Letter", "a woman at a section house, to her brother", p(
     "&hellip; and I will not write about the men because you knew them both.",
     "I will write about the sound because you asked me straight out and I would rather answer "
     "you than have you hear it at second hand. Yes. There was a sound in it. It went on all the "
     "second night and it stopped at first light exactly, not faded, stopped, the way "
     "a man stops talking when somebody comes in.",
     "Arthur says it was the wind in the wire. There is a mile and a half of wire on that section "
     "and he is very likely right and he has said it every day since, which is more days than a "
     "man says a thing he believes."),
     cls="letter"),
 paper("Note from the weather office", "Fort Marcy, 1880", p(
     "Fall of sixty-nine degrees in nine hours, observed. The most rapid fall on this "
     "station&rsquo;s record and not the most rapid on the territorial record, which stands at "
     "seventy-eight.",
     "Wind at the maximum the instrument records, which is to say the instrument stopped.",
     "No unusual electrical activity. No observation of any kind is offered here as to sounds "
     "reported by persons in the storm, this office having no instrument for it."),
     ),

 '  <h2 id="ix-bird">The Bird</h2>',
 gloss("Everybody in this country has a bird story and almost all of them are about an eagle seen "
       "at a distance in bad light. I have three here. The third is not."),
 paper("Account", "a boy of eleven, in the presence of his father", p(
     "It went over the barn and the barn shook. I was in the yard and I sat down, not fell, sat "
     "down, because the air came down on me.",
     "My father says it was the storm coming and I have said yes sir every time since and I am "
     "saying yes sir now."),
     ),
 news("THE TERRITORIAL ENTERPRISE", "spring, 1877",
      ["A MONSTROUS BIRD", "SPORTSMEN DISAPPOINTED"],
      ["Reported Near the Breaks. Nine Gentlemen Ride Out and Return With an Appetite", None],
      ["Our readers will recall the large bird reported in February near the breaks, and will be "
       "glad to learn that a party of nine gentlemen of this town rode out on Saturday to procure "
       "it for science.",
       "They returned on Monday having procured two antelope, a quantity of whisky at Gurley&rsquo;s "
       "and a fine account of themselves, and no bird. One of the party is of the opinion that the "
       "bird has gone north for the season. Another is of the opinion that there was never any "
       "bird. We incline to the second gentleman, who was the only one of the nine who was sober "
       "on the Sunday and is consequently the only one whose opinion we can date."]),
 paper("Account", "a rancher, who asked that it be printed exactly as he gave it", p(
     "I'm not going to tell you it was a bird.",
     "I will tell you what I can account for. There was a shadow on the grass moving north to "
     "south and it was longer than the corral, which is ninety feet, and I paced it after against "
     "the fence line so I would have a figure.",
     "There was no sound. That's my whole story and it's the part that has kept me from telling "
     "it for six years. A thing of that size over your head at three hundred feet makes a sound "
     "and there was no sound at all, and the horses didn't move.",
     "I looked up. I want that in. I did look up. I'm not one of these men who tells you he "
     "looked at the ground. I looked straight up and there was nothing there and there was a "
     "shadow ninety feet long on the grass in front of me going south, and I stood and watched it "
     "go over the rise.",
     "Print it how I said it. If you tidy it up I'll know."),
     ),
 ednote("I have not tidied it up. Every other bird account Ashby collected describes wings, a "
        "beak, a colour, a cry. This one describes a shadow and no bird, and it is the only one of "
        "the thirty-odd from a man who paced out a measurement afterwards"),
]))


# ================================================================ X. Songs & Sayings
CH10 = chapter("songs", "XI", "Songs &amp; Sayings of the Territory",
               "What people sing, and what they say without thinking about it.",
               "XI. Songs &amp; Sayings", "\n".join([

 """  <p>A song is the only kind of paper in this book that nobody wrote down at the time. It is
  taken from a mouth, and the mouth is usually a child&rsquo;s, and every version is different and
  all of them are the real one.</p>
  <p>Most of this chapter came to me from Miss Harriet Crandall, of a college in Massachusetts, who
  has been on a collecting tour of this country for five years and who has forgotten more about
  this business than Ashby ever learned. She and Ashby corresponded for two years and disagreed
  about nearly everything, which is why the correspondence is worth printing.</p>""",

 '  <h2 id="ix-weathersong">The One About the Weather</h2>',
 gloss("It has no name. Miss Crandall has collected it under nine different titles in six "
       "territories and lists it in her own index by its refrain."),
 song("collected at a mining camp in the Bitterroots, and at a farming village three hundred miles south, in the same season", [
     ["Oh the sky come down at Michaelmas",
      "and the sky come down at noon,",
      "and my mother put the shutters to",
      "and sang me out of tune.",
      "<em>Come in, come in out of the weather,</em>",
      "<em>come in and shut the door.</em>"],
     ["Oh the cattle stood at the wire all night",
      "and never turned their head,",
      "and the man that went to fetch them in",
      "come back and went to bed.",
      "<em>Come in, come in out of the weather,</em>",
      "<em>come in and shut the door.</em>"],
     ["Oh the well went sweet and the well went sour",
      "and the well went sweet again,",
      "and nobody asked and nobody told",
      "and the water tasted plain.",
      "<em>Come in, come in out of the weather,</em>",
      "<em>come in and shut the door.</em>"],
 ], "as sung by children, 1879 and after"),
 paper("Letter", "Miss H. Crandall to N. Ashby, 2 April", p(
     "Mr. Ashby,",
     "You are making a mystery out of a commonplace and I say so as a friend.",
     "A tune does not need a route. I have traced songs from Cornwall to the Bitterroots in nine "
     "years by way of three freighters and a Methodist, and the carriers are always people nobody "
     "thinks to ask because nobody thinks they sing. Rail crews sing. Section hands sing. The "
     "answer to your question is almost certainly a man with a fiddle whose name we will never "
     "have, and the discipline is to say so and stop.",
     "Your second point is better and I'll give it to you. The song takes new verses and nobody "
     "claims them. That is unusual. It isn't unique. I can name you four songs that do it, and "
     "in three of the four the composer turned up eventually and was a schoolmistress.",
     "Send me the wells verse in the hand you took it down in and not in your own tidy copy. Your "
     "tidy copies are useless to me."),
     cls="letter", sign="Yrs. sincerely, H. Crandall"),
 paper("Letter", "Miss H. Crandall to N. Ashby, 14 November, the following year", p(
     "Mr. Ashby,",
     "I have sorted eleven hundred verses by first attested date, which has taken me two years "
     "and which you may tell me was a waste of it.",
     "Nine hundred and sixty of them attach to an event I can name and date, and in every one of "
     "those the verse follows the event, by between four months and three years. That is what a "
     "song does and it is what I expected and it is a satisfactory result.",
     "There are forty-one I cannot attach to anything.",
     "They are not nonsense verses. Nonsense verses are easy to spot and I have thrown out two "
     "hundred of those already. These are of exactly the same construction as the nine hundred and "
     "sixty. They name a place, a month, a family and a circumstance, in the same metre and with "
     "the same wrong grammar in the third line, and I have been through the county papers of six "
     "territories and not one of the forty-one has happened.",
     "I'm sending you the list because you won't leave me alone until I do and because I'd "
     "like it in a second pair of hands. I am drawing no conclusion from it. I want that in "
     "writing, Mr. Ashby, because I know what you'll do with this, and if I see my name attached "
     "to a conclusion I have not drawn I shall be extremely put out."),
     cls="letter", sign="Yrs., H. Crandall"),
 ednote("Ashby did not draw the conclusion. To his credit he wrote back and said so, and she "
        "kept the letter and sent me a copy of it when she heard this book was being made, along "
        "with a note asking that her caution be printed as prominently as her list. It has been"),
 gloss("Three of the forty-one. Miss Crandall&rsquo;s note is printed with them at her insistence: "
       "<em>a verse that names a place and a month and a family is a verse about something that "
       "happened. If nobody has yet found the event, the likeliest explanation by a very long way "
       "is that nobody has yet looked in the right county paper.</em>"),
 song("three of the unattached verses, from Miss Crandall&rsquo;s list", [
     ["Oh the Odom well at candlemas",
      "went down and never come,",
      "and the girl that told him where to dig",
      "was not his and not his son&rsquo;s."],
     ["Oh the Crossing had a marshal",
      "and the Crossing had a light,",
      "and the man that carried both of them",
      "put neither down that night."],
     ["Oh the seventh and the seventh",
      "and the seventh makes the three,",
      "and whatever&rsquo;s in the bottom of it",
      "was never in the sea."],
 ], "no event attached as of 1885"),

 '  <h2 id="ix-sayings">Sayings</h2>',
 gloss("Ashby kept a running list at the back of every field-book. These are the ones that turn up "
       "in more than three counties. He made no attempt to explain any of them and neither shall I."),
 paper("Sayings of the Territory", "from the backs of eleven field-books", p(
     "<em>Salt on the sill and iron on the door, and if you have only one of them, iron.</em>",
     "<em>Never tell a stranger your mother&rsquo;s name. Tell him your father&rsquo;s twice.</em>",
     "<em>A dry well is a well. A sweet well that was dry last year is a neighbour.</em>",
     "<em>Count the horses.</em> (Given alone, with no explanation, in nine counties.)",
     "<em>Pay a man the day he works. Pay anything else the day after.</em>",
     "<em>If the dogs won&rsquo;t go in, you have got what you came for and you can go home.</em>",
     "<em>The country keeps books.</em>",
     "<em>Two is a coincidence, three is a road, and four is somebody&rsquo;s business.</em>"),
     ),
 field("undated", "the back of the ninth field-book",
       ["Have now got <em>count the horses</em> from nine counties and not one person who can tell "
        "me what it means. Four said their grandmother said it. Two said it means what it says. One "
        "said it was about horse thieves, which is the only sensible answer anybody's given me and "
        "is plainly not it, because a man who's worried about horse thieves says so.",
        "I'm going to stop asking. A saying that everybody has and nobody can gloss is older than "
        "anybody who has it, and the honest thing is to write it down and leave it."]),
]))


# ================================================================ XI. Frauds & Errors
CH11 = chapter("frauds", "XII", "Frauds, Errors &amp; Honest Mistakes",
               "The ones that came apart, and the one that did not.",
               "XII. Frauds &amp; Errors", "\n".join([

 """  <p>A book like this one is worth nothing at all unless it also prints the failures, and there
  are a great many more failures than anything else. Ashby chased two hundred and forty stories to
  the end. Nineteen of them survived the chasing. Everything else in this book came out of the
  nineteen, and this chapter is a handful of the two hundred and twenty-one.</p>
  <p>They come apart in four ways, and after a while you can guess which before you get there. A
  man wanted money. A man wanted a drink bought for him. Somebody misread a document. Or the thing
  happened exactly as described and had a cause anybody sober could see.</p>""",

 '  <h2 id="ix-giant">The Petrified Man at Wilcox</h2>',
 gloss("Exhibited for two years at twenty-five cents. Ashby paid the twenty-five cents four times "
       "and thought it was the best value in the Territories."),
 news("THE WILCOX INDEPENDENT", "11 June 1881",
      ["THE STONE MAN", "OUR OWN ANTIQUITY"],
      ["Seven Feet if He Is an Inch. Professors Invited", None],
      ["The petrified man discovered on Mr. Sipes&rsquo;s property in April continues to draw "
       "visitors from as far as the capital, and we are gratified to report that two gentlemen of "
       "science have now examined him and pronounced themselves unable to account for him, which "
       "in our experience is as near to a certificate as science ever comes.",
       "The figure is seven feet and one inch, lies upon its right side, and is of a uniform "
       "grey. Mr. Sipes has declined an offer of eleven hundred dollars from a party in Chicago "
       "and states that the stone man belongs to this county."]),
 paper("Letter", "a monument cutter at Trinidad, to Ashby, four years later", p(
     "Sir,",
     "You are the fourth to write to me and I will tell you the same as the others. I cut it. I "
     "cut it out of a block I had left over from the Purdy monument in the autumn of 1880 and I "
     "was paid forty dollars for it and I have the entry in my book which you are welcome to see.",
     "I'm not ashamed of it. It's a good piece of work. The toes alone took me two days and "
     "nobody has ever looked at the toes.",
     "What I will say is that I did not know what it was for. I was asked for a figure of a "
     "sleeping man, seven feet, no clothing, no face to speak of, and told to make the surface "
     "rough, and I did as I was asked. The first I knew of Wilcox was when my sister-in-law sent "
     "me the paper.",
     "If you print this, print that I've offered to say so under oath at any time these four "
     "years and nobody has taken me up on it. The county doesn't want to know. There's a man "
     "taking a quarter at the door."),
     cls="letter", sign="Yrs., a monument cutter"),

 '  <h2 id="ix-haunting">The Haunting at the Trice House</h2>',
 gloss("Confessed in full, in writing, by the man who did it, who was paid nine dollars a week for "
       "eleven weeks and considered it honest work."),
 paper("Statement", "made before a justice, and not prosecuted", p(
     "I done the noises. I done them with a length of wire under the floor and a bucket and I "
     "done the light with a lamp and a sheet of tin in the orchard.",
     "Mr. Trice paid me to do it and his reason was his brother was trying to make him sell the "
     "house and he wanted the brother to be the one who looked a fool. I am aware that is not a "
     "reason a court will like.",
     "I done it eleven weeks. The people who saw it weren't stupid people and I want to say so. "
     "A man in a dark orchard who has been told there's a light will see a light, and I didn't "
     "have to be very good, and I wasn't very good, and it worked on the schoolmaster and it "
     "worked on two preachers.",
     "There's one thing I didn't do and I have said it every time I've been asked and I'll "
     "say it here. I didn't do the crying. There was crying in that house on four nights in "
     "October and I wasn't in the house and I wasn't under it and I was at my sister&rsquo;s at "
     "Gurley&rsquo;s twenty-two miles off on two of the four, which she will swear to and has.",
     "I done the noises and the light. I never done the crying and I'd like that written "
     "down separate."),
     ),
 ednote("It is written down separate. I would add that a man confessing to eleven weeks of fraud "
        "has no reason left to hold anything back, and that this is the only reservation in a "
        "confession of nine hundred words"),

 '  <h2 id="ix-forgery">The Forgery</h2>',
 gloss("I said in the front of this book that one paper here is a forgery and that I have printed "
       "it anyway. This is it. It purports to be a marshal&rsquo;s supplementary return on the Pell "
       "place (Chapter I) and it is not."),
 paper("Purported supplementary return", "Calvary Crossing, dated 31 April 1882", p(
     "Supplementary to my return of the 18th inst. on the Pell homestead.",
     "On a further search of the premises on the 29th I went down into the cellar, which was not "
     "mentioned in my first return, and found there marks upon the floor and the lower courses of "
     "the wall which I am not competent to describe and did not measure.",
     "I counted them. There were seven.",
     "I have burned the barn and I will not be going back to the place and I have said so to the "
     "county."),
     sign="T. Coil, marshal"),
 ednote("It is a forgery and it is not a clever one. There is no 31st of April. The marshal at "
        "Calvary Crossing is Coyle and has been for nine years and this document spells him Coil. "
        "The paper is a commercial ruled stock that no county office in the territory buys, and the "
        "hand is not his, and Mr. Coyle has seen it and has said so in terms I have not printed"),
 field("June, &rsquo;84", "Calvary Crossing",
       ["The forgery is worthless and I'm keeping it.",
        "It says cellar and it says seven. The cellar was public in the coroner&rsquo;s return, so "
        "that is nothing. The seven was not in the coroner&rsquo;s return, it was not in the "
        "marshal&rsquo;s return, it was not in the Banner, and it is in the children&rsquo;s rhyme "
        "at the schoolhouse and in this forgery and nowhere else on earth that I can find.",
        "So either the forger heard the rhyme and used it, which is the answer, or he and the "
        "children got it from the same place.",
        "I have been to the schoolhouse again. The rhyme has been going about a year, which puts it "
        "after the forgery by four months. So he did not get it from them.",
        "I'd like to find the man. I wouldn't prosecute him. I'd like to buy him a dinner and ask "
        "him one question."]),
 ednote("Ashby never found him. Nor have I, and I have had two years and a printer&rsquo;s budget "
        "and better manners, and I will say plainly that I think the likeliest explanation is a "
        "rumour in a town of four hundred people, moving faster than either of us could track it "
        "afterwards, which is what rumours in towns of four hundred do"),
]))


# ================================================================ XII. The Last of the Satchel
CH12 = chapter("last", "XIII", "The Last of the Satchel",
               "What was in it, in the order it was in.",
               "XIII. The Last of the Satchel", "\n".join([

 """  <p>Ashby stopped writing in the autumn of 1884. The satchel came to me through a lawyer at
  the Crossing in the spring of 1886 with a letter of instruction that was two lines long and is
  printed below.</p>
  <p>I have added nothing here and taken nothing out and kept the order. Three of these papers have
  no business being in a book. I am aware of it.</p>""",

 paper("Letter of instruction", "found on the top of the satchel", p(
     "Whoever gets this: print all of it or none of it, and do not tidy the spelling.",
     "There is no ending. Do not supply one."),
     cls="letter", sign="N. Ashby"),

 field("2 Oct., &rsquo;84", "Coffin Wells",
       ["Well at the Renfro place came back. Sweet, cold, drawing clean, and it's been dead "
        "eleven months.",
        "Nobody in this town is pleased. That is the only thing I want to write down about it. I "
        "went round to four houses and told them, thinking it was good news, and four times I got "
        "the same face back."]),
 field("6 Oct., &rsquo;84", "Coffin Wells",
       ["Second one back. The Dunbar.",
        "Asked Mrs. Kirby, who has been here longest, what it means when they come back. She said "
        "they do not come back. I said two of them have. She said yes."]),
 paper("Note, undated, on the back of a bill", "in the satchel", p(
     "Ask at the mission about the count on the back board. Ask who keeps it. Ask whether they "
     "have ever had to put the figure down and then put it up again, and how long between."),
     ),
 field("11 Oct., &rsquo;84", "the mission ground",
       ["Somebody's living out here. I've known that for three years and so has everybody in "
        "the county and it's the least interesting fact in the basin.",
        "What I didn't know is that the somebody is expecting people. There's a second cup. It's "
        "washed and it's upside down on a stone next to the first one and it has been used, and it "
        "isn't mine, and I've been coming out here on and off since &rsquo;81 and I have never "
        "once been offered a cup of anything.",
        "So there is a visitor. A regular one, and one who washes up.",
        "I'm not going to ask. If I ask, they'll stop."]),
 paper("Letter", "Miss H. Crandall to N. Ashby, 19 October 1884, unopened when found", p(
     "Mr. Ashby,",
     "Forty-one is now thirty-eight.",
     "Three of my unattached verses have attached themselves. Two are from last year and one is "
     "from August, and all three are now in the county papers, and the verses are older than the "
     "papers by between one and four years, and I have the dates from three independent "
     "collections and one of them is yours.",
     "I'm not drawing a conclusion. I'm telling you that I've stopped sorting by date and "
     "started sorting the other way, and I want you to tell me I'm being a fool, and I'd "
     "rather have it from you than from anybody at the college.",
     "Please write by return."),
     cls="letter", sign="H. Crandall"),
 ednote("The seal was not broken. I have written to Miss Crandall, who is well, and who has asked "
        "that the letter be printed, and who has asked me to say that she has continued the work "
        "and that the figure today is thirty-one"),
 field("24 Oct., &rsquo;84", "the Stage Road, below Saltlick",
       ["Met somebody on the road about four in the morning and I'm going to write it down "
        "properly for once instead of collecting it off somebody else.",
        "He was courteous. He knew I was going to the Crossing. He asked after my sister by name "
        "and asked whether she had got the place at the school, which she has, and which I have "
        "told nobody in this territory.",
        "He got one thing wrong and I caught it at the time, which nobody in two hundred and eleven "
        "accounts has ever done, and I caught it because I have been waiting eleven years to. He "
        "said my father&rsquo;s name and it was not my father&rsquo;s name.",
        "I said, that is not my father.",
        "He said: no."]),
 paper("A page, torn, no date", "the last thing in the satchel", p(
     "&mdash;&mdash; and it comes down to the wells in the end, and I have known that since the "
     "second winter and have not been able to write it down because the moment I write it down it "
     "is a theory, and a theory is a thing a man defends.",
     "So here is the theory and I am done defending it. There are seven and there has been "
     "somebody counting them for seventy-five years, and the counting is the work, and the person "
     "who does the work is always old and is always alone and has always just taken it on from "
     "somebody, and I have never met one of them who was the first.",
     "I do not know what happens when the counting stops. Nobody does. The honest position is that "
     "nobody has ever seen it stop, which is not the same as"),
     ),
 ednote("The page is torn there. The rest of it is not in the satchel and the lawyer at the "
        "Crossing is satisfied that nothing was removed. I have printed it as it is, per the "
        "instruction, and I will observe for the last time that a man who says the honest position "
        "is that nobody has seen a thing is not a man who has seen it"),
 '''  <p class="note">There is no Chapter XIV. Ashby&rsquo;s numbering went to thirteen in every one
  of the eleven field-books, and he never gave a reason, and by the end I had stopped wanting
  one.</p>''',
]))


# ================================================================ assemble
CHAPTERS = [CH1, CH2, CH3, CH4, CH5, CH6, CH7, CH8, CH9T, CH9, CH10, CH11, CH12]

BODY = CONTENTS + BEFORE + "".join(CHAPTERS)

start_marker = "<!-- ===================== CONTENTS ===================== -->"
si = H.find(start_marker)
assert si != -1, "contents marker not found"
sci = H.find("<script>")
assert sci != -1
assert H.rfind("</div>", si, sci) != -1
new_html = H[:si] + BODY + "\n</div>\n" + H[sci:]

from nav_tools import add_detailed_toc, build_index

LEG_INDEX = [
    ("Ashby, N. (who gathered these papers)", "before"),
    ("Ashby, the last of the satchel", "last"),
    ("Agency, a file closed by the", "ix-agency"),
    ("Assay, an, and what followed it", "ix-assay"),
    ("Bank, a good month at a small", "ix-foreclosure"),
    ("Arrangement, a letter about an", "ix-hexer"),
    ("Articles of employment", "ix-contract"),
    ("Bird, the", "ix-bird"),
    ("Bounty claim, a", "ix-claim"),
    ("Burying ground, the business at the old", "ix-swarm"),
    ("Cellar, the (see the Pell place)", "ix-pell"),
    ("Chainmen, a petition from the", "ix-cut"),
    ("Clause, one copied from four instruments", "ix-clause"),
    ("Coroner&rsquo;s returns, one year of", "ix-coroner"),
    ("Crandall, Miss H., and the unattached verses", "ix-weathersong"),
    ("Dinners, gentlemen who take", "ix-kansas"),
    ("Dry camp, the", "ix-thirst"),
    ("Ellender party, the", "ix-ellender"),
    ("Fifth rider, the", "ix-fifth"),
    ("Flour, a homestead&rsquo;s account of its", "ix-glutton"),
    ("Forgery, the", "ix-forgery"),
    ("Gurley&rsquo;s, the man at", "ix-fivewives"),
    ("Haunting, a confessed", "ix-haunting"),
    ("Houses that take women in, the", "ix-houses"),
    ("Mad Spaniard, the", "ix-spaniard"),
    ("Norther of &rsquo;80, the", "ix-norther"),
    ("Painted Mesa, the spring on", "ix-mesa"),
    ("Pell place, the", "ix-pellnews"),
    ("Pell place, the rhyme about", "ix-pell"),
    ("Petrified man at Wilcox, the", "ix-giant"),
    ("Photographer, what one would not print", "ix-mirror"),
    ("Returned, a boy who came back", "ix-returned"),
    ("Resignation, a deputy&rsquo;s", "ix-deputy"),
    ("Revival, the Good", "ix-revival"),
    ("Riding circuit, a preacher&rsquo;s letters on", "ix-circuit"),
    ("Sawbones, a case book kept by a", "ix-sawbones"),
    ("Tracker&rsquo;s evidence, a", "ix-scout"),
    ("Trades, them that make a living at it", "trades"),
    ("Saltlick Station, two accounts of", "ix-saltlick"),
    ("San Clavo, the register at", "ix-sanclavo"),
    ("Sayings of the Territory", "ix-sayings"),
    ("Song, the one about the weather", "ix-weathersong"),
    ("Spoil, the thing in the", "ix-veinwork"),
    ("Survey, the railroad&rsquo;s day-book", "ix-survey"),
    ("Undertaker&rsquo;s book, an", "ix-undertaker"),
    ("Vane Banking House, terms of", "ix-vane"),
    ("Wells, the water going bad", "ix-water"),
    ("Will of a careful man, the", "ix-will"),
    ("Wrong detail, the", "ix-wrongdetail"),
]
new_html = build_index(
    new_html, curated=LEG_INDEX, creatures=False,
    subtitle="Every paper in this book, and the page it is printed on.",
    intro="Papers are listed by what they are about rather than by who wrote them, since a good "
          "many of them were written by nobody in particular. A leading &ldquo;the&rdquo; is "
          "ignored in the ordering.")
new_html = add_detailed_toc(new_html)
open("legends.html", "w", encoding="utf-8").write(new_html)
print(f"legends.html: papers {new_html.count('class=\"paper')} "
      f"| glosses {new_html.count('class=\"gloss\"')} "
      f"| editor's notes {new_html.count('class=\"ednote\"')} "
      f"| size {len(new_html)}")
