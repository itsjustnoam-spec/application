---
name: backend-test-infra
description: Use when writing or reviewing backend tests that touch PostgreSQL, MongoDB, the FastAPI test client, the reverse proxy, RabbitMQ, or Temporal. Defines the integration and API test layers and how to set up each dependency. Complements pytest-conventions.
---

# Backend Test Infrastructure

`pytest-conventions` defines how a test is written. This skill defines **what each layer tests and how its dependencies are set up**. Always follow the project's existing fixtures first: find them in the existing tests (see `patterns.md` and the root `CLAUDE.md`), and only add new fixtures when none exist.

---

## 1. The Two Layers

| | Integration | API |
|---|---|---|
| Calls | The service manager/reader directly (e.g. the entities reader) | The endpoint, through the FastAPI test client |
| Database | Real test database | Real test database |
| Proves | Business logic, queries, ORM behavior, domain exceptions, edge cases | Routing, validation (422), status codes, error-to-status mapping, response shape |
| File | `tests/<domain>/test_<operation>_<domain>.py` | **The same file** as the integration tests of that operation |

- Every new endpoint gets **both** layers.
- Put edge-case depth in the integration layer. The API layer covers success, every validation/error status, and the response shape.
- Unit tests (no I/O) are for pure helpers with real logic only. No tests for migrations or for plain schema/model validation (see `pytest-conventions` §9).

---

## 2. A Separate Test Database (all services)

- Tests **always** run against their own database (Postgres database / Mongo database), never the one the application uses, unless the user explicitly says otherwise. That way test writes and cleanups can't touch application data, and the app can keep running while tests run.
- The test database's name and URL come from `.env` (e.g. `TEST_DATABASE_URL`, `TEST_MONGO_DB`) like every other connection setting. They're never hardcoded.
- Guard in the root `conftest.py`: fail fast if the configured test database name doesn't differ from the application's (e.g. it must end in `_test`).

## 2a. PostgreSQL (CRUD service)

- Test against **real PostgreSQL**, not SQLite. JSON columns, constraints, `ON CONFLICT`, and case sensitivity behave differently. Use the project's test database (docker-compose service or testcontainers) as found in the reference tests.
- Isolation: one transaction per test, rolled back at teardown (the `db_session` pattern in `pytest-conventions`), with the engine at `session` scope.
- Data setup: the `env` fixture (see `pytest-conventions` §8).
- Migrations aren't tested; they're verified by running them (see `sql-conventions`).

## 3. FastAPI test client (API layer)

- Use the project's existing client fixture. If there is none: `httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test")` for async apps, or `TestClient(app)` for sync ones.
- Override the DB dependency so the API test uses the same rolled-back `db_session`: `app.dependency_overrides[get_session] = lambda: db_session`. Clear the overrides at teardown.
- Assert the status code **and** the body. For errors, assert the exact `detail`.

## 4. MongoDB service

- Prefer a real Mongo (testcontainers or the compose service) when the code relies on indexes, aggregation, or transactions. `mongomock`/`mongomock-motor` is acceptable for simple CRUD, if the project already uses it.
- Isolation: a test database separate from the application's (§2), plus a unique database name per test or dropped collections at teardown.
- Create the indexes the code relies on inside the fixture, using the app's own index setup function.

## 5. Reverse proxy

- Pure pass-through routes have no tests (exempt).
- Routes with logic (header rewriting, auth, path mapping, aggregation): mock the downstream service at the HTTP boundary (`respx`, or `httpx.MockTransport`), then assert the forwarded request (method, path, headers, body) and the proxied response.

## 6. RabbitMQ

- **Publishing:** patch the publisher where it's looked up (`services.entities.publish_entity_created`), then assert the exact message payload and routing key. Never connect to a real broker in unit or integration tests.
- **Consuming:** call the consumer's handler function directly with a message body built from the schema. Assert its effects (DB state, published follow-up messages), plus ack/requeue behavior for bad messages.
- Test idempotency: delivering the same message twice has no double effect.

## 7. Temporal

- Workflows: `WorkflowEnvironment.start_time_skipping()` from `temporalio.testing`, with a `Worker` registering the workflow and **mocked activities** (functions with the same `@activity.defn(name=...)`). Assert the workflow result and the activities called.
- Activities: test them as normal async functions (integration layer, real DB), or with `ActivityEnvironment` when they use activity context (heartbeats, info).
- Cover retries and timeouts that the spec defines (a mocked activity that fails N times, then succeeds).

---

## 8. Coverage

- Run: `uv run pytest --cov=<package> --cov-report=xml`
- Changed lines only: `uv run diff-cover coverage.xml --compare-branch=<base> --fail-under=100`
- Uncovered changed lines are either tested or listed as exempt in `test-plan.md` with a reason.
