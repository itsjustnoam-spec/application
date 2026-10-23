# Progress: <feature name>

Phase: EXPLORE
<!-- One value only. In order: EXPLORE, GRILL, SPEC, IMPLEMENT, TEST-PLAN, TESTS, REVIEW-ROUND-<n>, FIX-ROUND-<n> (n ≤ 3), DONE. -->

Base: <commit SHA from `git merge-base HEAD origin/<base branch>`>
Base branch: <main>
Worktree: <.claude/worktrees/<slug>, or none>
Push: <yes | no, from the grill>
Playwright check: <yes | no, from the grill>

## Test services
<!-- This branch's own Docker services (git-worktree §3): compose project, file, and host ports. -->
- Compose project: <slug> · file: `docs/features/<slug>/docker-compose.yml` · ports: <service → port>

## Conventions reviewers
- Reviewer 1: <skills>
- Reviewer 2: <skills>

## Tasks
- [ ] TASK-1 <title>
- [ ] TASK-2 <title>

## Deviations
<!-- Anything the spec didn't cover, and the conservative choice made. One line each. -->
- DEV-1 TASK-n: <situation> → <choice> (why)

## Check results
<!-- Latest result of the checks, types, and tests per service. -->
