#!/usr/bin/env bash
# reset.sh - put the lab back to its starting state.
#   1. drop the "shop" database (orders + any indexes you created)
#   2. re-seed the 200 messy orders (seed 42)
#   3. delete resume_token.json so watch_orders.py starts fresh
#
# Run from the repo root on your laptop:   bash lab/reset.sh
# (it uses "docker exec", so the containers must be running: docker compose up -d)
set -euo pipefail

echo "1/3 Dropping database 'shop'..."
docker exec mongo mongosh --quiet --eval 'db.getSiblingDB("shop").dropDatabase()'

echo "2/3 Seeding shop.orders..."
docker exec -w /home/developer/lab dev_env python3 seed_orders.py

echo "3/3 Removing resume_token.json..."
docker exec dev_env rm -f /home/developer/lab/resume_token.json

echo "Done. Check: docker exec mongo mongosh --quiet shop --eval 'db.orders.countDocuments({})'   # -> 200"
