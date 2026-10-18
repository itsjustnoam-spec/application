# Grill With Docs

Find out exactly what the user wants **before** anything is planned, so that after the spec is approved the work can run without stopping to ask.

## Inputs
- The feature description.
- `docs/features/<slug>/context.md` and `patterns.md`, written by the explorer. Read both first.
- `docs/CONTEXT.md` (domain glossary) and `docs/adr/` (decision log) if they exist.

## Ground rules
1. **Never ask what the code can answer.** If the answer is in `context.md`, `patterns.md`, or the code, look it up instead. Ask only about intent, behavior, and trade-offs.
2. **Batch questions.** Use `AskUserQuestion` with **up to 4 related questions per round**.
3. **Always recommend.** Each question has 2–4 options, and the first option is your recommendation, labeled "(Recommended)", with a one-line reason in its description. Ground recommendations in the existing patterns.
4. **Be concrete.** Ask "When an entity with the same name exists, should create return 409 or overwrite it?", never "How should errors be handled?".
5. **Challenge the language.** If the user uses a term that conflicts with `docs/CONTEXT.md` or the code (e.g. "item" when the code says "entity"), ask which one is meant, and record the answer in the glossary.

## The unknowns ledger
Keep a running list in `docs/features/<slug>/grill-notes.md`:
```markdown
## Unknowns
- U-1 <question> → status: open | decided: <answer> | assumed: <assumption>
## Decisions
- D-1 <decision> (from U-1)
```
Before every round, add any assumption you are silently making as an unknown. The grill ends only when **no unknown is open or assumed**. Each assumption is either confirmed by the user (it becomes a decision) or asked about.

## Coverage checklist
Go through every item and mark it covered or N/A in the notes. The order is a suggestion; group related items into one round.

- [ ] Behavior: main user flow, step by step
- [ ] Users and permissions: who can do it, and what others see
- [ ] Data: new or changed models, fields, types, nullability, defaults, uniqueness, migration of existing rows
- [ ] API contract: endpoints, methods, request/response shapes, status codes, pagination, filtering
- [ ] Reverse proxy: new or changed routes
- [ ] Errors: every failure mode and what the user sees for it
- [ ] Edge cases: empty, huge, duplicate, concurrent, deleted-in-between, invalid input
- [ ] Cross-service effects: RabbitMQ messages (schema, who consumes them), Temporal workflows (retries, timeouts, idempotency)
- [ ] UI: views, dialogs, states (loading / empty / error / success), tooltips, where it lives in navigation
- [ ] Patterns: for every inconsistency `I-n` in `patterns.md`, which side to follow, and confirmation of every pattern that will be reused
- [ ] Non-goals: what explicitly won't be built
- [ ] Backward compatibility: existing clients, existing data, other services' consumers
- [ ] Tests: anything special beyond the defaults (backend: integration + API layers, 100% of new code; frontend: only shared code and important behavior, with no coverage target). Which **user journeys** deserve a browser test (Playwright, mocked backend)? Recommend one happy path per new journey plus its main failure.
- [ ] Missing tooling from `context.md` (e.g. diff-cover): add it as part of this feature, or skip that check?
- [ ] Git: the Jira issue (the branch is `BTRC-<JIRA-ISSUE>-<what-we-do>` in kebab case, e.g. `BTRC-1234-add-authentication`, inside a worktree too), commit per task or one commit at the end, open an MR or not

## Readback
When the ledger is empty, write a **readback** of 5–8 bullets: what will be built, what won't, and the riskiest decision. Ask one final question: "Is this what you want?" with the options "Yes, write the spec (Recommended)" and "No, I'll correct it". Loop until the user says yes.

## Docs updates
- New or clarified domain terms go in `docs/CONTEXT.md` (create it if missing): `**Term**: definition. Code name: X.`
- Decisions that will matter beyond this feature (a new convention, an architecture choice) get a short ADR in `docs/adr/NNNN-<title>.md`: context, decision, consequences.
- Everything else stays in `grill-notes.md`.

## Output
- `docs/features/<slug>/grill-notes.md` with every unknown decided.
- Any updates to `docs/CONTEXT.md` and `docs/adr/`.
