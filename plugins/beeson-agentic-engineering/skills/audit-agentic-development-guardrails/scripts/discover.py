#!/usr/bin/env python3
"""Read-only inventory of agentic-development guardrail signals in a repository.

Usage:
  discover.py [ROOT] [--out-dir DIR] [--summary] [--since-days 90] [--max-commits 500]
              [--max-files 60000] [--github] [--comment-pages 3]

Collects languages, manifests, guardrail tool configs, CI gate commands and soft-fail
patterns, TypeScript and Python strictness, agent instruction files, CODEOWNERS
coverage, suppression and type escape-hatch counts, largest files, git hotspots,
directories touched per commit, reverts, and comment lines added in the window.
With --github, also reads rulesets, branch protection, and recent PR review comments
through the gh CLI.

Writes discover.json (and review-comments.json with --github) into --out-dir, or prints
JSON to stdout. --summary also prints a short digest. Never modifies ROOT. Stdlib only.
"""
import argparse
import fnmatch
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
from collections import Counter

IGNORED_DIRS = {
    "node_modules", ".git", "dist", "build", "out", "target", "vendor", ".venv", "venv",
    "__pycache__", ".next", ".nuxt", ".svelte-kit", "coverage", ".turbo", ".cache", "Pods",
    "DerivedData", ".gradle", ".idea", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox",
    "bower_components", ".yarn", ".pnpm-store", ".guardrail-audit", ".verification-evidence",
}
LOCKFILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb", "bun.lock", "Cargo.lock",
    "poetry.lock", "uv.lock", "Pipfile.lock", "go.sum", "Gemfile.lock", "composer.lock",
    "gradle.lockfile", "packages.lock.json", "Podfile.lock", "pubspec.lock", "mix.lock",
}
SOURCE_EXTS = {
    ".ts": "c", ".tsx": "c", ".mts": "c", ".cts": "c", ".js": "c", ".jsx": "c", ".mjs": "c",
    ".cjs": "c", ".vue": "c", ".svelte": "c", ".go": "c", ".rs": "c", ".java": "c", ".kt": "c",
    ".kts": "c", ".scala": "c", ".swift": "c", ".cs": "c", ".c": "c", ".cc": "c", ".cpp": "c",
    ".h": "c", ".hpp": "c", ".m": "c", ".mm": "c", ".dart": "c", ".php": "c",
    ".py": "hash", ".rb": "hash", ".ex": "hash", ".exs": "hash",
}
LANGUAGES = {
    ".ts": "TypeScript", ".tsx": "TypeScript", ".mts": "TypeScript", ".cts": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".vue": "Vue", ".svelte": "Svelte", ".go": "Go", ".rs": "Rust", ".java": "Java",
    ".kt": "Kotlin", ".kts": "Kotlin", ".scala": "Scala", ".swift": "Swift", ".cs": "C#",
    ".c": "C", ".cc": "C++", ".cpp": "C++", ".h": "C/C++", ".hpp": "C++", ".m": "Objective-C",
    ".mm": "Objective-C", ".dart": "Dart", ".php": "PHP", ".py": "Python", ".rb": "Ruby",
    ".ex": "Elixir", ".exs": "Elixir",
}
JS_EXTS = {".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte"}
TS_EXTS = {".ts", ".tsx", ".mts", ".cts"}
GENERATED_SUFFIXES = (".min.js", "_pb2.py", "_pb2_grpc.py", ".pb.go", ".g.dart", ".freezed.dart", ".d.ts")

MANIFESTS = {
    "package.json", "pnpm-workspace.yaml", "lerna.json", "nx.json", "turbo.json", "rush.json",
    "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile", "go.mod", "go.work",
    "Cargo.toml", "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle",
    "settings.gradle.kts", "Gemfile", "composer.json", "pubspec.yaml", "mix.exs", "Package.swift",
    "WORKSPACE", "WORKSPACE.bazel", "MODULE.bazel", "Makefile", "justfile", "Taskfile.yml",
}

TOOL_FILES = {
    "eslint": ["eslint.config.*", ".eslintrc", ".eslintrc.*"],
    "biome": ["biome.json", "biome.jsonc"],
    "oxlint": [".oxlintrc.json", "oxlintrc.json"],
    "prettier": [".prettierrc", ".prettierrc.*", "prettier.config.*"],
    "typescript": ["tsconfig.json", "tsconfig.*.json"],
    "dependency-cruiser": [".dependency-cruiser.*", "dependency-cruiser.*"],
    "nx": ["nx.json"],
    "turborepo": ["turbo.json"],
    "knip": ["knip.json", "knip.jsonc", ".knip.json", "knip.config.*"],
    "betterer": [".betterer.ts", ".betterer.js", ".betterer.results"],
    "eslint-bulk-suppressions": ["eslint-suppressions.json"],
    "size-limit": [".size-limit.json", ".size-limit.js", ".size-limit.cjs", ".size-limit.mjs", ".size-limit.ts"],
    "bundlewatch": ["bundlewatch.config.json", ".bundlewatch.config.json"],
    "danger": ["dangerfile.js", "dangerfile.ts", "Dangerfile"],
    "semgrep": [".semgrep.yml", ".semgrep.yaml", "semgrep.yml", "semgrep.yaml", ".semgrep/*"],
    "ast-grep": ["sgconfig.yml", "sgconfig.yaml"],
    "stryker": ["stryker.conf.*", "stryker.config.*", ".stryker.conf.*"],
    "api-extractor": ["api-extractor.json"],
    "husky": [".husky/*"],
    "lefthook": ["lefthook.yml", "lefthook.yaml", ".lefthook.yml"],
    "pre-commit": [".pre-commit-config.yaml"],
    "lint-staged": [".lintstagedrc", ".lintstagedrc.*", "lint-staged.config.*"],
    "ruff": ["ruff.toml", ".ruff.toml"],
    "mypy": ["mypy.ini", ".mypy.ini"],
    "pyright": ["pyrightconfig.json"],
    "import-linter": [".importlinter"],
    "golangci-lint": [".golangci.yml", ".golangci.yaml", ".golangci.toml", ".golangci.json"],
    "clippy": ["clippy.toml", ".clippy.toml"],
    "cargo-deny": ["deny.toml"],
    "detekt": ["detekt.yml", "detekt-config.yml"],
    "checkstyle": ["checkstyle.xml"],
    "bazel": ["BUILD", "BUILD.bazel", "WORKSPACE", "WORKSPACE.bazel", "MODULE.bazel"],
    "gitleaks": [".gitleaks.toml", "gitleaks.toml"],
    "dependabot": [".github/dependabot.yml", ".github/dependabot.yaml"],
    "renovate": ["renovate.json", "renovate.json5", ".renovaterc", ".renovaterc.json", ".github/renovate.json", ".github/renovate.json5"],
    "codeowners": ["CODEOWNERS"],
    "bugbot": ["BUGBOT.md"],
}
NPM_TOOLS = {
    "eslint": ["eslint"], "biome": ["@biomejs/biome"], "oxlint": ["oxlint"], "prettier": ["prettier"],
    "typescript": ["typescript"], "dependency-cruiser": ["dependency-cruiser"],
    "eslint-plugin-boundaries": ["eslint-plugin-boundaries"],
    "eslint-plugin-import": ["eslint-plugin-import", "eslint-plugin-import-x"],
    "eslint-comments": ["eslint-plugin-eslint-comments", "@eslint-community/eslint-plugin-eslint-comments"],
    "typescript-eslint": ["typescript-eslint", "@typescript-eslint/eslint-plugin"],
    "nx": ["nx"], "knip": ["knip"], "ts-prune": ["ts-prune"], "betterer": ["@betterer/cli"],
    "size-limit": ["size-limit"], "bundlewatch": ["bundlewatch"], "danger": ["danger"],
    "stryker": ["@stryker-mutator/core"], "api-extractor": ["@microsoft/api-extractor"],
    "husky": ["husky"], "lefthook": ["lefthook"], "lint-staged": ["lint-staged"],
    "zod": ["zod"], "valibot": ["valibot"], "trpc": ["@trpc/server"],
    "openapi-codegen": ["openapi-typescript", "@hey-api/openapi-ts", "orval", "openapi-generator-cli", "@openapitools/openapi-generator-cli"],
    "graphql-codegen": ["@graphql-codegen/cli"], "ts-pattern": ["ts-pattern"],
    "lighthouse-ci": ["@lhci/cli"], "playwright": ["@playwright/test"], "vitest": ["vitest"], "jest": ["jest"],
}
PY_SECTIONS = {
    "ruff": r"^\[tool\.ruff", "mypy": r"^\[(tool\.)?mypy", "pyright": r"^\[tool\.pyright",
    "import-linter": r"^\[(tool\.)?importlinter", "mutmut": r"^\[(tool\.)?mutmut",
    "vulture": r"^\[tool\.vulture", "pylint": r"^\[(tool\.pylint|pylint)", "flake8": r"^\[flake8",
    "black": r"^\[tool\.black", "deptry": r"^\[tool\.deptry", "pytest": r"^\[(tool\.pytest|pytest|tool:pytest)",
    "pytest-rerunfailures": r"pytest-rerunfailures", "pydantic": r"\bpydantic\b",
}
JVM_MARKERS = {
    "archunit": r"archunit", "checkstyle": r"checkstyle", "spotbugs": r"spotbugs",
    "errorprone": r"error_?prone", "pmd": r"\bpmd\b", "detekt": r"detekt", "ktlint": r"ktlint",
    "pitest": r"pitest", "spotless": r"spotless", "jacoco": r"jacoco",
}

CI_PATTERNS = [
    ".github/workflows/*.yml", ".github/workflows/*.yaml", ".gitlab-ci.yml", ".circleci/config.yml",
    "Jenkinsfile", "azure-pipelines.yml", ".buildkite/*.yml", ".buildkite/*.yaml",
    "bitbucket-pipelines.yml", ".drone.yml", "cloudbuild.yaml", ".travis.yml",
]
GATE_WORDS = re.compile(
    r"\b(lint|eslint|biome|oxlint|tsc|typecheck|type-check|mypy|pyright|ruff|flake8|pylint|black|"
    r"prettier|format|fmt|depcruise|dependency-cruiser|knip|semgrep|ast-grep|sg scan|danger|betterer|"
    r"size-limit|bundlewatch|stryker|mutmut|golangci|go vet|clippy|cargo deny|gitleaks|trufflehog|"
    r"codeql|test|pytest|jest|vitest|playwright|check|verify|guard|validate|nx affected|turbo run)\b",
    re.I,
)
SOFT_FAIL = re.compile(
    r"continue-on-error:\s*true|\|\|\s*true\b|\|\|\s*exit 0|allow_failure:\s*true|--exit-zero|"
    r"\bset \+e\b|--max-warnings[= ]-1|soft_fail:\s*true",
    re.I,
)
TRIGGERS = ("pull_request", "pull_request_target", "push", "merge_group", "schedule", "workflow_dispatch", "merge_request")

SUPPRESSIONS = [
    ("eslint-disable", re.compile(r"eslint-disable"), JS_EXTS),
    ("biome-ignore", re.compile(r"biome-ignore"), JS_EXTS),
    ("oxlint-disable", re.compile(r"oxlint-disable"), JS_EXTS),
    ("ts-ignore", re.compile(r"@ts-ignore"), JS_EXTS),
    ("ts-expect-error", re.compile(r"@ts-expect-error"), JS_EXTS),
    ("ts-nocheck", re.compile(r"@ts-nocheck"), JS_EXTS),
    ("type-ignore", re.compile(r"#\s*type:\s*ignore"), {".py"}),
    ("pyright-ignore", re.compile(r"#\s*pyright:\s*ignore"), {".py"}),
    ("noqa", re.compile(r"#\s*noqa"), {".py"}),
    ("pylint-disable", re.compile(r"#\s*pylint:\s*disable"), {".py"}),
    ("nolint", re.compile(r"//\s*nolint"), {".go"}),
    ("rust-allow", re.compile(r"#!?\[allow\("), {".rs"}),
    ("jvm-suppress", re.compile(r"@SuppressWarnings|@Suppress\("), {".java", ".kt", ".kts", ".scala"}),
    ("rubocop-disable", re.compile(r"rubocop:disable"), {".rb"}),
]
ESCAPE_HATCHES = [
    ("ts-any", re.compile(r":\s*any\b|\bas\s+any\b|<any>|\bany\[\]"), TS_EXTS),
    ("ts-double-cast", re.compile(r"\bas\s+unknown\s+as\b"), TS_EXTS),
    ("rust-unsafe", re.compile(r"\bunsafe\s*(\{|fn\b|impl\b)"), {".rs"}),
    ("go-unsafe", re.compile(r"\"unsafe\""), {".go"}),
]
EXPIRY = re.compile(r"(expires?|until|remove (by|after))\W{0,3}\d{4}-\d{2}", re.I)
DIRECTIVE = re.compile(r"eslint-|@ts-|noqa|type:\s*ignore|pyright:|pylint:|nolint|prettier-ignore|biome-ignore|istanbul ignore|c8 ignore|rubocop:")
NARRATION = re.compile(
    r"\b(per (the )?(review|feedback|discussion|pr|comment)|as (discussed|requested|suggested|mentioned)|"
    r"reviewer|requested by|do not (remove|change|touch|delete)|don'?t (remove|change|touch|delete)|"
    r"previously|used to|was changed|no longer|now uses|instead of the old|we now|changed (this|to)|"
    r"workaround|hack)\b",
    re.I,
)
IMPERATIVE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+.*\b(never|always|do not|don't|must|avoid)\b", re.I)
AGENT_FILES = {"AGENTS.md", "CLAUDE.md", "GEMINI.md", ".cursorrules", ".windsurfrules", "copilot-instructions.md", "BUGBOT.md", "CONTRIBUTING.md"}
GATE_SCRIPT_NAMES = re.compile(r"^(lint|typecheck|type-check|types|check|verify|guard|validate|ci|test|format|fmt)([:_-].*)?$")


def run(cmd, cwd=None, timeout=60):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, errors="replace")
        return p.returncode, p.stdout, p.stderr
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, "", str(e)


def git(root, *args, timeout=120):
    code, out, _ = run(["git", "-C", root, *args], timeout=timeout)
    return out if code == 0 else None


def is_ignored(path):
    return any(part in IGNORED_DIRS for part in path.split("/"))


def is_generated(path):
    low = path.lower()
    return "generated" in low or low.endswith(GENERATED_SUFFIXES)


def ext_of(path):
    return os.path.splitext(path)[1].lower()


def read_text(root, rel, limit=1_500_000):
    p = os.path.join(root, rel)
    try:
        if os.path.getsize(p) > limit:
            return None
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def list_files(root, max_files):
    out = git(root, "ls-files", "-z", "-co", "--exclude-standard")
    if out is not None:
        files = [f for f in out.split("\0") if f and not is_ignored(f)]
    else:
        files = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
            for fn in filenames:
                files.append(os.path.relpath(os.path.join(dirpath, fn), root).replace(os.sep, "/"))
    files = [f for f in files if os.path.isfile(os.path.join(root, f))]
    truncated = len(files) > max_files
    return sorted(files)[:max_files], truncated


def match_pattern(path, pattern):
    if "/" in pattern:
        return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, "*/" + pattern)
    return fnmatch.fnmatch(os.path.basename(path), pattern)


def strip_jsonc(text):
    out, i, n, in_str, esc = [], 0, len(text), False, False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j == -1 else j
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j == -1 else j + 2
            continue
        out.append(c)
        i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def load_jsonc(root, rel):
    text = read_text(root, rel)
    if text is None:
        return None
    try:
        return json.loads(strip_jsonc(text))
    except ValueError:
        return None


# ---------------------------------------------------------------- sections


def section_languages(files):
    c = Counter(LANGUAGES[ext_of(f)] for f in files if ext_of(f) in LANGUAGES and not is_generated(f))
    return dict(c.most_common(12))


def section_manifests(files):
    found = [f for f in files if os.path.basename(f) in MANIFESTS]
    return {"count": len(found), "paths": sorted(found, key=lambda p: (p.count("/"), p))[:60]}


def section_tooling(root, files):
    tools = {}
    for tool, patterns in TOOL_FILES.items():
        hits = [f for f in files if any(match_pattern(f, p) for p in patterns)]
        if hits:
            tools.setdefault(tool, {"configs": [], "signals": []})["configs"] = sorted(hits, key=lambda p: (p.count("/"), p))[:10]

    deps, scripts, exports_count = set(), {}, 0
    pkgs = [f for f in files if os.path.basename(f) == "package.json"][:300]
    for rel in pkgs:
        data = load_jsonc(root, rel)
        if not isinstance(data, dict):
            continue
        for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
            if isinstance(data.get(key), dict):
                deps.update(data[key])
        if "exports" in data:
            exports_count += 1
        if isinstance(data.get("scripts"), dict):
            gate = {k: v for k, v in data["scripts"].items() if GATE_SCRIPT_NAMES.match(k)}
            if gate:
                scripts[rel] = gate
    for tool, names in NPM_TOOLS.items():
        hit = [n for n in names if n in deps]
        if hit:
            tools.setdefault(tool, {"configs": [], "signals": []})["signals"].append("npm: " + ", ".join(hit))

    py_files = [f for f in files if os.path.basename(f) in ("pyproject.toml", "setup.cfg", "tox.ini", "requirements.txt", "requirements-dev.txt")][:60]
    for rel in py_files:
        text = read_text(root, rel) or ""
        for tool, pat in PY_SECTIONS.items():
            if re.search(pat, text, re.M | re.I):
                tools.setdefault(tool, {"configs": [], "signals": []})["signals"].append(rel)

    jvm_files = [f for f in files if os.path.basename(f) in ("pom.xml", "build.gradle", "build.gradle.kts")][:80]
    for rel in jvm_files:
        text = (read_text(root, rel) or "").lower()
        for tool, pat in JVM_MARKERS.items():
            if re.search(pat, text):
                tools.setdefault(tool, {"configs": [], "signals": []})["signals"].append(rel)

    for t in tools.values():
        t["signals"] = sorted(set(t["signals"]))[:10]

    make_targets = {}
    for rel in [f for f in files if os.path.basename(f) in ("Makefile", "justfile", "Justfile")][:20]:
        text = read_text(root, rel) or ""
        names = sorted({m.group(1) for m in re.finditer(r"^([A-Za-z0-9_.-]+)\s*:(?!=)", text, re.M)})
        gate = [n for n in names if GATE_SCRIPT_NAMES.match(n)]
        if gate:
            make_targets[rel] = gate

    return {
        "tools": dict(sorted(tools.items())),
        "package_scripts": scripts,
        "make_targets": make_targets,
        "package_json_with_exports": exports_count,
        "package_json_count": len(pkgs),
        "go_internal_dirs": len({os.path.dirname(f) for f in files if "/internal/" in "/" + f and f.endswith(".go")}),
    }


def resolve_tsconfig(root, rel, depth=0):
    data = load_jsonc(root, rel)
    if not isinstance(data, dict):
        return {}, []
    opts, external = {}, []
    ext = data.get("extends")
    for parent in ([ext] if isinstance(ext, str) else ext or []):
        if isinstance(parent, str) and parent.startswith(".") and depth < 4:
            prel = os.path.normpath(os.path.join(os.path.dirname(rel), parent)).replace(os.sep, "/")
            if not prel.endswith(".json"):
                prel += ".json"
            popts, pext = resolve_tsconfig(root, prel, depth + 1)
            opts.update(popts)
            external += pext
        elif isinstance(parent, str):
            external.append(parent)
    opts.update(data.get("compilerOptions") or {})
    return opts, external


def section_typescript(root, files):
    configs = sorted((f for f in files if match_pattern(f, "tsconfig.json") or match_pattern(f, "tsconfig.*.json")), key=lambda p: (p.count("/"), p))[:30]
    flags = ("strict", "noUncheckedIndexedAccess", "exactOptionalPropertyTypes", "noImplicitAny",
             "noImplicitReturns", "noFallthroughCasesInSwitch", "noPropertyAccessFromIndexSignature",
             "allowJs", "checkJs", "skipLibCheck")
    out = []
    for rel in configs:
        opts, external = resolve_tsconfig(root, rel)
        out.append({"path": rel, "extends_packages": external, **{k: opts.get(k) for k in flags if k in opts}})
    return out


def section_python_typing(root, files):
    out = {}
    for rel in [f for f in files if os.path.basename(f) in ("pyproject.toml", "setup.cfg", "mypy.ini", ".mypy.ini", "pyrightconfig.json")][:40]:
        text = read_text(root, rel) or ""
        info = {}
        if rel.endswith("pyrightconfig.json"):
            data = load_jsonc(root, rel) or {}
            info["pyright_mode"] = data.get("typeCheckingMode")
        else:
            for name, header in (("mypy", r"^\[(tool\.)?mypy\]"), ("pyright", r"^\[tool\.pyright\]")):
                m = re.search(header, text, re.M)
                if not m:
                    continue
                rest = text[m.end():]
                nxt = re.search(r"^\[", rest, re.M)
                body = rest[: nxt.start()] if nxt else rest
                if name == "mypy":
                    info["mypy_strict"] = bool(re.search(r"^\s*strict\s*=\s*(true|True)", body, re.M))
                else:
                    mm = re.search(r"typeCheckingMode\s*=\s*\"(\w+)\"", body)
                    info["pyright_mode"] = mm.group(1) if mm else None
        if info:
            out[rel] = info
    return out


def section_rust(root, files):
    out = {"forbid_unsafe": [], "lints_tables": []}
    for rel in [f for f in files if os.path.basename(f) == "Cargo.toml"][:40]:
        text = read_text(root, rel) or ""
        if re.search(r"^\[(workspace\.)?lints", text, re.M):
            out["lints_tables"].append(rel)
        if re.search(r"unsafe_code\s*=\s*\"(forbid|deny)\"", text):
            out["forbid_unsafe"].append(rel)
    for rel in [f for f in files if os.path.basename(f) in ("lib.rs", "main.rs")][:200]:
        text = read_text(root, rel) or ""
        if re.search(r"#!\[(forbid|deny)\(unsafe_code", text):
            out["forbid_unsafe"].append(rel)
    return out if (out["forbid_unsafe"] or out["lints_tables"]) else {}


def is_ci_file(path):
    for p in CI_PATTERNS:
        if "/" in p:
            if fnmatch.fnmatch(path, p):
                return True
        elif fnmatch.fnmatch(os.path.basename(path), p):
            return True
    return False


def section_ci(root, files):
    result = {"files": [], "scheduled": []}
    for rel in sorted(f for f in files if is_ci_file(f))[:60]:
        text = read_text(root, rel) or ""
        lines = text.splitlines()
        gate_lines, soft = [], []
        for n, line in enumerate(lines, 1):
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if SOFT_FAIL.search(s):
                soft.append({"path": rel, "line": n, "text": s[:160]})
            if len(gate_lines) < 40 and GATE_WORDS.search(s) and re.search(r"(run:|^-\s|script|command|^\w[\w-]*\s)", s):
                gate_lines.append({"line": n, "text": s[:160]})
        triggers = [t for t in TRIGGERS if re.search(rf"\b{t}\b", text)]
        result["files"].append({"path": rel, "triggers": triggers, "gate_lines": gate_lines, "soft_fail": soft})
        if "schedule" in triggers:
            result["scheduled"].append(rel)
    return result


def section_agent_instructions(root, files):
    out = []
    for rel in files:
        base = os.path.basename(rel)
        if base in AGENT_FILES or rel.startswith(".cursor/rules/") or "/.cursor/rules/" in rel:
            text = read_text(root, rel) or ""
            lines = text.splitlines()
            out.append({
                "path": rel,
                "lines": len(lines),
                "imperative_rules": sum(1 for l in lines if IMPERATIVE.search(l)),
                "has_rule_table": any(l.lstrip().startswith("|") and re.search(r"enforc", l, re.I) for l in lines),
            })
        if len(out) >= 60:
            break
    skills = sorted({rel.split("/SKILL.md")[0] for rel in files if rel.endswith("/SKILL.md") and ".cursor/skills/" in "/" + rel})
    return {"files": out, "project_skills": skills[:40]}


def section_codeowners(root, files):
    out = []
    gate_pat = re.compile(r"(\.github|workflows|eslint|tsconfig|biome|ruff|golangci|dependency-cruiser|CODEOWNERS|package\.json|lock|pyproject|Makefile|semgrep|\.cursor)", re.I)
    for rel in [f for f in files if os.path.basename(f) == "CODEOWNERS"][:5]:
        text = read_text(root, rel) or ""
        patterns = [l.split()[0] for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]
        out.append({
            "path": rel,
            "rules": len(patterns),
            "catch_all": any(p in ("*", "/*", "/**", "**") for p in patterns),
            "gate_config_patterns": [p for p in patterns if gate_pat.search(p)][:20],
        })
    return out


def section_source_scan(root, files):
    sup = {name: {"count": 0, "top_files": Counter()} for name, _, _ in SUPPRESSIONS}
    with_reason = with_expiry = 0
    hatches = Counter()
    sizes = []
    for rel in files:
        ext = ext_of(rel)
        if ext not in SOURCE_EXTS or is_generated(rel):
            continue
        text = read_text(root, rel)
        if text is None:
            continue
        lines = text.splitlines()
        sizes.append((len(lines), rel))
        for line in lines:
            for name, pat, exts in SUPPRESSIONS:
                if ext not in exts:
                    continue
                m = pat.search(line)
                if not m:
                    continue
                sup[name]["count"] += 1
                sup[name]["top_files"][rel] += 1
                tail = line[m.end():]
                if name == "eslint-disable":
                    if " -- " in tail or tail.strip().startswith("--"):
                        with_reason += 1
                elif name == "biome-ignore" or len(re.findall(r"[A-Za-z]{2,}", tail)) >= 3:
                    with_reason += 1
                if EXPIRY.search(line):
                    with_expiry += 1
            for name, pat, exts in ESCAPE_HATCHES:
                if ext in exts:
                    hatches[name] += len(pat.findall(line))
    by_pattern = {
        k: {"count": v["count"], "top_files": [f"{p} ({c})" for p, c in v["top_files"].most_common(5)]}
        for k, v in sup.items() if v["count"]
    }
    sizes.sort(reverse=True)
    structure = {
        "source_files": len(sizes),
        "largest_files": [{"path": p, "lines": n} for n, p in sizes[:15]],
        "over_500": sum(1 for n, _ in sizes if n > 500),
        "over_1000": sum(1 for n, _ in sizes if n > 1000),
        "over_3000": sum(1 for n, _ in sizes if n > 3000),
    }
    suppressions = {
        "total": sum(v["count"] for v in by_pattern.values()),
        "with_reason": with_reason,
        "with_expiry": with_expiry,
        "by_pattern": by_pattern,
    }
    return suppressions, {k: v for k, v in hatches.items() if v}, structure


def dir_key(path):
    parts = path.split("/")[:-1]
    return "/".join(parts[:3]) if parts else "."


def section_git(root, since_days, max_commits):
    if git(root, "rev-parse", "--git-dir") is None:
        return {"available": False}
    head = (git(root, "rev-parse", "--short", "HEAD") or "").strip()
    branch = (git(root, "rev-parse", "--abbrev-ref", "HEAD") or "").strip()
    origin_head = (git(root, "symbolic-ref", "--short", "refs/remotes/origin/HEAD") or "").strip()
    remote = (git(root, "remote", "get-url", "origin") or "").strip()
    shallow = (git(root, "rev-parse", "--is-shallow-repository") or "").strip() == "true"
    out = git(root, "log", f"--since={since_days}.days", "--no-merges", f"--max-count={max_commits}",
              "--name-only", "--pretty=format:%x1e%h%x1f%s", timeout=180) or ""
    commits = []
    for rec in out.split("\x1e"):
        rec = rec.strip("\n")
        if not rec:
            continue
        header, _, rest = rec.partition("\n")
        sha, _, subject = header.partition("\x1f")
        commits.append((sha, subject, [f for f in rest.splitlines() if f.strip()]))

    touched = Counter()
    spreads = []
    for _, _, fs in commits:
        for f in fs:
            base = os.path.basename(f)
            if base in LOCKFILES or base.lower().startswith("changelog"):
                continue
            touched[f] += 1
        dirs = {dir_key(f) for f in fs if ext_of(f) in SOURCE_EXTS and not is_ignored(f)}
        if dirs:
            spreads.append(len(dirs))
    revert_re = re.compile(r"^\s*revert\b|\breverts?\b", re.I)
    fix_re = re.compile(r"^\s*(fix|bugfix|hotfix)(\(.+?\))?!?:|^\s*fix(es|ed)?\s", re.I)
    reverts = [f"{sha} {s}" for sha, s, _ in commits if revert_re.search(s)]
    result = {
        "available": True,
        "head": head,
        "branch": branch,
        "default_branch": origin_head.split("/", 1)[-1] if origin_head else None,
        "remote": remote,
        "shallow": shallow,
        "window_days": since_days,
        "commits": len(commits),
        "hotspots": [{"path": p, "commits": c, "share": round(c / len(commits), 2)} for p, c in touched.most_common(20)] if commits else [],
        "dir_spread": {
            "median": statistics.median(spreads),
            "p90": sorted(spreads)[int(0.9 * (len(spreads) - 1))],
            "commits_with_source": len(spreads),
        } if spreads else {},
        "reverts": {"count": len(reverts), "subjects": reverts[:20]},
        "fix_commits": sum(1 for _, s, _ in commits if fix_re.search(s)),
    }
    result["added_comments"] = added_comments(root, since_days, min(max_commits, 300))
    return result


def added_comments(root, since_days, max_commits, max_lines=400_000):
    pathspecs = [f"*{e}" for e in sorted(SOURCE_EXTS)]
    cmd = ["git", "-C", root, "log", f"--since={since_days}.days", "--no-merges", f"--max-count={max_commits}",
           "-p", "--unified=0", "--no-color", "--no-ext-diff", "--pretty=format:%x1e%h", "--", *pathspecs]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, errors="replace")
    except OSError:
        return {}
    added = comments = processed = 0
    samples, cur_path, style, truncated = [], None, None, False
    for line in proc.stdout:
        processed += 1
        if processed > max_lines:
            truncated = True
            proc.kill()
            break
        if line.startswith("+++ "):
            p = line[4:].strip()
            cur_path = p[2:] if p.startswith("b/") else p
            style = None if (is_ignored(cur_path) or is_generated(cur_path)) else SOURCE_EXTS.get(ext_of(cur_path))
            continue
        if not line.startswith("+") or style is None:
            continue
        body = line[1:].strip()
        if not body:
            continue
        added += 1
        if style == "c":
            is_comment = body.startswith(("//", "/*", "*/", "* ")) or body == "*" or body.startswith("<!--")
        else:
            is_comment = body.startswith("#") and not body.startswith("#!")
        if not is_comment or DIRECTIVE.search(body):
            continue
        comments += 1
        if len(samples) < 20 and NARRATION.search(body):
            samples.append({"path": cur_path, "text": body[:160]})
    proc.wait()
    return {
        "added_lines": added,
        "comment_lines": comments,
        "comment_share": round(comments / added, 3) if added else 0,
        "narration_samples": samples,
        "truncated": truncated,
    }


def parse_github_remote(url):
    m = re.match(r"(?:git@github\.com:|ssh://git@github\.com/|https?://(?:[^@/]+@)?github\.com/)([^/]+)/([^/]+?)(?:\.git)?/?$", url or "")
    return (m.group(1), m.group(2)) if m else None


def gh_api(path):
    code, out, err = run(["gh", "api", path], timeout=45)
    if code != 0:
        return None, (err or out).strip()[:240]
    try:
        return json.loads(out), None
    except ValueError:
        return None, "unparseable response"


def section_github(remote, out_dir, pages):
    result = {"available": False}
    if not shutil.which("gh"):
        result["error"] = "gh CLI not found"
        return result
    parsed = parse_github_remote(remote)
    if not parsed:
        result["error"] = f"origin is not a GitHub remote ({remote or 'none'})"
        return result
    owner, repo = parsed
    info, err = gh_api(f"repos/{owner}/{repo}")
    if err:
        result["error"] = err
        return result
    branch = info.get("default_branch")
    result.update({"available": True, "repo": f"{owner}/{repo}", "default_branch": branch, "visibility": info.get("visibility")})

    rules, err = gh_api(f"repos/{owner}/{repo}/rules/branches/{branch}")
    if err:
        result["rules_error"] = err
    else:
        required, types, reviews = [], [], None
        for r in rules or []:
            types.append(r.get("type"))
            params = r.get("parameters") or {}
            if r.get("type") == "required_status_checks":
                required += [c.get("context") for c in params.get("required_status_checks", [])]
            if r.get("type") == "pull_request":
                reviews = params.get("required_approving_review_count")
        result["rules"] = {"types": sorted(set(t for t in types if t)), "required_status_checks": required, "required_reviews": reviews}

    prot, err = gh_api(f"repos/{owner}/{repo}/branches/{branch}/protection")
    if err:
        result["protection_error"] = err
    else:
        rsc = prot.get("required_status_checks") or {}
        contexts = rsc.get("contexts") or [c.get("context") for c in rsc.get("checks", [])]
        result["protection"] = {
            "required_status_checks": contexts,
            "strict_up_to_date": rsc.get("strict"),
            "enforce_admins": (prot.get("enforce_admins") or {}).get("enabled"),
            "required_reviews": (prot.get("required_pull_request_reviews") or {}).get("required_approving_review_count"),
            "allow_force_pushes": (prot.get("allow_force_pushes") or {}).get("enabled"),
        }

    comments = []
    for page in range(1, pages + 1):
        batch, err = gh_api(f"repos/{owner}/{repo}/pulls/comments?per_page=100&sort=created&direction=desc&page={page}")
        if err:
            result["review_comments_error"] = err
            break
        for c in batch or []:
            user = c.get("user") or {}
            comments.append({
                "body": (c.get("body") or "")[:2000],
                "path": c.get("path"),
                "author": user.get("login"),
                "author_type": user.get("type"),
                "created_at": c.get("created_at"),
                "url": c.get("html_url"),
            })
        if not batch or len(batch) < 100:
            break
    summary = {
        "count": len(comments),
        "bot_count": sum(1 for c in comments if c["author_type"] == "Bot" or (c["author"] or "").endswith("[bot]")),
        "oldest": comments[-1]["created_at"] if comments else None,
    }
    if out_dir and comments:
        path = os.path.join(out_dir, "review-comments.json")
        with open(path, "w") as f:
            json.dump(comments, f, indent=1)
        summary["file"] = path
    result["review_comments"] = summary
    return result


# ---------------------------------------------------------------- summary


def print_summary(d):
    p = print
    g = d.get("git") or {}
    p(f"Repo: {d['root']}  head={g.get('head')}  branch={g.get('branch')}  default={g.get('default_branch')}")
    p(f"Files scanned: {d['files_scanned']}{' (truncated)' if d['files_truncated'] else ''}")
    p("Languages: " + ", ".join(f"{k} {v}" for k, v in d["languages"].items()))
    tools = d["tooling"]["tools"]
    p("Guardrail tools: " + (", ".join(tools) or "none found"))
    for rel, s in d["tooling"]["package_scripts"].items():
        p(f"  scripts in {rel}: " + ", ".join(s))
    for rel, s in d["tooling"]["make_targets"].items():
        p(f"  targets in {rel}: " + ", ".join(s))
    ts = d.get("typescript") or []
    if ts:
        strict = sum(1 for t in ts if t.get("strict"))
        p(f"tsconfigs: {len(ts)} ({strict} with strict set directly or via relative extends)")
    if d.get("python_typing"):
        p("Python typing: " + json.dumps(d["python_typing"]))
    ci = d["ci"]
    soft = [s for f in ci["files"] for s in f["soft_fail"]]
    p(f"CI files: {len(ci['files'])}, soft-fail patterns: {len(soft)}, scheduled workflows: {len(ci['scheduled'])}")
    for s in soft[:10]:
        p(f"  soft-fail {s['path']}:{s['line']}: {s['text']}")
    ai = d["agent_instructions"]
    for f in ai["files"]:
        p(f"Agent file {f['path']}: {f['lines']} lines, {f['imperative_rules']} imperative rules, rule table={f['has_rule_table']}")
    if ai["project_skills"]:
        p("Project skills: " + ", ".join(ai["project_skills"]))
    for c in d["codeowners"]:
        p(f"CODEOWNERS {c['path']}: {c['rules']} rules, catch-all={c['catch_all']}, gate-config patterns={c['gate_config_patterns']}")
    sup = d["suppressions"]
    p(f"Suppressions: {sup['total']} (with reason {sup['with_reason']}, with expiry {sup['with_expiry']})")
    for k, v in sorted(sup["by_pattern"].items(), key=lambda kv: -kv[1]["count"]):
        p(f"  {k}: {v['count']}  top: {', '.join(v['top_files'][:3])}")
    if d["escape_hatches"]:
        p("Escape hatches: " + ", ".join(f"{k} {v}" for k, v in d["escape_hatches"].items()))
    st = d["structure"]
    p(f"Source files: {st['source_files']}, >1000 lines: {st['over_1000']}, >3000 lines: {st['over_3000']}")
    for f in st["largest_files"][:8]:
        p(f"  {f['lines']:>6}  {f['path']}")
    if g.get("available"):
        p(f"Git window: {g['window_days']} days, {g['commits']} commits{' (shallow clone)' if g.get('shallow') else ''}")
        for h in g["hotspots"][:8]:
            p(f"  hotspot {h['commits']:>4} ({h['share']:.0%})  {h['path']}")
        if g.get("dir_spread"):
            p(f"Dirs touched per commit: median {g['dir_spread']['median']}, p90 {g['dir_spread']['p90']}")
        p(f"Reverts: {g['reverts']['count']}, fix commits: {g['fix_commits']}")
        ac = g.get("added_comments") or {}
        if ac:
            p(f"Added comment lines: {ac['comment_lines']} of {ac['added_lines']} ({ac['comment_share']:.1%}), narration samples: {len(ac['narration_samples'])}")
    gh = d.get("github")
    if gh is not None:
        if gh.get("available"):
            req = (gh.get("rules") or {}).get("required_status_checks", []) + (gh.get("protection") or {}).get("required_status_checks", [])
            p(f"GitHub {gh['repo']}: default={gh['default_branch']}, required checks={sorted(set(req)) or 'none found'}")
            for k in ("rules_error", "protection_error", "review_comments_error"):
                if gh.get(k):
                    p(f"  {k}: {gh[k]}")
            rc = gh.get("review_comments") or {}
            p(f"  review comments: {rc.get('count', 0)} ({rc.get('bot_count', 0)} bots), oldest {rc.get('oldest')}")
        else:
            p(f"GitHub: unavailable ({gh.get('error')})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--out-dir", help="directory for discover.json and review-comments.json")
    ap.add_argument("--summary", action="store_true", help="print a short digest")
    ap.add_argument("--since-days", type=int, default=90)
    ap.add_argument("--max-commits", type=int, default=500)
    ap.add_argument("--max-files", type=int, default=60000)
    ap.add_argument("--github", action="store_true", help="read rulesets, protection, and review comments via gh")
    ap.add_argument("--comment-pages", type=int, default=3, help="pages of 100 review comments to fetch")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    top = git(root, "rev-parse", "--show-toplevel")
    if top:
        root = top.strip()
    if not os.path.isdir(root):
        sys.exit(f"not a directory: {root}")
    if args.out_dir:
        os.makedirs(args.out_dir, exist_ok=True)

    files, truncated = list_files(root, args.max_files)
    suppressions, hatches, structure = section_source_scan(root, files)
    data = {
        "root": root,
        "files_scanned": len(files),
        "files_truncated": truncated,
        "languages": section_languages(files),
        "manifests": section_manifests(files),
        "tooling": section_tooling(root, files),
        "typescript": section_typescript(root, files),
        "python_typing": section_python_typing(root, files),
        "rust": section_rust(root, files),
        "ci": section_ci(root, files),
        "agent_instructions": section_agent_instructions(root, files),
        "codeowners": section_codeowners(root, files),
        "suppressions": suppressions,
        "escape_hatches": hatches,
        "structure": structure,
        "git": section_git(root, args.since_days, args.max_commits),
    }
    if args.github:
        data["github"] = section_github(data["git"].get("remote"), args.out_dir, args.comment_pages)

    if args.out_dir:
        path = os.path.join(args.out_dir, "discover.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        if not args.summary:
            print(f"Wrote {path}")
    elif not args.summary:
        json.dump(data, sys.stdout, indent=2)
        print()
    if args.summary:
        print_summary(data)


if __name__ == "__main__":
    main()
