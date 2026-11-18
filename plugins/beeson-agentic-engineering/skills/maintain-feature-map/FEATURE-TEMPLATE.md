# agent-map Templates (`README.md` + `<feature>.md`)

Every repository's feature map lives in `<repo-root>/agent-map/`, checked into source control.

```text
agent-map/
├── README.md                  # Stack overview, harness baseline, regression sweep index, task router
├── <feature-slug>.md          # One file per user-facing feature or core service flow
└── ...
```

Follow both templates exactly. `validate.py` checks section headings, ordering, metadata comments, tracked paths, and link integrity.

---

## 1. `agent-map/README.md` Template

````markdown
# <App / Repo Name> — Agent Feature Map

<!-- agent-map v2 | Last linted: <short-git-sha> | Scope: agent-map -->

<2–4 sentences describing what this product/repository is, who uses or calls it, and its primary surfaces (Web UI, API, CLI, Workers, Mobile, etc.).>

## Stack & architecture at a glance

- **Languages & runtimes:** <e.g., TypeScript (Node 22), Python 3.12, Go 1.23>
- **Apps & services:**
  - `<path>` — <role, framework, how it runs>
  - `<path>` — <role, framework, how it runs>
- **Shared foundations / packages:**
  - `<path>` — <what it provides and who depends on it>
- **Data & external state:** <Postgres/Prisma in `packages/db`, Redis streams, S3, third-party APIs>
- **How pieces communicate:** <e.g., browser → `apps/web` (Next.js) → `apps/api` (Fastify REST) → `services/worker` (BullMQ)>

## Baseline & verification harness

- **Install / setup:** `<command>`
- **Start local stack:** `<command>` (ready when: `<observable log line, health URL, or prompt>`)
- **Verification skill / harness:** <path to `.cursor/skills/run-verification-rig/SKILL.md` if present, or primary E2E/integration test runner command such as `pnpm test:e2e`, `pytest`, `go test ./...`>
- **Fast static checks:** `<typecheck / lint / unit test command>`

## Features (regression sweep order)

Ordered top-to-bottom so a verification pass can exercise prerequisites (e.g., auth, onboarding, core entity creation) before downstream features. Open **only** the feature file needed for your current task.

| # | Feature | User / Caller Surface | Key Code Paths |
|---|---------|-----------------------|----------------|
| 1 | [Auth & Sessions](./auth-and-sessions.md) | `/login`, `POST /api/auth/*`, `cli login` | `apps/web/src/features/auth`, `apps/api/src/auth` |
| 2 | [Create & Manage Notes](./notes-crud.md) | `/notes`, `notes create`, `POST /api/notes` | `apps/web/src/features/notes`, `apps/api/src/notes` |

## Common tasks → start here

| If asked to... | Open first | Then check |
|----------------|------------|------------|
| Add or modify a user-facing feature | Matching file in `Features` above | Its `Code touchpoints` & `Gotchas` |
| Change database schema / migrations | `<feature or foundation file>` | `<schema path + codegen command>` |
| Add a new API route or webhook | `<feature file>` | `<router entry file>` |
| Debug CI / build / deploy | `<infra or root config path>` | `<workflow path>` |

## Global gotchas

- <Repo-wide trap that affects multiple features: generated code, required env vars, build ordering, shared state.>

## Notes
<!-- Human-maintained. The linter preserves this section verbatim. -->
````

---

## 2. `agent-map/<feature-slug>.md` Template

File name must be `kebab-case.md` (lowercase letters, numbers, hyphens). Cap each feature file at **150 lines**.

Line 1 is the H1 title with an em dash (` — `).
Line 3 is the metadata comment with `Last linted: <sha>` and `Paths: <comma-separated repo-relative directories or files>`.

````markdown
# <Feature Name> — <one-line user-visible behavior, ≤ 14 words>

<!-- agent-map v2 | Last linted: <short-git-sha> | Paths: <path1>, <path2>, <path3> -->

<1 short paragraph (2–4 sentences) describing what this feature does from the user's or caller's perspective, and what it explicitly does NOT own.>

## Sub-features

- `<short-id>` — <one-line description of user/caller-visible capability>
- `<short-id>` — <one-line description>

## How to reach it (user / caller POV)

- **UI / Screen:** <route path, navigation menu item, button label, keyboard shortcut — or omit if no UI>
- **CLI / Command:** `<exact command and flags>` <— or omit if no CLI>
- **API / Webhook / Event:** `<METHOD /route/path>`, `<queue/topic name>`, or `<exported SDK function>` <— or omit if N/A>
- **Prerequisites / State:** <auth role, feature flag, seeded record, or env var required to reach it>

## Driving & verifying it

Preconditions:

- <App/service state or test environment required before driving>

- **<Action label>.** <What the user/caller does>. Run `<exact harness command, curl/CLI invocation, or targeted test command>`. Observable result: <what screen state, response payload, DB row, or test assertion proves it worked>.
- **<Edge / cancellation / persistence check>.** <Second step proving state persisted or error handled>. Run `<command>`. Observable result: <proof>.

## Code touchpoints & dependencies

- **Entry points (UI / route / handler):**
  - `<path/to/file>` — <role>
- **Core logic & services:**
  - `<path/to/file_or_dir>` — <role>
- **State, schema & persistence:**
  - `<path/to/schema_or_store>` — <tables, models, caches, or queues touched>
- **Tests:**
  - `<path/to/test_file_or_dir>` — <unit / integration / e2e coverage>
- **Dependencies:**
  - Depends on features: [`<other-feature>.md`](./<other-feature>.md) (<why>)
  - Shared packages / external services: `<package or external API>` (<why it matters>)

## Gotchas (what usually lies)

- <Specific, verifiable runtime or code trap. Examples: "Saving returns 200 before the async indexer finishes; query `/api/status` or wait for job completion before asserting search results", "`schema.prisma` generates types via `pnpm db:gen`—never edit `generated/` directly".>
- <Another concrete trap.>

## Notes
<!-- Human-maintained. The linter preserves this section verbatim. -->
````

---

## Contract Rules Enforced by `validate.py`

1. **`agent-map/README.md` must exist** and have:
   - Line 1 H1 with ` — `
   - Line 3 metadata comment `<!-- agent-map v2 | Last linted: <sha> | Scope: agent-map -->`
   - Required H2s in order:
     1. `## Stack & architecture at a glance`
     2. `## Baseline & verification harness`
     3. `## Features (regression sweep order)`
     4. `## Common tasks → start here`
     5. `## Global gotchas`
     6. `## Notes`
   - Every sibling `agent-map/<feature>.md` file is linked in `## Features (regression sweep order)`, and no dead links exist.
2. **Every `agent-map/<feature>.md` must have:**
   - Line 1 H1 with ` — ` (purpose ≤ 14 words)
   - Line 3 metadata comment `<!-- agent-map v2 | Last linted: <sha> | Paths: <path1>, <path2> -->`
   - Every path in `Paths:` must exist in the repository (used by `drift.py` to detect staleness when code changes).
   - Required H2s in exact order:
     1. `## Sub-features`
     2. `## How to reach it (user / caller POV)`
     3. `## Driving & verifying it`
     4. `## Code touchpoints & dependencies`
     5. `## Gotchas (what usually lies)`
     6. `## Notes`
   - ≤ 150 lines per feature file.
3. **`AGENTS.md` (and `CLAUDE.md` if present) at repo root** must contain the `<!-- agent-map:start --> ... <!-- agent-map:end -->` block referencing `agent-map/README.md`.
