### Multi-phase or multi-PR plan

**You own the plan, not the code. The plan is a checklist an owner runs box by box and the operator audits from the evidence.** The plan is the deliverable. Do not implement.

1. When the change is one or two files with an obvious approach, skip the plan. Say so and stop.
2. Settle open questions by prototype before you write. Run `prototype.md` for each. Keep the branch, the SHA, and the screenshots as prototype evidence. Ask the operator only about a product or preference call that no run can settle, and give options.
3. Explore in fresh subagents. Each returns file pointers, conventions, test commands, and entry points. No inlined dumps in the main thread.
4. Write the plan file under the path the operator names, or the project store's `docs/` folder. Use the skeleton below. One section per PR. One PR is one change with its own evidence. Name the execution playbook in **How to read this**: `autopilot-full.md` when the run may merge, `autopilot-stack.md` when the operator lands the PRs, `orchestrate.md` for a standing program.
5. State the verification rule verbatim at the head of every verification block: "Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked." The live block is mandatory. Its lanes drive the real surface through the verification harness at the PR head, one lane per concrete scenario with a pass predicate and the artifact it saves. One lane is always the regression lane against trunk (if trunk lacks the feature, record that and gate the behaviour the diff adds instead of inventing a trunk result). The perf block names the metric, the probe run interleaved at trunk and head, the trunk baseline recorded first, and the number that fails.
6. Self-check the plan before handing back: every heading present in skeleton order, every box tied to evidence (a file, a log line, a screenshot, a test run, or a SHA), every PR naming its execution playbook, its files, and its review gate.
7. Hand back. Post the plan path and the self-check output, then stop. Execution starts on the operator's explicit go, under the execution playbook the plan names.

Plan skeleton (fill every placeholder, keep the heading order):

````markdown
# <Program> plan

<Under ten lines. What changes, for whom, the rule the program enforces, and the PR ids in order.>

## How to read this

One box is one unit of work. Every box names the evidence that checks it. Check a box only when its evidence exists.
The program runs `playbooks/<execution playbook>.md`. <Who merges, and which PR ids are the operator's items that stop at merge-ready.>
Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program
- [ ] State the protocol and this plan to the operator, then stop. Start execution only on the operator's explicit go.
- [ ] Re-read the execution playbook, the swarm or verification method, the verification harness, and `opening-a-pr.md` from trunk at program start and at every audit tick.
- [ ] On the operator's go, arm the audit tick with the host's loop mechanism. The tick re-reads the execution playbook, fixes drift, probes every active lane by its side effects (pushes, PR activity), replaces stuck lanes, and reports only tracked changes not already reported.

### Spawn owners
- [ ] Spawn one owner per PR with the full lifecycle the execution playbook names.
- [ ] Follow the dependency graph. Start dependent work only after its parent merges, or base it on the parent branch when the execution playbook stacks.
- [ ] Hold the file boundaries. <PR id or class> touches only `<glob>`.
- [ ] Hold the review gate. <PR ids that change an interaction> wait for the operator's review with screenshots and a video before merge.

### PR mechanics, for every PR
- [ ] Resolve the forge once and record it. Open the PR ready, never draft, per Opening a PR.
- [ ] Run the repo's lint and typecheck once before the PR-facing push.
- [ ] Triage every bot and security-reviewer comment sceptically: verify each claim against the code, fix real findings, dismiss noise with the concrete disproof on the thread.

### Verdict and merge, for every PR
- [ ] A full independent verification runs once at the code-ready head. A new behaviour change or large new diff earns another. A rebase, conflict resolution, or minor fix gets a single verifier. A wording-only change gets none.
- [ ] The verdict is clean when no blocking finding stands: only a bug a user would hit, a failed gate, or a wrong shipped doc blocks. Everything else becomes a follow-up.
- [ ] <The merge or handoff rule from the execution playbook.>

## <Task as a verb phrase> (<PR id>)

**Depends on.** <PR id, or None.>

**Files.**
- [ ] Edit `<path>`. Create `<path>`. Delete `<path>`.

**Build.**
- [ ] <One change. Name the symbol and the file.>

**You see.**
- [ ] <One observable result, with the exact log line or screen state.>

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] <Test file and the case it gains.> Run `<command>`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Lane 1. Regression lane against trunk. <Scenario, artifact saved, pass predicate.>
- [ ] Lanes 2-N. <One concrete scenario per lane, artifact saved, pass predicate.>

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Metric. <Measured at both trunk and head.>
- [ ] Probe. <Command or procedure, interleaved at trunk and head.>
- [ ] Baseline. Record the trunk value first.
- [ ] Rule. <Head against trunk, with the number that fails.>

**Review gate.** <Operator reviews before merge, with the artifacts named, or: None, with the reason.>

**Merge.**
- [ ] Independent clean verdict at the exact head SHA.
- [ ] Bot triage done.
- [ ] <Owner merges, or operator lands bottom-up.>

## Close the program
- [ ] Every box above is checked with its evidence.
- [ ] Reply to the operator with the report the execution playbook names.

## Appendix A. Prototype evidence
<Each open question a prototype answered, with branch, SHA, and artifact links. Each question that stays unproven.>

## Appendix B. Alternatives rejected
<Each approach weighed and why it lost.>

## Appendix C. Risks
<Each risk with the PR it lands in and what the owner watches.>

## Appendix D. Links and reading list
<Docs to read before editing, which PRs get design or adversarial review, the decision-trail path.>
````

**Reply:** the plan path, the PR ids with their dependencies and the review-gated set, what the prototypes proved and what stays unproven, and the self-check output.
