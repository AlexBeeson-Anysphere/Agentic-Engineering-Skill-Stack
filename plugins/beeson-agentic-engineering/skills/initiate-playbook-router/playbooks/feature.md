### Feature

**You own the design. Plan, review, verify.** Delegate implementation. Stay in the lead.

1. Run the Understand capability over the affected subsystem. If a Feature Map exists, open the one feature file for this area first and ground the design in how a user reaches and drives this behaviour today.
2. Run design exploration for competing shapes before implementing, unless the shape is already concrete and local.
3. Name the data shape first, and choose its organizing structure before any logic is written: a state machine over scattered booleans, a table or registry over branching, a typed model over repeated shape assumptions, a boundary over leaked internals.
4. Write the throughput checkpoint as four task-list items. A dimension that genuinely does not apply (single file, no fan-out) keeps its item with `n/a: <reason>` rather than being dropped:
   - **Blocking first steps.** Gates run before fan-out.
   - **Independent workstreams.** Disjoint files, services, or layers parallelize. Shared writes serialize.
   - **Shared mutable state.** Default to splitting the target so actors do not share it. Serialize only for real invariants.
   - **Smallest safe decomposition.** If one worker is best, name why.
5. Delegate implementation to a subagent on the configured feature model with a specific scope: file paths, the named data shape from step 3, and success criteria. When the implementation admits multiple valid shapes (error handling, abstraction layer, test structure), delegate via Arena instead so competing attempts surface the alternatives and a cross-model judge guards the pick. Port shared-primitive improvements to all consumers and verify each. Commit liberally.
6. Verify on the matching surface via the verification harness. A UI change walks the changed flow, a CLI change runs the real command, a storage change reads the value back. "Inconclusive" or wrong-surface is not a pass. Flag it.
7. Rebase into small, ordered commits, each ending in a verifiable state, verified before the next. Stack follow-ups.
8. If the design is contested, run adversarial review before shipping.
9. Run Opening a PR (`opening-a-pr.md`).

Code-coupled work (one feature, one migration) goes to a single owner with the checkpoint inline. That owner fans out internally after the blocking phase. Parent-level fan-out is for slices that produce independent artifacts (audits, cross-subsystem investigations, competing experiments). Rewrite the checkpoint at phase boundaries. Spawn a fresh owner rather than chaining interrupts.

**Reply:** what you built, what you chose and why, the throughput checkpoint, open decisions. Tables for design alternatives.
