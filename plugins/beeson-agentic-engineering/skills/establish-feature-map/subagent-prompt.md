# Subagent Prompt Template (Feature Tracer)

Use this template when spawning parallel subagents via `Task` (`subagent_type: generalPurpose`). Assign 1–3 closely related features per subagent so each subagent can deeply trace code and write accurate `agent-map/<feature>.md` files.

````text
You are tracing and writing feature map files in `agent-map/` for the `establish-feature-map` skill.

Repository root: {{REPO_ROOT}}
Git SHA to stamp as "Last linted": {{SHORT_SHA}}
Existing verification skill / harness (if any): {{VERIFY_SKILL_OR_TEST_HARNESS}}

Read these two files first and follow them strictly:
1. Template & contract: {{SKILL_DIR}}/FEATURE-TEMPLATE.md
2. Discovery & slicing guide: {{SKILL_DIR}}/feature-discovery-guide.md

You are responsible for writing the following feature file(s) in `{{REPO_ROOT}}/agent-map/`:
{{FEATURE_ASSIGNMENTS}}
Example:
- `agent-map/auth-and-sessions.md`
  - Candidate scope / paths: `apps/web/src/features/auth`, `apps/api/src/modules/auth`, `e2e/auth.spec.ts`
  - Existing `## Notes` to preserve verbatim: {{NOTES_OR_NONE}}

Procedure for each assigned feature:
1. Trace the feature end-to-end from the caller/user entry point (UI route/component, CLI command, API endpoint, or worker trigger) through handlers/services down to state/database schemas and tests.
2. Verify every path you cite. Never guess filenames, route paths, CLI flags, or npm/make scripts.
3. Identify how to drive and verify the feature:
   - If the repo has a verification skill (e.g., `.cursor/skills/verify-*/SKILL.md`), use its harness conventions and cross-check any existing `.cursor/skills/verify-*/features/*.md` recipes.
   - Otherwise, document concrete CLI/curl commands, UI steps with stable selectors/roles, or targeted integration/E2E test commands (`pnpm test ...`, `pytest ...`, `go test ...`) and the observable result that proves it works.
4. Document specific, verifiable Gotchas ("what usually lies"): async delays, generated files that must not be hand-edited, required seed/env state, caching traps, or misleading status responses.
5. Set the line 3 metadata comment `Paths:` to the comma-separated list of repo-relative directories/files that implement or test this feature. Every listed path must exist.
6. Keep each file ≤ 150 lines and follow the exact H2 section names and order from `FEATURE-TEMPLATE.md`.
7. Preserve any existing `## Notes` content verbatim.
8. Run:
   `python3 {{SKILL_DIR}}/scripts/validate.py {{REPO_ROOT}} --only {{FEATURE_FILE_REL_PATHS}}`
   Fix any contract, path, or link errors in your assigned files before finishing. (Ignore a warning that `agent-map/README.md` doesn't index your file yet—the coordinator writes `README.md` after all subagents return.)

Return a concise digest for each feature file in this exact format:

FEATURE_FILE: agent-map/<slug>.md
TITLE: <Feature Name> — <one-line purpose>
SURFACES: <routes, CLI commands, endpoints, or triggers>
PATHS: <comma-separated repo paths in header>
DEPENDS_ON_FEATURES: <other feature slugs or none>
TOP_GOTCHA: <one sentence>
VALIDATION: <clean | errors>
UNCERTAIN: <anything ambiguous or potentially broken in product code, or none>
````
