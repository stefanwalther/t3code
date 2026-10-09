#!/usr/bin/env python3
"""Build the interactive threads helper HTML from a t3-open.json snapshot.

Self-contained output: all CSS and JS inline, no network requests, same
T3 semantic token names and component API (variant/size, data-slot
table) as apps/web/src/components/ui so a future port needs no restyle.

Usage: python3 build-t3-helper.py --in t3-open.json --out t3-threads-helper.html
"""
import argparse, json
from pathlib import Path

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>T3 Threads Helper</title>
<style>
:root{
--background:#faf9f5;--foreground:#141413;--muted:#f0eee7;--muted-foreground:#87867f;
--popover:#ffffff;--popover-foreground:#141413;--card:#ffffff;--card-foreground:#141413;
--border:#e6e3da;--input:#e6e3da;--primary:#1c1c1e;--primary-foreground:#faf9f5;
--secondary:#eceae2;--secondary-foreground:#3a3935;--accent:#f0eee7;--accent-foreground:#141413;
--destructive:#b3402a;--destructive-foreground:#fff7f4;--warning:#b8860b;--warning-foreground:#4a3200;
--success:#788c5d;--success-foreground:#14210a;--info:#5b7fa6;--info-foreground:#0e1c2a;
--ring:#d97757;--radius-sm:.25rem;--radius-md:.5rem;--radius-lg:.75rem;--control-radius:.5rem;
}
.dark{--background:#191917;--foreground:#edebe4;--muted:#262522;--muted-foreground:#98968c;
--popover:#212120;--popover-foreground:#edebe4;--card:#212120;--card-foreground:#edebe4;
--border:#35342f;--input:#35342f;--primary:#edebe4;--primary-foreground:#191917;
--secondary:#2c2b27;--secondary-foreground:#edebe4;--accent:#2c2b27;--accent-foreground:#edebe4;
--destructive:#d26a55;--warning:#d4a017;--success:#97ac7c;--info:#8aa8c4;--ring:#e08a66}
@media(prefers-color-scheme:dark){:root:not(.light){--background:#191917;--foreground:#edebe4;--muted:#262522;--muted-foreground:#98968c;--popover:#212120;--popover-foreground:#edebe4;--card:#212120;--card-foreground:#edebe4;--border:#35342f;--input:#35342f;--primary:#edebe4;--primary-foreground:#191917;--secondary:#2c2b27;--secondary-foreground:#edebe4;--accent:#2c2b27;--accent-foreground:#edebe4;--ring:#e08a66}}
*{box-sizing:border-box}
body{margin:0;background:var(--background);color:var(--foreground);font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;font-size:14px;line-height:1.5}
header,main,footer{max-width:1180px;margin:0 auto;padding:0 16px}
.top{display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding-top:20px}
.eyebrow{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted-foreground)}
h1{font-size:24px;margin:4px 0;font-weight:650;letter-spacing:-.01em}
.sub{color:var(--muted-foreground);margin:0 0 12px;max-width:80ch}
/* Button mirrors apps/web buttonVariants: variant + size only, no ad hoc restyle */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;white-space:nowrap;border-radius:var(--control-radius);border:1px solid transparent;font-weight:500;cursor:pointer}
.btn[data-variant=default]{background:var(--primary);color:var(--primary-foreground);border-color:var(--primary)}
.btn[data-variant=outline]{background:var(--popover);color:var(--foreground);border-color:var(--input)}
.btn[data-variant=secondary]{background:var(--secondary);color:var(--secondary-foreground)}
.btn[data-variant=ghost]{background:transparent;color:var(--foreground)}
.btn[data-size=sm]{height:28px;padding:0 10px;font-size:12px}
.btn[data-size=default]{height:32px;padding:0 12px;font-size:13px}
/* Badge mirrors badgeVariants */
.badge{display:inline-flex;align-items:center;gap:4px;white-space:nowrap;border-radius:var(--radius-sm);border:1px solid transparent;font-weight:500}
.badge[data-size=sm]{height:20px;min-width:20px;padding:0 6px;font-size:11px;line-height:1}
.badge[data-variant=default]{background:var(--primary);color:var(--primary-foreground)}
.badge[data-variant=secondary]{background:var(--secondary);color:var(--secondary-foreground)}
.badge[data-variant=outline]{background:var(--background);border-color:var(--input);color:var(--foreground)}
.badge[data-variant=warning]{background:color-mix(in srgb,var(--warning) 8%,transparent);color:var(--warning-foreground)}
.badge[data-variant=error]{background:color-mix(in srgb,var(--destructive) 8%,transparent);color:var(--destructive)}
.badge[data-variant=success]{background:color-mix(in srgb,var(--success) 12%,transparent);color:var(--success-foreground)}
.badge[data-variant=info]{background:color-mix(in srgb,var(--info) 12%,transparent);color:var(--info-foreground)}
/* Input mirrors input-control */
.field{display:inline-flex;width:100%;border-radius:var(--radius-lg);border:1px solid var(--input);background:var(--background);color:var(--foreground)}
.field input,.field select{width:100%;background:transparent;border:0;color:inherit;font:inherit;padding:0 12px;height:32px;outline:none;min-width:0}
.field select{cursor:pointer}
.card{background:var(--card);color:var(--card-foreground);border:1px solid var(--border);border-radius:var(--radius-lg);padding:12px}
.stats{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin:12px 0}
@media(max-width:840px){.stats{grid-template-columns:repeat(2,minmax(0,1fr))}}
.stat .k{font-family:ui-monospace,Menlo,monospace;font-size:11px;color:var(--muted-foreground);text-transform:uppercase;letter-spacing:.06em}
.stat .v{font-size:28px;font-weight:650}
.filters{display:flex;gap:8px;flex-wrap:wrap;background:var(--card);border:1px solid var(--border);border-radius:var(--radius-lg);padding:10px;margin:10px 0;position:sticky;top:0;z-index:5}
.filters .grow{flex:1 1 200px;min-width:170px}
.filters .w160{flex:0 1 160px;min-width:140px}
.check{display:inline-flex;gap:6px;align-items:center;min-height:32px;font-size:13px;color:var(--foreground)}
.grid2{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:12px}
@media(max-width:980px){.grid2{grid-template-columns:minmax(0,1fr)}}
h2{font-size:15px;margin:0 0 8px}
/* Table mirrors table.tsx data-slots */
[data-slot=table-container]{width:100%;overflow-x:auto}
[data-slot=table]{width:100%;border-collapse:collapse;font-size:12px}
[data-slot=table-header] tr{border-bottom:1px solid var(--border)}
[data-slot=table-head]{height:40px;padding:0 8px;text-align:left;font-weight:500;color:var(--foreground);white-space:nowrap}
[data-slot=table-row]{border-bottom:1px solid var(--border)}
[data-slot=table-row]:hover{background:color-mix(in srgb,var(--muted) 50%,transparent)}
[data-slot=table-cell]{padding:8px;vertical-align:top}
.num{text-align:right;font-family:ui-monospace,Menlo,monospace}
.trow{padding:9px 2px;border-top:1px solid var(--border);display:grid;grid-template-columns:48px 48px minmax(0,1fr);gap:10px;font-size:13px}
.trow:first-of-type{border-top:0}
.mono{font-family:ui-monospace,Menlo,monospace}
.mut{color:var(--muted-foreground)}
.rowtitle{font-weight:600}
.port{margin-top:12px}
code{font-family:ui-monospace,Menlo,monospace;font-size:12px}
:focus-visible{outline:2px solid var(--ring);outline-offset:2px}
</style>
</head>
<body>
<header>
<div class="top"><span class="eyebrow">Personal helper · T3 Code style</span>
<span style="flex:1"></span>
<button class="btn" data-variant="outline" data-size="sm" id="themeBtn" type="button">Toggle dark</button>
<button class="btn" data-variant="ghost" data-size="sm" id="resetBtn" type="button">Reset filters</button>
</div>
<h1>What needs picking up</h1>
<p class="sub">Same variant and size names as <code>apps/web/src/components/ui</code>. Tokens use T3 semantic names so this ports to a real route without restyle. Data is a read only temp backup copy.</p>
<div class="mut mono" id="snapLine" style="margin:0 0 12px;font-size:12px"></div>
<div class="stats">
<div class="card stat"><div class="k">Open</div><div class="v" id="sOpen">–</div><div class="mut">in snapshot</div></div>
<div class="card stat"><div class="k">Pickup</div><div class="v" id="sPickup">–</div><div class="mut">input, plan, failed, stale</div></div>
<div class="card stat"><div class="k">Stale over 7d</div><div class="v" id="sStale">–</div><div class="mut">no update</div></div>
<div class="card stat"><div class="k">Oldest open</div><div class="v" id="sOld">–</div><div class="mut">days</div></div>
<div class="card stat"><div class="k">Waiting input</div><div class="v" id="sWait">–</div><div class="mut">pending</div></div>
</div>
</header>
<main>
<div class="filters">
<div class="field grow"><input type="search" id="q" placeholder="Filter titles"></div>
<div class="field w160"><select id="proj"><option value="">All projects</option></select></div>
<div class="field w160"><select id="mach"><option value="">All machines</option></select></div>
<div class="field w160"><select id="loc"><option value="">Any location</option><option value="worktree">Worktree</option><option value="main">Main checkout</option><option value="none">No worktree</option></select></div>
<div class="field w160"><select id="sort"><option value="oldest">Oldest first</option><option value="stale">Stalest first</option><option value="recent">Recent first</option><option value="newest">Newest first</option></select></div>
<label class="check"><input type="checkbox" id="pickupOnly" checked> pickup only</label>
<label class="check"><input type="checkbox" id="staleOnly"> stale 7d+</label>
</div>
<div class="grid2">
<section class="card"><h2>Pickup queue <span class="mut mono" id="pickCount"></span></h2><div id="pickList"></div></section>
<section class="card"><h2>Oldest work <span class="mut mono" id="oldCount"></span></h2><div id="oldList"></div></section>
</div>
<section class="card port"><h2>All open threads <span class="mut mono" id="allCount"></span></h2>
<div data-slot="table-container"><table data-slot="table"><thead data-slot="table-header"><tr><th data-slot="table-head">Age</th><th data-slot="table-head">Stale</th><th data-slot="table-head">Project</th><th data-slot="table-head">Thread</th><th data-slot="table-head" style="text-align:right">Copy</th></tr></thead><tbody id="allBody"></tbody></table></div></section>
</main>
<footer class="mut">Snapshot only. Copy gives thread_id for paste into T3 search.</footer>
<script>
const ROWS = __DATA__;
const proj=document.getElementById("proj");
[...new Set(ROWS.map(r=>r.project))].sort().forEach(p=>{const o=document.createElement("option");o.value=p;o.textContent=p;proj.appendChild(o);});
const mach=document.getElementById("mach");
[...new Set(ROWS.map(r=>r.machine||"local"))].sort().forEach(m=>{const o=document.createElement("option");o.value=m;o.textContent=m;mach.appendChild(o);});
function failed(r){return (r.runs||[]).some(x=>x[0]==="failed"&&x[1]>0);}
function pickup(r){return r.pending_approval_count>0||r.pending_user_input_count>0||r.has_actionable_proposed_plan===1||failed(r)||r.stale_d>=7;}
function badges(r){const b=[];if(r.pending_user_input_count>0)b.push("<span class='badge' data-size='sm' data-variant='error'>input "+r.pending_user_input_count+"</span>");if(r.pending_approval_count>0)b.push("<span class='badge' data-size='sm' data-variant='error'>approval "+r.pending_approval_count+"</span>");if(r.has_actionable_proposed_plan===1)b.push("<span class='badge' data-size='sm' data-variant='success'>plan</span>");if(failed(r))b.push("<span class='badge' data-size='sm' data-variant='warning'>failed</span>");if(r.stale_d>=7)b.push("<span class='badge' data-size='sm' data-variant='warning'>stale "+r.stale_d+"d</span>");return b.length?b.join(" "):"<span class='badge' data-size='sm' data-variant='secondary'>steady</span>";}
function esc(s){return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function list(ignore){const q=document.getElementById("q").value.toLowerCase(),p=proj.value,m=mach.value,l=document.getElementById("loc").value,s=document.getElementById("sort").value,po=document.getElementById("pickupOnly").checked&&!ignore,so=document.getElementById("staleOnly").checked;let o=ROWS.filter(r=>(!p||r.project===p)&&(!m||(r.machine||"local")===m)&&(!l||r.worktree_kind===l)&&(!q||r.title.toLowerCase().includes(q))&&(!po||pickup(r))&&(!so||r.stale_d>=7));const by={oldest:(a,b)=>a.created_at.localeCompare(b.created_at),newest:(a,b)=>b.created_at.localeCompare(a.created_at),stale:(a,b)=>b.stale_d-a.stale_d,recent:(a,b)=>b.updated_at.localeCompare(a.updated_at)}[s];return o.sort(by);}
function item(r){return "<div class='trow'><div class='num'><b>"+r.age_d+"d</b><br><span class='mut'>age</span></div><div class='num'><b>"+r.stale_d+"d</b><br><span class='mut'>stale</span></div><div><div class='rowtitle'>"+esc(r.title)+"</div><div class='mut mono'>"+esc(r.project)+" · "+r.updated_at.slice(0,10)+"</div><div style='margin-top:4px'>"+badges(r)+"</div></div></div>";}
function render(){const all=list(true),pk=list(false).filter(pickup);const pl=pk.slice(0,15),ol=all.slice(0,15);
const byMach={};ROWS.forEach(r=>{const m=r.machine||"local";if(!byMach[m]||(r.exported_at||"")>byMach[m].at)byMach[m]={at:r.exported_at||"?",n:0};byMach[m].n++;});
document.getElementById("snapLine").textContent="Snapshots: "+Object.keys(byMach).sort().map(m=>m+" "+byMach[m].at.slice(0,16).replace("T"," ")+" ("+byMach[m].n+")").join(" · ");
document.getElementById("sOpen").textContent=ROWS.length;
document.getElementById("sPickup").textContent=ROWS.filter(pickup).length;
document.getElementById("sStale").textContent=ROWS.filter(r=>r.stale_d>=7).length;
document.getElementById("sOld").textContent=Math.max.apply(null,ROWS.map(r=>r.age_d))+"d";
document.getElementById("sWait").textContent=ROWS.filter(r=>r.pending_user_input_count>0).length;
document.getElementById("pickCount").textContent=pl.length+" of "+pk.length;
document.getElementById("oldCount").textContent=ol.length+" of "+all.length;
document.getElementById("allCount").textContent=all.length;
document.getElementById("pickList").innerHTML=pl.map(item).join("")||"<p class='mut'>No pickup match.</p>";
document.getElementById("oldList").innerHTML=ol.map(item).join("");
document.getElementById("allBody").innerHTML=all.map(r=>"<tr data-slot='table-row'><td data-slot='table-cell' class='num'>"+r.age_d+"d</td><td data-slot='table-cell' class='num'>"+r.stale_d+"d</td><td data-slot='table-cell'>"+esc(r.project)+"</td><td data-slot='table-cell'><b>"+esc(r.title)+"</b><br><span class='mut mono'>"+r.thread_id.slice(0,8)+" · "+badges(r)+"</span></td><td data-slot='table-cell' style='text-align:right'><button class='btn' data-variant='outline' data-size='sm' data-id='"+r.thread_id+"'>copy</button></td></tr>").join("");}
document.addEventListener("input",e=>{if(e.target.id==="q")render();});
document.addEventListener("change",render);
document.getElementById("resetBtn").addEventListener("click",()=>{document.getElementById("q").value="";proj.value="";mach.value="";document.getElementById("loc").value="";document.getElementById("sort").value="oldest";document.getElementById("pickupOnly").checked=false;document.getElementById("staleOnly").checked=false;render();});
document.getElementById("themeBtn").addEventListener("click",()=>document.documentElement.classList.toggle("dark"));
document.addEventListener("click",e=>{const b=e.target.closest("[data-id]");if(!b)return;navigator.clipboard.writeText(b.dataset.id).then(()=>{b.textContent="copied";setTimeout(()=>b.textContent="copy",1100);});});
render();
</script>
</body>
</html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="t3-open.json")
    ap.add_argument("--out", dest="out", default="t3-threads-helper.html")
    a = ap.parse_args()
    rows = json.loads(Path(a.inp).read_text())
    data_js = json.dumps(rows, separators=(",", ":"))
    Path(a.out).write_text(TEMPLATE.replace("__DATA__", data_js))
    print(f"wrote {a.out} rows={len(rows)}")


if __name__ == "__main__":
    main()
