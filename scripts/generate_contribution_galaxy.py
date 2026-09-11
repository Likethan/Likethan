import json
import os
import random
import urllib.request
from datetime import datetime, timezone
from xml.sax.saxutils import escape

USERNAME = "Likethan"
OUTPUT = "dist/contribution-galaxy.svg"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date contributionCount contributionLevel }
        }
      }
    }
  }
}
"""


def fetch_calendar():
    token = os.environ["GITHUB_TOKEN"]
    payload = json.dumps({"query": QUERY, "variables": {"login": USERNAME}}).encode()
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Likethan-contribution-galaxy",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    if data.get("errors"):
        raise RuntimeError(data["errors"])
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def level_value(level):
    return {
        "NONE": 0,
        "FIRST_QUARTILE": 1,
        "SECOND_QUARTILE": 2,
        "THIRD_QUARTILE": 3,
        "FOURTH_QUARTILE": 4,
    }.get(level, 0)


def main():
    calendar = fetch_calendar()
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]

    random.seed(20260911)
    width, height = 980, 300
    left, top = 42, 54
    cell_x, cell_y = 17, 29

    stars = []
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week["contributionDays"]):
            level = level_value(day["contributionLevel"])
            count = int(day["contributionCount"])
            if level == 0:
                continue
            x = left + wi * cell_x
            y = top + di * cell_y
            size = 1.6 + level * 0.85 + min(count, 20) * 0.06
            stars.append((x, y, size, level, count, wi * 7 + di))

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<defs>',
        '<radialGradient id="bg"><stop offset="0" stop-color="#17102d"/><stop offset="0.55" stop-color="#090817"/><stop offset="1" stop-color="#03040a"/></radialGradient>',
        '<radialGradient id="nebula"><stop offset="0" stop-color="#8b5cf6" stop-opacity=".22"/><stop offset=".5" stop-color="#4f46e5" stop-opacity=".08"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>',
        '<linearGradient id="trail" x1="0" x2="1"><stop offset="0" stop-color="#7c3aed" stop-opacity="0"/><stop offset=".55" stop-color="#a78bfa" stop-opacity=".35"/><stop offset="1" stop-color="#ffffff" stop-opacity=".95"/></linearGradient>',
        '<filter id="glow"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        '<filter id="soft"><feGaussianBlur stdDeviation="18"/></filter>',
        '</defs>',
        '<rect width="100%" height="100%" rx="18" fill="url(#bg)"/>',
        '<ellipse cx="490" cy="150" rx="420" ry="130" fill="url(#nebula)" filter="url(#soft)"/>',
        '<text x="42" y="30" fill="#f5f3ff" font-family="Inter,Segoe UI,sans-serif" font-size="14" font-weight="700" letter-spacing="2">CONTRIBUTION GALAXY</text>',
        f'<text x="938" y="30" text-anchor="end" fill="#a1a1aa" font-family="Inter,Segoe UI,sans-serif" font-size="12">{total:,} contributions · LAST 12 MONTHS</text>',
    ]

    # A restrained star field keeps the visualization cosmic without overpowering the data.
    for i in range(90):
        x = random.randint(18, width - 18)
        y = random.randint(42, height - 18)
        r = random.choice([0.45, 0.6, 0.8, 1.0])
        op = random.choice([0.18, 0.25, 0.35, 0.5])
        svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#c4b5fd" opacity="{op}"/>')

    # Contribution cells become animated shooting stars. Higher contribution levels get longer trails.
    for idx, (x, y, size, level, count, seed) in enumerate(stars):
        duration = 2.8 + (seed % 9) * 0.18
        delay = -((seed * 37) % 900) / 100.0
        trail = 7 + level * 5
        opacity = 0.48 + level * 0.12
        safe_count = escape(str(count))
        svg.append(
            f'<g filter="url(#glow)" opacity="{opacity:.2f}">'
            f'<line x1="{x-trail}" y1="{y+trail*.45:.1f}" x2="{x}" y2="{y}" stroke="url(#trail)" stroke-width="{max(1, size*.55):.1f}" stroke-linecap="round">'
            f'<animate attributeName="x1" values="{x-trail};{x-3};{x-trail}" dur="{duration:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/></line>'
            f'<circle cx="{x}" cy="{y}" r="{size:.2f}" fill="#f5f3ff">'
            f'<animate attributeName="r" values="{size:.2f};{size*1.45:.2f};{size:.2f}" dur="{duration:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/></circle>'
            f'<title>{safe_count} contribution(s)</title></g>'
        )

    svg.append('<text x="490" y="282" text-anchor="middle" fill="#71717a" font-family="Inter,Segoe UI,sans-serif" font-size="10" letter-spacing="1.5">EACH LIGHT REPRESENTS A DAY OF ACTIVITY</text>')
    svg.append('</svg>')

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as file:
        file.write("\n".join(svg))


if __name__ == "__main__":
    main()
