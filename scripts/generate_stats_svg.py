"""Build a stats SVG from GraphQL (same private-aware source as the streak card)."""
from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "stats-card.svg"

STATS_QUERY = """
query {
  viewer {
    login
    name
    repositories(ownerAffiliations: OWNER, first: 100, isFork: false) {
      pageInfo { hasNextPage endCursor }
      nodes { stargazerCount }
    }
    contributionsCollection {
      contributionYears
      totalIssueContributions
      totalPullRequestContributions
      totalRepositoriesWithContributedCommits
      contributionCalendar { totalContributions }
    }
  }
}
"""


def year_total_query(year: int) -> str:
    return f"""
query {{
  viewer {{
    contributionsCollection(from: "{year}-01-01T00:00:00Z", to: "{year}-12-31T23:59:59Z") {{
      contributionCalendar {{ totalContributions }}
      totalIssueContributions
      totalPullRequestContributions
      totalRepositoriesWithContributedCommits
    }}
  }}
}}
"""

STARS_PAGE = """
query ($cursor: String) {
  viewer {
    repositories(ownerAffiliations: OWNER, first: 100, isFork: false, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes { stargazerCount }
    }
  }
}
"""


def graphql(token: str | None, query: str, variables: dict | None = None) -> dict:
    if not token:
        cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
        if variables and variables.get("cursor"):
            cmd.extend(["-f", f"cursor={variables['cursor']}"])
        body = json.loads(subprocess.check_output(cmd, text=True))
    else:
        payload: dict = {"query": query}
        if variables:
            payload["variables"] = variables
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "noumanshakeil-stats-card",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode())
    if "errors" in body:
        raise RuntimeError(body["errors"])
    return body["data"]


def sum_stars(token: str | None, first_page: dict) -> int:
    stars = sum(n["stargazerCount"] for n in first_page["nodes"])
    page = first_page
    while page["pageInfo"]["hasNextPage"]:
        cursor = page["pageInfo"]["endCursor"]
        if not token:
            # inline cursor into query for gh fallback
            q = f"""
            query {{
              viewer {{
                repositories(ownerAffiliations: OWNER, first: 100, isFork: false, after: "{cursor}") {{
                  pageInfo {{ hasNextPage endCursor }}
                  nodes {{ stargazerCount }}
                }}
              }}
            }}
            """
            page = graphql(token, q)["viewer"]["repositories"]
        else:
            page = graphql(token, STARS_PAGE, {"cursor": cursor})["viewer"]["repositories"]
        stars += sum(n["stargazerCount"] for n in page["nodes"])
    return stars


def rank_for(contribs: int) -> tuple[str, float]:
    """Rough percentile-style rank used only for the ring label."""
    thresholds = [
        (10000, "S+", 1.0),
        (5000, "S", 0.95),
        (2000, "A+", 0.88),
        (1000, "A", 0.8),
        (500, "A-", 0.72),
        (250, "B+", 0.64),
        (100, "B", 0.55),
        (50, "B-", 0.45),
        (20, "C+", 0.35),
        (5, "C", 0.25),
    ]
    for n, label, pct in thresholds:
        if contribs >= n:
            return label, pct
    return "C-", 0.15


def render(name: str, stars: int, commits: int, prs: int, issues: int, contrib_to: int, rank: str, pct: float) -> str:
    r = 40
    circ = 2 * 3.1415926 * r
    dash = f"{circ * pct:.1f} {circ:.1f}"
    title = f"{name}'s GitHub Stats" if name else "GitHub Stats"
    # Fixed columns: icon | label | right-aligned value (matches github-readme-stats layout)
    rows = [
        ("*", "Total Stars Earned:", f"{stars:,}"),
        ("+", "Total Contributions:", f"{commits:,}"),
        ("P", "Total PRs:", f"{prs:,}"),
        ("!", "Total Issues:", f"{issues:,}"),
        ("#", "Contributed to (last year):", f"{contrib_to:,}"),
    ]
    row_h = 26
    start_y = 62
    icon_x = 28
    label_x = 48
    value_x = 310  # right edge of value column; text-anchor=end
    lines = []
    for i, (icon, label, value) in enumerate(rows):
        y = start_y + i * row_h
        lines.append(
            f'    <text x="{icon_x}" y="{y}" fill="#39d353" font-size="14" font-weight="700">{icon}</text>'
        )
        lines.append(
            f'    <text x="{label_x}" y="{y}" fill="#c9d1d9" font-size="13">{label}</text>'
        )
        lines.append(
            f'    <text x="{value_x}" y="{y}" fill="#58a6ff" font-size="13" font-weight="700" text-anchor="end">{value}</text>'
        )
    body = "\n".join(lines)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="450" height="195" viewBox="0 0 450 195" role="img">
  <rect width="450" height="195" rx="8" fill="#0d1117" stroke="#e6edf3" stroke-opacity="0.15"/>
  <g font-family="Segoe UI, Ubuntu, sans-serif">
    <text x="25" y="32" fill="#58a6ff" font-size="16" font-weight="700">{title}</text>
{body}

    <circle cx="380" cy="112" r="40" fill="none" stroke="#21262d" stroke-width="6"/>
    <circle cx="380" cy="112" r="40" fill="none" stroke="#39d353" stroke-width="6"
            stroke-dasharray="{dash}" stroke-linecap="round" transform="rotate(-90 380 112)"/>
    <text x="380" y="118" text-anchor="middle" fill="#58a6ff" font-size="28" font-weight="800">{rank}</text>
  </g>
</svg>
'''


def main() -> None:
    token = os.environ.get("STATS_PAT") or os.environ.get("GITHUB_TOKEN") or None
    data = graphql(token, STATS_QUERY)["viewer"]
    coll = data["contributionsCollection"]
    years = coll.get("contributionYears") or []

    # Same all-time calendar total as the streak card (private-aware when PAT can see them).
    commits = 0
    prs = 0
    issues = 0
    contrib_to = 0
    if years:
        for year in sorted(years):
            ycoll = graphql(token, year_total_query(year))["viewer"]["contributionsCollection"]
            commits += int(ycoll["contributionCalendar"]["totalContributions"])
            prs += int(ycoll["totalPullRequestContributions"])
            issues += int(ycoll["totalIssueContributions"])
            # repos-with-commits is not safely summable across years; keep rolling value
        contrib_to = int(coll["totalRepositoriesWithContributedCommits"])
    else:
        commits = int(coll["contributionCalendar"]["totalContributions"])
        prs = int(coll["totalPullRequestContributions"])
        issues = int(coll["totalIssueContributions"])
        contrib_to = int(coll["totalRepositoriesWithContributedCommits"])

    stars = sum_stars(token, data["repositories"])
    rank, pct = rank_for(commits)
    name = data.get("name") or data.get("login") or "GitHub"

    svg = render(name, stars, commits, prs, issues, contrib_to, rank, pct)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8", newline="\n")
    print(
        f"stars={stars} contributions={commits} prs={prs} issues={issues} "
        f"repos={contrib_to} rank={rank} -> {OUT}"
    )


if __name__ == "__main__":
    main()
