# MongoDB as a Source System — Lecture Deck Content
**Naya College · Big Data Engineering · Big Data Services module**
Instructor source for the live deck (Claude Slides artifact, Naya template). **44 slides** · ~150 min lecture (+60 min practice, +30 min break, not included).

> **Numbering.** This file now uses the numbering of the **live deck (44 slides)**. The first version of this file had 42 slides; see "What changed" below if you have old notes or an old PDF.

---

## Read me first (for the instructor)

**Assumed versions (state these to the class once, on slide 1 or 18)**

| Component | Version assumed | Note |
|---|---|---|
| MongoDB server | **8.0** (`mongo:8.0` image) | All code also valid on 7.0 and on 9.0 (GA since 29 Sep 2026 [S24]) |
| mongosh | the one bundled in the `mongo:8.0` image | Run via `docker exec -it mongo mongosh` |
| PyMongo | **4.18+** (4.18.3 in dev_env, Python 3.10) | 4.19.0 needs Python 3.11+, so the lab pins 4.18.3 |
| Python | 3.10+ | Tested 3.13 |
| MongoDB Kafka Connector | **3.1.2** (latest GitHub release) | Concept level only in this lesson [S17] |

**What changed vs. the first version (old → new slide numbers)**

| Change | Detail |
|---|---|
| **NEW slide 4** | Schema on Write vs Schema on Read (+ BSON/Bronze/Silver link) |
| **Slide 8 split** | Old slide 8 (two companies) → **slide 8 Toyota Connected** + **slide 9 Forbes**, one company per slide like the Kafka lessons (Netflix / Uber) |
| Old slides 9–40 | Shift **+1** (old 9 → 10 … old 40 → 41) |
| Old slide 41 (Hello Heart placeholder) | Replaced by **slide 42: Source-Side Checklist** (generic, no company details) |
| Old slide 42 (summary) | Now **slide 43** |
| Old slide 4 (vocabulary map) | Moved to the **end as slide 44**, a reference / take-home cheat sheet (0 min in the lecture) |

**Testing status.** No MongoDB server was reachable from the environment this was written in. The practice dataset generator was run, and the expected outputs in Appendix B were computed from that exact deterministic data (seed 42) and cross-checked against an in-memory MongoDB emulator for the queries it supports. The compose file in Appendix A (mongo + dev_env) is **untested**. **Run Appendix A + B once before class.**

**Source tags.** `[S#]` = source in Appendix C. `[UNVERIFIED]` = I could not confirm it from a source; check or drop. Company case studies (Toyota Connected, Forbes) are vendor / company-reported: say so out loud.

**Timing per part:** P1 26.5 · P2 30 · P3 20 · P4 15 · P5 10 · P6 20 · P7 20 · P8 10 = **~151.5 min** (trim with the cut list at the end).

**Slide → practice map (new numbering).** Setup: 30–31 · Step 1 Explore: 4, 11, 15, 22, 26 · Step 2 CRUD: 18–21 · Step 3 Aggregations: 23–26 · Step 4 Index/explain: 27–29 · Step 5 Change stream: 35–38 · Wrap-up: 15, 40, 42 · Optional: 39–41. If the GitHub repo's `lab/handout.md` groups the steps differently (e.g. Part A mongosh / Part B Python), the slide numbers stay the same.

---

# PART 1 — Why MongoDB? (26.5 min)

---

### Slide 1 — MongoDB as a Source System
**Part:** 1 · **Minutes:** 2 · **Type:** title

**On-slide content**
- Title: *MongoDB — The Source Side of the Pipeline*
- Subtitle: Big Data Engineering · Naya College
- Learning goals (4):
  1. Explain where MongoDB sits in a data platform
  2. Explore an unknown collection and spot schema problems
  3. Query and aggregate with SQL-equivalent thinking
  4. Explain how Change Streams + Kafka move data out

**Speaker notes**
Today we are not learning MongoDB to become MongoDB admins or to run analytics on it. We're learning it the way a data engineer meets it on day one: someone says "the app data is in Mongo, get it into the warehouse." By the end of today you should be able to open a collection you've never seen, tell me what's wrong with it before it breaks your pipeline, and explain how a change in the app turns into a row in Snowflake. Quick show of hands: who has ever had to load JSON into a SQL table? Keep that pain in mind, it's the theme of the day.

---

### Slide 2 — Where MongoDB Sits in the Data Platform
**Part:** 1 · **Minutes:** 3 · **Type:** diagram

**On-slide content**
- Recap from the Kafka lessons: producers → topics → consumers / sink connectors
- Today we zoom into the **left edge**: the operational database
- MongoDB = system of record for the **app**, not for analytics
- Our job: get changes **out**, reliably, without hurting the app

**Diagram description**
Left-to-right flow, five boxes:
1. `Mobile / Web App` (icon: phone)
2. `MongoDB` — **highlighted** (brand green outline, label "TODAY")
3. `Kafka` — drawn as a cylinder with 3 stacked topic bars, label "from Kafka lessons" (greyed)
4. `Stream / Sink layer` (greyed)
5. `Warehouse / Lakehouse` (Snowflake / Iceberg, greyed)
Arrows: 1→2 "writes (OLTP)", 2→3 "source connector (?)" with a big question mark, 3→4→5 solid grey.
Below the flow, a thin bracket under boxes 1–2 labelled "Operational world", under 3–5 labelled "Analytical world".

**Speaker notes**
Remember the Netflix and Uber stories from the Kafka lessons: events flowing through topics into consumers. Today's question is where those events come from when the source is a database, not a producer you control. The arrow with the question mark is the whole lecture. Think of MongoDB as the kitchen of a restaurant: it's built to cook orders fast, not to do the monthly accounting. Who here has ever run a heavy report on a production database and gotten a call from a developer? That's why we move the data out.

---

### Slide 3 — Document Model vs Tables
**Part:** 1 · **Minutes:** 3 · **Type:** comparison-table

**On-slide content**
Left: one order as **3 SQL tables** (orders, order_items, customers). Right: the same order as **one document**.

```json
{
  "_id": ObjectId("6a88a5940000000000000000"),
  "order_id": "ORD-10000",
  "customer": { "customer_id": "C0008", "name": "Noa Avraham",
                "contact": { "email": "noa.avraham8@example.com" } },
  "items": [ { "sku": "SKU-104", "name": "Headphones", "qty": 1, "unit_price": 499.0 } ],
  "total": NumberDecimal("499.00"),
  "status": "paid"
}
```

**Diagram description**
Left half: three small table grids `orders(order_id, customer_id, total, status)`, `order_items(order_id, sku, qty, unit_price)`, `customers(customer_id, name, email)` with FK arrows `order_items.order_id → orders`, `orders.customer_id → customers`. Right half: the JSON block above inside a single rounded "document" card. A large "=" sign between halves.

**Speaker notes**
In SQL you split the order across three tables and JOIN it back every time you read it. In MongoDB the app stores the order the way it thinks about it: one object, with the items nested inside. Analogy: SQL is a filing cabinet where the invoice, the line items and the customer card sit in different drawers; MongoDB staples them together into one folder. Reading one order is fast and simple. But ask yourself: what happens when an analyst wants "revenue per SKU across all orders"? That's where our work starts.

---

### Slide 4 — Schema on Write vs Schema on Read  *(NEW)*
**Part:** 1 · **Minutes:** 3 · **Type:** comparison-table

**On-slide content**

| | Schema on write | Schema on read |
|---|---|---|
| **Defined** | In the database (`CREATE TABLE`) | In the code that reads it |
| **Checked** | On every `INSERT` | When someone reads the data |
| **Bad data** | Rejected with an error | Accepted, stored silently |
| **New shape** | `ALTER TABLE` / migration | Just write the new shape |
| **Examples** | PostgreSQL, Snowflake Silver | MongoDB, JSON files, Bronze |

Callout: **Bronze** = schema on read: keep everything as it came. **Silver** = schema on write: enforce names and types. MongoDB does not enforce for you, so **your pipeline must**.

**Speaker notes**
You already know schema on write from SQL: you define the table first, and the database rejects anything that doesn't fit. Try to insert the text "499.00" into a DECIMAL column and you get an error right at the source. MongoDB works the opposite way, schema on read: the database stores whatever the app sends, and the structure is only interpreted by whoever reads it later. Analogy: SQL is a security guard at the door checking every ID; MongoDB lets everyone in and the problems show up inside the building, which for us means in Snowflake. This connects to the medallion layers you already know: Bronze is schema on read, we keep the raw data exactly as it arrived; Silver is schema on write, where we enforce names and types. One more point we'll see on slide 11: MongoDB stores BSON, a binary JSON with extra types like ObjectId, Decimal128 and Date, and that is exactly where the type problems come from. Question to the class: in your current job, where is the schema enforced, in the database or in the code?

---

### Slide 5 — When MongoDB Shines
**Part:** 1 · **Minutes:** 2.5 · **Type:** concept

**On-slide content**
- Entities read and written **as a whole** (order, profile, device state)
- Structure that **evolves fast** with app releases
- **Polymorphic** records (different product types, different fields)
- High write volume with **horizontal scaling** (sharding)

**Speaker notes**
MongoDB is a great fit when the app reads and writes one "thing" at a time: a user profile, a shopping cart, a device's last reported state. It also fits teams that ship weekly and change the data shape often, because nobody has to run a migration first. Analogy: it's like a backpack with flexible pockets versus a toolbox with fixed slots. Can you think of a system at your current job where every record looks a little different? That's a typical Mongo candidate.

---

### Slide 6 — When NOT to Use MongoDB
**Part:** 1 · **Minutes:** 2.5 · **Type:** concept

**On-slide content**
- **Analytics** over the whole dataset (scans, big GROUP BYs) → warehouse
- Highly **relational** data with many-to-many JOINs → PostgreSQL
- **Full-text / log search** at scale → Elasticsearch
- Pure key lookups / caching at micro-second latency → Redis

**Speaker notes**
This is the most important slide for data engineers. MongoDB *can* run aggregations, and you'll see we use them for exploration and data quality checks. But a full-collection GROUP BY on the production cluster competes with the app for the same CPU and memory. That's exactly why the pattern is "copy the data out and analyze elsewhere." Question: if the product team asks you for a daily revenue dashboard, where should that query run? (Answer: not on the app's primary.)

---

### Slide 7 — MongoDB vs the Neighbours
**Part:** 1 · **Minutes:** 4 · **Type:** comparison-table

**On-slide content**

| | Data model | Consistency (default) | Query power | Scaling | Best fit |
|---|---|---|---|---|---|
| **MongoDB** | Documents (BSON) | Writes default to `w:"majority"` since 5.0 [S15] | Rich filters, aggregation, secondary indexes | Replica sets + native sharding | App data with evolving JSON entities |
| **PostgreSQL** | Relational tables | ACID; replication sync or async by choice [S14] | Full SQL, JOINs | Vertical + read replicas [S14]; sharding via extensions [UNVERIFIED] | Relational OLTP |
| **Cassandra** | Wide-column | Tunable per query; driver default `ONE` [S10] | CQL by partition key; no JOINs [UNVERIFIED] | Masterless, linear write scaling [UNVERIFIED] | Huge write-heavy time series |
| **DynamoDB** | Key-value / document | Eventually consistent reads by default; strong reads opt-in [S11] | Key + index access | Fully managed partitioning [UNVERIFIED] | Serverless key access on AWS |
| **Redis** | In-memory key-value / data structures | Async replication by default [S12] | Key operations | Cluster mode [UNVERIFIED] | Cache, sessions, counters |
| **Elasticsearch** | Inverted index over JSON | Near real-time: searchable within ~1 s refresh [S13] | Full-text + aggregations | Shards + replicas [UNVERIFIED] | Search, logs (your ELK lessons) |

**Speaker notes**
Don't memorize this table; read it as "which tool for which job." Notice the consistency column: almost everyone except PostgreSQL makes you choose between speed and freshness, and the defaults differ. Cassandra lets each query pick how many replicas must answer, DynamoDB reads are eventually consistent unless you ask for strong reads, and Elasticsearch documents become searchable after a refresh, about a second. For us the key point: MongoDB sits in the "operational app database" box, Elasticsearch is the one you'll meet again in the ELK lessons. Question: which of these would you choose for a leaderboard that updates every second?

**Designer note:** 6×6 table, MongoDB row highlighted. Put the [S#] tags in a footer line, not in cells, if space is tight.

---

### Slide 8 — Real-World Use Cases: Toyota Connected  *(was half of old slide 8)*
**Part:** 1 · **Minutes:** 2 · **Type:** use-case

**On-slide content** (simple bullets + dark logo-style box "TOYOTA CONNECTED", like the Kafka Netflix/Uber slides)
- **Toyota Connected** builds the platform behind **Toyota Safety Connect**: crash notification and emergency help [S1][S2]
- **Problem:** the legacy database had reliability issues, and a crash alert cannot wait for a fix [S1][S2]
- **Why MongoDB:** target of **99.99% availability**, upgrades without downtime (multi-region), developers create collections without a DBA [S1][S4]
- **Architecture:** AWS microservices over **20+ MongoDB Atlas databases**, 9M+ vehicles, data reaches safety agents in ~3 seconds [S2][S3][S4]

Callout: **Not chosen:** staying on the legacy database. These are company and vendor case studies: marketing with real facts inside. *(The legacy product Toyota replaced is not named publicly [UNVERIFIED].)*

**Speaker notes**
In the Kafka lessons you saw Netflix and Uber, companies that move events. Now the other side: companies whose application data lives in MongoDB. Toyota Connected runs the platform behind Toyota's emergency services. A crash notification can't wait for a maintenance window, so availability drove the decision: they moved off a legacy database with reliability problems to MongoDB Atlas, spread over more than 20 databases behind AWS microservices, serving over nine million vehicles, with data reaching the safety agents in about three seconds. Honest caveat: MongoDB's own material says 99.99% availability, while one interview quote says 99%, so treat vendor case studies as marketing with real facts inside. Question: this app data lives in MongoDB, so who consumes it for analytics, and how does it get there? That is the rest of today.

---

### Slide 9 — Real-World Use Cases: Forbes  *(NEW, split from old slide 8)*
**Part:** 1 · **Minutes:** 2 · **Type:** use-case

**On-slide content** (simple bullets + dark logo-style box "FORBES")
- **Forbes** moved its digital platform to **MongoDB Atlas on Google Cloud** (migration took ~6 months, done late 2019) [S5][S6]
- **Problem:** a self-managed, on-prem setup slowed releases; provisioning and maintenance were a burden [S5][S7]
- **Why MongoDB:** managed service, easy replication and provisioning, flexible documents behind a stable API [S5][S7]
- **Reported results:** 58% faster builds, 2×–10× faster release cycles, 25% lower total cost [S5]

Callout: **Not chosen:** keeping self-managed on-prem MongoDB. Next step: replace Solr with Atlas Search [S7]. Results are company-reported.

**Speaker notes**
Same side of the story, a different industry. Forbes is a media company: its articles and product data change shape often, and the self-managed on-prem setup slowed the engineering teams down. They moved to MongoDB Atlas on Google Cloud, with microservices and an API layer on top of the documents. Notice that last part: a stable API in front of flexible documents. That is a hint of the schema drift problem we will meet in Part 2, because the app team hides the flexibility behind the API, but a data pipeline reading straight from the database does not get that protection. The numbers on the slide (58% faster builds, 2 to 10 times faster releases, 25% lower total cost) come from MongoDB's own write-up, so present them as reported, not measured by us. Question: who in a company like this consumes the data for analytics, and where does it have to land?

*Sources: S5 (MongoDB blog), S6 (Google Cloud blog), S7 (MongoDB case study).*

---

### Slide 10 — The Modern Architecture: App → MongoDB → CDC → Kafka → Lakehouse
**Part:** 1 · **Minutes:** 2.5 · **Type:** diagram

**On-slide content**
- **Then:** batch jobs push data *into* MongoDB (eBay 2012: daily bulk load from Hadoop [S8])
- **Now:** MongoDB is the **source**; changes stream *out* via CDC
- Oplog → Change Streams → Kafka source connector → topics → Bronze/Silver/Gold
- No nightly dumps, no queries against the app's primary

**Diagram description**
Top strip, small and greyed with a red diagonal "OUTDATED" stamp: `Hadoop (batch)` → `MongoDB` labelled "daily bulk load", plus a `Storm` box beside it.
Main diagram, left to right:
1. `App` → (writes) →
2. `MongoDB Replica Set` (3 stacked nodes, the top labelled PRIMARY) with a small scroll icon inside labelled `oplog`
3. Arrow labelled `Change Stream (CDC)` →
4. `Kafka Connect: MongoDB Source Connector` (gear icon) →
5. `Kafka topic: shop.orders` (cylinder) →
6. `Sink / Spark job` →
7. Three stacked layers: `Bronze (raw JSON, Iceberg)`, `Silver (flattened, typed)`, `Gold (business tables, Snowflake)`.
Under arrows 3–5, a small callout: "resume token stored in Connect offsets".

**Speaker notes**
Older slides you'll find online show MongoDB next to Hadoop and Storm, with data loaded into Mongo in batches; eBay's 2012 search-suggestion setup literally bulk-loaded MongoDB from Hadoop once a day. Today the arrow points the other way: MongoDB is where the truth is born, and we capture every change as it happens. Analogy: instead of photocopying the whole notebook every night, we read the notebook's change log line by line. Every box on this diagram gets its own part of today's lecture, and the oplog box is the one that makes everything else possible. Keep this picture; we'll come back to it at slide 39.

---

# PART 2 — Data Modeling (30 min)

---

### Slide 11 — BSON and Data Types
**Part:** 2 · **Minutes:** 5 · **Type:** comparison-table

**On-slide content**

| BSON type | Looks like | What breaks downstream |
|---|---|---|
| `ObjectId` | `ObjectId("6a88a594…")` | Arrives as `{"$oid": "…"}` in JSON; 12 bytes, first 4 = creation time |
| `Decimal128` | `NumberDecimal("499.00")` | Arrives as `{"$numberDecimal": "499.00"}` — a **string** inside an object, not a number |
| `Date` | `ISODate("2026-08-21T19:23:00Z")` | Arrives as `{"$date": …}`; UTC milliseconds — timezone assumptions break |
| `Int32 / Int64 / Double` | `1`, `NumberLong(1)`, `1.0` | Same field, three numeric types → Spark infers `string` or fails |

**Code (mongosh)**
```javascript
// Same value, different BSON types — all legal in ONE collection
db.types_demo.insertMany([
  { price: 499 },                       // Int32
  { price: 499.0 },                     // Double
  { price: NumberDecimal("499.00") },   // Decimal128
  { price: "499.00" }                   // String
]);
// Ask MongoDB which type each document really holds
db.types_demo.aggregate([{ $project: { _id: 0, price: 1, t: { $type: "$price" } } }]);
// → int, double, decimal, string
```

**Speaker notes**
BSON is binary JSON with extra types that plain JSON doesn't have, and that is exactly where pipelines get hurt. When the connector serializes a document to JSON, a Decimal128 price becomes an object containing a string, and your Snowflake column suddenly receives `{"$numberDecimal":"499.00"}` instead of 499. Analogy: it's like receiving a bank transfer in a currency your accounting system doesn't recognize; the money is there, but you can't add it up until you convert it. Question: in SQL, could the same column hold an integer in one row and a string in another? In MongoDB it can, and it's the most common bug we'll hunt today.

---

### Slide 12 — Collections and Documents
**Part:** 2 · **Minutes:** 3 · **Type:** concept

**On-slide content**
- Collection = group of documents, **no enforced columns**
- Every document has a unique `_id` (your downstream MERGE key)
- Max document size **16 MB**; nesting allowed, arrays allowed
- Created **implicitly** on first insert — typos create new collections

**Code (mongosh)**
```javascript
use shop                          // switches DB; created lazily on first write
db.oders.insertOne({ x: 1 })      // typo → a NEW collection "oders" now exists
show collections                  // orders, oders
db.oders.drop()                   // clean up
```

**Speaker notes**
A collection is the closest thing to a table, but nothing forces its documents to share fields. There's no CREATE TABLE step: the first insert creates the database and the collection, which is convenient and also how typos turn into ghost collections. Downstream, every collection usually maps to one Kafka topic and one Bronze table, so a surprise collection can mean a surprise topic. Question: what's the equivalent risk in SQL? (You'd get an error "table does not exist" — MongoDB gives you silence instead.)

---

### Slide 13 — Embedding vs Referencing
**Part:** 2 · **Minutes:** 5 · **Type:** comparison-table

**On-slide content**

| | Embed (sub-document / array) | Reference (store the `_id`) |
|---|---|---|
| SQL analogy | Pre-joined, denormalized row | Foreign key |
| Read | One query, fast | Needs `$lookup` or 2 queries |
| Update | Duplicate data → update in many places | Update once |
| Growth | Unbounded arrays hit 16 MB | No size issue |
| **Pipeline impact** | Nested arrays → must explode/flatten; one change event = whole parent | Clean 1:1 tables, but joins move to the warehouse |

**Diagram description**
Two panels. Left "EMBED": one large card `order` containing three small stacked cards `item`. Right "REFERENCE": card `order { customer_id: "C0008" }` with a dashed arrow to a separate card `customer { _id: "C0008" }`.

**Speaker notes**
This is the core modeling decision in MongoDB, and the app team makes it for the app's reads, not for your warehouse. Embedding is like a pre-joined, denormalized table: great for showing an order page, awkward when an analyst wants one row per item. Referencing looks like a foreign key, so it feels familiar, but MongoDB doesn't enforce it, so orphans are possible. Rule of thumb: embed what you always read together and what stays small; reference what grows without limit or is shared. Question: our orders embed items — what happens to the change event size when one item's quantity changes?

---

### Slide 14 — Modeling by Access Patterns
**Part:** 2 · **Minutes:** 4 · **Type:** concept

**On-slide content**
- SQL: model the **data** first, write queries later
- MongoDB: list the **queries** first, shape documents to fit them
- Result: the schema reflects **the app's screens**, not business entities
- DE consequence: expect duplication, pre-computed fields, and odd shapes

**Diagram description**
Two vertical arrows side by side. Left arrow labelled "SQL" going `Entities → Normalized tables → Any query`. Right arrow labelled "MongoDB" going `App screens/queries → Document shape → Fast for those queries`.

**Speaker notes**
In SQL we normalize first and trust JOINs to answer any question later. MongoDB teams do the opposite: they write down "the order page needs X, the customer page needs Y" and shape documents to answer those in one read. That's why you'll find fields like `customer.name` copied into every order: it's not a bug, it's a design choice for speed. Analogy: SQL is a library sorted by subject; MongoDB is a desk arranged for one specific job. Question: when you load this into the warehouse, which copy of the customer's name is the "true" one?

---

### Slide 15 — Flexible Schema, Schema Drift and Its Cost
**Part:** 2 · **Minutes:** 5 · **Type:** concept

**On-slide content**
- No `ALTER TABLE` → app release **v2** just writes new shapes
- Our dataset: `customer.email` (v1) → `customer.contact.email` (v2)
- Pipeline symptoms: NULL spikes, new columns, type conflicts, failed loads
- Defense: detect drift (`$type`, `$exists`), track `schema_v`, contracts with app team

**Code (mongosh)**
```javascript
// Same business field, two locations, depending on when the order was written
db.orders.find({}, { _id: 0, schema_v: 1, "customer.email": 1, "customer.contact.email": 1 }).limit(3);
// How many orders use each shape?
db.orders.aggregate([{ $group: { _id: "$schema_v", n: { $sum: 1 } } }]);
// → { _id: 1, n: 107 }, { _id: 2, n: 93 }
```

**Speaker notes**
Flexible schema is a gift to developers and a bill sent to data engineers. On June 1st the app team moved email into a `contact` sub-document; nobody told the data team, because from their side nothing broke. Downstream, your Silver table's `email` column silently becomes NULL for every new order, and the marketing dashboard drops by half. Analogy: it's like a supplier changing the layout of their invoice without telling accounting. Question: in your current job, how would you find out a source changed shape — from monitoring or from an angry stakeholder?

---

### Slide 16 — Schema Validation with `$jsonSchema`
**Part:** 2 · **Minutes:** 4 · **Type:** code

**On-slide content**
```javascript
// Enforce a minimal contract on new writes (MongoDB 7.0+)
db.runCommand({
  collMod: "orders",
  validator: {
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
  },
  validationLevel: "moderate",  // existing invalid docs are not re-checked on unrelated updates
  validationAction: "error"     // "warn" = log only, good first step
});
// Try a bad write:
db.orders.insertOne({ order_id: "ORD-X", status: "SHIPPED", created_at: new Date(), total: "10" });
// → MongoServerError: Document failed validation
```

**Speaker notes**
This is the closest MongoDB gets to a CREATE TABLE with constraints, and it's opt-in. It is also the "schema on write" option from slide 4, added after the fact. Validation only applies to writes from now on; the 200 messy documents already in the collection stay messy, which is why `validationLevel: "moderate"` exists. A good migration path is `validationAction: "warn"` first, watch the logs, then switch to error. As a data engineer, your role here is to *ask* the app team for this contract on the fields your pipeline depends on. MongoDB 9.0 also adds a new validation level called `constraint` [S25] — check the 9.0 docs before using it. Question: which fields from our orders collection would you insist on, and which would you leave flexible?

---

### Slide 17 — Nested Documents and Arrays in Pipelines
**Part:** 2 · **Minutes:** 4 · **Type:** diagram
*(Planned cut — keep for reference)*

**On-slide content**
- Nested object → dot-notation columns: `shipping.address.city`
- Array of objects → **explode** to a child table (one row per item)
- Array of scalars (`tags`) → array column or bridge table
- Keep `_id` + array index as the child key

**Diagram description**
Left: one order card with `items: [A, B, C]`. Arrow labelled `$unwind / explode()`. Right: a 3-row table `order_items(order_id, item_idx, sku, qty)` with rows A, B, C, each highlighted with the same order_id.

**Code (PySpark, for reference)**
```python
from pyspark.sql import functions as F
items = (orders_df
         .select("_id", "order_id", F.posexplode_outer("items").alias("item_idx", "item"))
         .select("order_id", "item_idx", "item.sku", F.col("item.qty").cast("int").alias("qty")))
```

**Speaker notes**
Analysts want flat tables; MongoDB gives you trees. The standard Silver-layer move is: nested objects become dot-named columns, arrays of objects become child tables, exactly like normalizing in reverse. Use `explode_outer` not `explode`, otherwise orders with an empty items array silently disappear — and our dataset has 40 of them. Question: if the order has 3 items and one item changes, do you rewrite one child row or all three?

---

# PART 3 — CRUD and Administrative Commands (20 min)

---

### Slide 18 — Insert and Find
**Part:** 3 · **Minutes:** 4 · **Type:** code

**On-slide content**
```javascript
// mongosh (MongoDB 8.0) — connect: docker exec -it mongo mongosh
use shop

// INSERT INTO orders VALUES (...)
db.orders.insertOne({
  order_id: "ORD-99999",
  customer: { customer_id: "C0999", name: "Test Student" },
  items: [{ sku: "SKU-101", name: "Yoga Mat", qty: 1, unit_price: 89.9 }],
  total: NumberDecimal("89.90"),
  status: "created",
  created_at: new Date()
});

// SELECT * FROM orders LIMIT 1
db.orders.findOne();

// SELECT * FROM orders WHERE order_id = 'ORD-99999'
db.orders.find({ order_id: "ORD-99999" });
```

**Speaker notes**
Everything in mongosh is JavaScript, and every query is a document describing what you want. `insertOne` returns the generated `_id`, which is an ObjectId whose first 4 bytes are a timestamp, so it roughly sorts by creation time. `find` returns a cursor, not an array; mongosh just prints the first 20 for you. Question: in SQL, inserting a row with a column that doesn't exist fails; what do you think happens here if I add a field `gift_note`?

---

### Slide 19 — Filters, Projection, Sort, Limit
**Part:** 3 · **Minutes:** 4 · **Type:** code

**On-slide content**
```javascript
// SELECT order_id, total FROM orders
// WHERE shipping.address.city = 'Haifa' AND status IN ('shipped','delivered')
// ORDER BY created_at DESC LIMIT 5
db.orders.find(
  { "shipping.address.city": "Haifa", status: { $in: ["shipped", "delivered"] } },  // WHERE
  { _id: 0, order_id: 1, total: 1, status: 1 }                                       // SELECT
).sort({ created_at: -1 }).limit(5);                                                 // ORDER BY, LIMIT

// Operators: $eq $ne $gt $gte $lt $lte $in $nin $exists $type $regex
db.orders.countDocuments({ total: { $gte: 1000 } });     // → 75
db.orders.countDocuments({ total: { $type: "string" } }); // → 19  (excluded above!)
```

**Speaker notes**
The first argument of `find` is your WHERE, the second is your SELECT list, and `sort` and `limit` read just like SQL. Dot notation reaches into nested documents, which is how you'll query most real collections. Now the trap: `total >= 1000` returns 75, but 19 orders store total as a string, and MongoDB never compares strings to numbers, so those orders are silently left out. Analogy: it's a filter that skips anything written in the wrong currency without telling you. Question: how many of those 19 do you think are actually over 1000? (In our data, 7.)

---

### Slide 20 — Update Operators and Upsert
**Part:** 3 · **Minutes:** 5 · **Type:** code

**On-slide content**
```javascript
// UPDATE orders SET status='paid', updated_at=NOW() WHERE order_id='ORD-99999'
db.orders.updateOne(
  { order_id: "ORD-99999" },
  { $set: { status: "paid" }, $currentDate: { updated_at: true } }
);

// Other operators: $inc  $unset  $push  $pull  $addToSet  $rename
db.orders.updateOne({ order_id: "ORD-99999" },
                    { $push: { items: { sku: "SKU-102", qty: 2, unit_price: 39.9 } } });

// Pipeline update = UPDATE ... SET status = LOWER(status)
db.orders.updateMany({ status: { $exists: true } },
                     [{ $set: { status: { $toLower: "$status" } } }]);   // modifiedCount: 30

// UPSERT = INSERT ... ON CONFLICT (order_id) DO UPDATE
db.orders.updateOne(
  { order_id: "ORD-77777" },
  { $set: { status: "created" }, $setOnInsert: { created_at: new Date() } },
  { upsert: true }
);
```

**Speaker notes**
Updates use operators: `$set` changes fields, `$inc` adds to numbers, `$push` appends to arrays, and you can also pass an aggregation pipeline for computed updates like lower-casing. Upsert is MongoDB's INSERT ... ON CONFLICT: update if it exists, insert if it doesn't, with `$setOnInsert` for fields that should only be set on creation. Here's the data-engineering link: every one of these updates becomes a change event, and by default that event carries only the changed fields, not the whole document. Question: if the event only says "status changed to paid", what does your Silver table need to already have?

---

### Slide 21 — Delete
**Part:** 3 · **Minutes:** 2 · **Type:** code

**On-slide content**
```javascript
// DELETE FROM orders WHERE order_id = 'ORD-77777'
db.orders.deleteOne({ order_id: "ORD-77777" });

// DELETE FROM orders WHERE order_id IN (...)
db.orders.deleteMany({ order_id: { $in: ["ORD-99999", "ORD-77777"] } });

// TRUNCATE (keeps indexes)            DROP TABLE (removes everything)
db.orders.deleteMany({});              // db.orders.drop();
```
- Hard deletes leave **no trace in the collection** — only in the oplog
- Many teams prefer **soft delete**: `$set: { deleted_at: new Date() }`

**Speaker notes**
Deletes mirror SQL closely; the gotcha is that `deleteMany({})` with an empty filter deletes everything, there's no "are you sure". For pipelines, hard deletes are the hardest event to capture: the document is gone, and the delete event carries only its `_id`. That's why many teams use soft deletes, a `deleted_at` field, which turns a delete into a normal update. Question: if you only run a nightly full dump, can you ever know that an order was deleted?

---

### Slide 22 — Exploring an Unknown Collection
**Part:** 3 · **Minutes:** 5 · **Type:** code

**On-slide content**
```javascript
use shop
db.getCollectionNames();                       // SHOW TABLES
db.runCommand({ listCollections: 1, nameOnly: true });

db.orders.estimatedDocumentCount();            // fast, from metadata
db.orders.countDocuments({});                  // exact: 200

db.orders.distinct("status");                  // SELECT DISTINCT status (14 variants before cleanup!)
db.orders.aggregate([{ $sample: { size: 3 } }]); // random rows, not just the oldest

// Size & storage — the "how big is this?" check before a full export
db.orders.aggregate([{ $collStats: { storageStats: {} } }]);
db.orders.getIndexes();
```

**Speaker notes**
This is your first-five-minutes checklist whenever someone hands you a collection. Use `$sample`, not `find().limit()`, because limit gives you the oldest documents and the drift usually lives in the newest ones. `distinct` on a categorical field is the fastest data-quality alarm you have: on our data it returns 14 status values where the business expects 5. `$collStats` tells you size and document count so you know whether an initial snapshot will take minutes or hours. Question: which one of these would you run first on a production cluster, and which would you avoid at peak hours?

---

# PART 4 — Aggregation Basics (15 min)

---

### Slide 23 — What Is a Pipeline
**Part:** 4 · **Minutes:** 3 · **Type:** diagram

**On-slide content**
- Documents flow through **stages**; each stage's output feeds the next
- Order matters: `$match` early = less work later
- Same idea as SQL clauses — but **you** choose the order
- Same idea as Spark transformations you'll write downstream

**Diagram description**
Horizontal pipe made of 4 segments: `$match` (funnel icon) → `$group` (stack icon) → `$sort` (arrows icon) → `$limit` (scissors icon). Above the pipe, 8 small document dots enter on the left; 5 remain after `$match`; 3 grouped dots after `$group`; 1 dot exits. Under each segment the SQL word in grey: `WHERE`, `GROUP BY`, `ORDER BY`, `LIMIT`.

**Speaker notes**
An aggregation pipeline is a conveyor belt: each station does one job and passes the result on. In SQL you write clauses in a fixed order and the optimizer decides how to execute; here you literally write the execution order, so putting `$match` first matters. If you've used Spark DataFrames, this will feel familiar: filter, groupBy, agg, orderBy. Question: what goes wrong if you put `$match` after `$group`?

---

### Slide 24 — `$match`, `$group`, `$project` vs SQL
**Part:** 4 · **Minutes:** 5 · **Type:** code

**On-slide content** (two columns)

**SQL**
```sql
SELECT LOWER(REPLACE(city,'-',' ')) AS city,
       COUNT(*)                     AS orders,
       SUM(CAST(total AS DECIMAL))  AS revenue
FROM   orders
WHERE  status <> 'cancelled'
GROUP  BY 1
ORDER  BY revenue DESC
LIMIT  3;
```

**MongoDB**
```javascript
db.orders.aggregate([
  { $match: { status: { $ne: "cancelled" } } },                       // WHERE
  { $group: {                                                         // GROUP BY
      _id: { $replaceAll: { input: { $toLower: "$shipping.address.city" },
                            find: "-", replacement: " " } },
      orders:  { $sum: 1 },                                           // COUNT(*)
      revenue: { $sum: { $convert: { input: "$total", to: "decimal",  // CAST
                                     onError: null, onNull: null } } } } },
  { $sort: { revenue: -1 } },                                         // ORDER BY
  { $limit: 3 },                                                      // LIMIT
  { $project: { _id: 0, city: "$_id", orders: 1, revenue: 1 } }       // SELECT alias
]);
```

**Speaker notes**
Put the two side by side and read them line by line; every SQL clause has a stage. `$group`'s `_id` is your GROUP BY key, and each other field is an aggregate like COUNT or SUM. Notice the `$convert`: without it, the 19 string totals would be skipped by `$sum`, the same silent-exclusion problem as before. Also notice "TLV" and "Beer Sheva" still don't merge with "tel aviv" and "be'er sheva" — normalization by rules only goes so far, which is why reference tables exist. Question: where would you rather fix city names, here or in the Silver layer?

---

### Slide 25 — `$unwind` and `$lookup`
**Part:** 4 · **Minutes:** 4 · **Type:** code

**On-slide content**
```javascript
// Top SKUs by quantity — "explode" the items array first
db.orders.aggregate([
  { $unwind: "$items" },                                  // one doc per array element
  { $group: { _id: "$items.sku",
              name: { $first: "$items.name" },
              qty:  { $sum: { $toInt: "$items.qty" } } } }, // qty is sometimes "2" (string)
  { $sort: { qty: -1 } }, { $limit: 3 }
]);
// → SKU-105 Backpack 100 · SKU-106 Sunglasses 98 · SKU-107 Bike Helmet 92

// LEFT JOIN customers c ON o.customer.customer_id = c._id
db.orders.aggregate([
  { $lookup: { from: "customers", localField: "customer.customer_id",
               foreignField: "_id", as: "customer_doc" } },
  { $limit: 1 }
]);
```

**Speaker notes**
`$unwind` is the MongoDB version of Spark's `explode`: an order with three items becomes three documents, each carrying the parent fields. Careful: by default `$unwind` drops documents whose array is empty or missing, just like an inner join; add `preserveNullAndEmptyArrays: true` to keep them. `$lookup` is a LEFT OUTER JOIN that puts the matches into an array field. It works, but heavy joins belong in the warehouse, not on the app's database. Question: why does `qty` need `$toInt` here?

---

### Slide 26 — Data Quality Checks with Aggregation
**Part:** 4 · **Minutes:** 3 · **Type:** code
*(Planned cut — keep for practice)*

**On-slide content**
```javascript
// 1. Type profile of a field  (SQL has no equivalent — columns have one type)
db.orders.aggregate([{ $group: { _id: { $type: "$total" }, n: { $sum: 1 } } }]);
// → decimal 115 · double 55 · string 19 · missing 11

// 2. Duplicate business keys  (GROUP BY order_id HAVING COUNT(*) > 1)
db.orders.aggregate([
  { $group: { _id: "$order_id", n: { $sum: 1 } } },
  { $match: { n: { $gt: 1 } } }
]);
// → ORD-10010 (2), ORD-10011 (2)

// 3. Missing required fields
db.orders.countDocuments({ status: { $exists: false } });   // → 7
```

**Speaker notes**
These three queries are a mini data-quality report you can run before you build anything. The `$type` profile is something SQL simply can't give you, because a SQL column has one type; here it's the first thing to check. Duplicate business keys are the classic HAVING COUNT(*) > 1, and in our data they come from an app retry bug. Question: which of these checks would you turn into an automated test in your pipeline?

---

# PART 5 — Indexes (10 min)

---

### Slide 27 — Why Indexes Matter
**Part:** 5 · **Minutes:** 3 · **Type:** concept

**On-slide content**
- Without an index: **COLLSCAN** — read every document
- With an index: **IXSCAN** — jump to matching keys (B-tree)
- Indexes cost RAM and slow writes; they serve the **app's** queries
- DE angle: an unindexed export query can hurt production

**Speaker notes**
Indexes work exactly like in SQL: a sorted structure that lets the database skip straight to the matches instead of reading the whole collection. Analogy: a book's index versus reading every page to find one word. Every index also has to be updated on every write, so the app team won't add one just because your nightly query is slow. Question: if your extraction filters on `updated_at` but there's no index on it, who pays the price?

---

### Slide 28 — Single and Compound Indexes
**Part:** 5 · **Minutes:** 3 · **Type:** code

**On-slide content**
```javascript
// CREATE INDEX ix_customer ON orders(customer_id)
db.orders.createIndex({ "customer.customer_id": 1 });

// Compound: equality first, then sort, then range  (ESR rule)
db.orders.createIndex({ status: 1, created_at: -1 });
// serves: find({status:"paid"}).sort({created_at:-1})
// serves: find({status:"paid"})          (prefix)
// NOT:    find().sort({created_at:-1})   (missing prefix "status")

// Multikey: index on an array field indexes every element
db.orders.createIndex({ "items.sku": 1 });
db.orders.getIndexes();
```

**Speaker notes**
A single-field index is your everyday CREATE INDEX, and dot notation lets you index nested fields. Compound indexes follow the same left-prefix rule as SQL composite indexes; MongoDB's guideline is equality fields first, then sort fields, then ranges. An index on an array field is "multikey": every SKU in every order gets its own entry, which is powerful and can get big. Question: which index would help a query "all paid orders from last week, newest first"?

---

### Slide 29 — Reading `explain()`
**Part:** 5 · **Minutes:** 4 · **Type:** code

**On-slide content**
```javascript
db.orders.dropIndex({ "customer.customer_id": 1 });   // start without the index
db.orders.find({ "customer.customer_id": "C0008" }).explain("executionStats");
//   winningPlan.stage: "COLLSCAN"   nReturned: 11   totalDocsExamined: 200

db.orders.createIndex({ "customer.customer_id": 1 });
db.orders.find({ "customer.customer_id": "C0008" }).explain("executionStats");
//   winningPlan: FETCH ← IXSCAN     nReturned: 11   totalKeysExamined: 11   totalDocsExamined: 11
```
- Look at 3 numbers: **stage**, **nReturned**, **totalDocsExamined**
- Healthy query: docsExamined ≈ nReturned

**Speaker notes**
`explain` is MongoDB's EXPLAIN ANALYZE. Ignore most of the output and look at three things: did it COLLSCAN or IXSCAN, how many documents came back, and how many it had to read to find them. Before the index we read 200 documents to return 11; after, we read exactly 11. On 200 documents nobody notices; on 200 million, that's the difference between milliseconds and an incident. Question: what ratio of docsExamined to nReturned would make you worried?

---

# PART 6 — Replication, Sharding, Transactions (20 min)

---

### Slide 30 — Replica Sets and Elections
**Part:** 6 · **Minutes:** 4 · **Type:** diagram

**On-slide content**
- 1 **primary** takes all writes; **secondaries** copy it
- Primary down → secondaries **elect** a new primary (seconds)
- Typical: 3 members (odd number → majority possible)
- Our lab: **1-member replica set** — enough for oplog + change streams

**Diagram description**
Triangle of three database cylinders. Top: `PRIMARY` (green). Bottom-left and bottom-right: `SECONDARY` (grey). Arrows from primary to each secondary labelled "replicate oplog". Dashed lines between all three labelled "heartbeats". A small `App` box above the primary with a solid arrow "writes" and a dashed arrow to a secondary "reads (optional)". Inset (right): the primary crossed out with a red X, one secondary now labelled `NEW PRIMARY` with a ballot icon.

**Speaker notes**
A replica set is MongoDB's high-availability unit: one primary accepts writes, the others replay its changes and stand ready. If the primary dies, the remaining members vote, and the one with the most up-to-date data becomes primary within seconds; the app driver reconnects automatically. Analogy: a team with a captain, and if the captain leaves the field, the team votes a new one instead of stopping the game. Why does this matter to us? Because the mechanism secondaries use to copy the primary is the same one we'll use to capture changes. Question: why do we need an odd number of voters?

---

### Slide 31 — The Oplog: the Foundation of CDC
**Part:** 6 · **Minutes:** 5 · **Type:** code

**On-slide content**
- `local.oplog.rs`: an ordered log of every write on the primary
- **Capped**: fixed size, oldest entries overwritten → a **time window**
- Idempotent entries: replaying twice gives the same result
- Change Streams read it for you (don't parse the oplog yourself)

```javascript
use local
db.oplog.rs.find({ ns: "shop.orders" }).sort({ $natural: -1 }).limit(1);
// { op: "u", ns: "shop.orders", o: { $v: 2, diff: { u: { status: "paid" } } },
//   o2: { _id: ObjectId("...") }, ts: Timestamp({ t: 1761310000, i: 1 }), ... }

rs.printReplicationInfo();   // oplog size + "log length start to end" = your safety window
```

**Speaker notes**
The oplog is the heart of everything in Parts 6 to 8. Every insert, update and delete on the primary is written as an entry in a special capped collection, secondaries tail it to stay in sync, and change streams read it too. "Capped" is the critical word: it's a circular buffer, so if your consumer is down longer than the oplog window, the changes it missed are gone. Analogy: a security camera that records over the oldest footage; if you check too late, the tape has moved on. Question: if `rs.printReplicationInfo()` says the window is 6 hours and your connector is down for the weekend, what happens Monday morning?

---

### Slide 32 — Read and Write Concerns
**Part:** 6 · **Minutes:** 4 · **Type:** comparison-table

**On-slide content**

| Setting | Meaning | Trade-off |
|---|---|---|
| `w: 1` | Primary acknowledged | Fast; can be rolled back on failover |
| `w: "majority"` | Majority of members have it — **default since 5.0** [S15] | Durable; slightly slower |
| `readConcern: "local"` | Latest data on this node | May later be rolled back |
| `readConcern: "majority"` | Only majority-committed data | Never rolled back — what CDC wants |

```javascript
db.orders.insertOne({ order_id: "ORD-W1" }, { writeConcern: { w: "majority", wtimeout: 5000 } });
db.orders.find({}).readConcern("majority").limit(1);
```

**Speaker notes**
Write concern answers "how sure do I want to be that this write survives a crash"; read concern answers "how sure do I want to be that what I read won't disappear." Since MongoDB 5.0 the default write concern is majority for most deployments, so writes are durable unless someone lowers it. Change streams only emit majority-committed changes, which protects your pipeline from publishing a write that later gets rolled back. Analogy: `w:1` is a verbal agreement, majority is a signed contract. Question: would you rather your pipeline be fast or never publish a phantom order?

---

### Slide 33 — Sharding (concept only)
**Part:** 6 · **Minutes:** 3 · **Type:** diagram
*(Planned cut)*

**On-slide content**
- Split one collection across **shards** by a **shard key**
- Router (`mongos`) sends each query to the right shard(s)
- Bad shard key → hot shard; queries without the key → scatter-gather
- For CDC: change streams merge events from all shards for you

**Diagram description**
Top: `App` → `mongos (router)`. Below the router, three boxes `Shard A (customer_id A–H)`, `Shard B (I–P)`, `Shard C (Q–Z)`, each drawn as a mini 3-node replica set. A small side box `Config servers` connected to mongos with a dashed line.

**Speaker notes**
Sharding is horizontal scaling: one huge collection split by a shard key across several replica sets, with a router that knows which shard holds what. It's the same idea as Kafka partitions keyed by a message key. You won't design shard keys as a data engineer, but you'll feel them: a query without the shard key hits every shard. Question: what would be a terrible shard key for orders?

---

### Slide 34 — Transactions
**Part:** 6 · **Minutes:** 4 · **Type:** code

**On-slide content**
```python
# PyMongo 4.18+ — multi-document ACID transaction (requires a REPLICA SET or sharded cluster)
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/?directConnection=true")
db = client.shop

def place_order(session):
    db.orders.insert_one({"order_id": "ORD-TX1", "status": "paid"}, session=session)
    db.inventory.update_one({"sku": "SKU-101"}, {"$inc": {"stock": -1}},
                            upsert=True, session=session)

with client.start_session() as s:
    s.with_transaction(place_order)   # commits both or neither; retries transient errors
```
- Single-document writes were always atomic
- Multi-document transactions need a **replica set** — another reason for `--replSet`

**Speaker notes**
Writes to a single document have always been atomic in MongoDB, which is one reason embedding is popular. When you must change several documents together, you use a transaction, and just like BEGIN/COMMIT in SQL, either everything commits or nothing does. They only work on a replica set or sharded cluster, which is one more reason our lab runs a one-node replica set instead of a standalone. For CDC: each change in a transaction still arrives as its own event, tagged with the transaction info. Question: should every write be a transaction? (No — they cost performance; use them when the business needs all-or-nothing.)

*(Hostname note: from a laptop terminal use `localhost:27017`; inside the dev_env container use `mongo:27017`. Always with `directConnection=true`.)*

---

# PART 7 — Change Streams (20 min)

---

### Slide 35 — What Are Change Streams
**Part:** 7 · **Minutes:** 4 · **Type:** diagram

**On-slide content**
- A **subscription** to changes on a collection, DB, or whole deployment
- Built on the oplog, but with a stable, documented event format
- Only **majority-committed** changes; ordered; resumable
- Requires a replica set or sharded cluster — not standalone

**Diagram description**
Center: `MongoDB Replica Set` with a scroll labelled `oplog` inside. From the scroll, three arrows going right, each into a box: `watch(collection)`, `watch(database)`, `watch(deployment)`. All three flow into one box `Your consumer (PyMongo / Kafka Connector)`. Above: `App` writing into the replica set.

**Speaker notes**
Change streams are MongoDB's built-in CDC API: you open a cursor that never ends and receive an event for every change. You could tail the raw oplog yourself, but its format is internal and changes between versions; change streams give you a stable, documented contract. Analogy: instead of reading the kitchen's internal order tickets, you subscribe to the restaurant's official notification service. Remember the Kafka consumer from our earlier lessons? This is the same pattern, just reading from a database instead of a topic. Question: why does it matter that only majority-committed changes are sent?

---

### Slide 36 — Event Types and `fullDocument`
**Part:** 7 · **Minutes:** 5 · **Type:** code

**On-slide content**
```javascript
// UPDATE event — default (deltas only)
{ _id: { _data: "8268..." },              // resume token
  operationType: "update",
  clusterTime: Timestamp({ t: 1761310000, i: 1 }),
  ns: { db: "shop", coll: "orders" },
  documentKey: { _id: ObjectId("6a88a594...") },
  updateDescription: { updatedFields: { status: "paid" }, removedFields: [] } }

// + fullDocument: "updateLookup" → also the CURRENT whole document (may be newer, or null)
// DELETE event → only documentKey, never fullDocument
```

| `operationType` | Has `fullDocument`? |
|---|---|
| insert, replace | always |
| update | only with `updateLookup` / `whenAvailable` / `required` |
| delete | never (pre-images only if enabled) |

**Speaker notes**
Every event has the same skeleton: a resume token in `_id`, the operation type, the time, the namespace and the document's `_id`. Updates by default carry only what changed, like a git diff. If you ask for `updateLookup`, MongoDB fetches the current document when it sends the event; but if another update or a delete happened in between, you get a newer version or null [S16]. Deletes never include the document because it no longer exists; if you need the "before" image, the collection must have pre- and post-images enabled. Question: for a Silver table that keeps the latest state of each order, which mode would you choose, and what's the risk?

---

### Slide 37 — Resume Tokens and Fault Tolerance
**Part:** 7 · **Minutes:** 4 · **Type:** diagram

**On-slide content**
- Every event carries a **resume token** = bookmark in the oplog
- Consumer stores the token **after** processing → restart with `resume_after`
- Result: **at-least-once** delivery → design downstream to be idempotent
- Token older than the oplog window → `ChangeStreamHistoryLost` → re-snapshot

**Diagram description**
Horizontal timeline (the oplog) drawn as a ribbon of numbered slots 1…12, with a "window" bracket over slots 4–12 and slots 1–3 faded ("overwritten"). Consumer icon reading slot 7 with a bookmark flag labelled `token=7`. Lower row: "Crash 💥 → restart → resume_after(token=7) → continue at 8". Separate red scenario on the right: bookmark at slot 2 (faded zone) with label "token lost → full re-sync".

**Speaker notes**
A resume token is a bookmark: save it after you process each event, and after a crash you continue right after it. If you crash after processing but before saving, you'll see that event again — that's at-least-once, the same guarantee you saw with Kafka consumer offsets. So downstream must be idempotent: MERGE by `_id`, keep the latest `clusterTime`. The danger zone is when your bookmark falls off the end of the oplog: then there's nothing to resume from and you need a new full snapshot. Question: where does the Kafka connector keep its bookmark? (Kafka Connect offsets — slide 41.)

---

### Slide 38 — Live Demo: Watching a Collection
**Part:** 7 · **Minutes:** 7 · **Type:** demo

**On-slide content** (code, left 2/3; demo steps right 1/3)
```python
# watch_orders.py — PyMongo 4.18+, MongoDB 7.0+ replica set (full file in Appendix A)
from bson import json_util
from pymongo import MongoClient
from pathlib import Path

coll = MongoClient("mongodb://mongo:27017/?directConnection=true")["shop"]["orders"]
token_file = Path("resume_token.json")
token = json_util.loads(token_file.read_text()) if token_file.exists() else None

pipeline = [{"$match": {"operationType": {"$in": ["insert", "update", "replace", "delete"]}}}]
with coll.watch(pipeline, full_document="updateLookup", resume_after=token) as stream:
    for event in stream:                                   # blocks until the next change
        print(event["operationType"], event["documentKey"]["_id"],
              json_util.dumps(event.get("updateDescription") or event.get("fullDocument"))[:200])
        token_file.write_text(json_util.dumps(stream.resume_token))  # bookmark AFTER processing
```
Demo steps (in mongosh, second terminal):
1. `db.orders.insertOne({order_id:"DEMO-1", status:"created"})`
2. `db.orders.updateOne({order_id:"DEMO-1"},{$set:{status:"paid"}})`
3. Ctrl+C the watcher → run step 4 → restart watcher
4. `db.orders.deleteOne({order_id:"DEMO-1"})` → arrives after restart

**Speaker notes**
Split the screen: watcher on the left, mongosh on the right. Insert, and the event appears instantly with the full document; update, and you see only the changed field plus the looked-up document. Now the important part: stop the watcher, delete the document while it's down, start it again — the delete still arrives, because we resumed from the saved token. That's exactly what the Kafka connector does for us in production, just with the bookmark stored in Kafka instead of a file. Question before I restart: will the delete event show the order's status? (No — only the `_id`.) Note on hostnames: inside the dev_env container the host is `mongo`; from a laptop terminal or Compass use `localhost:27017` (always with `directConnection=true`).

**Demo fallback:** if the network or Docker fails, show a pre-recorded terminal GIF of the same 4 steps.

---

# PART 8 — MongoDB and Kafka (10 min)

---

### Slide 39 — The MongoDB Kafka Source Connector
**Part:** 8 · **Minutes:** 2.5 · **Type:** diagram

**On-slide content**
- Official connector, **actively maintained**: latest release **3.1.2** (7 Oct 2026) [S17]
- A Kafka Connect plugin that runs a **change stream for you** and writes events to topics
- Needs MongoDB **3.6+** (4.0+ to watch a whole DB/deployment) and Kafka Connect 2.1+ [S22]
- Managed alternative: Atlas Stream Processing (Atlas only) [S23]

**Code (connector config, for reading — not hands-on)**
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

**Diagram description**
Zoom of slide 10's middle: `MongoDB (oplog)` → arrow `change stream` → large box `Kafka Connect worker` containing a smaller box `MongoSourceConnector task` and a small cylinder `offsets topic (resume token)` → arrow → `Kafka topic: shop.orders`.

**Speaker notes**
In the Kafka lessons we talked about source connectors as an idea; this is a real one. It's a plugin you deploy into Kafka Connect, and internally it does exactly what our Python script did: open a change stream, turn each event into a Kafka record, and store the resume token, here in Kafka Connect's offsets instead of a file. It's the official MongoDB connector and still actively released; the newest version came out this month. Notice there's no code to write, just configuration. Question: comparing to our Python watcher, what do we get for free here? (Scaling, offsets, retries, monitoring.)

**Instructor note:** the compatibility page lists minimum versions only; I found no explicit statement that 9.0 is tested [UNVERIFIED for 9.0].

---

### Slide 40 — Message Structure: Updates and Deletes
**Part:** 8 · **Minutes:** 2.5 · **Type:** comparison-table

**On-slide content**

| Connector setting | insert | update | delete |
|---|---|---|---|
| **Default** (`change.stream.full.document=""`) [S18] | Full change event incl. `fullDocument` | Event with `updateDescription` (deltas only) | Event with `documentKey` only |
| `change.stream.full.document=updateLookup` | same | Deltas **+ current** `fullDocument` (may be newer or null) | `documentKey` only |
| `publish.full.document.only=true` (forces updateLookup) [S18] | Just the document | Just the current document | **No document to publish** → dropped [S28] |
| …`+ publish.full.document.only.tombstone.on.delete=true` [S18] | — | — | **Tombstone**: key = `_id`, value = `null` |

- Record **key** = `documentKey` by default (`change.stream.document.key.as.key=true`) [S18]
- "Before" image: `change.stream.full.document.before.change` + collection pre-images enabled (MongoDB 6.0+) [S27]

**Speaker notes**
This table is the decision you'll make on day one with a Mongo source. The tempting setup is "full document only" because downstream gets clean documents that look like rows — but then deletes vanish unless you also turn on tombstones. Tombstones are the Kafka convention you may remember from compacted topics: a key with a null value means "this key is gone." Downstream, your Snowflake or Iceberg MERGE uses the `_id` from the key: upsert on documents, delete on tombstones. Question: if the business asks "how many orders were cancelled by deleting them last month", which setting must you have chosen?

---

### Slide 41 — What Happens on Failure
**Part:** 8 · **Minutes:** 2 · **Type:** comparison-table

**On-slide content**

| Failure | What the connector does | What you do |
|---|---|---|
| Connect worker restarts | Resumes from the resume token in Connect offsets | Nothing — expect a few **duplicates** (at-least-once) |
| Connector down longer than the oplog window | `Invalid resume token` → stops [S21] | New `offset.partition.name` + `startup.mode=copy_existing` re-snapshot [S20][S19] |
| Quiet collection, busy cluster | Token ages out even while running | Set `heartbeat.interval.ms` (default `0` = off) [S20] |
| Bad record / conversion error | Stops (`mongo.errors.tolerance=none` default) [S20] | `=all` + dead-letter topic, and monitor it |

**Speaker notes**
Most failures are boring: the worker restarts, reads its saved token and continues, and you get a few duplicates that your idempotent MERGE absorbs. The dangerous one is a long outage: if the oplog has moved past the saved token, the connector cannot continue and someone has to decide between a gap and a full re-snapshot. A sneaky variant: a collection with very few writes, on a busy cluster, can lose its token even while the connector is up — heartbeats fix that by refreshing the token. Question: who in your team would get paged for "invalid resume token", and do they know the oplog window?

---

### Slide 42 — Source-Side Checklist  *(replaces the old Hello Heart placeholder)*
**Part:** 8 · **Minutes:** 1.5 · **Type:** checklist
*(Generic by design: no company-specific details.)*

**On-slide content** (5 numbered rows; the grey reference after each row points to the slides that cover it)
1. **Oplog window** longer than your longest outage · slides 31, 41
2. **Decide how deletes arrive**: tombstones or they vanish · slide 40
3. **Profile types and shapes**: `$type`, `schema_v`, a `$jsonSchema` contract · slides 15, 16, 26
4. **Idempotent sink**: MERGE by `_id`, expect duplicates · slides 37, 41
5. **Quiet collections**: set `heartbeat.interval.ms` · slide 41

**Speaker notes**
This is the whole lesson as a checklist you can take to any team that says "the app data is in Mongo, get it into the warehouse." One: check the oplog window before you connect anything, because if the connector is down longer than the window, you need a full re-snapshot. Two: decide on day one how deletes arrive, because with full-document-only mode a delete simply disappears unless tombstones are on. Three: profile the collection for mixed types and moved fields, and ask the app team for a validation contract on the fields your pipeline depends on. Four: make the sink idempotent, MERGE by _id, because at-least-once delivery means duplicates. Five: on a quiet collection set a heartbeat so the resume token doesn't age out. Each point maps to a slide we already covered, so use this as your review. Question to the class: which of these five do you think a team usually discovers only after something breaks?

---

### Slide 43 — Summary and Practice Instructions
**Part:** 8 · **Minutes:** 1.5 · **Type:** summary

**On-slide content**
- MongoDB = app's **source of truth**; analytics happens **downstream**
- Flexible schema → **drift, mixed types, nested arrays** → you must detect them
- Oplog → **Change Streams** → **Kafka source connector** → lakehouse
- **Practice (60 min):** `docker compose up -d` → open `lab/handout.md` → Setup

**Speaker notes**
Three takeaways: MongoDB is where the data is born, not where it's analyzed; its flexibility is the data engineer's main problem to manage; and the oplog-to-Kafka path is how modern platforms get the data out. For the next hour you'll do everything we discussed on a deliberately messy dataset. Your goal: find at least four data problems and see a change stream with your own eyes. Questions before we start?

---

### Slide 44 — SQL to MongoDB Vocabulary Map  *(reference slide, moved to the end)*
**Part:** appendix · **Minutes:** 0 (show during practice, or hand out) · **Type:** comparison-table

**On-slide content**

| SQL | MongoDB |
|---|---|
| database | database |
| table | collection |
| row | document (BSON) |
| column | field (can be nested) |
| primary key | `_id` (auto `ObjectId`) |
| `WHERE` | filter `{ field: value }` |
| `SELECT col` | projection `{ col: 1 }` |
| `GROUP BY` | `$group` (aggregation) |
| `JOIN` | `$lookup` (or embed) |
| `ALTER TABLE` | nothing — no fixed schema |

**Speaker notes**
This is your translation dictionary; it sits at the end so you can put it on screen during the practice hour. Two rows matter most for us. First, `_id`: every document has one and it's what we'll MERGE on downstream. Second, the last row: there is no ALTER TABLE, because there is no table definition to alter. That ties back to slides 4 and 15: if there's no ALTER TABLE, how do you find out a column was added?

---

# Appendix A — Lab Setup: Single-Node Replica Set + Messy Dataset

Files (delivered alongside this deck, in the GitHub repo `nivbadli1/cde_mongodb`): `docker-compose.yml`, `lab/seed_orders.py`, `orders.json` (generated), `lab/watch_orders.py`.

## A.1 `docker-compose.yml`  (mongo + dev_env — **untested, run once before class**)

```yaml
# Single-node MongoDB replica set + the course dev environment.
# A replica set (even with ONE member) is required for: the oplog,
# change streams, multi-document transactions and the Kafka source connector.
#
#   docker compose up -d
#   docker compose ps            # wait for mongo "healthy"
#   docker exec -it mongo mongosh
#
# Image: mongo:8.0 (works the same with mongo:7.0 or mongo:9.0).
services:
  mongo:
    image: mongo:8.0
    container_name: mongo
    hostname: mongo
    command: ["mongod", "--replSet", "rs0", "--bind_ip_all", "--port", "27017"]
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    # The healthcheck doubles as the initializer:
    #  - replica set already initiated -> rs.status() succeeds -> healthy
    #  - otherwise -> rs.initiate() with host "mongo:27017" (the compose-network name)
    healthcheck:
      test:
        - CMD
        - mongosh
        - --quiet
        - --eval
        - >
          try { rs.status().ok }
          catch (e) { rs.initiate({_id: 'rs0', members: [{_id: 0, host: 'mongo:27017'}]}).ok }
      interval: 5s
      timeout: 10s
      start_period: 10s
      retries: 30

  dev_env:
    # Copy this block from your existing course compose if the image tag or ports differ.
    image: ofrir119/developer_env:spark340_ssh
    container_name: dev_env
    ports:
      - "22022:22"
      - "8888:8888"
      - "4040-4042:4040-4042"
    environment:
      MONGO_URI: mongodb://mongo:27017/?directConnection=true
    depends_on:
      mongo:
        condition: service_healthy

volumes:
  mongo_data:
```

**Hostnames — say this once to the class:**
- **Inside the `dev_env` container** (Jupyter notebooks, Python scripts): `mongodb://mongo:27017/?directConnection=true`.
- **From the laptop** (Compass, a local Python): `mongodb://localhost:27017/?directConnection=true`.
- **mongosh**: `docker exec -it mongo mongosh` (no URI needed).
- Always use `directConnection=true`: the replica set advertises `mongo:27017`, which a laptop cannot resolve; with `directConnection=true` the driver skips discovery and uses the address you gave.
- A Kafka Connect container on the same compose network can reach `mongo:27017` directly, so the connector config on slide 39 (`mongodb://mongo:27017/?replicaSet=rs0`) works as written. (Untested in this lesson.)

**Manual alternative** (if a student's compose overrides the healthcheck):
```javascript
// docker exec -it mongo mongosh
rs.initiate({ _id: "rs0", members: [{ _id: 0, host: "mongo:27017" }] });
rs.status().members[0].stateStr;   // → "PRIMARY" after a few seconds
```

## A.2 Dataset: `seed_orders.py` (200 messy orders, deterministic)

```python
"""
seed_orders.py - builds the practice dataset for the Naya MongoDB lesson.

Creates 200 "orders" documents for a fictional Israeli e-commerce shop,
with intentionally MESSY fields (this is the point of the exercise):
  - total:       Decimal128 / double / string / missing
  - status:      mixed case ("shipped", "SHIPPED", "Shipped") / missing
  - created_at:  BSON Date / ISO string / epoch-millis integer
  - customer:    schema v1 has customer.email,
                 schema v2 moved it to customer.contact.email (+ phone)
  - items:       array of 0-4 sub-documents; qty sometimes a string
  - tags:        array / single string / missing
  - city:        "Tel Aviv" / "tel aviv" / "Tel-Aviv" ...
  - coupon:      string / null / missing
  - 2 duplicated order_id values (for data-quality checks)

Usage (MongoDB running as replica set rs0):
    pip install "pymongo==4.18.3"
    python seed_orders.py                       # inserts into shop.orders
    python seed_orders.py --json-only           # only writes orders.json
The connection string comes from $MONGO_URI (set inside dev_env), else localhost.

orders.json is canonical Extended JSON, so this also works:
    mongoimport --uri "mongodb://localhost:27017/?directConnection=true" \
        --db shop --collection orders --jsonArray --file orders.json

Tested with: Python 3.12/3.13, PyMongo 4.18+, MongoDB 8.0 (also valid for 7.0 / 9.0).
The generator is deterministic (seed=42): every student gets the same data,
so the "expected outputs" in the practice guide match.
"""
import argparse
import os
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from bson import Decimal128, ObjectId
from bson.json_util import dumps, JSONOptions, JSONMode

SEED = 42
N_DOCS = 200
SCHEMA_V2_FROM = datetime(2026, 6, 1, tzinfo=timezone.utc)  # app release that moved email
START = datetime(2026, 1, 1, tzinfo=timezone.utc)

FIRST = ["Noa", "Yonatan", "Maya", "Itai", "Tamar", "Omer", "Shira", "Daniel",
         "Yael", "Amit", "Lior", "Roni", "Eden", "Guy", "Michal", "Ariel"]
LAST = ["Cohen", "Levi", "Mizrahi", "Peretz", "Biton", "Friedman", "Azoulay",
        "Katz", "Shapiro", "Ben-David", "Golan", "Avraham"]
CITIES = {
    "Tel Aviv": ["Tel Aviv", "Tel Aviv", "tel aviv", "Tel-Aviv", "TLV"],
    "Haifa": ["Haifa", "Haifa", "haifa"],
    "Jerusalem": ["Jerusalem", "Jerusalem", "jerusalem"],
    "Netanya": ["Netanya", "Netanya"],
    "Be'er Sheva": ["Be'er Sheva", "Beer Sheva"],
    "Rishon LeZion": ["Rishon LeZion", "Rishon Lezion"],
}
PRODUCTS = [  # sku, name, price (ILS)
    ("SKU-100", "Running Shoes", 349.90), ("SKU-101", "Yoga Mat", 89.90),
    ("SKU-102", "Water Bottle", 39.90), ("SKU-103", "Smart Watch", 899.00),
    ("SKU-104", "Headphones", 499.00), ("SKU-105", "Backpack", 229.00),
    ("SKU-106", "Sunglasses", 179.00), ("SKU-107", "Bike Helmet", 259.00),
]
STATUSES = ["created", "paid", "shipped", "delivered", "cancelled"]
PAYMENTS = ["credit_card", "paypal", "bit", "apple_pay"]
TAGS = ["gift", "express", "first_order", "vip", "sale"]


def build_docs():
    rnd = random.Random(SEED)
    docs = []
    for i in range(N_DOCS):
        created = START + timedelta(minutes=rnd.randint(0, 290 * 24 * 60))
        cust_no = rnd.randint(1, 60)
        first, last = rnd.choice(FIRST), rnd.choice(LAST)
        canonical_city = rnd.choice(list(CITIES))
        city = rnd.choice(CITIES[canonical_city])

        # ---- items (array of sub-documents) --------------------------------
        items = []
        for _ in range(rnd.choice([0, 1, 1, 2, 2, 3, 4]) if i % 25 else 0):
            sku, name, price = rnd.choice(PRODUCTS)
            qty = rnd.randint(1, 3)
            items.append({
                "sku": sku, "name": name,
                "qty": str(qty) if rnd.random() < 0.1 else qty,   # mixed type!
                "unit_price": price,
            })
        amount = round(sum(int(it["qty"]) * it["unit_price"] for it in items), 2)

        # ---- customer: schema drift v1 -> v2 -------------------------------
        email = f"{first}.{last}{cust_no}@example.com".lower().replace("'", "")
        customer = {"customer_id": f"C{cust_no:04d}", "name": f"{first} {last}"}
        if created < SCHEMA_V2_FROM:
            schema_v = 1
            customer["email"] = email
        else:
            schema_v = 2
            customer["contact"] = {"email": email,
                                   "phone": f"+972-5{rnd.randint(0, 9)}-{rnd.randint(1000000, 9999999)}"}

        doc = {
            # deterministic ObjectId: 4-byte timestamp = order time, rest = counter
            "_id": ObjectId(f"{int(created.timestamp()):08x}{i:016x}"),
            "order_id": f"ORD-{10000 + i}",
            "schema_v": schema_v,
            "customer": customer,
            "shipping": {"address": {"city": city, "country": "IL"}},
            "items": items,
        }

        # ---- total: Decimal128 / double / string / missing -----------------
        r = rnd.random()
        if r < 0.60:
            doc["total"] = Decimal128(Decimal(f"{amount:.2f}"))
        elif r < 0.85:
            doc["total"] = float(amount)
        elif r < 0.95:
            doc["total"] = f"{amount:.2f}"          # a string. Classic.
        # else: missing

        # ---- status: mixed case / missing ----------------------------------
        r = rnd.random()
        status = rnd.choice(STATUSES)
        if r < 0.85:
            doc["status"] = status
        elif r < 0.92:
            doc["status"] = status.upper()
        elif r < 0.97:
            doc["status"] = status.capitalize()
        # else: missing

        # ---- created_at: Date / ISO string / epoch millis ------------------
        r = rnd.random()
        if r < 0.85:
            doc["created_at"] = created
        elif r < 0.95:
            doc["created_at"] = created.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            doc["created_at"] = int(created.timestamp() * 1000)

        # ---- payment: sometimes missing ------------------------------------
        if rnd.random() < 0.9:
            doc["payment"] = {"method": rnd.choice(PAYMENTS),
                              "installments": rnd.choice([1, 1, 1, 3, 6])}

        # ---- tags: array / string / missing --------------------------------
        r = rnd.random()
        if r < 0.6:
            doc["tags"] = rnd.sample(TAGS, rnd.randint(1, 2))
        elif r < 0.75:
            doc["tags"] = rnd.choice(TAGS)
        # else: missing

        # ---- coupon: string / null / missing -------------------------------
        r = rnd.random()
        if r < 0.2:
            doc["coupon"] = rnd.choice(["WELCOME10", "SUMMER26", "VIP15"])
        elif r < 0.5:
            doc["coupon"] = None

        docs.append(doc)

    # two duplicated business keys (a bug in the app's retry logic)
    docs[150]["order_id"] = docs[10]["order_id"]
    docs[151]["order_id"] = docs[11]["order_id"]
    return docs


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--uri", default=os.getenv("MONGO_URI", "mongodb://localhost:27017/?directConnection=true"))
    p.add_argument("--json-only", action="store_true")
    args = p.parse_args()

    docs = build_docs()
    with open("orders.json", "w", encoding="utf-8") as f:
        f.write(dumps(docs, json_options=JSONOptions(json_mode=JSONMode.CANONICAL), indent=1))
    print(f"wrote orders.json ({len(docs)} docs)")

    if args.json_only:
        return
    from pymongo import MongoClient
    client = MongoClient(args.uri)
    coll = client["shop"]["orders"]
    coll.drop()
    coll.insert_many(docs)
    print(f"inserted {coll.count_documents({})} docs into shop.orders")


if __name__ == "__main__":
    main()
```

**What's messy, by design (exact counts for seed 42):**

| Field | Mess | Count |
|---|---|---|
| `total` | Decimal128 / double / **string** / missing | 115 / 55 / 19 / 11 |
| `status` | 14 spellings of 5 values (lower, UPPER, Capitalized); missing | 30 non-lowercase; 7 missing |
| `created_at` | Date / ISO **string** / epoch-millis **int** | 162 / 26 / 12 |
| `customer` email | `customer.email` (schema_v 1) vs `customer.contact.email` (schema_v 2) | 107 / 93 |
| `items` | empty arrays; `qty` stored as string | 40 empty; 36 string qtys |
| `tags` | array / single string / missing | 119 / 38 / 43 |
| `coupon` | string / `null` / missing | 43 / 67 / 90 |
| `payment` | missing sub-document | 22 |
| `shipping.address.city` | "Tel Aviv", "tel aviv", "Tel-Aviv", "TLV", "Beer Sheva" vs "Be'er Sheva"… | 13 raw spellings |
| `order_id` | duplicated business keys | ORD-10010, ORD-10011 |

## A.3 Change stream watcher: `watch_orders.py`

```python
"""
watch_orders.py - live Change Stream demo (slide 38 + practice step 5).

Prints every change on shop.orders while you insert / update / delete in mongosh.
Saves the resume token after every event, so if you stop it (Ctrl+C) and start it
again, it continues exactly where it stopped - the same trick the Kafka source
connector uses (it stores the token in Kafka Connect offsets).

Requirements:
  - MongoDB 7.0+ running as a replica set (single-node rs0 is fine)
  - Python 3.10+, PyMongo 4.18+      ->  pip install "pymongo==4.18.3"

Run:
  python watch_orders.py                 # resume from saved token if it exists
  python watch_orders.py --from-scratch  # ignore saved token, start from "now"
"""
import argparse
import os
import sys
from pathlib import Path

from bson import json_util
from pymongo import MongoClient
from pymongo.errors import OperationFailure, PyMongoError

URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?directConnection=true")
TOKEN_FILE = Path("resume_token.json")


def load_token():
    if TOKEN_FILE.exists():
        return json_util.loads(TOKEN_FILE.read_text())
    return None


def save_token(token):
    # resume tokens are BSON documents -> store as Extended JSON
    TOKEN_FILE.write_text(json_util.dumps(token))


def pretty(event):
    """Print the parts of a change event a data engineer cares about."""
    op = event["operationType"]
    key = event.get("documentKey", {}).get("_id")
    print(f"\n=== {op.upper()}  _id={key}  clusterTime={event.get('clusterTime')}")
    if op == "update":
        desc = event["updateDescription"]
        print("  updatedFields :", json_util.dumps(desc.get("updatedFields")))
        print("  removedFields :", desc.get("removedFields"))
    if event.get("fullDocument") is not None:
        print("  fullDocument  :", json_util.dumps(event["fullDocument"])[:300])
    elif op in ("update", "replace"):
        print("  fullDocument  : None  (document was deleted before the lookup ran)")
    if op == "delete":
        print("  (delete events carry only the _id - no fullDocument)")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--from-scratch", action="store_true")
    args = p.parse_args()

    coll = MongoClient(URI)["shop"]["orders"]
    token = None if args.from_scratch else load_token()

    # Optional server-side filter - same idea as the connector's "pipeline" setting.
    # Example: only inserts/updates/deletes (ignore drop/rename/invalidate noise)
    pipeline = [{"$match": {"operationType": {"$in": ["insert", "update", "replace", "delete"]}}}]

    print(f"Watching shop.orders  (resume_after={'saved token' if token else 'None -> now'})")
    try:
        with coll.watch(
            pipeline,
            full_document="updateLookup",   # also return the current full doc on updates
            resume_after=token,
        ) as stream:
            for event in stream:            # blocks and waits for the next event
                pretty(event)
                save_token(stream.resume_token)
    except KeyboardInterrupt:
        print("\nStopped. Resume token saved to", TOKEN_FILE)
    except OperationFailure as e:
        # Typical cause: the token's oplog entry was already overwritten
        # (ChangeStreamHistoryLost). Same failure the Kafka connector reports.
        print("Cannot resume:", e.details.get("codeName"), "-", e, file=sys.stderr)
        print("Run again with --from-scratch (and accept the data gap!)", file=sys.stderr)
        sys.exit(1)
    except PyMongoError as e:
        print("Connection problem:", e, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
```

---

# Appendix B — Practice Guide (60 min)

**Goal:** explore a collection you've never seen, find its data problems, fix some with CRUD, analyze with aggregations, speed up a query with an index, and watch changes live.

Expected outputs below are computed from the seed-42 dataset. Numbers must match exactly; formatting (spacing, field order) may differ. Decimal sums produced by `$convert` from doubles may print with extra trailing zeros, e.g. `Decimal128('31354.6000000000')`.

## Step 0 — Setup (5 min) · slides 30–31

```bash
docker compose up -d
docker compose ps                        # mongo STATUS must show (healthy)
# Python runs inside dev_env (MONGO_URI is preset there); on a laptop: pip install "pymongo==4.18.3"
python seed_orders.py                    # → wrote orders.json (200 docs) / inserted 200 docs into shop.orders
docker exec -it mongo mongosh
```
```javascript
rs.status().members[0].stateStr          // → 'PRIMARY'
use shop
```

## Step 1 — Explore (10 min) · slides 4, 11, 15, 22, 26

```javascript
db.getCollectionNames()                  // → [ 'orders' ]
db.orders.countDocuments({})             // → 200
db.orders.aggregate([{ $sample: { size: 2 } }])   // 2 random docs — compare their shapes!
db.orders.distinct("status")
// → [ 'CANCELLED','CREATED','Cancelled','DELIVERED','Delivered','PAID','Paid',
//     'SHIPPED','Shipped','cancelled','created','delivered','paid','shipped' ]   (14 values)
db.orders.countDocuments({ status: { $exists: false } })          // → 7
db.orders.aggregate([{ $group: { _id: { $type: "$total" }, n: { $sum: 1 } } }])
// → decimal 115, double 55, string 19, missing 11
db.orders.aggregate([{ $group: { _id: { $type: "$created_at" }, n: { $sum: 1 } } }])
// → date 162, string 26, long 12
db.orders.aggregate([{ $group: { _id: "$schema_v", n: { $sum: 1 } } }])
// → 1: 107, 2: 93
db.orders.countDocuments({ "customer.email": { $exists: true } })          // → 107
db.orders.countDocuments({ "customer.contact.email": { $exists: true } })  // → 93
db.orders.countDocuments({ items: { $size: 0 } })                          // → 40
```
**Task:** write down at least 4 data problems you found. (Expected: mixed `total` types, inconsistent `status` case + missing, `created_at` in 3 formats, email moved between schema versions, empty `items`, inconsistent city names, duplicate `order_id`.)

## Step 2 — CRUD (15 min) · slides 18–21

```javascript
// 2a. Silent exclusion: numbers vs strings
db.orders.countDocuments({ total: { $gte: 1000 } })        // → 75
db.orders.countDocuments({ total: { $type: "string" } })   // → 19
// Question: how many of the 19 string totals are >= 1000?  → 7  (82 total if converted)

// 2b. Case sensitivity
db.orders.countDocuments({ "shipping.address.city": "Haifa", status: "delivered" })   // → 2

// 2c. Fix status casing (pipeline update)
db.orders.updateMany({ status: { $exists: true } },
                     [{ $set: { status: { $toLower: "$status" } } }])
// → matchedCount: 193, modifiedCount: 30
db.orders.distinct("status")   // → [ 'cancelled', 'created', 'delivered', 'paid', 'shipped' ]
db.orders.countDocuments({ "shipping.address.city": "Haifa", status: "delivered" })   // → 3

// 2d. Insert + upsert + delete your own test order
db.orders.insertOne({ order_id: "ORD-TEST-1", status: "created", total: NumberDecimal("10.00"), created_at: new Date() })
db.orders.updateOne({ order_id: "ORD-TEST-2" }, { $set: { status: "created" } }, { upsert: true })
// → upsertedCount: 1
db.orders.deleteMany({ order_id: { $in: ["ORD-TEST-1", "ORD-TEST-2"] } })   // → deletedCount: 2
db.orders.countDocuments({})                                                // → 200
```

## Step 3 — Aggregations (15 min) · slides 23–26

**3a. Orders per status (after Step 2c)** — like `GROUP BY status ORDER BY 2 DESC`
```javascript
db.orders.aggregate([
  { $group: { _id: "$status", n: { $sum: 1 } } },
  { $sort: { n: -1 } }
])
// → cancelled 58, delivered 36, shipped 34, created 33, paid 32, null 7
```
(If you run it with `{ $toLower: "$status" }` *before* Step 2c, the 7 missing statuses show as `""` (empty string), not `null` — `$toLower` turns missing into an empty string.)

**3b. Revenue per city, excluding cancelled (slide 24)**
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
Follow-up: remove `$limit` and find the cities that still don't merge (`tlv`, `beer sheva` vs `be'er sheva`).

**3c. Top 3 SKUs by quantity (`$unwind`)**
```javascript
db.orders.aggregate([
  { $unwind: "$items" },
  { $group: { _id: "$items.sku", name: { $first: "$items.name" }, qty: { $sum: { $toInt: "$items.qty" } } } },
  { $sort: { qty: -1 } }, { $limit: 3 }
])
// → SKU-105 Backpack 100, SKU-106 Sunglasses 98, SKU-107 Bike Helmet 92
```
Follow-up: remove `$toInt`. Why do the numbers drop? (String qtys are ignored by `$sum`.)

**3d. Duplicate business keys**
```javascript
db.orders.aggregate([{ $group: { _id: "$order_id", n: { $sum: 1 } } }, { $match: { n: { $gt: 1 } } }])
// → ORD-10010 (2), ORD-10011 (2)
```

## Step 4 — Index + explain (7 min) · slides 27–29

```javascript
db.orders.find({ "customer.customer_id": "C0008" }).explain("executionStats").executionStats
// → nReturned: 11, totalDocsExamined: 200, (queryPlanner.winningPlan.stage: 'COLLSCAN')
db.orders.createIndex({ "customer.customer_id": 1 })
db.orders.find({ "customer.customer_id": "C0008" }).explain("executionStats").executionStats
// → nReturned: 11, totalKeysExamined: 11, totalDocsExamined: 11 (IXSCAN under FETCH)
```
Bonus: create `{ status: 1, created_at: -1 }` and explain `find({status:"paid"}).sort({created_at:-1})` — no `SORT` stage should appear.

## Step 5 — Change Stream in PyMongo (8 min) · slides 35–38

Terminal 1 (inside dev_env, or a laptop with `MONGO_URI` pointing to `localhost`):
```bash
python watch_orders.py --from-scratch
# → Watching shop.orders  (resume_after=None -> now)
```
Terminal 2 (mongosh):
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
```
Watching shop.orders  (resume_after=saved token)
=== DELETE  _id=...
  (delete events carry only the _id - no fullDocument)
```
**Discussion (slides 15, 40, 42):** this is what the Kafka source connector does with Kafka Connect offsets.

## Bonus (if time remains) · slides 39–41
- Add the `$jsonSchema` validator from slide 16 with `validationAction: "warn"`, insert a bad document, then find the warning: `docker logs mongo | grep -i "validation"`.
- Build a "Silver" view: `$project` a flat `email` field with `{ $ifNull: ["$customer.contact.email", "$customer.email"] }` and count how many are still null (→ 0).

---

# Appendix C — Sources

Accessed 24 Oct 2026.

| # | Source | URL |
|---|---|---|
| S1 | MongoDB — Toyota Connected case study | https://mongodb.com/solutions/customer-case-studies/toyota-connected |
| S2 | KMWorld — MongoDB Atlas transforms Toyota Safety Connect | https://www.kmworld.com/Articles/News/KM-In-Practice/MongoDB-Atlas-transforms-Toyota-Safety-Connect-165968.aspx |
| S3 | Just Auto — Toyota Connected interview (quotes 99% availability) | https://www.just-auto.com/?p=173190 |
| S4 | MongoDB blog — Atlas at 10 Years (Toyota: 20+ DBs, 99.99%, 9M+ vehicles) | https://mongodb.com/company/blog/news/atlas-10-years-celebrating-customers-behind-platform |
| S5 | MongoDB blog — Forbes cloud migration (58% build speed, 2–10× releases, 25% TCO) | https://mongodb.com/blog/post/forbes-cloud-migration-helps-worlds-biggest-media-brand-continue-standard-digital-innovation |
| S6 | Google Cloud blog — Forbes migrates to MongoDB Atlas on Google Cloud | https://cloud.google.com/blog/products/databases/forbes-migrates-to-mongodb-atlas-on-google-cloud |
| S7 | MongoDB — Forbes case study (Solr → Atlas Search plan) | https://www.mongodb.com/solutions/customer-case-studies/forbes |
| S8 | MongoDB @ eBay (2012 talk; daily bulk load from Hadoop) | https://speakerdeck.com/mongodb/mongodb-ebay |
| S9 | MongoDB blog — eBay multi-data-center applications (2017) | https://www.mongodb.com/blog/post/ebay-building-mission-critical-multi-data-center-applications-with-mongodb |
| S10 | DataStax — Configuring data consistency (Cassandra) | https://docs.datastax.com/en/cassandra/2.0/cassandra/dml/dml_config_consistency_c.html |
| S11 | AWS SDK docs — DynamoDB `ConsistentRead`; AWS global tables consistency | https://docs.aws.amazon.com/sdkfornet1/latest/apidocs/html/P_Amazon_DynamoDBv2_Model_KeysAndAttributes_ConsistentRead.htm · https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html |
| S12 | Redis — Replication | https://redis.io/docs/latest/operate/oss_and_stack/management/replication/ |
| S13 | Elastic — Near real-time search | https://www.elastic.co/docs/manage-data/data-store/near-real-time-search |
| S14 | PostgreSQL — High Availability, Load Balancing, and Replication | https://www.postgresql.org/docs/current/high-availability.html |
| S15 | MongoDB — Default read/write concerns | https://mongodb.com/docs/manual/reference/mongodb-defaults/ |
| S16 | MongoDB — Change Streams | https://www.mongodb.com/docs/current/changeStreams/ |
| S17 | GitHub — mongodb/mongo-kafka releases | https://github.com/mongodb/mongo-kafka/releases |
| S18 | MongoDB Kafka Connector — Change Stream properties | https://www.mongodb.com/docs/kafka-connector/current/source-connector/configuration-properties/change-stream/ |
| S19 | MongoDB Kafka Connector — Startup properties | https://www.mongodb.com/docs/kafka-connector/current/source-connector/configuration-properties/startup/ |
| S20 | MongoDB Kafka Connector — Error handling and resuming | https://www.mongodb.com/docs/kafka-connector/current/source-connector/configuration-properties/error-handling/ |
| S21 | MongoDB Kafka Connector — Invalid resume token | https://www.mongodb.com/docs/kafka-connector/current/troubleshooting/recover-from-invalid-resume-token/ |
| S22 | MongoDB Kafka Connector — Compatibility | https://mongodb.com/docs/kafka-connector/upcoming/compatibility |
| S23 | MongoDB — Kafka Connector vs Atlas Stream Processing | https://mongodb.com/docs/kafka-connector/master/kafka-connector-atlas-stream-processing-comparison |
| S24 | MongoDB press release — MongoDB 9.0 GA (29 Sep 2026) | https://mongodb.com/company/newsroom/press-releases/mongodb-launches-mongodb-9-0-the-best-version-ever-built-and-atlas-infinite-for-ai-scale-demand |
| S25 | MongoDB — 9.0 release notes | https://www.mongodb.com/docs/manual/release-notes/9.0/ |
| S26 | PyPI - pymongo (4.19.0 latest, needs Python 3.11+; 4.18.3 used in dev_env) | https://pypi.org/project/pymongo/ |
| S27 | MongoDB blog — Kafka Connector 1.9 (pre/post images) | https://mongodb.com/blog/post/introducing-mongodb-connector-apache-kafka-version-1-9 |
| S28 | OneUptime — Change Streams with the Kafka Connector (deletes excluded with full-document-only) | https://oneuptime.com/blog/post/2026-03-31-mongodb-change-streams-kafka-connector/view |

---

# Cut list (if you're running late)

Already planned cuts: slides **17, 26, 33**. Beyond those, cut in this order:

1. **Slide 44 — Vocabulary map** is already out of the lecture flow (0 min); just don't show it.
2. **Slide 9 — Forbes** (−2 min): keep Toyota as the single use-case, mention Forbes in one sentence.
3. **Slide 21 — Delete** (−2 min): say one sentence while on slide 20; keep the "deletes are invisible except in the oplog" point for slide 36.
4. **Slide 14 — Modeling by access patterns** (−4 min): fold its one-liner ("schema follows the app's screens") into slide 13.
5. **Slide 34 — Transactions** (−4 min): one sentence on slide 30 ("they require a replica set").
6. **Slide 32 — Read/write concerns** (−2 of 4 min): keep only the "change streams emit majority-committed changes only" line.

**Never cut:** 4, 10, 15, 22, 31, 36–38, 40, 42 — they carry the lesson's goal.
