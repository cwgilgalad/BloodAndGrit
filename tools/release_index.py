#!/usr/bin/env python3
"""Write RELEASES.md — the archive of every version that ever shipped.

GitHub's Releases page carries one page now: thirty-four pages of history, each with a zip nobody
downloads, is noise in front of the one download that matters, and the zips alone were 1.9 GB. The
history is not thrown away: it moves here, where it belongs, and every version stays reachable by
its git tag. Narrowed again on 2026-08-27 from three per-component pages to a single page carrying
all of them, so `/releases/latest` is right for every audience without anybody moving a flag.

Derived from the GitHub API rather than typed, which is this repo's rule about counts in prose
applied to a list of versions: nobody can forget to add a row.

    python tools/release_index.py            # this repo, from `gh`
    python tools/release_index.py --repo cwgilgalad/TideWatch --out ../TideWatch/RELEASES.md

It also reads its own last output and MERGES, so the order it is run in cannot cost anything. It
used to say "run this before deleting any release", and on 2026-08-19 somebody deleted first: the
API answered with the three pages still standing and the file went from thirty-four rows to three.
A tool that only works if you remember to run it first is a tool that will lose what it is for.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Which family a tag belongs to, and what to call that family. First match wins, so the
# order matters: `gritkeeper-` before the bare-version fallback.
FAMILIES = [
    (re.compile(r"^gritkeeper-v"), "GritKeeper — the Keeper's app"),
    (re.compile(r"^books-v"), "The three books"),
    (re.compile(r"^modules-v"), "The three modules"),
    (re.compile(r"^tidewatch-win-v"), "Tidewatch — the Windows app"),
    (re.compile(r"^tidewatch-html-v"), "Tidewatch — the HTML app"),
    (re.compile(r"^labs-v"), "The labs"),
]
OTHER = "Everything else"


def family(tag):
    for pat, name in FAMILIES:
        if pat.match(tag):
            return name
    return OTHER


def verkey(tag):
    """Sort key that puts 1.10.0 after 1.9.0, which a string sort does not."""
    nums = [int(n) for n in re.findall(r"\d+", tag)]
    return nums + [0] * (4 - len(nums)) if len(nums) < 4 else nums


ROW_RE = re.compile(r"^\|\s*(?:v[\d.]+|[\w-]+)(?:\s*\*\*[^|]*\*\*)?\s*\|\s*`([^`]+)`\s*\|"
                    r"\s*([\d-]*)\s*\|\s*(.*?)\s*\|\s*$", re.M)


def previously(path):
    """{tag: (shipped, what it was)} out of the file's own tables. The archive of what has been
    deleted from GitHub lives here and nowhere else, so it is read before it is overwritten."""
    p = Path(path)
    if not p.exists():
        return {}
    return {m.group(1): (m.group(2), m.group(3)) for m in ROW_RE.finditer(p.read_text(encoding="utf-8"))}


def title_of(rel):
    """The release's own headline, with the version stripped off the front — the table already
    has a Version column, and repeating it in every row is the kind of noise that makes a table
    unreadable. An untitled release answers with an em dash rather than a blank cell."""
    t = (rel.get("name") or "").strip()
    t = re.sub(r"^[A-Za-z&'\s]*v?\d+[\d.]*\s*(—|-|·|:)?\s*", "", t).strip()
    # A release whose headline names BOTH halves ("(Windows) / v1.16.0 (HTML) — the UX revamp")
    # is left with a parenthetical the family heading already says. Drop it; keep the sentence.
    t = re.sub(r"^\((?:Windows|HTML)\)\s*/?\s*v?[\d.]*\s*(?:\((?:Windows|HTML)\))?\s*(—|-|·|:)?\s*", "", t).strip()
    return t or "—"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=None, help="owner/name; default is the checkout's own remote")
    ap.add_argument("--out", default="RELEASES.md")
    ap.add_argument("--json", default=None, help="read a saved API dump instead of calling gh")
    a = ap.parse_args()

    if a.json:
        rels = json.loads(Path(a.json).read_text(encoding="utf-8"))
    else:
        cmd = ["gh", "api", "--paginate"]
        cmd.append(f"repos/{a.repo}/releases?per_page=100" if a.repo else "repos/{owner}/{repo}/releases?per_page=100")
        out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if out.returncode != 0:
            sys.exit(f"gh failed: {out.stderr.strip()[:400]}")
        rels = json.loads(out.stdout)

    rels = [r for r in rels if not r.get("draft")]

    # What GitHub still holds, plus what only the last file remembers. A release page that has been
    # retired keeps its row: the tag is still there, and `git checkout <tag>` still works.
    rows = {tag: {"tag_name": tag, "published_at": when, "name": None, "_kept": what}
            for tag, (when, what) in previously(a.out).items()}
    for r in rels:
        rows[r["tag_name"]] = r
    if not rows:
        sys.exit("no releases found, and no history to keep")
    rels = list(rows.values())

    groups = {}
    for r in rels:
        groups.setdefault(family(r["tag_name"]), []).append(r)

    lines = [
        "# Release history",
        "",
        "GitHub carries **one Release page**, and it holds the current build of every part of the",
        "game at once: the app, the three books, the three modules, and the six PDFs as their own",
        "downloads. Consolidated 2026-08-27 from three per-component pages, which had a trap in",
        "them — README points at `/releases/latest`, so shipping a book quietly aimed the app's",
        "download button at a zip of PDFs until somebody remembered to move the Latest flag back.",
        "",
        "Everything that ever shipped is listed here, and every version below is still reachable by its",
        "git tag:",
        "",
        "```",
        "git checkout <tag>      # the tree exactly as it shipped, at any tag below",
        "```",
        "",
        "The full notes for each version — what changed and why — are in",
        "[CHANGELOG.md](CHANGELOG.md), which is the canonical log and always has been. This page is the",
        "index to it.",
        "",
    ]

    order = [n for _, n in FAMILIES if n in groups] + ([OTHER] if OTHER in groups else [])
    for name in order:
        rs = sorted(groups[name], key=lambda r: verkey(r["tag_name"]), reverse=True)
        lines += [f"## {name}", "", "| Version | Tag | Shipped | What it was |", "|---|---|---|---|"]
        top = max(rs, key=lambda r: verkey(r["tag_name"]))["tag_name"]
        for r in rs:
            ver = re.search(r"v[\d.]+", r["tag_name"])
            # Each family has its OWN current version: the books do not stop being current because
            # the app shipped after them. One marker per table, not one for the whole page.
            star = " **← current**" if r["tag_name"] == top else ""
            lines.append(
                f"| {ver.group(0) if ver else r['tag_name']}{star} | `{r['tag_name']}` | "
                f"{(r['published_at'] or '')[:10]} | {r.get('_kept') or title_of(r)} |"
            )
        lines.append("")

    lines += [
        "---",
        "",
        f"*{len(rels)} release{'' if len(rels) == 1 else 's'} across "
        f"{len(groups)} famil{'y' if len(groups) == 1 else 'ies'}, generated by "
        "`tools/release_index.py` from the GitHub API and from this file's own last version. "
        "Regenerate it whenever a version ships.*",
        "",
    ]
    Path(a.out).write_text("\n".join(lines), encoding="utf-8")
    print(f"{a.out}: {len(rels)} releases across {len(groups)} "
          f"famil{'y' if len(groups) == 1 else 'ies'}")


if __name__ == "__main__":
    main()
