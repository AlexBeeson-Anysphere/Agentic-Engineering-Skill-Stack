# Subagent Prompt Template (Feature Drift Auditor)

Use this template when spawning parallel subagents via `Task` (`subagent_type: generalPurpose`) during `maintain-feature-map`. Only dispatch subagents for features that are `STALE`, `BROKEN_PATHS`, `INVALID_META`, or newly discovered from unmapped code churn.

````text
You are auditing and updating feature files in `agent-map/` for the `maintain-feature-map` skill.

Repository root: {{REPO_ROOT}}
Current HEAD git SHA (stamp as "Last linted" once verified): {{HEAD_SHA}}
Template & contract: {{SKILL_DIR}}/FEATURE-TEMPLATE.md

Assigned feature file(s):
{{FEATURE_DRIFT_ASSIGNMENTS}}
Example:
- `agent-map/billing-and-checkout.md`
  - Status: STALE (last linted at `a1b2c3d`)
  - Missing paths: `none`
  - Changed files since `a1b2c3d`: `apps/api/src/routes/billing.ts`, `apps/web/src/features/billing/CheckoutForm.tsx`
  - Existing `## Notes` to preserve verbatim: {{NOTES_CONTENT}}

Triage & Update Procedure:
1. Read the assigned `agent-map/<feature>.md` file and inspect the git diff (`git -C {{REPO_ROOT}} diff <last_sha> HEAD -- <paths>`) plus the current source files.
2. Classify every discrepancy you find into one of three buckets:
   - **Map drift:** Code was intentionally refactored, a route/command/flag changed, a sub-feature was added/removed, or paths moved. -> Update `agent-map/<feature>.md` (including `Paths:` in line 3) to match current truth.
   - **Verification / harness gap:** A test command, selector, precondition, or CLI flag in `## Driving & verifying it` is outdated. -> Update the recipe to match current source/tests.
   - **Suspected product regression:** The feature file describes user-facing behavior or wiring that disappeared or broke in code without an obvious replacement (e.g., a dead button, a dropped handler still called by the UI, a broken route). -> **Do NOT edit product code, and do NOT silently erase the broken behavior from the map.** Note it in your returned `PRODUCT_REGRESSIONS` digest so the coordinator reports it to the user.
3. Preserve the existing `## Notes` section verbatim.
4. Stamp `Last linted: {{HEAD_SHA}}` in line 3 once the file reflects current source.
5. Run:
   `python3 {{SKILL_DIR}}/scripts/validate.py {{REPO_ROOT}} --only {{FEATURE_FILE_REL_PATHS}}`
   and fix any contract, link, or path errors.

Return a concise digest for each assigned feature file in this exact shape:

FEATURE_FILE: agent-map/<slug>.md
OUTCOME: <updated | re-stamped-clean | created | needs-human-review>
MAP_DRIFT_FIXED: <bullet summary of doc/path/touchpoint updates, or none>
VERIFY_RECIPE_UPDATED: <bullet summary of recipe changes, or none>
RECOMMENDED_CHECK_CMD: <fast targeted test or doctor command the coordinator can run, or none>
PRODUCT_REGRESSIONS: <suspected product breakage discovered in code, or none>
VALIDATION: <clean | errors>
````
