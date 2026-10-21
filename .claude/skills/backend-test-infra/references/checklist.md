# Backend Test Infrastructure Checklist

Run this per changed backend test file, together with the pytest checklist. Every item must be answered ✅, ❌ (with `file:line`), or N/A.

## Layers
- [ ] BT-01 Every new endpoint has integration and API tests; edge-case depth is in the integration layer, and the API layer covers success, every validation/error status, and the response shape
- [ ] BT-02 Unit tests (no I/O) exist only for pure helpers with real logic

## Databases
- [ ] BT-03 Tests use a separate test database whose URL comes from `.env`, and the root `conftest.py` fails fast when it could be the application's database (the name must end in `_test`)
- [ ] BT-04 PostgreSQL tests run on real PostgreSQL (not SQLite), with one connection and transaction per test rolled back at teardown, the session joined with `join_transaction_mode="create_savepoint"`, and a `session`-scoped engine
- [ ] BT-05 MongoDB tests use a real Mongo when the code relies on indexes, aggregation, or transactions; a separate test database with a unique name per test or collections dropped at teardown; indexes created with the app's own setup function

## API layer
- [ ] BT-06 API tests use the project's client fixture, override the session dependency with the test session (cleared at teardown), and assert the status code **and** the body, with the exact `detail` for errors

## Services
- [ ] BT-07 Reverse proxy: pass-through routes have no tests; routes with logic mock the downstream service at the HTTP boundary and assert the forwarded request and the proxied response
- [ ] BT-08 RabbitMQ: publishers are patched where they're looked up and the exact payload and routing key are asserted; consumers' handlers are called directly and their effects and ack/requeue behavior are asserted; idempotency is tested; no real broker
- [ ] BT-09 Temporal: workflows run in the time-skipping test environment with mocked activities; activities are tested as functions (or with `ActivityEnvironment`); the retries and timeouts the spec defines are covered

## Coverage
- [ ] BT-10 Every uncovered changed line is either tested or listed as exempt in `test-plan.md` with a reason
