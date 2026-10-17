# Python Conventions Checklist

Run this per changed `.py` file (tests use the pytest checklist as well). Migration files (Alembic `versions/` / `migrations/`) are exempt from PY-07 to PY-16 and PY-02. Every item must be answered ✅, ❌ (with `file:line`), or N/A.

## Typing
- [ ] PY-01 Every function parameter has a type annotation (except `self`/`cls`)
- [ ] PY-02 No function is annotated `-> None`
- [ ] PY-03 No `return None`, except in functions annotated `-> X | None`
- [ ] PY-04 No trailing bare `return` as the last statement of a function
- [ ] PY-05 Every function that returns a value has a return annotation
- [ ] PY-06 Local annotations only where the type isn't obvious (empty collections, unions, untyped external values). No `count: int = 0` style annotations.

## File layout
- [ ] PY-07 File starts with the page docstring, containing a description, `:author:` and `:date: DD/MM/YY`
- [ ] PY-08 Section banners match `# ----- Name ----- #` and the name is capitalized
- [ ] PY-09 `Imports` banner is on the line right after the closing `"""`, with 1 blank line below
- [ ] PY-10 `Consts` banner has 1 blank line above and 1 below
- [ ] PY-11 `Classes` / `Functions` / domain banners have 1 blank line above and 2 below
- [ ] PY-12 No empty banner sections
- [ ] PY-13 No `__all__` in application packages

## Docstrings
- [ ] PY-14 Opening and closing `"""` are on their own lines in every docstring
- [ ] PY-15 No blank lines between `:param` / `:return` / `:raises` lines
- [ ] PY-16 `__init__` methods have no docstring
- [ ] PY-29 No blank line between a class docstring and the class body
- [ ] PY-17 Docstrings exist only where the contract is non-obvious (no redundant docstrings)
- [ ] PY-18 Description is one concise sentence ending in `.` and doesn't mention raising errors
- [ ] PY-19 API endpoint docstrings have only a description (no `:param`/`:return`/`:raises`)
- [ ] PY-20 Proxy pass-through functions have a single-line docstring only
- [ ] PY-21 No docstring or comment mentions past implementations

## Classes & SQLModel
- [ ] PY-30 Table models: `__tablename__` is on the line right after the class docstring
- [ ] PY-31 Table models: `__table_args__` (constraints, indexes) is at the end of the class, after the fields

## Configuration & strings
- [ ] PY-33 URLs, hosts, ports, DB names, credentials, and keys come from `.env` via settings (never hardcoded), and new keys are added to `.env.example`
- [ ] PY-34 Large strings (long messages, SQL, templates) are named constants; short strings stay inline

## Naming
- [ ] PY-22 Function and variable names say exactly what they handle (no `load`, `process`, `data`, `item`)

## Conditions
- [ ] PY-23 No truthy/falsy checks on non-bool values. Uses `is None` / `is not None` / `len(x) == 0`.
- [ ] PY-32 Exactly one blank line after every `if` block (with its `elif`/`else`) that is followed by more code in the same block

## Calls
- [ ] PY-24 Calls with 3+ arguments, or whose single-line form would make the line 70+ characters (indentation included), have one argument per line and a trailing comma

## Exceptions
- [ ] PY-25 No raising of builtin exceptions (`Exception`, `ValueError`, `KeyError`, `RuntimeError`, …)
- [ ] PY-26 Custom exception class names end with `Error`
- [ ] PY-27 Each custom exception represents a clear domain failure

## Tooling
- [ ] PY-28 Dependencies added with `uv add`, and commands run through `uv run`
