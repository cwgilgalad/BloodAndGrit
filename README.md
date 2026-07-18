# Blood & Grit — book sources

Three companion books share one HTML engine (cover + client-side paginator + print CSS).
**Each book is one builder script that carries its own content** — edit the builder, run it.
See `CLAUDE.md` for the full handoff doc (version table, structure, verification standards,
changelog).

## Build (Windows: real Python 3.12 + `pip install playwright` + Edge)

```bash
# Player's Book  → edit the SRC string in build_player.py, then:
python build_player.py                 # → blood-and-grit.html (the shared shell — build this first)

# Keeper's Book  → edit build_keeper.py, then:
python build_keeper.py                 # reads blood-and-grit.html → keeper-handbook.html

# Bestiary       → edit build_bestiary.py (creatures included), then:
python build_bestiary.py               # reads blood-and-grit.html → bestiary.html
```

## Verify (headless Edge)

```bash
python measure_index.py                 # Player's Book: parity/clip/anchors + re-patch index statics
python measure_book.py keeper-handbook.html
python measure_book.py bestiary.html
```

## What's what

- `build_player.py` — Player's Book: the full book HTML lives in its `SRC` string (edit there),
  plus the asset-inlining build. `measure_index.py` patches index statics into `SRC` directly.
- `build_keeper.py` — Keeper's Book content + builder.
- `build_bestiary.py` — Bestiary content + builder, including the 25 ordinary beasts, the
  tier/name sorter, and the generated Roll-by-Tier appendix (formerly `bestiary_extra.py`).
  To add a creature, edit this one file.
- `nav_tools.py` — generates the detailed two-level Contents and the indexes for all three books.
- `perdition_map.py` — draws the Perdition Basin map (player + Keeper layers) as inline SVG;
  `python perdition_map.py both` writes `_map_preview.html`.
- `pag_patch.py` — shared paginator patch (splittable blocks).
- `assets/` — images (only the cover emblem `img20.png` is currently referenced).

**Version cascade:** bumping the Player's Book version means updating the hard-coded match
strings in `build_keeper.py` and `build_bestiary.py` too (do the Keeper/Bestiary own-version
replacements *before* the Player cascade so e.g. `v2.10` isn't corrupted). See `CLAUDE.md`.
