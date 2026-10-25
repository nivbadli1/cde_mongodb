# Slide → Lab Map

Slide numbers refer to the final 44-slide deck ([`MongoDB_Lesson_Deck_Content.md`](MongoDB_Lesson_Deck_Content.md)). Student instructions: [`lab/handout.md`](../lab/handout.md).

| Lab section | Min | Slides | What the student does |
|---|---|---|---|
| Setup | 5 | 30, 31 | `docker compose up -d`, check `(healthy)`, install PyMongo in dev_env, run `seed_orders.py`, `rs.status()` → PRIMARY, `rs.printReplicationInfo()` (oplog window) |
| A1 Connect and explore | 8 | 18, 22 | `getCollectionNames`, `estimatedDocumentCount` vs `countDocuments`, `findOne`, `find` by `order_id`, `$sample`, `distinct("status")` → 14 values |
| A2 Find the data problems | 7 | 4, 11, 15, 26 | Missing `status` (7), `$type` profile of `total` and `created_at`, `schema_v` 107/93, v1 vs v2 email `$exists`, empty `items` (40); lists ≥ 4 problems |
| A3 CRUD fixes | 8 | 19, 20, 21 | Silent exclusion (`$gte: 1000` → 75 vs 19 strings), case-sensitive filter, pipeline update `$toLower` (modified 30), insert + upsert + `deleteMany` |
| A4 Aggregations | 10 | 23, 24, 25, 26 | Orders per status, revenue per city with `$convert` + `$replaceAll`, top SKUs with `$unwind` + `$toInt`, duplicate `order_id` (HAVING) |
| A5 Index and explain | 5 | 27, 28, 29 | `explain("executionStats")` before/after `createIndex`: COLLSCAN 200 docs → IXSCAN 11 docs; bonus compound index (no SORT stage) |
| B1 PyMongo notebook | 7 | 11, 15, 17 | `B1_pymongo_explore.ipynb`: `$sample`, Python type profile, flatten email across v1/v2 (93 → 0 missing), explode items keeping empty orders (381 rows) |
| B2 Change stream | 8 | 35, 36, 37, 38 | `watch_orders.py` in a terminal (or `B2_change_stream.ipynb`): insert, update (`updatedFields` + `fullDocument`), Ctrl+C, delete while stopped, resume from token |
| Wrap-up | 2 | 15, 40, 42 | Picks which of the 5 source-side checklist items to apply first; links the resume token to Kafka Connect offsets |
| Optional extras | - | 39, 40, 41 | Reads the connector config, answers delete-semantics (tombstones) and failure-table questions; no Kafka needed |
| **Total** | **60** | | |

## Slides not practiced in the lab

1-3, 5-10, 12-14, 16, 32-34, 43, 44 (concepts, use cases, modeling, validation, concerns, sharding, transactions, summary, vocabulary). Slide 44 (vocabulary map) is useful to keep on screen during Part A.
