#!/usr/bin/env bash
# setup_dev_env.sh - install the pinned PyMongo inside the dev_env container.
#
# Run from the repo folder on your laptop (host):
#   docker exec dev_env bash /home/developer/lab/setup_dev_env.sh
#
# Why a pinned version: dev_env has Python 3.10, and PyMongo 4.19.0 needs Python 3.11+.
# 4.18.3 is the latest PyMongo that supports Python 3.10 (PyMongo 4.18+ is what the lab needs).
#
# The install lives inside the container, so run this again after every
# "docker compose down" (docker compose stop/start keeps it). Safe to re-run.
set -euo pipefail

PYMONGO_VERSION="4.18.3"

installed="$(python3 -c 'import pymongo; print(pymongo.version)' 2>/dev/null || true)"
if [ "$installed" = "$PYMONGO_VERSION" ]; then
  echo "pymongo $installed already installed - nothing to do."
  exit 0
fi

echo "Installing pymongo==$PYMONGO_VERSION for $(python3 --version)..."
for attempt in 1 2 3; do
  if pip install --quiet --disable-pip-version-check "pymongo==$PYMONGO_VERSION"; then
    break
  fi
  if [ "$attempt" = 3 ]; then
    echo "pip install failed 3 times - check the internet connection and run this script again." >&2
    exit 1
  fi
  echo "pip install failed (attempt $attempt), retrying in 5 s..." >&2
  sleep 5
done

python3 -c 'import pymongo; print("pymongo", pymongo.version, "OK")'
