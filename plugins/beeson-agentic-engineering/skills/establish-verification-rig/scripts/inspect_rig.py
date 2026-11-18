#!/usr/bin/env python3
"""Inspect a repository to help `establish-verification-rig` interview the app.

Usage:
  inspect_rig.py [ROOT] [--summary | --json]

Detects:
- Surfaces (Web UI, API/Service, CLI/TUI, Desktop/Mobile, Worker, Library/SDK)
- Run / Launch commands (package.json scripts, Makefile targets, docker-compose, Cargo/Go/Python entrypoints)
- Existing harnesses (Playwright, Cypress, Vitest/Jest, pytest, Go test, CLI bin targets)
- Environment & state setup (.env.example, Prisma/Drizzle/SQL migrations, seed scripts, ports)
- `agent-map/` status and coverage
- Existing `.cursor/skills/run-verification-rig/` or `.cursor/skills/verify-*/` skills

Stdlib only.
"""
import argparse
import json
import os
import re
import sys

_feature_map_scripts = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "establish-feature-map", "scripts")
)
if not os.path.isdir(_feature_map_scripts):
    _feature_map_scripts = os.path.expanduser("~/.cursor/skills/establish-feature-map/scripts")
sys.path.insert(0, _feature_map_scripts)
from mapcommon import (  # noqa: E402
    MAP_DIR_NAME, git_short_sha, git_toplevel, list_files, parse_feature_meta,
    parse_readme_meta,
)

PORT_RE = re.compile(r"(?:PORT|port|--port|-p)\s*[=:]?\s*(\d{4,5})\b")
URL_PORT_RE = re.compile(r"(?:localhost|127\.0\.0\.1):(\d{4,5})\b")


def read_json_safe(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def read_text_safe(path, max_bytes=20000):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read(max_bytes)
    except OSError:
        return ""


def inspect_package_json(root, rel_path):
    data = read_json_safe(os.path.join(root, rel_path))
    if not isinstance(data, dict):
        return None
    scripts = data.get("scripts") or {}
    deps = {}
    for k in ("dependencies", "devDependencies", "peerDependencies"):
        if isinstance(data.get(k), dict):
            deps.update(data[k])

    surfaces = []
    harnesses = []
    if any(d in deps for d in ("next", "react", "vue", "svelte", "@sveltejs/kit", "astro", "nuxt", "remix", "@remix-run/react", "vite")):
        surfaces.append("web-ui")
    if "electron" in deps or "@tauri-apps/cli" in deps:
        surfaces.append("desktop")
    if any(d in deps for d in ("express", "fastify", "@nestjs/core", "hono", "koa", "@trpc/server", "apollo-server", "graphql-yoga")):
        surfaces.append("api")
    if data.get("bin") or any(d in deps for d in ("commander", "yargs", "oclif", "cac", "ink", "citty")):
        surfaces.append("cli")
    if any(d in deps for d in ("bullmq", "bull", "agenda", "@temporalio/worker")):
        surfaces.append("worker")

    if any(d in deps for d in ("@playwright/test", "playwright")):
        harnesses.append("playwright")
    if "cypress" in deps:
        harnesses.append("cypress")
    if "vitest" in deps:
        harnesses.append("vitest")
    if "jest" in deps:
        harnesses.append("jest")
    if "supertest" in deps:
        harnesses.append("supertest")

    return {
        "path": rel_path,
        "name": data.get("name"),
        "bin": data.get("bin"),
        "scripts": scripts,
        "surfaces": surfaces,
        "harnesses": harnesses,
    }


def inspect_makefile(root, rel_path):
    txt = read_text_safe(os.path.join(root, rel_path))
    targets = []
    for line in txt.splitlines():
        m = re.match(r"^([a-zA-Z0-9_.-]+)\s*:", line)
        if m and not m.group(1).startswith("."):
            targets.append(m.group(1))
    return {"path": rel_path, "targets": targets[:40]}


def inspect_env_example(root, rel_path):
    txt = read_text_safe(os.path.join(root, rel_path))
    keys = []
    ports = set()
    for line in txt.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" in s:
            k = s.split("=", 1)[0].strip()
            keys.append(k)
        for pm in PORT_RE.findall(s) + URL_PORT_RE.findall(s):
            ports.add(int(pm))
    return {"path": rel_path, "keys": keys[:30], "ports": sorted(ports)}


def inspect_agent_map(root):
    map_dir = os.path.join(root, MAP_DIR_NAME)
    if not os.path.isdir(map_dir):
        return {"exists": False, "readme": None, "features": []}

    readme_path = os.path.join(map_dir, "README.md")
    readme_txt = read_text_safe(readme_path, 50000) if os.path.isfile(readme_path) else ""
    readme_meta = parse_readme_meta(readme_txt) if readme_txt else None
    wires_rig = "run-verification-rig" in readme_txt

    features = []
    for entry in sorted(os.listdir(map_dir)):
        if not entry.endswith(".md") or entry == "README.md":
            continue
        rel = f"{MAP_DIR_NAME}/{entry}"
        txt = read_text_safe(os.path.join(map_dir, entry), 50000)
        meta = parse_feature_meta(txt)
        has_driving = "## Driving & verifying it" in txt and "Preconditions:" in txt
        features.append({
            "file": rel,
            "slug": entry[:-3],
            "sha": meta["sha"] if meta else None,
            "paths": meta["paths"] if meta else [],
            "has_driving_section": has_driving,
        })

    return {
        "exists": True,
        "readme_exists": bool(readme_txt),
        "readme_meta": readme_meta,
        "readme_wires_run_verification_rig": wires_rig,
        "feature_count": len(features),
        "features": features,
    }


def scan_repo(root, files):
    pkg_jsons = []
    makefiles = []
    env_examples = []
    compose_files = []
    schema_files = []
    e2e_configs = []
    python_manifests = []
    go_manifests = []
    rust_manifests = []
    detected_ports = set()

    for f in files:
        base = os.path.basename(f)
        lower = base.lower()

        if base == "package.json":
            info = inspect_package_json(root, f)
            if info:
                pkg_jsons.append(info)
                for s_val in info["scripts"].values():
                    for pm in PORT_RE.findall(str(s_val)) + URL_PORT_RE.findall(str(s_val)):
                        detected_ports.add(int(pm))

        elif base in ("Makefile", "GNUmakefile", "Justfile"):
            makefiles.append(inspect_makefile(root, f))

        elif lower.startswith(".env") and ("example" in lower or "sample" in lower or "template" in lower):
            env_info = inspect_env_example(root, f)
            env_examples.append(env_info)
            detected_ports.update(env_info["ports"])

        elif re.match(r"^(docker-)?compose.*\.ya?ml$", lower):
            compose_files.append(f)

        elif base in ("schema.prisma", "drizzle.config.ts", "drizzle.config.js", "alembic.ini") or f.endswith((".sql", ".graphql", ".proto")):
            schema_files.append(f)

        elif re.match(r"^(playwright|cypress|vitest|jest)\.config\.[a-z]+$", lower) or base in ("pytest.ini", "conftest.py"):
            e2e_configs.append(f)

        elif base in ("pyproject.toml", "requirements.txt", "setup.py", "Pipfile"):
            python_manifests.append(f)

        elif base == "go.mod":
            go_manifests.append(f)

        elif base == "Cargo.toml":
            rust_manifests.append(f)

    surfaces = set()
    harnesses = set()
    for p in pkg_jsons:
        surfaces.update(p["surfaces"])
        harnesses.update(p["harnesses"])
    if python_manifests:
        txt_all = "\n".join(read_text_safe(os.path.join(root, pm)) for pm in python_manifests[:5]).lower()
        if any(w in txt_all for w in ("fastapi", "flask", "django", "starlette", "aiohttp")):
            surfaces.add("api")
        if any(w in txt_all for w in ("click", "typer", "argparse", "[project.scripts]")):
            surfaces.add("cli")
        if "pytest" in txt_all or any(os.path.basename(c) in ("pytest.ini", "conftest.py") for c in e2e_configs):
            harnesses.add("pytest")
        if "playwright" in txt_all:
            harnesses.add("playwright")
    if go_manifests:
        if any(f.startswith("cmd/") or f == "main.go" for f in files):
            surfaces.add("cli-or-service (go)")
        if any(f.endswith("_test.go") for f in files):
            harnesses.add("go-test")
    if rust_manifests:
        surfaces.add("cli-or-service (rust)")
        harnesses.add("cargo-test")

    rig_skill_path = ".cursor/skills/run-verification-rig/SKILL.md"
    has_rig_skill = os.path.isfile(os.path.join(root, rig_skill_path))
    legacy_verify_skills = [
        os.path.dirname(f)
        for f in files
        if f.startswith(".cursor/skills/verify-") and os.path.basename(f) == "SKILL.md"
    ]

    return {
        "root": root,
        "sha": git_short_sha(root),
        "file_count": len(files),
        "surfaces": sorted(surfaces),
        "harnesses": sorted(harnesses),
        "detected_ports": sorted(detected_ports),
        "package_jsons": pkg_jsons[:15],
        "makefiles": makefiles[:5],
        "env_examples": env_examples[:5],
        "compose_files": compose_files[:10],
        "schema_files": schema_files[:20],
        "e2e_configs": e2e_configs[:15],
        "python_manifests": python_manifests[:10],
        "go_manifests": go_manifests[:10],
        "rust_manifests": rust_manifests[:10],
        "agent_map": inspect_agent_map(root),
        "run_verification_rig_exists": has_rig_skill,
        "legacy_verify_skills": legacy_verify_skills,
    }


def print_summary(info):
    print(f"root:      {info['root']}")
    print(f"sha:       {info['sha']}   files: {info['file_count']}")
    print(f"surfaces:  {info['surfaces'] or ['(inspect entrypoints manually)']}")
    print(f"harnesses: {info['harnesses'] or ['(none detected — use CLI/HTTP/browser recipe)']}")
    print(f"ports:     {info['detected_ports'] or 'none detected'}")

    am = info["agent_map"]
    print(f"\nagent-map/: exists={am['exists']}  features={am.get('feature_count', 0)}  wires_rig={am.get('readme_wires_run_verification_rig', False)}")
    for feat in am.get("features", []):
        print(f"  - {feat['file']:36} driving_ok={feat['has_driving_section']} paths={feat['paths']}")

    print(f"\n.cursor/skills/run-verification-rig/SKILL.md: {'EXISTS' if info['run_verification_rig_exists'] else 'MISSING'}")
    if info["legacy_verify_skills"]:
        print(f"legacy verify-* skills: {info['legacy_verify_skills']}")

    if info["package_jsons"]:
        print("\npackage.json scripts:")
        for pj in info["package_jsons"]:
            sc = ", ".join(f"{k}=`{v}`" for k, v in list(pj["scripts"].items())[:10])
            print(f"  {pj['path']} ({pj.get('name') or 'unnamed'}): {sc or '(no scripts)'}")

    if info["makefiles"]:
        print("\nMakefile targets:")
        for mk in info["makefiles"]:
            print(f"  {mk['path']}: {', '.join(mk['targets'][:15])}")

    if info["compose_files"]:
        print(f"\ndocker-compose files: {info['compose_files']}")
    if info["e2e_configs"]:
        print(f"test/e2e configs:     {info['e2e_configs']}")
    if info["schema_files"]:
        print(f"schemas/migrations:   {info['schema_files'][:8]}")
    if info["env_examples"]:
        print("env templates:")
        for ev in info["env_examples"]:
            print(f"  {ev['path']}: keys={ev['keys'][:10]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--json", action="store_true")
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
