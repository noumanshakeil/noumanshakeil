"""Fetch noumanshakeil public repos via gh and dump JSON."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
out = ROOT / "repos.json"

raw = subprocess.check_output(
    [
        "gh",
        "api",
        "users/noumanshakeil/repos?per_page=100&type=owner",
        "--paginate",
    ],
    text=True,
)

# gh --paginate may concatenate JSON arrays; parse carefully
chunks: list = []
decoder = json.JSONDecoder()
idx = 0
s = raw.strip()
while idx < len(s):
    while idx < len(s) and s[idx].isspace():
        idx += 1
    if idx >= len(s):
        break
    obj, end = decoder.raw_decode(s, idx)
    chunks.append(obj)
    idx = end

repos: list = []
for chunk in chunks:
    if isinstance(chunk, list):
        repos.extend(chunk)
    else:
        repos.append(chunk)

clean = [
    {
        "name": r["name"],
        "description": r.get("description") or "",
        "html_url": r["html_url"],
        "fork": r.get("fork", False),
        "archived": r.get("archived", False),
        "language": r.get("language"),
        "topics": r.get("topics") or [],
        "pushed_at": r.get("pushed_at"),
    }
    for r in repos
    if not r.get("fork") and r["name"].lower() != "noumanshakeil"
]

out.write_text(json.dumps(clean, indent=2), encoding="utf-8")
print(f"Wrote {len(clean)} repos -> {out}")
for r in sorted(clean, key=lambda x: x["name"].lower()):
    print(f"{r['name']}\t{r['description'][:80]}")
