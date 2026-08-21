#!/usr/bin/env python3
"""verify_release.py — the app's version says the same thing everywhere, and a version that
claims to have shipped actually shipped.

WHY THIS EXISTS. On 2026-08-02 the Keeper launched GritKeeper and it was v1.31.0, two releases
behind what the repository said. Both halves of the failure were silent:

  * v1.32.0 was written, verified, merged to main and entered in the CHANGELOG as a shipped
    release — and was then never published, signed, packaged, tagged or released. Nothing
    anywhere noticed, because every check the project has looks at the SOURCE.
  * v1.33.0 was built and verified the same way the next day, and the delivered
    `GritKeeper/app/GritKeeper.exe` — the one the desktop shortcut actually runs — stayed on
    1.31.0 through all of it.

CI already catches the equivalent for the books: `git diff --exit-code -- '*.html'` fails when a
build script changes and the built HTML does not. The app had no such check, because its artifact
is a 163 MB signed binary that is deliberately git-ignored, so no diff can see it. This is that
missing check, split by what can be seen from where:

  DEFAULT (runs in CI, reads only what is in git)
    1. Every place that names the app's version agrees: the csproj, the newest CHANGELOG entry,
       README.md's "current editions" line, CLAUDE.md's two, and both app READMEs —
       `GK/source/README.md` and the delivered `GritKeeper/README.md`.

       The last two joined the list on 2026-08-08, after the delivered README — the one inside the
       zip, which is what a stranger reads first — was found claiming v1.10.1 against a v1.33.0
       app. Twenty-three releases, in the open, unnoticed: this script checked the root README and
       CLAUDE.md, and `update_readme.py` wrote only the root README, so that copy had neither a
       writer nor a reader. `update_readme.py` now writes all of them; this checks all of them.
    2. Every GritKeeper version in the CHANGELOG except the newest has a `gritkeeper-vX.Y.Z`
       tag. The newest is exempt because it is the one being worked on. This is the check that
       would have caught v1.32.0: the moment v1.33.0 became the newest entry, v1.32.0 stopped
       being exempt and had no tag.

  --delivered (local only)
    3. `GritKeeper/app/GritKeeper.exe` carries the csproj's version. This is the only check that
       looks at what the Keeper actually double-clicks. It cannot run in CI — the exe is not in
       git and takes a publish + sign + package to make.

    python verify_release.py              # report, exit 1 on any finding
    python verify_release.py --delivered  # also check the packaged exe
    python verify_release.py --quiet      # only findings
"""
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
VER = re.compile(r"(\d+\.\d+\.\d+)")

# Versions that appear in the CHANGELOG and will never have a tag, with the reason. A release
# that was skipped is a fact about the project's history, and recording it here is how this check
# stays honest instead of being switched off the first time it is inconvenient. Anything NOT on
# this list and not tagged is a finding.
UNSHIPPED = {
    "1.28.0": "merged 2026-07-29 and folded into the v1.29.0 release two days later; no separate "
              "build was ever published under this number",
    "1.32.0": "merged 2026-08-01 but never published, signed or packaged — the miss that this "
              "script exists to prevent. Its work reached the Keeper inside v1.33.0 the next day",
}


def read(name):
    return (ROOT / name).read_text(encoding="utf-8-sig")


def csproj_version():
    m = re.search(r"<Version>\s*([\d.]+)\s*</Version>", read("GK/source/BloodAndGritKeeper.csproj"))
    return m.group(1) if m else None


def changelog_versions():
    """Every GritKeeper version entered in the CHANGELOG, newest first, deduplicated.

    Matched on the entry's own heading shape — `- **GritKeeper v1.33.0 — title (date).**` — rather
    than on any mention of a version, so a sentence inside one entry referring back to an older
    release cannot be mistaken for that release having its own entry.
    """
    seen, out = set(), []
    for m in re.finditer(r"^- \*\*GritKeeper v(\d+\.\d+\.\d+)", read("CHANGELOG.md"), re.M):
        v = m.group(1)
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def tags():
    try:
        r = subprocess.run(["git", "tag", "--list", "gritkeeper-v*"],
                           cwd=ROOT, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None                      # no git here; the tag check reports itself as skipped
    return {line.strip()[len("gritkeeper-v"):] for line in r.stdout.splitlines() if line.strip()}


def delivered():
    """(version, build-commit, error) for the packaged exe, read via PowerShell — parsing a PE
    version resource by hand is a lot of code to avoid a tool that is present on the only OS this
    exe runs on.

    The commit comes free: .NET stamps `InformationalVersion` as `1.33.0+<full sha>`, which is the
    only way to tell one build of a version from another. A version number alone cannot — see the
    check below for what that misses.
    """
    exe = ROOT / "GritKeeper" / "app" / "GritKeeper.exe"
    if not exe.is_file():
        return None, None, f"no packaged exe at {exe.relative_to(ROOT)}"
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             f"$v=(Get-Item '{exe}').VersionInfo; $v.FileVersion + '|' + $v.ProductVersion"],
            capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, None, f"could not read the exe's version ({e})"
    out = (r.stdout or "").strip()
    m = VER.search(out)
    if not m:
        return None, None, f"no version in the exe ({out!r})"
    sha = re.search(r"\+([0-9a-f]{7,40})", out)
    return m.group(1), (sha.group(1) if sha else None), None


def app_changed_since(sha):
    """Which app sources have changed between the packaged build's commit and HEAD.

    Scoped to the two projects that COMPILE INTO the exe — `GK/source` (the WinForms UI) and
    `GK/rules` (the engine and its embedded `Data/*.json`). Not `GK/smoke`, which is the test rig
    and ships to nobody, and not `GK/CLAUDE.md`, which is a handoff document.

    The scoping is the whole point. Comparing the packaged commit against HEAD alone reports the
    package as stale after any commit at all — a CHANGELOG line, a note in this file — and a warning
    that fires when nothing is wrong is the warning people learn to scroll past, which is the same
    defect the commit-message gate had. It has to be quiet to be worth reading.
    """
    try:
        r = subprocess.run(["git", "diff", "--name-only", f"{sha}..HEAD",
                            "--", "GK/source/", "GK/rules/"],
                           cwd=ROOT, capture_output=True, text=True)
    except OSError:
        return None
    if r.returncode != 0:                # the packaged build predates this clone's history
        return None
    return [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]



# The three book versions, as the Python builders stamp them. Each builder splices its own cover
# onto the Player's shell by string-replacing the Player's version with its own, so the number on
# the RIGHT of each tuple is that book's own. build_player.py is the shell and carries its number
# on the left of nothing — it is read out of its own cover line.
BOOK_SITES = {
    "Player's Book":  ("build_player.py",   r"Edition of 1885 · Version (\d+\.\d+)</div>"),
    "Keeper's Book":  ("build_keeper.py",   r"The Keeper's Book · Version (\d+\.\d+) -->"),
    "Bestiary":       ("build_bestiary.py", r"The Bestiary · Version (\d+\.\d+) -->"),
}


def book_versions():
    """What each builder stamps on its own cover, or None where the wording has moved."""
    out = {}
    for book, (path, pat) in BOOK_SITES.items():
        m = re.search(pat, read(path))
        out[book] = m.group(1) if m else None
    return out


def app_book_versions():
    """The C#-side copy of the same three numbers, which shows in the status bar."""
    m = re.search(r'PlayerBookVer = "([\d.]+)", KeeperBookVer = "([\d.]+)", BestiaryVer = "([\d.]+)"',
                  read("GK/source/MainForm.cs"))
    return dict(zip(BOOK_SITES, m.groups())) if m else None


def main():
    quiet = "--quiet" in sys.argv
    check_delivered = "--delivered" in sys.argv
    findings = []

    src = csproj_version()
    if not src:
        print("no <Version> in GK/source/BloodAndGritKeeper.csproj")
        return 2

    # ---- 1. every place that names the version agrees with the csproj ----
    # The csproj is the single source of truth (see CLAUDE.md); everything else is a copy, and a
    # copy that drifts is how a release announces the wrong number.
    claims = [
        ("CHANGELOG.md  newest entry", (changelog_versions() or [None])[0]),
        ("README.md     current editions",
         next((m.group(1) for m in re.finditer(r"GritKeeper v(\d+\.\d+\.\d+)", read("README.md"))), None)),
        ("CLAUDE.md     current versions",
         next((m.group(1) for m in re.finditer(r"GritKeeper app v(\d+\.\d+\.\d+)", read("CLAUDE.md"))), None)),
        ("CLAUDE.md     app section heading",
         next((m.group(1) for m in re.finditer(r"## GritKeeper \(v(\d+\.\d+\.\d+)\)", read("CLAUDE.md"))), None)),
        ("GK/source/README.md  app version",
         next((m.group(1) for m in re.finditer(r"\*\*App version (\d+\.\d+\.\d+)", read("GK/source/README.md"))), None)),
        # The delivered copy. It is the only tracked file in an otherwise generated folder, which is
        # how it went twenty-three releases without anyone noticing.
        ("GritKeeper/README.md app version",
         next((m.group(1) for m in re.finditer(r"\*\*App version (\d+\.\d+\.\d+)", read("GritKeeper/README.md"))), None)),
    ]
    for where, claimed in claims:
        if claimed is None:
            findings.append(f"{where}: no GritKeeper version found — has the wording changed?")
        elif claimed != src:
            findings.append(f"{where}: says v{claimed}, the csproj says v{src}")

    # ---- 1b. the status bar names the books the app actually ships alongside ----
    # A second copy of a number the Python builders own. It drifted through GritKeeper v1.42.0
    # unnoticed because it is only ever READ at a glance, in a status bar, by somebody who has no
    # reason to doubt it. Read both sides and compare.
    stamped, in_app = book_versions(), app_book_versions()
    if in_app is None:
        findings.append("GK/source/MainForm.cs: the book-version constants are not where this "
                        "check looks — has the wording changed?")
    else:
        for book in BOOK_SITES:
            want, got = stamped[book], in_app[book]
            if want is None:
                findings.append(f"{BOOK_SITES[book][0]}: no cover version found for the {book} — "
                                f"has the cover wording changed?")
            elif want != got:
                findings.append(f"status bar: says {book} v{got}, {BOOK_SITES[book][0]} "
                                f"stamps v{want}")
            elif not quiet:
                print(f"  status bar   {book}: v{got}")

    # ---- 2. a version that has stopped being the newest must have been released ----
    versions, tagged = changelog_versions(), tags()
    if tagged is None:
        if not quiet:
            print("tag check skipped: git is not available here")
    else:
        for v in versions[1:]:                       # [0] is the one being worked on
            if v in tagged or v in UNSHIPPED:
                continue
            findings.append(
                f"CHANGELOG lists v{v} as shipped, but there is no gritkeeper-v{v} tag — that "
                f"release was never cut. Cut it, or record why it never shipped in UNSHIPPED "
                f"(verify_release.py).")

    # ---- 3. the exe the Keeper actually runs ----
    if check_delivered:
        got, built_at, why = delivered()
        repack = ("Run: dotnet publish -c Release (in GK/source) -> .\\sign.ps1 -> .\\package.ps1")
        if why:
            findings.append(f"delivered exe: {why}")
        elif got != src:
            findings.append(
                f"GritKeeper/app/GritKeeper.exe is v{got}, the source is v{src} — the app on this "
                f"machine is behind. {repack}")
        elif built_at:
            # Same version, different build. The version check alone cannot see this, and it missed
            # it live: the wizard's button weights were fixed and merged under v1.33.0 while the
            # packaged exe still held the build from the commit before, and the check said the app
            # matched the source because both said 1.33.0. A version identifies a release; only the
            # commit identifies a build.
            changed = app_changed_since(built_at)
            if changed:
                findings.append(
                    f"GritKeeper/app/GritKeeper.exe says v{got}, but it was built from "
                    f"{built_at[:9]} and {len(changed)} app source file(s) have changed since "
                    f"({', '.join(changed[:3])}{'…' if len(changed) > 3 else ''}). Same version, "
                    f"older build. {repack}")

    if not quiet:
        print(f"source version (csproj):  v{src}")
        for where, claimed in claims:
            print(f"  {where}: v{claimed}")
        if tagged is not None:
            missing = [v for v in versions[1:] if v not in tagged and v not in UNSHIPPED]
            print(f"  releases: {len(versions)} in the CHANGELOG, "
                  f"{len(versions) - 1 - len(missing)} of the {len(versions) - 1} past ones tagged "
                  f"({len(UNSHIPPED)} recorded as never shipped)")
        if check_delivered:
            got, built_at, why = delivered()
            print(f"  delivered GritKeeper/app/GritKeeper.exe: "
                  f"{why or 'v' + got + (f' built from {built_at[:9]}' if built_at else '')}")
        print()

    if findings:
        print(f"{len(findings)} finding(s):")
        for f in findings:
            print(f"  {f}")
        return 1

    # --quiet says nothing at all when there is nothing to say. It is what the pre-push hook uses,
    # and a hook that prints on every successful push is a hook people stop reading.
    if not quiet:
        print("the version says the same thing everywhere, and every past release was cut."
              + (" The packaged app matches the source." if check_delivered else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
