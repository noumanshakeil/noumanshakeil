"""Build a streak SVG from GitHub GraphQL (includes private contribs with a user PAT)."""
from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "streak-card.svg"
# Profile owner is in Islamabad — match GitHub local-day boundaries.
TZ = ZoneInfo(os.environ.get("STREAK_TZ", "Asia/Karachi"))

YEARS_QUERY = """
query {
  viewer {
    contributionsCollection {
      contributionYears
    }
  }
}
"""

def year_query(year: int) -> str:
    return f"""
query {{
  viewer {{
    contributionsCollection(from: "{year}-01-01T00:00:00Z", to: "{year}-12-31T23:59:59Z") {{
      contributionCalendar {{
        totalContributions
        weeks {{
          contributionDays {{
            date
            contributionCount
          }}
        }}
      }}
    }}
  }}
}}
"""


def graphql(token: str | None, query: str) -> dict:
    """Use PAT via HTTPS, or fall back to authenticated `gh api graphql`."""
    if not token:
        body = json.loads(
            subprocess.check_output(["gh", "api", "graphql", "-f", f"query={query}"], text=True)
        )
    else:
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=json.dumps({"query": query}).encode(),
            headers={
                "Authorization": f"bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "noumanshakeil-streak-card",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode())
    if "errors" in body:
        raise RuntimeError(body["errors"])
    return body["data"]


def fetch_all_days(token: str | None) -> tuple[int, list[tuple[date, int]]]:
    """All-time total + per-day counts across every contribution year."""
    years = graphql(token, YEARS_QUERY)["viewer"]["contributionsCollection"]["contributionYears"]
    by_day: dict[date, int] = {}
    total = 0
    for year in sorted(years):
        cal = graphql(token, year_query(year))["viewer"]["contributionsCollection"][
            "contributionCalendar"
        ]
        total += int(cal["totalContributions"])
        for week in cal["weeks"]:
            for day in week["contributionDays"]:
                d = date.fromisoformat(day["date"])
                if d.year == year:
                    by_day[d] = int(day["contributionCount"])
    days = sorted(by_day.items())
    return total, days


def compute_streaks(
    days: list[tuple[date, int]], today: date
) -> tuple[int, int, date | None, date | None, date | None, date | None]:
    """Return current, longest, and date ranges."""
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

    by_day = {d: c for d, c in days}
    cursor = today
    # If today is still empty, streak may be intact through yesterday (TZ edge).
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
    token = os.environ.get("STATS_PAT") or os.environ.get("GITHUB_TOKEN") or None

    total, days = fetch_all_days(token)
    today = datetime.now(TZ).date()
    current, longest, cs, ce, ls, le = compute_streaks(days, today)
    first = min((d for d, c in days if c > 0), default=today).strftime("%b %d, %Y")
    svg = render_svg(total, current, longest, fmt_range(cs, ce), fmt_range(ls, le), first)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8", newline="\n")
    print(
        f"total={total} current={current} longest={longest} "
        f"first={first} today={today} tz={TZ.key} -> {OUT}"
    )


if __name__ == "__main__":
    main()
