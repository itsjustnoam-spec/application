# How to work

## Think before coding
- State your assumptions. When a request can be read more than one way, say so and ask instead of guessing.
- When something is unclear, stop and name what's confusing.

## Keep it simple
- Write the least code that solves the task. No features, options, or abstractions nobody asked for.
- When behavior depends on a type or key, prefer one generic mapping (a dict of type → handler) over a chain of ifs.

## Make surgical changes
- Don't change existing code the task doesn't need: no refactors, renames, reformatting, or "improvements" of code next to your change.
- Match the style of the code around you. Remove only what your own change made unused.

## Work toward a checkable goal
- Turn the task into checks that prove it's done (tests, a command, a visible result), run them, and report the real outcome. If a check fails or was skipped, say so.

## Git
- Branch names: `BTRC-<JIRA-ISSUE>-<what-we-do>`, e.g. `BTRC-1234-add-authentication`. The same name inside a worktree: never `worktree-add-authentication` or `worktree-BTRC-1234-add-authentication`. If you don't know the Jira issue, ask.
- Before pushing (CI changes or anything else), ask once whether you may push on your own. If yes, push, then follow the pipeline through the GitLab MCP server if one is connected: when a job fails, read its log, fix it, and push again until the pipeline passes.

## Conventions
- Coding and testing conventions are the skills in `~/.claude/skills/` (`python-conventions`, `pytest-conventions`, `vue-conventions`, ...). `midnight_models` is the shared models library.
