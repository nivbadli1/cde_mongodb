# Slide → Lab Map

Slide numbers refer to the final 44-slide deck ([`MongoDB_Lesson_Deck_Content.md`](MongoDB_Lesson_Deck_Content.md)). Student instructions: [`lab/handout.md`](../lab/handout.md). Homework: [`lab/homework.md`](../lab/homework.md).

| Lab section | Mode | Min | Slides | What the student does |
|---|---|---|---|---|
| Setup | TOGETHER | 8 | 30, 31 | `docker compose up -d`, check `(healthy)`, `setup_dev_env.sh`, run `seed_orders.py`, `rs.status()` → PRIMARY, `rs.printReplicationInfo()` (oplog window) |
| A1 Connect and explore | TOGETHER | 4 | 18, 22 | `getCollectionNames`, `estimatedDocumentCount` vs `countDocuments`, `findOne`, `find` by `order_id`, `$sample`, `distinct("status")` → 14 values |
| A2 Find the data problems | TOGETHER (1st query) → SOLO | 6 | 4, 11, 15, 26 | Missing `status` (7), `$type` profile of `total` and `created_at`, `schema_v` 107/93, v1 vs v2 email `$exists`, empty `items` (40); Your turn: orders with no email anywhere |
| A3 CRUD fixes | SOLO | 7 | 19, 20, 21 | Silent exclusion (`$gte: 1000` → 75 vs 19 strings), case-sensitive filter, pipeline update `$toLower` (modified 30), insert + upsert + `deleteMany`; Your turn: orders with more than 2 items |
| A4 Aggregations | SOLO | 9 | 23, 24, 25, 26 | Orders per status, revenue per city, top SKUs with `$unwind` (if time remains), duplicate `order_id`; Your turn: orders per payment method |
| A5 Index and explain | SOLO | 5 | 27, 28, 29 | `explain("executionStats")` before/after `createIndex`: COLLSCAN 200 docs → IXSCAN 11 docs; Your turn (if time remains): compound index, no SORT stage |
| Buffer | - | 2 | - | Catch up, open Jupyter |
| B1 PyMongo notebook | SOLO | 7 | 11, 15, 17 | `B1_pymongo_explore.ipynb`: `$sample`, Python type profile, flatten email across v1/v2 (93 → 0 missing), explode items keeping empty orders (381 rows) |
| B2 Change stream | SOLO | 8 | 35, 36, 37, 38 | `watch_orders.py` in a terminal (or `B2_change_stream.ipynb`): insert, update (`updatedFields` + `fullDocument`), Ctrl+C, delete while stopped, resume from token |
| Wrap-up | TOGETHER | 4 | 15, 40, 42 | Picks which of the 5 source-side checklist items to apply first; what was hard |
| **Total in class** | | **60** | | |
| HW1 Data-quality report | HOMEWORK | ~15 | 11, 15, 26 | `HW1_data_quality_report.ipynb`: type profiles, missing status, duplicate keys, email shapes, empty items as functions; self-check |
| HW2 Silver flatten | HOMEWORK | ~30 | 4, 15, 17, 25 | `HW2_silver_flatten.ipynb`: `orders_flat` (unified email, numeric total, lowercase status, datetime) + `order_items` (int qty); decides on empty orders; self-check |
| HW3 `$jsonSchema` contract | HOMEWORK | ~20 | 4, 16 | Copy with `$out`, validator in `warn` → find the log line → `error` → rejection; explain `moderate` |
| HW4 Written questions | HOMEWORK | ~15 | 31, 37, 40, 41, 42 | Oplog window, delete events, tombstones, failure table, checklist |
| Optional extras | HOMEWORK (optional) | ~10 | 39, 40, 41 | Reads the connector config, answers delete-semantics and failure-table questions; no Kafka needed |

## Slides not practiced in the lab

1-3, 5-10, 12-14, 32-34, 43, 44 (concepts, use cases, modeling, concerns, sharding, transactions, summary, vocabulary). Slide 16 (validation) is practiced in homework HW3 only. Slide 44 (vocabulary map) is useful to keep on screen during Part A.
