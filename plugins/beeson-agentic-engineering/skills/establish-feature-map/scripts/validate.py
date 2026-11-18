#!/usr/bin/env python3
"""Validate `agent-map/` contract, links, tracked paths, and AGENTS.md wiring.

Usage:
  validate.py [ROOT] [--only FILE ...] [--max-lines 150] [--no-stale]

Checks:
1. `agent-map/README.md` exists, has valid metadata comment, required H2 sections in order,
   and indexes every sibling `agent-map/<feature>.md` file (no orphans, no broken links).
2. Each `agent-map/<feature>.md` has `# Name — purpose` on line 1, valid metadata comment on line 3
   with `Paths: ...`, every listed path exists in the repo, required H2 sections in order,
   valid relative links, and <= max-lines.
3. Root `AGENTS.md` (or `CLAUDE.md`) exists and includes the `<!-- agent-map:start -->` block
   pointing to `agent-map/README.md`.
4. Warns if any feature file is STALE (tracked `Paths:` have changed since `Last linted: <sha>`).

Exits 1 on any error, 0 otherwise. Stdlib only.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mapcommon import (  # noqa: E402
    BLOCK_END, BLOCK_START, FEATURE_REQUIRED_H2, MAP_DIR_NAME,
    README_REQUIRED_H2, changed_files_since, git_toplevel, list_files,
    parse_feature_meta, parse_readme_meta,
)

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
TITLE_RE = re.compile(r"^# \S.* — \S.*$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.md$")


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def err(self, path, msg):
        self.errors.append(f"{path}: {msg}")

    def warn(self, path, msg):
        self.warnings.append(f"{path}: {msg}")


def check_links(root, rel_file, text, rep):
    base = os.path.dirname(os.path.join(root, rel_file))
    linked_files = set()
    for _, target in LINK_RE.findall(text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        clean = target.split("#", 1)[0]
        if not clean:
            continue
        abs_t = os.path.normpath(os.path.join(base, clean))
        if not os.path.exists(abs_t):
            rep.err(rel_file, f"broken link: {target}")
        else:
            rel_t = os.path.relpath(abs_t, root).replace(os.sep, "/")
            linked_files.add(rel_t)
    return linked_files


def check_headings_order(rel_file, lines, required_h2, rep):
    headings = [line.strip() for line in lines if line.startswith("## ")]
    for req in required_h2:
        if req not in headings:
            rep.err(rel_file, f"missing required section `{req}`")
    for h in headings:
        if h not in required_h2:
            rep.warn(rel_file, f"unexpected H2 section `{h}` (keep to template sections)")
    present = [h for h in required_h2 if h in headings]
    actual = [h for h in headings if h in required_h2]
    if actual != present:
        rep.err(rel_file, f"sections out of order: got {actual}, expected {present}")


def validate_readme(root, text, sibling_features, rep):
    rel_file = f"{MAP_DIR_NAME}/README.md"
    lines = text.splitlines()
    if not lines or not TITLE_RE.match(lines[0]):
        rep.err(rel_file, "line 1 must be `# <Repo Name> — Agent Feature Map` (em dash)")

    meta = parse_readme_meta(text)
    if not meta:
        rep.err(
            rel_file,
            "missing metadata comment on line 3: `<!-- agent-map v2 | Last linted: <sha> | Scope: agent-map -->`",
        )
    elif meta["scope"] != MAP_DIR_NAME:
        rep.err(rel_file, f"Scope `{meta['scope']}` must be `{MAP_DIR_NAME}`")

    check_headings_order(rel_file, lines, README_REQUIRED_H2, rep)
    linked = check_links(root, rel_file, text, rep)

    for feat in sibling_features:
        if feat not in linked:
            rep.err(rel_file, f"does not link to sibling feature file `{feat}` (orphan feature)")


def validate_feature_file(root, rel_file, text, rep, max_lines, check_stale):
    fname = os.path.basename(rel_file)
    if not SLUG_RE.match(fname):
        rep.err(rel_file, "filename must be kebab-case (`lowercase-words.md`)")

    lines = text.splitlines()
    if not lines or not TITLE_RE.match(lines[0]):
        rep.err(rel_file, "line 1 must be `# <Feature Name> — <one-line purpose>` (em dash)")
    else:
        purpose_words = lines[0].split(" — ", 1)[-1].split()
        if len(purpose_words) > 14:
            rep.warn(rel_file, f"title purpose is {len(purpose_words)} words (recommend <= 14)")

    meta = parse_feature_meta(text)
    if not meta:
        rep.err(
            rel_file,
            "missing metadata comment on line 3: `<!-- agent-map v2 | Last linted: <sha> | Paths: <path1>, <path2> -->`",
        )
    else:
        if not meta["paths"]:
            rep.err(rel_file, "`Paths:` in metadata comment cannot be empty")
        existing_paths = []
        for p in meta["paths"]:
            abs_p = os.path.join(root, p)
            if not os.path.exists(abs_p):
                rep.err(rel_file, f"tracked path in `Paths:` does not exist: `{p}`")
            else:
                existing_paths.append(p)
        if check_stale and existing_paths:
            changed = changed_files_since(root, meta["sha"], existing_paths)
            if changed:
                sample = ", ".join(changed[:4]) + (f" (+{len(changed) - 4} more)" if len(changed) > 4 else "")
                rep.warn(rel_file, f"STALE since {meta['sha']}: {len(changed)} file(s) changed ({sample})")
            elif changed is None and meta["sha"] != "nogit":
                rep.warn(rel_file, f"cannot verify git sha `{meta['sha']}`")

    check_headings_order(rel_file, lines, FEATURE_REQUIRED_H2, rep)

    # Check Driving & verifying it has Preconditions:
    if "## Driving & verifying it" in text:
        sec = text.split("## Driving & verifying it", 1)[1].split("\n## ", 1)[0]
        if "Preconditions:" not in sec:
            rep.err(rel_file, "`## Driving & verifying it` must start with `Preconditions:`")

    if len(lines) > max_lines:
        rep.warn(rel_file, f"{len(lines)} lines exceeds cap of {max_lines}; split into smaller features")

    check_links(root, rel_file, text, rep)


def check_agent_files(root, files, rep):
    root_agents = [f for f in files if f in ("AGENTS.md", "CLAUDE.md")]
    if not root_agents:
        rep.err("AGENTS.md", "no root `AGENTS.md` or `CLAUDE.md` found; create `AGENTS.md` with the agent-map block")
        return
    for f in root_agents:
        try:
            with open(os.path.join(root, f), encoding="utf-8", errors="replace") as fh:
                txt = fh.read()
        except OSError:
            continue
        if BLOCK_START not in txt or BLOCK_END not in txt:
            rep.err(f, "missing `<!-- agent-map:start --> ... <!-- agent-map:end -->` block")
        else:
            block = txt.split(BLOCK_START, 1)[1].split(BLOCK_END, 1)[0]
            if f"{MAP_DIR_NAME}/README.md" not in block:
                rep.err(f, f"agent-map block does not reference `{MAP_DIR_NAME}/README.md`")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--only", nargs="*", help="validate only specific feature file(s) (for subagents)")
    ap.add_argument("--max-lines", type=int, default=150)
    ap.add_argument("--no-stale", action="store_true")
    args = ap.parse_args()

    start = os.path.abspath(args.root)
    root = git_toplevel(start) or start
    files = list_files(root)
    rep = Report()

    map_dir = os.path.join(root, MAP_DIR_NAME)
    if not os.path.isdir(map_dir):
        rep.err(MAP_DIR_NAME, f"`{MAP_DIR_NAME}/` directory does not exist at repo root")
        for e in rep.errors:
            print(f"ERROR {e}")
        sys.exit(1)

    only_set = None
    if args.only:
        only_set = set()
        for item in args.only:
            rel = os.path.relpath(os.path.abspath(item), root).replace(os.sep, "/") if os.path.isabs(item) else item
            only_set.add(rel.lstrip("./"))

    all_md = sorted(
        f"{MAP_DIR_NAME}/{e}"
        for e in os.listdir(map_dir)
        if e.endswith(".md") and os.path.isfile(os.path.join(map_dir, e))
    )
    readme_rel = f"{MAP_DIR_NAME}/README.md"
    sibling_features = [f for f in all_md if f != readme_rel]

    if not sibling_features and not only_set:
        rep.err(MAP_DIR_NAME, f"no feature files (`{MAP_DIR_NAME}/<feature>.md`) found")

    for rel_file in sibling_features:
        if only_set and rel_file not in only_set:
            continue
        try:
            with open(os.path.join(root, rel_file), encoding="utf-8", errors="replace") as fh:
                txt = fh.read()
        except OSError as e:
            rep.err(rel_file, f"unreadable: {e}")
            continue
        validate_feature_file(root, rel_file, txt, rep, args.max_lines, not args.no_stale)

    if not only_set or readme_rel in only_set:
        readme_abs = os.path.join(root, readme_rel)
        if not os.path.isfile(readme_abs):
            rep.err(readme_rel, f"missing `{readme_rel}` index file")
        else:
            with open(readme_abs, encoding="utf-8", errors="replace") as fh:
                validate_readme(root, fh.read(), sibling_features, rep)
        check_agent_files(root, files, rep)

    for w in rep.warnings:
        print(f"WARN  {w}")
    for e in rep.errors:
        print(f"ERROR {e}")
    checked_count = len(only_set) if only_set else len(all_md)
    print(f"\n{checked_count} agent-map file(s) checked; {len(rep.errors)} errors, {len(rep.warnings)} warnings")
    sys.exit(1 if rep.errors else 0)


if __name__ == "__main__":
    main()
