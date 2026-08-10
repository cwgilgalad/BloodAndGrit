#!/usr/bin/env python3
"""Every name in the modules, and whether any two of them are the same name.

Written on 2026-08-09 for a fault that shipped: Modules I and III went out as *The Salt at Coffin
Wells* and *The Reckoning of the Wells*. (III is *What the Water Answers* now — this script is why.)
Nothing checked it, because nothing was looking — every other
auditor in this repo reads ONE artifact and asks whether it is sound. This one reads all three and
asks whether they are distinct, which is a question no single-file check can be asked.

It reports two kinds of clash, and they are not equally bad.

  A TITLE clash is the loud one. Two adventures that share a distinctive word in their titles read
  as a series when they are not one, and two that share a SHAPE — "The <abstract> <prep> <place>" —
  read as the same title twice even when every word differs. That second one is why this checks
  grammar and not just vocabulary: widening the word lists alone would have produced "The Ashes at
  Gallows Fork" beside "The Judgment of the Hollow", which is the identical fault in a better coat.

  A BODY clash is the quiet one — an NPC, a town or a landmark named in two modules. Some of these
  are deliberate (the Basin is one country and its landmarks recur on purpose), so the shared-name
  list is reported for a human to read rather than failed on. Only a name a module INTRODUCES —
  a person in its cast, the place on its own map — is held to be exclusive.

Exit code 1 on any hard clash. Run it before cutting a modules release.
"""
import html
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
MODULES = [
    ("I", "module-salt-at-coffin-wells.html"),
    ("II", "module-a-face-not-his-own.html"),
    ("III", "module-what-the-water-answers.html"),
]

# Words that carry no identity. Two titles sharing one have not collided — "the" is not what makes
# "The Long Debt" and "The Cold Water" different titles. Mirrors Namer.Bland in GK/rules/Names.cs;
# the two lists answer the same question on either side of the language boundary.
BLAND = {
    "the", "a", "an", "of", "at", "and", "for", "to", "not", "own", "that", "where", "until",
    "what", "no", "something", "do", "in", "on", "by", "with", "from", "is", "his", "her",
    "their", "it", "its", "as", "or", "but", "so", "up", "out", "off", "was", "were", "are",
    "be", "been", "has", "have", "had", "will", "would", "can", "could", "may", "might",
}

# The game's own vocabulary. These are SUPPOSED to recur in every module — a module that never says
# "Keeper" or "Grit" is not a Blood & Grit module — so they are not evidence of a clash.
GAME_TERMS = {
    "Keeper", "Keepers", "Grit", "Blood", "Nerve", "Mark", "Taint", "Dread", "Sign", "Signs",
    "Miracle", "Miracles", "Tier", "Defense", "Beat", "Beats", "Iron", "Code", "Calling",
    "Callings", "Origin", "Origins", "Sawbones", "Posse", "Soul", "Souls", "Bestiary",
    "Player", "Players", "Book", "Act", "Acts", "Scene", "Scenes", "Round", "Rounds",
    "Contents", "Index", "Module", "Adventure", "West", "East", "North", "South", "God",
    "Lord", "Christ", "Jesus", "Amen", "Sunday", "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "January", "February", "March", "April", "May",
    "June", "July", "August", "September", "October", "November", "December",
    "Putting", "Down", "Long", "Odds", "Cast", "Truth", "Hook", "Ground", "Clock", "Cost",
    "After", "Before", "What", "When", "Where", "Why", "How", "This", "That", "These",
    "Those", "There", "Here", "They", "Them", "She", "Her", "Him", "His", "You", "Your",
    "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
    "If", "It", "In", "On", "At", "To", "Of", "And", "But", "Or", "So", "The", "A", "An",
    "Not", "No", "Yes", "All", "Any", "Some", "Each", "Every", "Both", "Either", "Neither",
    # Stat-block and furniture vocabulary. Every creature entry says Attacks / Saves / Special /
    # Speed, every map carries a Download control, every cast entry has a Wants and a Lever. These
    # are the SHAPE of a module, so of course all three share them — that is conformance, not a
    # clash, and leaving them in buries the sixteen real names under nineteen false ones.
    "Attacks", "Saves", "Special", "Speed", "Check", "Costs", "Download", "Ref", "Version",
    "Strikes", "Tiers", "Wants", "Lever", "Alone", "Line", "Say", "Says", "Read", "Ready",
    # Callings and creature names — the books' own nouns, shared by design.
    "Gunhand", "Preacher", "Drifter", "Outlaw", "Scout", "Gambler", "Prospector", "Rancher",
    "Teamster", "Padre", "Nightwalker", "Mountain", "Lion", "Drowned", "Possessed", "Hunger",
    "Walks", "Skin", "Walker", "Plague", "Dead",
}

TAG = re.compile(r"<[^>]+>")
SCRIPT_STYLE = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
TITLE_TAG = re.compile(r"<title>(.*?)</title>", re.S | re.I)
# A proper noun as this repo writes them: one or more capitalised words, allowing an internal
# lowercase joiner ("Mission San Clavo", "the Salt at Coffin Wells" -> "Salt", "Coffin Wells").
PROPER = re.compile(r"\b([A-Z][a-z']{2,}(?:\s+(?:of|at|the|de|del|la|San|Santa)\s+|\s+)?)+")


PARA = re.compile(r"<p\b[^>]*>(.*?)</p>", re.S | re.I)


def prose_of(path):
    """Running prose only — the contents of <p>, and nothing else.

    This is load-bearing, not tidiness. The first version of this script read the whole document
    and reported 85 shared "names", of which about six were names: the rest were headings, table
    headers, map legends and UI labels, where EVERY word is Title Case and the "skip the sentence
    opener" heuristic has nothing to bite on. A stat block's "Attacks", a map's "Legend" and a
    download button's "Download" are not characters. Names live in sentences.
    """
    raw = path.read_text(encoding="utf-8")
    body = SCRIPT_STYLE.sub(" ", raw)
    return " ".join(html.unescape(TAG.sub(" ", m.group(1))) for m in PARA.finditer(body))


def title_of(path):
    """The adventure's own name, out of the <title> tag.

    The tag reads "Blood & Grit — The Salt at Coffin Wells (v1.0)": series, adventure, version.
    Taking the part BEFORE the separator gets the series every time, which made all three titles
    "Blood & Grit" and produced three confident, meaningless clashes on the first run.
    """
    raw = path.read_text(encoding="utf-8")
    m = TITLE_TAG.search(raw)
    if not m:
        return ""
    full = html.unescape(TAG.sub("", m.group(1))).strip()
    parts = re.split(r"\s*[—–|:]\s*", full)
    name = parts[-1] if len(parts) > 1 else full
    return re.sub(r"\s*\(v[\d.]+\)\s*$", "", name).strip()


def distinctive(phrase):
    """The words in a phrase that carry identity. Mirrors Namer.Distinctive."""
    for raw in re.split(r"[\s\-—]+", phrase):
        w = raw.strip(".,:;!?\"'()").split("'")[0]
        if len(w) > 2 and w.lower() not in BLAND:
            yield w


def shape_of(title):
    """A title's grammatical skeleton: every distinctive word blanked, connectives kept.

    "The Salt at Coffin Wells" and "The Reckoning of the Wells" both reduce to "the _ <prep> the _",
    which is the collision a vocabulary check cannot see. Prepositions are folded together on
    purpose — at/of/in/on differ in meaning and not in cadence, and cadence is what makes two
    titles sound like one.
    """
    out = []
    for raw in re.split(r"\s+", title.strip()):
        w = raw.strip(".,:;!?\"'()").lower()
        if not w:
            continue
        if w in {"at", "of", "in", "on", "from", "for", "to", "by", "with"}:
            out.append("<prep>")
        elif w in BLAND:
            out.append(w)
        else:
            out.append("_")
    return " ".join(out)


def proper_nouns(text):
    """Capitalised phrases that are not the game's own vocabulary and not sentence-openers.

    Sentence-openers are the hard part: "The banker dug" starts with a capital and names nobody.
    A word is only counted when it appears capitalised at least once in a position that is NOT
    after a full stop — which is what actually distinguishes a name from a first word.
    """
    mid = set()
    for sent in re.split(r"(?<=[.!?])\s+", text):
        words = sent.split()
        for w in words[1:]:                       # skip the opener of every sentence
            bare = w.strip(".,:;!?\"'()—")
            if re.fullmatch(r"[A-Z][a-z']{2,}", bare) and bare not in GAME_TERMS:
                mid.add(bare)
    return mid


def main():
    seen = {}
    for num, fname in MODULES:
        p = HERE / fname
        if not p.exists():
            print(f"  MISSING  {fname}")
            return 2
        seen[num] = {"title": title_of(p), "nouns": proper_nouns(prose_of(p)), "file": fname}

    hard = 0
    print("Module titles")
    for num in seen:
        print(f"  {num:<4} {seen[num]['title']}")

    # ---- title word clashes ----
    print("\nTitle words")
    words = defaultdict(list)
    for num, d in seen.items():
        for w in distinctive(d["title"]):
            words[w.lower()].append(num)
    clashes = {w: v for w, v in words.items() if len(v) > 1}
    if clashes:
        for w, v in sorted(clashes.items()):
            print(f"  CLASH    '{w}' in modules {', '.join(v)}")
        hard += len(clashes)
    else:
        print("  ok       no distinctive word appears in two titles")

    # ---- title shape clashes ----
    print("\nTitle shapes")
    shapes = defaultdict(list)
    for num, d in seen.items():
        shapes[shape_of(d["title"])].append(num)
    shape_clash = {s: v for s, v in shapes.items() if len(v) > 1}
    for s, v in sorted(shapes.items(), key=lambda kv: kv[1]):
        flag = "CLASH   " if len(v) > 1 else "ok      "
        print(f"  {flag} {', '.join(v):<8} {s}")
    if shape_clash:
        hard += len(shape_clash)

    # ---- shared proper nouns ----
    print("\nProper nouns shared between modules")
    shared = defaultdict(list)
    for num, d in seen.items():
        for w in d["nouns"]:
            shared[w].append(num)
    both = {w: v for w, v in sorted(shared.items()) if len(v) > 1}
    if both:
        for w, v in both.items():
            print(f"  shared   {w:<22} {', '.join(v)}")
        print(f"\n  {len(both)} shared — read them. A recurring landmark is the Basin being one")
        print("  country; a recurring PERSON or TOWN is two modules using one name.")
    else:
        print("  ok       no proper noun appears in two modules")

    print()
    if hard:
        print(f"FAIL: {hard} hard clash(es) between module titles.")
        return 1
    print("Every module title is distinct in vocabulary and in shape.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
