"""Shared constants and helpers for establish-feature-map & maintain-feature-map. Stdlib only."""
import os
import re
import subprocess

MAP_DIR_NAME = "agent-map"

IGNORE_DIRS = {
    ".git", "node_modules", "vendor", "dist", "build", "out", "target", ".next",
    ".nuxt", ".svelte-kit", ".turbo", ".cache", "__pycache__", ".venv", "venv",
    ".tox", "coverage", ".pytest_cache", ".mypy_cache", ".idea", ".vscode", "obj",
    ".terraform", ".gradle", "Pods", "DerivedData", ".dart_tool", ".parcel-cache",
    "storybook-static", ".serverless", ".expo", "tmp", "temp", "logs",
}

GENERATED_DIRS = {"generated", "gen", "__generated__"}
FIXTURE_DIRS = {"fixtures", "__fixtures__", "snapshots", "__snapshots__", "testdata", "__mocks__"}

SURFACE_DIR_HINTS = {
    "features", "modules", "pages", "app", "routes", "controllers", "handlers",
    "endpoints", "api", "cmd", "commands", "cli", "views", "screens", "workflows",
    "workers", "jobs", "consumers", "lambdas", "functions", "services", "graphql",
    "grpc", "trpc", "routers",
}

MANIFEST_FILES = {
    "package.json": "node", "deno.json": "deno", "deno.jsonc": "deno",
    "go.mod": "go",
    "pyproject.toml": "python", "setup.py": "python", "requirements.txt": "python",
    "Pipfile": "python",
    "Cargo.toml": "rust",
    "pom.xml": "jvm", "build.gradle": "jvm", "build.gradle.kts": "jvm",
    "settings.gradle": "jvm", "settings.gradle.kts": "jvm",
    "Gemfile": "ruby", "composer.json": "php", "mix.exs": "elixir",
    "pubspec.yaml": "dart", "Package.swift": "swift", "CMakeLists.txt": "c-cpp",
    "Dockerfile": "container", "serverless.yml": "serverless", "serverless.yaml": "serverless",
    "main.tf": "terraform", "Chart.yaml": "helm",
}
MANIFEST_GLOBS = [
    (re.compile(r".*\.csproj$"), "dotnet"),
    (re.compile(r".*\.fsproj$"), "dotnet"),
    (re.compile(r".*\.sln$"), "dotnet"),
    (re.compile(r".*\.xcodeproj$"), "xcode"),
    (re.compile(r"docker-compose.*\.ya?ml$"), "compose"),
]
MONOREPO_MARKERS = {
    "pnpm-workspace.yaml", "lerna.json", "nx.json", "turbo.json",
    "rush.json", "go.work", "Cargo.toml",
}

SOURCE_EXTS = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte", ".astro",
    ".py", ".go", ".rs", ".java", ".kt", ".kts", ".scala", ".cs", ".fs", ".rb",
    ".php", ".ex", ".exs", ".dart", ".swift", ".m", ".mm", ".c", ".cc", ".cpp", ".h",
    ".hpp", ".sql", ".prisma", ".graphql", ".gql", ".proto", ".tf", ".hcl", ".sh",
    ".bash", ".zsh", ".ps1", ".lua", ".clj", ".erl", ".hs", ".ml", ".r", ".jl",
    ".html", ".css", ".scss", ".sass", ".less", ".yaml", ".yml", ".toml", ".json",
}

# Matches:
# <!-- agent-map v2 | Last linted: abc1234 | Scope: agent-map -->
# <!-- agent-map v2 | Last linted: abc1234 | Paths: apps/web/src/auth, apps/api/src/auth -->
README_META_RE = re.compile(
    r"<!--\s*agent-map\s+v(\d+)\s*\|\s*Last linted:\s*(\S+)\s*\|\s*Scope:\s*([^\s>]+)\s*-->"
)
FEATURE_META_RE = re.compile(
    r"<!--\s*agent-map\s+v(\d+)\s*\|\s*Last linted:\s*(\S+)\s*\|\s*Paths:\s*(.+?)\s*-->"
)

BLOCK_START = "<!-- agent-map:start -->"
BLOCK_END = "<!-- agent-map:end -->"

README_REQUIRED_H2 = [
    "## Stack & architecture at a glance",
    "## Baseline & verification harness",
    "## Features (regression sweep order)",
    "## Common tasks → start here",
    "## Global gotchas",
    "## Notes",
]

FEATURE_REQUIRED_H2 = [
    "## Sub-features",
    "## How to reach it (user / caller POV)",
    "## Driving & verifying it",
    "## Code touchpoints & dependencies",
    "## Gotchas (what usually lies)",
    "## Notes",
]


def git(root, *args):
    try:
        out = subprocess.run(
            ["git", "-C", root, *args], capture_output=True, text=True, timeout=30
        )
        if out.returncode != 0:
            return None
        return out.stdout
    except (OSError, subprocess.TimeoutExpired):
        return None


def git_toplevel(path):
    out = git(path, "rev-parse", "--show-toplevel")
    return out.strip() if out else None


def git_short_sha(root):
    out = git(root, "rev-parse", "--short", "HEAD")
    return out.strip() if out else "nogit"


def is_ignored_path(rel):
    parts = [p for p in rel.replace("\\", "/").split("/") if p and p != "."]
    return any(p in IGNORE_DIRS for p in parts)


def list_files(root):
    """Return relative file paths (tracked + untracked, excluding gitignored and IGNORE_DIRS)."""
    out = git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    files = []
    if out is not None:
        for p in out.split("\0"):
            if p and not is_ignored_path(p) and os.path.isfile(os.path.join(root, p)):
                files.append(p.replace(os.sep, "/"))
        return sorted(set(files))
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        rel_dir = os.path.relpath(dirpath, root)
        for f in filenames:
            rel = f if rel_dir == "." else os.path.join(rel_dir, f)
            files.append(rel.replace(os.sep, "/"))
    return sorted(set(files))


def manifest_label(filename):
    if filename in MANIFEST_FILES:
        return MANIFEST_FILES[filename]
    for rx, label in MANIFEST_GLOBS:
        if rx.match(filename):
            return label
    return None


def parse_feature_meta(text):
    """Parse line-3 metadata from a feature file."""
    head = "\n".join(text.splitlines()[:6])
    m = FEATURE_META_RE.search(head)
    if not m:
        return None
    raw_paths = [p.strip().rstrip("/") for p in m.group(3).split(",") if p.strip()]
    return {
        "version": m.group(1),
        "sha": m.group(2),
        "paths": raw_paths,
    }


def parse_readme_meta(text):
    head = "\n".join(text.splitlines()[:6])
    m = README_META_RE.search(head)
    if not m:
        return None
    return {
        "version": m.group(1),
        "sha": m.group(2),
        "scope": m.group(3),
    }


def extract_notes_section(text):
    """Return content under ## Notes so it can be preserved verbatim."""
    marker = "\n## Notes"
    idx = text.find(marker)
    if idx == -1:
        return None
    return text[idx + 1:]


def changed_files_since(root, sha, paths=None):
    """Return list of changed files (committed since sha + uncommitted working tree) under paths.
    Returns None if sha is unknown/unverifiable."""
    if not sha or sha == "nogit":
        return None
    if git(root, "cat-file", "-e", f"{sha}^{{commit}}") is None:
        return None
    cmd = ["diff", "--name-only", sha, "--"]
    if paths:
        cmd.extend(paths)
    out = git(root, *cmd)
    if out is None:
        return None
    changed = {
        line.strip()
        for line in out.splitlines()
        if line.strip() and not line.strip().startswith(f"{MAP_DIR_NAME}/")
    }
    # Also include untracked files under those paths
    untracked_cmd = ["ls-files", "--others", "--exclude-standard", "--"]
    if paths:
        untracked_cmd.extend(paths)
    untracked = git(root, *untracked_cmd)
    if untracked:
        for line in untracked.splitlines():
            p = line.strip()
            if p and not p.startswith(f"{MAP_DIR_NAME}/") and not is_ignored_path(p):
                changed.add(p)
    return sorted(changed)
