---
name: git-worktree
description: Use when starting a feature or task that should run in parallel with other work, when the user asks for a worktree, a separate or isolated branch, or parallel sessions, or when /feature starts while another feature is active in this checkout. Explains how to create, enter, set up, resume, and remove a git worktree for a branch in this monorepo.
---

# Git Worktrees (parallel features)

A worktree is a second checkout of the same repository, on its own branch, in its own folder. Each feature in its own worktree means several Claude sessions can work at the same time without touching each other's files.

## 1. Pick the way in

The branch and the worktree folder have the same name: `BTRC-<JIRA-ISSUE>-<what-we-do>` in kebab case, e.g. `BTRC-1234-add-authentication`. Never use a `worktree-` prefix, so `worktree-add-authentication` and `worktree-BTRC-1234-add-authentication` are both wrong.

| Situation | Do this |
|---|---|
| **Already in a worktree** (`git rev-parse --git-dir` differs from `git rev-parse --git-common-dir`) | Nothing. Work here. |
| In a session, starting a feature | Create the worktree with git (§2), then call the **`EnterWorktree`** tool with `path` set to `.claude/worktrees/<branch>`. Never call `EnterWorktree` with `name`: it creates a `worktree-<name>` branch. |
| The user is starting a new terminal | Tell them to create the worktree with git (§2), then run `claude` inside `.claude/worktrees/<branch>`. Not `claude -w`, which also names the branch `worktree-<name>`. |

## 2. Create with git

Keep worktrees under `.claude/worktrees/` in the project, so Claude can enter them without an extra approval prompt. Branch from the remote base branch (usually `main`).

New branch:
```bash
git fetch origin
```

```bash
git worktree add .claude/worktrees/<branch> -b <branch> origin/main
```

Existing branch:
```bash
git worktree add .claude/worktrees/<branch> <branch>
```

## 3. Set up the new worktree

A worktree is a fresh checkout: gitignored things don't exist there.
- **Dependencies:** run `uv sync` in each Python service you'll touch, and `npm install` in each frontend app you'll touch. The root `CLAUDE.md` lists the exact commands.
- **`.env` files:** the repo-root `.worktreeinclude` lists them (gitignore syntax), and Claude Code copies them into every worktree it creates. For a worktree created with plain `git worktree add`, copy them by hand.
- **Feature files:** `docs/features/` is gitignored, so each worktree has its own folder and its own `.active` marker. Run `/feature` and `/feature resume <branch>` **inside** the worktree.
- **Docker infrastructure** (Postgres, Mongo, RabbitMQ, Temporal): don't start a second `docker compose` stack from the worktree, because the ports clash. Reuse the stack that's already running. If tests create databases or queues with fixed names, two worktrees running tests at the same time can collide. Run them one at a time, or use a per-worktree name.

## 4. Pushing

Push the branch under its own name: `git push -u origin <branch>`. Then open the merge request from it.

## 5. Resume, list, remove

- **Resume** in a new terminal: run `claude` inside `.claude/worktrees/<branch>`, then `/feature resume <branch>`.
- **List:** `git worktree list`.
- **Leave** without deleting (inside a session): the `ExitWorktree` tool.
- **Remove** when the branch is merged: `git worktree remove .claude/worktrees/<branch>`, then `git branch -d <branch>`. If git says the worktree is locked, run `git worktree unlock` on it first. Never use `--force` when the worktree has changes the user hasn't confirmed are disposable.
