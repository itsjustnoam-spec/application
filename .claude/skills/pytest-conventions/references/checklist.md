# Pytest Conventions Checklist

Run this per changed test file. Every item must be answered ✅, ❌ (with `file:line`), or N/A.

## Location & naming
- [ ] TS-01 File path is `tests/<domain>/test_<operation>_<domain>.py`; manager and API tests of the same operation are in the same file (no `tests/routers/`, `tests/managers/`, `tests/schemas/`)
- [ ] TS-02 Test names follow `test_<unit>_<condition>_<expected>`
- [ ] TS-03 `tests/conftest.py` holds only the shared database, session, and client fixtures; a domain's `env`, its `Environment` dataclass, its model builders, and its other helpers (request-body builders, assertions) live in `tests/<domain>/conftest.py` and `tests/<domain>/utils.py`

## File structure
- [ ] TS-04 Order is imports, then local fixtures, then test functions
- [ ] TS-27 (auto) No page docstring and no section banners in test files
- [ ] TS-05 No test classes (unless strictly necessary), and no unittest `setUp`/`tearDown`
- [ ] TS-06 (auto, PY-52) No comments (no `# Arrange` / `# Act` / `# Assert` labels either)

## Test body
- [ ] TS-07 Arrange / Act / Assert are visibly separated by single blank lines
- [ ] TS-08 Exactly one action under test per test
- [ ] TS-09 One assertion concept per test (multiple asserts only on the same result)
- [ ] TS-10 No `for` loops in tests. Uses `@pytest.mark.parametrize`.
- [ ] TS-11 Every test asserts something meaningful (no missing asserts, no `assert True`, not only "the mock was called" when a real result exists)
- [ ] TS-12 Tests check behavior, not private implementation details
- [ ] TS-35 Each test reads top to bottom (DAMP), without helper abstractions that hide what it arranges or checks

## Fixtures
- [ ] TS-14 Fixture scope is `function` unless the setup is expensive and read-only
- [ ] TS-15 Setup that needs cleanup uses a `yield` fixture
- [ ] TS-28 (auto) Test bodies never call a session method (`add`, `get`, `exec`, `commit`, ...); they only pass the session to the app's functions
- [ ] TS-30 (auto for the root conftest and for session writes) Every object a test relies on comes from its domain's `env` fixture in `tests/<domain>/conftest.py`, built there or in `tests/<domain>/utils.py`; the root `tests/conftest.py` has no `env`; no other fixture or helper creates objects (no `make_*` factories)
- [ ] TS-31 Test bodies never create objects: a test takes what it needs from `env`, and any variant it needs is a named member of `env`
- [ ] TS-37 (auto) `env` and its builders use only the app's models, never its managers, services, converters, or utils
- [ ] TS-38 Each test checks one core behavior and calls the one app function under test (no "create, then update" in one test); a second app function is called only in an edge case, while the test still checks one thing
- [ ] TS-29 No tests for migrations, and no tests that only check which input a model or schema accepts
- [ ] TS-36 No tests of framework or library behavior (that FastAPI routes, that SQLAlchemy saves), trivial getters, or constants

## Isolation & mocking
- [ ] TS-17 No shared mutable state between tests, and tests pass in any order
- [ ] TS-18 Patches target where the name is looked up (`services.user.send_email`), not where it's defined
- [ ] TS-19 Only boundaries are mocked (network, clock, third-party APIs, queues). The unit under test is never mocked.
- [ ] TS-20 Time-dependent tests freeze the clock

## Errors
- [ ] TS-21 Error paths are tested with `pytest.raises(<DomainError>, match=...)`
- [ ] TS-22 No `pytest.raises(Exception)` / `ValueError` when a domain exception exists

## Layers & coverage
- [ ] TS-23 Each new endpoint has integration tests (service manager/reader) **and** API tests (test client)
- [ ] TS-24 New code has 100% line coverage (`diff-cover`), except pure proxy pass-through routes
- [ ] TS-26 Tests run against a separate test database (never the application's), unless the user explicitly said otherwise

## Placement & hand-made data
- [ ] TS-32 No test files in `midnight_models`
- [ ] TS-33 New tests are added to the existing file of their operation; no new file (or helper module) for a small case
- [ ] TS-34 Mocks and expected values are built by hand, never with the app's own functions (converters, builders); importing types and enums is fine
