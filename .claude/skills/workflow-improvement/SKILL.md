---
name: workflow-improvement
description: Rules for turning evidence (a finished session, GitLab merge request reviews) into concrete improvements of the Claude setup (CLAUDE.md, convention skills, checklists, new skills or commands, hooks, reviewer agents) and for applying them safely. Used by /retro and /review-mrs.
disable-model-invocation: true
---

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
| 1 | **Hook / script check** (`.claude/scripts/`) | A rule that a script can check reliably was broken | Judgment calls |
| 2 | **Existing convention skill + its checklist** | A coding or testing rule for a stack an existing skill already covers | Project facts |
| 3 | **Reviewer agent** (`.claude/agents/review-*.md`) | A reviewer missed a class of problem, or produced false positives | New coding rules (those go to #2, which the reviewer already reads) |
| 4 | **Workflow skill or command** (`feature`, `grill-with-docs`, `write-spec`, `test-plan`) | A phase of the workflow went wrong (bad questions, a weak spec, a missing test layer) | Coding rules |
| 5 | **Root `CLAUDE.md`** (or a service's own `CLAUDE.md`) | A project fact needed in most sessions: architecture, where things live, run/test commands, gotchas | Style rules, long procedures |
| 6 | **`docs/CONTEXT.md` / `docs/adr/`** | A domain term, or a decision with lasting consequences | Anything Claude must follow while coding |
| 7 | **New convention skill** | At least 3 related rules for an area no skill covers (e.g. Temporal, RabbitMQ, SQLModel) | One or two rules (add them to the closest existing skill instead) |
| 8 | **New workflow skill or command** | A repeated multi-step procedure with a clear trigger | One-off tasks |
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

- **Convention skill:** add the rule in the right section of `SKILL.md`, then add a checklist item to `references/checklist.md` with the **next free ID** (e.g. `PY-29`). Never renumber or reuse IDs: old review files refer to them.
- **CLAUDE.md:** create it if missing. Keep the sections `Architecture`, `Where things live`, `Commands`, `Gotchas`. Keep each line a fact, and keep the file under about 200 lines.
- **New skill:** `.claude/skills/<kebab-name>/SKILL.md` with frontmatter `name`, `description` (starts with "Use when …", or for workflow-internal skills, says what it's for and who uses it), and the invocation setting from §6. Keep it under about 200 lines and put details in `references/`. If it adds rules a reviewer should check, add `references/checklist.md` and add the skill to the file-type routing in `agents/review-conventions.md`.
- **New command:** `.claude/commands/<name>.md` with `description`, `argument-hint`, and `disable-model-invocation: true`.
- **Hook or script change:** add or update tests in `.claude/scripts/tests/`, and run them (`uv run --with pytest pytest .claude/scripts/tests`) before reporting it as applied. A broken hook blocks every edit.
- **YAML frontmatter:** wrap a `description` in double quotes if it contains `: `, otherwise the frontmatter fails to parse and the item loads with no metadata.
- After applying, list every file you changed.

---

## 6. Model-invocation policy (for every skill and command)

`disable-model-invocation: true` means Claude can't load the item on its own: only the user (`/name`) or an explicit instruction to **read the file by path** can. It also keeps its description out of the context in every session.

| Kind | Setting | Why |
|---|---|---|
| Convention and test-convention skills (`*-conventions`, `backend-test-infra`) | omit (model-invoked) | Claude must load them by itself whenever it touches that kind of code, inside or outside `/feature`, and the review agents load them too |
| Workflow-phase skills used by a command (`grill-with-docs`, `write-spec`, `test-plan`, `workflow-improvement`) | `true` | Only meaningful inside their command. Loading them on their own would start a grill or create workflow files in the middle of an unrelated task. The commands read them by path |
| Commands (`feature`, `retro`, `review-mrs`) | `true` | Long-running, they write files, and they're started on purpose by the user |
| A new skill | Decide with this table, and state the reason in the improvements document | |

If a command or skill needs a `true` skill, it must say "Read `.claude/skills/<name>/SKILL.md`", never "Load the `<name>` skill".
