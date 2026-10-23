# SQL Conventions Checklist

Run this per changed Python file that defines a table model or changes data through a database session. Every item must be answered ✅, ❌ (with `file:line`), or N/A.

- [ ] SQL-04 (auto) Table models declare indexes in `__table_args__` (`Index(...)`), never with `index=True` on a `Field` or `Column`
- [ ] SQL-05 Table models: `__tablename__` is the first line after the docstring and `__table_args__` is last (the checker reports these as PY-30 / PY-31)
- [ ] SQL-01 No `session.rollback()`: rollbacks go through the transaction object (`transaction.rollback()`)
- [ ] SQL-02 The unit of work (e.g. the request's session dependency) starts the transaction and commits or rolls it back; managers don't commit
- [ ] SQL-03 Expected failures (e.g. constraints) use a nested transaction (`session.begin_nested()`) started **before** the objects are changed, rolled back with `transaction.rollback()`
