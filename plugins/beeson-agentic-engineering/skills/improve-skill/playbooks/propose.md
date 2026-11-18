# Propose

Write an improved version of the target skill. Leave the original untouched.

## Steps

1. Read the incumbent.
2. Set the success criteria.
3. Analyze the current skill.
4. Draft the proposed skill.
5. Write the proposal beside the original.
6. Summarize and stop.

## 1. Read the incumbent

Read `SKILL.md` in full. Read every file it links, plus scripts and sibling references it tells the agent to open. Note the skill name, frontmatter shape, and directory layout.

## 2. Set the success criteria

- The user gave a concrete improvement goal → that goal is the success criteria. Do not widen it.
- No goal → improve clarity, concision, stronger guidance, better examples, and less redundancy. Preserve the intended behavior, triggers, and outputs.

## 3. Analyze the current skill

Write a short private analysis covering:

- What it does well and must keep.
- Where it is ambiguous, verbose, missing an edge case, or likely to be skipped.
- Instructions that restate model knowledge, duplicate another section, or conflict.

Do not show this analysis as a redesign essay. Use it to decide the edits.

## 4. Draft the proposed skill

Produce the full proposed `SKILL.md`. Edit in place conceptually: same skill name and frontmatter shape unless the user asked to rename or restructure. Keep `description` in third person, with what the skill does and when to use it.

Prefer fewer, more imperative lines over new sections. Keep the body under 500 lines. Move long reference material to a sibling file only when the incumbent already uses that pattern, or when the body would otherwise exceed 500 lines.

If a referenced file must change, draft the full replacement. In the proposed `SKILL.md`, keep the normal filenames (the names the skill would use after promotion).

## 5. Write the proposal beside the original

Write `SKILL.proposed.md` in the same directory as the incumbent `SKILL.md`. If a referenced file changed, write `<name>.proposed.<ext>` beside that file.

Do not modify the original files. Do not replace `SKILL.md`. Do not commit.

## 6. Summarize and stop

In chat, give a short list: each change, and why it meets the success criteria. Point at the proposed file path.

Stop. Do not apply the change. If the user asked for a full improve-and-eval cycle, continue to [eval.md](eval.md) and use `SKILL.proposed.md` as the proposed skill.
