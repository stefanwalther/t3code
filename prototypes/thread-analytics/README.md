# Thread analytics prototype (INTERNAL, DO NOT UPSTREAM)

Personal helper for answering "what needs picking up" across T3 Code
threads: open count, per-project breakdown, oldest work, stale threads,
pending input and actionable plans.

This lives on the fork only, on branch
`t3code/prototype-thread-analytics-dashboard`, so the approach can be
tested outside the product before any real PR proposal. It deliberately
bends the "no scratch files in the repo" rule with maintainer sign-off;
nothing here ships in the app.

## Read-only by design

The scripts never open the live database read-write. They copy
`~/.t3/userdata/statev2.sqlite` via the SQLite backup API to temp and
query the copy. Generated `*.json`, `*.html` and `*.sqlite` files are
gitignored: they contain personal thread titles and must never be
committed.

## Usage

```bash
python3 prototypes/thread-analytics/t3-dashboard-prototype.py --out /tmp/t3-metrics.json
python3 prototypes/thread-analytics/t3-open-export.py --out /tmp/t3-open.json
python3 prototypes/thread-analytics/build-t3-helper.py --in /tmp/t3-open.json --out /tmp/t3-threads-helper.html
```

## Multiple machines

One server only ever sees its own threads. Run `t3-open-export.py`
on each machine, collect the small JSON files in one place, then:

```bash
python3 prototypes/thread-analytics/merge-t3-open.py --out /tmp/t3-open-all.json m4.json m1.json
python3 prototypes/thread-analytics/build-t3-helper.py --in /tmp/t3-open-all.json --out /tmp/t3-threads-helper.html
```

Open means `deleted_at IS NULL AND archived_at IS NULL AND
settled_at IS NULL` on `projection_threads`. Pickup means pending
approval or input, an actionable plan, a failed run, or stale 7 days
or more. Each T3 server only knows its own threads, so no machine
column exists in the database; the export records the local hostname
and a worktree location (`worktree`, `main`, `none`) per thread, and
the dashboard filters on both. Merged snapshots from several machines
work with the same fields.

## Style

The dashboard HTML mirrors the app from the start so a future proposal
ports cleanly: T3 semantic token names (`background`, `foreground`,
`muted`, `primary`, `border`, `input`, `ring`, `control-radius`),
`dark` class override, and the same component API as
`apps/web/src/components/ui` (Button, Badge, Input and Table variant
and size names, `data-slot` table structure). Layout classes only on
parents, no component restyle.

## PR port map (if this ever graduates)

- Pure query in `apps/server/src/threads/ThreadMetricsService.ts`
  reading the same projections (service method, thin transport).
- Contract in `packages/contracts/src/threadMetrics.ts`.
- Route in `apps/web/src/routes/threads.metrics.tsx` reusing the
  existing UI variants.
