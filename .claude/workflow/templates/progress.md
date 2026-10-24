# Progress: <feature name>

Phase: EXPLORE
<!-- One value only. In order: EXPLORE, GRILL, SPEC, IMPLEMENT, TEST-PLAN, TESTS, REVIEW-ROUND-1 to 4, FIX-ROUND-1 to 3, SUMMARY, GIT, DONE. -->

Base: <the full 40-character SHA from `git merge-base`, nothing after it>
Base branch: <main>
Worktree: <.claude/worktrees/<slug>, or none>
Push: <yes | no, copied from grill-notes.md>
Playwright check: <yes | no | N/A, copied from grill-notes.md>

## Test services
<!-- The compose project named after this branch (git-worktree §3). -->
Compose project: <branch name in lowercase>
Compose files: <the project's compose file> + `docs/features/<slug>/compose.override.yml`
Ports: <service → host port, one per service>

## Test commands
<!-- Filled in once, before the first test run, with the real paths and ports. Phases 6–8 rerun exactly these. -->
- Backend (<service>): `uv run pytest --cov=<package> --cov-report=xml` then `uv run diff-cover coverage.xml --compare-branch=<Base>`
- Frontend (<app>): `npx vitest run`

## Reviewer skills
- conventions-reviewer: <the non-test skills that apply>
- tests-reviewer: <the test skills that apply>

## Tasks
- [ ] TASK-1 <title>
- [ ] TASK-2 <title>

## Deviations
<!-- Anything the spec didn't cover, and the conservative choice made. One line each. -->
- DEV-1 TASK-n: <situation> → <choice> (why)

## Check results
<!-- Latest result of the checks, types, and tests per service. -->
