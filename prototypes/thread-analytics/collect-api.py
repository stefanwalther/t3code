#!/usr/bin/env python3
"""Collect open-thread snapshots from T3 servers over HTTP and merge them.

Each T3 server exposes GET /api/orchestration/shell (threads plus
archivedThreads) behind a bearer token with the orchestration:read
scope. This script polls every configured machine, normalizes rows to
the same shape t3-open-export.py produces, and writes the merged file
that build-t3-helper.py renders. No sqlite copying, no SSH.

Config lives OUTSIDE Dropbox at ~/.config/t3-dashboard/endpoints.json
(mode 0600, tokens are secret material):
  {"machines": {"mbp-swr-2024-m4": {"base_url": "http://localhost:3773", "token": "..."}}}

Mint a token per machine with:
  t3 auth session issue --scope orchestration:read --ttl 90d \\
    --label thread-dashboard-collector --subject thread-dashboard --token-only

Usage: python3 collect-api.py --out /tmp/t3-open-all.json [--html out.html]
"""
import argparse, datetime, json, os, sys, urllib.request, urllib.error
from pathlib import Path

CONFIG = Path(os.path.expanduser("~/.config/t3-dashboard/endpoints.json"))
PROTOCOL_HEADER = "x-t3-orchestration-protocol"
PROTOCOL_VERSION = "2"


def api_get(base_url: str, path: str, token: str | None, timeout: int = 10):
    req = urllib.request.Request(base_url.rstrip("/") + path)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header(PROTOCOL_HEADER, PROTOCOL_VERSION)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{path} -> HTTP {e.code}")
    except Exception as e:
        raise RuntimeError(f"{path} -> {type(e).__name__}: {e}")


def worktree_kind(path: str | None) -> str:
    if not path:
        return "none"
    return "worktree" if "/.t3/worktrees/" in path else "main"


def normalize(t: dict, titles: dict, machine: str, exported_at: str) -> dict | None:
    # The shell carries the whole tree including subagent children. The
    # dashboard tracks user threads, so only top-level threads count.
    if (t.get("lineage") or {}).get("parentThreadId"):
        return None
    if t.get("deletedAt") or t.get("archivedAt") or t.get("settledAt"):
        return None
    if t.get("settledOverride") == "settled":
        return None
    created = t.get("createdAt", "")
    updated = t.get("updatedAt", "")
    pending = t.get("pendingRuntimeRequest")
    status = t.get("status", "idle")
    last_error = t.get("lastError")
    failed = status == "failed" or bool(last_error)
    try:
        age_d = (datetime.datetime.now(datetime.timezone.utc)
                 - datetime.datetime.fromisoformat(created.replace("Z", "+00:00"))).days
        stale_d = (datetime.datetime.now(datetime.timezone.utc)
                   - datetime.datetime.fromisoformat(updated.replace("Z", "+00:00"))).days
    except ValueError:
        age_d, stale_d = 0, 0
    pid = t.get("projectId", "")
    return {
        "thread_id": t.get("id", ""),
        "project": titles.get(pid, pid[:8] or "unknown"),
        "title": t.get("title", ""),
        "created_at": created,
        "updated_at": updated,
        "latest_user_message_at": t.get("latestUserMessageAt"),
        "pending_approval_count": 0,
        "pending_user_input_count": 0,
        "waiting": pending is not None,
        "waiting_kind": (pending or {}).get("kind"),
        "has_actionable_proposed_plan": 1 if t.get("hasActionableProposedPlan") else 0,
        "worktree_path": t.get("worktreePath"),
        "age_d": age_d,
        "stale_d": stale_d,
        "runs": [],
        "failed": failed,
        "last_error": last_error,
        "status": status,
        "exported_at": exported_at,
        "machine": machine,
        "worktree_kind": worktree_kind(t.get("worktreePath")),
        "source": "api",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="t3-open-all.json")
    ap.add_argument("--config", default=str(CONFIG))
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text())
    machines = cfg.get("machines", {})
    if not machines:
        sys.exit(f"no machines configured in {a.config}")
    if os.stat(a.config).st_mode & 0o077:
        print(f"warning: {a.config} is readable beyond owner, run chmod 600", flush=True)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows, seen = [], []
    for name, m in machines.items():
        base, token = m["base_url"], m.get("token")
        if not token:
            print(f"skip {name}: no token", flush=True)
            continue
        try:
            desc = api_get(base, "/.well-known/t3/environment", None)
            machine = desc.get("label", name)
            proj = api_get(base, "/api/projects", token)
            plist = proj.get("projects", proj if isinstance(proj, list) else [])
            titles = {p.get("id"): p.get("title", p.get("id", "")) for p in plist if p.get("id")}
            shell = api_get(base, "/api/orchestration/shell", token)
            n = 0
            for t in shell.get("threads", []) + shell.get("archivedThreads", []):
                r = normalize(t, titles, machine, now)
                if r:
                    rows.append(r)
                    n += 1
            seen.append(machine)
            print(f"{machine}: open={n}", flush=True)
        except RuntimeError as e:
            print(f"{name}: unreachable ({e}), skipped", flush=True)
    rows.sort(key=lambda r: r["created_at"])
    Path(a.out).write_text(json.dumps(rows))
    print(f"threads={len(rows)} machines={sorted(set(seen))} (M1 excluded)")
    print(f"wrote {a.out} (personal data, do not commit)")


if __name__ == "__main__":
    main()
