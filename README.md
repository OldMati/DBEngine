# DBEngine

A relational database engine built from scratch in Python. No ORM and no embedded database underneath: storage, buffer management, indexing, query execution, and optimization are all implemented from first principles, following the design covered in CMU's [15-445](https://15445.courses.cs.cmu.edu/).

```sql
CREATE TABLE users (id INT, name VARCHAR, age INT)
INSERT INTO users VALUES (1, 'alice', 30), (2, 'bob', 25)
CREATE INDEX idx_age ON users (age)
SELECT * FROM users WHERE age >= 25 AND age < 40
DELETE FROM users WHERE id = 2
```

## Architecture

```
SQL string
   │  sqlglot
   ▼
Logical plan
   │  rule based optimizer: predicate pushdown, index selection, join selection
   ▼
Physical plan
   │  Volcano iterator model: open / next / close
   ▼
Execution operators: SeqScan, IndexScan, HashJoin, IndexJoin, Delete
   │
   ▼
B+ Tree index: point lookups, range scans, duplicate keys
   │
   ▼
Buffer pool: LRU-K replacement
   │
   ▼
Slotted page heap files (disk)
```

### Storage

- **Buffer pool** with LRU-K page replacement policy
- **Slotted page heap files** for variable length tuple storage
- **B+ tree** supporting point lookups, range scans, and duplicate keys

### Execution

Volcano style iterator model. Every operator implements `open()`, `next()`, `close()`.

| Operator | Purpose |
|---|---|
| Sequential scan | Full table scan |
| Index scan | B+ tree backed lookup or range scan |
| Hash join | Equi join via in memory hash table |
| Index join | Join using an existing index |
| Delete | Tuple removal |

### Query planning

SQL is parsed with `sqlglot`, converted to a logical plan, optimized, and lowered to a physical plan of operators. Supported statements:

`SELECT` (joins, filters, range predicates), `INSERT`, `DELETE`, `CREATE TABLE`, `CREATE INDEX`, `DROP TABLE`, `DESCRIBE`

Tables and indexes persist to disk and survive a restart.

### Optimizer

Rule based, not cost based:

- Predicate pushdown
- Uses an index scan whenever one covers an equality or range predicate
- Chooses between a hash join and an index join

## Getting started

```bash
pip install -r requirements.txt
python main.py
```

This starts an interactive REPL:

```
db> SELECT * FROM users WHERE age >= 25
--------------------------
| name       | age       |
--------------------------
| Alice      | 30        |
| Bob        | 25        |
--------------------------

Rows affected: 2
Executed in 0.000981s
```

## Design decisions and known limitations

- **Optimizer is rule based, not cost based.** It applies an index scan whenever one matches the predicate, without estimating selectivity, so it can occasionally pick an index scan where a sequential scan would be faster. A cost model would sit on top of the existing rules.
- **Indexes are single column and integer keyed.** No composite keys yet.
- **Deletes do not rebalance the B+ tree.** The tree can get sparse under heavy delete workloads, since there is no merge or redistribute on underflow.
- **Durability is flush on write, not write ahead logging.** A WAL is the natural next step for crash recovery without a full flush on every write.

## Roadmap

- [ ] Write ahead logging for crash recovery
- [ ] Cost based optimizer with selectivity estimation
- [ ] Composite and multi column indexes
- [ ] B+ tree merge and redistribute on deletion

## Stack

Python, [sqlglot](https://github.com/tobymao/sqlglot) for SQL parsing
