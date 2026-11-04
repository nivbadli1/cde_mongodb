# MongoDB Cheat Sheet — SQL ↔ MongoDB
**Naya College · Big Data Engineering**

> All examples use `db.orders` in the `shop` database. Open the shell with `docker exec -it mongo mongosh`, then `use shop`.

---

## 1. Concepts

| SQL | MongoDB |
| --- | --- |
| database | database |
| table | collection |
| row | document (BSON) |
| column | field (can be nested) |
| primary key | `_id` (auto-generated `ObjectId`) |
| foreign key | reference (a field holding another document's `_id`, not enforced) |
| JOIN | embed (document inside a document) or `$lookup` |
| `ALTER TABLE` | none — there is no fixed schema |

---

## 2. CRUD

| Action | SQL | MongoDB |
| --- | --- | --- |
| Insert | `INSERT INTO orders VALUES (...)` | `db.orders.insertOne({ order_id: "ORD-1", status: "created" })` |
| Insert many | `INSERT ... VALUES (...), (...)` | `db.orders.insertMany([{...}, {...}])` |
| One row | `SELECT * FROM orders LIMIT 1` | `db.orders.findOne()` |
| Filter | `SELECT * FROM orders WHERE status = 'paid'` | `db.orders.find({ status: "paid" })` |
| Columns | `SELECT order_id, total FROM orders` | `db.orders.find({}, { _id: 0, order_id: 1, total: 1 })` |
| Sort & limit | `ORDER BY created_at DESC LIMIT 5` | `.sort({ created_at: -1 }).limit(5)` |
| Count | `SELECT COUNT(*) FROM orders WHERE ...` | `db.orders.countDocuments({ status: "paid" })` |
| Distinct | `SELECT DISTINCT status FROM orders` | `db.orders.distinct("status")` |
| Update one | `UPDATE orders SET status='paid' WHERE order_id='ORD-1'` | `db.orders.updateOne({ order_id: "ORD-1" }, { $set: { status: "paid" } })` |
| Update many | `UPDATE orders SET ... WHERE ...` | `db.orders.updateMany({ ... }, { $set: { ... } })` |
| Upsert | `INSERT ... ON CONFLICT DO UPDATE` / `MERGE` | `db.orders.updateOne({ order_id: "ORD-2" }, { $set: {...} }, { upsert: true })` |
| Delete | `DELETE FROM orders WHERE order_id='ORD-1'` | `db.orders.deleteOne({ order_id: "ORD-1" })` |
| Delete all | `TRUNCATE orders` | `db.orders.deleteMany({})` ⚠️ no "are you sure?" |
| Drop table | `DROP TABLE orders` | `db.orders.drop()` |

**Watch out:**
- `"shipping.address.city"` = dot notation for a nested field. Quotes are required.
- In a projection, `1` = include the field, `0` = exclude it. In `sort`, `1` = ASC, `-1` = DESC.
- **`updateOne` without `$set` replaces the whole document!**

---

## 3. Comparison operators (in filters)

| MongoDB | SQL | Example |
| --- | --- | --- |
| `$eq` / `$ne` | `=` / `<>` | `{ status: { $ne: "cancelled" } }` |
| `$gt` / `$gte` | `>` / `>=` | `{ total: { $gte: 1000 } }` |
| `$lt` / `$lte` | `<` / `<=` | `{ total: { $lt: 100 } }` |
| `$in` / `$nin` | `IN` / `NOT IN` | `{ status: { $in: ["paid", "shipped"] } }` |
| `$exists` | roughly `IS NOT NULL` / `IS NULL` (precisely: field present or not) | `{ coupon: { $exists: false } }` |
| `$type` | no SQL equivalent: "the field is of type X" | `{ total: { $type: "string" } }` |
| `$regex` | `LIKE`, but with a regular expression | `{ "customer.name": { $regex: "^Noa" } }` |
| `$and` / `$or` | `AND` / `OR` | `{ $or: [{ status: "paid" }, { total: { $gt: 500 } }] }` |
| `$size` | no SQL equivalent: array length | `{ items: { $size: 0 } }` |

Several conditions in the same object = implicit **AND**: `{ status: "paid", total: { $gt: 100 } }`.

⚠️ **Trap:** MongoDB never compares a string to a number. `{ total: { $gte: 1000 } }` silently skips orders whose total is stored as `"1200.00"`.

---

## 4. Update operators

| Operator | What it does | Example |
| --- | --- | --- |
| `$set` | Changes or adds a field (`SET`) | `{ $set: { status: "paid" } }` |
| `$unset` | Removes a field from the document | `{ $unset: { coupon: "" } }` |
| `$inc` | Adds to a number | `{ $inc: { qty: 1 } }` → `qty = qty + 1` |
| `$currentDate` | Current date (`NOW()`) | `{ $currentDate: { updated_at: true } }` |
| `$push` | Appends an element to an array | `{ $push: { tags: "vip" } }` |
| `$pull` | Removes an element from an array | `{ $pull: { tags: "sale" } }` |
| `$addToSet` | Adds to an array only if not already there | like a Python `set` |
| `$rename` | Renames a field | `{ $rename: { "email": "contact.email" } }` |
| `$setOnInsert` | Set only when an upsert creates a new document | `{ $setOnInsert: { created_at: new Date() } }` |

**Update using the current value (pipeline update):** wrap it in `[ ]`; then `"$field"` = the field's value.
```javascript
// UPDATE orders SET status = LOWER(status) WHERE status IS NOT NULL
db.orders.updateMany({ status: { $exists: true } },
                     [{ $set: { status: { $toLower: "$status" } } }])
```

---

## 5. Aggregation — basic stages

`db.orders.aggregate([ stage1, stage2, ... ])` — each stage receives the output of the previous one.

| Stage | SQL | Example |
| --- | --- | --- |
| `$match` | `WHERE` | `{ $match: { status: "paid" } }` |
| `$group` | `GROUP BY` | `{ $group: { _id: "$status", n: { $sum: 1 } } }` |
| `$sum: 1` | `COUNT(*)` | inside `$group` |
| `$sum: "$total"` | `SUM(total)` | inside `$group` |
| `$avg` / `$min` / `$max` | `AVG` / `MIN` / `MAX` | `{ avg: { $avg: "$total" } }` |
| `$project` | `SELECT` + aliases | `{ $project: { _id: 0, city: "$_id", n: 1 } }` |
| `$sort` / `$limit` | `ORDER BY` / `LIMIT` | `{ $sort: { n: -1 } }, { $limit: 3 }` |
| `$unwind` | `explode()` in Spark | `{ $unwind: "$items" }` |
| `$lookup` | `LEFT JOIN` | `{ $lookup: { from: "customers", localField: "customer.customer_id", foreignField: "_id", as: "c" } }` |

**Two rules:**
- **`_id` inside `$group`** = the grouping key ("group by what"), not a document's id.
- **`"$status"` with `$`** = the field's value. **`"status"` without `$`** = just the text "status".

---

## 6. Useful commands

| Command | What it does |
| --- | --- |
| `show dbs` / `show collections` | `SHOW DATABASES` / `SHOW TABLES` |
| `db.orders.estimatedDocumentCount()` | Fast count from metadata |
| `db.orders.aggregate([{ $sample: { size: 3 } }])` | 3 random documents |
| `db.orders.getIndexes()` | List indexes |
| `db.orders.find({...}).explain("executionStats")` | `EXPLAIN ANALYZE` |
| `rs.status()` | Replica set status (who is PRIMARY) |
