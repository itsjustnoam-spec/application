# FieldOps

Industrial equipment maintenance platform, organized as a monorepo.

| Path | What it is |
|---|---|
| `web/helios/` | Vue 3 + Vuetify + TypeScript (Vite) web app |
| `web/juniper/` | FastAPI reverse proxy, the single entry point (`/api/<service>/...`) |
| `services/atlas/` | FastAPI + PostgreSQL + SQLModel service, with Alembic migrations |
| `services/orion/` | FastAPI + MongoDB service |
| `docker-compose.yml` | PostgreSQL, MongoDB, RabbitMQ, Temporal (+ UI), and the services |

Each Python project keeps its code in `src/<package>/` and its tests in `tests/`.

## Prerequisites

- Docker (with Compose)
- [uv](https://docs.astral.sh/uv/) for the Python projects (uv installs Python 3.12 for you)
- Node.js 24+ and npm for the web app

## Run everything

Full stack in containers:

```bash
docker compose up --build
```

| Endpoint | URL |
|---|---|
| Juniper proxy (entry point) | http://localhost:8000/health |
| Temporal UI | http://localhost:8233 |
| RabbitMQ management | http://localhost:15672 (guest / guest) |
| PostgreSQL | localhost:5432 (fieldops / fieldops) |
| MongoDB | localhost:27017 |

Web app, on the host (Vite proxies `/api` to Juniper on port 8000):

```bash
cd web/helios
npm install
npm run dev
```

Open http://localhost:5173.

Atlas migrations, run against the PostgreSQL container:

```bash
cd services/atlas
uv sync
DATABASE_URL=postgresql+psycopg://fieldops:fieldops@localhost:5432/fieldops uv run alembic upgrade head
```

Each Python project can also run on its own. Install dependencies with `uv sync`, then start it with `uv run uvicorn <package>.main:app --port <port>` from its directory. Juniper reads `ATLAS_SERVICE_URL` and `ORION_SERVICE_URL`, which default to `http://localhost:8001` and `http://localhost:8002`.

## Run the tests

### Python projects (`web/juniper`, `services/atlas`, `services/orion`)

Run these from inside each project directory:

```bash
uv sync
uv run ruff check .
uv run mypy
uv run pytest
```

- `uv run pytest` runs the tests and writes `coverage.xml` (pytest-cov).
- Changed-line coverage, against `main`:

  ```bash
  uv run diff-cover coverage.xml --compare-branch=main --fail-under=100
  ```

### Web app (`web/helios`)

```bash
cd web/helios
npm install
npm run typecheck        # vue-tsc
npm run test             # Vitest: unit, component and integration layers
npm run test:coverage    # Vitest with v8 coverage, written to coverage/
npx playwright install chromium   # first run only
npm run test:e2e         # Playwright browser tests, backend fully mocked
```

- Changed-line coverage, against `main`:

  ```bash
  uvx diff-cover coverage/cobertura-coverage.xml --compare-branch=main --fail-under=100
  ```

The test layers are described in `.claude/skills/vitest-conventions` and `.claude/skills/browser-test-conventions`, and the Python layers in `.claude/skills/pytest-conventions`.
