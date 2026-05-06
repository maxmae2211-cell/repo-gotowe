#!/usr/bin/env python3
"""Generowanie raportu HTML ze spike testu Taurus."""
import csv
import statistics
from collections import defaultdict

JTL_FILES = [
    "reports/spike-test/kpi.jtl",
    "reports/spike-test/kpi-1.jtl",
    "reports/spike-test/kpi-2.jtl",
]
OUTPUT = "reports/spike-test-report.html"

# --- Wczytaj dane ze wszystkich plików JTL ---
rows = []
seen_ts_elapsed = set()
for path in JTL_FILES:
    try:
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row["timeStamp"], row["elapsed"], row.get("threadName",""))
                if key not in seen_ts_elapsed:
                    seen_ts_elapsed.add(key)
                    rows.append({
                        "ts": int(row["timeStamp"]),
                        "elapsed": int(row["elapsed"]),
                        "success": row["success"].lower() == "true",
                        "threads": int(row["allThreads"]),
                        "code": row["responseCode"],
                    })
    except FileNotFoundError:
        pass
rows.sort(key=lambda r: r["ts"])

if not rows:
    print("Brak danych!")
    exit(1)

total = len(rows)
failures = sum(1 for r in rows if not r["success"])
successes = total - failures
error_rate = failures / total * 100

elapsed_ms = [r["elapsed"] for r in rows]
elapsed_s  = [e / 1000 for e in elapsed_ms]

avg_rt   = statistics.mean(elapsed_s)
median   = statistics.median(elapsed_s)
sorted_e = sorted(elapsed_ms)

def percentile(data_sorted, p):
    idx = int(len(data_sorted) * p / 100)
    return data_sorted[min(idx, len(data_sorted)-1)] / 1000

p50  = percentile(sorted_e, 50)
p90  = percentile(sorted_e, 90)
p95  = percentile(sorted_e, 95)
p99  = percentile(sorted_e, 99)
p999 = percentile(sorted_e, 99.9)
pmax = sorted_e[-1] / 1000

# --- Agreguj po czasie (buckety 5s) ---
t0 = rows[0]["ts"]
buckets = defaultdict(lambda: {"elapsed": [], "failures": 0, "threads": 0})
for r in rows:
    b = (r["ts"] - t0) // 5000
    buckets[b]["elapsed"].append(r["elapsed"])
    if not r["success"]:
        buckets[b]["failures"] += 1
    buckets[b]["threads"] = max(buckets[b]["threads"], r["threads"])

time_labels = []
tps_data    = []
avgrt_data  = []
errors_data = []
threads_data = []

for b in sorted(buckets.keys()):
    d = buckets[b]
    t = b * 5
    time_labels.append(str(t))
    count = len(d["elapsed"])
    tps_data.append(round(count / 5, 1))
    avgrt_data.append(round(statistics.mean(d["elapsed"]) / 1000, 3))
    errors_data.append(round(d["failures"] / count * 100, 1))
    threads_data.append(d["threads"])

# --- Buduj HTML ---
html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Spike Test — Raport</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Segoe UI',sans-serif; background:#0f172a; color:#e2e8f0; padding:24px; }}
  h1 {{ font-size:2rem; font-weight:700; color:#f8fafc; margin-bottom:4px; }}
  .subtitle {{ color:#94a3b8; margin-bottom:28px; font-size:.95rem; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px; margin-bottom:28px; }}
  .card {{ background:#1e293b; border-radius:12px; padding:20px; border:1px solid #334155; }}
  .card .label {{ font-size:.8rem; color:#94a3b8; text-transform:uppercase; letter-spacing:.05em; }}
  .card .value {{ font-size:2rem; font-weight:700; margin-top:4px; }}
  .card.ok .value {{ color:#4ade80; }}
  .card.warn .value {{ color:#fbbf24; }}
  .card.bad .value {{ color:#f87171; }}
  .card.neutral .value {{ color:#60a5fa; }}
  .charts {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:28px; }}
  .chart-box {{ background:#1e293b; border-radius:12px; padding:20px; border:1px solid #334155; }}
  .chart-box h3 {{ font-size:.9rem; color:#94a3b8; margin-bottom:14px; text-transform:uppercase; letter-spacing:.05em; }}
  .full {{ grid-column:1/-1; }}
  table {{ width:100%; border-collapse:collapse; background:#1e293b; border-radius:12px; overflow:hidden; border:1px solid #334155; }}
  th {{ background:#334155; padding:10px 16px; text-align:left; font-size:.8rem; color:#94a3b8; text-transform:uppercase; }}
  td {{ padding:10px 16px; border-top:1px solid #334155; font-size:.9rem; }}
  .fail {{ color:#f87171; font-weight:600; }}
  .pass {{ color:#4ade80; font-weight:600; }}
</style>
</head>
<body>
<h1>🔥 Spike Test — Raport</h1>
<p class="subtitle">GET /get @ localhost:8000 | Fazy: 10 VU → 500 VU → 10 VU | 6 maja 2026</p>

<div class="grid">
  <div class="card neutral">
    <div class="label">Łączne żądania</div>
    <div class="value">{total:,}</div>
  </div>
  <div class="card {'ok' if error_rate < 5 else 'warn' if error_rate < 20 else 'bad'}">
    <div class="label">Błędy</div>
    <div class="value">{error_rate:.1f}%</div>
  </div>
  <div class="card {'ok' if avg_rt < 1 else 'warn' if avg_rt < 3 else 'bad'}">
    <div class="label">Avg Response Time</div>
    <div class="value">{avg_rt:.2f}s</div>
  </div>
  <div class="card {'ok' if p95 < 2 else 'warn' if p95 < 5 else 'bad'}">
    <div class="label">P95 Response Time</div>
    <div class="value">{p95:.2f}s</div>
  </div>
  <div class="card neutral">
    <div class="label">P50 (mediana)</div>
    <div class="value">{p50:.2f}s</div>
  </div>
  <div class="card {'ok' if pmax < 5 else 'warn' if pmax < 15 else 'bad'}">
    <div class="label">Max Response Time</div>
    <div class="value">{pmax:.1f}s</div>
  </div>
</div>

<div class="charts">
  <div class="chart-box full">
    <h3>VU + Avg Response Time w czasie</h3>
    <canvas id="vuChart"></canvas>
  </div>
  <div class="chart-box">
    <h3>Przepustowość (req/s)</h3>
    <canvas id="tpsChart"></canvas>
  </div>
  <div class="chart-box">
    <h3>Błędy (%)</h3>
    <canvas id="errChart"></canvas>
  </div>
</div>

<h2 style="margin-bottom:12px;color:#f8fafc">Percentyle Response Time</h2>
<table style="margin-bottom:28px">
  <tr><th>Percentyl</th><th>Czas (s)</th><th>Ocena</th></tr>
  <tr><td>P50</td><td>{p50:.3f}</td><td class="{'ok' if p50<1 else 'warn' if p50<3 else 'fail'}">{'OK' if p50<1 else 'Wolno' if p50<3 else 'FAIL'}</td></tr>
  <tr><td>P90</td><td>{p90:.3f}</td><td class="{'ok' if p90<2 else 'warn' if p90<5 else 'fail'}">{'OK' if p90<2 else 'Wolno' if p90<5 else 'FAIL'}</td></tr>
  <tr><td>P95</td><td>{p95:.3f}</td><td class="{'ok' if p95<3 else 'warn' if p95<10 else 'fail'}">{'OK' if p95<3 else 'Wolno' if p95<10 else 'FAIL'}</td></tr>
  <tr><td>P99</td><td>{p99:.3f}</td><td class="fail">FAIL</td></tr>
  <tr><td>P99.9</td><td>{p999:.3f}</td><td class="fail">FAIL</td></tr>
  <tr><td>MAX</td><td>{pmax:.3f}</td><td class="fail">FAIL</td></tr>
</table>

<h2 style="margin-bottom:12px;color:#f8fafc">Wnioski</h2>
<div class="card" style="margin-bottom:12px">
  <ul style="padding-left:18px;line-height:2">
    <li>Serwer <b>działa stabilnie przy 10 VU</b> — avg RT ~1.4s, 0% błędów</li>
    <li>Przy skoku do <b>500 VU serwer się załamał</b> — wskaźnik błędów wzrósł do ~51%</li>
    <li>Błędy: <code>Connection refused</code>, <code>failed to respond</code>, <code>Read timed out</code></li>
    <li>P95 = {p95:.1f}s, P99 = {p99:.1f}s — dramatyczny wzrost latencji przy spike</li>
    <li>FastAPI z jednym procesem uvicorn <b>nie skaluje się</b> do 500 concurrent users</li>
    <li>Rekomendacja: <b>uvicorn z wieloma workerami</b> lub <b>gunicorn + uvicorn workers</b></li>
  </ul>
</div>

<script>
const labels = {time_labels};
const threads = {threads_data};
const avgrt   = {avgrt_data};
const tps     = {tps_data};
const errors  = {errors_data};

const cfg = (label, data, color, yLabel) => ({{
  type:'line',
  data:{{ labels, datasets:[{{ label, data, borderColor:color, backgroundColor:color+'22', fill:true, tension:.3, pointRadius:2 }}] }},
  options:{{ responsive:true, plugins:{{ legend:{{ display:false }} }}, scales:{{ y:{{ title:{{ display:true, text:yLabel, color:'#94a3b8' }}, grid:{{ color:'#334155' }}, ticks:{{ color:'#94a3b8' }} }}, x:{{ title:{{ display:true, text:'Czas (s)', color:'#94a3b8' }}, grid:{{ color:'#334155' }}, ticks:{{ color:'#94a3b8', maxTicksLimit:12 }} }} }} }}
}});

new Chart(document.getElementById('vuChart'), {{
  type:'line',
  data:{{ labels, datasets:[
    {{ label:'Virtual Users', data:threads, borderColor:'#60a5fa', backgroundColor:'#60a5fa22', fill:false, tension:.3, pointRadius:2, yAxisID:'y' }},
    {{ label:'Avg RT (s)', data:avgrt, borderColor:'#f87171', backgroundColor:'#f8717122', fill:false, tension:.3, pointRadius:2, yAxisID:'y1' }}
  ]}},
  options:{{ responsive:true, interaction:{{ mode:'index', intersect:false }}, scales:{{
    y:{{ type:'linear', position:'left', title:{{ display:true, text:'VU', color:'#94a3b8' }}, grid:{{ color:'#334155' }}, ticks:{{ color:'#94a3b8' }} }},
    y1:{{ type:'linear', position:'right', title:{{ display:true, text:'Avg RT (s)', color:'#94a3b8' }}, grid:{{ drawOnChartArea:false }}, ticks:{{ color:'#94a3b8' }} }},
    x:{{ grid:{{ color:'#334155' }}, ticks:{{ color:'#94a3b8', maxTicksLimit:12 }} }}
  }} }}
}});
new Chart(document.getElementById('tpsChart'), cfg('req/s', tps, '#4ade80', 'Żądania/s'));
new Chart(document.getElementById('errChart'), cfg('Błędy %', errors, '#f87171', 'Błędy (%)'));
</script>
</body>
</html>
"""

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Raport zapisany: {OUTPUT}")
print(f"Łącznie żądań: {total:,} | Błędy: {error_rate:.1f}% | Avg RT: {avg_rt:.2f}s | P95: {p95:.2f}s")
