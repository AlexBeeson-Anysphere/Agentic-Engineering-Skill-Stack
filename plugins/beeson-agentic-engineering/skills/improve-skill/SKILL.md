---
name: improve-skill
description: Improve an existing skill by proposing changes and blindly evaluating them against the incumbent. Use when the user wants to improve a skill, test a skill change, compare skill variants, or run a skill eval. Supports an optional improvement goal; otherwise performs general quality improvements.
---

# Improve a skill

Two playbooks. Route to one, then follow that file verbatim. Do not add a third workflow.

## Confirm the target

Do this before opening a playbook. Resolve the target to a real `SKILL.md`:

- Project skill: `<repo>/.cursor/skills/<name>/SKILL.md`
- User skill: `~/.cursor/skills/<name>/SKILL.md`

Search both locations when the user names a skill. One match: use it and say the path. Several matches, or none: ask the user to point at the `SKILL.md` and stop.

## Route

- Proposal, improvement, or rewrite → open [playbooks/propose.md](playbooks/propose.md) and follow it verbatim.
- Evaluate, compare, or test a proposed skill against the current one → open [playbooks/eval.md](playbooks/eval.md) and follow it verbatim.
- Both in one request → run Propose to completion, then Eval on the file Propose wrote.

## Before any work

Copy the chosen playbook's steps into a todo list before doing the work. On a combined run, copy Propose's steps first. Add Eval's steps only after the proposed file exists.

## Done

- Propose ends with the proposed file written, the original untouched, and a short change summary. Do not apply the change.
- Eval ends with a Cursor canvas (opened, or an absolute path if it cannot be opened) and a concise chat recommendation: promote the proposed skill, keep the incumbent, or iterate.
