#!/usr/bin/env python3
"""audit_ui.py — the static wiring audit for GritKeeper's toolbars.

Reads GK/source/*.cs and checks every button the app builds through the shared helpers:

  * it has a handler (a Btn with a null handler is a button that does nothing when pressed —
    only MenuBtn is allowed one, since it wires its own drop-down),
  * it has a tooltip (the app's own convention; a bare label with no tip is the odd one out),
  * MenuBtn's items each carry a handler,
  * it is at least 24px on its narrow side (WCAG 2.5.8 Target Size (Minimum), AA — Microsoft's
    own Windows control guidance lands on ~23px, so 24 is the floor both agree on),
  * a destructive button is recoverable: it either confirms first or edits an undo-backed list.

Plus two checks on the things around the buttons:

  * every modal dialog answers Esc (it sets a CancelButton),
  * no two items in one menu claim the same Alt access key.

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

# helper -> (min args, handler arg index or None, tooltip arg index, width arg index)
# PrimaryBtn and DangerBtn are Btn with a different face (MainForm.cs) — same signature, and
# their CALL SITES deserve the same audit as any other button. They were missing here, so five
# of the tracker's buttons were never checked at all.
#   Btn/PrimaryBtn/DangerBtn/QuietBtn(text, onClick, w = 120, tip = null)
#   MenuBtn(text, w, tip, params (label, onClick)[] items)
#   ToggleBtn(text, w, tip)
#   DieBtn(text, sides, onClick, w, tip = null)
#
# QuietBtn and ToggleBtn joined in v1.33.0 with the three button weights, and the reason they are
# here is the reason PrimaryBtn and DangerBtn are: a helper the audit does not know about is a set
# of buttons nobody checks. The tell was the count — 131 down to 126 with only three buttons
# actually removed. ToggleBtn wires no handler of its own (its caller subscribes to CheckedChanged,
# which is the state changing rather than a press), so it is listed with MenuBtn's None.
HELPERS = {
    "Btn":        (2, 1, 3, 2),
    "PrimaryBtn": (2, 1, 3, 2),
    "DangerBtn":  (2, 1, 3, 2),
    "QuietBtn":   (2, 1, 3, 2),
    "MenuBtn":    (3, None, 2, 1),
    "ToggleBtn":  (3, None, 2, 1),
    "DieBtn":     (4, 2, 4, 3),
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


def dialogs(text):
    """Yield (line_no, var_name, body) for each locally-built Form that is shown MODALLY.

    The scope of one dialog is taken as everything from its `new Sheet` to the next one (or the
    end of the file), which is exact enough here: these are built, filled and shown inside a
    single method, one per method. A window that is never `ShowDialog`n is a pop-out (a
    creature card, a soul's Ledger, the tour's callout) and is deliberately not audited.

    `Sheet` is the app's own Form subclass — it carries the themed title bar (see Chrome.cs) and
    every window in the app is built from it. `Form` is still matched here on purpose: a plain
    Form is a window that slipped the theme, and it should keep being audited for its Esc route
    rather than quietly dropping out of the count the moment someone writes the wrong base.
    """
    marks = [(m.start(), m.group(1), text.count("\n", 0, m.start()) + 1)
             for m in re.finditer(r"(?:using\s+)?var\s+(\w+)\s*=\s*new\s+(?:Sheet|Form)\b", text)]
    for i, (pos, name, line) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        body = text[pos:end]
        if re.search(r"\b" + name + r"\.ShowDialog\b", body):
            yield line, name, body


def body_of(text, name):
    """The body of a method `name`, by brace matching. Used to follow a button's handler when it
    delegates (`(s, e) => NewFight()`) instead of doing the work inline."""
    m = re.search(r"\b(?:void|bool|int|string)\s+" + re.escape(name) + r"\s*\([^)]*\)\s*\{", text)
    if not m:
        return ""
    i, depth = m.end(), 1
    while i < len(text) and depth:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return text[m.end():i]


def mnemonics(label):
    """The access keys in a label: the letter after a single '&'. '&&' is a literal ampersand."""
    return [m.group(1).lower() for m in re.finditer(r"(?<!&)&([A-Za-z0-9])", label.replace("&&", ""))]


# The smallest a clickable target may be. WCAG 2.5.8 (Target Size, Minimum, AA) sets 24x24 CSS px
# and Microsoft's own Windows control guidance lands in the same place at ~23px, so 24 is the floor
# both agree on. Nothing in the app is under it today — the narrowest are the 34px dice-keypad keys
# — which makes this a REGRESSION guard rather than a backlog: it exists so the next cramped
# toolbar is caught while it is being written.
MIN_TARGET_PX = 24

# The six BindingLists wired to `ListChanged += CaptureUndo` in MainForm.cs. An edit to any of
# them lands on the Universal Undo stack without the caller doing anything, which is what makes
# a destructive button on one of them recoverable.
UNDO_BACKED = r"\b(party|tracker|signs|encounter|clocks|rides)\.(Clear|Remove|RemoveAt)\("


def main():
    quiet = "--quiet" in sys.argv
    if not SRC.is_dir():
        print(f"no source tree at {SRC}")
        return 2

    findings, counts, dlgcount = [], {}, 0
    sources = {}
    for path in sorted(SRC.glob("*.cs")):
        text = path.read_text(encoding="utf-8-sig")
        # the helpers' own definitions are declarations, not calls
        # ToggleBtn returns a CheckBox rather than a Button — it is a switch, not a press — so the
        # return type is matched loosely here. Pinning it to `Button` would have let ToggleBtn's own
        # definition be counted as a call site and reported for having no literal tooltip.
        text = re.sub(r"static\s+(?:Button|CheckBox)\s+"
                      r"(Btn|PrimaryBtn|DangerBtn|QuietBtn|MenuBtn|ToggleBtn|DieBtn)\(", r"DEF_\1(", text)
        sources[path.name] = text
    # One string for method-body lookups: a button's handler often delegates across files (a
    # Tracker button calling a method that lives in MainForm.cs), so following it has to be
    # tree-wide, not per file.
    alltext = "\n".join(sources.values())

    for name, text in sources.items():
        path = SRC / name
        for helper, (minargs, hidx, tidx, widx) in HELPERS.items():
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

                # ---- the target has to be big enough to hit ----
                if len(args) > widx and re.fullmatch(r"\d+", args[widx].strip()):
                    w = int(args[widx])
                    if w < MIN_TARGET_PX:
                        findings.append(f"{where}  {helper}({label}) — {w}px wide, under the "
                                        f"{MIN_TARGET_PX}px minimum target size")

                # ---- a destructive button has to be recoverable ----
                # The one class of button where a misfire can't be taken back by looking at it.
                # Two routes count, and only two: a Confirm() prompt, or an edit to one of the
                # six bound lists, which `ListChanged += CaptureUndo` puts on the Universal Undo
                # stack for free (MainForm.cs:229-234). An undoable action does NOT need a prompt
                # — putting one on every one of them is the surest way to train a Keeper to
                # dismiss prompts unread mid-fight, which is how the prompt that MATTERS gets
                # clicked through. A handler with neither route is the finding.
                if helper == "DangerBtn" and hidx < len(args):
                    reach = args[hidx]
                    for callee in re.findall(r"\b([A-Z]\w+)\s*\(", reach):
                        reach += body_of(alltext, callee)
                    if not (re.search(r"\bConfirm\(", reach) or re.search(UNDO_BACKED, reach)):
                        findings.append(f"{where}  DangerBtn({label}) — destructive, but the "
                                        "handler neither confirms nor touches an undo-backed list")

        # ---- modal dialogs must answer Esc ----
        # Windows-wide, Esc dismisses a dialog. Wiring AcceptButton and leaving CancelButton unset
        # compiles, looks finished, and produces a modal that ignores the one key everybody presses
        # first — which reads as a hung window rather than as a firm question. Four had drifted that
        # way by v1.28.0, two of them the Strike and Dread dialogs a Keeper opens most in a fight.
        # Where cancelling makes no sense, point CancelButton at the commit button: Esc should still
        # close the thing, and doing what the title-bar ✕ already does is honest.
        for line, name, body in dialogs(text):
            dlgcount += 1
            if not re.search(r"\b" + name + r"\.CancelButton\s*=", body):
                findings.append(f"{path.name}:{line}  the dialog built as `{name}` sets no "
                                "CancelButton — Esc does nothing in it")

    # ---- the menu bar's access keys have to be unique within their menu ----
    # Alt+F then S for Save. Two items in one drop-down claiming the same letter is neither a
    # compile error nor a crash: Windows quietly demotes the key from "jump and activate" to
    # "cycle between the matches", so a shortcut somebody learned stops working and nothing says
    # why. Uniqueness is only required WITHIN one menu — &Save under File and &Show me around
    # under Help never meet — so the check groups by the menu each item is added to, and the
    # top-level bar is a group of its own.
    menus = sources.get("Menus.cs", "")
    mnemcount = 0
    if menus:
        groups = {}

        def claim(owner, label, line):
            for key in mnemonics(label):
                groups.setdefault((owner, key), []).append((line, label))

        # An item built on one line and added by name on another: `var glass = new
        # ToolStripMenuItem("The turn &glass")`, and `undoMenuItem = Item("&Undo", …)`. Both
        # forms, or Alt+U and Alt+R under Edit go unchecked.
        named = {m.group(1): m.group(2) for m in re.finditer(
            r'(?:var\s+)?(\w+)\s*=\s*(?:new\s+ToolStripMenuItem|Item)\(\s*"([^"]*)"', menus)}

        # A local function that adds to one menu — `void ModeItem(string text, RunMode m)` puts
        # its argument under Table. Its call sites carry the labels, so resolve the function to
        # the menu it feeds and credit each call to that menu.
        adders = {}
        for m in re.finditer(r"\bvoid\s+(\w+)\s*\([^)]*\)", menus):
            owner = re.search(r"(\w+)\.DropDownItems\.Add\(", body_of(menus, m.group(1)))
            if owner:
                adders[m.group(1)] = owner.group(1)

        for m in re.finditer(r"(\w+)\.DropDownItems\.Add\((.*)", menus):
            owner, arg = m.group(1), m.group(2)
            lit = re.search(r'"([^"]*)"', arg)
            if lit:
                label = lit.group(1)
            else:
                ident = re.match(r"\s*(\w+)\s*\)", arg)
                if not ident or ident.group(1) not in named:
                    continue          # built from data (the View menu names its items off the tabs)
                label = named[ident.group(1)]
            claim(owner, label, menus.count("\n", 0, m.start()) + 1)

        for func, owner in adders.items():
            for m in re.finditer(r"\b" + func + r'\(\s*"([^"]*)"', menus):
                claim(owner, m.group(1), menus.count("\n", 0, m.start()) + 1)

        for ident, label in named.items():
            if re.search(r"\bmenu\.Items\.Add\(\s*" + ident + r"\s*\)", menus):
                claim("the menu bar", label, 0)

        mnemcount = sum(len(v) for v in groups.values())
        for (owner, key), hits in sorted(groups.items()):
            if len(hits) > 1:
                which = ", ".join(f"{lbl!r}" + (f" (line {ln})" if ln else "") for ln, lbl in hits)
                findings.append(f"Menus.cs  {owner}: Alt+{key.upper()} is claimed by "
                                f"{len(hits)} items — {which}")

    if not quiet:
        print("buttons per file")
        for name in sorted(counts):
            print(f"  {name:<18} {counts[name]}")
        print(f"  {'TOTAL':<18} {sum(counts.values())}")
        print(f"\nmodal dialogs checked for an Esc route: {dlgcount}")
        print(f"menu access keys checked for collisions:  {mnemcount}")
        print()

    if findings:
        print(f"{len(findings)} finding(s):")
        for f in findings:
            print("  " + f)
        return 1
    print("every button has a handler, a tooltip and a hittable target; every destructive button\n"
          "is recoverable; every modal dialog answers Esc; no two menu items share an access key.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
