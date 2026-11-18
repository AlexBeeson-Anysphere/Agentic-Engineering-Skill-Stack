#!/usr/bin/env python3
"""Check the Cursor and Claude Code plugin package against the repo tree.

The skill folders under plugins/beeson-agentic-engineering/skills/ are the
registry. This script checks that both marketplace manifests point at that
plugin, that every SKILL.md name matches its directory, and that the README
links to every skill.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "beeson-agentic-engineering"
MARKETPLACE_NAME = "beeson-agentic-engineering"
PLUGIN_REL = Path("plugins") / PLUGIN_NAME
SKILLS_REL = PLUGIN_REL / "skills"
NAME_RE = re.compile(r"^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.S)
PRINCIPLES_REL = SKILLS_REL / "engineering-principles"
RELATIVE_MD_LINK_RE = re.compile(r"\]\(((?!https?:|#)[^)\s]+\.md)(?:#[^)]*)?\)")

errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def load_json(rel: Path) -> dict:
    path = ROOT / rel
    if not path.is_file():
        fail(f"missing {rel}")
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"{rel} is not valid JSON: {exc}")
        return {}
    if not isinstance(data, dict):
        fail(f"{rel} must be a JSON object")
        return {}
    return data


def frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line or line[0] in " \t" or ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip("\"'")
    return fields


def main() -> int:
    cursor_market = load_json(Path(".cursor-plugin/marketplace.json"))
    claude_market = load_json(Path(".claude-plugin/marketplace.json"))
    cursor_plugin = load_json(PLUGIN_REL / ".cursor-plugin/plugin.json")
    claude_plugin = load_json(PLUGIN_REL / ".claude-plugin/plugin.json")

    for label, doc in (
        ("Cursor marketplace", cursor_market),
        ("Claude marketplace", claude_market),
    ):
        if doc.get("name") != MARKETPLACE_NAME:
            fail(f"{label} name is {doc.get('name')!r}, expected {MARKETPLACE_NAME!r}")
        owner = doc.get("owner")
        if not isinstance(owner, dict) or not owner.get("name"):
            fail(f"{label} owner.name is missing")
        plugins = doc.get("plugins")
        if not isinstance(plugins, list) or len(plugins) != 1:
            fail(f"{label} must list exactly one plugin")
            continue
        entry = plugins[0]
        if not isinstance(entry, dict):
            fail(f"{label} plugin entry must be an object")
            continue
        if entry.get("name") != PLUGIN_NAME:
            fail(f"{label} plugin name is {entry.get('name')!r}")
        source = entry.get("source")
        if not isinstance(source, str) or not source:
            fail(f"{label} plugin source is missing")
            continue
        if source.startswith("..") or source.startswith("/"):
            fail(f"{label} source must stay inside the repo: {source}")
        resolved = (ROOT / source).resolve()
        try:
            resolved.relative_to(ROOT)
        except ValueError:
            fail(f"{label} source escapes the repo: {source}")
            continue
        manifest = resolved / ".cursor-plugin/plugin.json"
        if label.startswith("Claude"):
            if not source.startswith("./"):
                fail(f"Claude marketplace source must start with ./ : {source}")
            manifest = resolved / ".claude-plugin/plugin.json"
        if not manifest.is_file():
            fail(f"{label} source {source} has no {manifest.name} at the expected path")

    for label, doc in (("Cursor plugin", cursor_plugin), ("Claude plugin", claude_plugin)):
        name = doc.get("name")
        if name != PLUGIN_NAME:
            fail(f"{label} name is {name!r}, expected {PLUGIN_NAME!r}")
        elif not NAME_RE.match(str(name)):
            fail(f"{label} name is not kebab-case: {name}")
        if not doc.get("description"):
            fail(f"{label} description is missing")
        if doc.get("version") != "1.0.0":
            fail(f"{label} version is {doc.get('version')!r}")
        author = doc.get("author")
        if not isinstance(author, dict) or not author.get("name"):
            fail(f"{label} author.name is missing")

    skills_dir = ROOT / SKILLS_REL
    if not skills_dir.is_dir():
        fail(f"missing {SKILLS_REL}")
        skill_names: list[str] = []
    else:
        skill_names = sorted(p.name for p in skills_dir.iterdir() if p.is_dir())

    readme = ROOT / "README.md"
    readme_text = readme.read_text() if readme.is_file() else ""
    if not readme.is_file():
        fail("missing README.md")

    seen: set[str] = set()
    for skill_md in sorted(ROOT.joinpath(PLUGIN_REL).rglob("SKILL.md")):
        rel = skill_md.relative_to(ROOT)
        parent = skill_md.parent
        if parent.parent != skills_dir:
            fail(f"{rel} is not a direct child of {SKILLS_REL}/<name>/")
            continue
        fields = frontmatter(skill_md.read_text())
        name = fields.get("name", "")
        if name != parent.name:
            fail(f"{rel} frontmatter name {name!r} does not match directory {parent.name!r}")
        if not fields.get("description"):
            fail(f"{rel} description is missing")
        if not NAME_RE.match(parent.name):
            fail(f"{rel} directory name is not kebab-case")
        seen.add(parent.name)
        link = f"{SKILLS_REL.as_posix()}/{parent.name}/SKILL.md"
        if link not in readme_text:
            fail(f"README.md does not link to {link}")
        if parent.name.startswith("principle-"):
            canonical = f"../engineering-principles/principles/{parent.name}.md"
            if canonical not in skill_md.read_text():
                fail(f"{rel} must point at {canonical} instead of carrying its own copy")

    missing_dirs = [name for name in skill_names if name not in seen]
    for name in missing_dirs:
        fail(f"{SKILLS_REL}/{name} has no SKILL.md")

    # Templates link to paths inside the application repo, so only the router,
    # the principle catalog, and links that target a principle are resolved here.
    routing_dirs = (skills_dir / "initiate-playbook-router", ROOT / PRINCIPLES_REL)
    for doc in sorted(skills_dir.rglob("*.md")):
        in_routing = any(doc.is_relative_to(d) for d in routing_dirs)
        for match in RELATIVE_MD_LINK_RE.finditer(doc.read_text()):
            if not in_routing and "principle-" not in match.group(1):
                continue
            if not (doc.parent / match.group(1)).resolve().is_file():
                fail(f"{doc.relative_to(ROOT)} links to missing {match.group(1)}")

    catalog = ROOT / PRINCIPLES_REL / "SKILL.md"
    catalog_text = catalog.read_text() if catalog.is_file() else ""
    for guideline in sorted((ROOT / PRINCIPLES_REL / "principles").glob("*.md")):
        if f"](principles/{guideline.name})" not in catalog_text:
            fail(f"{PRINCIPLES_REL}/SKILL.md does not list principles/{guideline.name}")

    if errors:
        print(f"validate_plugin: {len(errors)} error(s)")
        for message in errors:
            print(f"  {message}")
        return 1

    print(f"validate_plugin: ok ({len(seen)} skills, both marketplaces resolve)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
