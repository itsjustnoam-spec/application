# How to work

## Think before coding
- State your assumptions. When a request can be read more than one way, say so and ask instead of guessing.
- When something is unclear, stop and name what's confusing.
- For a technical choice with real alternatives (a library, where code lives, a new component vs extending one), say what you'd use and why, offer the alternatives with their trade-offs, and let the user decide.
- Inside `/feature`, after the plan is approved, don't ask: choose the conservative option, log it as a `DEV-n` line in `progress.md`, and continue.

## Keep it simple
- Write the least code that solves the task. No features, options, or abstractions nobody asked for.
- When behavior depends on a type or key, prefer one generic mapping (a dict of type → handler) over a chain of ifs.
- Before writing something new, search for existing code that already does it, or would with a small change (a new parameter, a generic type). Reuse it instead of writing it again.

## Make surgical changes
- Never change an existing line the task doesn't need: no refactors, renames, reformatting, re-dating, or "fixing" of old code, even when it breaks a convention and even in a file you add code to. Conventions apply to the lines you write.
- Match the style of the code around you, unless a convention skill says otherwise.
- Delete what your change replaced or made unused. Leave nothing unused behind.

## Clean code
- No code comments. Names, types, and docstrings explain the code.
- Never silence a linter or type checker (`noqa`, `type: ignore`, `eslint-disable`, `@ts-ignore`, ...). Fix the code instead.
- Never use another class's or module's private members (names starting with `_`). Use the public API, or make the needed function public where it's defined.

## Work toward a checkable goal
- Turn the task into checks that prove it's done (tests, a command, a visible result), run them, and report the real outcome. If a check fails or was skipped, say so.

## Tests use their own services
- Never run tests against databases or services that are already running: they belong to the user or to other branches. Start your own throwaway containers first (`docker compose -p <branch>` on free ports, copying the setup of the project's `docker-compose.yml` and running containers), point the test settings at them, and remove them when you're done.

## Git
- Branch names: `BTRC-<JIRA-ISSUE>-<what-we-do>`, e.g. `BTRC-1234-add-authentication`. The same name inside a worktree: never `worktree-add-authentication` or `worktree-BTRC-1234-add-authentication`. If you don't know the Jira issue, ask.
- Before pushing (CI changes or anything else), ask once whether you may push on your own (in `/feature`, the grill asks). If yes, push, then follow the pipeline through the GitLab MCP server if one is connected: when a job fails, read its log, fix it, and push again until the pipeline passes.

## Conventions
- Coding and testing conventions are the skills in `~/.claude/skills/` (`python-conventions`, `sql-conventions`, `pytest-conventions`, `vue-conventions`, ...). `midnight_models` is the shared models library.
- Check what you wrote with `python ~/.claude/scripts/lint_changed.py --since auto <files>`, and Python types with `python ~/.claude/scripts/mypy_strict.py --since auto <package>`. Both report only the lines your branch wrote.
