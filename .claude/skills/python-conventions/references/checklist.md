# Python Conventions Checklist

Run this per changed `.py` file (tests use the pytest checklist as well). Migration files (Alembic `versions/` / `migrations/`) are exempt from every item. Test files are exempt from PY-01, PY-07 to PY-12, PY-17 to PY-21, PY-24, PY-33, PY-34, PY-35, PY-41, PY-42, and PY-55.

Run `python ~/.claude/scripts/check_python_conventions.py --since auto <files>` first: it checks every item marked (auto) on the lines the branch wrote. Copy its result for those items, then judge the rest. Judge only lines the branch added or changed. Every item must be answered ✅, ❌ (with `file:line`), or N/A.

## Typing
- [ ] PY-01 (auto) Every function parameter has a type annotation (except `self`/`cls`)
- [ ] PY-02 (auto) No function is annotated `-> None`
- [ ] PY-03 (auto) No `return None`, except in functions annotated `-> X | None`
- [ ] PY-04 (auto) No trailing bare `return` as the last statement of a function
- [ ] PY-05 Every function that returns a value has a return annotation
- [ ] PY-06 Local annotations only where the type isn't obvious (empty collections, unions, untyped external values). No `count: int = 0` style annotations.

## File layout
- [ ] PY-07 (auto) File starts with the page docstring, containing a description, `:author:` and `:date: DD/MM/YY`
- [ ] PY-08 (auto) Section banners match `# ----- Name ----- #` and the name is capitalized
- [ ] PY-09 (auto) `Imports` banner is on the line right after the closing `"""`, with 1 blank line below
- [ ] PY-10 `Consts` banner has 1 blank line above and 1 below
- [ ] PY-11 (auto) `Classes` / `Functions` / domain banners have 1 blank line above and 2 below
- [ ] PY-12 No empty banner sections
- [ ] PY-13 (auto) No `__all__` in application packages

## Docstrings
- [ ] PY-14 (auto) Opening and closing `"""` are on their own lines in every docstring
- [ ] PY-15 (auto) No blank lines between `:param` / `:return` / `:raises` lines
- [ ] PY-16 (auto) `__init__` methods have no docstring
- [ ] PY-29 (auto) No blank line between a class docstring and the class body
- [ ] PY-17 Docstrings of business-logic functions have `:param` / `:return` / `:raises` as needed; small helpers may have only the description
- [ ] PY-35 (auto for presence) Every function and method has a docstring (except `__init__` and tests). Judge by hand that endpoint docstrings have only a description, with no `:param`/`:return`/`:raises`.
- [ ] PY-18 Description is one concise sentence ending in `.` and doesn't mention raising errors
- [ ] PY-41 (auto) Function, method, and endpoint descriptions are in the imperative mood (`Lock the resource.`, not `Locks the resource.`)
- [ ] PY-42 (auto) Boolean returns say what the value means (`:return: Whether the asset is overdue.`), never `True when ..., False when ...`
- [ ] PY-20 Proxy pass-through functions have a single-line docstring only
- [ ] PY-21 No docstring mentions past implementations

## Classes & SQLModel
- [ ] PY-30 (auto) Table models: `__tablename__` is on the line right after the class docstring
- [ ] PY-31 (auto) Table models: `__table_args__` (constraints, indexes) is at the end of the class, after the fields
- [ ] PY-43 (auto) String enums inherit from `StrEnum`, never `str, Enum`
- [ ] PY-46 (auto) Pydantic field validation uses `Annotated[..., BeforeValidator(...)]` / `AfterValidator(...)`, not `@field_validator` methods

## Configuration & strings
- [ ] PY-33 (auto for URL and localhost literals) URLs, hosts, ports, DB names, credentials, and keys come from `.env` via settings (never hardcoded)
- [ ] PY-34 (auto) Strings of more than 3 words (messages, SQL, templates) are named constants; strings of 3 words or fewer stay inline
- [ ] PY-55 (auto) No constant holds a string of 3 words or fewer

## FastAPI & database
- [ ] PY-37 (auto) Dependencies are functions passed with `Depends(...)` in each endpoint's signature, never stored in a constant or type alias
- [ ] PY-40 (auto) No `session.rollback()`: transactions are explicit and rolled back through the transaction object (see the `sql-conventions` checklist)

## Naming
- [ ] PY-22 Function and variable names say exactly what they handle (no `load`, `process`, `data`, `item`)
- [ ] PY-36 (auto) No single-letter or abbreviated names (`q`, `db`, `e`, `err`, `idx`, ...) for variables, parameters, loop variables, or `except ... as`. Short external names use `alias=`.

## Conditions
- [ ] PY-23 No truthy/falsy checks on non-bool values. Uses `is None` / `is not None` / `len(x) == 0`.
- [ ] PY-38 (auto) Comprehensions and generator expressions: expression, each `for`, and each `if` on their own lines; brackets on their own lines
- [ ] PY-32 (auto) Exactly one blank line after every `if` block (with its `elif`/`else`) that is followed by more code in the same block
- [ ] PY-47 (auto for if/elif chains on one value) Behavior that depends on a type or key is a dict lookup (type → value, handler, or class), not a chain of `if`/`elif` per type
- [ ] PY-45 `if` conditions that do real work (a query, chained calls, several combined checks) are moved into a well-named variable first

## Calls
- [ ] PY-24 (auto) Calls with 3+ arguments, or whose single-line form would make the line 70+ characters (indentation included), have one argument per line and a trailing comma
- [ ] PY-44 (auto) List and set literals with two or more items have one item per line, brackets on their own lines, and a trailing comma (a literal of at most 30 characters may stay on one line)

## Exceptions
- [ ] PY-25 (auto) No raising of builtin exceptions (`Exception`, `ValueError`, `KeyError`, `RuntimeError`, …)
- [ ] PY-26 (auto) Custom exception class names end with `Error`
- [ ] PY-39 (auto) A class whose body is only a docstring ends with `pass`
- [ ] PY-27 Each custom exception represents a clear domain failure

## Tooling
- [ ] PY-28 Dependencies added with `uv add`, and commands run through `uv run`
- [ ] PY-50 `python ~/.claude/scripts/mypy_strict.py --since auto <package>` passes (never silenced with `-> None`)

## Comments, suppressions & private members
- [ ] PY-52 (auto) No comments: the only `#` lines are section banners
- [ ] PY-53 (auto) No lint or type-checker suppressions (`noqa`, `type: ignore`, `pylint: disable`, ...)
- [ ] PY-54 (auto) No private member (`_name`) of another class or module is used or imported

## midnight_models
- [ ] PY-48 (auto) No `raise` in `midnight_models`: errors are raised only in the applications
- [ ] PY-49 Every new model in `midnight_models` is exported from the package's `__init__.py`
