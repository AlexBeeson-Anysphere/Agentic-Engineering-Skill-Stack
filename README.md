# Beeson Agentic Engineering Skill Stack

This repository is a Cursor plugin and a Claude Code plugin. It packages the skills for building and maintaining a software system with a coding agent: a feature map, a verification rig, a playbook router, review and parallel-work skills, and the engineering principles those playbooks select.

Install the plugin once. Then, in the application repository, ask for a skill by name or with its slash command. The plugin does not copy itself into the application. Skills that create project files write those files into the application repo (`agent-map/`, `.cursor/skills/run-verification-rig/`).

There are 34 skills: 11 operational skills (how the work runs, plus the feature map and verification rig) and 23 principles the router pulls in when a ticket needs them. Each principle is also a skill you can open by name.

## Install in Cursor

The plugin directory is [`plugins/beeson-agentic-engineering`](plugins/beeson-agentic-engineering). It contains [`.cursor-plugin/plugin.json`](plugins/beeson-agentic-engineering/.cursor-plugin/plugin.json) and `skills/`. The marketplace index is [`.cursor-plugin/marketplace.json`](.cursor-plugin/marketplace.json).

### Team marketplace

On a Teams or Enterprise plan, an admin imports the Git repository:

1. Open the Cursor dashboard and go to **Plugins & MCPs**.
2. Under **Team Marketplaces**, choose **Add Marketplace**.
3. Choose **Import from Repo** and paste the repository URL.
4. In Cursor, open **Customize**, find **Beeson Agentic Engineering**, and choose **Install**. Pick **User** so it is available in every project, or **Project** so it is shared with that repository.

### This machine

This works on any plan that allows local plugins.

1. Copy `plugins/beeson-agentic-engineering` to `~/.cursor/plugins/local/beeson-agentic-engineering`. The destination must contain `.cursor-plugin/plugin.json` and `skills/`.
2. Reload the window (**Developer: Reload Window**).
3. Open **Customize** and confirm **Beeson Agentic Engineering** is installed and that `initiate-playbook-router` is listed.

On Enterprise, local imports follow the admin setting **Allow Local Plugin Imports** under **Dashboard → Settings → Security & Identity → Marketplace and Plugins**. The setting is off by default, and it also controls **Import from Disk** in **Customize**. Copy the directory into `~/.cursor/plugins/local`. A symlink that points outside that folder is skipped.

In chat, `/add-plugin` plus the Git repository URL registers a personal marketplace from this repo. Personal GitHub imports have been reported to stay on the first commit they indexed. Use the local copy or a team marketplace when you need later commits.

### Confirm

In a new agent chat, type `/initiate-playbook-router`. The command should resolve to the installed skill. Cloning this repository into an application repo does not, by itself, load the skills.

## Install in Claude Code

The Claude Code marketplace index is [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json). The plugin manifest is [`plugins/beeson-agentic-engineering/.claude-plugin/plugin.json`](plugins/beeson-agentic-engineering/.claude-plugin/plugin.json). The marketplace name and the plugin name are both `beeson-agentic-engineering`.

### From Git

Replace `<owner>/<repo>` with the GitHub repository that contains this plugin.

```bash
claude plugin marketplace add <owner>/<repo>
claude plugin install beeson-agentic-engineering@beeson-agentic-engineering
```

Inside a session:

```text
/plugin marketplace add <owner>/<repo>
/plugin install beeson-agentic-engineering@beeson-agentic-engineering
```

Add `--scope project` on `claude plugin marketplace add` when the marketplace registration should be committed for the team. The default scope is the current user.

### From a local checkout

```bash
claude plugin marketplace add /absolute/path/to/this/repo
claude plugin install beeson-agentic-engineering@beeson-agentic-engineering
```

For one session, without installing:

```bash
claude --plugin-dir /absolute/path/to/this/repo/plugins/beeson-agentic-engineering
```

### Confirm

Start a new session and run `/initiate-playbook-router`. The skill list for the plugin should include the catalog below.

## How to use a skill

Slash commands use the skill `name` from its frontmatter, which matches the directory name. Example: `/establish-feature-map`.

Most skills set `disable-model-invocation: true`. They start when you name them or type the slash command. `initiate-playbook-router` and `improve-skill` can also be selected from the wording of the request.

Shell commands inside the map and rig skills use `$SKILL_DIR`, the directory of the `SKILL.md` the agent already opened, and sibling directories next to it. Those paths resolve inside the installed plugin. They do not require a copy under `~/.cursor/skills/`.

The router keeps a working copy of each principle in [`plugins/beeson-agentic-engineering/skills/initiate-playbook-router/principles`](plugins/beeson-agentic-engineering/skills/initiate-playbook-router/principles) and reads that copy while a playbook is running. Opening `/principle-prove-it-works` loads the matching skill.

## Catalog

### Running the work

| Skill | Use |
| --- | --- |
| [initiate-playbook-router](plugins/beeson-agentic-engineering/skills/initiate-playbook-router/SKILL.md) | Routes a substantial request to one playbook, selects a few engineering principles, and requires evidence before reporting success. Use for vague tickets, bugs, features, refactors, investigations, performance work, and migrations. |
| [arena](plugins/beeson-agentic-engineering/skills/arena/SKILL.md) | Runs several attempts at the same artifact, picks a base, and grafts the strongest parts of the others into it. Use when one draft would lock in the wrong shape. |
| [swarm](plugins/beeson-agentic-engineering/skills/swarm/SKILL.md) | Fans out parallel workers across slices or a race and returns one report. Use for coverage, gauntlets, and exploration. |
| [interrogate](plugins/beeson-agentic-engineering/skills/interrogate/SKILL.md) | Sends one diff to independent reviewers and returns a synthesized verdict. Use to stress-test a change before merge. |
| [improve-skill](plugins/beeson-agentic-engineering/skills/improve-skill/SKILL.md) | Proposes a change to an existing skill and evaluates it against the current text. The original stays in place until you promote the proposal. |
| [bro](plugins/beeson-agentic-engineering/skills/bro/SKILL.md) | Restates the last message in plain language, with the jargon removed. |

### Feature map and verification

These skills write into the application repository. The feature map is the index agents read before searching the tree. The verification rig is how they launch and drive the real application.

| Skill | Use |
| --- | --- |
| [establish-feature-map](plugins/beeson-agentic-engineering/skills/establish-feature-map/SKILL.md) | Builds `agent-map/` from scratch: an index plus one file per user-facing feature, with behavior, code touchpoints, verification steps, and gotchas. Works across web, mobile, API, CLI, workers, and monorepos. |
| [maintain-feature-map](plugins/beeson-agentic-engineering/skills/maintain-feature-map/SKILL.md) | Lints `agent-map/` against code drift. Updates only dirty or new features, and separates map drift from product regressions. |
| [establish-verification-rig](plugins/beeson-agentic-engineering/skills/establish-verification-rig/SKILL.md) | Builds a project-local rig at `.cursor/skills/run-verification-rig/` that launches the app, checks that it is actually up, drives a feature, saves evidence, and tears the run down. Proves one live feature before hand-off. |
| [maintain-verification-rig](plugins/beeson-agentic-engineering/skills/maintain-verification-rig/SKILL.md) | Re-drives every mapped feature on a schedule or after a risky change. Separates product bugs, stale map files, and gaps in the rig. |
| [audit-agentic-development-guardrails](plugins/beeson-agentic-engineering/skills/audit-agentic-development-guardrails/SKILL.md) | Scores how much of an architecture standard is enforced mechanically (types, lint, CI, gate governance, and the escape loop). Read-only on the target repo. Returns a level from 0 to 4, a weighted rubric, and a roadmap. |

### Engineering principles

The router selects the smallest set that changes a decision on the current ticket. You can also open one directly when the situation matches.

| Skill | Use |
| --- | --- |
| [principle-attack-the-premise](plugins/beeson-agentic-engineering/skills/principle-attack-the-premise/SKILL.md) | When two fixes that share a premise fail the same check, census which actors hold the imbalance and question the premise. |
| [principle-boundary-discipline](plugins/beeson-agentic-engineering/skills/principle-boundary-discipline/SKILL.md) | Put validation, parsing, and error handling at the edges (CLI, config, network, external APIs). Keep business logic in pure functions. |
| [principle-build-the-lever](plugins/beeson-agentic-engineering/skills/principle-build-the-lever/SKILL.md) | For a non-trivial edit, migration, analysis, or check, build the script or skill that does the job or proves it, so a reviewer can rerun it. |
| [principle-encode-lessons-in-structure](plugins/beeson-agentic-engineering/skills/principle-encode-lessons-in-structure/SKILL.md) | When the same correction shows up a second time, encode it as a lint, a check, a metadata flag, or a script. |
| [principle-exhaust-the-design-space](plugins/beeson-agentic-engineering/skills/principle-exhaust-the-design-space/SKILL.md) | For a new interaction or architecture with no local precedent, build two or three prototypes and compare them before committing. |
| [principle-experience-first](plugins/beeson-agentic-engineering/skills/principle-experience-first/SKILL.md) | When product scope and polish trade off, ship fewer finished behaviors. |
| [principle-fix-root-causes](plugins/beeson-agentic-engineering/skills/principle-fix-root-causes/SKILL.md) | Reproduce a failure, ask why until the cause is in hand, and fix it there. |
| [principle-foundational-thinking](plugins/beeson-agentic-engineering/skills/principle-foundational-thinking/SKILL.md) | Choose the data structures and the scaffold before writing the logic that depends on them. |
| [principle-guard-the-context-window](plugins/beeson-agentic-engineering/skills/principle-guard-the-context-window/SKILL.md) | When files, logs, or fan-out would fill the main thread, send the bulk to subagents and keep the summary. |
| [principle-laziness-protocol](plugins/beeson-agentic-engineering/skills/principle-laziness-protocol/SKILL.md) | Prefer deletion and the smallest change that solves the problem. |
| [principle-make-operations-idempotent](plugins/beeson-agentic-engineering/skills/principle-make-operations-idempotent/SKILL.md) | Design commands, lifecycle steps, and processing loops so a retry after a crash reaches the same end state. |
| [principle-migrate-callers-then-delete-legacy-apis](plugins/beeson-agentic-engineering/skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md) | When replacing an internal API, migrate the callers and delete the old API in the same change. |
| [principle-minimize-reader-load](plugins/beeson-agentic-engineering/skills/principle-minimize-reader-load/SKILL.md) | When code is hard to trace, collapse pass-through layers and shrink the state a reader has to hold. |
| [principle-model-the-domain](plugins/beeson-agentic-engineering/skills/principle-model-the-domain/SKILL.md) | When logic is stateful or a shape is repeated across files, encode the domain in a structure so invalid combinations cannot be represented. |
| [principle-never-block-on-the-human](plugins/beeson-agentic-engineering/skills/principle-never-block-on-the-human/SKILL.md) | Do reversible work and show the result. Ask before irreversible actions. |
| [principle-outcome-oriented-execution](plugins/beeson-agentic-engineering/skills/principle-outcome-oriented-execution/SKILL.md) | During a planned rewrite, converge on the target design. Skip throwaway compatibility steps between phases. |
| [principle-prove-it-works](plugins/beeson-agentic-engineering/skills/principle-prove-it-works/SKILL.md) | Before calling work done, exercise the real artifact: run the feature, read the stored value, or inspect the diff. |
| [principle-redesign-from-first-principles](plugins/beeson-agentic-engineering/skills/principle-redesign-from-first-principles/SKILL.md) | Fold a new requirement into the design as if it had been a foundational assumption. |
| [principle-separate-before-serializing-shared-state](plugins/beeson-agentic-engineering/skills/principle-separate-before-serializing-shared-state/SKILL.md) | When concurrent actors might write the same file, branch, or key, give them separate state. Share one writer only when that is a real invariant. |
| [principle-sequence-verifiable-units](plugins/beeson-agentic-engineering/skills/principle-sequence-verifiable-units/SKILL.md) | Split a sweep, migration, or stack of changes so each unit ends in a check, and check it before the next. |
| [principle-subtract-before-you-add](plugins/beeson-agentic-engineering/skills/principle-subtract-before-you-add/SKILL.md) | Delete dead code and redundant checks before building the new design on top. |
| [principle-test-behavior-not-implementation](plugins/beeson-agentic-engineering/skills/principle-test-behavior-not-implementation/SKILL.md) | Call the code the way its users do and assert the result they observe. |
| [principle-type-system-discipline](plugins/beeson-agentic-engineering/skills/principle-type-system-discipline/SKILL.md) | Make illegal states unrepresentable, parse external data at the boundary, and derive types from the authoritative schema. |

## Sample usage

This is one pass over a standard internal operations application: a staff web UI, an HTTP API, a relational database, SSO, and a worker that issues invoices, sends email, and runs a nightly reconciliation. CI runs on pull requests. The same sequence applies to a customer-facing product with the same parts. Names below are the features a user would recognize.

Install this plugin in Cursor or Claude Code before the first session in the application repo.

### 1. Make the repo legible, then provable

Start here, before feature work. The router assumes both layers exist.

1. Run `/establish-feature-map`. The agent slices the product into features and writes `agent-map/`. For this application that is sign-in, customer accounts, orders, billing, admin, and the invoice worker, in the order you would regression-test them. Each file records what the user does, which code owns it, how to drive it, and what usually lies.
2. Run `/establish-verification-rig`. If `agent-map/` is missing, this skill runs the feature map first. It writes `.cursor/skills/run-verification-rig/` in the application repo: how to launch from a scratch directory, how to tell that the app is ready, how to drive a feature, where evidence is stored, and how to stop only the processes that run started. It then drives one real feature, such as sign-in or creating an order, and keeps the evidence after cleanup.

After this, an agent can open `agent-map/README.md`, read one feature file, and drive that feature with the rig. It does not start by searching the tree.

### 2. Build a feature

Finance wants credit memos on an order: a staff action in the web UI, an API that records the memo and an audit row, money stored as a typed amount, and a worker job that emails the PDF.

Ask the agent to take the ticket through `/initiate-playbook-router`. The router sends new behavior to the feature playbook and selects a small set of principles. On this ticket that is typically:

- `/principle-model-the-domain` for memo states (draft, issued, voided) so those states cannot be combined illegally
- `/principle-boundary-discipline` and `/principle-type-system-discipline` at the API boundary, where the request is parsed into a money type
- `/principle-prove-it-works`, which means drive the new journey with `.cursor/skills/run-verification-rig/` and keep the evidence

The agent implements in slices that can be checked: the domain type, the API, the UI action, the worker job. When the shape of the storage is genuinely unsettled (an order event versus its own table), run `/arena` on that decision and keep one grafted result. Before merge, run `/interrogate` on the diff. Use `/swarm` when the API, the worker, and the admin UI can be checked as separate slices.

Then run `/maintain-feature-map` so the order and billing feature files match the code that landed.

### 3. Fix a production bug

Credit-memo emails show the pre-tax total. Ask for `/initiate-playbook-router` and describe the bug. The router sends it to the bug-fix playbook: reproduce the email on the rig, find the cause, fix that cause, and show the same drive failing before the fix and passing after it. `/principle-fix-root-causes` is the principle that keeps the change on the cause.

### 4. Answer a slowness with a measurement

The billing admin page times out for large accounts. The router sends a measured slowness to the performance playbook: record a baseline on the rig or the existing benchmark, then show the same measurement after the change. A question about why the page is slow, with no request to change it, stays a read-only investigation.

### 5. Keep the map, the rig, and the gates honest

Run these on a cadence, or after a large change:

- `/maintain-feature-map` when code has moved and the map may be stale
- `/maintain-verification-rig` to re-drive every feature in `agent-map/` and separate a product regression from a stale selector or a startup command that changed
- `/audit-agentic-development-guardrails` once a quarter, or when the team wants to know whether architecture rules are enforced by CI and types or only described in prose. The report is a level from 0 to 4 plus a roadmap. It does not modify the application.

### 6. Explain the work, and repair a skill that misleads

`/bro` rewrites the last status update in plain language for someone who wants the outcome (credit memos email the right total, the billing page stays under the timeout) and does not want the playbook names.

When a skill gives a wrong instruction a second time, run `/improve-skill` against that `SKILL.md`. It writes a proposal and compares it with the current skill. It leaves the original in place.

## Layout

```text
.cursor-plugin/marketplace.json          Cursor marketplace index
.claude-plugin/marketplace.json          Claude Code marketplace index
plugins/beeson-agentic-engineering/
  .cursor-plugin/plugin.json             Cursor plugin manifest
  .claude-plugin/plugin.json             Claude Code plugin manifest
  skills/<skill-name>/SKILL.md           one directory per skill
scripts/validate_plugin.py               checks manifests, skill names, and this README
```

Cursor and Claude Code both discover skills as `skills/<name>/SKILL.md` under the plugin root. A new skill is a new directory there whose frontmatter `name` matches the directory name. Add a row to the catalog in this README. `python3 scripts/validate_plugin.py` fails when a skill is missing from the catalog, or when a catalog link has no skill.

The engineering principles are flat skill directories, siblings of the router. Links between principles stay `../principle-<name>/SKILL.md`.

## Check the package

From the repository root:

```bash
python3 scripts/validate_plugin.py
```

A passing run prints the skill count and confirms both marketplace entries resolve to a plugin manifest.
