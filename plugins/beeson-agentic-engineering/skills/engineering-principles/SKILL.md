---
name: engineering-principles
description: Selects the smallest set of engineering principles that should constrain the decision in front of you, and loads only those guidelines from a catalog of 23. Use when choosing types or architecture, sizing a diff, debugging, writing or keeping tests, reviewing a change, sequencing a migration, delegating to subagents, or when initiate-playbook-router reaches principle selection. Also use when the user names a principle such as prove it works, fix root causes, or laziness protocol. Do not load the whole catalog.
---

# Engineering Principles

Principles constrain decisions. They are not a workflow and do not create a second task list. Under a running playbook from `initiate-playbook-router`, the playbook owns the lifecycle and this catalog constrains decisions inside it. Outside a playbook, apply the same contract to the decision at hand.

The guidelines live in [principles/](principles/). Each is a reference file, not an independently invokable skill. Open only the ones you select.

## Named request

If the user names a principle (`/engineering-principles prove-it-works`, "apply fix root causes"), open that guideline in full and apply it to the current work. Skip selection.

## Selection contract

1. Under a playbook, start with that playbook's defaults below. Outside a playbook, start from the decision at hand; Prove It Works still applies to any deliverable.
2. Add a conditional principle only when its trigger is present in the task or discovered during execution.
3. Select the smallest set that changes a decision. Two to five principles is typical, not a quota.
4. Read every selected principle guideline in full before the step or decision it constrains.
5. Record each selection as `<principle>: <trigger>; affects <playbook step or decision>`.
6. Re-evaluate at phase boundaries and after evidence changes the task's shape. Do not re-route a playbook merely because a new principle applies.

## Playbook defaults

- **Every deliverable:** [Prove It Works](principles/principle-prove-it-works.md). Read-only work proves load-bearing claims from sources; changed artifacts are exercised on the real surface.
- **Multi-step mutating work:** [Sequence Verifiable Units](principles/principle-sequence-verifiable-units.md) for sweeps, migrations, repeated edits, or commit and PR shaping. Do not select it merely because a read-only investigation has several steps.
- **Bug fix:** [Fix Root Causes](principles/principle-fix-root-causes.md). Add [Test Behavior, Not Implementation](principles/principle-test-behavior-not-implementation.md) when tests are written or changed.
- **Feature:** [Foundational Thinking](principles/principle-foundational-thinking.md) and [Model the Domain](principles/principle-model-the-domain.md).
- **Refactoring:** [Subtract Before You Add](principles/principle-subtract-before-you-add.md) and [Minimize Reader Load](principles/principle-minimize-reader-load.md). Add Laziness Protocol only when the proposed shape introduces optional abstractions, layers, or signal threading.
- **Perf issue or hillclimb:** [Build the Lever](principles/principle-build-the-lever.md).
- **Prototype or novel design:** [Exhaust the Design Space](principles/principle-exhaust-the-design-space.md).
- **Investigation or forensics:** [Guard the Context Window](principles/principle-guard-the-context-window.md). Add Fix Root Causes when the deliverable is a causal diagnosis.
- **Autonomous run, orchestrate, autopilot, or multi-phase plan:** [Outcome-Oriented Execution](principles/principle-outcome-oriented-execution.md), Guard the Context Window, and Sequence Verifiable Units.
- **Babysit, shipping, or opening a PR:** Prove It Works and Sequence Verifiable Units.
- **Authoring or evaluating a skill:** Prove It Works. Add [Encode Lessons in Structure](principles/principle-encode-lessons-in-structure.md) when the skill captures a recurring correction.

These are starting points. Drop a default with a stated reason when its trigger is absent. Add conditional principles only from evidence.

## Conditional principles

### Core design

- [Laziness Protocol](principles/principle-laziness-protocol.md): sizing a diff or proposing optional abstractions, layers, or signal threading. Refactoring alone does not trigger it.
- [Foundational Thinking](principles/principle-foundational-thinking.md): choosing core types, data structures, scaffolding order, or shared state before writing logic.
- [Redesign From First Principles](principles/principle-redesign-from-first-principles.md): integrating a new requirement into an existing design.
- [Attack the Premise](principles/principle-attack-the-premise.md): two fixes sharing one premise failed the same gate.
- [Subtract Before You Add](principles/principle-subtract-before-you-add.md): sequencing an addition, refactor, rewrite, or migration.
- [Minimize Reader Load](principles/principle-minimize-reader-load.md): code is hard to trace or requires too much hidden state.
- [Outcome-Oriented Execution](principles/principle-outcome-oriented-execution.md): planned rewrites or migrations with explicit phase boundaries.
- [Experience First](principles/principle-experience-first.md): product, UX, API, or maintainer-experience tradeoffs.
- [Exhaust the Design Space](principles/principle-exhaust-the-design-space.md): a novel interaction or architecture decision has multiple viable shapes and no precedent.
- [Build the Lever](principles/principle-build-the-lever.md): non-trivial edits, migrations, analyses, checks, or delegated recipes can be made deterministic and rerunnable.

### Architecture

- [Model the Domain](principles/principle-model-the-domain.md): stateful logic, branching growth, or repeated shape assumptions.
- [Boundary Discipline](principles/principle-boundary-discipline.md): validation, error handling, parsing, framework adapters, or external input.
- [Type System Discipline](principles/principle-type-system-discipline.md): designing types or signatures in a statically typed language.
- [Make Operations Idempotent](principles/principle-make-operations-idempotent.md): commands, lifecycle steps, or loops run amid crashes, retries, or restarts.
- [Migrate Callers Then Delete Legacy APIs](principles/principle-migrate-callers-then-delete-legacy-apis.md): introducing a replacement internal API with coordinated callers.
- [Separate Before Serializing Shared State](principles/principle-separate-before-serializing-shared-state.md): concurrent actors may write the same file, branch, key, or state object.

### Verification and debugging

- [Prove It Works](principles/principle-prove-it-works.md): before declaring any task complete.
- [Fix Root Causes](principles/principle-fix-root-causes.md): debugging symptoms or adding guards around unexplained state.
- [Sequence Verifiable Units](principles/principle-sequence-verifiable-units.md): multi-step mutating work, sweeps, migrations, similar edits, commits, or PR stacks. A read-only investigation having several steps does not trigger it.
- [Test Behavior, Not Implementation](principles/principle-test-behavior-not-implementation.md): writing, changing, or deciding whether to keep a test.

### Delegation and autonomy

- [Guard the Context Window](principles/principle-guard-the-context-window.md): large outputs, long files, repeated reads, or fan-out planning threaten the lead context.
- [Never Block on the Human](principles/principle-never-block-on-the-human.md): a reversible execution decision tempts the agent to ask for permission.

### Meta

- [Encode Lessons in Structure](principles/principle-encode-lessons-in-structure.md): the same instruction or correction appears a second time.
