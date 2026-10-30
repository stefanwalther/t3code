#!/usr/bin/env bash
# Collect multi-machine T3 thread snapshots via Dropbox shuttle.
# Run on ANY machine: exports local snapshot, merges all synced snapshots,
# rebuilds the helper HTML. No SSH needed, Dropbox sync carries the files.
# Usage: bash prototypes/thread-analytics/collect-all.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SHUTTLE="$HOME/Library/CloudStorage/Dropbox/shared_storage/t3-snapshots"
ARTIFACTS="$HOME/Library/CloudStorage/Dropbox/shared_storage/tmp/html-artifacts"
HOST="$(scutil --get LocalHostName 2>/dev/null || hostname -s 2>/dev/null || hostname)"
HOST="${HOST%.local}"
mkdir -p "$SHUTTLE" "$ARTIFACTS"
echo "== export $HOST =="
python3 "$HERE/t3-open-export.py" --out "$SHUTTLE/$HOST.json"
echo "== merge ($(ls "$SHUTTLE"/*.json 2>/dev/null | wc -l | tr -d ' ') snapshots) =="
python3 "$HERE/merge-t3-open.py" --out /tmp/t3-open-all.json "$SHUTTLE"/*.json
echo "== build =="
python3 "$HERE/build-t3-helper.py" --in /tmp/t3-open-all.json --out "$ARTIFACTS/t3-threads-helper.html"
echo "done: $ARTIFACTS/t3-threads-helper.html"
