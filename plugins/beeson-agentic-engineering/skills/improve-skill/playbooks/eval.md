# Eval

Blindly compare the incumbent skill with a proposed skill on realistic tasks. Present the result in a Cursor canvas.

Requires two artifacts:

- Incumbent: the target `SKILL.md` (and its referenced files).
- Proposed: `SKILL.proposed.md` beside it, or another file the user named.

If the proposed file is missing, stop and ask for it. Do not invent a proposal inside this playbook.

## Steps

1. Frame the comparison.
2. Prepare the two environments.
3. Author the organic prompts.
4. Run the candidates.
5. Blind-judge the outputs.
6. Synthesize a recommendation.
7. Publish the canvas.

## Blinding

These rules override convenience.

- Candidate prompts and directory names must not contain: eval, test, judge, experiment, rubric, compare, benchmark, candidate, arena, incumbent, proposed, variant, baseline.
- The task the candidate sees must read like a normal user request.
- Do not tell a candidate that another run, another model, or another skill version exists.
- Directory and file names a candidate can see must look like an ordinary project and ordinary inputs.
- Keep the A/B map, model names, and paths in the parent notes only.
- The judge sees outputs only as "Variant A" and "Variant B". No model names, no paths, no statement of which version is the incumbent.

## 1. Frame the comparison

State, in the parent notes only:

- The proposed file under test, and the incumbent path.
- What success looks like (the user's goal, or the general-quality bar from Propose).
- A rubric of 3–6 concrete criteria. Each criterion must be gradeable from the candidate's final output alone (for example: "the commit message states the user-visible reason", not "the agent tried hard").

Hold the rubric back from candidates.

Assign A/B with a coin flip. Record the map. Do not put the map in any candidate or judge prompt.

## 2. Prepare the environments

Create two directories outside the target repo. Name them like ordinary projects (`weekly-notes`, `invoice-desk`), not after the arm of the comparison.

In each directory:

- Copy the skill tree to `.cursor/skills/<skill-name>/`.
- Incumbent arm: leave those files as they are.
- Proposed arm: overwrite `SKILL.md` with the proposed contents. Overwrite any referenced file that has a `.proposed` sibling, using the normal filename. Do not leave a `*.proposed.*` file in the directory.
- Plant the same minimal project context in both (a README, a sample input, whatever a real request would already have). Names must be ordinary.

The only intended difference between the directories is the skill content.

## 3. Author the organic prompts

Write 1–3 prompts a user would actually send. Each one must exercise the skill's intended behavior and be answerable from the planted context. No meta language. Save the prompts in the parent notes, not in the candidate directories.

Use the same prompts for both arms.

## 4. Run the candidates

Spawn candidates with the Task tool, `subagent_type: generalPurpose`.

Models: read the session's available subagent model slugs. Group them by family (the leading name, ignoring size and effort). Use the same set on every arm. Prefer one slug from each of two families. If only one family is listed, run one candidate per arm and record that limit. Do not hardcode a slug list.

Launch every candidate in one message so they run in parallel. Wait for their results. Do not poll.

Each candidate prompt has two parts and nothing else:

1. Setup, identical except for the directory path: "Do all work in `<dir>`. Before acting, read and follow `<dir>/.cursor/skills/<skill-name>/SKILL.md` and every file it tells you to open. Do not read or copy a skill from outside `<dir>`."
2. The organic prompt, verbatim.

The Task `description` is a short title taken from the organic task. It must not use a forbidden word.

Collect each candidate's final message and any files it wrote inside its directory. Discard scratch that the candidate was not asked for.

## 5. Blind-judge the outputs

Spawn one judge with the Task tool, `subagent_type: generalPurpose`. Use a model family that did not produce the candidate outputs when a remaining family exists.

The judge prompt contains only:

- The rubric.
- The organic prompt(s).
- Each run's final output and relevant artifacts, labeled only "Variant A" or "Variant B". Strip model names, directory names, and skill filenames first.

Ask the judge to score every criterion per variant, then declare a winner or a tie, with reasons tied to the rubric. Do not ask which skill is better. Do not reveal that a skill changed.

## 6. Synthesize a recommendation

Read the candidate outputs and the judge's verdict. Decide:

- **Promote** — the proposed skill won on the rubric, and the losses are minor.
- **Keep** — the incumbent matched or beat the proposal, or the proposal changed intended behavior.
- **Iterate** — the result is mixed, or a criterion the proposal was supposed to fix did not move.

State one disagreement if your reading and the judge's verdict diverge, and which one you are following. Do not promote from a tie unless the user's goal was met and nothing regressed.

## 7. Publish the canvas

Read `~/.cursor/skills-cursor/canvas/SKILL.md` and follow it, including its pre-delivery self-check. Read `~/.cursor/skills-cursor/canvas/sdk/index.d.ts` before using a component.

Write one file directly at `~/.cursor/projects/<workspace>/canvases/<skill-name>-skill-comparison.canvas.tsx`. Do not create the directory yourself. Do not add helper files. Import only from `cursor/canvas`. Embed the data inline. Colors come from `useHostTheme()` tokens.

The canvas must show:

- A header with the recommendation and the overall winner (incumbent, proposed, or tie). The header may name the arms; the judge prompt must not.
- The key changed sections of incumbent vs proposed, using `DiffView` where there is a real diff.
- The rubric and per-variant scores in a `Table`.
- The judge's reasoning.
- Short excerpts from the candidate runs, labeled by arm after unblinding.
- Three actions in a `Row`: "Promote proposed skill", "Keep incumbent", and "Iterate". Use `Button` and `useCanvasAction` `newComposerChat`. Each `userPrompt` must name the incumbent path and the proposed path and state the one action. Buttons do not edit files themselves.

After writing, open the canvas with `open_resource` when that tool is available. In chat, give the absolute canvas path and the recommendation in a few sentences: winner, the criterion that decided it, and what you would do next.
