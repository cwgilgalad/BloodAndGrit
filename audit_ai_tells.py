#!/usr/bin/env python3
"""audit_ai_tells.py — does the repository's own prose read like a person wrote it?

The books already get this treatment. The REPOSITORY did not, and the repository is what someone
sees first: the README, this project's handoff doc, the changelog, the release notes. Prose that
reads as machine-generated undercuts the work it is describing, so it gets measured the same way
the books do.

Two independent signals, because either one alone is easy to game:

  BURSTINESS — the standard deviation of sentence length divided by its mean. Human writing varies
  a lot: a four-word sentence next to a forty-word one. Generated prose regresses to a comfortable
  middle. Measured on the books earlier: 0.65 / 0.94 / 0.49. Rough bands, from that calibration:
      >= 0.55  human-like
      0.45-0.55 acceptable, watch it
      <  0.45  flat — the tell
  Note this is a signal, not a verdict. Reference docs are legitimately more uniform than prose.

  TELLS — phrases and shapes that are disproportionately common in generated text. The one this
  project cares most about is NEGATIVE PARALLELISM ("not just X, but Y" / "it isn't X, it's Y"):
  it is the single most recognisable LLM cadence and it is easy to write by accident.

Usage:
    python audit_ai_tells.py                  # audit the tracked docs, exit 1 on any hard tell
    python audit_ai_tells.py FILE [FILE ...]  # audit specific files
    python audit_ai_tells.py --commits 60     # also audit the last N commit messages
"""
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent

# The prose a reader actually meets first. GK/CLAUDE.md joined the list in v1.29.2: it was split
# out of the root CLAUDE.md on 2026-07-30 and carries ~24,000 characters of the same kind of prose,
# so leaving it off would have quietly exempted a quarter of the project's documentation from the
# standard the rest of it is held to.
DEFAULT_DOCS = ["README.md", "CLAUDE.md", "GK/CLAUDE.md", "CHANGELOG.md", "NOTICE"]

# The books. Pass --books to scan these too. They were exempted at first on the theory that their
# period-western register would confuse the scan; that was wrong, and it hid real findings — the
# cadence tells are about SHAPE, not vocabulary, and shape does not care what century the diction
# comes from. Sixteen negative-parallelism constructions were sitting in here unexamined.
BOOKS = ["blood-and-grit.html", "keeper-handbook.html", "bestiary.html"]

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
    (r"\bthe user (?:wants|asked me|requested|would like|prefers|has asked)\b", "assistant register (\"the user wants …\")"),
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
]

SENT_SPLIT = re.compile(r"(?<=[.!?])[\s\n]+")


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
# "Vital Breath" is the Medicine Man's Miracle pool; "landscape-Letter" is a page orientation.
COMPOUNDS = [r"Vital Breath", r"landscape-Letter", r"landscape Letter"]


def sentences(prose):
    out = []
    for s in SENT_SPLIT.split(prose):
        words = [w for w in re.split(r"\s+", s.strip()) if w]
        if len(words) >= 2:
            out.append(len(words))
    return out


def burstiness(lengths):
    if len(lengths) < 8:
        return None
    mean = sum(lengths) / len(lengths)
    if mean == 0:
        return None
    var = sum((n - mean) ** 2 for n in lengths) / len(lengths)
    return (var ** 0.5) / mean


def audit(name, raw):
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

    dashes = raw.count("—")
    per_1k = dashes / max(1, len(prose) / 1000)
    return {
        "sentences": len(lens), "burst": b, "hard": hard, "quoted": quoted, "soft": soft,
        "words": sum(lens), "shortest": min(lens) if lens else 0, "longest": max(lens) if lens else 0,
        "emdash_per_1k": per_1k,
    }


def band(b):
    if b is None:
        return "too short to measure"
    if b >= 0.55:
        return "human-like"
    if b >= 0.45:
        return "acceptable"
    return "FLAT — the tell"


def main():
    # Walk the argv rather than filtering it: the value after --commits is a count, not a file, and
    # filtering only on a leading "--" swallowed it as a filename and audited nothing else.
    args, ncommits, books, i = [], 0, False, 1
    while i < len(sys.argv):
        a = sys.argv[i]
        if a == "--commits":
            ncommits = int(sys.argv[i + 1]) if i + 1 < len(sys.argv) else 40
            i += 2
            continue
        if a == "--books":
            books = True
            i += 1
            continue
        if not a.startswith("--"):
            args.append(a)
        i += 1

    targets = args or (DEFAULT_DOCS + (BOOKS if books else []))
    findings = 0

    print("burstiness = sd/mean of sentence length. Books measured 0.65 / 0.94 / 0.49.\n")
    print(f"{'file':<22}{'sents':>6}{'words':>7}{'burst':>7}  {'range':<10}{'em/1k':>6}  verdict")
    print("-" * 78)
    reports = []
    for t in targets:
        p = ROOT / t
        if not p.is_file():
            print(f"{t:<22}  (not found)")
            continue
        r = audit(t, p.read_text(encoding="utf-8-sig"))
        reports.append((t, r))
        bs = f"{r['burst']:.2f}" if r["burst"] is not None else "  -"
        rng = f"{r['shortest']}-{r['longest']}"
        print(f"{t:<22}{r['sentences']:>6}{r['words']:>7}{bs:>7}  {rng:<10}{r['emdash_per_1k']:>6.1f}  {band(r['burst'])}")

    if ncommits:
        log = subprocess.run(["git", "log", f"-{ncommits}", "--format=%B%n---8<---"],
                             capture_output=True, text=True, encoding="utf-8", cwd=ROOT).stdout
        r = audit(f"last {ncommits} commits", log.replace("---8<---", ""))
        reports.append((f"commit msgs ({ncommits})", r))
        bs = f"{r['burst']:.2f}" if r["burst"] is not None else "  -"
        print(f"{'commit msgs':<22}{r['sentences']:>6}{r['words']:>7}{bs:>7}  "
              f"{str(r['shortest']) + '-' + str(r['longest']):<10}{r['emdash_per_1k']:>6.1f}  {band(r['burst'])}")

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

    print("\n" + "=" * 78)
    print("SOFT TELLS — corporate register; judgement call, never a failure")
    print("=" * 78)
    for name, r in reports:
        if r["soft"]:
            print(f"\n{name}:")
            for w, (n, line, ctx) in sorted(r["soft"].items(), key=lambda kv: -kv[1][0]):
                print(f"  {w}×{n}  first at L{line}:  …{ctx}…")
    if not any(r["soft"] for _, r in reports):
        print("\n  none.")

    print()
    if findings:
        print(f"{findings} hard tell(s). Rewrite them in your own cadence — do not just delete the words.")
        return 1
    print("no hard tells: the prose reads as written rather than generated."
          + (f"  ({quoted_total} in quoted book text, reported above and not counted.)" if quoted_total else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
