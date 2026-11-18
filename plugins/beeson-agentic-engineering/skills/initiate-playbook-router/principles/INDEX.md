# Engineering Principle Catalog

Use this catalog after choosing the primary playbook. Principles constrain how a playbook runs; they do not create a second workflow or task list.

## Selection contract

1. Start with the playbook defaults below.
2. Add a conditional principle only when its trigger is present in the task or discovered during execution.
3. Select the smallest set that changes a decision. Two to five principles is typical, not a quota.
4. Read every selected principle guideline in full before the playbook step it constrains.
5. Record each selection as `<principle>: <trigger>; affects <playbook step or decision>`.
6. Re-evaluate at phase boundaries and after evidence changes the task's shape. Do not re-route merely because a new principle applies.

## Playbook defaults

- **Every deliverable:** [Prove It Works](principle-prove-it-works.md). Read-only work proves load-bearing claims from sources; changed artifacts are exercised on the real surface.
- **Multi-step mutating work:** [Sequence Verifiable Units](principle-sequence-verifiable-units.md) for sweeps, migrations, repeated edits, or commit and PR shaping. Do not select it merely because a read-only investigation has several steps.
- **Bug fix:** [Fix Root Causes](principle-fix-root-causes.md). Add [Test Behavior, Not Implementation](principle-test-behavior-not-implementation.md) when tests are written or changed.
- **Feature:** [Foundational Thinking](principle-foundational-thinking.md) and [Model the Domain](principle-model-the-domain.md).
- **Refactoring:** [Subtract Before You Add](principle-subtract-before-you-add.md) and [Minimize Reader Load](principle-minimize-reader-load.md). Add Laziness Protocol only when the proposed shape introduces optional abstractions, layers, or signal threading.
- **Perf issue or hillclimb:** [Build the Lever](principle-build-the-lever.md).
- **Prototype or novel design:** [Exhaust the Design Space](principle-exhaust-the-design-space.md).
- **Investigation or forensics:** [Guard the Context Window](principle-guard-the-context-window.md). Add Fix Root Causes when the deliverable is a causal diagnosis.
- **Autonomous run, orchestrate, autopilot, or multi-phase plan:** [Outcome-Oriented Execution](principle-outcome-oriented-execution.md), Guard the Context Window, and Sequence Verifiable Units.
- **Babysit, shipping, or opening a PR:** Prove It Works and Sequence Verifiable Units.
- **Authoring or evaluating a skill:** Prove It Works. Add [Encode Lessons in Structure](principle-encode-lessons-in-structure.md) when the skill captures a recurring correction.

These are starting points. Drop a default with a stated reason when its trigger is absent. Add conditional principles only from evidence.

## Conditional principles

### Core design

- [Laziness Protocol](principle-laziness-protocol.md): sizing a diff or proposing optional abstractions, layers, or signal threading. Refactoring alone does not trigger it.
- [Foundational Thinking](principle-foundational-thinking.md): choosing core types, data structures, scaffolding order, or shared state before writing logic.
- [Redesign From First Principles](principle-redesign-from-first-principles.md): integrating a new requirement into an existing design.
- [Attack the Premise](principle-attack-the-premise.md): two fixes sharing one premise failed the same gate.
- [Subtract Before You Add](principle-subtract-before-you-add.md): sequencing an addition, refactor, rewrite, or migration.
- [Minimize Reader Load](principle-minimize-reader-load.md): code is hard to trace or requires too much hidden state.
- [Outcome-Oriented Execution](principle-outcome-oriented-execution.md): planned rewrites or migrations with explicit phase boundaries.
- [Experience First](principle-experience-first.md): product, UX, API, or maintainer-experience tradeoffs.
- [Exhaust the Design Space](principle-exhaust-the-design-space.md): a novel interaction or architecture decision has multiple viable shapes and no precedent.
- [Build the Lever](principle-build-the-lever.md): non-trivial edits, migrations, analyses, checks, or delegated recipes can be made deterministic and rerunnable.

### Architecture

- [Model the Domain](principle-model-the-domain.md): stateful logic, branching growth, or repeated shape assumptions.
- [Boundary Discipline](principle-boundary-discipline.md): validation, error handling, parsing, framework adapters, or external input.
- [Type System Discipline](principle-type-system-discipline.md): designing types or signatures in a statically typed language.
- [Make Operations Idempotent](principle-make-operations-idempotent.md): commands, lifecycle steps, or loops run amid crashes, retries, or restarts.
- [Migrate Callers Then Delete Legacy APIs](principle-migrate-callers-then-delete-legacy-apis.md): introducing a replacement internal API with coordinated callers.
- [Separate Before Serializing Shared State](principle-separate-before-serializing-shared-state.md): concurrent actors may write the same file, branch, key, or state object.

### Verification and debugging

- [Prove It Works](principle-prove-it-works.md): before declaring any task complete.
- [Fix Root Causes](principle-fix-root-causes.md): debugging symptoms or adding guards around unexplained state.
- [Sequence Verifiable Units](principle-sequence-verifiable-units.md): multi-step mutating work, sweeps, migrations, similar edits, commits, or PR stacks. A read-only investigation having several steps does not trigger it.
- [Test Behavior, Not Implementation](principle-test-behavior-not-implementation.md): writing, changing, or deciding whether to keep a test.

### Delegation and autonomy

- [Guard the Context Window](principle-guard-the-context-window.md): large outputs, long files, repeated reads, or fan-out planning threaten the lead context.
- [Never Block on the Human](principle-never-block-on-the-human.md): a reversible execution decision tempts the agent to ask for permission.

### Meta

- [Encode Lessons in Structure](principle-encode-lessons-in-structure.md): the same instruction or correction appears a second time.
