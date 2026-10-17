# SQL Conventions Checklist

Run this per changed Python file that uses a database session, a model, or a migration. Every item must be answered ✅, ❌ (with `file:line`), or N/A.

## Sessions & transactions
- [ ] SQL-01 Sessions come from a dependency function and are passed in as parameters; no global session
- [ ] SQL-02 Each unit of work starts an explicit transaction before its first query and keeps the transaction object
- [ ] SQL-03 Commit and rollback go through the transaction object; no `session.rollback()`, and no scattered `session.commit()`
- [ ] SQL-04 Partial failures use a savepoint (`begin_nested()`), not a second top-level transaction

## Queries
- [ ] SQL-10 No SQL built with f-strings, `%`, or concatenation; raw SQL uses `text()` with bound parameters
- [ ] SQL-11 User search escapes `%`, `_`, and the escape character
- [ ] SQL-12 Paginated queries `order_by` a unique, stable key
- [ ] SQL-13 Filtering happens in SQL, not in Python
- [ ] SQL-14 No N+1 queries: related rows read in a loop are eager-loaded
- [ ] SQL-15 Soft-deleted rows are filtered out wherever they shouldn't appear

## Integrity & models
- [ ] SQL-20 Uniqueness and other rules are enforced by database constraints; `IntegrityError` becomes a domain error
- [ ] SQL-21 Constraints and indexes have explicit, descriptive names
- [ ] SQL-22 Frequently filtered, joined, or sorted columns are indexed
- [ ] SQL-23 Timestamps are timezone-aware

## Migrations
- [ ] SQL-30 Every schema change has a migration, with a working `downgrade`
- [ ] SQL-31 No already-applied migration was edited
- [ ] SQL-32 New `NOT NULL` columns on existing tables have a default or a backfill
