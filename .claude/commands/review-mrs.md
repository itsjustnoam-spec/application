---
description: Reads one or more GitLab merge requests (diffs, review discussions, fix-up commits) through the GitLab MCP server and writes an improvements document for the Claude setup, then applies the ones you pick. Read-only on GitLab.
argument-hint: "<MR URL or project!iid> [more MRs...]"
disable-model-invocation: true
---

# Learn from merge requests

Merge requests: `$ARGUMENTS`

Read `.claude/skills/workflow-improvement/SKILL.md` first and follow it for every step below.

## 0. Check access
- Find the GitLab MCP tools available in this session: tool names containing `gitlab`, `merge_request`, or `mr`. You need tools to read an MR, its diff/changes, its discussions or notes, and its commits.
- If no GitLab MCP server is connected, stop and tell the user to add one (e.g. `claude mcp add` with their GitLab MCP server and a personal access token with the `read_api` scope), then run the command again.
- If the arguments are empty, ask the user for MR URLs or `group/project!iid` references.

**GitLab is read-only for this command.** Never comment, approve, resolve threads, edit, or merge, even if a tool allows it.

## 1. Gather evidence per MR
For each MR:
1. **Metadata:** title, description, author, labels, target branch, and state.
2. **Diff:** the changed files and hunks. Note which services and layers (backend, frontend, tests) are touched.
3. **Review discussions:** every human comment and thread, with its file, line, and whether it was resolved. These are the main source: they show what the team expects and what Claude (or the author) didn't know.
4. **Commits:** fix-up commits that came after review comments ("address review", "fix lint") show what reviewers keep catching.
5. Ignore bot or CI noise, unless it points to a recurring failure (e.g. the same lint rule failing in several MRs).

For each human comment, classify it:
- **Breaks an existing rule:** the rule exists in a skill or checklist but wasn't followed. Recommend automating it or making it more prominent.
- **Missing rule:** a team expectation that isn't written anywhere. Recommend a new convention.
- **Project fact:** recommend a `CLAUDE.md` or `docs/CONTEXT.md` addition.
- **One-off:** no change. List it under "Considered and rejected".

Look **across** MRs as well: the same kind of comment in two or more MRs gets a higher priority.

## 2. Compare with the current setup
Read the root `CLAUDE.md`, the relevant `.claude/skills/*/SKILL.md` files and checklists, the reviewer agents, and earlier `docs/improvements/` documents before recommending anything, so you don't duplicate an existing rule.

## 3. Write the document
Use the template in the skill. Write to `docs/improvements/<YYYY-MM-DD>-mr-<ids>.md`. Evidence links point to the MR note (URL, or `project!iid` plus `file:line`). Quote only short excerpts of comments.

## 4. Ask what to apply
Show the user a short list (`IMP-n`, priority, title, destination). Ask which to apply: they can answer with IDs, "all high", "all", or "none". Don't apply anything before they answer.

## 5. Apply
Apply only the picked IDs, following the skill's "Apply" section. Update each recommendation's **Status** in the document, then report the files changed.
