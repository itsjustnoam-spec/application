# FieldOps

Industrial equipment maintenance platform in one monorepo. This project is a test bed for the Claude workflow in `.claude/`.

## Architecture
- `web/helios/`: Vue 3 + Vuetify + TypeScript (Vite) web app. Vite proxies `/api` to Juniper on port 8000.
- `web/juniper/`: FastAPI reverse proxy, the single entry point (`/api/<service>/...`).
- `services/atlas/`: FastAPI + PostgreSQL + SQLModel service (sites, asset types, assets), with Alembic migrations.
- `services/orion/`: FastAPI + MongoDB service.
- `docker-compose.yml`: PostgreSQL, MongoDB, RabbitMQ, Temporal (+ UI), and the services.

## Where things live
- Python projects: code in `src/<package>/`, tests in `tests/<domain>/test_<operation>_<domain>.py`, shared fixtures (including `env`) in `tests/conftest.py`.
- Atlas: entities in `src/atlas/entities/`, managers in `src/atlas/managers/`, routers in `src/atlas/routers/`, schemas in `src/atlas/schemas/`, settings in `src/atlas/settings.py` (read from `services/atlas/.env`).
- Helios: views in `src/views/`, components in `src/components/`, API clients in `src/api/`, types in `src/models/`, shared logic in `src/utils/`. Tests in `tests/unit/`, `tests/integration/`, `tests/e2e/`, with factories and MSW handlers in `tests/mocks/`.

## Commands
- Infrastructure: `docker compose up -d postgres mongo rabbitmq temporal` from the repo root.
- Python project (run inside its directory): `uv sync`, `uv run ruff check .`, `uv run pytest` (writes `coverage.xml`), `python ../../.claude/scripts/mypy_strict.py src tests`.
- Changed-line coverage (Python): `uv run diff-cover coverage.xml --compare-branch=main --fail-under=100`.
- Atlas migrations: `PYTHONPATH=src uv run alembic upgrade head` from `services/atlas`.
- Helios (inside `web/helios`): `npm install`, `npm run typecheck`, `npm test` (Vitest), `npx playwright test` (browser tests, backend mocked), `npm run dev`.

## Gotchas
- Atlas reads `DATABASE_URL` and `TEST_DATABASE_URL` from `services/atlas/.env`. Copy it from `.env.example`. The test database (`fieldops_test`) must exist in the Postgres container; the tests create its tables.
- Alembic needs `PYTHONPATH=src`, because `alembic.ini` doesn't add `src` to the path.
- Helios has no ESLint config yet, so the post-edit hook doesn't lint frontend files here.
- Frontend tests have no coverage target (see `.claude/skills/vitest-conventions`), even though the root `README.md` shows a frontend diff-cover command.
