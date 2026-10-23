---
name: pytest-conventions
description: Use when writing, maintaining, reviewing, or debugging Python tests with pytest. Enforces the tests/<domain>/test_<operation> layout, test data only through the env fixture in conftest and the app's own managers, what not to test (migrations, plain validation), AAA structure, fixture patterns, parametrization, DAMP test naming, 100% coverage, and strict isolation.
---

# Pytest Testing Conventions

Opinionated, comprehensive testing patterns for Python and pytest. Incorporates proven patterns from `pytest-patterns`, `pytest-best-practices`, and `python-testing-patterns`. Follow these instructions whenever writing, refactoring, or reviewing Python tests.

---

## 1. Core Principles

1. **Test behavior, not implementation**: Focus on what the code does and its observable contract, not internal private implementation details.
2. **One assertion concept per test**: A test verifies a single outcome or behavior. Multiple `assert` statements are permitted only when validating properties of the same single result.
3. **DAMP over DRY in tests**: Descriptive And Meaningful Phrases over rigid Don't Repeat Yourself. Tests should be readable from top to bottom without jumping through complex helper abstractions.
4. **Narrow fixture scopes**: Default to `function` scope. Widen to `module` or `session` only for expensive, read-only setup (e.g. database engines, mock servers).
5. **Isolation and order-independence**: Zero shared mutable state across tests. Tests must pass regardless of execution order and run cleanly in parallel (e.g. with `pytest-xdist`).

---

## 2. Test File & Directory Organization

### Directory Structure & Layout

Tests are grouped by **domain** (a thing in the application, such as `sites` or `entities`), not by code layer. One domain directory holds the tests of its managers **and** its API. Inside it, each file covers **one operation**, and contains both the manager-level (integration) tests and the API tests for that operation:

```
tests/
  conftest.py                   # Root fixtures: engine, session, clients, and the env fixture
  utils.py                      # The Environment dataclass that env returns, shared helpers
  <domain>/                     # e.g. sites, asset_types, entities
    conftest.py                 # This domain's fixtures (clients, frozen clocks, ...); they never create objects
    utils.py                    # This domain's non-fixture helpers (builders of request bodies, assertions)
    test_create_<domain>.py     # e.g. test_create_site.py: manager + API tests for creating
    test_update_<domain>.py
    test_list_<domain>.py
    test_delete_<domain>.py
```

- **No layer directories**: no `tests/routers/`, `tests/managers/`, or `tests/schemas/`. A router test and a manager test of the same operation live in the same file.
- **Path format**: `tests/<domain>/test_<operation>_<domain>.py`.
- **Tests go in the main file of their operation.** A new test joins the existing file for that operation; a new file is only for a new operation. Don't create a file (or a helpers module) for each small case.
- **Test function naming**: `test_<unit>_<condition>_<expected>`:
  - `test_create_user_duplicate_email_raises_duplicate_user_error`
  - `test_calculate_discount_zero_percent_returns_original_price`
  - `test_verify_token_expired_signature_returns_false`

### Internal Test File Structure

Every test file must follow this strict sequence:
1. **Imports straight away**: Standard library, third-party, application code under test. Test files have **no page docstring and no section banners**: the file-layout rules of `python-conventions` don't apply to tests.
2. **Local Fixtures**: Module-specific fixtures immediately following imports.
3. **Test Functions**: Standalone functions (`def test_*`).
   - **No classes in test files** unless strictly necessary.
   - **No code comments in test files.** Tests must be self-explanatory.

---

## 3. The AAA Structure in Action

Every test body separates Arrange, Act, and Assert with single blank lines, and has exactly one action under test:

```python
def test_calculate_discount_valid_percentage_reduces_total():
    base_price = 100.0

    discounted_price = calculate_discount(base_price, 20.0)

    assert discounted_price == 80.0
```

---

## 4. Fixture Patterns & Scoping

### Conftest Hierarchy

Fixtures cascade downwards from root `tests/conftest.py` into domain `conftest.py` files. Keep shared database connections and global clients in root `conftest.py`; the database fixtures are described in `backend-test-infra`. Never use `unittest`-style `setUp`/`tearDown`. Setup that needs cleanup is a `yield` fixture.

### No Factory Fixtures

Don't write fixtures or helpers that create objects (`make_site(...)`, `make_asset(...)`, `create_test_user(...)`). Every object a test needs comes from the `env` fixture, or is created by the test itself through the application's managers (see §8).

---

## 5. Parametrization & Data-Driven Tests

Never use loops inside test methods: they hide which iteration failed. Use `@pytest.mark.parametrize`:

```python
@pytest.mark.parametrize("input_email,is_valid", [
    ("user@domain.com", True),
    ("missing-at.com", False),
])
def test_email_validator_various_inputs(input_email: str, is_valid: bool):
    validation_result: bool = validate_email_address(input_email)

    assert validation_result is is_valid
```

---

## 6. Testing Exceptions & Error Paths

Always test error branches and custom exception handling. Use `pytest.raises` with exact exception types and message matching:

```python
def test_withdraw_insufficient_funds_raises_overdraft_error():
    account: BankAccount = BankAccount(balance=50.0)

    with pytest.raises(InsufficientFundsError, match="Requested 100.0 but balance is 50.0"):
        account.withdraw(100.0)
```

Never assert generic `Exception` or `ValueError` when domain exceptions are defined.

---

## 7. Mocking Best Practices

- **Patch where the name is used/imported**:
  If `services/user.py` imports `send_email` from `utils/email.py`, patch `services.user.send_email`, NOT `utils.email.send_email`.
- **Deterministic Time**: Use `monkeypatch` or `freezegun` to freeze clock values in time-dependent tests.
- **Never mock the subject under test**: Only mock external network calls, system timers, and third-party APIs.
- **Mocks and expected values are hand-made**: Build mock data and expected values **by hand** in the test (or in `env`). Never produce them with the application's own functions, such as a converter that turns a row into its API model: if that function has a bug, the test copies the bug and never finds it. Importing the app's types and enums is fine.

---

## 8. Test Data: the `env` Fixture

All the data a test relies on, but doesn't test, comes from **one fixture, `env`**, in `tests/conftest.py`. It builds a small, named world (sites, asset types, assets, ...) for every test, inside the test's rolled-back transaction, and returns it as an `Environment` dataclass (declared in `tests/utils.py`), so tests read `env.north_site` or `env.retired_compressor`.

- **`env` is the only place that creates objects in the database for tests.** It may add them through the session or the application's managers.
- **The object under test is created through the application's own functions.** A test about creating or changing something calls the manager (`create_asset(...)`, `archive_site(...)`) or the API. That's the only creation allowed outside `env`.
- **Never call a manager to create something just to test something else with it.** When creating isn't what the test is about, the object comes from `env`.
- **No factory fixtures and no creating helpers** (`make_site`, `make_asset`, ...), in any `conftest.py` or `utils.py`, root or domain. A domain's `conftest.py` and `utils.py` hold fixtures and helpers for that domain's tests, but objects still come only from `env`.
- **A test never uses the session directly**: no `session.add`, `session.get`, `session.exec`, `session.commit`, or any other session call in a test body. A test only passes the session to the application's functions. To check the result, it uses the application's read functions or the API.
- **When a test needs something `env` doesn't have**, add it to `env` under a name that says what's special about it (`archived_site`, `retired_compressor`, `asset_due_yesterday`). Don't build it in the test.
- Tests never depend on what another test created. `env` is function-scoped, so every test starts from the same world.

```python
# tests/utils.py
@dataclass
class Environment:
    north_site: Site
    archived_site: Site
    pump: AssetType
    compressor: Asset


# tests/conftest.py
@pytest.fixture
def env(db_session: Session) -> Environment:
    north_site = Site(name="North Depot", address="1 Main Street", timezone="Europe/Berlin")
    archived_site = Site(name="Old Depot", address="2 Main Street", timezone="UTC", archived=True)
    pump = AssetType(name="Pump", category=AssetCategory.MECHANICAL, inspection_interval_days=30)
    compressor = Asset(name="Compressor", serial_number="SN-1", site=north_site, asset_type=pump)
    db_session.add_all(
        [
            north_site,
            archived_site,
            pump,
            compressor,
        ],
    )
    db_session.flush()
    return Environment(
        north_site=north_site,
        archived_site=archived_site,
        pump=pump,
        compressor=compressor,
    )


# GOOD:
def test_archive_asset_active_asset_hides_it_from_list(db_session: Session, env: Environment):
    archive_asset(db_session, env.compressor.id)

    assert list_assets(db_session).total == 0


def test_create_asset_valid_input_returns_asset(db_session: Session, env: Environment):
    asset_input = build_asset_input(site_id=env.north_site.id, asset_type_id=env.pump.id)

    asset = create_asset(db_session, asset_input)

    assert asset.site_id == env.north_site.id


# BAD:
def test_archive_asset_active_asset_hides_it_from_list(db_session: Session, make_asset):
    asset = make_asset(name="Compressor")  # factory fixture instead of env
    ...


def test_list_assets_archived_site_is_hidden(db_session: Session):
    site = Site(name="North plant", timezone="UTC")
    db_session.add(site)  # object created and saved directly in the test
    db_session.commit()
    ...
```

---

## 9. What Not to Test

- **Migrations.** Verify them by running them (see `sql-conventions`), not with tests.
- **Plain object or schema validation**: tests that only construct a model or schema and check which input it accepts or rejects. Validation is tested through behavior instead, e.g. an API test that sends an invalid body and gets 422 with the right detail.
- Framework or library behavior (that FastAPI routes, that SQLAlchemy saves), and trivial getters or constants.
- **The `midnight_models` library.** It has no tests; its models are tested through the applications that use them.

---

## 10. Test Layers & Infrastructure

Backend features are tested on two layers:

- **Integration tests**: call the service manager/reader directly (e.g. the entities reader) against a real test database. They cover business logic, ORM behavior, and edge cases without HTTP.
- **API tests**: call the endpoint through the FastAPI test client. They cover routing, validation, status codes, and response shapes.

Every new endpoint gets both layers. Both layers run against a **separate test database**, never the application's database, unless the user explicitly says otherwise. Its connection settings come from `.env`. Database, Mongo, Temporal, and RabbitMQ test setups are described in the **`backend-test-infra`** skill. Reviewers use `references/checklist.md`.

---

## 11. Running Tests

Run tests with `uv run pytest` (a path or `-k <name>` narrows the run).
