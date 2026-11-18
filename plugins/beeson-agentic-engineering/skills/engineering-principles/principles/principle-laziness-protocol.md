# Laziness Protocol

Aim for the most result with the least code and complexity.

- **Prefer deletion.** When asked to refactor or improve, look for removals before additions.
- **Maintain a flat hierarchy.** Avoid deep call chains and pass-through stacks. If answering a question requires tracing through more than 3 files or layers, flatten it. This bans stacked layers, not rich interfaces. A module hiding a lot behind a small API is good.
- **Consolidate decisions.** Do not repeat the same choice in several places. Put it behind one source of truth and pass the result as a simple flag.
- **Minimize the diff.** Make the smallest change that solves the problem. Fewer lines beat "elegant" boilerplate.
- **Take small leaks seriously.** Complexity is incremental. An extra flag, one more parameter, a small interface leak each look cheap and compound into system complexity.
- **Question the threading.** If a task asks you to pass a new signal through types, schemas, pipelines, or similar layers, stop and look for a more direct path.

**The test:** If a human developer would find the code exhausting to maintain, it is a bad solution.
