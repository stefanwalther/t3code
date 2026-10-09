#!/usr/bin/env python3
"""Export the open-thread work list that feeds build-t3-helper.py.

Read-only: copies statev2.sqlite via the SQLite backup API to temp and
queries the copy. Output contains personal thread titles, keep it out
of git (see .gitignore in this folder).

Usage: python3 t3-open-export.py [--db ~/.t3/userdata/statev2.sqlite] [--out t3-open.json]
"""
import argparse, json, shutil, sqlite3, socket, sys, tempfile, os
import datetime
from pathlib import Path

QUERY = """
SELECT t.thread_id, p.title AS project, t.title, t.created_at, t.updated_at,
  t.latest_user_message_at, t.pending_approval_count, t.pending_user_input_count,
  t.has_actionable_proposed_plan, t.worktree_path,
  CAST((julianday('now')-julianday(t.created_at)) AS INT) AS age_d,
  CAST((julianday('now')-julianday(t.updated_at)) AS INT) AS stale_d
FROM projection_threads t
JOIN projection_projects p ON p.project_id = t.project_id
WHERE t.deleted_at IS NULL AND t.archived_at IS NULL AND t.settled_at IS NULL
ORDER BY t.created_at ASC
"""

RUNS_QUERY = """
SELECT thread_id, status, COUNT(*) AS n
FROM orchestration_v2_projection_runs
GROUP BY thread_id, status
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.expanduser("~/.t3/userdata/statev2.sqlite"))
    ap.add_argument("--out", default="t3-open.json")
    a = ap.parse_args()
    src = Path(a.db)
    if not src.exists():
        sys.exit(f"DB not found: {src}")
    tmp = Path(tempfile.mkstemp(suffix="-statev2.sqlite")[1])
    s = sqlite3.connect(f"file:{src}?mode=ro", uri=True, timeout=5)
    d = sqlite3.connect(str(tmp), timeout=5)
    try:
        s.backup(d)
    finally:
        s.close(); d.close()
    try:
        con = sqlite3.connect(f"file:{tmp}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        rows = [dict(r) for r in con.execute(QUERY).fetchall()]
        runs = {}
        for r in con.execute(RUNS_QUERY).fetchall():
            runs.setdefault(r["thread_id"], []).append([r["status"], r["n"]])
        con.close()
    finally:
        tmp.unlink(missing_ok=True)
    for r in rows:
        r["runs"] = runs.get(r["thread_id"], [])
        r["exported_at"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        # Single-server DBs only know their own host. Recording the machine
        # now keeps the field stable for later merged multi-machine snapshots.
        # Match the environment display name T3 shows (LocalHostName,
        # without the .local suffix that socket.gethostname() carries).
        r["machine"] = socket.gethostname().removesuffix(".local")
        path = r.get("worktree_path") or ""
        if not path:
            r["worktree_kind"] = "none"
        elif "/.t3/worktrees/" in path:
            r["worktree_kind"] = "worktree"
        else:
            r["worktree_kind"] = "main"
    Path(a.out).write_text(json.dumps(rows))
    pickup = sum(1 for r in rows if (
        r["pending_approval_count"] > 0 or r["pending_user_input_count"] > 0
        or r["has_actionable_proposed_plan"] == 1 or r["stale_d"] >= 7
        or any(s == "failed" for s, _ in r["runs"])))
    print(f"open={len(rows)} pickup={pickup}")
    print(f"wrote {a.out} (personal data, do not commit)")

if __name__ == "__main__":
    main()
