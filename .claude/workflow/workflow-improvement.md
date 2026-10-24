# Workflow Improvement

How to find what should change in the Claude setup, decide **where** each change belongs, write it as a concrete proposal, and apply it without damaging what already works.

The output is always an improvements document (template below). Nothing is changed until the user picks which recommendations to apply.

---

## 1. Collect evidence

Every recommendation needs evidence: a quote, a `file:line`, a finding ID, or an MR note link. No evidence, no recommendation.

| Signal | Usually means |
|---|---|
| The user corrected Claude ("no, we do X", "don't do Y") | A missing or unclear rule |
| The same mistake happened twice or more | A rule exists but isn't followed: automate it or make it more prominent |
| A hook blocked an edit | The rule works. Recommend nothing unless the hook was wrong (false positive) |
| A reviewer finding was **fixed** | Something reached review that should have been prevented earlier |
| A reviewer finding was **dismissed** as a false positive | The reviewer's instructions need tightening |
| A finding came back in a later review round, or a feature needed all 3 fix rounds | The fix approach or the rule behind it is unclear |
| The same finding category shows up across several features (`review/history.md`) | A convention or checklist gap: the strongest signal for a new rule or a hook |
| The grill asked something the code or docs could have answered | A fact missing from `CLAUDE.md` or `docs/CONTEXT.md` |
| Claude had to search for how to run, test, or start something | A command missing from `CLAUDE.md` |
| A `DEV-n` deviation in `progress.md` | A gap in the spec template or a convention |
| A human MR reviewer comment | A team rule or project fact Claude didn't know |
| Fix-up commits after review in an MR | What reviewers keep catching: candidates for checklists and hooks |
| A multi-step procedure done by hand more than once | A candidate for a new skill or command |

---

## 2. Choose the destination

Pick the **first** row that fits. Prefer strengthening something that exists over adding something new: every added line costs context in every session, and smaller models suffer most from bloat.

| # | Destination | Use when | Don't use for |
|---|---|---|---|
| 1 | **Hook / script check** (`~/.claude/scripts/`) | A rule that a script can check reliably was broken | Judgment calls |
| 2 | **Existing convention skill + its checklist** | A coding or testing rule for a stack an existing skill already covers | Project facts |
| 3 | **Reviewer agent** (`~/.claude/agents/review-*.md`) | A reviewer missed a class of problem, or produced false positives | New coding rules (those go to #2, which the reviewer already reads) |
| 4 | **Workflow guide or command** (`~/.claude/workflow/*.md`, `~/.claude/commands/*.md`) | A phase of the workflow went wrong (bad questions, a weak spec, a missing test layer) | Coding rules |
| 5 | **Root `CLAUDE.md`** (or a service's own `CLAUDE.md`) | A project fact needed in most sessions: architecture, where things live, run/test commands, gotchas | Style rules, long procedures |
| 6 | **`docs/CONTEXT.md` / `docs/adr/`** | A domain term, or a decision with lasting consequences | Anything Claude must follow while coding |
| 7 | **New convention skill** | At least 3 related rules for an area no skill covers (e.g. Temporal, RabbitMQ, SQLModel) | One or two rules (add them to the closest existing skill instead) |
| 8 | **New command, workflow guide, or skill** | A repeated multi-step procedure with a clear trigger (choose the form with §6) | One-off tasks |
| — | **Nothing** | It happened once, has low impact, or is already covered | |

---

## 3. Write each recommendation

- **One change per recommendation.** Don't bundle unrelated edits.
- **Check for duplicates and conflicts first:** read the target file. If the rule already exists, the recommendation is to make it clearer, more prominent, or automated, not to add it again. If it contradicts an existing rule, say so and ask the user which one wins.
- **Write the exact text to add** (or a diff for an edit), formatted as it will appear in the target file. "Add a note about X" isn't a recommendation.
- **Never change the core of a convention skill.** Add, clarify, or give examples. Removing or reversing a rule needs the user's explicit choice, so present it as a question in the document.
- **Priority:**
  - **High:** caused a bug, a wrong spec, or repeated corrections
  - **Medium:** cost noticeable time, or caused review churn
  - **Low:** a nice-to-have
- **IDs:** `IMP-1`, `IMP-2`, … in order of priority.

---

## 4. Document template

Write to `docs/improvements/<YYYY-MM-DD>-<source>.md`, where `<source>` is `session-<topic>` or `mr-<ids>`.

```markdown
# Improvements: <source>

Date: <YYYY-MM-DD> · Evidence from: <session topic / MR list>

## Summary
<3–5 bullets: what went well, what went wrong, the top 3 recommendations>

## Recommendations
### IMP-1 <short title> · High
- **Destination:** `<file path>` (<destination type from §2>)
- **Evidence:** <quotes, file:line, finding IDs, MR note links>
- **Why:** <what goes wrong without it>
- **Change:**
  ```
  <exact text to add, or a diff>
  ```
- **Status:** proposed

### IMP-2 …

## Questions for you
- <conflicts between rules, or anything that needs your decision>

## Considered and rejected
- <signal> → no change, because <reason>
```

---

## 5. Apply (only the IDs the user picked)

Apply each picked recommendation and set its **Status** to `applied` (or `skipped: <reason>`).

- **Convention skill:** add the rule in the right section of `SKILL.md`, then add a checklist item to `references/checklist.md` with the **next free ID** (e.g. `PY-29`). Never renumber or reuse IDs: old review files refer to them. Try never to take a skill past about 200 lines; if it already is past that, or the change would take it there, don't cut or move anything on your own: ask the user what to do.
- **CLAUDE.md:** create it if missing. Keep the sections `Architecture`, `Where things live`, `Commands`, `Gotchas`. Keep each line a fact, and keep the file under about 200 lines.
- **New skill:** `~/.claude/skills/<kebab-name>/SKILL.md` with frontmatter `name` and `description` (starts with "Use when …"). Only create a skill if Claude should load it by itself (see §6); otherwise it's a workflow guide. Try never to take a skill past about 200 lines. If a change would, don't cut or move anything on your own: ask the user what to do. If it adds rules a reviewer should check, add `references/checklist.md`, add the skill to the file table in `agents/review-conventions.md`, and add it to one of the two skill lists in phase 7 of `commands/feature.md`.
- **New workflow guide:** `~/.claude/workflow/<name>.md`, plain markdown with no frontmatter, plus templates in `~/.claude/workflow/templates/`. The command that uses it says "Read `~/.claude/workflow/<name>.md`".
- **New command:** `~/.claude/commands/<name>.md` with `description`, `argument-hint`, and `disable-model-invocation: true`.
- **Hook or script change:** add or update tests in `~/.claude/scripts/tests/`, and run them (`uv run --with pytest pytest ~/.claude/scripts/tests`) before reporting it as applied. A broken hook blocks every edit.
- **YAML frontmatter:** wrap a `description` in double quotes if it contains `: `, otherwise the frontmatter fails to parse and the item loads with no metadata.
- After applying, list every file you changed, and tell the user: "These changes are in `~/.claude`. Copy them into the repo's `.claude/` folder and commit them there, or the next `install.sh` will stop and ask about them."

---

## 6. Where instructions live, and who can invoke them

Claude Code refuses a Skill tool call to a skill that has `disable-model-invocation: true`, and tells Claude not to do the steps another way. A workflow that depends on such a skill can therefore stall. So:

| Kind | Form | Why |
|---|---|---|
| Rules Claude must apply on its own whenever it touches that kind of code (`*-conventions` incl. `sql-conventions`, `backend-test-infra`) | Skill, model-invoked (no flag) | Claude and the review agents load them automatically, inside or outside `/feature` |
| Know-how Claude should reach for at the right moment (`git-worktree`) | Skill, model-invoked (no flag) | The description is what triggers it |
| Steps used only inside a command (`grill-with-docs`, `write-spec`, `test-plan`, `workflow-improvement`) | **Plain file in `~/.claude/workflow/`**, not a skill | They'd misfire if loaded on their own, but the commands must be able to read them. A plain file has no invocation rules to block it |
| Commands the user starts on purpose (`feature`, `retro`, `review-mrs`) | Command with `disable-model-invocation: true` | Long-running, they write files, and the user decides when to start them |

**Never** give a skill `disable-model-invocation: true` if a command or another skill depends on it. Make it a workflow guide instead. State the chosen form and the reason in the improvements document for every new item.
