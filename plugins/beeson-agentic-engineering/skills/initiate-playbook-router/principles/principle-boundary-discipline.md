# Boundary Discipline

Place validation, type narrowing, and error handling at system boundaries. Trust internal code unconditionally. Business logic lives in pure functions. The shell is thin and mechanical.

**Why:** Scattered validation is noisy, redundant, and gives a false sense of safety. Keep logic out of framework wiring so it can be tested without the framework.

**The pattern:**
- **At boundaries** (CLI args, config files, external APIs, network protocols): validate, return errors, handle defensively.
- **Inside the system:** typed data, error propagation, no re-validation. Trust the types.

**Applications:**

Validation and error handling:
- Validate config at parse time (the boundary), not inside business logic
- Store raw data at boundaries. Parse lazily at use-site
- No redundant nil checks deep in call chains if the boundary already validated

Code organization:
- Keep the general-purpose core separate from special-purpose policy. Adapters hold the special cases
- Don't let domain knowledge leak across the boundary into every caller (information leakage). Hide the decision on one side
- Business logic in pure functions with no framework dependencies
- Parse functions: pure transforms from raw bytes to typed state
- Prompt construction: structured state in, string out
- Scoring and assessment: pure transforms from state to results

**The tests:**
- "Is this data crossing a system boundary right now?" If not, validation is redundant.
- "Can this be a pure function that the shell just calls?" If yes, extract it.
