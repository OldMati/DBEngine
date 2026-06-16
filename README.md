# DBEngine

A small relational database I built from scratch in Python — storage, execution, and query planning, with no database or ORM doing the work underneath. I followed CMU's 15-445 course and implemented each layer myself.

It runs real SQL:

```sql
CREATE TABLE users (id INT, name VARCHAR, age INT)
INSERT INTO users VALUES (1, 'alice', 30), (2, 'bob', 25)
CREATE INDEX idx_age ON users (age)
SELECT name FROM users WHERE age >= 25 AND age < 40
DELETE FROM users WHERE id = 2
```

## What's in it

**Storage** — a buffer pool with LRU-K page replacement, slotted-page heap files, and a B+ tree that handles point lookups, range scans, and duplicate keys.

**Execution** — the Volcano iterator model, where every operator implements `open`/`next`/`close`. So far: sequential scan, index scan, hash join, index join, and delete.

**SQL and planning** — queries are parsed with `sqlglot`, turned into a logical plan, optimized, then lowered to a physical plan of operators. Supports `SELECT` (joins, filters, range predicates), `INSERT`, `DELETE`, `CREATE TABLE`, `CREATE INDEX`, `DROP TABLE`, and `DESCRIBE`. Tables and indexes are persisted, so they survive a restart.

**Optimizer** — rule-based. It does predicate pushdown, picks an index scan when one covers an equality or range predicate, and chooses between a hash join and an index join.

## Running it

```bash
pip install -r requirements.txt
python main.py
```

That drops you into a REPL:

```
db> SELECT name, age FROM users WHERE age >= 25
--------------------------
| name       | age       |
--------------------------
| Alice      | 30        |
| Bob        | 25        |
--------------------------

Rows affected: 2
Executed in 0.000981s
```

## Future work

The optimizer is rule-based, not cost-based — it'll use an index whenever one matches, without checking how selective the query actually is, so it can occasionally pick an index scan where a plain table scan would've been faster. A cost model would sit on top of these same rules.

Indexes are single-column and integer-keyed for now. Deletes remove entries but don't rebalance the tree, so it can get a bit sparse under heavy deletion. And durability is flush-on-write rather than a proper write-ahead log — WAL is the obvious next thing if I keep going.
