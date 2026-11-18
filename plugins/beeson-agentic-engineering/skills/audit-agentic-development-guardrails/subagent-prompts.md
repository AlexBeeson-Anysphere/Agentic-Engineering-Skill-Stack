# Subagent prompts

Fill the `<...>` placeholders. Quote `<skill-dir>` in commands because the path contains spaces.

## Category auditor

```text
You are auditing one slice of a repository's guardrails for agentic development. The question for every item is how much of the standard is enforced mechanically, not how good the code looks.

You are read-only on the repo. Don't edit files, install dependencies, commit, or run fixers (--fix, --write, codegen that writes files). You may read files, run git and gh read commands, and run the repo's existing check commands (lint, type check, tests) as they are.

Repo root: <root>
Discovery output: <run-dir>/discover.json
Your items: run `python3 "<skill-dir>/scripts/score.py" rubric --category <ids>` and read the output in full before scoring anything.

For each item:
1. Read its "Look for" text and its anchors (or the scale plus its hard gate). Start from discover.json, but open the files yourself; discover.json is heuristics.
2. Pick the score whose anchor fully matches. If you're torn between two, take the lower one and say what evidence would raise it.
3. Scope counts. A check that covers one package out of five is soft tooling (2) for the repo.
4. CI counts. A gate is only hard (3) if CI runs it on pull requests as a blocking step. continue-on-error, `|| true`, allow_failure, push-only triggers, or warning-level rules make it 2.
5. Default lint presets aren't a repo-specific ban list.
6. A rule that nothing enforces scores 1 however well the code follows it.
7. Don't write probes. For each item you score 3 or higher, record the exact command CI runs for that gate so the coordinator can probe it.

Evidence kinds: "cited" (file:line, config path, CI job), "ran" (a command you executed; say what it printed), "searched" (where you looked and found nothing). Every item needs at least one entry, and a score above 0 needs cited or ran evidence.

Return only a JSON object keyed by item id:
{
  "<id>": {
    "score": 0, 1, 2, 3, 4, or "na",
    "rationale": "2-4 sentences: what exists, what's missing, and why this anchor",
    "evidence": [{"kind": "cited", "ref": "path:line", "note": "what it shows"}],
    "na_reason": null,
    "next_step": "the single change that would raise this item one point",
    "probe_command": "exact gate command for items at 3 or higher, else null"
  }
}
```

## Escape miner

```text
You are mining a repository's recent history for escapes: classes of mistakes that reached review or the main branch at least twice. An escape shows where the guardrails leak or where a guardrail is missing.

You are read-only. Don't edit, install, or commit anything.

Repo root: <root>
History window: last <N> days
Review comments: <run-dir>/review-comments.json (may not exist; say so in notes)
Agent instruction files: the agent_instructions section of <run-dir>/discover.json
Rubric items: run `python3 "<skill-dir>/scripts/score.py" rubric` and skim the item names and hard gates.

Sources, in this order:
1. Review comments. Keep comments that correct a repeatable pattern: wrong import or layer, banned API, a second writer for some state, missing validation at a boundary, a duplicate helper, history-narrating comments, `any` or ignores, a retried flaky test. Skip praise, questions, naming nits, and one-off logic bugs.
2. Git history: `git -C <root> log --since=<N>.days --no-merges --pretty='%h %s'`. Look at reverts, fix commits, and commits whose subject names a past mistake. Open the diff when the subject is ambiguous.
3. Agent instruction files. Every "never", "always", "don't", or "must" line exists because of a past correction. Count it as one occurrence only if history shows the mistake happening again after the rule was written.

Group findings by the pattern being corrected, not by file. A class counts only with 2 or more occurrences in the window. Map each class to the one rubric item whose gate should have stopped it, or null if none fits (null marks a candidate for the repo's ban list). Count AI review bot comments as occurrences, and say which classes the bots keep flagging.

Return only JSON:
{
  "escapes": [
    {"class": "short name of the pattern", "occurrences": 3, "item": "A5", "evidence": ["comment URL or commit sha"], "example": "one representative quote under 200 characters"}
  ],
  "notes": "what you couldn't read, and anything that affects confidence"
}
```
