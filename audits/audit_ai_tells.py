#!/usr/bin/env python3
"""audit_ai_tells.py — does the repository's own prose read like a person wrote it?

The books already get this treatment. The REPOSITORY did not, and the repository is what someone
sees first: the README, this project's handoff doc, the changelog, the release notes. Prose that
reads as machine-generated undercuts the work it is describing, so it gets measured the same way
the books do.

Three independent signals, because any one alone is easy to game:

  BURSTINESS — the standard deviation of sentence length divided by its mean. Human writing varies
  a lot: a four-word sentence next to a forty-word one. Generated prose regresses to a comfortable
  middle. Measured on the books earlier: 0.65 / 0.94 / 0.49. Rough bands, from that calibration:
      >= 0.55  human-like
      0.45-0.55 acceptable, watch it
      <  0.45  flat — the tell
  Note this is a signal, not a verdict. Reference docs are legitimately more uniform than prose.

  TELLS — phrases and shapes that are disproportionately common in generated text. The one this
  project cares most about is NEGATIVE PARALLELISM ("not just X, but Y" / "it isn't X, it's Y"):
  it is the single most recognisable LLM cadence and it is easy to write by accident. The list was
  brought up to the 2026 literature on 2026-08-22 — see the sources cited beside HARD below.

  LEXICAL DIVERSITY — a moving-average type-token ratio, added 2026-08-22. The 2026 survey leads
  on lower lexical diversity in generated text; this is that finding, measured. Read it against a
  file's own history rather than against an absolute, and see mattr() for why.

Every pattern in HARD is proved by --selfcheck, which runs each one against a sentence built to
trip it. A guard that has never been seen to fire is a guard nobody should trust: two of the ones
here were written wrong the first time and looked exactly like the ones written right.

RESEARCH SIGNALS (added 2026-09-16) — rates per thousand words, printed beside the same rates from
writing done without a model: the 5e SRD for rules prose and The Virginian for western prose. They
cover the 2025-26 findings the hard tells cannot: lexical richness, participial clauses and
nominalizations, the Antislop phrase list, StoryScope's fiction habits, Claude's own tics, and a set
of shapes (two-beat reveals, a clause echoing its own opening words, "the whole of it") that are
fine once and a tell when they keep coming. Sources are in ai_tells_lexicon.py. They are reported
on every run and only fail under --strict, which is the exit test for the voice pass.

Usage:
    python audit_ai_tells.py                  # audit the tracked docs, exit 1 on any hard tell
    python audit_ai_tells.py FILE [FILE ...]  # audit specific files
    python audit_ai_tells.py --commits 60     # also audit the last N commit messages
    python audit_ai_tells.py --books          # scan the six books as well
    python audit_ai_tells.py --strict         # also fail on research shapes and runaway rates
    python audit_ai_tells.py --all            # list every research instance, not the first few
    python audit_ai_tells.py --worklist F.tsv # write every research instance to a file
    python audit_ai_tells.py --calibrate F    # print the research rates for any plain text file
    python audit_ai_tells.py --selfcheck      # prove every pattern still fires, and only on cue
"""
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# This file lives in audits/, so the repo root is one level up. Every path
# below hangs off it -- including the cwd handed to git -- so this one line is
# what makes the move to audits/ a move and not a rewrite.
ROOT = Path(__file__).resolve().parent.parent

# The word lists live beside this file. The commit-msg hook loads this module by path, so the folder
# is put on sys.path here rather than trusting the caller to have done it.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ai_tells_lexicon as LEX  # noqa: E402

# The prose a reader actually meets first. GK/CLAUDE.md joined the list in v1.29.2: it was split
# out of the root CLAUDE.md on 2026-07-30 and carries ~24,000 characters of the same kind of prose,
# so leaving it off would have quietly exempted a quarter of the project's documentation from the
# standard the rest of it is held to.
DEFAULT_DOCS = ["README.md", "CLAUDE.md", "GK/CLAUDE.md", "CHANGELOG.md", "NOTICE"]

# The books. Pass --books to scan these too. They were exempted at first on the theory that their
# period-western register would confuse the scan; that was wrong, and it hid real findings — the
# cadence tells are about SHAPE, not vocabulary, and shape does not care what century the diction
# comes from. Sixteen negative-parallelism constructions were sitting in here unexamined.
BOOKS = ["blood-and-grit.html", "keeper-handbook.html", "bestiary.html",
         "module-salt-at-coffin-wells.html", "module-a-face-not-his-own.html",
         "module-what-the-water-answers.html"]

# ---- hard tells: these are worth failing over ----------------------------------------------------
# Negative parallelism in its common shapes. The pattern is deliberately narrow: it needs the
# contrast pair, so an ordinary "not" sentence doesn't trip it.
HARD = [
    (r"\bnot (?:just|only|merely|simply)\b[^.?!]{0,80}?,? but\b", "negative parallelism (not just X, but Y)"),
    (r"\b(?:isn't|is not|wasn't|was not|aren't|are not)\b[^.?!]{0,60}?[,;—-]\s*(?:it's|it is|they're|they are)\b",
     "negative parallelism (it isn't X, it's Y)"),
    (r"\bit'?s? (?:not|never) (?:about|that)\b[^.?!]{0,60}?,? (?:it'?s|but)\b", "negative parallelism (it's not about X, it's Y)"),
    (r"\bmore than (?:just|merely|simply)\b", "\"more than just\""),
    (r"\bdelve[sd]? into\b", "\"delve into\""),
    (r"\b(?:in|at) (?:today's|the modern) (?:world|landscape|era)\b", "generic scene-setting opener"),
    (r"\bit'?s worth noting\b", "\"it's worth noting\""),
    (r"\bwhen it comes to\b", "\"when it comes to\""),
    (r"\bthat being said\b", "\"that being said\""),
    (r"\bin conclusion\b", "\"in conclusion\""),
    (r"\b(?:let'?s|we'?ll) (?:dive|jump) (?:in|into)\b", "\"let's dive in\""),
    (r"\bnavigat(?:e|ing) the (?:complex|complexities|landscape|world)\b", "\"navigating the landscape\""),
    # An assistant describing its operator in the third person. Nothing gives the game away faster
    # in a doc that is otherwise written in the first person — CLAUDE.md opens with "How I like to
    # work" and "I direct in plain words", so "user's stated plan" a thousand lines later reads as a
    # different author entirely. Caught by eye, not by this scan, which is why it is here now.
    # The established `(user-reported)` / `(user-asked)` parentheticals are house convention and are
    # deliberately NOT matched: they credit where a fix came from and read as a normal changelog note.
    # "the" is OPTIONAL, and that is the whole point: the phrase that prompted this pattern was
    # "(user's stated plan, 2026-07-29)" with no article at all, and the first version of the regex
    # required one and sailed straight past it. A guard written from memory of the problem instead of
    # from the actual text is a guard that does not fire.
    # The POSSESSIVE is required, and it is the discriminator. "user's stated plan" is an assistant
    # narrating its operator; "Two user request batches in one session" is a changelog crediting
    # where the work came from, which is this project's house convention and appears throughout the
    # history. Dropping the apostrophe to catch the first flagged four of the second.
    (r"\b(?:the\s+)?user's\s+(?:stated|request|wish|intent|preference|instruction|words|plan|goal)", "assistant register (\"user's …\")"),
    (r"\b(?:per|as (?:per|requested by)|according to) the user\b", "assistant register (\"per the user\")"),
    (r"\bthe user (?:wants|asked me|requested|would like|prefers|has asked)\b", "assistant register (\"the user wants \u2026\")"),

    # ---- added 2026-08-22, from the current literature ------------------------------------------
    # Everything above was written against the 2023-24 generation's habits, and those habits moved.
    # Three sources, all free to read, which is why they were the ones chosen — a check nobody can
    # open the reasoning behind is a check people stop trusting:
    #   * Wikipedia, "Signs of AI writing" (living catalogue, read 2026-08-22)
    #     https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
    #     The most operationally useful of the three. Every entry is a shape somebody had to
    #     recognise by eye across thousands of suspect drafts before it could be written down.
    #   * Geng, Dong & Poibeau, "Beyond Via: Analysis and Estimation of the Impact of Large
    #     Language Models in Academic Papers", arXiv:2603.25638 (March 2026), open access.
    #     Vocabulary shift measured across arXiv: words as ordinary as "beyond" and "via" moved
    #     far enough to be detectable in aggregate. NOTHING from it is a hard tell here, and that
    #     is a finding rather than an omission. A frequency argument needs a corpus; one document
    #     cannot carry one; and a checker that fails on the word "beyond" is a checker nobody runs
    #     twice.
    #   * Terčon & Dobrovoljc, "Linguistic Characteristics of AI-Generated Text: A Survey",
    #     arXiv:2510.05136, open access. Synthesises the feature-level work across models, genres
    #     and languages. Its headline findings are a more formal and impersonal style marked by a
    #     higher share of nouns, and lower lexical diversity — the second of which is measured as
    #     a column below. It is also the source behind the framing-verb cluster reported from
    #     mid-2025 on ("emphasizing", "highlighting", "showcasing"), which is the vocabulary the
    #     participial pattern below runs on.
    #
    # The line this file already drew decided every one of these: a SHAPE fails, a WORD gets
    # reported. Shapes survive paraphrase and register. Words are just words, and this project
    # writes in a period-western register that collides with a good many of them.

    # The participial restatement. A clause hung off a comma that says the main clause again in
    # the register of a press release: "The initiative represented a shift, marking a pivotal
    # moment in the evolution of the field." The strongest single addition of this pass, because
    # it is a shape, it is close to absent from edited human prose, and no honest rewrite keeps it
    # by accident. The verb list is confined to verbs that only ever restate. "showing", "leaving"
    # and "making" do real work in ordinary sentences and are deliberately not here.
    (r",\s*(?:ensuring|highlighting|emphasi[sz]ing|underscoring|showcasing|cementing|solidifying|"
     r"underlining|reaffirming|reinforcing|exemplifying|epitomi[sz]ing)\b[^.?!]{0,140}[.?!]",
     "participial restatement (\", \u2026underscoring its importance.\")"),

    # Copula avoidance: reaching past "is" and "has" for something that sounds like more work is
    # being done. "boasts" is the purest case in the set, since there is no sentence it improves.
    (r"\b(?:serves?|stands?|functions?) as (?:a|an|the)\b", "copula avoidance (\"serves as a\")"),
    (r"\bboasts\b", "copula avoidance (\"boasts\")"),
    (r"\bplays? an? (?:key|vital|crucial|pivotal|central|significant|important) role\b",
     "\"plays a key role\""),

    # Attribution to a crowd that never gets named. It is what a model does when it has a claim
    # and no source: the plural implies several authorities and cites none of them.
    (r"\b(?:experts|observers|critics|analysts|researchers|scholars) (?:say|argue|note|noted|have "
     r"noted|have cited|agree|believe|suggest)\b", "vague attribution (\"experts argue\")"),
    (r"\b(?:industry reports|studies have shown|research (?:shows|suggests)|it is widely "
     r"(?:believed|regarded|considered|held))\b", "vague attribution (\"studies have shown\")"),

    # The "Challenges and Future Prospects" close: a paragraph that arrives whatever the subject
    # is, concedes a difficulty in the abstract, and finishes hopeful.
    (r"\bdespite (?:its|their|the)\b[^.?!]{0,70}?\bfaces?\b[^.?!]{0,30}?\bchallenges\b",
     "\"despite its X, Y faces challenges\""),

    # Chat-window filler: a model performing enthusiasm at a reader.
    (r"\bhere'?s the (?:thing|kicker|catch|deal)\b", "chat filler (\"here's the thing\")"),
    (r"\blet that sink in\b", "chat filler (\"let that sink in\")"),
    (r"\bthe bottom line (?:is|here)\b", "chat filler (\"the bottom line is\")"),
    (r"\bbuckle up\b", "chat filler (\"buckle up\")"),

    # Paste artifacts: markup that exists only inside a chat client's own rendering. Any one of
    # them means text went from a window into a file without being read. No judgement required and
    # no false positive available, which makes these the cheapest checks in the file — and the only
    # ones here that catch PROVENANCE rather than cadence.
    (r"contentReference|oaicite|turn\d+(?:search|view|news|image)\d+", "paste artifact (ChatGPT)"),
    (r"\[cite:\s*\d+\]|\[span_\d+\]\(start_span\)", "paste artifact (Gemini)"),
    (r"<grok[-_]card|grok_render", "paste artifact (Grok)"),
    (r"[\u3010\u3011]", "paste artifact (lenticular citation bracket)"),
    (r"\bas an AI(?: language)? model\b", "assistant self-reference (\"as an AI model\")"),
]

# ---- soft tells: counted and reported, never failed over ----------------------------------------
# Corporate-register vocabulary. One or two is nothing; a cluster is a smell. Words this project
# has legitimate technical use for (e.g. "robust" about a parser) are why these are soft.
SOFT_WORDS = [
    "leverage", "utilize", "utilise", "seamless", "robust", "holistic", "synergy",
    "cutting-edge", "state-of-the-art", "game-changing", "myriad", "plethora",
    "tapestry", "realm", "landscape", "testament to", "underscore", "pivotal",
    "meticulous", "moreover", "furthermore", "additionally", "notably",
    "comprehensive", "streamline", "elevate", "empower", "unlock", "harness",
    "crucial", "essential", "vital", "significant", "innovative", "transformative",
    # Added 2026-08-22 alongside the hard tells above: the promotional register the same three
    # sources name, plus the mid-2025-on framing verbs in their non-participial uses. Soft for the
    # usual reason. "rich", "marked" and "profound" all have honest work in a western, and a
    # checker that fails on those is a checker that gets switched off.
    "vibrant", "nestled", "breathtaking", "showcase", "showcasing", "align with", "fostering",
    "intricate", "testament", "groundbreaking", "commitment to", "emphasizing", "highlighting",
    "multifaceted", "nuanced", "profound", "resonate", "unwavering",
]

SENT_SPLIT = re.compile(r"(?<=[.!?])[\s\n]+")
ENTITY = re.compile(r"&(?:#\d{1,5}|#x[0-9a-fA-F]{1,5}|[a-zA-Z]{2,10});")
ENTITY_DASH = re.compile(r"&(?:mdash|#8212|#x2014);", re.I)


def _blank(m):
    """Replace a span with the same number of characters, keeping newlines where they were."""
    return re.sub(r"[^\n]", " ", m.group(0))


def _keep_link_text(m):
    """`[text](url)` -> `text` padded back out to the original width."""
    inner = m.group(1)
    return inner + " " * (len(m.group(0)) - len(inner))


def strip_html(text):
    """Blank out HTML so the books can go through the same scan. Length-preserving, as below.

    CAVEAT, and do not quote the number without it: the BURSTINESS figure for an .html target is
    not trustworthy. Blanking tags leaves table cells, headings and stat-block fields running
    together with no terminal punctuation between them, so the sentence splitter produces
    pseudo-sentences of several hundred words — the reported range goes to 1,268 on the Player's
    Book — and that inflates the standard deviation enormously. The books measured 0.65 / 0.94 /
    0.49 under a proper text extraction; this scan reports 1.56 / 1.16 / 0.92 for the same prose.
    The TELL SCAN on .html is sound, because it matches local phrasing and does not care where the
    sentence boundaries are. Use this for the tells; use the book audit for burstiness.
    """
    text = re.sub(r"<script.*?</script>", _blank, text, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", _blank, text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", _blank, text)
    # An em dash spelled `&mdash;` is an em dash. Blanking it with everything else made the dash
    # column blind to the books' actual house punctuation: all three builders write the entity, so
    # the metric was only ever seeing the handful of literal dashes that come in through creature
    # data and quote attributions. Keep the character, pad the rest of the entity back out, so the
    # count is real and the length stays preserved for line numbers.
    text = re.sub(r"&(?:mdash|#8212|#x2014);",
                  lambda m: "—" + " " * (len(m.group(0)) - 1), text, flags=re.I)
    text = re.sub(r"&[a-zA-Z]+;|&#\d+;", _blank, text)
    return text


def strip_markup(text):
    """Blank out what isn't prose: code fences, inline code, tables, link URLs, HTML comments.

    LENGTH-PRESERVING, deliberately. The first version collapsed spans to a single space, so every
    match offset afterwards was shorter than the original and the line numbers it reported were
    fiction — it pointed at lines 233 and 563 for tells that were nowhere near either. A checker
    that reports the wrong location is worse than no checker: it sends you to rewrite innocent
    prose. Blanking instead of deleting keeps offsets 1:1 with the raw text.
    """
    text = re.sub(r"```.*?```", _blank, text, flags=re.S)
    text = re.sub(r"<!--.*?-->", _blank, text, flags=re.S)
    text = re.sub(r"`[^`]*`", _blank, text)
    text = re.sub(r"^\s*\|.*$", _blank, text, flags=re.M)          # table rows
    text = re.sub(r"^\s{4,}\S.*$", _blank, text, flags=re.M)       # indented code
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", _keep_link_text, text)
    text = re.sub(r"https?://\S+", _blank, text)
    text = re.sub(r"^(#{1,6})", _blank, text, flags=re.M)          # heading marks
    text = re.sub(r"[*_>]", " ", text)
    return text


# Quoted spans get reported SEPARATELY but still COUNT as findings.
#
# The first version of this excused them as "somebody else's cadence". That was circular and wrong,
# and it was caught immediately: what these docs quote is the BOOKS, and the books were written by
# the same hand as the docs. Labelling your own prose a quotation does not make it somebody else's,
# it just launders the finding — the one thing an audit must never do. Both hits on the first real
# run were book rules text (`a Rank "is not how hard the Sign is to say; it is how far you have to
# reach"`, `"this is not a thing you kill, it is a thing you resolve"`), and scanning the books
# themselves then turned up SIXTEEN of the same construction that this scan had been waving through.
#
# The only thing quoting changes is WHERE the fix goes: not in the changelog, which is a record of
# what the book said and must stay accurate, but in the book. So a quoted hit is still a hit, and it
# is labelled with where it actually lives.
#
# Two things this pattern has to get right. It allows a quote to WRAP: these docs are hard-wrapped
# at ~95 columns, so a quoted rule almost always straddles a newline, and forbidding \n meant no
# quote was ever recognised. It stops at a blank line, so an unbalanced quote mark cannot swallow
# the rest of the file. And the delimiters are double quotes ONLY — including the apostrophe would
# make "don't … it's" read as a quoted span and would MASK genuine tells, which is the one failure
# mode worse than a false positive here.
QUOTE_SPAN = re.compile(r'["“]((?:[^"“”]|\n(?!\s*\n)){4,300}?)["”]')


def quoted_ranges(text):
    return [(m.start(), m.end()) for m in QUOTE_SPAN.finditer(text)]


def in_quotes(pos, ranges):
    return any(a <= pos < b for a, b in ranges)


# Soft-tell words that are part of a proper noun or a real technical compound in THIS project.
# "Vital Breath" was the Medicine Man's pool until the merge of 2026-09-02 and is kept here so a
# reprint of an older book still scans; "landscape-Letter" is a page orientation.
COMPOUNDS = [r"Vital Breath", r"landscape-Letter", r"landscape Letter"]


def sentences(prose):
    out = []
    for s in SENT_SPLIT.split(prose):
        words = [w for w in re.split(r"\s+", s.strip()) if w]
        if len(words) >= 2:
            out.append(len(words))
    return out


def mattr(prose, window=100):
    """Moving-average type-token ratio: the mean of unique/total over every 100-word window.

    Lower lexical diversity is one of the two findings the 2026 survey leads with, and it is the
    one a script can measure without a part-of-speech tagger. Plain TTR was the obvious first
    choice and is unusable here: it falls as a document lengthens, so CHANGELOG.md at 28,000 words
    would score far below NOTICE at 379 for reasons that have nothing to do with who wrote either.
    A fixed window removes the length dependence, which is the whole reason MATTR exists.

    The band below is calibrated on THIS REPO, not lifted from a paper. The literature reports the
    direction of the effect rather than a threshold, and a threshold copied out of a study run on
    student essays would say nothing about a changelog. Measured 2026-08-22, and the figures are
    strikingly flat across five documents of wildly different length and purpose: README 0.73 ·
    CLAUDE.md 0.75 · GK/CLAUDE.md 0.74 · CHANGELOG 0.73 · NOTICE 0.75 · commit messages 0.74.
    That flatness is what makes the column worth reading at all: one hand wrote all of them, so a
    file that drifts more than about 0.05 below its own history is the signal. The absolute number
    is close to meaningless on its own.
    """
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", prose.lower())
    if len(words) < window:
        return len(set(words)) / len(words) if words else None
    total = 0.0
    for i in range(len(words) - window + 1):
        total += len(set(words[i:i + window])) / window
    return total / (len(words) - window + 1)


def burstiness(lengths):
    if len(lengths) < 8:
        return None
    mean = sum(lengths) / len(lengths)
    if mean == 0:
        return None
    var = sum((n - mean) ** 2 for n in lengths) / len(lengths)
    return (var ** 0.5) / mean


# ---- research signals ----------------------------------------------------------------------------
# Counted per thousand words and set beside BASELINES. Most of these are fine once; the rate is the
# signal. Under --strict, any SHAPE not listed in audits/ai_tells_keep.txt fails, and so does any rate
# in STRICT_RATES running at more than twice the higher human baseline.

WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")
CONTRACTION = re.compile(r"\b[A-Za-z]+(?:n['’]t|['’](?:re|ve|ll|d|m))\b"
                         r"|\b(?:it|that|there|here|what|he|she|who|let|where|how)['’]s\b", re.I)
NOMINALIZATION = re.compile(r"\b[a-z]{3,}(?:tion|sion|ment|ness|ity|ance|ence|ancy|ency)s?\b", re.I)
PARTICIPLE = re.compile(r",\s+(?:[a-z]+ly\s+)?([a-z]{2,}ing)\b", re.I)
TRICOLON = re.compile(r"(?<![,;]\s)(?<![\w'’-])[\w'’-]+(?:\s[\w'’-]+){0,2},\s[\w'’-]+(?:\s[\w'’-]+){0,2}"
                      r",?\s(?:and|or)\s[\w'’-]+", re.I)

# The negative-parallelism shapes the hard list does not fail on. "…, not two." and "no X, just Y"
# have honest uses in rules text, so they count toward the rate and never fail alone.
NEGPAR_HARD = [re.compile(p, re.I) for p, lab in HARD if lab.startswith("negative parallelism")]
NEGPAR_SOFT = [re.compile(p, re.I) for p in (
    r",\s+not\s+(?:a\s+|an\s+|the\s+)?[\w'’-]+(?:\s+[\w'’-]+){0,2}[.!?;]",
    r"\bno\s+[\w'’-]+(?:\s+[\w'’-]+){0,3},\s+(?:just|only)\s+[\w'’-]+",
    r"\bnot because\b[^.;!?]{2,80}\bbut because\b",
    r"\bless (?:a|an|of an?) [\w'’-]+(?:\s+[\w'’-]+){0,2} than (?:a|an) [\w'’-]+",
    r"\bnever\b[^.;!?]{2,40}[;,]\s+(?:always|only)\b",
)]

# Shapes that are worth a person's eye every time they appear.
# "the whole of it" is often literal ("clears the whole of it", meaning all of the Mark). The habit
# is the definition: "Scarcity is the whole of its power", "kindness is the whole of the creed".
SHAPES = [
    ("\"the whole of it\"", re.compile(r"\b(?:is|was|are|were|be)\s+(?:all\s+)?" + LEX.CLAUDE_REGISTER[0][2:],
                                       re.I)),
    ("invented authority", re.compile(
        r"\b(?:\w+|\d+) years (?:behind (?:a|the) screen|(?:of|spent) (?:running|gming|game-?mastering|"
        r"designing|playtesting))\b|\bas (?:a|an) (?:veteran|seasoned|experienced) "
        r"(?:game ?master|gm|keeper|designer)\b", re.I)),
    ("stated theme", re.compile("|".join(LEX.THEME_STATEMENT), re.I)),
]
# In a book set in 1885, a modern year or talk of earlier printings is the edit history showing.
BOOK_SHAPES = [
    ("edit history inside the book", re.compile(
        r"\b(?:was|were) (?:printed|moved|carried|kept) in (?:the )?(?:player|keeper)['’]s book until\b"
        r"|\b(?:until|since|as of|before|after) (?:199\d|20\d\d)\b"
        r"|\bin (?:an|the) (?:earlier|previous|last) (?:version|edition|printing|release)\b", re.I)),
]
NAMED_CLOSER = re.compile(r"^(?:that|this|which)(?: is|['’]s) (?:the (?:point|tell|trick|job|lesson|"
                          r"difference|whole of it)|what (?:it|they|he|she|this|that) (?:is|are) for)"
                          r"[.!]?$", re.I)

def _phrase_re(p):
    return re.compile(r"(?<![\w'’-])" + re.escape(p) + r"(?![\w'’-])", re.I)

SLOP_RES = [(p, _phrase_re(p)) for p in LEX.ANTISLOP]
WIKI_RES = [(p, _phrase_re(p)) for p in LEX.WIKI_PHRASES]
CLAUDE_RES = [(p, re.compile(p, re.I)) for p in LEX.CLAUDE_REGISTER]
SMELL_RES = [re.compile(p, re.I) for p in LEX.SMELL]
BODY_RES = [re.compile(p, re.I) for p in LEX.BODY_EMOTION]
THEME_RES = [re.compile(p, re.I) for p in LEX.THEME_STATEMENT]
NAME_RES = [(n, re.compile(r"(?<![\w'’-])" + re.escape(n) + r"(?![\w'’-])"))
            for n in LEX.SLOP_NAMES_ANTISLOP + LEX.SLOP_NAMES_REPORTED]

# Rates that can fail a --strict run, and the columns the report prints, in order.
STRICT_RATES = ["negpar", "twobeat", "echo", "claude", "slop"]
COLUMNS = [("negpar", "negp"), ("twobeat", "2bt"), ("closer", "clos%"), ("tricolon", "tri"),
           ("echo", "echo"), ("claude", "cla"), ("slop", "slop"), ("wiki", "wiki"), ("smell", "smel"),
           ("body", "body"), ("theme", "them"), ("ptcp", "ptcp"), ("nomin", "nomi"), ("contr", "cont"),
           ("hapax", "hapx"), ("lexd", "lexd")]
VOICE = [("dash", "dash"), ("semi", "semi"), ("colon", "coln"), ("paren", "parn"),
         ("question", "ques"), ("contr", "cont"), ("mean_len", "slen"), ("burst", "brst"),
         ("nomin", "nomi"), ("ptcp", "ptcp"), ("word_len", "wlen"), ("long", "long%")]

# From `--calibrate` on 2026-09-16, over the two texts named at the foot of ai_tells_lexicon.py:
# the 5e SRD (208,164 words of rules) and The Virginian (129,416 words of western prose).
BASELINES = {
    "srd5": {"negpar": 0.062, "twobeat": 0.029, "closer": 2.409, "tricolon": 4.194, "echo": 1.182,
             "claude": 0.029, "slop": 0.355, "wiki": 0.038, "smell": 0.466, "body": 0.0, "theme": 0.0,
             "ptcp": 2.959, "nomin": 32.345, "contr": 5.044, "hapax": 0.183, "lexd": 0.566,
             "dash": 3.862, "semi": 0.538, "colon": 13.388, "paren": 16.468, "question": 0.062,
             "mean_len": 10.759, "burst": 0.924, "word_len": 4.668, "long": 8.348},
    "virginian": {"negpar": 0.108, "twobeat": 0.379, "closer": 6.694, "tricolon": 3.06, "echo": 0.34,
                  "claude": 0.224, "slop": 0.039, "wiki": 0.008, "smell": 0.077, "body": 0.0,
                  "theme": 0.0, "ptcp": 3.493, "nomin": 11.907, "contr": 15.5, "hapax": 0.306,
                  "lexd": 0.443, "dash": 5.084, "semi": 5.656, "colon": 1.02, "paren": 0.348,
                  "question": 6.738, "mean_len": 13.284, "burst": 0.761, "word_len": 4.257,
                  "long": 5.575},
}

# An optional profile of the author's own informal writing, kept on the author's machine and out of
# git. When it is present the report adds a column showing how far each book sits from it.
VOICE_PROFILE = ROOT / "voice-profile.local.json"
KEEP_FILE = Path(__file__).resolve().parent / "ai_tells_keep.txt"


ABBREVIATIONS = re.compile(r"\b(?:Ch|ch|vs|pp?|No|no|St|Mt|Ft|Dr|Mr|Mrs|Jr|Sr|Co|etc|e\.g|i\.e|cf|approx)\.")


def _sentences(text):
    """Sentences, without splitting after "Ch." or "vs." or "e.g."."""
    guarded = ABBREVIATIONS.sub(lambda m: m.group(0)[:-1] + "․", text)
    return [s.strip().replace("․", ".") for s in SENT_SPLIT.split(guarded) if WORD.search(s)]


def _nwords(s):
    return len(WORD.findall(s))


def _snip(text, start, end, pad=60):
    return re.sub(r"\s+", " ", text[max(0, start - pad):end + pad]).strip()


def echo_head(sentence):
    """A clause, a coordinator, then that clause's opening words again: "evidence that it never
    happened or evidence that it keeps happening". Returns the repeated words, or None."""
    toks = [t.lower().strip("'’") for t in WORD.findall(sentence)]
    for k, t in enumerate(toks):
        if t not in ("or", "and", "but", "yet", "nor"):
            continue
        for n in (3, 2):
            head = toks[k + 1:k + 1 + n]
            # Single letters are dice and versions ("3d6 at 4th, 4d6 at 7th"), not words.
            if len(head) < n or any(len(h) < 2 for h in head) or \
                    all(h in LEX.HEAD_STOPS for h in head):
                continue
            for i in range(max(0, k - 14), k - n):
                if toks[i:i + n] == head:
                    return " ".join(head)
    return None


def two_beats(sents):
    """Pairs of tiny sentences, the two-beat reveal: "Not worse. Quieter." / "Every time. No
    exceptions." Returns each pair as one string."""
    out = []
    for i in range(len(sents) - 1):
        a, b = sents[i], sents[i + 1]
        if re.search(r"[\d=–]", a + b):          # rules and tables: "Score 8–9 gives –1."
            continue
        na, nb = _nwords(a), _nwords(b)
        nots = a.lower().startswith("not ") or b.lower().startswith("not ")
        # A pair of short sentences opening a paragraph is usually a label and its rule ("Failure.
        # You fall short."). The reveal comes after something longer has been said.
        after_long = i > 0 and _nwords(sents[i - 1]) >= 8
        if (nots and na <= 4 and nb <= 4) or \
                (after_long and na <= 3 and nb <= 3 and a.endswith(".") and b.endswith(".")):
            out.append(f"{a} {b}")
    return out


def hapax_share(words, window=1000, step=500):
    """Share of words used exactly once, averaged over 1,000-word windows so length does not decide
    it. One of the lexical-richness measures in arXiv:2606.04177."""
    if not words:
        return None
    if len(words) < window:
        spans = [words]
    else:
        spans = [words[i:i + window] for i in range(0, len(words) - window + 1, step)]
    shares = []
    for span in spans:
        once = sum(1 for n in collections.Counter(span).values() if n == 1)
        shares.append(once / len(span))
    return sum(shares) / len(shares)


def doc_units(prose):
    """A markdown-ish document as (where, paragraph) pairs, split on blank lines."""
    out, pos = [], 0
    for block in re.split(r"(\n[ \t]*\n)", prose):
        if block.strip() and WORD.search(block):
            out.append((f"L{prose.count(chr(10), 0, pos) + 1}", re.sub(r"\s+", " ", block).strip()))
        pos += len(block)
    return out


# A tag, including one whose quoted attribute holds a ">" (the map download button's onclick does).
TAG = re.compile(r"<[a-zA-Z/!][^>\"']*(?:\"[^\"]*\"[^>\"']*|'[^']*'[^>\"']*)*>")
BLOCK_TAG = re.compile(r"</?(?:p|li|div|blockquote|section|ul|ol|dd|dt|dl|figure|figcaption|aside|"
                       r"header|footer|br|hr)\b(?:[^>\"']|\"[^\"]*\"|'[^']*')*>", re.I)


# Elements that are typography rather than prose: stat blocks, running heads, page numbers, the
# "Found —" label and the dash before a witness's name. Their dashes are not the author's.
NOT_PROSE_CLASSES = ["statblock", "runhead", "pg", "cf-tag", "src", "kn-tag", "cr-name", "ix-hd"]
NOT_PROSE_CHAPTERS = ("", "Contents", "Index", "The Ledger")


def _blank_classes(src, classes):
    """Blank every element carrying one of `classes`, nested children and all, keeping offsets."""
    opener = re.compile(r'<(div|span|p)\b[^>]*\bclass="(?:[^"]*\s)?(?:' + "|".join(map(re.escape, classes))
                        + r')(?:\s[^"]*)?"[^>]*>', re.I)
    spans = []
    for m in opener.finditer(src):
        if spans and m.start() < spans[-1][1]:
            continue
        depth = 1
        for t in re.finditer(r"<(/?)" + m.group(1) + r"\b[^>]*>", src[m.end():], re.I):
            depth += -1 if t.group(1) else 1
            if depth == 0:
                spans.append((m.start(), m.end() + t.end()))
                break
    parts, last = [], 0
    for a, b in spans:
        parts += [src[last:a], re.sub(r"[^\n]", " ", src[a:b])]
        last = b
    return "".join(parts) + src[last:]


def book_units(path):
    """A built book as (chapter :: section, block of prose) pairs.

    Reads every block of text, boxes and callouts included, which tools/extract_rules.py does not
    (it takes <p> and <li> only, and a Keeper's box is a <div>). Tables, maps, scripts, stat blocks
    and the rest of NOT_PROSE_CLASSES are left out, and so are the chapters in NOT_PROSE_CHAPTERS."""
    import html as H
    src = _blank_classes(Path(path).read_text(encoding="utf-8"), NOT_PROSE_CLASSES)
    heads = [(m.start(), 1, m.group(1)) for m in re.finditer(r'<h1 class="chapter"[^>]*>(.*?)</h1>', src, re.S)]
    heads += [(m.start(), 2, m.group(1)) for m in re.finditer(r"<h2\b[^>]*>(.*?)</h2>", src, re.S)]
    heads = sorted((pos, kind, re.sub(r"\s+", " ", H.unescape(TAG.sub(" ", t))).strip()) for pos, kind, t in heads)

    clean = src
    for pat in (r"<(script|style)\b.*?</\1>", r"<table\b.*?</table>", r"<svg\b.*?</svg>",
                r"<(h[1-6])\b.*?</\1>"):
        clean = re.sub(pat, _blank, clean, flags=re.S | re.I)
    clean = BLOCK_TAG.sub(lambda m: "\n\n" + " " * (len(m.group(0)) - 2), clean)
    clean = TAG.sub(_blank, clean)

    out, chapter, section, hi = [], "", "", 0
    for m in re.finditer(r"(?:[^\n]|\n(?![ \t]*\n))+", clean):
        while hi < len(heads) and heads[hi][0] <= m.start():
            _, kind, title = heads[hi]
            chapter, section = (re.sub(r"^[IVXL]+\.\s*", "", title), "") if kind == 1 else (chapter, title)
            hi += 1
        text = re.sub(r"\s+", " ", H.unescape(m.group(0))).strip()
        if not WORD.search(text) or chapter in NOT_PROSE_CHAPTERS:
            continue
        out.append((f"{chapter} :: {section}" if section else chapter, text))
    return out


def research(units, book=False):
    """Every research signal for one document. `units` is a list of (where, paragraph)."""
    words, lens, instances = [], [], []
    c = collections.Counter()
    names = collections.Counter()
    shapes = SHAPES + (BOOK_SHAPES if book else [])
    for where, text in units:
        ws = [w.lower() for w in WORD.findall(text)]
        if not ws:
            continue
        words += ws
        sents = _sentences(text)
        lens += [_nwords(s) for s in sents]

        if len(sents) >= 3:
            c["closer_eligible"] += 1
            if _nwords(sents[-1]) <= 6 and _nwords(sents[-2]) >= 12:
                c["closer"] += 1
        for s in sents:
            if NAMED_CLOSER.match(s):
                instances.append(("named closer", where, s))
            head = echo_head(s)
            if head:
                c["echo"] += 1
                instances.append(("echo", where, f"[{head}] {s}"))
        for pair in two_beats(sents):
            c["twobeat"] += 1
            instances.append(("two-beat reveal", where, pair))

        for rx in NEGPAR_HARD + NEGPAR_SOFT:
            for m in rx.finditer(text):
                c["negpar"] += 1
                instances.append(("negative parallelism", where, _snip(text, m.start(), m.end())))
        for label, rx in shapes:
            for m in rx.finditer(text):
                instances.append((label, where, _snip(text, m.start(), m.end())))

        for group, key in ((CLAUDE_RES, "claude"), (SLOP_RES, "slop"), (WIKI_RES, "wiki")):
            for phrase, rx in group:
                for m in rx.finditer(text):
                    c[key] += 1
                    if key != "wiki":
                        instances.append((f"{key}: {m.group(0).lower()}", where, _snip(text, m.start(), m.end())))
        c["smell"] += sum(len(rx.findall(text)) for rx in SMELL_RES)
        c["body"] += sum(len(rx.findall(text)) for rx in BODY_RES)
        c["theme"] += sum(len(rx.findall(text)) for rx in THEME_RES)
        c["tricolon"] += len(TRICOLON.findall(text))
        c["ptcp"] += sum(1 for m in PARTICIPLE.finditer(text) if m.group(1).lower() not in LEX.ING_NOUNS)
        c["nomin"] += len(NOMINALIZATION.findall(text))
        c["contr"] += len(CONTRACTION.findall(text))
        c["dash"] += text.count("—") + text.count("--")
        c["semi"] += text.count(";")
        c["colon"] += text.count(":")
        c["paren"] += text.count("(")
        c["question"] += text.count("?")
        for n, rx in NAME_RES:
            m = rx.search(text)
            if m:
                names[n] += len(rx.findall(text))
                instances.append((f"name: {n}", where, _snip(text, m.start(), m.end())))

    nw = max(1, len(words))
    per_k = lambda k: c[k] * 1000.0 / nw  # noqa: E731
    rates = {k: per_k(k) for k in ("negpar", "twobeat", "tricolon", "echo", "claude", "slop", "wiki",
                                   "smell", "body", "theme", "ptcp", "nomin", "contr", "dash", "semi",
                                   "colon", "paren", "question")}
    rates["closer"] = 100.0 * c["closer"] / c["closer_eligible"] if c["closer_eligible"] >= 20 else None
    rates["hapax"] = hapax_share(words)
    rates["lexd"] = sum(1 for w in words if w not in LEX.FUNCTION_WORDS) / nw if words else None
    mean_len = sum(lens) / len(lens) if lens else None
    rates["mean_len"] = mean_len
    rates["burst"] = burstiness(lens)
    rates["word_len"] = sum(len(w) for w in words) / nw if words else None
    rates["long"] = 100.0 * sum(1 for w in words if len(w) >= 9) / nw if words else None
    return {"words": len(words), "counts": dict(c), "rates": rates, "instances": instances,
            "names": dict(names)}


def flag(key, rates, counts):
    """True when a rate runs at more than twice the higher human baseline, on at least three hits."""
    rate = rates.get(key)
    if rate is None or not BASELINES:
        return False
    base = max((b.get(key) or 0.0) for b in BASELINES.values())
    hits = counts.get(key, 0)
    return hits >= 3 and rate > max(2.0 * base, 0.25)


def load_keep():
    """audits/ai_tells_keep.txt: one kept instance per line, `file<TAB>fragment<TAB>why`. An author
    may keep a device on purpose; the rate still counts it, the shape list stops asking."""
    keep = []
    if KEEP_FILE.is_file():
        for line in KEEP_FILE.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                parts = line.split("\t")
                if len(parts) >= 2:
                    keep.append((parts[0].strip(), parts[1].strip().lower()))
    return keep


def audit(name, raw, units=None, book=False):
    prose = strip_html(raw) if name.endswith(".html") else strip_markup(raw)
    lens = sentences(prose)
    b = burstiness(lens)
    low = prose.lower()

    qranges = quoted_ranges(prose)
    hard, quoted = [], []
    for pat, label in HARD:
        for m in re.finditer(pat, low, flags=re.I):
            line = prose.count("\n", 0, m.start()) + 1
            snippet = re.sub(r"\s+", " ", prose[max(0, m.start() - 40):m.end() + 40]).strip()
            (quoted if in_quotes(m.start(), qranges) else hard).append((label, line, snippet))

    # Blank the project's own proper nouns before counting soft words, so "Vital Breath" is not
    # read as the corporate "vital" and "landscape-Letter" is not read as "landscape".
    softtext = prose
    for c in COMPOUNDS:
        softtext = re.sub(c, _blank, softtext, flags=re.I)
    softlow = softtext.lower()
    soft = {}
    for w in SOFT_WORDS:
        hits = [m.start() for m in re.finditer(r"\b" + re.escape(w) + r"\b", softlow)]
        if hits:
            ln = softtext.count("\n", 0, hits[0]) + 1
            ctx = re.sub(r"\s+", " ", softtext[max(0, hits[0] - 45):hits[0] + 55]).strip()
            soft[w] = (len(hits), ln, ctx)

    # Em-dash density, per THOUSAND WORDS. It was per thousand characters until 2026-08-09, which is
    # the same number divided by about six, and it was being read against a per-word baseline — so
    # the column had been quietly reporting a sixth of the real figure since the day it was added.
    # The baseline it is read against: Freeburg 2026 measured 3.23 em dashes per 1,000 words across
    # 57k words of published human essays, against 10.62 for GPT-4.1, and found the frontier models
    # spread from 0 to 10-plus. So the dash is not a binary tell; density is the whole signal, and
    # the band below is set where a real editor would start noticing rather than where a detector
    # trips.
    nwords = max(1, sum(lens))

    # An HTML entity is text, not punctuation, and the books write theirs out longhand. Counting
    # raw characters therefore read `&rsquo;` as a semicolon nobody typed and missed every
    # `&mdash;` entirely — so the dash column sat dead still through a pass that removed fifty of
    # them by hand, and the three books' wildly different dash rates were measuring which spelling
    # each builder happened to use. Blank the entities to same-length filler (the same
    # length-preserving trick strip_html uses, so reported line numbers stay true) and count the
    # spelled-out dashes separately.
    spelled = len(ENTITY_DASH.findall(prose))
    clean = ENTITY.sub(lambda m: "·" * len(m.group(0)), prose)
    em_1k = (clean.count("—") + spelled) / (nwords / 1000)

    # Punctuation variety. The 2026 work on markdown-shaped prose finds LLM output leans on a
    # narrow inventory — period, comma, em dash — where human prose reaches for semicolons, colons,
    # parentheses and question marks. Counted as the share of "reaching" marks among all marks.
    marks = {c: clean.count(c) for c in ",.;:?!()"}
    reach = sum(marks[c] for c in ";:?!()")
    variety = reach / max(1, sum(marks.values()))

    # Opener repetition. Distinct first-two-words as a share of sentences: generated prose restarts
    # its sentences from a smaller stock of openings than a person does.
    heads = [" ".join(s.strip().split()[:2]).lower()
             for s in SENT_SPLIT.split(prose) if len(s.split()) >= 4]
    openers = len(set(heads)) / max(1, len(heads))

    ttr = mattr(prose)

    return {
        "sentences": len(lens), "burst": b, "hard": hard, "quoted": quoted, "soft": soft,
        "words": sum(lens), "shortest": min(lens) if lens else 0, "longest": max(lens) if lens else 0,
        "emdash_per_1k": em_1k, "variety": variety, "openers": openers, "mattr": ttr,
        "research": research(units if units is not None else doc_units(prose), book),
    }


def band(b):
    if b is None:
        return "too short to measure"
    if b >= 0.55:
        return "human-like"
    if b >= 0.45:
        return "acceptable"
    return "FLAT — the tell"


# One sentence per HARD pattern, written to trip it and nothing else. Keyed by the pattern's own
# label so a renamed label breaks the link loudly instead of silently orphaning a case.
SELFCHECK = {
    "negative parallelism (not just X, but Y)": "This is not just a fix, but a rethink.",
    "negative parallelism (it isn't X, it's Y)": "It is not a bug; it is a design choice.",
    "negative parallelism (it's not about X, it's Y)": "It's not about speed, it's about care.",
    "\"more than just\"": "The app is more than just a dice roller.",
    "\"delve into\"": "Let us delve into the mechanics.",
    "generic scene-setting opener": "In today's world, every table needs a Keeper.",
    "\"it's worth noting\"": "It's worth noting that the Mark has six steps.",
    "\"when it comes to\"": "When it comes to Dread, the DC is what matters.",
    "\"that being said\"": "That being said, the rule still stands.",
    "\"in conclusion\"": "In conclusion, the posse survives.",
    "\"let's dive in\"": "Let's dive into the Bestiary.",
    "\"navigating the landscape\"": "Navigating the complexities of the frontier is hard.",
    "assistant register (\"user's \u2026\")": "This followed the user's stated plan.",
    "assistant register (\"per the user\")": "Renamed per the user on Tuesday.",
    "assistant register (\"the user wants \u2026\")": "The user wants a keyboard pass.",
    "participial restatement (\", \u2026underscoring its importance.\")":
        "The release shipped on time, underscoring its importance to the schedule.",
    "copula avoidance (\"serves as a\")": "The Bestiary serves as a reference for Keepers.",
    "copula avoidance (\"boasts\")": "The app boasts ten tabs.",
    "\"plays a key role\"": "Nerve plays a crucial role in horror scenes.",
    "vague attribution (\"experts argue\")": "Experts argue that pacing matters most.",
    "vague attribution (\"studies have shown\")": "Studies have shown that players prefer it.",
    "\"despite its X, Y faces challenges\"":
        "Despite its strengths, the system faces challenges at high levels.",
    "chat filler (\"here's the thing\")": "Here's the thing about Grit.",
    "chat filler (\"let that sink in\")": "Six steps to damnation. Let that sink in.",
    "chat filler (\"the bottom line is\")": "The bottom line is that the posse dies.",
    "chat filler (\"buckle up\")": "Buckle up, because Tier V hits hard.",
    "paste artifact (ChatGPT)": "See the note :contentReference[oaicite:3] for detail.",
    "paste artifact (Gemini)": "The rule changed [cite: 12] last year.",
    "paste artifact (Grok)": "Rendered by <grok-card id=7> in the reply.",
    "paste artifact (lenticular citation bracket)": "The source \u30107\u3011says otherwise.",
    "assistant self-reference (\"as an AI model\")": "As an AI language model, I cannot roll dice.",
}


def selfcheck():
    """Every HARD pattern must fire on a sentence built for it, and no pattern may fire on a
    control paragraph of this project's own prose. Both halves matter: the first proves the guard
    works, the second proves it is narrow enough to leave honest writing alone."""
    labels = [lab for _, lab in HARD]
    bad = 0
    missing = [lab for lab in labels if lab not in SELFCHECK]
    orphan = [lab for lab in SELFCHECK if lab not in labels]
    for lab in missing:
        print(f"  NO CASE   {lab}")
    for lab in orphan:
        print(f"  ORPHANED  {lab}  (label renamed? case now tests nothing)")
    bad += len(missing) + len(orphan)
    for pat, lab in HARD:
        case = SELFCHECK.get(lab)
        if case is None:
            continue
        if not re.search(pat, case, flags=re.I):
            print(f"  DEAD      {lab}\n            did not match: {case}")
            bad += 1
    control = (
        "The posse rode out at first light. Nerve is Resolve plus level, and it is spent on "
        "Dread Checks. Four points a soul, and a standout costs sixteen. The Keeper decides "
        "what the ground is worth before the shooting starts, then rolls in the open."
    )
    for pat, lab in HARD:
        if re.search(pat, control, flags=re.I):
            print(f"  TRIGGERY  {lab} fires on ordinary prose")
            bad += 1
    # The research shapes: each must be found in its case, and none in the control.
    for label, case in RESEARCH_CASES.items():
        found = [lab for lab, _, _ in research([("case", case)], book=True)["instances"]]
        if not any(lab.startswith(label) for lab in found):
            print(f"  DEAD      research shape {label}\n            did not match: {case}")
            bad += 1
    control_hits = [lab for lab, _, _ in research([("control", control)], book=True)["instances"]]
    for lab in control_hits:
        print(f"  TRIGGERY  research shape {lab} fires on ordinary prose")
        bad += 1
    # The counters, on sentences whose right answer is known.
    for text, key, want in COUNTER_CASES:
        got = research([("case", text)])["counts"].get(key, 0)
        if got != want:
            print(f"  MISCOUNT  {key}: wanted {want}, got {got} in: {text}")
            bad += 1

    print(f"\n{len(labels)} hard pattern(s), {len(SELFCHECK)} case(s), {len(RESEARCH_CASES)} research "
          f"shape(s), {len(COUNTER_CASES)} counter case(s): "
          + ("all fire on their case and none on the control." if not bad else f"{bad} problem(s)."))
    return 1 if bad else 0


RESEARCH_CASES = {
    "\"the whole of it\"": "Eating together is the whole of the worship.",
    "invented authority": "Thirty years behind a screen teaches one thing about devils.",
    "stated theme": "The lesson here is that greed always costs you in the end.",
    "edit history inside the book": "This was printed in the Player's Book until 2026.",
    "named closer": "Keep the dice hidden from the players at every table. That is the point.",
    "two-beat reveal": "The town was quieter after the revival came through. Not worse. Quieter.",
    "echo": "It is either evidence that it never happened or evidence that it keeps happening.",
}

COUNTER_CASES = [
    ("I don't think it's wrong, and they won't mind.", "contr", 3),
    ("Bring guns, horses, and whiskey to the fight.", "tricolon", 1),
    ("Bring guns, horses, whiskey, and rope to the fight.", "tricolon", 0),
    ("The posse rode on, leaving the town behind them.", "ptcp", 1),
    ("He found the thing, nothing more than that.", "ptcp", 0),
    ("The arrangement needed careful consideration.", "nomin", 2),
]


def main():
    # Walk the argv rather than filtering it: the value after --commits is a count, not a file, and
    # filtering only on a leading "--" swallowed it as a filename and audited nothing else.
    args, ncommits, books, i = [], 0, False, 1
    worklist = profile_out = None
    while i < len(sys.argv):
        a = sys.argv[i]
        if a == "--commits":
            ncommits = int(sys.argv[i + 1]) if i + 1 < len(sys.argv) else 40
            i += 2
            continue
        if a in ("--worklist", "--profile-out"):
            value = sys.argv[i + 1] if i + 1 < len(sys.argv) else None
            worklist, profile_out = (value, profile_out) if a == "--worklist" else (worklist, value)
            i += 2
            continue
        if a == "--books":
            books = True
            i += 1
            continue
        if not a.startswith("--"):
            args.append(a)
        i += 1
    strict, show_all = "--strict" in sys.argv, "--all" in sys.argv

    if "--selfcheck" in sys.argv:
        return selfcheck()
    if "--calibrate" in sys.argv:
        return calibrate(args, profile_out)

    targets = args or (DEFAULT_DOCS + (BOOKS if books else []))
    findings = 0

    print("burstiness = sd/mean of sentence length. Books measured 0.65 / 0.94 / 0.49.")
    print("em/1kw = em dashes per thousand words (human baseline ~3.2, GPT-4.1 ~10.6, Freeburg 2026).")
    print("var = share of punctuation that is ; : ? ! ( ).  opn = distinct sentence openers.")
    print("div = lexical diversity, moving-average type-token ratio over 100-word windows.\n")
    print(f"{'file':<30}{'sents':>6}{'words':>7}{'burst':>7}  {'range':<10}"
          f"{'em/1kw':>7}{'var':>6}{'opn':>6}{'div':>6}  verdict")
    print("-" * 102)
    reports = []
    for t in targets:
        p = ROOT / t
        if not p.is_file():
            print(f"{t:<22}  (not found)")
            continue
        is_book = t in BOOKS
        r = audit(t, p.read_text(encoding="utf-8-sig"), units=book_units(p) if is_book else None,
                  book=is_book)
        reports.append((t, r))
        bs = f"{r['burst']:.2f}" if r["burst"] is not None else "  -"
        rng = f"{r['shortest']}-{r['longest']}"
        dv = f"{r['mattr']:.2f}" if r["mattr"] is not None else "  -"
        print(f"{t:<30}{r['sentences']:>6}{r['words']:>7}{bs:>7}  {rng:<10}"
              f"{r['emdash_per_1k']:>7.1f}{r['variety']:>6.2f}{r['openers']:>6.2f}{dv:>6}"
              f"  {band(r['burst'])}")

    if ncommits:
        log = subprocess.run(["git", "log", f"-{ncommits}", "--format=%B%n---8<---"],
                             capture_output=True, text=True, encoding="utf-8", cwd=ROOT).stdout
        r = audit(f"last {ncommits} commits", log.replace("---8<---", ""))
        reports.append((f"commit msgs ({ncommits})", r))
        bs = f"{r['burst']:.2f}" if r["burst"] is not None else "  -"
        dv = f"{r['mattr']:.2f}" if r["mattr"] is not None else "  -"
        print(f"{'commit msgs':<22}{r['sentences']:>6}{r['words']:>7}{bs:>7}  "
              f"{str(r['shortest']) + '-' + str(r['longest']):<10}{r['emdash_per_1k']:>6.1f}"
              f"{r['variety']:>7.2f}{r['openers']:>6.2f}{dv:>6}  {band(r['burst'])}")

    # Findings in ALREADY-LANDED commit messages are reported and not counted. This is not a
    # softening. A commit message cannot be edited without rewriting history, and this project's
    # own standing rule is that history on main is not rewritten — so a hard failure there is
    # one that can never be cleared, which is exactly the defect the quoted-book-text case had.
    # (Rewritten exactly once, on 2026-08-28, to purge 68 PDF blobs that were 95% of the clone.
    # Every commit message came through it verbatim, so the reasoning here is untouched: the rule
    # is that messages are not rewritten to fix themselves, and one deliberate blob purge under
    # backup is not a licence to start.)
    # The gate for commit messages is .githooks/commit-msg, which runs this same scan over the
    # message BEFORE it is written, while it can still be changed. Files stay fatal: files can
    # be edited. (Found the hard way: a commit message written on 2026-08-01 carried the very
    # figure this audit exists to catch, and turned CI red with nothing anyone could do about it.)
    landed_msgs = [(n, r) for n, r in reports if n.startswith("commit msgs")]
    reports = [(n, r) for n, r in reports if not n.startswith("commit msgs")]

    print("\n" + "=" * 78)
    print("HARD TELLS — these are the ones to fix")
    print("=" * 78)
    for name, r in reports:
        if r["hard"]:
            findings += len(r["hard"])
            print(f"\n{name}:")
            for label, line, snip in r["hard"]:
                print(f"  L{line:<5} {label}")
                print(f"         …{snip}…")
    if not findings:
        print("\n  none.")

    # Reported in full and deliberately NOT counted. CLAUDE.md has said since this script was
    # written that quoted spans "are reported apart and never fail, since both real hits were the
    # books' own rules text quoted back into a changelog and rewriting either would falsify the
    # record" — and the tally counted them anyway and returned 1. Nobody noticed for as long as
    # nobody ran it as a gate; the first CI run ever to execute it went red on two findings that
    # the project has already ruled must stay exactly as they are, which is a check that can never
    # pass and so a check that teaches people to ignore it.
    quoted_total = sum(len(r["quoted"]) for _, r in reports)
    if quoted_total:
        print("\n" + "=" * 78)
        print("IN QUOTED BOOK TEXT — reported, never a failure. Fix them in the BOOK, not here.")
        print("=" * 78)
        print("(A changelog quoting the books must stay an accurate record of what they said, so the")
        print(" rewrite belongs upstream in build_*.py — and until it happens the quote is correct.)")
        for name, r in reports:
            for label, line, snip in r["quoted"]:
                print(f"\n{name} L{line}: {label}")
                print(f"  …{snip}…")

    msg_hits = sum(len(r["hard"]) + len(r["quoted"]) for _, r in landed_msgs)
    if msg_hits:
        print("\n" + "=" * 78)
        print("IN COMMIT MESSAGES ALREADY WRITTEN — reported, never a failure.")
        print("=" * 78)
        print("(They cannot be edited without rewriting history, which this project does not do on")
        print(" main. The commit-msg hook is what stops the next one — install the hooks once per")
        print(" clone with `git config core.hooksPath .githooks`.)")
        for name, r in landed_msgs:
            for label, line, snip in r["hard"] + r["quoted"]:
                print(f"\n{name} L{line}: {label}")
                print(f"  …{snip}…")

    print("\n" + "=" * 78)
    print("SOFT TELLS — corporate register; judgement call, never a failure")
    print("=" * 78)
    for name, r in reports + landed_msgs:
        if r["soft"]:
            print(f"\n{name}:")
            for w, (n, line, ctx) in sorted(r["soft"].items(), key=lambda kv: -kv[1][0]):
                print(f"  {w}×{n}  first at L{line}:  …{ctx}…")
    if not any(r["soft"] for _, r in reports + landed_msgs):
        print("\n  none.")

    strict_failures = report_research(reports, landed_msgs, show_all, worklist)

    print()
    if findings:
        print(f"{findings} hard tell(s). Rewrite them in your own cadence — do not just delete the words.")
        return 1
    if strict and strict_failures:
        print(f"--strict: {strict_failures} research failure(s), listed above.")
        return 1
    print("no hard tells: the prose reads as written rather than generated."
          + (f"  ({quoted_total} in quoted book text, reported above and not counted.)" if quoted_total else "")
          + (f"  (--strict would fail on {strict_failures} research finding(s).)" if strict_failures and not strict else ""))
    return 0


# Labels whose every instance needs a person's decision under --strict. The rest count toward rates.
STRICT_SHAPE_LABELS = ("\"the whole of it\"", "invented authority", "stated theme",
                       "edit history inside the book", "named closer")


def report_research(reports, landed_msgs, show_all=False, worklist=None):
    """Print the research table, the shapes, the names and the voice comparison. Returns how many
    things --strict would fail on (files only; commit messages that already landed cannot change)."""
    keep = load_keep()
    print("\n" + "=" * 78)
    print("RESEARCH SIGNALS — per 1,000 words; clos% is a share of paragraphs; hapx and lexd are shares")
    print("'!' = more than twice the higher human baseline, on three or more hits")
    print("=" * 78)
    print(f"{'':<27}" + "".join(f"{short:>6}" for _, short in COLUMNS))

    def row(label, rates, counts=None):
        cells = []
        for key, _ in COLUMNS:
            v = rates.get(key)
            if v is None:
                cells.append(f"{'-':>6}")
                continue
            text = f"{v:.2f}" if key in ("hapax", "lexd") else f"{v:.1f}"
            mark = "!" if counts is not None and flag(key, rates, counts) else ""
            cells.append(f"{text + mark:>6}")
        print(f"{label[:27]:<27}" + "".join(cells))

    for bname, brates in BASELINES.items():
        row(f"(human) {bname}", brates)
    for name, r in reports + landed_msgs:
        row(name, r["research"]["rates"], r["research"]["counts"])

    failures = 0
    rows_out = []
    for name, r in reports:
        res = r["research"]
        for key in STRICT_RATES:
            if flag(key, res["rates"], res["counts"]):
                failures += 1
        by_label = collections.defaultdict(list)
        for label, where, snip in res["instances"]:
            rows_out.append((name, label, where, snip))
            kept = any(f == name and frag in snip.lower() for f, frag in keep)
            if label in STRICT_SHAPE_LABELS and not kept:
                failures += 1
            by_label[label].append((where, snip, kept))
        if not by_label:
            continue
        print(f"\n{name}:")
        shapes = {k: v for k, v in by_label.items() if not k.startswith(("claude:", "slop:", "name:"))}
        for label, hits in sorted(shapes.items(), key=lambda kv: -len(kv[1])):
            strict_mark = "  [strict]" if label in STRICT_SHAPE_LABELS else ""
            print(f"  {label} ×{len(hits)}{strict_mark}")
            for where, snip, kept in (hits if show_all else hits[:3]):
                print(f"      {'(kept) ' if kept else ''}{where[:48]}: …{snip[:150]}…")
        for prefix in ("claude:", "slop:", "name:"):
            tally = collections.Counter(k[len(prefix):].strip() for k in by_label if k.startswith(prefix)
                                        for _ in by_label[k])
            if tally:
                top = ", ".join(f"{w} ×{n}" for w, n in tally.most_common(12))
                print(f"  {prefix[:-1]} phrases: {top}")

    if VOICE_PROFILE.is_file():
        author = json.loads(VOICE_PROFILE.read_text(encoding="utf-8")).get("rates", {})
        print("\n" + "=" * 78)
        print("VOICE — each book beside the author's own writing (local profile, never committed)")
        print("=" * 78)
        print(f"{'':<27}" + "".join(f"{short:>6}" for _, short in VOICE))
        for label, rates in [("(author)", author)] + [(f"(human) {b}", v) for b, v in BASELINES.items()] + \
                [(n, r["research"]["rates"]) for n, r in reports if n in BOOKS]:
            print(f"{label[:27]:<27}" + "".join(
                f"{'-':>6}" if rates.get(k) is None else f"{rates[k]:>6.1f}" for k, _ in VOICE))

    if worklist:
        with open(worklist, "w", encoding="utf-8") as fh:
            fh.write("file\tlabel\twhere\tsnippet\n")
            for rowv in rows_out:
                fh.write("\t".join(str(x).replace("\t", " ") for x in rowv) + "\n")
        print(f"\nwrote {len(rows_out)} research instance(s) to {worklist}")
    return failures


def calibrate(files, profile_out=None):
    """Print the research rates for plain-text or markdown files. This is how BASELINES was filled,
    and how an author's own profile is made. Project Gutenberg's header and licence are cut off."""
    units = []
    for f in files:
        raw = Path(f).read_text(encoding="utf-8-sig", errors="replace")
        body = re.search(r"\*\*\* ?START OF.*?\*\*\*(.*)\*\*\* ?END OF", raw, re.S)
        if body:
            raw = body.group(1)
        units += doc_units(strip_markup(raw) if f.endswith(".md") else raw)
    res = research(units)
    rates = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in res["rates"].items()}
    summary = json.dumps({"words": res["words"], "rates": rates}, indent=1)
    print(summary)
    if profile_out:
        Path(profile_out).write_text(summary, encoding="utf-8")
        print(f"wrote {profile_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
