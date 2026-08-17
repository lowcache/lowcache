#!/usr/bin/env python3
"""Fetch profile stats from the GitHub API into assets/stats.json. Stdlib only.

Usage: python3 scripts/gen-stats.py [username]
Honors GITHUB_TOKEN for authenticated requests (required in CI to avoid rate limits).

This script only fetches DATA. Rendering lives in build_sheets.py (sheet LC-200)
so the drawing-set styling stays in one place. The daily workflow runs both;
neither needs a third-party package, because the font subsets are committed
under assets/fonts/cache/.
"""
import datetime
import json
import os
import sys
import urllib.request

USER = sys.argv[1] if len(sys.argv) > 1 else "lowcache"
API = "https://api.github.com"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "stats.json")

TOP_N = 6


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
langs = {}
for r in repos:
    for k, v in get(f"/repos/{USER}/{r['name']}/languages").items():
        langs[k] = langs.get(k, 0) + v
total = sum(langs.values()) or 1
top = sorted(langs.items(), key=lambda x: -x[1])[:TOP_N]

data = {
    # the date the survey was taken; LC-200 prints this as its revision
    "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
    "user": USER,
    "repos": len(repos),
    "stars": stars,
    "followers": user.get("followers", 0),
    "since": user["created_at"][:4],
    "languages": [
        {"name": name, "pct": round(size / total * 100, 1)} for name, size in top
    ],
}

out = os.path.abspath(OUT)
with open(out, "w") as f:
    json.dump(data, f, indent=2, sort_keys=True)
    f.write("\n")
print(f"wrote {out} ({len(repos)} repos, {stars} stars, {len(top)} langs)")
