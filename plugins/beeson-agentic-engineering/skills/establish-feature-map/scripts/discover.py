#!/usr/bin/env python3
"""Discover repository structure, stack boundaries, verification harnesses, and candidate feature surfaces.

Usage:
  discover.py [ROOT] [--summary | --json]

Stdlib only. Used by establish-feature-map to plan the initial `agent-map/` layout.
"""
import argparse
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mapcommon import (  # noqa: E402
    BLOCK_START, FIXTURE_DIRS, GENERATED_DIRS, MAP_DIR_NAME, MONOREPO_MARKERS,
    SOURCE_EXTS, SURFACE_DIR_HINTS, extract_notes_section, git_short_sha,
    git_toplevel, list_files, manifest_label, parse_feature_meta,
)


def scan_repo(root, files):
    stacks = defaultdict(list)
    languages = defaultdict(int)
    dir_source_counts = defaultdict(int)
    dir_Subdirs = defaultdict(set)
    surface_dirs = []
    verify_skills = []
    agent_files = []
    legacy_scattered_maps = []

    for f in files:
        parts = f.split("/")
        name = parts[-1]
        ext = os.path.splitext(name)[1].lower()
        rel_dir = "/".join(parts[:-1]) or "."

        if ext in SOURCE_EXTS:
            languages[ext] += 1
            for i in range(len(parts)):
                anc = "/".join(parts[:i]) or "."
                dir_source_counts[anc] += 1
                if i < len(parts) - 1:
                    dir_Subdirs[anc].add("/".join(parts[:i + 1]))

        label = manifest_label(name)
        if label:
            stacks[label].append(rel_dir)

        if f.startswith(".cursor/skills/verify-") and name == "SKILL.md":
            verify_skills.append(rel_dir)

        if name in ("AGENTS.md", "CLAUDE.md"):
            has_block = False
            try:
                with open(os.path.join(root, f), encoding="utf-8", errors="replace") as fh:
                    has_block = BLOCK_START in fh.read()
            except OSError:
                pass
            agent_files.append({"path": f, "has_block": has_block})

        if name == "MAP.md" and not f.startswith(f"{MAP_DIR_NAME}/"):
            legacy_scattered_maps.append(f)

    # Identify candidate feature/surface directories
    for d, src_count in sorted(dir_source_counts.items()):
        if d == "." or d.startswith(f"{MAP_DIR_NAME}") or d.startswith(".cursor"):
            continue
        parts = d.split("/")
        if any(p in GENERATED_DIRS | FIXTURE_DIRS for p in parts):
            continue
        leaf = parts[-1].lower()
        parent_leaf = parts[-2].lower() if len(parts) >= 2 else ""
        subdirs = sorted(dir_Subdirs[d])

        if leaf in SURFACE_DIR_HINTS and (len(subdirs) >= 1 or src_count >= 3):
            surface_dirs.append({
                "path": d,
                "kind": f"surface-container ({leaf})",
                "source_files": src_count,
                "children": [os.path.basename(s) for s in subdirs[:25]],
            })
        elif parent_leaf in ("features", "modules", "routes", "pages", "app", "cmd", "services", "apps", "packages") and src_count >= 2:
            surface_dirs.append({
                "path": d,
                "kind": f"child-of-{parent_leaf}",
                "source_files": src_count,
                "children": [os.path.basename(s) for s in subdirs[:15]],
            })

    # Inspect existing agent-map/ if present
    existing_feature_files = []
    map_dir = os.path.join(root, MAP_DIR_NAME)
    if os.path.isdir(map_dir):
        for entry in sorted(os.listdir(map_dir)):
            if not entry.endswith(".md"):
                continue
            rel = f"{MAP_DIR_NAME}/{entry}"
            try:
                with open(os.path.join(map_dir, entry), encoding="utf-8", errors="replace") as fh:
                    txt = fh.read()
            except OSError:
                continue
            meta = parse_feature_meta(txt) if entry != "README.md" else None
            notes = extract_notes_section(txt)
            existing_feature_files.append({
                "path": rel,
                "meta": meta,
                "has_custom_notes": bool(notes and len(notes.splitlines()) > 2),
            })

    monorepo_markers = [
        f for f in files if "/" not in f and f in MONOREPO_MARKERS
    ]

    return {
        "root": root,
        "sha": git_short_sha(root),
        "file_count": len(files),
        "monorepo_markers": monorepo_markers,
        "stacks": {k: sorted(set(v)) for k, v in sorted(stacks.items())},
        "languages": dict(sorted(languages.items(), key=lambda kv: -kv[1])[:10]),
        "verify_skills": verify_skills,
        "agent_files": agent_files,
        "existing_agent_map": existing_feature_files,
        "legacy_scattered_maps": legacy_scattered_maps,
        "candidate_surfaces": surface_dirs[:60],
    }


def print_summary(info):
    print(f"root: {info['root']}")
    print(f"sha:  {info['sha']}   total files: {info['file_count']}")
    print(f"monorepo markers: {info['monorepo_markers'] or 'none'}")
    print(f"languages: {info['languages']}")
    print("stacks:")
    for k, v in info["stacks"].items():
        shown = ", ".join(v[:8]) + (f" (+{len(v) - 8} more)" if len(v) > 8 else "")
        print(f"  {k:12} {shown}")
    print(f"verification skills: {info['verify_skills'] or 'none'}")
    print("agent files:")
    for a in info["agent_files"] or []:
        print(f"  {a['path']} (has agent-map block: {a['has_block']})")
    if not info["agent_files"]:
        print("  (none — create root AGENTS.md)")
    print(f"existing {MAP_DIR_NAME}/ files: {len(info['existing_agent_map'])}")
    for ef in info["existing_agent_map"]:
        paths = ef["meta"]["paths"] if ef["meta"] else []
        print(f"  {ef['path']:40} paths={paths}")
    if info["legacy_scattered_maps"]:
        print(f"legacy scattered MAP.md files found ({len(info['legacy_scattered_maps'])}):")
        for lm in info["legacy_scattered_maps"]:
            print(f"  {lm}")
    print("\ncandidate feature/surface directories:")
    if not info["candidate_surfaces"]:
        print("  (flat or small repo — inspect top-level files directly)")
    for s in info["candidate_surfaces"]:
        kids = f" -> [{', '.join(s['children'][:8])}]" if s["children"] else ""
        print(f"  {s['path']:42} ({s['kind']}, {s['source_files']} src files){kids}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--summary", action="store_true")
    args = ap.parse_args()

    start = os.path.abspath(args.root)
    root = git_toplevel(start) or start
    files = list_files(root)
    info = scan_repo(root, files)

    if args.summary or not args.json:
        print_summary(info)
    if args.json:
        json.dump(info, sys.stdout, indent=2)
        print()


if __name__ == "__main__":
    main()
