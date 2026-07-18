#!/usr/bin/env python3
"""Extract KT/source/Data/creatures.json from a built bestiary.html.

Faithfulness gate: run first against the pre-editorial bestiary.html and diff
the output against the existing creatures.json — they must match structurally
before the new HTML's output is trusted.

Usage: python extract_creatures.py bestiary.html KT/source/Data/creatures.json
"""
import html as H
import json
import re
import sys

ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}


def strip_tags(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = H.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def balanced_div(src, start):
    """src[start:] begins at a '<div'; return the block through its close."""
    depth = 0
    for m in re.finditer(r"<div\b|</div>", src[start:]):
        depth += 1 if m.group(0) != "</div>" else -1
        if depth == 0:
            return src[start : start + m.end()]
    raise ValueError("unbalanced div")


def parse(path):
    src = open(path, encoding="utf-8").read()
    chapters = [(m.start(), re.sub(r"^[IVX]+\.\s*", "", strip_tags(m.group(1))))
                for m in re.finditer(r'<h1 class="chapter">(.*?)</h1>', src, re.S)]
    out = []
    for m in re.finditer(r'<div class="creature">', src):
        block = balanced_div(src, m.start())
        chap = ""
        for pos, name in chapters:
            if pos < m.start():
                chap = name
        name = strip_tags(re.search(r'<p class="cr-name"[^>]*>(.*?)</p>', block, re.S).group(1))
        tier_text = strip_tags(re.search(r'<p class="cr-kind">(.*?)</p>', block, re.S).group(1))
        tier = ROMAN[re.match(r"Tier ([IVX]+)", tier_text).group(1)]
        lore = [strip_tags(p) for p in re.findall(r'<p class="cr-lore">(.*?)</p>', block, re.S)]

        found = ""
        fm = re.search(r'<p class="cr-found">(.*?)</p>', block, re.S)
        if fm:
            found = re.sub(r"^Found\s+—\s+", "", strip_tags(fm.group(1)))

        witness = ""
        wm = re.search(r'<div class="quote">(.*?)<span class="src">(.*?)</span>', block, re.S)
        if wm:
            witness = strip_tags(wm.group(1)) + " " + strip_tags(wm.group(2))

        keeper = ""
        km = re.search(r'<div class="keeper-note">(.*?)</div>', block, re.S)
        if km:
            keeper = strip_tags(re.sub(r'<span class="kn-tag">.*?</span>', " ", km.group(1), flags=re.S))

        sb = re.search(r'<div class="statblock">.*', block, re.S).group(0)
        stats = {}
        for lm in re.finditer(r"<span class='sb-tag'>(.*?)</span>(.*?)(?=<span class='sb-tag'>|</p>)", sb, re.S):
            stats[strip_tags(lm.group(1))] = strip_tags(lm.group(2))

        out.append({
            "name": name,
            "chapter": chap,
            "tierText": tier_text,
            "tier": tier,
            "defense": stats.get("Defense", ""),
            "blood": stats.get("Blood", ""),
            "speed": stats.get("Speed", ""),
            "saves": stats.get("Saves", ""),
            "attacks": stats.get("Attacks", ""),
            "special": stats.get("Special", ""),
            "dread": stats.get("Dread", ""),
            "puttingItDown": stats.get("Putting It Down", ""),
            "mark": stats.get("Mark", ""),
            "lore": lore,
            "found": found,
            "keeperNote": keeper,
            "witness": witness,
        })
    return out


if __name__ == "__main__":
    data = parse(sys.argv[1])
    with open(sys.argv[2], "w", encoding="utf-8", newline="") as f:
        json.dump(data, f, indent=1, ensure_ascii=True)
    print(f"{len(data)} creatures -> {sys.argv[2]}")
