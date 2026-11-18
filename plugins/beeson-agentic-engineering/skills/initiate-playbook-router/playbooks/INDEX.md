# Playbook index

Router: [../SKILL.md](../SKILL.md). Source and adaptation notes: [../ATTRIBUTION.md](../ATTRIBUTION.md).

Copy the matched playbook's steps verbatim into the task list. A step you do not do stays in the list with `skip: <reason>`.

## Implementation

| Playbook | For | Deliverable |
|---|---|---|
| [investigation](investigation.md) | A read-only question. How does X work, why was Y built this way, are we sure, X or Y? | A cited explanation or a recommendation. No code change. |
| [bug-fix](bug-fix.md) | A reported defect. | A fix traced to runtime evidence, repro failing before and passing after. |
| [perf-issue](perf-issue.md) | A measured slowness. | A fix tied to a baseline and a post-fix measurement. |
| [hillclimb](hillclimb.md) | Sustained improvement of one metric against a target. | A decision log of kept and reverted attempts, one commit per accepted win. |
| [runtime-forensics](runtime-forensics.md) | A live symptom: leak, idle spin, glitch. | A cited diagnosis. Not a fix. |
| [trace-forensics](trace-forensics.md) | A captured profile, trace, spindump, or heap snapshot. | A cited diagnosis from the artifact. Not a fix. |
| [feature](feature.md) | New or changed behaviour, built from a named data shape. | Working behaviour verified on the matching surface. |
| [refactoring](refactoring.md) | A behaviour-preserving change to structure or shape. | The new structure, held against a behaviour pin, with an equivalence proof. |
| [prototype](prototype.md) | A design or empirical fork to settle cheaply by observing it. | A decision plus a throwaway artifact. Not shippable code. |
| [visual-parity](visual-parity.md) | Pixel-exact equivalence between two implementations. | Zero image diff per component against a baseline established first. |

## Meta and decision

| Playbook | For | Deliverable |
|---|---|---|
| [authoring-a-skill](authoring-a-skill.md) | Writing or editing a SKILL.md. | A validated skill that changes a decision, nothing more. |
| [eval](eval.md) | Testing whether a skill, prompt, or structure change improves agent behaviour. | A blinded comparison and a promote-or-not recommendation. |
| [multi-phase-plan](multi-phase-plan.md) | Work spanning phases or stacked PRs. | A checklist plan an owner runs box by box. The plan is the deliverable. |
| [figure-it-out](figure-it-out.md) | Large, cross-cutting, or no playbook fits. | A bespoke playbook designed for the task, then run like any other. |

## Delivery and long runs

| Playbook | For | Deliverable |
|---|---|---|
| [opening-a-pr](opening-a-pr.md) | Opening a PR. Invoked at the end of every code-changing playbook. | Small ordered commits and a briefing-style PR body. |
| [babysit](babysit.md) | Driving a PR or stack to merge-ready. | Merge-ready frontier. Landing is a separate playbook. |
| [shipping](shipping.md) | Landing a verified green stack. | Only the contiguous independently verified run lands, bottom-up. |
| [autonomous-run](autonomous-run.md) | A long task driven to a checkable predicate without stopping. | The predicate met, with discards reported. |
| [orchestrate](orchestrate.md) | A standing multi-day program, many PRs, a fleet of agents. | Program state, per-PR verdicts, decisions waiting on the operator. |
| [autopilot-full](autopilot-full.md) | A queue of independent PRs run to merged, one owner per PR. | Owners merge only what an independent swarm verified. |
| [autopilot-stack](autopilot-stack.md) | That queue built and verified, not merged. | Verified PRs handed to the operator to land. |
| [session-pickup](session-pickup.md) | Resuming a prior agent's in-flight work. | A resume point. Nothing already done gets redone. |
| [pause-safely](pause-safely.md) | Suspending in-flight work cleanly. | A checkpoint a cold-start agent can resume from. |
| [worktree-cleanup](worktree-cleanup.md) | Reclaiming disk from worktrees and stale simulators. | Space reclaimed with a reason for everything held back. |
