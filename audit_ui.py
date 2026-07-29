#!/usr/bin/env python3
"""audit_ui.py — the static wiring audit for GritKeeper's toolbars.

Reads GK/source/*.cs and checks every button the app builds through the shared helpers:

  * it has a handler (a Btn with a null handler is a button that does nothing when pressed —
    only MenuBtn is allowed one, since it wires its own drop-down),
  * it has a tooltip (the app's own convention; a bare label with no tip is the odd one out),
  * MenuBtn's items each carry a handler.

It also reports the button count per file, so a tab that has quietly grown a second toolbar
is visible. This is the cheap check the project has leaned on before — it has caught orphaned
controls that compile fine and do nothing.

    python audit_ui.py            # report, exit 1 on any finding
    python audit_ui.py --quiet    # only findings
"""
import re
import sys
from pathlib import Path

# the app's labels carry ▾, ✥, —; a cp1252 console would die on them
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = Path(__file__).resolve().parent / "GK" / "source"

# helper -> (min args, index of the handler arg or None, index of the tooltip arg)
# PrimaryBtn and DangerBtn are Btn with a different face (MainForm.cs) — same signature, and
# their CALL SITES deserve the same audit as any other button. They were missing here, so five
# of the tracker's buttons were never checked at all.
HELPERS = {
    "Btn":        (2, 1, 3),
    "PrimaryBtn": (2, 1, 3),
    "DangerBtn":  (2, 1, 3),
    "MenuBtn":    (3, None, 2),
    "DieBtn":     (4, 2, 4),
}

# The parameter names the wrappers forward under. A call whose arguments ARE these names is one
# helper handing off to another inside its own definition, not a button on a bar — it has no
# literal tooltip because it is passing along whatever its caller gave it. Reported as two
# findings for two releases (MainForm.cs:672 and :688, PrimaryBtn and DangerBtn calling Btn),
# which is exactly how a cheap audit teaches people to ignore it.
FORWARDED = {"text", "onClick", "w", "tip"}


def split_args(text):
    """Split a call's argument text on top-level commas, respecting nesting and literals."""
    args, depth, buf = [], 0, []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in '"\'':
            quote, buf2 = c, [c]
            i += 1
            while i < n:
                if text[i] == "\\":
                    buf2.append(text[i:i + 2]); i += 2; continue
                buf2.append(text[i])
                if text[i] == quote:
                    i += 1; break
                i += 1
            buf.append("".join(buf2))
            continue
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        if c == "," and depth == 0:
            args.append("".join(buf).strip()); buf = []
        else:
            buf.append(c)
        i += 1
    if "".join(buf).strip():
        args.append("".join(buf).strip())
    return args


def calls(src, helper):
    """Yield (line_no, arg_list) for each call to a helper in one file's text."""
    for m in re.finditer(r"(?<![A-Za-z0-9_])" + helper + r"\(", src):
        start = m.end()
        depth, i, n = 1, start, len(src)
        while i < n and depth:
            c = src[i]
            if c in '"\'':
                quote = c
                i += 1
                while i < n:
                    if src[i] == "\\":
                        i += 2; continue
                    if src[i] == quote:
                        i += 1; break
                    i += 1
                continue
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            i += 1
        yield src.count("\n", 0, m.start()) + 1, split_args(src[start:i - 1])


def main():
    quiet = "--quiet" in sys.argv
    if not SRC.is_dir():
        print(f"no source tree at {SRC}")
        return 2

    findings, counts = [], {}
    for path in sorted(SRC.glob("*.cs")):
        text = path.read_text(encoding="utf-8-sig")
        # the helpers' own definitions are declarations, not calls
        text = re.sub(r"static\s+Button\s+(Btn|PrimaryBtn|DangerBtn|MenuBtn|DieBtn)\(", r"DEF_\1(", text)
        for helper, (minargs, hidx, tidx) in HELPERS.items():
            for line, args in calls(text, helper):
                counts[path.name] = counts.get(path.name, 0) + 1
                where = f"{path.name}:{line}"
                label = args[0] if args else "?"
                # One helper handing off to another inside its own definition: MenuBtn builds its
                # face with Btn(text, null, w, tip) and wires the drop-down itself; PrimaryBtn and
                # DangerBtn call Btn(text, onClick, w, tip) and then re-paint it. Every argument is
                # a forwarded parameter name, so there is no literal here to check and no button
                # here to count.
                if helper == "Btn" and len(args) > 3 and all(a in FORWARDED or a == "null" for a in args):
                    counts[path.name] -= 1
                    continue
                if len(args) < minargs:
                    findings.append(f"{where}  {helper}({label}) — only {len(args)} argument(s)")
                    continue
                if hidx is not None and args[hidx].strip() == "null":
                    findings.append(f"{where}  {helper}({label}) — no handler: pressing it does nothing")
                if len(args) <= tidx or not args[tidx].lstrip().startswith(('"', '$"')):
                    findings.append(f"{where}  {helper}({label}) — no tooltip")
                if helper == "MenuBtn":
                    for item in args[3:]:
                        if item.lstrip().startswith('("-"'):
                            continue                     # a separator, which carries no handler by design
                        # A group heading, written "— Mounts —" / "— The whole posse —". MenuBtn
                        # renders a null handler as a DISABLED item, so these can't read as a dead
                        # button; only a heading may take the exemption, and it must look like one.
                        if re.match(r'\(\s*"—[^"]*—"', item.lstrip()):
                            continue
                        if re.search(r",\s*null\s*\)\s*$", item):
                            findings.append(f"{where}  MenuBtn({label}) — a menu item with no handler")

    if not quiet:
        print("buttons per file")
        for name in sorted(counts):
            print(f"  {name:<18} {counts[name]}")
        print(f"  {'TOTAL':<18} {sum(counts.values())}")
        print()

    if findings:
        print(f"{len(findings)} finding(s):")
        for f in findings:
            print("  " + f)
        return 1
    print("every button has a handler and a tooltip.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
