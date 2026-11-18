---
name: initiate-playbook-router
description: Routes a substantial work request to one fixed playbook and the smallest relevant set of engineering principles, copies the playbook verbatim into the task list, delegates implementation, and requires runtime evidence before reporting success. Use proactively for vague tickets, bugs, features, refactors, investigations, performance work, PR delivery, migrations, or any multi-step task that needs rigour, and when the user says initiate-playbook-router, run the playbook, route this, or work in playbook mode. Do not use when a playbook is already running or for a fully specified one-line edit.
---

# Initiate Playbook Router

Adapted from Lauren Tan's `poteto-mode` router in pstack. See [ATTRIBUTION.md](ATTRIBUTION.md) for source, licence, and what was changed in the adaptation. The playbooks live in [playbooks/](playbooks/INDEX.md). The engineering-principle catalog lives in [principles/INDEX.md](principles/INDEX.md).

One claim runs the whole system: delivery rate is capped by how much you can verify, not how much you can generate. Vagueness is only affordable when the agent can independently establish where it is, what it changed, and whether it worked. This router is the machinery that makes a half-formed ticket safe to hand over: the vague input hits a fixed procedure instead of an open-ended planning session.

## Light exit

Do not route these. Handle them directly, still verify, and say you skipped the router and why:

- A fully specified one-line edit where file, change, and check are all named.
- A question you can answer from context already loaded in this session.
- A task already running under a playbook. Continue that playbook. Do not re-route mid-flight unless a re-route trigger below fires.

## Step 0. Pre-flight: establish where you are

Layers 1 and 2 of Scaled Agentic Engineering come before this layer. Check for them before routing, because the playbooks assume them:

1. **Feature Map.** Look for a feature-map index in the repo (commonly `docs/feature-map/`, a `feature-map` skill, or the index named in project rules). If it exists, open the index, then open only the one feature file for the change under test. Do not read the whole corpus. That scoping is the anti-spiral mechanism: the map already answers "where does this live," so stop exploring once it does.
2. **Verification harness.** Look for the project's verification or control skill (how to run, drive, and debug the real app: a control skill, a verification skill, or documented run commands). Note the exact command or surface you will use to prove the work. Name it in your first message.
3. **Project rules and state.** Read applicable project rules. Record branch, dirty state, and base ref if the task touches code.

If the Feature Map or the harness is missing, say so in one line and proceed with scoped exploration and the nearest real surface. Flag the gap as a follow-up. An absent map is a risk to name, not a reason to stop, and never a reason to claim verification you did not do.

## Step 1. Restate the goal

Your first message on the task states, in your own words:

- The user's goal and the problem they are solving.
- If the task ships a change, the smallest change you expect to meet it.
- The playbook you matched (Step 2) and the verification surface from Step 0.
- The engineering principles selected in Step 2.5, why each triggered, and which playbook step or decision each constrains.

Do not wait for confirmation. Restate the goal in every subagent brief and open the final report with it. Exception: a fully specified one-line edit under the light exit.

If the evidence rules out the change the user asked for, show the evidence and stop. No is an acceptable answer. Agreement is not the default.

## Step 2. Route: match the task to one playbook

Read the routing table, pick **one primary playbook**, and open its file in full before writing any code. The full index with signals is [playbooks/INDEX.md](playbooks/INDEX.md). Worked routing decisions, including the vague-ticket cases, are in [examples.md](examples.md).

| If the request is… | Playbook |
|---|---|
| Read-only question: how does X work, why was Y built this way, are we sure, X or Y? | [investigation](playbooks/investigation.md) |
| A reported defect to reproduce, root-cause, and fix | [bug-fix](playbooks/bug-fix.md) |
| A measured slowness to trace against a baseline | [perf-issue](playbooks/perf-issue.md) |
| Sustained improvement of one metric against a target, looped scientifically | [hillclimb](playbooks/hillclimb.md) |
| A live runtime symptom (leak, idle spin, glitch) to diagnose, not fix | [runtime-forensics](playbooks/runtime-forensics.md) |
| A captured profile, trace, spindump, or heap snapshot to diagnose after the fact | [trace-forensics](playbooks/trace-forensics.md) |
| New or changed behaviour | [feature](playbooks/feature.md) |
| Behaviour-preserving change to structure or shape | [refactoring](playbooks/refactoring.md) |
| A throwaway sketch to settle a design or empirical fork by observing it | [prototype](playbooks/prototype.md) |
| Pixel-exact equivalence between two implementations | [visual-parity](playbooks/visual-parity.md) |
| Writing or editing a SKILL.md | [authoring-a-skill](playbooks/authoring-a-skill.md) |
| Testing whether a skill, prompt, or structure change improves agent behaviour | [eval](playbooks/eval.md) |
| Driving a PR or stack to merge-ready: conflicts, review threads, CI | [babysit](playbooks/babysit.md) |
| Landing a verified green stack | [shipping](playbooks/shipping.md) |
| A long task to drive to a checkable predicate without stopping | [autonomous-run](playbooks/autonomous-run.md) |
| A standing, multi-day program of many stacked PRs under one coordinator | [orchestrate](playbooks/orchestrate.md) |
| A queue of independent PRs run to merged, one owner per PR | [autopilot-full](playbooks/autopilot-full.md) |
| That same queue, built and verified but not merged | [autopilot-stack](playbooks/autopilot-stack.md) |
| Resuming a prior agent's in-flight work | [session-pickup](playbooks/session-pickup.md) |
| Suspending in-flight work cleanly so it can be resumed | [pause-safely](playbooks/pause-safely.md) |
| Work spanning phases or stacked PRs, where the plan is the deliverable | [multi-phase-plan](playbooks/multi-phase-plan.md) |
| Reclaiming disk from merged or abandoned worktrees and stale simulators | [worktree-cleanup](playbooks/worktree-cleanup.md) |
| Opening a PR. Invoked at the end of every code-changing playbook | [opening-a-pr](playbooks/opening-a-pr.md) |
| Large, cross-cutting, no playbook fits, or work the user steps away from | [figure-it-out](playbooks/figure-it-out.md) |

### Routing tie-breaks

When two playbooks could claim the request, route by what must produce evidence first:

- **Diagnosis before fix.** A symptom with no known cause routes to runtime-forensics, trace-forensics, or investigation until a mechanism survives evidence. Then re-route to bug-fix or perf-issue to fix it. A defect with a known reproducible trigger routes straight to bug-fix; its playbook performs the causal diagnosis before changing code.
- **Bug, feature, or refactor.** It corrects behaviour users can observe: bug-fix. It adds or changes behaviour: feature. It changes only structure while behaviour is pinned unchanged: refactoring. If a refactor reveals a bug or a missing feature, split that out and ship the structural change first against the pinned contract.
- **Perf once vs perf as a program.** One measured slowness with a fix-shaped answer: perf-issue. Open-ended optimisation against a target number over many attempts: hillclimb.
- **Read-only performance work.** "Why is this slow?" with no code changes routes to runtime-forensics for a live symptom, trace-forensics for a captured artifact, or investigation for a cited architectural answer. Perf-issue begins only when the requested deliverable includes a fix.
- **Empirical fork before feature.** If a "which approach?" fork can be settled by observing behaviour, timing, layout, or output, route to prototype and let the result decide. Do not ask the human a question an experiment can answer. Reserve questions for genuine product or preference calls no experiment settles.
- **Scale.** Work one agent can finish inside the session routes to its task playbook, however program-shaped the phrasing sounds. Multi-day, many-PR, fleet-of-agents work routes to orchestrate. One long task driven to a predicate routes to autonomous-run.
- **Merge intent.** "Get it green / merge-ready" is babysit. "Land it / ship it" is shipping, which begins where babysit ends. "Do not merge" on an autonomous queue is autopilot-stack, not autopilot-full.
- **Read-only stays read-only.** Investigation and forensics change no code. If an investigation turns into a change, hand back, name the new playbook, and re-route explicitly.

## Step 2.5. Select the engineering principles

The playbook defines the task lifecycle. Principles constrain decisions inside that lifecycle. Principle selection is not a second workflow and does not create a competing plan.

1. Open [principles/INDEX.md](principles/INDEX.md).
2. Start with the matched playbook's defaults, then add only principles whose conditional triggers are present in the request or observed evidence.
3. Select the smallest set that changes a decision. Do not load the full catalog.
4. Read every selected principle guideline linked from the catalog in full before the playbook step it constrains. These files are references owned by this router, not independently invokable skills.
5. Record the principle contract as `<principle>: <trigger>; affects <playbook step or decision>`.
6. Re-evaluate the set at phase boundaries and when evidence changes the task's shape. Add or drop a principle visibly with a one-line reason. A changed principle set is not a playbook re-route.

## Step 3. Copy the playbook into the task list verbatim

This is the load-bearing step. Do not summarise the playbook. Do not improvise an equivalent plan.

1. Open the matched playbook file in full.
2. Create the task list with the playbook's numbered steps as the first items, **copied verbatim**, in order, before any task-specific items.
3. A step you choose not to do stays in the list, marked `skip: <one-line reason>`. A skipped step stays visible. Silent omission is the failure mode this prevents.
4. Write the principle contract after the verbatim playbook steps. A principle that creates a concrete action or evidence requirement gets one task-specific item after that block; name the playbook step it gates and execute it with that step. A decision policy does not become a ceremonial checkbox.
5. Add other task-specific items after the playbook steps. Keep exactly one item in progress at a time.
6. If the host has no task-list tool, write the same list and principle contract as a checklist in your reply and update it as steps complete.

## Step 4. Execute under the playbook

### Who does the work

The lead agent owns the playbook: it plans, routes, reviews every diff, and reports. It delegates investigation and implementation to subagents where the playbook says so, and it never spawns a subagent to run the playbook itself.

- **Fresh subagents by default.** Give new work a fresh subagent with consolidated scope: the restated goal, every later directive, file pointers rather than inlined dumps, the named data shape, the success criteria, and pointers to only the selected principle guidelines that constrain that subagent's slice. Resume an existing subagent only when the work strictly needs state that lives in it (its checkout, uncommitted changes, a running process).
- **You own every subagent's work.** Review the diff yourself. Write your own summary. Do not pass through what the subagent said.
- **The verifier is never the author.** The model that wrote the code is too generous grading its own homework. Verification, review, and judging go to a different agent, ideally a different model family.

### Delegation shapes

Do not conflate the two parallel shapes:

- **Arena.** The same task goes to several models. Synthesise one result from the competing attempts, grafting what each learned. Use for contested designs and for implementations that admit several valid shapes.
- **Swarm.** A task splits into independent slices. Workers run in parallel, wait for all, return one combined report. Use for coverage across many units: verification lanes, audits, exploration partitions.

Use a second opinion (same prompt, different model) when a decision is contested. Agreement across model families is high-signal.

### Matching the model to the job

This skill names no model slugs. Slugs age, and a role line beats a hard-coded default.

- If the project configures models per role (a setup rule, a model config, team convention), that configuration wins for every role below.
- Hardest work (cross-cutting design, subtle concurrency or algorithms, judgment on vague intent): the strongest judgment model available.
- Routine implementation: a capable code model. Trivial mechanical edits: the fastest code model that does the job reliably.
- Verification lanes: keep the family the role names so a diverse panel stays diverse. Change effort or speed, not family, unless the family has no suitable option.
- If a chosen model is rejected by the tool, fall back to the configured default, then to the parent chat's model, and say so. Never retry a rejected slug.

### Supporting capabilities

Playbooks refer to these capabilities by what they do. Use the project's skill of that name if one is installed; otherwise perform the action inline, in the lead, without pretending a skill ran.

| Capability | What it does |
|---|---|
| Understand | Map how a subsystem works and where things live before touching it |
| History | Establish why code is the way it is: git history, prior decisions, regression origin |
| Design exploration | Explore 2-3 competing shapes in parallel and pick one with reasons recorded |
| Adversarial review | Attack a contested design from several models before shipping it |
| Test-first | Write the failing reproduction or test before the fix, land it first in history |
| Measurement hygiene | Vet a benchmark before trusting it: what limits the number, what it actually measured, noise |
| Decision trail | A running log of what changed, why, and whether the goal moved, auditable after the fact |
| Throughput checkpoint | Blocking steps first, independent workstreams, shared mutable state, smallest safe decomposition |

## The evidence gate (non-negotiable)

No playbook reports success without evidence from the real artifact. A passing build is not sufficient evidence. "It compiles" is not a pass. "Inconclusive" is not a pass; flag it as inconclusive and keep working or report it as such.

Match proof to the change type:

| Change type | Required proof |
|---|---|
| CLI or TUI | Run the real command. Show its output. |
| UI (web, Electron, native) | Walk the changed flow on the real surface. Screenshot or recording. |
| Bug fix | The original reproduction, failing before and passing after, on the same surface. Paste both outputs. |
| Refactoring | A behaviour pin (characterisation test, snapshot, equivalence harness) green before and after, plus an old-vs-new equivalence check on the real artifact. |
| Migration or data transform | Replay real input through the new path. Diff output against the old path or the recorded baseline. |
| Perf | Baseline and post-fix measurement from the same harness, with the delta. Name what the number measures. |
| Storage or state | Read the value back after writing it. Show the read. |
| Docs, skills, playbooks | Frontmatter and links validate, referenced files exist, and a reader can follow the procedure without the author. |
| Read-only deliverable | A cited answer: file, symbol, artifact, or run output behind every load-bearing claim. |

Every claim in the report carries its evidence or its label (measured, inferred, guess) in the same sentence. Never hand the human a check you could run yourself.

## Work shaping: atomic, verifiable units

Sequence the work so each unit ends in a checkable state, and verify each unit before starting the next. Do not batch checks at the end.

- Each commit is as atomic as possible: one small change it describes, landable on its own, ordered so the sequence proves itself to a reviewer.
- For a bug with a cheap local test path, the failing reproduction lands before the fix in git history.
- Stage only the files the unit changed. Discard or revert changes that did not advance the predicate. Belt-and-suspenders that "might help" is a hypothesis, not a fix, and does not ship.
- A forty-thousand-line PR that merges is still nearly impossible to debug. Prefer five narrow PRs to one large one.

## Re-route triggers

Stop and re-route, naming the new playbook, when:

- Evidence refutes the premise the current playbook assumes. Write the premise down and test it directly before writing another fix that assumes it.
- A diagnosis playbook confirms a cause. Hand to bug-fix or perf-issue for the fix.
- A prototype settles the fork. Hand the chosen direction to feature for the real build.
- The work grows across phases or PRs beyond the current playbook's shape. Route to multi-phase-plan or figure-it-out.
- No playbook fits, or the fit is forced. Route to figure-it-out and design a bespoke playbook whose steps then get copied verbatim like any other.

Re-routing is a visible event: mark remaining items from the old playbook `skip: re-routed to <playbook>`, then copy the new playbook's steps in.

## Autonomy

- **Just do it.** Reversible work proceeds without asking. Use any tool available. Do not block on the human for a decision an observation can make.
- **Always pause** for irreversible writes: force-push to shared branches, deploys, data deletion, messages to customers, merging without the verification a delivery playbook requires.
- **Session overrides.** "Don't stop," "run until done," "going to bed" widen autonomy for the session. Gates the user named, and the Always-pause list, still need the user.
- Under a full-autonomy grant, decide calls the grant covers, act, and report the decision with what the user could tell you to do instead. In plain words, never a shorthand token to type back.

## Reply

Open the final report with the restated goal. Then give only what the matched playbook's **Reply** line names, plus:

- Playbook used, and any steps skipped with their reasons.
- Principles that materially changed a decision, with that decision. Do not recite principles that had no effect.
- Evidence: the actual outputs, paths, screenshots, or measurements behind the verdict, or the label inconclusive.
- What was reverted or discarded, and why.
- Open decisions that are genuinely the user's.

Write short declarative sentences. Name who the work is for and what changes for them before implementation detail, then what the next engineer who owns this inherits. Never fabricate a link, citation, or artifact reference: link only what you produced or read this session.

## Maintaining this router

These playbooks are production infrastructure with a drift budget, not documentation.

- A step that fails or misleads twice gets fixed in the playbook, in its own change, not worked around silently twice.
- A rule you catch yourself writing a second time gets encoded as a lint, a metadata flag, a runtime check, or a script instead of more prose. Every rule moved out of text and into a gate is a rule you stop paying for on every run.
- When a playbook step depends on a project skill that does not exist here yet (a Feature Map, a verification harness), that dependency is the next thing to build, in build order: verification harness and Feature Map first, maintenance automation for both, one CI gate for the failure agents repeat most, then playbooks for the three most common task shapes.
