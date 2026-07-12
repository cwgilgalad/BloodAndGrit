# Blood & Grit — book sources

Three companion books share one HTML engine (cover + client-side paginator + print CSS).
Edit the lean sources, then run the build scripts. See `CLAUDE.md` for the full handoff doc
(version table, structure, verification standards, changelog).

## Build (Windows: real Python 3.12 + `pip install playwright` + Edge)

```bash
# Player's Book  → edit player-src.html, then:
python build_player.py                 # → blood-and-grit.html (self-contained shell)

# Keeper's Book  → edit build_keeper.py, then:
cp blood-and-grit.html keeper-handbook.html && python build_keeper.py

# Bestiary       → edit build_bestiary.py (and/or bestiary_extra.py), then:
cp blood-and-grit.html bestiary.html && python build_bestiary.py
```

## Verify (headless Edge)

```bash
python measure_index.py                 # Player's Book: parity/clip/anchors + re-patch index statics
python measure_book.py keeper-handbook.html
python measure_book.py bestiary.html
```

## What's what

- `player-src.html` — Player's Book lean source (edit this).
- `build_keeper.py` / `build_bestiary.py` / `bestiary_extra.py` — the other two books' content + builders.
- `nav_tools.py` — generates the detailed two-level Contents and the indexes for all three books.
- `perdition_map.py` — draws the Perdition Basin map (player + Keeper layers) as inline SVG;
  `python perdition_map.py both` writes `_map_preview.html`.
- `pag_patch.py` — shared paginator patch (splittable blocks).
- `assets/` — images (only the cover emblem `img20.png` is currently referenced).

**Version cascade:** bumping the Player's Book version means updating the hard-coded match
strings in `build_keeper.py` and `build_bestiary.py` too (do the Keeper/Bestiary own-version
replacements *before* the Player cascade so e.g. `v2.10` isn't corrupted). See `CLAUDE.md`.
