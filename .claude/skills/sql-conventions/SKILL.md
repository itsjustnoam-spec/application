---
name: sql-conventions
description: Use when writing or reviewing Python code that defines table models or changes data in PostgreSQL through SQLAlchemy or SQLModel. Enforces indexes in __table_args__, the table model layout, and explicit transactions that are rolled back with transaction.rollback(), never session.rollback().
---

# SQL Conventions (PostgreSQL, SQLAlchemy / SQLModel)

How table models declare their table, and how application code commits and rolls back database changes. The code itself also follows `python-conventions`. Reviewers use `references/checklist.md`.

---

## Models

- `__tablename__` is the first line after the class docstring. `__table_args__` is the last thing in the class, after the fields.
- **Indexes go in `__table_args__`**, as `Index(...)`. Never declare them on the field: no `Field(index=True)` and no `Column(..., index=True)`.

```python
# GOOD:
class Asset(SQLModel, table=True):
    """
    An asset installed at a site.
    """
    __tablename__ = "assets"

    id: int | None = Field(default=None, primary_key=True)
    site_id: int = Field(foreign_key="sites.id")
    name: str

    __table_args__ = (
        Index("ix_assets_site_id", "site_id"),
    )

# BAD:
class Asset(SQLModel, table=True):
    """
    An asset installed at a site.
    """
    __table_args__ = ()
    site_id: int = Field(foreign_key="sites.id", index=True)
    __tablename__ = "assets"
```

---

## Transactions

- **Start a transaction, and roll back through it**: `transaction.rollback()`. **Never call `session.rollback()`.**
- **The unit of work owns the transaction.** For an API, that's the request: the session dependency starts the transaction, commits it when the request succeeds, and calls `transaction.rollback()` when it fails. Managers don't commit.
- **Expected failures use a nested transaction.** When a statement may fail in an expected way (e.g. a unique constraint), the manager starts a nested transaction with `session.begin_nested()`, flushes, and on failure calls `transaction.rollback()` and raises a domain error. The request's transaction stays usable.
- **Start the nested transaction before changing anything.** `begin_nested()` first flushes pending changes, so changes made before it are written outside it and can't be rolled back by it. In the example below, `begin_nested()` comes before `site.name` is changed.

```python
# GOOD: the request's session dependency owns the transaction
def get_session() -> Generator[Session, None, None]:
    """
    Open a session for one request and run the request in one transaction.
    """
    with Session(engine) as session:
        transaction = session.begin()
        try:
            yield session
        except Exception:
            transaction.rollback()
            raise

        transaction.commit()


# GOOD: a manager uses a nested transaction for the expected failure
def update_site(session: Session, site_id: int, site_input: SiteInput) -> Site:
    """
    ...
    """
    site = read_site(session, site_id)
    transaction = session.begin_nested()
    site.name = site_input.name
    try:
        session.flush()
    except IntegrityError as error:
        transaction.rollback()
        raise DuplicateNameError(SITE_NAME_TAKEN) from error

    transaction.commit()
    return site

# BAD:
session.add(site)
try:
    session.commit()  # managers don't commit
except IntegrityError as error:
    session.rollback()  # never roll back through the session
    raise DuplicateNameError(SITE_NAME_TAKEN) from error
```
