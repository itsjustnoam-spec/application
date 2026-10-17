# Pytest Conventions Checklist

Run this per changed test file. Every item must be answered ✅, ❌ (with `file:line`), or N/A.

## Location & naming
- [ ] TS-01 File path is `tests/<module_name>/test_<what_we_test>.py`
- [ ] TS-02 Test names follow `test_<unit>_<condition>_<expected>`
- [ ] TS-03 Module helpers and factories live in that module's `utils.py` (or `utils/`), and fixtures live in its `conftest.py` or at the top of the file

## File structure
- [ ] TS-04 Order is imports, then local fixtures, then test functions
- [ ] TS-05 No test classes (unless strictly necessary)
- [ ] TS-06 No comments (no `# Arrange` / `# Act` / `# Assert` labels either), unless documenting an upstream workaround

## Test body
- [ ] TS-07 Arrange / Act / Assert are visibly separated by single blank lines
- [ ] TS-08 Exactly one action under test per test
- [ ] TS-09 One assertion concept per test (multiple asserts only on the same result)
- [ ] TS-10 No `for` loops in tests. Uses `@pytest.mark.parametrize`.
- [ ] TS-11 Every test asserts something meaningful (no missing asserts, no `assert True`, not only "the mock was called" when a real result exists)
- [ ] TS-12 Tests check behavior, not private implementation details

## Fixtures
- [ ] TS-13 No `setUp`/`tearDown` or unittest classes
- [ ] TS-14 Fixture scope is `function` unless the setup is expensive and read-only
- [ ] TS-15 Setup that needs cleanup uses a `yield` fixture
- [ ] TS-16 Multiple variants use fixture factories, not copy-pasted fixtures

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
- [ ] TS-25 Tests run with `uv run pytest`
- [ ] TS-26 Tests run against a separate test database (never the application's), unless the user explicitly said otherwise
