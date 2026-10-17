---
description: End-of-session retrospective. Reviews this session and writes an improvements document (new skills, new conventions, CLAUDE.md additions, hook and reviewer fixes), then applies the ones you pick.
argument-hint: "[optional: focus, e.g. 'testing' or a feature slug]"
disable-model-invocation: true
---

# Session retrospective

Focus (optional): `$ARGUMENTS`

Read `.claude/skills/workflow-improvement/SKILL.md` first and follow it for every step below.

## 1. Gather evidence from this session
Use what is in this conversation, plus files on disk:
- **The conversation:** every correction the user made, every instruction they repeated, every question they had to answer that the code or docs could have answered, every hook block, and every error Claude hit (wrong command, missing tool, failed test run).
- **Feature artifacts:** for each feature touched this session (`docs/features/<slug>/`): `grill-notes.md` (questions asked), `progress.md` (deviations, check results), `review/*.md` (findings by category), `review/triage.md` (fixed vs. dismissed), and `summary.md` (anything left open).
- **The diff:** `git diff` and `git log` for this session's commits. Look for patterns in what had to be fixed.
- **The current setup:** the root `CLAUDE.md`, `.claude/skills/*/SKILL.md`, the checklists, `.claude/agents/`, `.claude/commands/`, and `.claude/settings.json`. Read the relevant ones before recommending anything, so you don't duplicate an existing rule.
- **Earlier improvement documents** in `docs/improvements/`: don't re-propose something the user already skipped, unless there is new evidence (and say so).

If a focus was given, concentrate on it, but still report High-priority items from other areas.

## 2. Write the document
Use the template in the skill. Write to `docs/improvements/<YYYY-MM-DD>-session-<topic>.md`. Every recommendation has evidence, a destination from the skill's table, and the exact text to add.

## 3. Ask what to apply
Show the user a short list (`IMP-n`, priority, title, destination). Ask which to apply: they can answer with IDs, "all high", "all", or "none". Don't apply anything before they answer.

## 4. Apply
Apply only the picked IDs, following the skill's "Apply" section. Update each recommendation's **Status** in the document, then report the files changed and anything that couldn't be applied.
