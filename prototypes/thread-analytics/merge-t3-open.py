#!/usr/bin/env python3
"""Merge per-machine t3-open.json snapshots into one multi-machine file.

Each machine runs t3-open-export.py locally and sends its small JSON
here. Rows already carry their machine name, so the dashboard machine
filter works unchanged on the merged output.

Usage: python3 merge-t3-open.py --out t3-open-all.json a.json b.json
"""
import argparse, json
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="t3-open-all.json")
    ap.add_argument("inputs", nargs="+")
    a = ap.parse_args()
    merged = {}
    for f in a.inputs:
        for r in json.loads(Path(f).read_text()):
            merged[r["thread_id"]] = r
    rows = sorted(merged.values(), key=lambda r: r["created_at"])
    Path(a.out).write_text(json.dumps(rows))
    machines = sorted({r.get("machine", "local") for r in rows})
    print(f"threads={len(rows)} machines={machines}")
    print(f"wrote {a.out} (personal data, do not commit)")

if __name__ == "__main__":
    main()
