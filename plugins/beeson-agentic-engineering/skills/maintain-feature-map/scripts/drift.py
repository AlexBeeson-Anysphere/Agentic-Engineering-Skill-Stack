#!/usr/bin/env python3
"""Analyze drift, coverage gaps, and staleness across `agent-map/`.

Usage:
  drift.py [ROOT] [--summary | --json] [--since-commits 30]

Reports for each `agent-map/<feature>.md`:
- status: FRESH | STALE | BROKEN_PATHS | INVALID_META
- changed files under its tracked `Paths:` since `Last linted: <sha>`
- missing paths (renamed or deleted in repo)
- preserved `## Notes` content

Also reports:
- unmapped active source paths (files changed in recent commits or working tree that
  do not fall under any feature file's `Paths:`)
- orphan or unindexed feature files in `agent-map/`

Exits 0 (informational report for maintain-feature-map). Stdlib only.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mapcommon import (  # noqa: E402
    FIXTURE_DIRS, GENERATED_DIRS, MAP_DIR_NAME, SOURCE_EXTS,
    changed_files_since, extract_notes_section, git, git_short_sha,
    git_toplevel, is_ignored_path, list_files, parse_feature_meta,
    parse_readme_meta,
)


def path_matches_any(file_path, tracked_paths):
    for tp in tracked_paths:
        tp_norm = tp.rstrip("/")
        if file_path == tp_norm or file_path.startswith(tp_norm + "/"):
            return True
    return False


def recent_changed_source_files(root, since_commits):
    """Return source files changed in the last N commits or working tree."""
    out = git(root, "log", f"-n{since_commits}", "--name-only", "--pretty=format:")
    candidates = set()
    if out:
        for line in out.splitlines():
            p = line.strip()
            if p:
                candidates.add(p)
    wt = git(root, "status", "--porcelain")
    if wt:
        for line in wt.splitlines():
            if len(line) > 3:
                p = line[3:].strip().split(" -> ")[-1]
                candidates.add(p)
    result = []
    for p in sorted(candidates):
        if p.startswith(f"{MAP_DIR_NAME}/") or p.startswith(".cursor/") or p.startswith(".github/"):
            continue
        if is_ignored_path(p):
            continue
        parts = p.split("/")
        if any(part in GENERATED_DIRS | FIXTURE_DIRS for part in parts):
            continue
        ext = os.path.splitext(p)[1].lower()
        if ext in SOURCE_EXTS and os.path.isfile(os.path.join(root, p)):
            result.append(p)
    return result


def analyze(root, since_commits):
    head_sha = git_short_sha(root)
    map_dir = os.path.join(root, MAP_DIR_NAME)
    if not os.path.isdir(map_dir):
        return {
            "root": root,
            "head_sha": head_sha,
            "exists": False,
            "error": f"`{MAP_DIR_NAME}/` directory does not exist. Run establish-feature-map first.",
        }

    entries = sorted(
        e for e in os.listdir(map_dir)
        if e.endswith(".md") and os.path.isfile(os.path.join(map_dir, e))
    )
    readme_info = {"exists": "README.md" in entries, "meta": None}
    if readme_info["exists"]:
        with open(os.path.join(map_dir, "README.md"), encoding="utf-8", errors="replace") as fh:
            readme_info["meta"] = parse_readme_meta(fh.read())

    features = []
    all_tracked_paths = []

    for e in entries:
        if e == "README.md":
            continue
        rel = f"{MAP_DIR_NAME}/{e}"
        with open(os.path.join(map_dir, e), encoding="utf-8", errors="replace") as fh:
            txt = fh.read()
        meta = parse_feature_meta(txt)
        notes = extract_notes_section(txt)
        if not meta:
            features.append({
                "file": rel,
                "status": "INVALID_META",
                "sha": None,
                "paths": [],
                "missing_paths": [],
                "changed_files": [],
                "has_notes": bool(notes),
            })
            continue

        paths = meta["paths"]
        all_tracked_paths.extend(paths)
        missing = [p for p in paths if not os.path.exists(os.path.join(root, p))]
        existing = [p for p in paths if p not in missing]
        changed = changed_files_since(root, meta["sha"], existing) if existing else []

        if missing:
            status = "BROKEN_PATHS"
        elif changed is None and meta["sha"] != "nogit":
            status = "UNKNOWN_SHA"
            changed = []
        elif changed:
            status = "STALE"
        else:
            status = "FRESH"

        features.append({
            "file": rel,
            "status": status,
            "sha": meta["sha"],
            "paths": paths,
            "missing_paths": missing,
            "changed_files": changed or [],
            "has_notes": bool(notes),
        })

    recent_src = recent_changed_source_files(root, since_commits)
    unmapped_recent = [
        f for f in recent_src
        if not path_matches_any(f, all_tracked_paths)
        and "/" in f  # skip root config files like package.json/tsconfig.json
    ]

    # Group unmapped recent files by their parent directory
    unmapped_dirs = {}
    for f in unmapped_recent:
        bucket = os.path.dirname(f) or "."
        unmapped_dirs.setdefault(bucket, []).append(f)

    counts = {}
    for feat in features:
        counts[feat["status"]] = counts.get(feat["status"], 0) + 1

    return {
        "root": root,
        "head_sha": head_sha,
        "exists": True,
        "readme": readme_info,
        "status_counts": counts,
        "features": features,
        "unmapped_recent_dirs": unmapped_dirs,
        "all_files_count": len(list_files(root)),
    }


def print_summary(rep):
    if not rep.get("exists"):
        print(f"ERROR: {rep.get('error')}")
        return
    print(f"root:     {rep['root']}")
    print(f"head sha: {rep['head_sha']}")
    r_meta = rep["readme"]["meta"]
    print(f"README:   exists={rep['readme']['exists']}  last_linted={r_meta['sha'] if r_meta else 'missing'}")
    print(f"counts:   {rep['status_counts']}")
    print("\nfeature files:")
    print(f"  {'STATUS':14} {'LAST_SHA':10} {'FILE':38} DETAILS")
    for f in rep["features"]:
        details = []
        if f["missing_paths"]:
            details.append(f"missing={f['missing_paths']}")
        if f["changed_files"]:
            sample = ", ".join(f["changed_files"][:3])
            more = f" (+{len(f['changed_files']) - 3})" if len(f["changed_files"]) > 3 else ""
            details.append(f"{len(f['changed_files'])} changed: {sample}{more}")
        if not details and f["status"] == "FRESH":
            details.append(f"tracks {len(f['paths'])} path(s)")
        print(f"  {f['status']:14} {(f['sha'] or '-'):10} {f['file']:38} {'; '.join(details)}")

    if rep["unmapped_recent_dirs"]:
        print("\nunmapped directories with recent code churn (check if new feature or missing `Paths:` entry):")
        for d, flist in sorted(rep["unmapped_recent_dirs"].items()):
            print(f"  {d:42} ({len(flist)} file(s): {', '.join(flist[:3])})")
    else:
        print("\nunmapped recent code churn: none")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--since-commits", type=int, default=30)
    args = ap.parse_args()

    start = os.path.abspath(args.root)
    root = git_toplevel(start) or start
    rep = analyze(root, args.since_commits)

    if args.summary or not args.json:
        print_summary(rep)
    if args.json:
        json.dump(rep, sys.stdout, indent=2)
        print()


if __name__ == "__main__":
    main()
