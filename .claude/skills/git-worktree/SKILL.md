---
name: git-worktree
description: Use when starting a feature or task that should run in parallel with other work, when the user asks for a worktree, a separate or isolated branch, or parallel sessions, or when /feature starts while another feature is active in this checkout. Explains how to create, enter, set up, resume, and remove a git worktree for a branch in this monorepo.
---

# Git Worktrees (parallel features)

A worktree is a second checkout of the same repository, on its own branch, in its own folder. Each feature in its own worktree means several Claude sessions can work at the same time without touching each other's files.

## 1. Pick the way in

The branch and the worktree folder have the same name, built as `~/.claude/CLAUDE.md` → Git says (`BTRC-<JIRA-ISSUE>-<what-we-do>`, never a `worktree-` prefix).

| Situation | Do this |
|---|---|
| **Already in a worktree** (`git rev-parse --git-dir` differs from `git rev-parse --git-common-dir`) | Nothing. Work here. |
| In a session, starting a feature | Create the worktree with git (§2), then call the **`EnterWorktree`** tool with `path` set to `.claude/worktrees/<branch>`. Never call `EnterWorktree` with `name`: it creates a `worktree-<name>` branch. |
| The user is starting a new terminal | Tell them to create the worktree with git (§2), then run `claude` inside `.claude/worktrees/<branch>`. Not `claude -w`, which also names the branch `worktree-<name>`. |

## 2. Create with git

Keep worktrees under `.claude/worktrees/` in the project, so Claude can enter them without an extra approval prompt. Fetch first, then branch from the remote base branch (`origin/<base>`, usually `origin/main`), so the branch starts from the latest code.

New branch:
```bash
git fetch origin
```

```bash
git worktree add .claude/worktrees/<branch> -b <branch> origin/<base>
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
- **Docker services** (Postgres, Mongo, RabbitMQ, Temporal): **never use the ones already running.** They belong to the user's main checkout or to other branches, and tests against them change their data. Before the first test run, start this worktree's own:
  1. **Copy the existing setup, don't invent one.** Read the project's `docker-compose.yml` (also in the main checkout: `git worktree list` shows its path) and, when it doesn't say enough, the running containers (`docker ps`, `docker inspect <container>`): images and versions, environment variables, init scripts, health checks.
  2. Write `docs/features/<branch>/docker-compose.yml` (that folder is git-ignored) with only the services the tests need. Publish each port on a free host port (`"127.0.0.1::5432"`, no fixed host port) and use no named volumes.
  3. Start it: `docker compose -p <branch> -f docs/features/<branch>/docker-compose.yml up -d --wait`.
  4. Read the host ports: `docker compose -p <branch> -f docs/features/<branch>/docker-compose.yml port <service> <container port>`.
  5. Point the test settings in this worktree's own `.env` at those ports (e.g. `TEST_DATABASE_URL`), never at the main checkout's services.
  6. Record the compose project name, the file, and the ports in `progress.md`.
  7. When the feature is done: `docker compose -p <branch> -f docs/features/<branch>/docker-compose.yml down -v`. Always pass `-p <branch>`, so nothing else is touched.

## 4. Pushing

Push the branch under its own name: `git push -u origin <branch>`. Then open the merge request from it.

## 5. Resume, list, remove

- **Resume** in a new terminal: run `claude` inside `.claude/worktrees/<branch>`, then `/feature resume <branch>`.
- **List:** `git worktree list`.
- **Leave** without deleting (inside a session): the `ExitWorktree` tool.
- **Remove** when the branch is merged: `git worktree remove .claude/worktrees/<branch>`, then `git branch -d <branch>`. If git says the worktree is locked, run `git worktree unlock` on it first. Never use `--force` when the worktree has changes the user hasn't confirmed are disposable.
