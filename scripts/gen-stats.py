#!/usr/bin/env python3
"""Generate assets/stats.svg from the GitHub API. Stdlib only.

Usage: python3 scripts/gen-stats.py [username]
Honors GITHUB_TOKEN for authenticated requests (required in CI to avoid rate limits).
"""
import json
import os
import sys
import urllib.request

USER = sys.argv[1] if len(sys.argv) > 1 else "lowcache"
API = "https://api.github.com"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "stats.svg")

# palette shared with header.svg
BG, PANEL, LINE = "#0d1117", "#161b22", "#21262d"
GREEN, AMBER, TEXT, DIM = "#3fb950", "#ffa657", "#c9d1d9", "#8b949e"

TOP_N = 6
BAR_X, BAR_W = 250, 480


def get(path):
    req = urllib.request.Request(API + path, headers={"Accept": "application/vnd.github+json"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req) as r:
        return json.load(r)


user = get(f"/users/{USER}")
repos = []
page = 1
while True:
    batch = get(f"/users/{USER}/repos?per_page=100&page={page}")
    repos += batch
    if len(batch) < 100:
        break
    page += 1
repos = [r for r in repos if not r["fork"]]

stars = sum(r["stargazers_count"] for r in repos)
since = user["created_at"][:4]
langs = {}
for r in repos:
    for k, v in get(f"/repos/{USER}/{r['name']}/languages").items():
        langs[k] = langs.get(k, 0) + v
total = sum(langs.values()) or 1
top = sorted(langs.items(), key=lambda x: -x[1])[:TOP_N]

rows_y = 118
height = rows_y + TOP_N * 26 + 20
lines = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 {height}" font-family="ui-monospace, 'Cascadia Code', 'JetBrains Mono', Menlo, Consolas, monospace" font-size="13">
  <rect x="1" y="1" width="878" height="{height - 2}" rx="12" fill="{BG}" stroke="{LINE}" stroke-width="1.5"/>
  <rect x="14" y="14" width="852" height="30" rx="6" fill="{PANEL}"/>
  <text x="28" y="34"><tspan fill="{GREEN}" font-weight="bold">$</tspan><tspan fill="{TEXT}" dx="8">gh-stats --user {USER}</tspan></text>
  <text x="28" y="76"><tspan fill="{AMBER}">repos:</tspan><tspan fill="{TEXT}" dx="8">{len(repos)} public</tspan><tspan fill="{AMBER}" dx="40">stars:</tspan><tspan fill="{TEXT}" dx="8">{stars}</tspan><tspan fill="{AMBER}" dx="40">on github since:</tspan><tspan fill="{TEXT}" dx="8">{since}</tspan></text>
  <text x="28" y="102" fill="{DIM}"># top languages by weight, all public repos</text>''']

for i, (name, size) in enumerate(top):
    pct = size / total * 100
    y = rows_y + i * 26
    w = max(round(BAR_W * pct / 100), 4)
    op = 0.95 - i * 0.12
    lines.append(f'''  <text x="28" y="{y + 12}" fill="{TEXT}">{name.lower()}</text>
  <rect x="{BAR_X}" y="{y}" width="{BAR_W}" height="14" rx="3" fill="{LINE}"/>
  <rect x="{BAR_X}" y="{y}" width="{w}" height="14" rx="3" fill="{GREEN}" opacity="{op:.2f}">
    <animate attributeName="width" from="0" to="{w}" begin="{0.2 + i * 0.12:.2f}s" dur="0.7s" fill="freeze"/>
  </rect>
  <text x="{BAR_X + BAR_W + 16}" y="{y + 12}" fill="{AMBER}">{pct:.1f}%</text>''')

lines.append("</svg>")
with open(os.path.abspath(OUT), "w") as f:
    f.write("\n".join(lines) + "\n")
print(f"wrote {os.path.abspath(OUT)} ({len(repos)} repos, {stars} stars, {len(top)} langs)")
