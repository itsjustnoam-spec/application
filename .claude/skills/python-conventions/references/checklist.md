# Python Conventions Checklist

Run this per changed `.py` file (tests use the pytest checklist as well). Migration files (Alembic `versions/` / `migrations/`) are exempt from PY-07 to PY-16, PY-35, and PY-02. Test files are exempt from PY-07 to PY-12, PY-17 to PY-21, PY-24, PY-35, PY-41, and PY-42.

Run `python .claude/scripts/check_python_conventions.py <files>` first: it checks every item marked (auto). Copy its result for those items, then judge the rest. Every item must be answered ✅, ❌ (with `file:line`), or N/A.

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
- [ ] PY-17 Docstrings of business-logic functions have `:param` / `:return` / `:raises` as needed; small helpers may have only the description
- [ ] PY-35 (auto for presence) Every function and method has a docstring (except `__init__` and tests). Judge by hand that endpoint docstrings have only a description, with no `:param`/`:return`/`:raises`.
- [ ] PY-18 Description is one concise sentence ending in `.` and doesn't mention raising errors
- [ ] PY-41 (auto) Function, method, and endpoint descriptions are in the imperative mood (`Lock the resource.`, not `Locks the resource.`)
- [ ] PY-42 (auto) Boolean returns say what the value means (`:return: Whether the asset is overdue.`), never `True when ..., False when ...`
- [ ] PY-20 Proxy pass-through functions have a single-line docstring only
- [ ] PY-21 No docstring or comment mentions past implementations

## Classes & SQLModel
- [ ] PY-30 Table models: `__tablename__` is on the line right after the class docstring
- [ ] PY-31 Table models: `__table_args__` (constraints, indexes) is at the end of the class, after the fields
- [ ] PY-43 (auto) String enums inherit from `StrEnum`, never `str, Enum`

## Configuration & strings
- [ ] PY-33 URLs, hosts, ports, DB names, credentials, and keys come from `.env` via settings (never hardcoded)
- [ ] PY-34 Large strings (long messages, SQL, templates) are named constants; short strings stay inline

## FastAPI & database
- [ ] PY-37 (auto) Dependencies are functions passed with `Depends(...)` in each endpoint's signature, never stored in a constant or type alias
- [ ] PY-40 (auto) No `session.rollback()`: transactions are explicit and rolled back through the transaction object (see the `sql-conventions` checklist)

## Naming
- [ ] PY-22 Function and variable names say exactly what they handle (no `load`, `process`, `data`, `item`)
- [ ] PY-36 (auto) No single-letter or abbreviated names (`q`, `db`, `e`, `err`, `idx`, ...) for variables, parameters, loop variables, or `except ... as`. Short external names use `alias=`.

## Conditions
- [ ] PY-23 No truthy/falsy checks on non-bool values. Uses `is None` / `is not None` / `len(x) == 0`.
- [ ] PY-38 (auto) Comprehensions and generator expressions: expression, each `for`, and each `if` on their own lines; brackets on their own lines
- [ ] PY-32 Exactly one blank line after every `if` block (with its `elif`/`else`) that is followed by more code in the same block
- [ ] PY-45 `if` conditions that do real work (a query, chained calls, several combined checks) are moved into a well-named variable first

## Calls
- [ ] PY-24 Calls with 3+ arguments, or whose single-line form would make the line 70+ characters (indentation included), have one argument per line and a trailing comma
- [ ] PY-44 (auto) List and set literals with two or more items have one item per line, brackets on their own lines, and a trailing comma (a literal of at most 30 characters may stay on one line)

## Exceptions
- [ ] PY-25 No raising of builtin exceptions (`Exception`, `ValueError`, `KeyError`, `RuntimeError`, …)
- [ ] PY-26 Custom exception class names end with `Error`
- [ ] PY-39 (auto) A class whose body is only a docstring ends with `pass`
- [ ] PY-27 Each custom exception represents a clear domain failure

## Tooling
- [ ] PY-28 Dependencies added with `uv add`, and commands run through `uv run`
