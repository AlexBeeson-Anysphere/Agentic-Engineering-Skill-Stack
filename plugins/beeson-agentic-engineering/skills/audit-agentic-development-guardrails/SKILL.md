---
name: audit-agentic-development-guardrails
description: Audits how much of a repository's architecture standard is enforced mechanically for agentic development (Lauren Tan's structural guardrails: architecture, types, lint and CI gates, gate governance, and the escape feedback loop). Writes a report with a Level 0-4 ladder assessment and the reasons for it, a weighted rubric score across 35 items, escapes mined from review history, and a roadmap. Read-only on the target repo. Use for /audit-agentic-development-guardrails, guardrail audits, agent-readiness or architecture-drift scorecards, or assessing a customer codebase against Dune-style guardrails.
disable-model-invocation: true
---

# Audit Agentic Development Guardrails

Score how much of the repo's architecture standard is enforced mechanically, not how good the code looks. A rule nothing enforces scores 1, however well the code follows it. A rule CI blocks scores 3. A gate the repo proves still bites scores 4.

`$SKILL_DIR` is the directory containing this file. Quote it in every command, because the path contains spaces.

## How scoring works

- **Items.** `rubric.json` holds 35 items in six categories. Each scores 0 to 4 against anchored text. Items without their own anchors use the shared scale (Absent, Prose, Soft tooling, Hard gate, Proven gate), and their `hard_gate` text defines what a 3 means for that item.
- **Score.** Each category's score is the mean of its applicable items. The overall score weights the categories in Lauren's enforcement order: Architecture 30, Static analysis and CI 20, Gate system 20, Types 15, Behavior tests 10, Feedback loop 5. N/A items drop out, and the remaining items in that category absorb the weight.
- **Level.** The level comes from gate items only, never from the score. A repo can score 70% and still be Level 1 if nothing is a required check. Level 1 needs T1 or S1 at 2. Level 2 needs T1, S1, A4, and G2 at 3. Level 3 needs G1 and G3 through G6 at 3. Level 4 needs F1 and F2 at 3. Each level also needs every level below it.
- **Escapes.** A mistake class seen twice or more in the history window, mapped to an item scored above 2, caps that item at 2, because the gate leaks.

`score.py` does all of this arithmetic. Never compute totals or the level yourself. To change weights or gates, edit `rubric.json`; `score.py` checks the rubric on every run, including that weights sum to 100.

## Outputs

Everything goes in the run directory. The default is `<repo-root>/.guardrail-audit/<YYYYMMDD>-<short-sha>/`, unless the user names another location, such as a customer folder.

- `report.md`: the level, ladder, rubric score, roadmap, escapes, and item detail
- `scores.json`: item scores with evidence, which is the auditable source of the report
- `result.json`: computed totals, for tracking trends across runs
- `discover.json`, `review-comments.json`, `probes/`: raw evidence

## Hard rules

1. **Read-only on the target repo.** Write only to the run directory. Probes run in a throwaway worktree outside the repo, which you remove afterward. Never commit, push, install dependencies, or run fixers (`--fix`, `--write`, codegen that writes files).
2. **Score against the anchors.** No half points. When torn between two scores, take the lower one and put the evidence that would raise it in `next_step`.
3. **Every score needs evidence.** There are four kinds: `ran` (a command you executed, with output saved under `probes/`), `cited` (file:line, config path, CI job, or URL), `attested` (the operator told you; record who in `by`), and `searched` (where you looked and found nothing). `score.py` rejects scores whose evidence doesn't support them.
4. **N/A is rare.** Use it only when the item's `na_when` applies, and give a reason. An N/A gate item passes its gate, and the report flags it.
5. **Don't fix anything.** Recommendations go in `next_step`. Fixes come afterward, through pstack's `/correct`.

## Workflow

Copy this checklist into a todo list and track progress:

```text
- [ ] 1. Set up the run directory and run discovery
- [ ] 2. Mine escapes (subagent, in parallel with step 3)
- [ ] 3. Dispatch category auditors (subagents)
- [ ] 4. Reconcile scores and probe claimed hard gates
- [ ] 5. Fill scores.json, validate, and render the report
- [ ] 6. Reply with the outcome
```

### 1. Set up and discover

```bash
ROOT=<repo-root>
RUN="$ROOT/.guardrail-audit/$(date +%Y%m%d)-$(git -C "$ROOT" rev-parse --short HEAD)"
git -C "$ROOT" status --porcelain > /tmp/guardrail-status-before.txt
python3 "$SKILL_DIR/scripts/discover.py" "$ROOT" --out-dir "$RUN" --github --summary
python3 "$SKILL_DIR/scripts/score.py" template --repo "$ROOT" --out "$RUN/scores.json"
```

- If the GitHub section reports that the token can't read rulesets or branch protection, or the origin isn't on GitHub, ask the operator once, up front. Ask which status checks are required on the default branch, who can bypass them, how agent and CI credentials are scoped, and whether secret scanning blocks merges. Record the answers as `attested` evidence on G2 and S6.
- If the window holds fewer than about 30 commits, rerun discovery with a larger `--since-days` and use that window for escape mining.
- If `git.shallow` is true, add a limit noting that history signals are partial.
- For a very large monorepo, agree on a path scope with the user and record it in `scope`.

### 2. Mine escapes

Launch one `generalPurpose` subagent with the escape-miner prompt in [subagent-prompts.md](subagent-prompts.md). Use the same window as discovery, which defaults to 90 days. Launch it in the same message as the step 3 auditors. Paste the `escapes` it returns into `scores.json`, after checking that the evidence links resolve.

### 3. Dispatch category auditors

Launch four `generalPurpose` subagents in parallel with the category-auditor prompt in [subagent-prompts.md](subagent-prompts.md):

- `A`: architecture, 11 items
- `S`: static analysis and CI, 8 items
- `T,B`: types and behavior tests, 6 items
- `G,F`: gate system and feedback loop, 10 items

For a small repo (under about 50 source files), score the items yourself instead.

### 4. Reconcile and probe

Merge the returned entries into `scores.json` `items`. Then check them:

- **Spot-check.** For every gate item (T1, S1, A4, G1 through G6, F1, F2) and every item at 3 or higher, open at least one cited ref yourself.
- **Cross-check against discovery.** If a soft-fail pattern sits on the CI step that runs a gate, that gate can't score above 2. The same applies if the gate runs only on push and not on pull requests, or if its job isn't a required check.
- **Leave escape caps to the script.** `score.py` caps an item mapped to an escape. Don't lower the item yourself, but mention the escape in its rationale.

Next, probe each item without its own anchors that scored 3 or higher. Start with T1, S1, and A4, then do up to about eight more. Use one worktree for every probe:

```bash
WT=/tmp/guardrail-probe-$(basename "$RUN")
git -C "$ROOT" worktree add --detach "$WT" HEAD
ln -s "$ROOT/node_modules" "$WT/node_modules"   # link dependency dirs that exist (node_modules, .venv); never install
mkdir -p "$RUN/probes"
# Per probe: write the smallest violation the gate should catch (a cross-layer import, a banned call,
# an `any`, a file over the length limit), then run the exact command CI runs for that gate:
#   (cd "$WT" && <gate command>) > "$RUN/probes/<item>.txt" 2>&1; echo "exit $?" >> "$RUN/probes/<item>.txt"
# Reset between probes:
git -C "$WT" checkout -- . && git -C "$WT" clean -fd -e node_modules -e .venv
# After the last probe:
git -C "$ROOT" worktree remove --force "$WT" && git -C "$ROOT" worktree prune
```

Act on each probe result:

- **The gate fails as expected.** Add `ran` evidence. Its `ref` is the command and its `note` is the probe file path.
- **The gate passes.** It doesn't bite. Lower the item to 2 and say so in the rationale.
- **The probe can't run**, for example because of missing dependencies or required secrets, keep the score and add a limit. The report lists the item under unprobed hard gates.

Last, diff `git -C "$ROOT" status --porcelain` against `/tmp/guardrail-status-before.txt`. Nothing outside the run directory may have changed.

### 5. Fill, validate, render

Fill these top-level fields in `scores.json`:

- `summary`: two to four sentences covering the level, the biggest blocker, and the strongest existing guardrail
- `level_rationale`: why the repo sits at this level, citing gate items
- `auditor`
- `window`, for example "last 90 days"
- `limits`

Then run:

```bash
python3 "$SKILL_DIR/scripts/score.py" validate "$RUN/scores.json"
python3 "$SKILL_DIR/scripts/score.py" report "$RUN/scores.json" --discover "$RUN/discover.json" --out "$RUN/report.md" --json "$RUN/result.json"
```

Fix every validation error and rerun until there are 0 errors. Warnings about a missing `next_step` are worth fixing too, because the roadmap uses that field.

An item entry looks like this:

```json
"A4": {
  "score": 2,
  "rationale": "dependency-cruiser forbids web-to-api imports, but CI runs it with continue-on-error, so violations still merge.",
  "evidence": [
    {"kind": "cited", "ref": ".dependency-cruiser.cjs:12", "note": "no-web-to-api rule"},
    {"kind": "cited", "ref": ".github/workflows/ci.yml:48", "note": "continue-on-error: true on the depcruise step"}
  ],
  "na_reason": null,
  "next_step": "Remove continue-on-error from the depcruise step and add the job to required checks."
}
```

An escape entry looks like this:

```json
{"class": "Direct Prisma writes from route handlers", "occurrences": 4, "item": "A5", "evidence": ["https://github.com/org/repo/pull/812#discussion_r123", "abc1234"]}
```

### 6. Reply

Keep the reply short. Don't paste the report. Include:

- the level, its name, and one sentence on why
- the rubric score
- the top three roadmap items
- the escape count
- the report path
- caveats: unprobed gates, attested evidence, and N/A gate items

## Resources

- [rubric.json](rubric.json): the ladder, category weights, and all 35 items with what to look for and the anchors. It's the single source of truth. `score.py rubric` renders it as markdown.
- [subagent-prompts.md](subagent-prompts.md): prompts for the category auditors and the escape miner.
- `scripts/discover.py`: read-only inventory of guardrail signals (stdlib Python 3). It calls `gh` when `--github` is set.
- `scripts/score.py`: `template`, `rubric`, `validate`, and `report` (stdlib Python 3).
