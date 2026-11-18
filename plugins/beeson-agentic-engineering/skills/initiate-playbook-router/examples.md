# Routing examples

Each example shows the request as a user would actually type it, the route, and why. The vague ones are the point: the playbook supplies the steps the ticket did not.

## Vague ticket in, fixed procedure out

**Request:** "export is broken for some users, sort it out"

Route: **bug-fix**. The playbook supplies what the ticket lacks: reproduce on the matching surface first, binary-search the cause with runtime evidence, delegate the fix, re-run the original repro, land the failing repro before the fix in history. The agent's first message restates the goal, names bug-fix, and names the verification surface. It does not ask which users, which export, or where to start: reproduction answers the first two, and the Feature Map feature file for export answers the third.

**Request:** "make search faster"

Route: **perf-issue** if a measurement exists or can be taken ("faster" against what baseline is the first step, not a question to the user: the playbook captures a baseline trace first). Route to **hillclimb** only if the user names a target and wants sustained optimisation ("get p95 under 200ms, keep going until you hit it"). Route to **prototype** first if "faster" turns out to be a perceived-latency design question that an observation settles.

## Tie-breaks in action

**Request:** "the app leaks memory overnight"

Route: **runtime-forensics**, not bug-fix. No mechanism is known yet, and the deliverable the user needs first is a diagnosis: capture the live signal, reduce it to the retainer chain, prove the mechanism, map it to source. When the cause is confirmed, the router re-routes to bug-fix for the fix, visibly: remaining forensics items marked `skip: re-routed to bug-fix`.

**Request:** "tidy up the billing module, it's a mess, also invoices sometimes double-charge"

Two routes, sequenced. The double-charge is a defect: **bug-fix** first, because a refactor over a live bug buries it. The tidy-up is **refactoring**, and it pins current billing behaviour (including, now, the fixed charge behaviour) before structure moves. One request, two playbooks, defect first.

**Request:** "should the settings page be one long form or tabs?"

Do not ask. Route: **prototype**. That fork is settled by observing both layouts, not by preference polling. Build both behind a switcher in a scratch dir, screenshot each, present tradeoffs and a recommendation. The chosen direction then routes to **feature** for the real build.

**Request:** "land the stack"

Route: **shipping**, not babysit. Shipping begins where babysit ends: independent verdicts first (from agents that did not write the code), then only the contiguous verified run lands, bottom-up. If the stack is not yet green, shipping's step 1 sends it back: get it merge-ready in babysit, then return.

## Light exit

**Request:** "rename `getUser` to `fetchUser` in `src/auth.ts` and run the auth tests"

No route. File, change, and check are all named. The agent does it directly, runs the tests, and says it skipped the router because the task was fully specified. Routing this would be ceremony, and ceremony is how routers get switched off.

## No playbook fits

**Request:** "migrate the whole test suite from the old runner to the new one, I'll review when I get back"

Route: **figure-it-out**. The deliverable before any code is the workflow itself: definition of done as a falsifiable predicate (suite green on the new runner, same test count or an accounted delta), quantified scope, rigor level, riskiest units first, verification harness built before the migration with the baseline captured from the old runner. The designed phase list is then copied into the task list verbatim and run like any playbook, with a decision trail the user reads on return.
