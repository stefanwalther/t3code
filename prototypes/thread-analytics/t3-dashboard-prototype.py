#!/usr/bin/env python3
"""T3 Code thread metrics prototype - external, read-only.
Copies statev2.sqlite to temp (never opens live DB read-write),
then outputs open threads, per-project, settled/closed per day.
Usage: python3 t3-dashboard-prototype.py [--db ~/.t3/userdata/statev2.sqlite] [--out metrics.json]
"""
import argparse, json, shutil, sqlite3, sys, tempfile, os
from pathlib import Path

def safe_copy(src: Path) -> Path:
    tmp = Path(tempfile.mkstemp(suffix="-statev2.sqlite")[1])
    # sqlite3 backup is safer than file copy for a live DB
    src_uri = f"file:{src}?mode=ro"
    try:
        s = sqlite3.connect(src_uri, uri=True, timeout=5)
        d = sqlite3.connect(str(tmp), timeout=5)
        s.backup(d)
        s.close(); d.close()
    except Exception:
        tmp.unlink(missing_ok=True)
        # fallback: filesystem copy (may fail if locked)
        tmp2 = Path(tempfile.mkstemp(suffix="-statev2.sqlite")[1])
        shutil.copyfile(src, tmp2)
        return tmp2
    return tmp

QUERIES = {
    "totals": """
      SELECT COUNT(*) AS total,
        SUM(CASE WHEN deleted_at IS NULL AND archived_at IS NULL AND settled_at IS NULL THEN 1 ELSE 0 END) AS open_threads,
        SUM(CASE WHEN settled_at IS NOT NULL AND deleted_at IS NULL THEN 1 ELSE 0 END) AS settled,
        SUM(CASE WHEN archived_at IS NOT NULL AND deleted_at IS NULL THEN 1 ELSE 0 END) AS archived
      FROM projection_threads""",
    "open_per_project": """
      SELECT p.title AS project, COUNT(*) AS open_n
      FROM projection_threads t JOIN projection_projects p ON p.project_id=t.project_id
      WHERE t.deleted_at IS NULL AND t.archived_at IS NULL AND t.settled_at IS NULL
      GROUP BY p.title ORDER BY open_n DESC""",
    "total_per_project": """
      SELECT p.title AS project, COUNT(*) AS total_n,
        SUM(CASE WHEN t.settled_at IS NULL AND t.archived_at IS NULL AND t.deleted_at IS NULL THEN 1 ELSE 0 END) AS open_n
      FROM projection_threads t JOIN projection_projects p ON p.project_id=t.project_id
      WHERE t.deleted_at IS NULL GROUP BY p.title ORDER BY total_n DESC LIMIT 30""",
    "settled_per_day": """
      SELECT substr(settled_at,1,10) AS day, COUNT(*) AS n
      FROM projection_threads WHERE settled_at IS NOT NULL
      GROUP BY day ORDER BY day DESC LIMIT 60""",
    "archived_per_day": """
      SELECT substr(archived_at,1,10) AS day, COUNT(*) AS n
      FROM projection_threads WHERE archived_at IS NOT NULL
      GROUP BY day ORDER BY day DESC LIMIT 60""",
    "created_per_day": """
      SELECT substr(created_at,1,10) AS day, COUNT(*) AS n
      FROM projection_threads WHERE deleted_at IS NULL
      GROUP BY day ORDER BY day DESC LIMIT 60""",
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.expanduser("~/.t3/userdata/statev2.sqlite"))
    ap.add_argument("--out", default="metrics.json")
    a = ap.parse_args()
    src = Path(a.db)
    if not src.exists():
        sys.exit(f"DB not found: {src}")
    print(f"copying {src} ({src.stat().st_size/1e9:.2f} GB) via sqlite backup...", flush=True)
    tmp = safe_copy(src)
    try:
        con = sqlite3.connect(f"file:{tmp}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        out = {}
        for k, q in QUERIES.items():
            out[k] = [dict(r) for r in con.execute(q).fetchall()]
        con.close()
    finally:
        tmp.unlink(missing_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=2))
    t = out["totals"][0]
    print(f"total={t['total']} open={t['open_threads']} settled={t['settled']} archived={t['archived']}")
    print("top open per project:")
    for r in out["open_per_project"][:10]:
        print(f"  {r['open_n']:3d}  {r['project']}")
    print(f"wrote {a.out}")

if __name__ == "__main__":
    main()
