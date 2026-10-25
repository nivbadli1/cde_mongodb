# Homework - MongoDB as a Source (about 75-90 min)

You work in the same lab environment as in class (`docker compose up -d`, see the [README quickstart](../README.md#quickstart)).
**Start with fresh data:** run `bash lab/reset.sh` from the repo folder on your laptop, so your numbers match the self-checks.

| Task | What | Slides | Where | Time |
|---|---|---|---|---|
| HW1 | Data-quality report | 11, 15, 26 | [`notebooks/HW1_data_quality_report.ipynb`](notebooks/HW1_data_quality_report.ipynb) | ~15 min |
| HW2 | Silver flatten: `orders_flat` + `order_items` | 4, 15, 17, 25 | [`notebooks/HW2_silver_flatten.ipynb`](notebooks/HW2_silver_flatten.ipynb) | ~30 min |
| HW3 | A `$jsonSchema` contract, warn → error | 4, 16 | mongosh (below) | ~20 min |
| HW4 | 5 written questions | 31, 37, 40, 41, 42 | below | ~15 min |
| Optional | Connector questions (not graded) | 39-41 | below | ~10 min |

Not finished in class? The A4 `$unwind` query (top SKUs) and the A5 "Your turn" index are part of this homework too. Do them in mongosh from the [handout](handout.md) first.

## What to hand in

- The three completed notebooks: **B1** (from class, if you didn't finish it), **HW1**, **HW2**, all with their outputs and all self-checks printing `OK`
- One short answers file (`.md` or `.txt`) with your **HW3** commands + outputs and your **HW4** answers
- Deliver via: `<ask the instructor>`

Open Jupyter at <http://localhost:8888> (password: `<ask the instructor>`). The notebooks are in **lab/notebooks/**.

---

## HW1 - Data-quality report (~15 min) · slides 11, 15, 26

Open `lab/notebooks/HW1_data_quality_report.ipynb`, fill in the `# TODO` cells, and run the self-check.
It wants the type profile of `total` and `created_at`, missing `status`, duplicate `order_id` values, the two email shapes, and empty `items`. These are the checks from A2/A4, written as reusable functions.

## HW2 - Silver flatten (~30 min) · slides 4, 15, 17, 25

Open `lab/notebooks/HW2_silver_flatten.ipynb`. Build:
- `orders_flat`: one row per order, with the email from both schema versions in one field, `total` as a number, `status` in lowercase, and `created_at` as a real `datetime`
- `order_items`: one row per item, with `order_id`, `item_idx`, `sku`, `qty` as an int, and `unit_price`

You also decide whether orders with an empty `items` array stay in `order_items`, and explain why in the markdown cell. Plain Python is enough: dev_env has no pandas, and you don't need it.

## HW3 - A schema contract with `$jsonSchema` (~20 min) · slides 4, 16

Work in mongosh (`docker exec -it mongo mongosh`). Work on a **copy**, so the lab data stays untouched:

```javascript
use shop
db.orders.aggregate([{ $out: "orders_contract" }])
db.orders_contract.countDocuments({})        // → 200
```

1. **Write the contract.** Write a `$jsonSchema` validator for the fields the pipeline depends on:
   - `order_id`: a string
   - `status`: one of `created`, `paid`, `shipped`, `delivered`, `cancelled`
   - `total`: a decimal
   - `created_at`: a date

   All four are required. Slide 16 shows the shape of the `collMod` command.
2. **Apply it as a warning first.** Apply it to `orders_contract` with `validationLevel: "moderate"` and `validationAction: "warn"`.
3. **Insert 2 bad documents.** Each one should break a different rule. Both inserts must succeed, because `warn` only logs.
4. **Find the warnings in the server log.** From your laptop terminal:
   ```bash
   docker logs mongo 2>&1 | grep "Document would fail validation"
   ```
   Copy one log line into your answers file and point out which rule failed.
5. **Switch to rejecting.** Change the validator to `validationAction: "error"` and insert another bad document. Copy the error message.
6. **Explain `moderate`.** In 2-3 sentences: why does `validationLevel: "moderate"` fit an existing messy collection like this one? What would `"strict"` do to an app that updates an old, invalid order?

Clean up when you are done: `db.orders_contract.drop()`.

## HW4 - Written questions (~15 min) · slides 31, 37, 40, 41, 42

Answer each in 2-3 sentences.

1. **Oplog window (slide 31).** `rs.printReplicationInfo()` says the oplog covers 6 hours. The connector is down from Friday evening to Monday morning. What happens when it restarts, and what do you have to do?
2. **Deletes (slides 36, 37).** Why does a delete change event have no `fullDocument`? What does the Silver table have to do when it receives one?
3. **Connector delete settings (slide 40).** What happens to deletes with `publish.full.document.only=true`? Which setting adds tombstones, and what does a tombstone look like (key and value)?
4. **Failure table (slide 41).** The resume token is older than the oplog window. Which row of the failure table is this, what does the connector do, and what do you do?
5. **Checklist (slide 42).** Which of the 5 source-side checklist items would you apply first in a real project, and why?

---

## Optional (not graded): connector questions · slides 39-41

Read-only. No Kafka runs in this lab.

1. **Connector config (slide 39).** Read the config below. Which line does the same job as `full_document="updateLookup"` in `watch_orders.py`? Where does the connector keep the bookmark that you kept in `resume_token.json`?
   ```json
   {
     "name": "mongo-orders-source",
     "config": {
       "connector.class": "com.mongodb.kafka.connect.MongoSourceConnector",
       "connection.uri": "mongodb://mongo:27017/?replicaSet=rs0",
       "database": "shop",
       "collection": "orders",
       "startup.mode": "copy_existing",
       "change.stream.full.document": "updateLookup",
       "heartbeat.interval.ms": "10000"
     }
   }
   ```
2. **Delete semantics (slide 40).** With `publish.full.document.only=true`, what happens to your `CS-1` delete from B2? Which extra setting turns it into a tombstone (key = `_id`, value = `null`)?
3. **Failures (slide 41).** Which row of the failure table matches what you did with Ctrl+C in B2? Which row would apply if the watcher were stopped for longer than the oplog window you saw in Setup?
