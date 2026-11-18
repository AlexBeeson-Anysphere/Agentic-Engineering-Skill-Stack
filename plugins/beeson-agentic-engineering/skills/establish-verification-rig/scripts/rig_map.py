#!/usr/bin/env python3
"""Resolve `agent-map/` verification plans for `.cursor/skills/run-verification-rig/`.

Ships inside `<repo>/.cursor/skills/run-verification-rig/scripts/rig_map.py` (and in
this skill's `scripts/rig_map.py`).

Modes:
  1. diff (default):
       rig_map.py [ROOT] --mode diff [--base REF] [--files FILE ...]
     Maps changed files in git (or `--files`) against each `agent-map/<feature>.md`'s
     tracked `Paths:`, pulls in prerequisite features (`Depends on features:`), and
     orders the verification plan in `agent-map/README.md` regression sweep order.

  2. feature:
       rig_map.py [ROOT] --mode feature <slug-or-file> [<slug-or-file> ...]
     Loads the target feature(s) and their prerequisites in regression sweep order,
     printing preconditions, `## Driving & verifying it` steps, `## Gotchas`, and
     the evidence directory to write artifacts into.

  3. sweep:
       rig_map.py [ROOT] --mode sweep
     Loads all features in `agent-map/README.md` top-to-bottom regression sweep order.

Stdlib only. Zero external dependencies.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys

MAP_DIR_NAME = "agent-map"
FEATURE_META_RE = re.compile(
    r"<!--\s*agent-map\s+v(\d+)\s*\|\s*Last linted:\s*(\S+)\s*\|\s*Paths:\s*(.+?)\s*-->"
)
README_FEATURE_LINK_RE = re.compile(r"\[([^\]]+)\]\(\./([a-z0-9-]+)\.md\)")
DEPENDS_LINK_RE = re.compile(r"\[[^\]]*\]\(\./([a-z0-9-]+)\.md\)")


def git(root, *args):
    try:
        out = subprocess.run(
            ["git", "-C", root, *args], capture_output=True, text=True, timeout=30
        )
        return out.stdout if out.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def git_toplevel(path):
    out = git(path, "rev-parse", "--show-toplevel")
    return out.strip() if out else None


def extract_section(text, heading):
    marker = f"\n{heading}\n"
    idx = text.find(marker)
    if idx == -1:
        if text.startswith(f"{heading}\n"):
            idx = 0
        else:
            return ""
    body = text[idx + len(marker):]
    next_h2 = body.find("\n## ")
    return body[:next_h2].strip() if next_h2 != -1 else body.strip()


def parse_readme_sweep_order(readme_text):
    sec = extract_section(readme_text, "## Features (regression sweep order)")
    order = []
    seen = set()
    for _, slug in README_FEATURE_LINK_RE.findall(sec or readme_text):
        if slug not in seen:
            seen.add(slug)
            order.append(slug)
    return order


def parse_feature_file(root, slug):
    rel_path = f"{MAP_DIR_NAME}/{slug}.md"
    abs_path = os.path.join(root, rel_path)
    if not os.path.isfile(abs_path):
        return None
    with open(abs_path, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    lines = txt.splitlines()
    title = lines[0].lstrip("# ").strip() if lines else slug
    head = "\n".join(lines[:6])
    m = FEATURE_META_RE.search(head)
    paths = [p.strip().rstrip("/") for p in m.group(3).split(",") if p.strip()] if m else []
    sha = m.group(2) if m else "unknown"

    reach_sec = extract_section(txt, "## How to reach it (user / caller POV)")
    driving_sec = extract_section(txt, "## Driving & verifying it")
    touch_sec = extract_section(txt, "## Code touchpoints & dependencies")
    gotchas_sec = extract_section(txt, "## Gotchas (what usually lies)")

    deps = []
    for line in touch_sec.splitlines():
        if "Depends on features" in line or "./" in line:
            for d_slug in DEPENDS_LINK_RE.findall(line):
                if d_slug != slug and d_slug not in deps:
                    deps.append(d_slug)

    return {
        "slug": slug,
        "file": rel_path,
        "title": title,
        "sha": sha,
        "paths": paths,
        "depends_on": deps,
        "how_to_reach": reach_sec,
        "driving_and_verifying": driving_sec,
        "gotchas": gotchas_sec,
    }


def load_all_features(root):
    map_dir = os.path.join(root, MAP_DIR_NAME)
    if not os.path.isdir(map_dir):
        return None, [], {}

    readme_path = os.path.join(map_dir, "README.md")
    readme_txt = ""
    if os.path.isfile(readme_path):
        with open(readme_path, encoding="utf-8", errors="replace") as fh:
            readme_txt = fh.read()

    sweep_order = parse_readme_sweep_order(readme_txt)
    features_by_slug = {}
    for entry in sorted(os.listdir(map_dir)):
        if not entry.endswith(".md") or entry == "README.md":
            continue
        slug = entry[:-3]
        f_obj = parse_feature_file(root, slug)
        if f_obj:
            features_by_slug[slug] = f_obj
            if slug not in sweep_order:
                sweep_order.append(slug)

    baseline_sec = extract_section(readme_txt, "## Baseline & verification harness")
    return baseline_sec, sweep_order, features_by_slug


def detect_changed_files(root, base_ref=None, explicit_files=None):
    if explicit_files:
        return sorted({f.strip().lstrip("./") for f in explicit_files if f.strip()})

    changed = set()
    if base_ref:
        out = git(root, "diff", "--name-only", base_ref, "--")
        if out:
            changed.update(l.strip() for l in out.splitlines() if l.strip())
    else:
        # Unstaged + staged + untracked
        for args in (
            ("diff", "--name-only", "HEAD", "--"),
            ("diff", "--name-only", "--cached", "--"),
            ("ls-files", "--others", "--exclude-standard"),
        ):
            out = git(root, *args)
            if out:
                changed.update(l.strip() for l in out.splitlines() if l.strip())
        # If working tree is clean, fall back to files changed in HEAD commit
        if not changed:
            out = git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD")
            if out:
                changed.update(l.strip() for l in out.splitlines() if l.strip())

    return sorted(
        f for f in changed
        if not f.startswith(".verification-evidence/")
    )


def file_matches_feature(rel_file, feat):
    if rel_file == feat["file"]:
        return True
    for tp in feat["paths"]:
        tp_norm = tp.rstrip("/")
        if rel_file == tp_norm or rel_file.startswith(tp_norm + "/"):
            return True
    return False


def expand_with_prerequisites(target_slugs, features_by_slug, sweep_order):
    needed = set(target_slugs)
    prereqs = set()
    queue = list(target_slugs)
    while queue:
        cur = queue.pop(0)
        f_obj = features_by_slug.get(cur)
        if not f_obj:
            continue
        for dep in f_obj["depends_on"]:
            if dep in features_by_slug and dep not in needed:
                needed.add(dep)
                prereqs.add(dep)
                queue.append(dep)

    ordered = [s for s in sweep_order if s in needed]
    for s in needed:
        if s not in ordered:
            ordered.append(s)
    return ordered, sorted(prereqs)


def build_plan(root, mode, base_ref, explicit_files, feature_args, run_id):
    baseline, sweep_order, features_by_slug = load_all_features(root)
    if features_by_slug is None:
        return {
            "ok": False,
            "error": f"`{MAP_DIR_NAME}/` does not exist at {root}. Run `/establish-feature-map` first.",
        }

    changed_files = []
    unmapped_changed_files = []
    direct_slugs = []

    if mode == "sweep":
        direct_slugs = list(sweep_order)
        ordered_slugs = list(sweep_order)
        prereq_slugs = []

    elif mode == "feature":
        for raw in feature_args or []:
            norm = os.path.basename(raw)
            if norm.endswith(".md"):
                norm = norm[:-3]
            if norm not in features_by_slug:
                return {
                    "ok": False,
                    "error": f"Feature `{raw}` not found in `{MAP_DIR_NAME}/`. Available: {', '.join(sweep_order)}",
                }
            if norm not in direct_slugs:
                direct_slugs.append(norm)
        ordered_slugs, prereq_slugs = expand_with_prerequisites(direct_slugs, features_by_slug, sweep_order)

    else:  # mode == "diff"
        changed_files = detect_changed_files(root, base_ref, explicit_files)
        for cf in changed_files:
            matched_any = False
            for slug in sweep_order:
                feat = features_by_slug[slug]
                if file_matches_feature(cf, feat):
                    matched_any = True
                    if slug not in direct_slugs:
                        direct_slugs.append(slug)
            if not matched_any and not cf.startswith((".cursor/", f"{MAP_DIR_NAME}/", "AGENTS.md", "CLAUDE.md")):
                unmapped_changed_files.append(cf)

        ordered_slugs, prereq_slugs = expand_with_prerequisites(direct_slugs, features_by_slug, sweep_order)

    evidence_root = f".verification-evidence/{run_id}"
    steps = []
    for idx, slug in enumerate(ordered_slugs, 1):
        feat = features_by_slug[slug]
        steps.append({
            "order": idx,
            "slug": slug,
            "file": feat["file"],
            "title": feat["title"],
            "role": "prerequisite" if slug in prereq_slugs else "target",
            "evidence_dir": f"{evidence_root}/{slug}",
            "how_to_reach": feat["how_to_reach"],
            "driving_and_verifying": feat["driving_and_verifying"],
            "gotchas": feat["gotchas"],
        })

    return {
        "ok": True,
        "root": root,
        "mode": mode,
        "run_id": run_id,
        "evidence_root": evidence_root,
        "baseline_harness": baseline,
        "changed_files": changed_files,
        "unmapped_changed_files": unmapped_changed_files,
        "target_features": direct_slugs,
        "prerequisite_features": prereq_slugs,
        "ordered_plan": steps,
    }


def print_human_plan(plan):
    if not plan.get("ok"):
        print(f"ERROR: {plan.get('error')}")
        sys.exit(1)

    print(f"=== VERIFICATION RIG PLAN (mode: {plan['mode']} | run_id: {plan['run_id']}) ===")
    print(f"Evidence root: {plan['evidence_root']}/")
    if plan["mode"] == "diff":
        print(f"Changed files ({len(plan['changed_files'])}): {', '.join(plan['changed_files'][:10]) or 'none'}")
        if plan["unmapped_changed_files"]:
            print(f"Unmapped changed files (shared/foundation — consider `--mode sweep` if cross-cutting): {', '.join(plan['unmapped_changed_files'][:8])}")

    if not plan["ordered_plan"]:
        print("\nNo mapped features matched the current diff. Pass `--mode feature <slug>` or `--mode sweep` to verify explicitly.")
        return

    print(f"\nFeatures to drive in regression order ({len(plan['ordered_plan'])}):")
    for step in plan["ordered_plan"]:
        tag = "PREREQ" if step["role"] == "prerequisite" else "TARGET"
        print(f"  {step['order']}. [{tag}] {step['slug']} ({step['file']}) -> evidence: {step['evidence_dir']}/")

    for step in plan["ordered_plan"]:
        print(f"\n--- [{step['order']}/{len(plan['ordered_plan'])}] {step['title']} ({step['file']}) ---")
        print(f"Role:         {step['role']}")
        print(f"Evidence dir: {step['evidence_dir']}/")
        print("\n[Driving & verifying it]")
        print(step["driving_and_verifying"] or "(missing section)")
        if step["gotchas"]:
            print("\n[Gotchas (what usually lies)]")
            print(step["gotchas"])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--mode", choices=["diff", "feature", "sweep"], default="diff")
    ap.add_argument("--base", help="git base ref for --mode diff (e.g. origin/main, HEAD~1)")
    ap.add_argument("--files", nargs="*", help="explicit changed file list for --mode diff")
    ap.add_argument("--run-id", help="explicit run ID (default: UTC timestamp)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("features", nargs="*", help="feature slug(s) when --mode feature")
    args = ap.parse_args()

    start = os.path.abspath(args.root)
    root = git_toplevel(start) or start
    run_id = args.run_id or datetime.datetime.now(datetime.timezone.utc).strftime("run-%Y%m%d-%H%M%S")

    plan = build_plan(root, args.mode, args.base, args.files, args.features, run_id)
    if args.json:
        json.dump(plan, sys.stdout, indent=2)
        print()
        if not plan.get("ok"):
            sys.exit(1)
    else:
        print_human_plan(plan)


if __name__ == "__main__":
    main()
