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
- Never change an existing line the task doesn't need: no refactors, renames, reformatting, re-dating, or "fixing" of old code, even when it breaks a convention and even in a file you add code to. Conventions apply to the lines you write. Two exceptions:
  - In a `.vue` file you add code to, fix the structure rules in the whole file: `Props` / `Emits` interfaces in `<script lang="ts">`, constants out of `<script setup>`, no exports.
  - Changing existing code so it can be reused instead of duplicated (one more parameter, a generic type) is allowed.
- Match the style of the code around you, unless a convention skill says otherwise.
- Delete what your change replaced or made unused. Leave nothing unused behind.

## Clean code
- No code comments. Names, types, and docstrings explain the code. Python's section banners (`# ----- Imports ----- #`) aren't comments: keep them where `python-conventions` requires them.
- Never silence a linter or type checker (`noqa`, `type: ignore`, `eslint-disable`, `@ts-ignore`, ...). Fix the code instead.
- Never use another class's or module's private members (names starting with `_`). Use the public API, or make the needed function public where it's defined.

## Find code with graphify
- Projects keep a code knowledge graph in `graphify-out/` (committed; a session-start hook updates it in the background, code only, no LLM). When `graphify-out/graph.json` exists, run `graphify query "<question>"` before your first grep, search, or source-file read for a codebase question.
- Use `graphify path "<A>" "<B>"` for how two things connect, `graphify explain "<name>"` for one function or class, `graphify affected "<name>"` for what a change impacts, and `graphify-out/GRAPH_REPORT.md` only for the overall architecture.
- Read files only for the lines the graph pointed to. Grep only when the graph has no answer. Put this rule in every subagent prompt that explores code.
- After changing code, run `graphify update .` (code only, a few seconds) so the graph stays current. Changes to `graphify-out/` in a diff are expected: never report them as a problem.

## Work toward a checkable goal
- Turn the task into checks that prove it's done (tests, a command, a visible result), run them, and report the real outcome. If a check fails or was skipped, say so.

## Tests use their own services
- Tests use only the Docker compose project named after your branch, in lowercase (`docker compose -p btrc-1234-add-authentication`). Never use other containers: they belong to the user or to other branches. If your project isn't running, create it from the project's own `docker-compose.yml` (the current directory's, or the main checkout's root) with an override that frees the fixed ports (`git-worktree` skill §3), point the test settings at it, and remove it when you're done.

## Git
- Branch names: `BTRC-<JIRA-ISSUE>-<what-we-do>`, e.g. `BTRC-1234-add-authentication`. The same name inside a worktree: never `worktree-add-authentication` or `worktree-BTRC-1234-add-authentication`. If you don't know the Jira issue, ask.
- Before pushing (CI changes or anything else), ask once whether you may push on your own (in `/feature`, the grill asks). If yes, push, then follow the pipeline through the GitLab MCP server if one is connected: when a job fails, read its log, fix it, and push again until the pipeline passes.

## Conventions
- Coding and testing conventions are the skills in `~/.claude/skills/` (`python-conventions`, `sql-conventions`, `pytest-conventions`, `vue-conventions`, ...). `midnight_models` is the shared models library.
- Check what you wrote with `python ~/.claude/scripts/lint_changed.py --since auto <files>`, and Python types with `python ~/.claude/scripts/mypy_strict.py --since auto <package>`. Both report only the lines your branch wrote.
