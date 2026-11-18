---
name: interrogate
description: "Use for \"interrogate\", \"adversarial review\", \"multi-model review\", \"challenge this\", \"stress test this code\", \"find blind spots\", or \"tear this apart\". Independent LLM reviewers challenge changes from different angles."
disable-model-invocation: true
---

# Interrogate

Spawn reviewers to adversarially review code changes. The default panel uses three different models. Each reviewer gets the same prompt and rubric. The adversarial signal comes from model diversity, not assigned personas.

The deliverable is a synthesized verdict. Do NOT auto-apply changes.

## Step 1, Determine Scope

Identify what to review from context:

- If the user points at specific files or a diff, use that
- If on a feature branch, run `git diff main...HEAD` (or the appropriate base branch) to get the full changeset
- If the user's message references recent work, gather the relevant files

Collect the material into a clear package: the diff (or file contents), and any surrounding context files the reviewers will need to understand the code.

## Step 2, State the Intent

Before spawning reviewers, state the intent explicitly. Derive this from:

- The user's message
- Commit messages
- PR description if one exists
- The code itself

Write one clear paragraph. If you're unsure about the intent, ask the user before proceeding.

## Step 3, Spawn Reviewers

Launch all reviewers in a single message using the Task tool. Use the `interrogate reviewers` line in `~/.cursor/rules/lauren-mode-models.mdc`, one reviewer per entry, extending or shrinking the Reviewer A/B/C labels below to the configured entry count. If the rule or that line is missing, use the table defaults. If the rule lacks the `# lauren-mode model overrides` header, still use its lines and tell the user once to rerun `/setup-lauren-mode`. All reviewers get the same prompt built from the template in `references/reviewer-prompt.md`. Pick each subagent's reasoning level and fast or standard speed for the job, per the Subagents section of `.cursor/skills/lauren/lauren-mode/SKILL.md`.

| Subagent | Default model |
|----------|---------------|
| Reviewer A | `claude-opus-5-5-xhigh-fast` |
| Reviewer B | `gpt-5.6-sol-max` |
| Reviewer C | `grok-4.7-xhigh-fast` |

For each reviewer:
- `subagent_type`: `generalPurpose`
- `model`: the configured `interrogate reviewers` entry, or the table default with no configured line. For an `auto` or `inherit-parent` entry, omit `model` so that reviewer runs on the parent model.
- `readonly`: `true`

If the Task tool rejects a configured entry, run that reviewer on the table default of its family and say so. Families go by prefix: `claude-*`, `gpt-*`, and `grok-*` with `cursor-grok-*` and `composer-*`. With no family match, use Reviewer A's default. If it rejects a table default, check the valid slugs in the Task tool's error message, pick the closest equivalent (prefer the highest-reasoning tier of the same family), spawn with it, and open a separate PR to update the default table. Do not block the review on the slug issue.

Read `references/reviewer-prompt.md` and fill in the template with:
1. The stated intent
2. The diff or file contents
3. The review rubric from `references/rubric.md`
4. The code-quality lens from `references/code-quality-review.md`

Fill in the same template for every reviewer, so each one applies the code-quality lens alongside the rubric.

## Step 4, Synthesize

As reviewer results come back, build a unified picture:

1. **Parse all findings** from every reviewer
2. **Identify consensus**. Findings raised by 2+ models independently are highest signal.
3. **Identify lone-model findings**. Still worth reading, but weight accordingly.
4. **Deduplicate**. Different models may describe the same issue differently. Merge these and note which models raised it.
5. **Note disagreements**. If one model flags something and another explicitly says the opposite, that's useful context for the verdict.

## Step 5, Lead Judgment

You are the lead reviewer, a pragmatic senior engineer, not a neutral aggregator.

Read `references/lead-judgment.md` for the full framework.

Categorize every finding into one of four buckets:

- **Act on**. Real issues affecting correctness, security, or maintainability given the actual goals. These would block a real PR.
- **Consider**. Legitimate points, but you're not sure they outweigh the cost of addressing them right now. Worth the user's attention.
- **Noted**. Technically valid but not actionable. Context-dependent, premature optimization, or low-impact given the current stage.
- **Dismissed**. Wrong, nitpicky, or missing context. Brief explanation why.

For each finding, include:
- Which model(s) raised it
- The category (act on / consider / noted / dismissed)
- A one-line rationale for the categorization

## Output Format

Present the verdict in this structure:

### Intent
> [The stated intent paragraph from Step 2]

### Reviewers
- Reviewer [label]: [model name], [N findings] (one bullet per reviewer)

### Act On
[Findings that should be addressed. For each: description, which models raised it, why it matters.]

### Consider
[Findings worth thinking about. For each: description, which models raised it, tradeoff involved.]

### Noted
[Valid but low-priority. Brief list.]

### Dismissed
[Rejected findings with brief rationale.]

### Agreement Map
[Where did models agree? Where did they diverge? What does the pattern of agreement/disagreement tell us?]
