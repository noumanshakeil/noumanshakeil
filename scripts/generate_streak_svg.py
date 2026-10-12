"""Build a streak SVG from GitHub GraphQL (includes private contribs with a user PAT)."""
from __future__ import annotations

import json
import os
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "streak-card.svg"

QUERY = """
query {
  viewer {
    login
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def graphql(token: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY}).encode(),
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "noumanshakeil-streak-card",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode())
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    return payload["data"]


def compute_streaks(days: list[tuple[date, int]]) -> tuple[int, int, date | None, date | None, date | None, date | None]:
    """Return current, longest, and date ranges."""
    # days sorted ascending
    days = sorted(days, key=lambda x: x[0])
    longest = 0
    longest_start = longest_end = None
    run = 0
    run_start = None

    for d, c in days:
        if c > 0:
            if run == 0:
                run_start = d
            run += 1
            if run > longest:
                longest = run
                longest_start, longest_end = run_start, d
        else:
            run = 0
            run_start = None

    # current streak: count back from today (UTC) while > 0
    # allow yesterday start if today is still 0 (timezone edge)
    by_day = {d: c for d, c in days}
    today = datetime.now(timezone.utc).date()
    cursor = today
    if by_day.get(cursor, 0) == 0:
        cursor = today - timedelta(days=1)

    current = 0
    current_end = cursor if by_day.get(cursor, 0) > 0 else None
    current_start = None
    while by_day.get(cursor, 0) > 0:
        current += 1
        current_start = cursor
        cursor -= timedelta(days=1)

    return current, longest, current_start, current_end, longest_start, longest_end


def fmt_range(a: date | None, b: date | None) -> str:
    if not a or not b:
        return ""
    if a == b:
        return a.strftime("%b %d")
    if a.year == b.year:
        return f"{a.strftime('%b %d')} - {b.strftime('%b %d')}"
    return f"{a.strftime('%b %d, %Y')} - {b.strftime('%b %d, %Y')}"


def render_svg(total: int, current: int, longest: int, cur_range: str, long_range: str, first: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195" role="img">
  <rect width="495" height="195" rx="8" fill="#0d1117" stroke="#e6edf3" stroke-opacity="0.15"/>
  <g font-family="Segoe UI, Ubuntu, sans-serif" text-anchor="middle">
    <text x="82" y="48" fill="#58a6ff" font-size="14" font-weight="700">Total Contributions</text>
    <text x="82" y="105" fill="#58a6ff" font-size="36" font-weight="800">{total:,}</text>
    <text x="82" y="135" fill="#8b949e" font-size="12">{first} - Present</text>

    <circle cx="247" cy="78" r="42" fill="none" stroke="#39d353" stroke-width="4"/>
    <text x="247" y="72" fill="#e6edf3" font-size="28" font-weight="800">{current}</text>
    <text x="247" y="140" fill="#39d353" font-size="14" font-weight="700">Current Streak</text>
    <text x="247" y="160" fill="#8b949e" font-size="12">{cur_range}</text>

    <text x="412" y="48" fill="#58a6ff" font-size="14" font-weight="700">Longest Streak</text>
    <text x="412" y="105" fill="#58a6ff" font-size="36" font-weight="800">{longest}</text>
    <text x="412" y="135" fill="#8b949e" font-size="12">{long_range}</text>
  </g>
</svg>
'''


def main() -> None:
    token = os.environ.get("STATS_PAT") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Set STATS_PAT (preferred) or GITHUB_TOKEN")

    data = graphql(token)
    cal = data["viewer"]["contributionsCollection"]["contributionCalendar"]
    total = cal["totalContributions"]
    days: list[tuple[date, int]] = []
    for week in cal["weeks"]:
        for day in week["contributionDays"]:
            days.append((date.fromisoformat(day["date"]), int(day["contributionCount"])))

    current, longest, cs, ce, ls, le = compute_streaks(days)
    first = min((d for d, c in days if c > 0), default=date.today()).strftime("%b %d, %Y")
    svg = render_svg(total, current, longest, fmt_range(cs, ce), fmt_range(ls, le), first)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8", newline="\n")
    print(f"total={total} current={current} longest={longest} -> {OUT}")


if __name__ == "__main__":
    main()
