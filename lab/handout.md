# MongoDB as a Source - Practice Lab (60 min)

**Goal:** explore a collection you have never seen, find its data problems, fix some with CRUD, analyze it with aggregations, speed up a query with an index, and watch changes live with a change stream.

Every section shows the slides it practices and a **mode**:
- **[TOGETHER]** the instructor runs it live on the projector, you copy along
- **[SOLO IN CLASS]** you work alone, the instructor walks around and helps
- **[HOMEWORK]** not done in class, see [homework.md](homework.md)

Expected outputs come from the seed-42 dataset: **numbers must match exactly**; spacing, field order and the order of groups may differ.

| Part | Section | Slides | Mode | Min |
|---|---|---|---|---|
| | Setup | 30-31 | TOGETHER | 8 |
| A (mongosh) | A1 Connect and explore | 18, 22 | TOGETHER | 4 |
| | A2 Find the data problems | 4, 11, 15, 26 | TOGETHER (first query), then SOLO | 6 |
| | A3 CRUD fixes | 19-21 | SOLO IN CLASS | 7 |
| | A4 Aggregations | 23-26 | SOLO IN CLASS | 9 |
| | A5 Index and explain | 27-29 | SOLO IN CLASS | 5 |
| | Catch-up buffer (switch to Jupyter, questions) | - | - | 2 |
| B (Python) | B1 PyMongo notebook | 11, 15, 17 | SOLO IN CLASS | 7 |
| | B2 Change stream | 35-38 | SOLO IN CLASS | 8 |
| | Wrap-up | 15, 40, 42 | TOGETHER | 4 |
| | **Total** | | | **60** |
| | Optional extras | 39-41 | HOMEWORK | - |

**Before class (at home):** in the repo folder run `docker compose pull` and then `docker compose up -d`, so the images are downloaded before you arrive.

**Connection rules (read once)**

| Where you run the code | Connection string |
|---|---|
| Inside `dev_env` (Jupyter, `docker exec -it dev_env bash`) | `mongodb://mongo:27017/?directConnection=true` |
| On your laptop (Compass, a local Python) | `mongodb://localhost:27017/?directConnection=true` |
| mongosh | `docker exec -it mongo mongosh` (no URI needed) |

Always keep `directConnection=true`: the replica set calls itself `mongo:27017`, a name your laptop cannot resolve.

---

## Setup (8 min) · slides 30-31
**[TOGETHER]**

**Goal:** a running 1-member replica set (slide 30) with 200 orders in `shop.orders`.

From the repo folder on your laptop (same commands as the README quickstart):
```bash
docker ps -a --filter name=dev_env --format "table {{.Names}}\t{{.Status}}"   # pre-check: an old dev_env? see Troubleshooting below
docker compose up -d
docker compose ps                                              # mongo STATUS must show (healthy)
docker exec dev_env bash /home/developer/lab/setup_dev_env.sh  # → pymongo 4.18.3 OK
docker exec -it dev_env bash
```
Inside dev_env:
```bash
cd /home/developer/lab
python3 seed_orders.py
# → wrote orders.json (200 docs)
#   inserted 200 docs into shop.orders
exit
```
Back on your laptop:
```bash
docker exec -it mongo mongosh
```
```javascript
rs.status().members[0].stateStr       // → 'PRIMARY'
rs.printReplicationInfo()             // slide 31: oplog size + "log length start to end"
use shop
```

> **PyMongo version.** The lab uses PyMongo 4.18+ (4.18.3 in dev_env, Python 3.10; 4.19.0 needs Python 3.11+). `setup_dev_env.sh` installs `pymongo==4.18.3`. On a laptop: `pip install "pymongo==4.18.3"`.
> The install lives inside the container: **re-run `docker exec dev_env bash /home/developer/lab/setup_dev_env.sh` after every `docker compose down`** (`docker compose stop`/`start` keeps it).

> **Troubleshooting: container name conflict.** If `docker compose up -d` fails with
> `Conflict. The container name "/dev_env" is already in use` (a leftover from the Kafka lessons):
> stop any Kafka-lesson work first (ports 22022 and 8888 are shared), then run `docker rm -f dev_env` and `docker compose up -d` again.
> This removes the old container only, not files on your laptop.

**Reflection:** `rs.printReplicationInfo()` shows the oplog window. What happens to a consumer that is down longer than that window? (slide 31)

---

# Part A - mongosh

Keep the mongosh session open for all of Part A.

## A1 Connect and explore (4 min) · slides 18, 22
**[TOGETHER]**

**Goal:** the "first five minutes" checklist on an unknown collection.

```javascript
db.getCollectionNames()                          // → [ 'orders' ]
db.orders.estimatedDocumentCount()               // → 200  (fast, from metadata)
db.orders.countDocuments({})                     // → 200  (exact)
db.orders.findOne()                              // one full document - read its fields
db.orders.find({ order_id: "ORD-10001" })        // WHERE order_id = 'ORD-10001' → 1 document, 4 items
db.orders.aggregate([{ $sample: { size: 2 } }])  // 2 random docs - compare their shapes!
db.orders.distinct("status")
// → [ 'CANCELLED','CREATED','Cancelled','DELIVERED','Delivered','PAID','Paid',
//     'SHIPPED','Shipped','cancelled','created','delivered','paid','shipped' ]   (14 values)
```

**Reflection:** the business expects 5 statuses. Why is `$sample` better than `find().limit()` for spotting problems like this? (slide 22)

## A2 Find the data problems (6 min) · slides 4, 11, 15, 26
**[TOGETHER]** for the first query (missing status), then **[SOLO IN CLASS]** for the rest and the "Your turn".

**Goal:** profile types and shapes - the things a schema-on-read source (slide 4) lets in silently.

```javascript
// Missing required field (slide 26)
db.orders.countDocuments({ status: { $exists: false } })          // → 7
```
Now on your own:
```javascript
// Type profile (slides 11, 26) - SQL has no equivalent
db.orders.aggregate([{ $group: { _id: { $type: "$total" }, n: { $sum: 1 } } }])
// → decimal 115, double 55, string 19, missing 11
db.orders.aggregate([{ $group: { _id: { $type: "$created_at" }, n: { $sum: 1 } } }])
// → date 162, string 26, long 12

// Schema drift (slide 15)
db.orders.aggregate([{ $group: { _id: "$schema_v", n: { $sum: 1 } } }])
// → 1: 107, 2: 93
db.orders.countDocuments({ "customer.email": { $exists: true } })          // → 107
db.orders.countDocuments({ "customer.contact.email": { $exists: true } })  // → 93

// Empty arrays ($size: 0 = an array with zero elements)
db.orders.countDocuments({ items: { $size: 0 } })                          // → 40
```

**Task:** write down at least 4 data problems you found.
(Expected: mixed `total` types, inconsistent `status` case + missing, `created_at` in 3 formats, email moved between schema versions, empty `items`. You will find inconsistent city names and duplicate `order_id` in A4.)

**Your turn:** count the orders that have **no email in either place** (neither `customer.email` nor `customer.contact.email`).

<details><summary>Answer</summary>

```javascript
db.orders.countDocuments({ "customer.email": { $exists: false }, "customer.contact.email": { $exists: false } })
// → 0
```
Every order has an email - it just lives in one of two places (107 + 93 = 200).
</details>

**Reflection:** in a schema-on-write database (slide 4), which of these problems would have been rejected at insert time?

## A3 CRUD fixes (7 min) · slides 19-21
**[SOLO IN CLASS]**

**Goal:** see silent exclusion, fix the status casing with a pipeline update, and practice upsert + delete.

```javascript
// 1. Silent exclusion: numbers vs strings (slide 19)
db.orders.countDocuments({ total: { $gte: 1000 } })        // → 75
db.orders.countDocuments({ total: { $type: "string" } })   // → 19

// 2. Case sensitivity (slide 19)
db.orders.countDocuments({ "shipping.address.city": "Haifa", status: "delivered" })   // → 2

// 3. Fix status casing = UPDATE ... SET status = LOWER(status) (slide 20)
db.orders.updateMany({ status: { $exists: true } },
                     [{ $set: { status: { $toLower: "$status" } } }])
// → matchedCount: 193, modifiedCount: 30
db.orders.distinct("status")   // → [ 'cancelled', 'created', 'delivered', 'paid', 'shipped' ]
db.orders.countDocuments({ "shipping.address.city": "Haifa", status: "delivered" })   // → 3

// 4. Insert + upsert + delete your own test orders (slides 18, 20, 21)
db.orders.insertOne({ order_id: "ORD-TEST-1", status: "created", total: NumberDecimal("10.00"), created_at: new Date() })
db.orders.updateOne({ order_id: "ORD-TEST-2" }, { $set: { status: "created" } }, { upsert: true })
// → upsertedCount: 1
db.orders.deleteMany({ order_id: { $in: ["ORD-TEST-1", "ORD-TEST-2"] } })   // → deletedCount: 2
db.orders.countDocuments({})                                                // → 200
```

**Your turn:** count the orders with **more than 2 items**.
Hint: dot notation also works with array positions - `items.2` is the 3rd element of `items`.

<details><summary>Answer</summary>

```javascript
db.orders.countDocuments({ "items.2": { $exists: true } })
// → 51
```
If the 3rd element exists, the order has at least 3 items.
</details>

**Reflection:** how many of the 19 string totals are actually >= 1000? (Answer from slide 19: 7 - so the true count is 82, not 75.)

## A4 Aggregations (9 min) · slides 23-26
**[SOLO IN CLASS]**

**Goal:** translate GROUP BY queries into pipelines. A4 assumes you ran the status fix in A3.

**1. Orders per status** - `GROUP BY status ORDER BY 2 DESC` (slides 23, 24)
```javascript
db.orders.aggregate([
  { $group: { _id: "$status", n: { $sum: 1 } } },
  { $sort: { n: -1 } }
])
// → cancelled 58, delivered 36, shipped 34, created 33, paid 32, null 7
```
(If you skipped the A3 fix and group by `{ $toLower: "$status" }` instead, the 7 missing statuses show as `""`, not `null` - `$toLower` turns missing into an empty string.)

**2. Revenue per city, excluding cancelled** (slide 24)
```javascript
db.orders.aggregate([
  { $match: { status: { $ne: "cancelled" } } },
  { $group: {
      _id: { $replaceAll: { input: { $toLower: "$shipping.address.city" }, find: "-", replacement: " " } },
      orders:  { $sum: 1 },
      revenue: { $sum: { $convert: { input: "$total", to: "decimal", onError: null, onNull: null } } } } },
  { $sort: { revenue: -1 } }, { $limit: 3 }
])
// → netanya    28 orders  31354.60
//   haifa      26 orders  29292.90
//   jerusalem  18 orders  24802.70
```
Decimal sums may print with extra trailing zeros, e.g. `Decimal128('31354.600000000000')`.
Follow-up: remove `$limit` and find the cities that still don't merge (`tlv`, `beer sheva` vs `be'er sheva`).

**3. Top 3 SKUs by quantity** - `$unwind` = explode (slide 25) *(if time remains, otherwise homework)*
```javascript
db.orders.aggregate([
  { $unwind: "$items" },
  { $group: { _id: "$items.sku", name: { $first: "$items.name" }, qty: { $sum: { $toInt: "$items.qty" } } } },
  { $sort: { qty: -1 } }, { $limit: 3 }
])
// → SKU-105 Backpack 100, SKU-106 Sunglasses 98, SKU-107 Bike Helmet 92
```
Follow-up: remove `$toInt`. Why do the numbers drop? (String qtys are ignored by `$sum`.)

**4. Duplicate business keys** - `GROUP BY order_id HAVING COUNT(*) > 1` (slide 26)
```javascript
db.orders.aggregate([{ $group: { _id: "$order_id", n: { $sum: 1 } } }, { $match: { n: { $gt: 1 } } }])
// → ORD-10010 (2), ORD-10011 (2)
```

**Your turn:** number of orders **per payment method** (`payment.method`), including the orders that have no payment at all, sorted by count.

<details><summary>Answer</summary>

```javascript
db.orders.aggregate([
  { $group: { _id: "$payment.method", n: { $sum: 1 } } },
  { $sort: { n: -1 } }
])
// → apple_pay 47, credit_card 44, paypal 44, bit 43, null 22
```
The 22 orders without a `payment` sub-document group under `null`. (`credit_card` and `paypal` tie at 44, so their order may swap.)
</details>

**Reflection:** which of these four queries would you turn into an automated data-quality test in your pipeline? (slide 26)

## A5 Index and explain (5 min) · slides 27-29
**[SOLO IN CLASS]**

**Goal:** see COLLSCAN turn into IXSCAN, and read the three numbers from slide 29.

```javascript
db.orders.find({ "customer.customer_id": "C0008" }).explain("executionStats").executionStats
// → nReturned: 11, totalDocsExamined: 200, executionStages.stage: 'COLLSCAN'
db.orders.createIndex({ "customer.customer_id": 1 })
db.orders.find({ "customer.customer_id": "C0008" }).explain("executionStats").executionStats
// → nReturned: 11, totalKeysExamined: 11, totalDocsExamined: 11
//   (executionStages.stage: 'FETCH' with inputStage.stage: 'IXSCAN')
```
If the first explain already shows IXSCAN, you created the index earlier: `db.orders.dropIndex({ "customer.customer_id": 1 })` and run it again.

**Your turn (bonus, slide 28)** *(if time remains, otherwise homework)*: create an index that supports `db.orders.find({ status: "paid" }).sort({ created_at: -1 })` and prove with `explain` that **no `SORT` stage** appears.

<details><summary>Answer</summary>

```javascript
db.orders.createIndex({ status: 1, created_at: -1 })        // → status_1_created_at_-1
db.orders.find({ status: "paid" }).sort({ created_at: -1 }).explain("executionStats").queryPlanner.winningPlan
// → { stage: 'FETCH',
//     inputStage: { stage: 'IXSCAN', indexName: 'status_1_created_at_-1', ... } }
db.orders.find({ status: "paid" }).sort({ created_at: -1 }).explain("executionStats").executionStats.nReturned
// → 32
```
Without the index the winning plan is `SORT` over `COLLSCAN`. Equality field (`status`) first, then the sort field (`created_at`): the ESR rule from slide 28. (32 assumes you ran the A3 status fix.)
</details>

**Reflection:** your nightly export filters on a field with no index. Who pays the price? (slide 27)

---

# Part B - Python

*(2 min catch-up buffer: finish your current task, open Jupyter, ask questions.)*

Open Jupyter at <http://localhost:8888> (password: `developer` - the local course container only). The repo's `lab` folder is mounted at `/home/developer/lab`, so you see it as **lab/** in the file browser.

## B1 PyMongo notebook (7 min) · slides 11, 15, 17
**[SOLO IN CLASS]**

**Goal:** see the same problems the way a pipeline sees them: Python types, a v1/v2 email flatten, and an items explode.

Open `lab/notebooks/B1_pymongo_explore.ipynb` and run all cells top to bottom. Expected outputs are written under each cell. Key numbers:

| Cell | Expected |
|---|---|
| Connect | `orders: 200` |
| Type conflicts | `total`: Decimal128 115, float 55, str 19, missing 11 · `created_at`: datetime 162, str 26, Int64 12 |
| Flatten email | naive: 93 missing · fixed: 0 missing · schema_v 1: 107, 2: 93 |
| Explode items | 381 item rows, 40 of them from empty orders, 36 string qtys fixed |

**Reflection:** with a plain (inner) explode, how many orders would vanish from the item table? (slide 17)

## B2 Change stream (8 min) · slides 35-38
**[SOLO IN CLASS]**

**Goal:** watch insert / update / delete events live, stop the consumer, and resume from the saved token.

You need **two terminals** on your laptop.

**Terminal 1 - the watcher (inside dev_env):**
```bash
docker exec -it dev_env bash
cd /home/developer/lab
python3 watch_orders.py --from-scratch
# → Watching shop.orders  (resume_after=None -> now)
```
**Terminal 2 - mongosh:**
```javascript
use shop
db.orders.insertOne({ order_id: "CS-1", status: "created" })
db.orders.updateOne({ order_id: "CS-1" }, { $set: { status: "paid" } })
```
Expected in Terminal 1 (ids/times will differ):
```
=== INSERT  _id=...  clusterTime=Timestamp(..., 1)
  fullDocument  : {"_id": {"$oid": "..."}, "order_id": "CS-1", "status": "created"}
=== UPDATE  _id=...
  updatedFields : {"status": "paid"}
  removedFields : []
  fullDocument  : {"_id": {"$oid": "..."}, "order_id": "CS-1", "status": "paid"}
```
Now **Ctrl+C** the watcher, then in mongosh: `db.orders.deleteOne({ order_id: "CS-1" })`. Restart **without** `--from-scratch`:
```bash
python3 watch_orders.py
```
```
Watching shop.orders  (resume_after=saved token)
=== DELETE  _id=...
  (delete events carry only the _id - no fullDocument)
```
The delete happened while the watcher was down and still arrived: it resumed from `resume_token.json` (slide 37).

> Use `docker exec -it dev_env bash`, not the Jupyter terminal: Jupyter's terminal does not get the `MONGO_URI` variable, so the script would try `localhost`. If you must use it, run `export MONGO_URI="mongodb://mongo:27017/?directConnection=true"` first.
>
> No second terminal? Run `lab/notebooks/B2_change_stream.ipynb` instead: same steps (insert, update, close, delete, resume) in one notebook.

**Reflection:** the delete event shows no `status`. Why, and what does that mean for a Silver table that only receives these events? (slide 36)

---

## Wrap-up (4 min) · slides 15, 40, 42
**[TOGETHER]**

What you just did with `resume_token.json` is what the Kafka source connector does with Kafka Connect offsets.

**Task:** write down which of the 5 items from the source-side checklist (slide 42) you would apply first in your own pipeline, and why:

1. **Oplog window** longer than your longest outage
2. **Decide how deletes arrive**: tombstones or they vanish
3. **Profile types and shapes**: `$type`, `schema_v`, a `$jsonSchema` contract
4. **Idempotent sink**: MERGE by `_id`, expect duplicates
5. **Quiet collections**: set `heartbeat.interval.ms`

Then, as a class: **what was hard today?** (one sentence each)

---

## Optional extras · slides 39-41
**[HOMEWORK]**

The connector questions (read-only config, delete semantics, failure table) moved to [homework.md](homework.md) (section "Optional").

---

**Start over** (drops `shop`, re-seeds, deletes `resume_token.json`): `bash lab/reset.sh` from the repo folder (Git Bash or WSL on Windows).
