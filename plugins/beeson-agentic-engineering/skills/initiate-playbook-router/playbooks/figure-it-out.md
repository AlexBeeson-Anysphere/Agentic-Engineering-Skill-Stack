### Figure it out

**You own the workflow itself. When no playbook fits, design one, then run it like any other.** Adapted from pstack's `figure-it-out` skill. For a large migration, an ambitious multi-part change, work a human reviews after stepping away, or any task where the fit to an existing playbook is forced.

The deliverable before any code is the workflow: a sequence of phases that scales rigor to the task, runs the scientific method, and leaves a decision trail a human can audit after stepping away.

1. **Frame, before any code.** Ground first, then commit. Do not start the run until you can state:
   - The definition of done as a falsifiable predicate: a check that can fail, not a description of effort.
   - Scope, quantified: rough units and effort, plus the blockers grounding surfaced.
   - The rigor level, biased high. One-way doors and high blast radius get more. Reversible low-stakes steps get less. Rigor is gates and artifacts, not "try harder".
   Present the framing and tradeoffs before committing to a long run. Reversible work proceeds without blocking on the human, but a multi-hour run earns one checkpoint.
2. **Design the workflow.** Decompose into atomic, independently-landable units. Sequence riskiest-unknown-first. Scaffold and verification come before features.
   - Build the verification harness before the work, with the baseline captured from the pre-change state, so the check reads as "old value vs new value".
   - For one-way-door design decisions, run design exploration (Arena where several shapes are valid). Skip it for mechanical work whose shape is already concrete. A second arena over a settled design is over-engineering.
   - Decide what fans out. Parallelize only across seams, and give each worker its own worktree or branch. Don't over-fan.
   - Write the designed phase list down. That list is what the human reviews. Then copy it into the task list verbatim, exactly as the router copies any playbook, and run it under steps 3-5.
3. **Run the loop.** Each unit is an experiment. State the hypothesis, make the smallest change, measure against the predicate on the real artifact, keep it if it advanced, revert it if it didn't. Verify each unit before starting the next instead of batching checks at the end.
   - Verify by inspecting the artifact, never a self-report. When something passes too easily, suspect the observation method before the system.
   - Pair delegated work with a judge on a different model. If a worker games the gate, reset and harden the contract. If the gate itself is wrong, fix the gate in its own change rather than routing around it.
   - A verdict is VERIFIED, NOT VERIFIED, or INCONCLUSIVE. Inconclusive is not a pass. Don't hide a negative.
4. **Keep the audit trail.** Log the run via the decision-trail capability, a row as each step lands rather than the whole trail saved for the end. Work ambitious enough for this playbook usually earns a committed trail so the reviewer can read it in the PR. The trail plus the diff is what lets the human come back and trust the work.
5. **Verify and hand back.** Check the whole against the step-1 predicate on the real product, not just the harness. Encode any recurring correction as a gate, a lint rule, a check, or a script instead of more prose. Run Opening a PR (`opening-a-pr.md`) for each landed unit or for the run, per its shape.

**Reply:** the playbook you designed, the rigor level and why, the decision-trail path, what's verified against the predicate, and what's still open.
