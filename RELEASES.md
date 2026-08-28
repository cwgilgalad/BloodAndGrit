# Release history

GitHub carries **one Release page**, and it holds the current build of every part of the
game at once: the app, the three books, the three modules, and the six PDFs as their own
downloads. Consolidated 2026-08-27 from three per-component pages, which had a trap in
them — README points at `/releases/latest`, so shipping a book quietly aimed the app's
download button at a zip of PDFs until somebody remembered to move the Latest flag back.

Everything that ever shipped is listed here, and every version below is still reachable by its
git tag:

```
git checkout <tag>      # the tree exactly as it shipped, at any tag below
```

The full notes for each version — what changed and why — are in
[CHANGELOG.md](CHANGELOG.md), which is the canonical log and always has been. This page is the
index to it.

## GritKeeper — the Keeper's app

| Version | Tag | Shipped | What it was |
|---|---|---|---|
| v1.50.0 **← current** | `gritkeeper-v1.50.0` | 2026-08-27 | Blood & Grit — GritKeeper v1.50.0 · Books v1.6 · Modules v1.5 |
| v1.48.0 | `gritkeeper-v1.48.0` | 2026-08-24 | the Witch's familiar is a creature now |
| v1.47.0 | `gritkeeper-v1.47.0` | 2026-08-24 | Undo stops taking things you didn't ask it to |
| v1.46.0 | `gritkeeper-v1.46.0` | 2026-08-24 | onto .NET 10 |
| v1.45.0 | `gritkeeper-v1.45.0` | 2026-08-23 | the Witch's familiar is a mechanism, not a note to self |
| v1.44.0 | `gritkeeper-v1.44.0` | 2026-08-22 | the budget repriced off the harness, and a Hexer's Debts counted |
| v1.43.1 | `gritkeeper-v1.43.1` | 2026-08-21 | the status bar catches up with the books |
| v1.43.0 | `gritkeeper-v1.43.0` | 2026-08-21 | twenty-five more horrors, and two counts the app was reciting from memory |
| v1.42.0 | `gritkeeper-v1.42.0` | 2026-08-20 | the Callings can be played from the Tracker |
| v1.41.0 | `gritkeeper-v1.41.0` | 2026-08-17 | the four fights Ch. IV names |
| v1.40.1 | `gritkeeper-v1.40.1` | 2026-08-16 | the spread reaches the table |
| v1.40.0 | `gritkeeper-v1.40.0` | 2026-08-16 | the Iron Code is run rather than read out |
| v1.39.0 | `gritkeeper-v1.39.0` | 2026-08-16 | the round gives the turn back |
| v1.38.0 | `gritkeeper-v1.38.0` | 2026-08-12 | — |
| v1.37.0 | `gritkeeper-v1.37.0` | 2026-08-10 | two adventures had the same name, and nothing was looking |
| v1.36.0 | `gritkeeper-v1.36.0` | 2026-08-09 | a button may refuse, but it may not refuse in silence |
| v1.35.0 | `gritkeeper-v1.35.0` | 2026-08-09 | — |
| v1.34.0 | `gritkeeper-v1.34.0` | 2026-08-10 | the daybook, for the failure that never throws |
| v1.33.0 | `gritkeeper-v1.33.0` | 2026-08-02 | the app stops borrowing Windows' clothes |
| v1.31.0 | `gritkeeper-v1.31.0` | 2026-08-02 | the table stops living beside the exe |
| v1.30.0 | `gritkeeper-v1.30.0` | 2026-08-01 | a soul you can describe, a glass you can find, and four faults that only show up in month six |
| v1.29.1 | `gritkeeper-v1.29.1` | 2026-07-30 | the download carries its own license, and a Linux build is planned |
| v1.29.0 | `gritkeeper-v1.29.0` | 2026-07-30 | what a Sign does, what a wound leaves, and a glass on the table |
| v1.26.0 | `gritkeeper-v1.26.0` | 2026-07-27 | an adventure, whole |
| v1.24.2 | `gritkeeper-v1.24.2` | 2026-07-27 | the fight runs itself |
| v1.20.1 | `gritkeeper-v1.20.1` | 2026-07-26 | — |
| v1.20.0 | `gritkeeper-v1.20.0` | 2026-07-26 | Blood & Grit — books v2.24/v2.11/v2.10 · GritKeeper v1.20.0 |
| v1.19.1 | `gritkeeper-v1.19.1` | 2026-07-26 | — |
| v1.19.0 | `gritkeeper-v1.19.0` | 2026-07-26 | — |
| v1.18.0 | `gritkeeper-v1.18.0` | 2026-07-26 | — |
| v1.17.0 | `gritkeeper-v1.17.0` | 2026-07-25 | — |
| v1.16.2 | `gritkeeper-v1.16.2` | 2026-07-25 | — |
| v1.11.0 | `gritkeeper-v1.11.0` | 2026-07-23 | — |
| v1.10.1 | `gritkeeper-v1.10.1` | 2026-07-22 | — |
| v1.8.0 | `gritkeeper-v1.8.0` | 2026-07-20 | — |
| v1.7.0 | `gritkeeper-v1.7.0` | 2026-07-20 | — |
| v1.6.0 | `gritkeeper-v1.6.0` | 2026-07-19 | — |
| v1.5.0 | `gritkeeper-v1.5.0` | 2026-07-19 | — |

## The three books

| Version | Tag | Shipped | What it was |
|---|---|---|---|
| v1.6 **← current** | `books-v1.6` | 2026-08-27 | Blood & Grit — Books v1.6 (Player's Book v2.33 — sixteen Origins, nineteen Callings, and a Perk on every one) |
| v1.5 | `books-v1.5` | 2026-08-23 | Blood & Grit — Books v1.5 (Player's Book v2.29, Keeper's Book v2.17 — the household method, and three options nothing could reach) |
| v1.4 | `books-v1.4` | 2026-08-22 | Blood & Grit — Books v1.4 (Keeper's Book v2.16, Bestiary v2.14 — the encounter budget repriced) |
| v1.3 | `books-v1.3` | 2026-08-21 | Blood & Grit — Books v1.3 (Bestiary v2.13, 175 creatures) |
| v1.2 | `books-v1.2` | 2026-08-20 | Blood & Grit — Books v1.2 (Player's Book v2.27) |
| v1.1 | `books-v1.1` | 2026-08-16 | Blood & Grit — Books v1.1 (Player's Book v2.26) |
| v1.0 | `books-v1.0` | 2026-08-10 | Blood & Grit - The Three Books (Player's v2.25, Keeper's v2.12, Bestiary v2.11) |

## The three modules

| Version | Tag | Shipped | What it was |
|---|---|---|---|
| v1.5 **← current** | `modules-v1.5` | 2026-08-27 | Blood & Grit — Modules v1.5 — the Contents and the Index are properly clickable |
| v1.4 | `modules-v1.4` | 2026-08-23 | Blood & Grit — Modules v1.4 — each adventure gets its turn |
| v1.3 | `modules-v1.3` | 2026-08-21 | Blood & Grit — Modules v1.3 — the three adventures in print, and the covers they should always have worn |
| v1.2 | `modules-v1.2` | 2026-08-17 | Blood & Grit Modules I-III v1.2 - What the Night Costs comes out of the engine |
| v1.1 | `modules-v1.1` | 2026-08-10 | Blood & Grit Modules I-III v1.1 - Module III is now What the Water Answers |
| v1.0 | `modules-v1.0` | 2026-08-10 | Blood & Grit Modules I-III v1.0 - three adventures, played before they were written |

---

*51 releases across 3 families, generated by `tools/release_index.py` from the GitHub API and from this file's own last version. Regenerate it whenever a version ships.*
