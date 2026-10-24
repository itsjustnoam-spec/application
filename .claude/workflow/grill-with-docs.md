# Grill With Docs

Find out exactly what the user wants **before** anything is planned, so that after the spec is approved the work can run without stopping to ask.

## Inputs
- The feature description.
- `docs/features/<slug>/context.md` and `patterns.md`, merged from the explorers. Read both first.
- `docs/CONTEXT.md` (domain glossary) and `docs/adr/` (decision log) if they exist.

## Ground rules
1. **Never ask what the code can answer.** If the answer is in `context.md`, `patterns.md`, or the code, look it up instead. Ask only about intent, behavior, and trade-offs.
2. **Batch questions.** Use `AskUserQuestion` with **up to 4 related questions per round**.
3. **Always recommend.** Each question has 2–4 options, and the first option is your recommendation, labeled "(Recommended)", with a one-line reason in its description. Ground recommendations in the existing patterns.
4. **Be concrete.** Ask "When an entity with the same name exists, should create return 409 or overwrite it?", never "How should errors be handled?".
5. **Ask only what changes the spec.** At most 4 rounds of questions before the readback (the approach round counts as one). Don't ask what the conventions, the patterns, or an earlier answer already decide.
6. **Challenge the language.** If the user uses a term that conflicts with `docs/CONTEXT.md` or the code (e.g. "item" when the code says "entity"), ask which one is meant, and record the answer in the glossary.

## The unknowns ledger
Keep a running list in `docs/features/<slug>/grill-notes.md`:
```markdown
## Unknowns
- U-1 <question> → status: open | decided: <answer> | assumed: <assumption>
## Decisions
- D-1 <decision> (from U-1)
```
**Every time you pick a default or think "probably", add it as an unknown** with status `assumed: <what you'd do>`. The grill ends only when **no unknown is open or assumed**: each assumption is either asked about or listed in the readback for the user to confirm. When the user says "you decide", record `decided: delegated, <the conservative option>` and list it in the readback.

## Approach questions (one round)
After the first round, when you know what will be built, ask about the **technical choices that have real alternatives**: a library, where new code lives, a new component vs extending an existing one, the shape of the data, sync vs async, reusing existing code vs writing new code. For each one:
- Say what you're going to use and why: "I'm going to use X, because …. Do you agree it's the best option?" X is the first option, labeled "(Recommended)".
- Offer 1–3 real alternatives as the other options, each with a one-line trade-off in its description.

Ask at most 4 of these, in one round, and only about choices that matter for the spec. Skip choices the conventions or the existing patterns already decide. Record each answer as a decision `D-n`; the spec lists them under "Technical choices".

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
- [ ] Tests: anything special beyond the defaults (backend: integration + API layers, 100% of new code; frontend: only shared code and important behavior, with no coverage target). There are no browser (Playwright) tests for now: don't ask about them.
- [ ] Playwright UI check: ask only when **both** hold: the feature has a frontend part, and a tool whose name contains `playwright` is available in this session (the Playwright MCP server). Ask one question, "Should I check the UI in the browser with Playwright during review?", with the options "No Playwright" and "Yes, check the UI in review", each with a one-line description. Without a frontend part record `N/A`; without the Playwright tools record `no (Playwright MCP not connected)` and don't ask.
- [ ] Missing tooling from `context.md` (e.g. diff-cover): add it as part of this feature, or skip that check?
- [ ] Git: commit per task or one commit at the end, open an MR or not, and **whether to push at the end**: ask "When the feature is done, may I push on my own and follow the pipeline until it passes?" with the options "Yes, push and follow the pipeline (Recommended)" and "No, I'll push myself"

## Readback
When the ledger is empty, write a **readback** of 5–8 bullets: what will be built, what won't, and the riskiest decision. Ask one final question: "Is this what you want?" with the options "Yes, write the spec (Recommended)" and "No, I'll correct it". Loop until the user says yes.

## Docs updates
- New or clarified domain terms go in `docs/CONTEXT.md` (create it if missing): `**Term**: definition. Code name: X.`
- Decisions that will matter beyond this feature (a new convention, an architecture choice) get a short ADR in `docs/adr/NNNN-<title>.md`: context, decision, consequences.
- Everything else stays in `grill-notes.md`.

## Output
`grill-notes.md` ends with these two lines, exactly in this form, because the spec and `progress.md` copy them:
```
Push: yes | no
Playwright check: yes | no | N/A
```
- `docs/features/<slug>/grill-notes.md` with every unknown decided.
- Any updates to `docs/CONTEXT.md` and `docs/adr/`.
