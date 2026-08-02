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
       README.md's "current editions" line, and CLAUDE.md's two.
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

ROOT = Path(__file__).resolve().parent
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


def delivered_version():
    """The FileVersion of the packaged exe, via PowerShell — reading a PE version resource by hand
    is a lot of code to avoid a tool that is present on the only OS this exe runs on."""
    exe = ROOT / "GritKeeper" / "app" / "GritKeeper.exe"
    if not exe.is_file():
        return None, f"no packaged exe at {exe.relative_to(ROOT)}"
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             f"(Get-Item '{exe}').VersionInfo.FileVersion"],
            capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, f"could not read the exe's version ({e})"
    m = VER.search(r.stdout or "")
    return (m.group(1), None) if m else (None, f"no version in the exe ({r.stdout.strip()!r})")


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
    ]
    for where, claimed in claims:
        if claimed is None:
            findings.append(f"{where}: no GritKeeper version found — has the wording changed?")
        elif claimed != src:
            findings.append(f"{where}: says v{claimed}, the csproj says v{src}")

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
        got, why = delivered_version()
        if why:
            findings.append(f"delivered exe: {why}")
        elif got != src:
            findings.append(
                f"GritKeeper/app/GritKeeper.exe is v{got}, the source is v{src} — the app on this "
                f"machine is behind. Run: dotnet publish -c Release (in GK/source) -> .\\sign.ps1 "
                f"-> .\\package.ps1")

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
            got, why = delivered_version()
            print(f"  delivered GritKeeper/app/GritKeeper.exe: {why or 'v' + got}")
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
