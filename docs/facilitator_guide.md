# Facilitator Guide - MongoDB Practice Lab

For the instructor. Student instructions are in [`lab/handout.md`](../lab/handout.md), homework in [`lab/homework.md`](../lab/homework.md) (solutions: [`homework_solutions.md`](homework_solutions.md) - **this repo is public, remove that file before sharing the link**). The slide content and expected outputs come from [`MongoDB_Lesson_Deck_Content.md`](MongoDB_Lesson_Deck_Content.md) (Appendix A + B).

## Message to students before class

> Before the MongoDB lesson, please clone https://github.com/nivbadli1/cde_mongodb and, in that folder, run `docker compose pull` and then `docker compose up -d` at home. This downloads the images (a few GB) so class time isn't spent on downloads. If `up` fails with `Conflict. The container name "/dev_env" is already in use`, see "Troubleshooting" in the README.

## Pre-class checklist (about 10 min, do it on a machine like the students')

```bash
git clone https://github.com/nivbadli1/cde_mongodb && cd cde_mongodb
docker ps -a --filter name=dev_env --format "table {{.Names}}\t{{.Status}}"   # an old dev_env (Kafka lessons)? see Troubleshooting below
docker compose up -d
docker compose ps                                  # mongo: Up (healthy); dev_env: Up
docker exec mongo mongosh --quiet --eval 'db.version() + " " + rs.status().members[0].stateStr'
# → 8.0.x PRIMARY
docker exec dev_env bash /home/developer/lab/setup_dev_env.sh   # → pymongo 4.18.3 OK
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

Then run `bash lab/reset.sh` so the database is clean for class. Also open <http://localhost:8888> and run B1 and B2 once (they need PyMongo installed in dev_env). Fill in the Jupyter password and the hand-in channel in `lab/handout.md` / `lab/homework.md` (they say `<ask the instructor>`).

Bring a fallback for slide 38 / B2: a recording of the 4 watcher steps (the deck suggests a terminal GIF).

### Troubleshooting: container name conflict

`docker compose up -d` fails with `Conflict. The container name "/dev_env" is already in use` (a leftover from the Kafka lessons).
Fix: stop any Kafka-lesson work first (ports 22022 and 8888 are shared), then `docker rm -f dev_env`, then `docker compose up -d` again.
This removes the old container only, not files on the host. (Reproduced and fixed this way while testing the lab.)

## Environment facts worth knowing

- **Jupyter runs as `developer` via `sudo`**, with `/home/developer` as its root. `sudo` drops the container's environment, so `MONGO_URI` is **not** visible to notebook kernels or the Jupyter terminal. The notebooks fall back to `mongodb://mongo:27017/?directConnection=true`; for scripts, use `docker exec -it dev_env bash` (it has `MONGO_URI`) or `export` it in the Jupyter terminal.
- **`./lab` is mounted at `/home/developer/lab`.** Files the scripts create (`orders.json`, `resume_token.json`) appear in the student's repo folder and are git-ignored. On Linux hosts the folder may be read-only for the `developer` user; `docker exec` runs as root, so the commands in the handout work either way.
- **PyMongo:** the lab uses PyMongo 4.18+ (4.18.3 in dev_env, Python 3.10; 4.19.0 needs Python 3.11+). `dev_env` ships without PyMongo; `lab/setup_dev_env.sh` installs `pymongo==4.18.3` (skips if already installed, retries pip 3 times). `lab/reset.sh` calls it too. It must be re-run after `docker compose down`. The install needs internet; if class Wi-Fi is bad, pre-install on student machines or bring a wheel (`pip download "pymongo==4.18.3" --python-version 3.10 --platform manylinux2014_x86_64 --only-binary=:all:`).
- **`nayacollege/mongo:1.0`** (inspected before writing this lab): MongoDB **6.0.13**, started as a plain `mongod` (standalone, no `--replSet`), no data inside. Change streams and the oplog do not work on it as-is, which is why this lab uses `mongo:8.0` with `--replSet rs0`.
- `rs.printReplicationInfo()` shows a different oplog size on every machine (it defaults to ~5% of free disk). Only the idea matters.

## Timing (60 min)

| Section | Slides | Mode | Min | Clock |
|---|---|---|---|---|
| Setup | 30-31 | TOGETHER | 8 | 0:00-0:08 |
| A1 Connect and explore | 18, 22 | TOGETHER | 4 | 0:08-0:12 |
| A2 Find the data problems | 4, 11, 15, 26 | TOGETHER (1st query) → SOLO | 6 | 0:12-0:18 |
| A3 CRUD fixes | 19-21 | SOLO | 7 | 0:18-0:25 |
| A4 Aggregations | 23-26 | SOLO | 9 | 0:25-0:34 |
| A5 Index and explain | 27-29 | SOLO | 5 | 0:34-0:39 |
| Catch-up buffer, switch to Jupyter | - | - | 2 | 0:39-0:41 |
| B1 PyMongo notebook | 11, 15, 17 | SOLO | 7 | 0:41-0:48 |
| B2 Change stream | 35-38 | SOLO | 8 | 0:48-0:56 |
| Wrap-up | 15, 40, 42 | TOGETHER | 4 | 0:56-1:00 |
| Homework HW1-HW4 + optional extras | see homework.md | HOMEWORK | - | at home |

## Run sheet (minute by minute)

**0:00-0:08 Setup - TOGETHER (projector).**
Say: "Today Mongo is a source. First we need a replica set, because the oplog and change streams only exist there (slide 30)."
Do: `docker compose ps` until healthy → `setup_dev_env.sh` → seed inside dev_env → mongosh → `rs.status().members[0].stateStr` → `rs.printReplicationInfo()` and point at "log length start to end" (slide 31).
Check: every laptop shows `inserted 200 docs`. Anyone stuck on a name conflict or port 27017 → the Troubleshooting section, or pair them with a neighbour and fix it during A2.

**0:08-0:12 A1 - TOGETHER.**
Say: "Someone hands you a collection you've never seen. Five-minute checklist."
Do: count → `findOne` → `$sample` twice (shapes differ) → `distinct("status")`. Ask: "the business has 5 statuses, how many do we have?" (14).

**0:12-0:18 A2 - first query TOGETHER, then SOLO.**
Do the missing-status count (7) on the projector, then: "the rest of A2 and the Your turn are yours, 5 minutes."
Circulate: people who type `$type` without quotes, people who read `missing 11` as an error. The Your turn answer is 0 - ask "why does this matter for Silver?"

**0:18-0:25 A3 - SOLO.**
Circulate: the silent-exclusion moment (75 vs 19 strings): ask a student to explain it out loud. Check that everyone ran the pipeline update (`modifiedCount: 30`) - A4 depends on it. Watch for `updateMany` without the `[...]` brackets (that is a normal update, not a pipeline).

**0:25-0:34 A4 - SOLO.**
Circulate: revenue numbers with long trailing zeros are fine. The `$unwind` item is marked "if time remains", so let slow students skip it. If many get 0 or odd numbers in the Your turn, check they grouped on `"$payment.method"` with the `$`.

**0:34-0:39 A5 - SOLO.**
Check: everyone sees COLLSCAN → IXSCAN and can name the three numbers (stage, nReturned, totalDocsExamined). The compound-index Your turn is optional; slow students take it home.

**0:39-0:41 Buffer.**
Everyone opens <http://localhost:8888>. Quick fixes for anyone stuck.

**0:41-0:48 B1 - SOLO.**
Circulate: `No module named 'pymongo'` → run `setup_dev_env.sh` from the host. Ask: "why does the naive email give 93 missing?"

**0:48-0:56 B2 - SOLO.**
This is the lesson's goal: make sure every student sees the DELETE arrive after the restart. Common mistakes: running the watcher in the Jupyter terminal (no `MONGO_URI`), restarting with `--from-scratch`. If terminals are a problem, send them to `B2_change_stream.ipynb`. Fallback: show the recording.

**0:56-1:00 Wrap-up - TOGETHER.**
Show slide 42. Each student names one checklist item they would apply first. Then: "what was hard today?" Take 2-3 answers. Point to `lab/homework.md`.

**If the class is slow:**
- At 0:25 still in A3 → skip the A3 Your turn, do A4 items 1, 2 and 4 only (item 3 `$unwind` → homework).
- At 0:34 still in A4 → do A5 as a 2-minute demo on the projector; the A5 Your turn → homework.
- At 0:48 still in B1 → stop B1 (it is repeated by HW1/HW2) and go to B2. **Never skip B2.**
- No time for the wrap-up discussion → students write their checklist item into the homework answers file (HW4 question 5).

## Common errors and fixes

| Symptom | Cause | Fix |
|---|---|---|
| `rs.status()` → `not running with --replSet`; PyMongo `OperationFailure: The $changeStream stage is only supported on replica sets` | mongod started without `--replSet` (e.g. an old compose, or `nayacollege/mongo:1.0`) | Use this repo's `docker-compose.yml`: `docker compose down && docker compose up -d` |
| `rs.status()` → `no replset config has been received` / `NotYetInitialized`; mongo never becomes healthy | Replica set not initiated (healthcheck overridden or failed) | `docker exec -it mongo mongosh --eval 'rs.initiate({ _id: "rs0", members: [{ _id: 0, host: "mongo:27017" }] })'`, then `rs.status().members[0].stateStr` → `'PRIMARY'` after a few seconds |
| `ServerSelectionTimeoutError: Could not reach any servers in [('mongo', 27017)]. Replica set is configured with internal hostnames or IPs?` from a laptop | URI without `directConnection=true`: the driver discovers the replica set member `mongo:27017`, which the laptop cannot resolve | Use `mongodb://localhost:27017/?directConnection=true` |
| `ServerSelectionTimeoutError ... localhost:27017` from inside dev_env | Script ran without `MONGO_URI` (Jupyter terminal) and fell back to `localhost` | Use `docker exec -it dev_env bash`, or `export MONGO_URI="mongodb://mongo:27017/?directConnection=true"` |
| `Bind for 0.0.0.0:27017 failed: port is already allocated` | A local MongoDB or an old `mongo` container uses 27017 | `docker ps` → stop it (`docker stop <name>`), or stop the local service. Last resort: change to `"27018:27017"` and use `localhost:27018` on the laptop |
| `Conflict. The container name "/dev_env" is already in use` (or `"/mongo"`) | Old container from the Kafka lessons or another course compose | Stop Kafka-lesson work (ports 22022/8888 are shared), `docker rm -f dev_env` (or `mongo`), then `docker compose up -d`. Removes the container only, not host files |
| `ModuleNotFoundError: No module named 'pymongo'` (or `'bson'`) | PyMongo not installed in dev_env. It is installed into the container, so `docker compose down` (or anything that recreates `dev_env`) removes it; `stop`/`start` keeps it | `docker exec dev_env bash /home/developer/lab/setup_dev_env.sh` |
| `ERROR: No matching distribution found for pymongo==4.19.0` in dev_env | Python 3.10 in dev_env; 4.19.0 needs 3.11+ | Use `setup_dev_env.sh` (installs 4.18.3) |
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

- **Bonus `$jsonSchema` validator (slide 16)**: not in class (slide 16 is not on the in-class map). It is **HW3** in the homework.
- **Silver view with `$ifNull`**: `$ifNull` is not on any slide. B1 and HW2 do the v1/v2 email flatten in Python instead.
- **`$lookup` (slide 25)**: there is no `customers` collection in the dataset, so it is not practiced.
