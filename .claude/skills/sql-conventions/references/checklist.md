# SQL Conventions Checklist

Run this per changed Python file that changes data through a database session. Every item must be answered ✅, ❌ (with `file:line`), or N/A.

- [ ] SQL-01 No `session.rollback()`: rollbacks go through the transaction object (`transaction.rollback()`)
- [ ] SQL-02 The unit of work (e.g. the request's session dependency) starts the transaction and commits or rolls it back; managers don't commit
- [ ] SQL-03 Expected failures (e.g. constraints) use a nested transaction (`session.begin_nested()`) started **before** the objects are changed, rolled back with `transaction.rollback()`
