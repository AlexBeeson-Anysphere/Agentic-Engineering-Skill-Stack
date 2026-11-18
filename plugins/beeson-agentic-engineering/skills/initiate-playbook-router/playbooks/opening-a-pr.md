### Opening a PR

Invoked at the end of every other playbook.

**Worktree.** Work from a git worktree off the base branch. Subagents inherit it. Multiple subagent calls on the same branch each get their own worktree, or fetch and reset between them. Dirty branch with unrelated work: patch out, fresh worktree, apply. Snarled worktree: reset from base, redo minimally.

**Commits.** Commit liberally. Rebase into small, ordered commits before opening PRs. Each commit is a future PR: landable, ordered to tell the story. Amend when the fix belongs in a just-made commit. New commit when separable. Commit bodies don't restate the subject.

**Titles.** Conventional Commits `type(scope): subject`, no trailing period. Type such as `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, or `perf`. Scope is the area. Subject is short, imperative, and names a real symbol when one carries the change.

**Descriptions.** The PR body is a one-minute briefing, not a lab notebook, for a reviewer who has the diff. It says why the change exists, what it leaves out, what it could break, and how you proved it works. Write short, simple sentences. The body becomes the squash commit body, so keep that commit under about 40 lines. Use `##` headings in this order, and drop a section with nothing to say:

- `## Why`: the problem and approach, 1-3 short sentences. Open with the restated goal from the router. No SHAs or rebase genealogy.
- `## What changed`: 1-3 short bullets. Name a real symbol or path only when it carries the change. Name both sides of a rename or retarget.
- `## Scope`: always. 1-3 short items on what it covers and what it deliberately leaves out (a follow-up, a known gap).
- `## Tradeoffs`: only rejected alternatives a reviewer would otherwise ask about. Skip when there was no real choice.
- `## Blast Radius`: 1-2 sentences on who or what it touches and why that is safe or risky.
- `## Verification`: 1-3 bullets, each a real run path and its outcome, from the router's evidence gate. Perf: one primary number with its unit, `before -> after`, and a link to the artifact for the rest.

After the sections, attach videos or screenshots when they prove a claim. Full SHAs, lane recitals, and file-by-file checklists go in a linked artifact, not the body.

**Forge.** Resolve the forge before the first PR operation and keep that choice for create, edit, view, watch, and merge. Use the forge CLI the project already uses (`gh` for GitHub) and record any fallback. Never require a stacking tool the project does not already use. When the run provides a built-in PR tool, create and edit through it, never through a CLI: a CLI-made PR misses what the tool tracks.

**Size and stacks.** Prefer five narrow PRs to one large PR. A stack is a base-branch chain. The root PR targets trunk. Each child rebases onto its parent's exact tip and its PR targets the parent branch. Branch from trunk only for independent work. Rebase on trunk before substantial stack work.

**Readiness.** Open every PR ready, never as a draft. Set that explicitly in whatever tool creates it. Read the PR back before you refer to its status.

**Babysit.** Opening a PR does not start a babysit. Post the URL and keep building. Finish the phase or stack first. Run a separate babysit pass only when the user asks for one after the whole stack exists. A subagent that opens a PR posts the URL and returns to the parent without babysitting, unless it is an Autopilot owner whose brief assigns the babysit loop.

**Reply:** the PR link, as a full URL.
