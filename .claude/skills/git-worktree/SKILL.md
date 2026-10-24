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
- **`.env` files** aren't in git, so a new worktree has none. Copy them from the main checkout (the first path in `git worktree list`): list them with `git -C <main checkout> ls-files --others --ignored --exclude-standard | grep -E '(^|/)\.env(\..*)?$' | grep -v node_modules`, then copy each one to the same path in the worktree.
- **Feature files:** `docs/features/` is gitignored, so each worktree has its own folder and its own `.active` marker. Run `/feature` and `/feature resume <branch>` **inside** the worktree.
- **Docker services** (Postgres, Mongo, RabbitMQ, Temporal): tests use **only the compose project named after this branch**. Never use any other container: the others belong to the user's main checkout or to other branches, and tests against them change their data.
  1. **The project name** is the branch name in lowercase (Docker rejects capitals): `BTRC-1234-add-authentication` → `btrc-1234-add-authentication`. Call it `<project>`, write it on the `Compose project:` line of `progress.md`, and use exactly that name in every command below.
  2. **If it's already running, use it:** `docker compose ls --filter name=<project>`. When it's listed, skip to step 6.
  3. **Otherwise create it from the project's own compose file**, never a new one: the `docker-compose.yml` (or `compose.yml`) in the current directory, or else the one in the project root of the main checkout (outside the worktree: the first path in `git worktree list`). Call it `<compose file>`.
  4. **Write an override** at `docs/features/<branch>/compose.override.yml` (that folder is git-ignored) for each service the tests need, so this copy never clashes with the running one:
     ```yaml
     services:
       postgres:
         container_name: !reset null
         ports: !override
           - "127.0.0.1::5432"
     ```
     `ports: !override` replaces the fixed host ports with free ones (keep the container port), and `container_name: !reset null` drops a fixed name when the service has one. Named volumes are already per project. When a service has no `healthcheck`, add one in the override (Postgres: `pg_isready -U <user> -d <db>`; Mongo: `mongosh --quiet --eval "db.runCommand({ping: 1})"`), so `--wait` waits until it accepts connections.
  5. **Start only those services:** `docker compose -p <project> -f <compose file> -f docs/features/<branch>/compose.override.yml up -d --wait <service> <service>`.
  6. **Read the host ports:** `docker compose -p <project> port <service> <container port>`.
  7. Point the test settings in this worktree's own `.env` at those ports (e.g. `TEST_DATABASE_URL`). Write the compose file, the override, and the ports in `progress.md`.
  8. When the feature is done: `docker compose -p <project> down -v`. Always pass `-p <project>`, so nothing else is touched.

## 4. Pushing

Push the branch under its own name: `git push -u origin <branch>`. Then open the merge request from it.

## 5. Resume, list, remove

- **Resume** in a new terminal: run `claude` inside `.claude/worktrees/<branch>`, then `/feature resume <branch>`.
- **List:** `git worktree list`.
- **Leave** without deleting (inside a session): the `ExitWorktree` tool.
- **Remove** when the branch is merged: `git worktree remove .claude/worktrees/<branch>`, then `git branch -d <branch>`. If git says the worktree is locked, run `git worktree unlock` on it first. Never use `--force` when the worktree has changes the user hasn't confirmed are disposable.
