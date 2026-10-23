# Write Spec & Plan

Produce `spec.md` and `plan.md` in `docs/features/<slug>/` from the templates in `~/.claude/workflow/templates/` (`spec.md`, `plan.md`). After the user approves them, nobody asks the user anything again, so the spec must be complete.

## Preconditions (stop if any one fails)
- `patterns.md` exists.
- `grill-notes.md` has no unknown that is `open` or `assumed`.

## Writing `spec.md`
- Use `~/.claude/workflow/templates/spec.md`. Fill every section, or write `N/A: <why>`. Never delete a section.
- **IDs:** requirements are `REQ-1…`, edge cases `EC-1…`, decisions `D-1…` (copied from grill-notes). Every requirement has testable acceptance criteria: "returns 404 with `EntityNotFoundError` detail", not "handles missing entities".
- **Contracts are exact:** field names, types, nullability, status codes, message schemas. The TS types must mirror the Pydantic/SQLModel schemas field for field.
- **Every decision is traceable:** each `REQ`/`EC` cites the `D-n` it comes from, when it comes from a decision.
- **Technical choices:** list every approach decision from the grill under "Technical choices", with the alternatives that were offered.
- **Git & review:** copy the push answer and the Playwright answer from the grill.
- **Open questions must be empty.** If you discover a new unknown while writing, stop and go back to the grill for it.

## Writing `plan.md`
- Use `~/.claude/workflow/templates/plan.md`.
- Order tasks by dependency: model/migration, then service manager/reader, then API route, then proxy route, then frontend types and client, then components/views. Async pieces (RabbitMQ, Temporal) come right after the code they depend on.
- Every task lists: files, covered `REQ` IDs, **the pattern it follows (`P-n` plus a reference file)**, the existing code it reuses (from "Reusable code" in `context.md`), and a verify command (from the root `CLAUDE.md`, or the service's own scripts).
- **Key details, only for the key parts:** new models and their fields, API contracts, shared components or helpers, and anything risky. For each, say how it will be built: the classes or functions with their signatures, the fields with their types, and where each piece lives, plus a short sketch when the shape isn't obvious. Don't detail every function.
- A task that follows no existing pattern must say `Pattern: NEW, because <reason>`, so the user sees it at the gate.
- Tasks are small: one layer of one service each. Prefer 5–15 tasks over 3 huge ones.
- Tests aren't tasks here. They're planned later in `test-plan.md`, after implementation.

## Self-check before presenting
Go through this list and fix anything that fails:
- [ ] Every `REQ` appears in at least one task
- [ ] Every task cites a `P-n` or explains `NEW`
- [ ] Every inconsistency `I-n` from `patterns.md` is resolved by a decision
- [ ] Every error in the API contract has a status code and a frontend behavior
- [ ] "Open questions" is empty
- [ ] Nothing in the spec contradicts `grill-notes.md`
- [ ] Every approach decision is under "Technical choices", and every key part has its key details in `plan.md`

## Presenting for approval
Show the user a short summary: goal, number of REQs/ECs/tasks, the technical choices, the key details of the riskiest part, every `NEW` pattern, and the riskiest decision. Point them to the two files. Then ask with `AskUserQuestion`: "Approve the spec and plan?" with the options "Approve and start (Recommended)" and "I have changes". On changes, edit the files and ask again.
