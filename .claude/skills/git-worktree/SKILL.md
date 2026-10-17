---
name: git-worktree
description: Use when starting a feature or task that should run in parallel with other work, when the user asks for a worktree, a separate or isolated branch, or parallel sessions, or when /feature starts while another feature is active in this checkout. Explains how to create, enter, set up, resume, and remove a git worktree for a branch in this monorepo.
---

# Git Worktrees (parallel features)

A worktree is a second checkout of the same repository, on its own branch, in its own folder. Each feature in its own worktree means several Claude sessions can work at the same time without touching each other's files.

## 1. Pick the way in

| Situation | Do this |
|---|---|
| **Already in a worktree** (`git rev-parse --git-dir` differs from `git rev-parse --git-common-dir`) | Nothing. Work here. |
| In a session, starting a feature | Call the **`EnterWorktree`** tool with the feature slug as the name. It creates `.claude/worktrees/<slug>/` on branch `worktree-<slug>` and moves this session into it. |
| The user is starting a new terminal | Tell them: `claude -w <slug>`, then `/feature ...` inside it. |
| You need a specific base or an existing branch | Create it with git (§2), then call `EnterWorktree` with that path. |

**Check the base before creating.** New worktrees branch from the remote's default branch (`origin/HEAD`). This repo has no `origin/HEAD` set, so it may fall back to the **current local `HEAD`**. If `git branch --show-current` isn't the base branch (usually `main`), create the worktree with git from the right base (§2).

## 2. Create with git (specific base or existing branch)

Keep worktrees under `.claude/worktrees/`, so Claude can enter them without an extra approval prompt.

New branch from a base:
```bash
git worktree add .claude/worktrees/<slug> -b worktree-<slug> origin/main
```

Existing branch:
```bash
git worktree add .claude/worktrees/<slug> <existing-branch>
```

Then call `EnterWorktree` with the path `.claude/worktrees/<slug>`.

## 3. Set up the new worktree

A worktree is a fresh checkout: gitignored things don't exist there.
- **Dependencies:** run `uv sync` in each Python service you'll touch, and `npm install` in each frontend app you'll touch. The root `CLAUDE.md` lists the exact commands.
- **`.env` files:** the repo-root `.worktreeinclude` lists them (gitignore syntax), and Claude Code copies them into every worktree it creates. For a worktree created with plain `git worktree add`, copy them by hand.
- **Feature files:** `docs/features/` is gitignored, so each worktree has its own folder and its own `.active` marker. Run `/feature` and `/feature resume <slug>` **inside** the worktree.
- **Docker infrastructure** (Postgres, Mongo, RabbitMQ, Temporal): don't start a second `docker compose` stack from the worktree, because the ports clash. Reuse the stack that's already running. If tests create databases or queues with fixed names, two worktrees running tests at the same time can collide. Run them one at a time, or use a per-worktree name.

## 4. Branch names and pushing

The branch is `worktree-<slug>`. Push it under the team's name: `git push -u origin HEAD:feature/<slug>`. Then open the merge request from `feature/<slug>`.

## 5. Resume, list, remove

- **Resume** in a new terminal: `claude -w <slug>` reopens the existing worktree, then run `/feature resume <slug>`.
- **List:** `git worktree list`.
- **Leave** without deleting (inside a session): the `ExitWorktree` tool.
- **Remove** when the branch is merged: `git worktree remove .claude/worktrees/<slug>`, then `git branch -d worktree-<slug>`. If git says the worktree is locked, run `git worktree unlock` on it first. Never use `--force` when the worktree has changes the user hasn't confirmed are disposable.
