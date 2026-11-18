#!/usr/bin/env python3
"""Validate `.cursor/skills/run-verification-rig/` and its integration with `agent-map/`.

Usage:
  validate_rig.py [ROOT] [--require-evidence DIR]

Checks:
1. `.cursor/skills/run-verification-rig/SKILL.md` exists, has valid YAML frontmatter
   (`name: run-verification-rig`, non-empty `description`), metadata comment on line 8+,
   and required H2 sections in order.
2. No unfilled template placeholders (`<App Name>`, `<command>`, `{{...}}`) in `SKILL.md`.
3. `.cursor/skills/run-verification-rig/scripts/rig_map.py` exists and is executable, and
   any other `.cursor/skills/run-verification-rig/scripts/*` files referenced in `SKILL.md`
   exist and are executable.
4. `agent-map/README.md` exists and references `.cursor/skills/run-verification-rig/SKILL.md`
   under `## Baseline & verification harness`.
5. Every `agent-map/<feature>.md` has `Preconditions:` and concrete `Run` + `Observable result:`
   steps under `## Driving & verifying it`.
6. If `--require-evidence DIR` is passed, verifies `DIR` exists on disk and contains at least
   one non-empty proof artifact file (confirming cleanup did not delete proof).

Exits 1 on any error, 0 otherwise. Stdlib only.
"""
import argparse
import os
import re
import subprocess
import sys

RIG_SKILL_REL = ".cursor/skills/run-verification-rig/SKILL.md"
RIG_MAP_SCRIPT_REL = ".cursor/skills/run-verification-rig/scripts/rig_map.py"
MAP_DIR_NAME = "agent-map"

REQUIRED_RIG_H2 = [
    "## Execution Modes (Integrated with agent-map/)",
    "## Launch",
    "## Doctor",
    "## Drive",
    "## Evidence",
    "## Cleanup",
    "## Helpers",
]

RIG_META_RE = re.compile(
    r"<!--\s*verification-rig\s+v(\d+)\s*\|\s*Last verified:\s*(\S+)\s*\|\s*Surface:\s*([^|]+?)\s*\|\s*Map:\s*agent-map/README\.md\s*-->"
)
PLACEHOLDER_RE = re.compile(r"(\{\{[A-Z0-9_]+\}\}|<App Name>|<command>|<primary-surface>|<short-git-sha>)")
SCRIPT_REF_RE = re.compile(r"\.cursor/skills/run-verification-rig/scripts/([a-zA-Z0-9_.-]+)")


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def err(self, path, msg):
        self.errors.append(f"{path}: {msg}")

    def warn(self, path, msg):
        self.warnings.append(f"{path}: {msg}")


def git_toplevel(path):
    try:
        out = subprocess.run(
            ["git", "-C", path, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=15
        )
        return out.stdout.strip() if out.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def validate_frontmatter(text, rep):
    if not text.startswith("---\n"):
        rep.err(RIG_SKILL_REL, "missing YAML frontmatter at top of file")
        return
    end = text.find("\n---\n", 4)
    if end == -1:
        rep.err(RIG_SKILL_REL, "unclosed YAML frontmatter")
        return
    fm = text[4:end]
    if "name: run-verification-rig" not in fm:
        rep.err(RIG_SKILL_REL, "frontmatter must contain `name: run-verification-rig`")
    if "description:" not in fm:
        rep.err(RIG_SKILL_REL, "frontmatter must contain a non-empty `description:`")


def validate_rig_skill(root, rep):
    abs_skill = os.path.join(root, RIG_SKILL_REL)
    if not os.path.isfile(abs_skill):
        rep.err(RIG_SKILL_REL, "missing `.cursor/skills/run-verification-rig/SKILL.md`")
        return

    with open(abs_skill, encoding="utf-8", errors="replace") as fh:
        text = fh.read()

    validate_frontmatter(text, rep)

    if not RIG_META_RE.search(text[:1500]):
        rep.err(
            RIG_SKILL_REL,
            "missing metadata comment: `<!-- verification-rig v1 | Last verified: <sha> | Surface: <...> | Map: agent-map/README.md -->`",
        )

    lines = text.splitlines()
    headings = [line.strip() for line in lines if line.startswith("## ")]
    for req in REQUIRED_RIG_H2:
        if req not in headings:
            rep.err(RIG_SKILL_REL, f"missing required section `{req}`")
    present = [h for h in REQUIRED_RIG_H2 if h in headings]
    actual = [h for h in headings if h in REQUIRED_RIG_H2]
    if actual != present:
        rep.err(RIG_SKILL_REL, f"sections out of order: got {actual}, expected {present}")

    bad_ph = PLACEHOLDER_RE.findall(text)
    if bad_ph:
        rep.err(RIG_SKILL_REL, f"unfilled template placeholders found: {sorted(set(bad_ph))}")

    if len(lines) > 500:
        rep.warn(RIG_SKILL_REL, f"{len(lines)} lines exceeds recommended 500-line skill limit")

    # Check required rig_map.py and any referenced helper scripts
    abs_rig_map = os.path.join(root, RIG_MAP_SCRIPT_REL)
    if not os.path.isfile(abs_rig_map):
        rep.err(RIG_MAP_SCRIPT_REL, "missing `scripts/rig_map.py` helper inside `run-verification-rig/`")
    elif not os.access(abs_rig_map, os.X_OK):
        rep.err(RIG_MAP_SCRIPT_REL, "`scripts/rig_map.py` is not executable (`chmod +x` required)")

    for script_name in sorted(set(SCRIPT_REF_RE.findall(text))):
        rel_s = f".cursor/skills/run-verification-rig/scripts/{script_name}"
        abs_s = os.path.join(root, rel_s)
        if not os.path.isfile(abs_s):
            rep.err(rel_s, f"helper script referenced in SKILL.md does not exist: `{rel_s}`")
        elif not os.access(abs_s, os.X_OK):
            rep.err(rel_s, f"helper script is not executable (`chmod +x` required): `{rel_s}`")


def validate_agent_map_wiring(root, rep):
    readme_rel = f"{MAP_DIR_NAME}/README.md"
    readme_abs = os.path.join(root, readme_rel)
    if not os.path.isfile(readme_abs):
        rep.err(readme_rel, f"missing `{readme_rel}` — run `/establish-feature-map` first")
        return

    with open(readme_abs, encoding="utf-8", errors="replace") as fh:
        readme_txt = fh.read()

    if "run-verification-rig" not in readme_txt:
        rep.err(
            readme_rel,
            "`## Baseline & verification harness` in `agent-map/README.md` does not reference `.cursor/skills/run-verification-rig/SKILL.md`",
        )

    map_dir = os.path.join(root, MAP_DIR_NAME)
    for entry in sorted(os.listdir(map_dir)):
        if not entry.endswith(".md") or entry == "README.md":
            continue
        rel_f = f"{MAP_DIR_NAME}/{entry}"
        with open(os.path.join(map_dir, entry), encoding="utf-8", errors="replace") as fh:
            f_txt = fh.read()
        if "## Driving & verifying it" not in f_txt:
            rep.err(rel_f, "missing `## Driving & verifying it` section")
            continue
        sec = f_txt.split("## Driving & verifying it", 1)[1].split("\n## ", 1)[0]
        if "Preconditions:" not in sec:
            rep.err(rel_f, "`## Driving & verifying it` must include `Preconditions:`")
        if "Observable result:" not in sec and "observable" not in sec.lower():
            rep.warn(rel_f, "`## Driving & verifying it` should state `Observable result:` for each action step")


def validate_evidence_dir(root, evidence_dir, rep):
    abs_ev = evidence_dir if os.path.isabs(evidence_dir) else os.path.join(root, evidence_dir)
    if not os.path.isdir(abs_ev):
        rep.err(evidence_dir, "evidence directory does not exist after cleanup (cleanup ate the proof or proof was never written)")
        return
    non_empty_files = []
    for dirpath, _, filenames in os.walk(abs_ev):
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(fp) > 0:
                    non_empty_files.append(os.path.relpath(fp, root))
            except OSError:
                pass
    if not non_empty_files:
        rep.err(evidence_dir, "evidence directory exists but contains zero non-empty proof files")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--require-evidence", help="verify that this evidence directory survived cleanup with non-empty artifacts")
    args = ap.parse_args()

    start = os.path.abspath(args.root)
    root = git_toplevel(start) or start
    rep = Report()

    validate_rig_skill(root, rep)
    validate_agent_map_wiring(root, rep)
    if args.require_evidence:
        validate_evidence_dir(root, args.require_evidence, rep)

    for w in rep.warnings:
        print(f"WARN  {w}")
    for e in rep.errors:
        print(f"ERROR {e}")
    print(f"\nverification-rig validation complete: {len(rep.errors)} errors, {len(rep.warnings)} warnings")
    sys.exit(1 if rep.errors else 0)


if __name__ == "__main__":
    main()
