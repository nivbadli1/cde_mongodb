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
