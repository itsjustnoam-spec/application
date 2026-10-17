---
name: sql-conventions
description: Use when writing or reviewing Python code that talks to PostgreSQL through SQLAlchemy or SQLModel, including sessions, transactions, queries, search and pagination, constraints, models, and Alembic migrations. Enforces explicit transactions with transaction.rollback() (never session.rollback()), parameterized queries, database-level integrity, and safe migrations.
---

# SQL Conventions (PostgreSQL, SQLAlchemy / SQLModel)

How application code uses the database. The code itself also follows `python-conventions`, which covers model class layout (`__tablename__` first, `__table_args__` last) and FastAPI dependencies. Reviewers use `references/checklist.md`.

---

## 1. Sessions

- One session per request or unit of work, created by a dependency function (e.g. `get_session`) and passed in as a parameter. Never a module-level or global session.
- Managers and other data-access functions receive the session as a parameter. They don't create their own.
- A session is never shared between threads or concurrent tasks.

## 2. Transactions

- **Start a transaction explicitly** at the beginning of the unit of work, before its first query, and keep the transaction object.
- **Commit and roll back through the transaction object**: `transaction.commit()` / `transaction.rollback()`. **Never call `session.rollback()`**, and don't scatter `session.commit()` calls across the code.
- One unit of work is one transaction. Don't commit halfway and keep going.
- A session holds one transaction at a time. When an inner step must be able to fail without undoing the whole unit of work, use a savepoint (`session.begin_nested()`) and roll back that savepoint.
- Flush (`session.flush()`) when you need database errors, such as constraint violations, or generated ids before the commit.

```python
# GOOD:
def create_site(session: Session, site_input: SiteInput) -> Site:
    """
    Creates a site.

    :param session: The open database session.
    :param site_input: The values of the new site.
    :return: The created site.
    :raises DuplicateNameError: When another site already has this name.
    """
    transaction = session.begin()
    site = Site(name=site_input.name, timezone=site_input.timezone)
    session.add(site)
    try:
        session.flush()
    except IntegrityError as error:
        transaction.rollback()
        raise DuplicateNameError(SITE_NAME_TAKEN) from error

    transaction.commit()
    session.refresh(site)
    return site

# BAD:
session.add(site)
try:
    session.commit()
except IntegrityError as error:
    session.rollback()  # never roll back through the session
    raise DuplicateNameError(SITE_NAME_TAKEN) from error
```

## 3. Queries

- Use the ORM query API (`select(...)`, `session.get(...)`, `session.exec(...)`). When raw SQL is unavoidable, use `text()` with **bound parameters**. Never build SQL with f-strings, `%`, or string concatenation.
- **Search on user input**: escape the `LIKE` wildcards `%` and `_` (and the escape character) before building a pattern, and pass the pattern as a parameter.
- **Pagination**: always `order_by` a unique, stable key (e.g. `name, id`) together with `limit` and `offset`. Unordered pages return rows in an undefined order.
- Select only the rows you need: filter in SQL, not in Python.
- **Avoid N+1 queries**: load related rows with `selectinload` / `joinedload` when you'll read them in a loop.
- Soft-deleted rows (e.g. `archived = True`) are filtered out consistently by every query that shouldn't see them.

## 4. Integrity

- Enforce rules in the database: `NOT NULL`, unique constraints (including partial unique indexes, e.g. unique among non-archived rows), foreign keys, and check constraints.
- Don't rely on "check first, then insert" for uniqueness: two requests can pass the check at the same time. Let the constraint decide, and turn its `IntegrityError` into a domain error (e.g. `DuplicateNameError`).
- Give every constraint and index an explicit, descriptive name (e.g. `uq_sites_name_active`, `ck_asset_types_inspection_interval_days_range`), so errors and migrations are readable.

## 5. Models and Columns

- Add an index for every column you filter, join, or sort on frequently.
- Timestamps are timezone-aware (`DateTime(timezone=True)`), stored in UTC.
- Enums: decide explicitly whether the database stores the member name or the value, and keep the API contract independent of that choice.

## 6. Migrations (Alembic)

- Every schema change has a migration. Generate it with autogenerate when a database is available, then read and fix the generated file. Don't trust it blindly.
- **Never edit a migration that has already been applied** anywhere shared. Write a new one.
- Every migration has a working `downgrade`.
- A new `NOT NULL` column on an existing table needs a server default or a data backfill in the same migration.
- Migrations aren't unit-tested (see `pytest-conventions`). Verify them by running `alembic upgrade head` (and `downgrade -1`) against a local database.

## 7. Tests

Tests use a separate test database, and each test is isolated by a transaction that's rolled back at teardown. See `backend-test-infra`.
