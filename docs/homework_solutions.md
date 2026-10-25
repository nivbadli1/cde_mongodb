# Homework Solutions (instructor only)

> **This repository is public.** Anyone with the link can read this file. Remove it (or move it to a private place) before you share the repo with students.

Everything here was run on freshly seeded data (`bash lab/reset.sh`): MongoDB 8.0, dev_env Python 3.10, PyMongo 4.18.3.

---

## HW1 - Data-quality report

Solution cells (they replace the `# TODO` cells, in order):

```python
def type_profile(field):
    rows = coll.aggregate([{"$group": {"_id": {"$type": f"${field}"}, "n": {"$sum": 1}}}])
    return {r["_id"]: r["n"] for r in rows}
```

```python
def missing_status():
    return coll.count_documents({"status": {"$exists": False}})

def duplicate_order_ids():
    rows = coll.aggregate([
        {"$group": {"_id": "$order_id", "n": {"$sum": 1}}},
        {"$match": {"n": {"$gt": 1}}},
    ])
    return sorted(r["_id"] for r in rows)

def email_shapes():
    return {
        "customer.email": coll.count_documents({"customer.email": {"$exists": True}}),
        "customer.contact.email": coll.count_documents({"customer.contact.email": {"$exists": True}}),
    }

def empty_items():
    return coll.count_documents({"items": {"$size": 0}})
```

Output of the report and self-check cells:
```
total_types         : {'double': 55, 'missing': 11, 'string': 19, 'decimal': 115}
created_at_types    : {'long': 12, 'date': 162, 'string': 26}
missing_status      : 7
duplicate_order_ids : ['ORD-10010', 'ORD-10011']
email_shapes        : {'customer.email': 107, 'customer.contact.email': 93}
empty_items         : 40
OK total_types
...
HW1 self-check passed
```
(The order of keys inside the type dicts may differ. The self-check compares dicts, so order doesn't matter.)

**Reflection, model answer:** fail the load on things that break the Silver contract or the MERGE: duplicate `_id`s (impossible here, but checked), a new `$type` showing up for `total` or `created_at`, or a sudden jump in missing status or email. Only warn on known, tolerated mess that Silver already converts (string totals, three date formats, empty items).

---

## HW2 - Silver flatten

Solution cells:

```python
from datetime import datetime, timezone
from bson import Decimal128

def unified_email(doc):
    customer = doc["customer"]
    return customer.get("email") or customer.get("contact", {}).get("email")

def total_as_number(doc):
    value = doc.get("total")
    if value is None:
        return None
    if isinstance(value, Decimal128):
        return float(value.to_decimal())
    return float(value)                      # float stays float, "499.00" -> 499.0

def clean_status(doc):
    status = doc.get("status")
    return status.lower() if status is not None else None

def created_at_as_datetime(doc):
    value = doc["created_at"]
    if isinstance(value, datetime):
        return value                          # already naive UTC from PyMongo
    if isinstance(value, str):
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    # epoch milliseconds (int / bson Int64)
    return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).replace(tzinfo=None)
```

```python
orders_flat = [
    {
        "_id": d["_id"],
        "order_id": d["order_id"],
        "schema_v": d["schema_v"],
        "email": unified_email(d),
        "total": total_as_number(d),
        "status": clean_status(d),
        "created_at": created_at_as_datetime(d),
        "city": d["shipping"]["address"]["city"],
    }
    for d in docs
]
```

```python
KEEP_EMPTY_ORDERS = False   # item table = real items only; empty orders still exist in orders_flat

order_items = []
for d in docs:
    if not d["items"] and KEEP_EMPTY_ORDERS:
        order_items.append({"order_id": d["order_id"], "item_idx": None, "sku": None,
                            "qty": None, "unit_price": None})
    for idx, item in enumerate(d["items"]):
        order_items.append({
            "order_id": d["order_id"],
            "item_idx": idx,
            "sku": item["sku"],
            "qty": int(item["qty"]),
            "unit_price": float(item["unit_price"]),
        })
```

Self-check output:
```
OK orders_flat has 200 rows
OK zero null emails
OK total is a number (11 missing)
OK status is lowercase (7 missing)
OK created_at is a datetime for all 200 rows
OK order_items has 341 rows (KEEP_EMPTY_ORDERS=False)
OK qty is int (total quantity 682)
HW2 self-check passed
```
With `KEEP_EMPTY_ORDERS = True` the same cells give `OK order_items has 381 rows (KEEP_EMPTY_ORDERS=True)` and pass too.

**Empty orders, model answer:** either choice is fine if it's argued. *Drop* (341 rows): `order_items` means real items, sums and counts are not polluted by NULL rows, and the 40 empty orders are still visible in `orders_flat`. *Keep* (381 rows, `explode_outer`): every order shows up in the item table, so a downstream inner join on `order_items` won't silently lose orders. The answer that loses points is "dropped them" with no reason, since that is the silent `explode` / `$unwind` loss from slides 17 and 25.

**Merge key, model answer:** `_id`. It is unique and immutable, and the change events carry it as `documentKey` (slides 12, 36). `order_id` has duplicates from the app's retry bug (ORD-10010, ORD-10011).

---

## HW3 - `$jsonSchema` contract

```javascript
use shop
db.orders.aggregate([{ $out: "orders_contract" }])
db.orders_contract.countDocuments({})          // → 200

const contract = {
  $jsonSchema: {
    bsonType: "object",
    required: ["order_id", "status", "created_at", "total"],
    properties: {
      order_id:   { bsonType: "string" },
      status:     { enum: ["created", "paid", "shipped", "delivered", "cancelled"] },
      created_at: { bsonType: "date" },
      total:      { bsonType: "decimal" }
    }
  }
}

// 1. warn first
db.runCommand({ collMod: "orders_contract", validator: contract,
                validationLevel: "moderate", validationAction: "warn" })
// → { ok: 1, ... }

// 2. two bad documents - both are accepted (warn only logs)
db.orders_contract.insertOne({ order_id: "BAD-1", status: "SHIPPED", created_at: new Date(), total: NumberDecimal("10.00") })   // status not in enum
db.orders_contract.insertOne({ order_id: "BAD-2", status: "paid", created_at: "2026-10-25", total: "10.00" })                   // created_at and total are strings
// → { acknowledged: true, insertedId: ObjectId('...') }  (both)
db.orders_contract.countDocuments({ order_id: /^BAD-/ })   // → 2

// Bonus: how many existing orders break the contract? ($jsonSchema also works as a query)
db.orders.countDocuments({ $nor: [ contract ] })            // → 118  (on freshly seeded data)
```

Find the warnings (laptop terminal):
```bash
docker logs mongo 2>&1 | grep "Document would fail validation"
```
```
{"t":{"$date":"..."},"s":"W","c":"STORAGE","id":20294,"ctx":"conn..","msg":"Document would fail validation","attr":{"namespace":"shop.orders_contract","document":{"_id":{"$oid":"..."},"order_id":"BAD-1","status":"SHIPPED",...},"errInfo":{...}}}
{"t":{"$date":"..."},"s":"W","c":"STORAGE","id":20294,"ctx":"conn..","msg":"Document would fail validation","attr":{"namespace":"shop.orders_contract","document":{"_id":{"$oid":"..."},"order_id":"BAD-2","status":"paid","created_at":"2026-10-25","total":"10.00"},"errInfo":{...}}}
```
One line per bad insert (2 lines). `errInfo.details` names the failing rule.

```javascript
// 3. switch to error - the same kind of document is now rejected
db.runCommand({ collMod: "orders_contract", validationAction: "error" })
db.orders_contract.insertOne({ order_id: "BAD-3", status: "SHIPPED", created_at: new Date(), total: NumberDecimal("10.00") })
// → MongoServerError: Document failed validation
//   Additional information: { ... propertyName: 'status', ... reason: 'value was not found in enum', consideredValue: 'SHIPPED' }
db.orders_contract.insertOne({ order_id: "GOOD-1", status: "paid", created_at: new Date(), total: NumberDecimal("10.00") })
// → acknowledged: true

// 4. moderate vs strict: update an OLD invalid order (string total)
db.orders_contract.updateOne({ order_id: "ORD-10006" }, { $set: { note: "touched" } })
// moderate → matchedCount: 1, modifiedCount: 1   (old invalid docs are not re-checked)
db.runCommand({ collMod: "orders_contract", validationLevel: "strict" })
db.orders_contract.updateOne({ order_id: "ORD-10006" }, { $set: { note: "touched again" } })   // a real change: a no-op update is not validated
// strict → MongoServerError: Document failed validation

db.orders_contract.drop()
```

**Why `moderate`, model answer:** the collection already holds 118 orders that break the contract. With `moderate`, new inserts and updates to documents that are *already valid* are checked, but updates to old invalid documents are not. So the contract protects everything new without breaking the app the first time it touches a legacy order. `strict` would reject any update to an old invalid order (the `ORD-10006` update above), which breaks the app until all old data is migrated. Going `warn` → `error` follows the same idea: watch the logs first, then enforce.

---

## HW4 - Model answers

1. **Oplog window.** The oplog is capped, so after more than 6 hours the entries after the connector's saved resume token have been overwritten. On Monday it can't resume (invalid resume token / `ChangeStreamHistoryLost`) and stops. You must re-snapshot (`startup.mode=copy_existing` with a new `offset.partition.name`) and accept or backfill the gap. Prevention: an oplog window longer than your longest outage (checklist item 1).
2. **Deletes.** When the delete event is produced, the document no longer exists, so there is nothing to put in `fullDocument`. The event carries only `documentKey._id` (pre-images only if they were enabled on the collection). The Silver table has to delete (or soft-delete / mark `deleted_at`) the row with that `_id`, which means Silver must be keyed by `_id`.
3. **`publish.full.document.only=true`.** It publishes only the current document, but a delete has no document, so the delete is dropped and silently vanishes downstream. `publish.full.document.only.tombstone.on.delete=true` publishes a tombstone instead: key = the document's `_id`, value = `null`. A MERGE in the sink then deletes the row.
4. **Token older than the oplog window.** That is the row "Connector down longer than the oplog window". The connector reports an invalid resume token and stops. You restart it with a new `offset.partition.name` and `startup.mode=copy_existing` to re-snapshot, and investigate the gap. (Heartbeats prevent the quiet-collection variant.)
5. **Checklist.** Open question, graded on the reasoning. A strong answer picks one item and ties it to a concrete risk, e.g. "decide how deletes arrive on day one, because with full-document-only deletes vanish silently and nobody notices until the numbers are wrong", or "the oplog window, because a long weekend outage would otherwise force a full re-snapshot".

---

## Optional connector questions - answers

1. `"change.stream.full.document": "updateLookup"`. The bookmark (resume token) is stored in Kafka Connect's offsets.
2. The delete is dropped (no document to publish). `publish.full.document.only.tombstone.on.delete=true` turns it into a tombstone.
3. Ctrl+C + restart = "Connect worker restarts" (resume from the saved token, maybe a few duplicates). Stopped longer than the oplog window = "Connector down longer than the oplog window" (invalid resume token → re-snapshot).
