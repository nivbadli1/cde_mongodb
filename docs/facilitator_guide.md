# Facilitator Guide - MongoDB Practice Lab

For the instructor. Student instructions are in [`lab/handout.md`](../lab/handout.md); the slide content and expected outputs come from [`MongoDB_Lesson_Deck_Content.md`](MongoDB_Lesson_Deck_Content.md) (Appendix A + B).

## Pre-class checklist (about 10 min, do it on a machine like the students')

```bash
git clone https://github.com/nivbadli1/cde_mongodb && cd cde_mongodb
docker compose up -d
docker compose ps                                  # mongo: Up (healthy); dev_env: Up
docker exec mongo mongosh --quiet --eval 'db.version() + " " + rs.status().members[0].stateStr'
# → 8.0.x PRIMARY
docker exec dev_env pip install "pymongo==4.18.3"  # dev_env has Python 3.10 -> 4.19.0 will not install
docker exec -w /home/developer/lab dev_env python3 seed_orders.py
# → wrote orders.json (200 docs) / inserted 200 docs into shop.orders
```

Spot-check the counts (all must match):
```bash
docker exec mongo mongosh --quiet shop --eval '
print(db.orders.countDocuments({}));                                    // 200
print(db.orders.distinct("status").length);                             // 14
print(db.orders.countDocuments({ status: { $exists: false } }));        // 7
print(db.orders.countDocuments({ total: { $gte: 1000 } }));             // 75
print(db.orders.countDocuments({ total: { $type: "string" } }));        // 19
print(db.orders.countDocuments({ items: { $size: 0 } }));               // 40
printjson(db.orders.aggregate([{ $group: { _id: { $type: "$total" }, n: { $sum: 1 } } }]).toArray());  // decimal 115, double 55, string 19, missing 11
printjson(db.orders.aggregate([{ $group: { _id: "$schema_v", n: { $sum: 1 } } }]).toArray());          // 1: 107, 2: 93
printjson(db.orders.aggregate([{ $group: { _id: "$order_id", n: { $sum: 1 } } }, { $match: { n: { $gt: 1 } } }]).toArray());  // ORD-10010, ORD-10011'
```

Test the change stream (two terminals):
1. `docker exec -it dev_env bash -c 'cd /home/developer/lab && python3 watch_orders.py --from-scratch'`
2. In mongosh: insert `CS-1`, update it to `paid` → both events appear.
3. Ctrl+C the watcher, `db.orders.deleteOne({ order_id: "CS-1" })`, restart the watcher **without** `--from-scratch` → the DELETE arrives.

Then run `bash lab/reset.sh` so the database is clean for class. Also open <http://localhost:8888> and run both notebooks once (they need PyMongo installed in dev_env).

Bring a fallback for slide 38 / B2: a recording of the 4 watcher steps (the deck suggests a terminal GIF).

## Environment facts worth knowing

- **Jupyter runs as `developer` via `sudo`**, with `/home/developer` as its root. `sudo` drops the container's environment, so `MONGO_URI` is **not** visible to notebook kernels or the Jupyter terminal. The notebooks fall back to `mongodb://mongo:27017/?directConnection=true`; for scripts, use `docker exec -it dev_env bash` (it has `MONGO_URI`) or `export` it in the Jupyter terminal.
- **`./lab` is mounted at `/home/developer/lab`.** Files the scripts create (`orders.json`, `resume_token.json`) appear in the student's repo folder and are git-ignored. On Linux hosts the folder may be read-only for the `developer` user; `docker exec` runs as root, so the commands in the handout work either way.
- **PyMongo:** `dev_env` has Python 3.10.7 and no PyMongo. PyMongo 4.19.0 requires Python ≥ 3.11, so the handout installs 4.18.3 (latest 3.10-compatible). The APIs used in the lab are the same. The install needs internet; if class Wi-Fi is bad, pre-install on student machines or bring a wheel (`pip download "pymongo==4.18.3" --python-version 3.10 --platform manylinux2014_x86_64 --only-binary=:all:`).
- **`nayacollege/mongo:1.0`** (inspected before writing this lab): MongoDB **6.0.13**, started as a plain `mongod` (standalone, no `--replSet`), no data inside. Change streams and the oplog do not work on it as-is, which is why this lab uses `mongo:8.0` with `--replSet rs0`.
- `rs.printReplicationInfo()` shows a different oplog size on every machine (it defaults to ~5% of free disk). Only the idea matters.

## Timing (60 min)

| Section | Slides | Min | Clock |
|---|---|---|---|
| Setup | 30-31 | 5 | 0:00-0:05 |
| A1 Connect and explore | 18, 22 | 8 | 0:05-0:13 |
| A2 Find the data problems | 4, 11, 15, 26 | 7 | 0:13-0:20 |
| A3 CRUD fixes | 19-21 | 8 | 0:20-0:28 |
| A4 Aggregations | 23-26 | 10 | 0:28-0:38 |
| A5 Index and explain | 27-29 | 5 | 0:38-0:43 |
| B1 PyMongo notebook | 11, 15, 17 | 7 | 0:43-0:50 |
| B2 Change stream | 35-38 | 8 | 0:50-0:58 |
| Wrap-up | 15, 40, 42 | 2 | 0:58-1:00 |
| Optional extras | 39-41 | - | fast students / home |

If the room is behind at 0:38, skip the A5 bonus and the A4 follow-ups; never skip B2 (it carries the lesson's goal).

## Common errors and fixes

| Symptom | Cause | Fix |
|---|---|---|
| `rs.status()` → `not running with --replSet`; PyMongo `OperationFailure: The $changeStream stage is only supported on replica sets` | mongod started without `--replSet` (e.g. an old compose, or `nayacollege/mongo:1.0`) | Use this repo's `docker-compose.yml`: `docker compose down && docker compose up -d` |
| `rs.status()` → `no replset config has been received` / `NotYetInitialized`; mongo never becomes healthy | Replica set not initiated (healthcheck overridden or failed) | `docker exec -it mongo mongosh --eval 'rs.initiate({ _id: "rs0", members: [{ _id: 0, host: "mongo:27017" }] })'`, then `rs.status().members[0].stateStr` → `'PRIMARY'` after a few seconds |
| `ServerSelectionTimeoutError: Could not reach any servers in [('mongo', 27017)]. Replica set is configured with internal hostnames or IPs?` from a laptop | URI without `directConnection=true`: the driver discovers the replica set member `mongo:27017`, which the laptop cannot resolve | Use `mongodb://localhost:27017/?directConnection=true` |
| `ServerSelectionTimeoutError ... localhost:27017` from inside dev_env | Script ran without `MONGO_URI` (Jupyter terminal) and fell back to `localhost` | Use `docker exec -it dev_env bash`, or `export MONGO_URI="mongodb://mongo:27017/?directConnection=true"` |
| `Bind for 0.0.0.0:27017 failed: port is already allocated` | A local MongoDB or an old `mongo` container uses 27017 | `docker ps` → stop it (`docker stop <name>`), or stop the local service. Last resort: change to `"27018:27017"` and use `localhost:27018` on the laptop |
| `Conflict. The container name "/mongo" is already in use` | Old container from another course compose | `docker rm -f mongo dev_env`, then `docker compose up -d` |
| `ModuleNotFoundError: No module named 'pymongo'` (or `'bson'`) | PyMongo not installed in dev_env. It is installed into the container, so `docker compose down` (or anything that recreates `dev_env`) removes it; `stop`/`start` keeps it | `docker exec dev_env pip install "pymongo==4.18.3"` |
| `ERROR: No matching distribution found for pymongo==4.19.0` in dev_env | Python 3.10 in dev_env; 4.19.0 needs 3.11+ | Install 4.18.3 |
| Counts differ from the handout | DB modified (A3 run twice, test docs left behind) or seeded with another script | `bash lab/reset.sh` |
| A4.1 shows `""` instead of `null` | Student skipped the A3 status fix and grouped with `$toLower` | Expected, explained in the handout |
| First explain in A5 shows IXSCAN | Index already created | `db.orders.dropIndex({ "customer.customer_id": 1 })` |
| Watcher restarted but the DELETE never arrives | Started with `--from-scratch` again, or the old watcher was still running and already consumed it | Restart without `--from-scratch`; make sure only one watcher runs |
| `Cannot resume: ChangeStreamHistoryLost` | Token older than the oplog (rare in class: after `reset.sh` or a new volume) | `python3 watch_orders.py --from-scratch` |

## Cut list (from the deck, for the lecture)

Already planned cuts: slides **17, 26, 33**. Beyond those, cut in this order:

1. **Slide 44 - Vocabulary map** is already out of the lecture flow (0 min); just don't show it.
2. **Slide 9 - Forbes** (-2 min): keep Toyota as the single use-case, mention Forbes in one sentence.
3. **Slide 21 - Delete** (-2 min): say one sentence while on slide 20; keep the "deletes are invisible except in the oplog" point for slide 36.
4. **Slide 14 - Modeling by access patterns** (-4 min): fold its one-liner ("schema follows the app's screens") into slide 13.
5. **Slide 34 - Transactions** (-4 min): one sentence on slide 30 ("they require a replica set").
6. **Slide 32 - Read/write concerns** (-2 of 4 min): keep only the "change streams emit majority-committed changes only" line.

**Never cut:** 4, 10, 15, 22, 31, 36-38, 40, 42 - they carry the lesson's goal.

Note: slides 17 and 26 are planned lecture cuts but are practiced in the lab (B1 and A2/A4), so the lab covers them even if the lecture skips them.

## What from Appendix B was left out of the handout

- **Bonus `$jsonSchema` validator (slide 16)** and **Silver view with `$ifNull`**: slide 16 is not on the lab's slide map, and `$ifNull` is not on any slide. B1 does the v1/v2 email flatten in Python instead. Add them back as extras if you want.
- **`$lookup` (slide 25)**: there is no `customers` collection in the dataset, so it is not practiced.
