# cde_mongodb

Practice lab for the **MongoDB as a Source System** lesson (Big Data Engineering, Naya College).
MongoDB is taught as the *source* of a data pipeline: schema drift, BSON types, nested arrays, the oplog, Change Streams and the Kafka source connector. 150 min lecture + **60 min practice** (this repo).

## Quickstart

Requirements: Docker with Docker Compose. Run from the repo folder (`cde_mongodb/`).

```bash
# --- 1. On your laptop (host), in the repo folder ---
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
  handout.md                student guide, 60 min, slide references on every section
  seed_orders.py            builds 200 messy orders (seed 42) into shop.orders
  watch_orders.py           change stream watcher with resume token
  setup_dev_env.sh          installs the pinned PyMongo inside dev_env (run via docker exec)
  reset.sh                  drop shop, re-seed, delete resume_token.json
  notebooks/
    B1_pymongo_explore.ipynb
    B2_change_stream.ipynb
docs/
  MongoDB_Lesson_Deck_Content.md   lecture deck content (source of truth, 44 slides)
  facilitator_guide.md             pre-class checklist, timing, common errors, cut list
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
- Instructor guide: [docs/facilitator_guide.md](docs/facilitator_guide.md)
- Slide map: [docs/slide_to_lab_map.md](docs/slide_to_lab_map.md)
- Deck content: [docs/MongoDB_Lesson_Deck_Content.md](docs/MongoDB_Lesson_Deck_Content.md)
