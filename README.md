# cde_mongodb

Practice lab for the **MongoDB as a Source System** lesson (Big Data Engineering, Naya College).
MongoDB is taught as the *source* of a data pipeline: schema drift, BSON types, nested arrays, the oplog, Change Streams and the Kafka source connector. 150 min lecture + **60 min practice** (this repo).

## What is in this lab and how we use it

| Item | Where | What it covers | Slides | When | Mode |
|---|---|---|---|---|---|
| Setup | [handout → Setup](lab/handout.md#setup-8-min--slides-30-31) | compose up, PyMongo, seed 200 orders, replica set + oplog check | 30-31 | class, 8 min | Together |
| A1 Connect and explore | [handout → A1](lab/handout.md#a1-connect-and-explore-4-min--slides-18-22) | first-five-minutes checklist on an unknown collection | 18, 22 | class, 4 min | Together |
| A2 Find the data problems | [handout → A2](lab/handout.md#a2-find-the-data-problems-6-min--slides-4-11-15-26) | `$type` profiles, missing fields, schema drift, empty arrays | 4, 11, 15, 26 | class, 6 min | Together → Solo |
| A3 CRUD fixes | [handout → A3](lab/handout.md#a3-crud-fixes-7-min--slides-19-21) | silent exclusion, pipeline update, upsert, delete | 19-21 | class, 7 min | Solo |
| A4 Aggregations | [handout → A4](lab/handout.md#a4-aggregations-9-min--slides-23-26) | GROUP BY as pipelines, `$unwind`, duplicates | 23-26 | class, 9 min | Solo |
| A5 Index and explain | [handout → A5](lab/handout.md#a5-index-and-explain-5-min--slides-27-29) | COLLSCAN vs IXSCAN, compound index | 27-29 | class, 5 min | Solo |
| B1 PyMongo notebook | [B1_pymongo_explore.ipynb](lab/notebooks/B1_pymongo_explore.ipynb) | Python types, v1/v2 email flatten, explode items | 11, 15, 17 | class, 7 min | Solo |
| B2 Change stream | [handout → B2](lab/handout.md#b2-change-stream-8-min--slides-35-38), [watch_orders.py](lab/watch_orders.py), [B2_change_stream.ipynb](lab/notebooks/B2_change_stream.ipynb) | insert / update / delete events, resume token | 35-38 | class, 8 min | Solo |
| Wrap-up | [handout → Wrap-up](lab/handout.md#wrap-up-4-min--slides-15-40-42) | source-side checklist, what was hard | 15, 40, 42 | class, 4 min | Together |
| Homework HW1-HW4 | [lab/homework.md](lab/homework.md) | data-quality report, Silver flatten, `$jsonSchema` contract, written questions | 4, 11, 15-17, 25, 26, 31, 37, 40-42 | home, 75-90 min | Homework |
| Optional extras | [homework.md → Optional](lab/homework.md) | connector config, delete semantics, failure table (read-only) | 39-41 | home | Homework |
| Slide map | [docs/slide_to_lab_map.md](docs/slide_to_lab_map.md) | every lab section → slides | - | instructor | - |

## How the 60 minutes go

1. **Together (12 min):** Setup and A1 on the projector, everyone copies along. A2's first query is done together too.
2. **Solo (40 min):** A2 to A5 in mongosh, then B1 and B2 in Jupyter and the terminal. Each section ends with a "Your turn" task; the answer is folded under it. The instructor walks around. A 2-minute buffer before Part B is for catching up.
3. **Wrap-up (4 min, together):** which source-side checklist item (slide 42) you would apply first, and what was hard.

## Homework

About 75-90 minutes in the same environment: two notebooks with built-in self-checks (HW1 data-quality report, HW2 Silver flatten), a `$jsonSchema` contract in mongosh (HW3) and five short written questions (HW4). See [lab/homework.md](lab/homework.md) for tasks, times and what to hand in.

## Quickstart

Requirements: Docker with Docker Compose. Run from the repo folder (`cde_mongodb/`).
**Before class (at home):** run `docker compose pull` and `docker compose up -d` once, so the images are already downloaded.

```bash
# --- 1. On your laptop (host), in the repo folder ---
docker ps -a --filter name=dev_env --format "table {{.Names}}\t{{.Status}}"   # pre-check: an old dev_env listed? see Troubleshooting
docker compose up -d
docker compose ps                                              # wait until mongo shows (healthy)
docker exec dev_env bash /home/developer/lab/setup_dev_env.sh  # installs pymongo==4.18.3; re-run after every "docker compose down"
docker exec -it dev_env bash                                   # opens a shell inside dev_env

# --- 2. Inside dev_env ---
cd /home/developer/lab
python3 seed_orders.py                                         # -> wrote orders.json (200 docs) / inserted 200 docs into shop.orders
exit

# --- 3. Back on your laptop: open mongosh and follow lab/handout.md ---
docker exec -it mongo mongosh
```

Jupyter (notebooks for Part B): <http://localhost:8888>. The `lab/` folder is mounted at `/home/developer/lab`.

Start over at any time: `bash lab/reset.sh` (installs PyMongo if missing, drops `shop`, re-seeds, deletes `resume_token.json`).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `docker compose up -d` → `Conflict. The container name "/dev_env" is already in use` (left over from the Kafka lessons) | Stop any Kafka-lesson work first (ports 22022 and 8888 are shared), then `docker rm -f dev_env` and `docker compose up -d` again. This removes the old container only, not files on your laptop. Same for `"/mongo"`. |
| mongo never becomes `(healthy)`; `rs.status()` → `no replset config has been received` (replica set not initiated) | `docker exec -it mongo mongosh --eval 'rs.initiate({ _id: "rs0", members: [{ _id: 0, host: "mongo:27017" }] })'`, then `rs.status().members[0].stateStr` → `'PRIMARY'` after a few seconds |
| From your laptop: `ServerSelectionTimeoutError: Could not reach any servers in [('mongo', 27017)]` (`directConnection` missing) | Use `mongodb://localhost:27017/?directConnection=true`. Without it the driver looks for the replica set member `mongo:27017`, a name your laptop cannot resolve. |
| Inside dev_env: `ServerSelectionTimeoutError ... localhost:27017` | The script ran without `MONGO_URI` (e.g. in the Jupyter terminal). Use `docker exec -it dev_env bash`, or `export MONGO_URI="mongodb://mongo:27017/?directConnection=true"` |
| `Bind for 0.0.0.0:27017 failed: port is already allocated` (port 27017 in use) | A local MongoDB or an old `mongo` container uses the port: `docker ps`, then `docker stop <name>` (or stop the local MongoDB service), and `docker compose up -d` again |
| `ModuleNotFoundError: No module named 'pymongo'` | `docker exec dev_env bash /home/developer/lab/setup_dev_env.sh` (needed again after every `docker compose down`) |

## Connection rules

| Where | URI |
|---|---|
| Inside `dev_env` (Jupyter, `docker exec -it dev_env bash`) | `mongodb://mongo:27017/?directConnection=true` (preset as `$MONGO_URI` in `docker exec` shells) |
| From your laptop (Compass, local Python) | `mongodb://localhost:27017/?directConnection=true` |
| mongosh | `docker exec -it mongo mongosh` |

Always use `directConnection=true`: the 1-member replica set advertises itself as `mongo:27017`, which a laptop cannot resolve.

## Repo map

```
docker-compose.yml          mongo:8.0 single-node replica set (rs0) + dev_env
lab/
  handout.md                student guide, 60 min, slide references + mode on every section
  homework.md               homework HW1-HW4 (75-90 min) + optional connector questions
  seed_orders.py            builds 200 messy orders (seed 42) into shop.orders
  watch_orders.py           change stream watcher with resume token
  setup_dev_env.sh          installs the pinned PyMongo inside dev_env (run via docker exec)
  reset.sh                  drop shop, re-seed, delete resume_token.json
  notebooks/
    B1_pymongo_explore.ipynb
    B2_change_stream.ipynb
    HW1_data_quality_report.ipynb
    HW2_silver_flatten.ipynb
docs/
  MongoDB_Lesson_Deck_Content.md   lecture deck content (source of truth, 44 slides)
  slide_to_lab_map.md              lab section → slides → what students do
slides/                     lecture PDF (added by the instructor)
```

## Versions

| Component | Version |
|---|---|
| MongoDB | 8.0 (`mongo:8.0`) |
| dev_env | `ofrir119/developer_env:spark340_ssh` (Python 3.10.7, Jupyter Lab) |
| PyMongo | 4.18+ (4.18.3 in dev_env, Python 3.10; 4.19.0 needs Python 3.11+). On a laptop: `pip install "pymongo==4.18.3"` |

## Links

- Student guide: [lab/handout.md](lab/handout.md)
- Homework: [lab/homework.md](lab/homework.md)
- Slide map: [docs/slide_to_lab_map.md](docs/slide_to_lab_map.md)
- Deck content: [docs/MongoDB_Lesson_Deck_Content.md](docs/MongoDB_Lesson_Deck_Content.md)
