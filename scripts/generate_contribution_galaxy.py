import json
import os
import random
import urllib.request
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
    left, top = 42, 58
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
            size = 1.5 + level * 0.9 + min(count, 25) * 0.055
            stars.append((x, y, size, level, count, wi * 7 + di))

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<defs>',
        '<radialGradient id="bg"><stop offset="0" stop-color="#17102d"/><stop offset="0.55" stop-color="#090817"/><stop offset="1" stop-color="#03040a"/></radialGradient>',
        '<radialGradient id="nebula"><stop offset="0" stop-color="#8b5cf6" stop-opacity=".24"/><stop offset=".5" stop-color="#4f46e5" stop-opacity=".09"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>',
        '<linearGradient id="meteorTrail" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#7c3aed" stop-opacity="0"/><stop offset=".5" stop-color="#a78bfa" stop-opacity=".32"/><stop offset="1" stop-color="#ffffff" stop-opacity=".98"/></linearGradient>',
        '<filter id="glow"><feGaussianBlur stdDeviation="2.8" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        '<filter id="soft"><feGaussianBlur stdDeviation="18"/></filter>',
        '</defs>',
        '<rect width="100%" height="100%" rx="18" fill="url(#bg)"/>',
        '<ellipse cx="490" cy="154" rx="430" ry="132" fill="url(#nebula)" filter="url(#soft)"/>',
        '<text x="42" y="31" fill="#f5f3ff" font-family="Inter,Segoe UI,sans-serif" font-size="14" font-weight="700" letter-spacing="2">CONTRIBUTION GALAXY</text>',
        f'<text x="938" y="31" text-anchor="end" fill="#a1a1aa" font-family="Inter,Segoe UI,sans-serif" font-size="12">{total:,} contributions · LAST 12 MONTHS</text>',
    ]

    # Background stars.
    for _ in range(105):
        x = random.randint(18, width - 18)
        y = random.randint(45, height - 20)
        r = random.choice([0.45, 0.6, 0.8, 1.0])
        op = random.choice([0.16, 0.22, 0.3, 0.42])
        svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#ddd6fe" opacity="{op}"/>')

    # Each real contribution day becomes a small meteor. The meteor travels along
    # a diagonal path and leaves a fading tail before returning to its origin.
    for index, (x, y, size, level, count, seed) in enumerate(stars):
        duration = 3.4 + (seed % 7) * 0.22
        delay = -((seed * 29) % 1200) / 100.0
        travel_x = 18 + level * 5
        travel_y = 12 + level * 4
        tail = 12 + level * 5
        opacity = min(0.92, 0.38 + level * 0.13)
        stroke = max(1.1, size * 0.48)
        safe_count = escape(str(count))

        svg.append(
            f'<g filter="url(#glow)" opacity="{opacity:.2f}">'
            f'<line x1="{x-tail:.1f}" y1="{y+tail*.55:.1f}" x2="{x:.1f}" y2="{y:.1f}" '
            f'stroke="url(#meteorTrail)" stroke-width="{stroke:.1f}" stroke-linecap="round">'
            f'<animate attributeName="x1" values="{x-tail:.1f};{x+travel_x-tail:.1f};{x-tail:.1f}" '
            f'dur="{duration:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="y1" values="{y+tail*.55:.1f};{y-travel_y+tail*.55:.1f};{y+tail*.55:.1f}" '
            f'dur="{duration:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="x2" values="{x:.1f};{x+travel_x:.1f};{x:.1f}" '
            f'dur="{duration:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="y2" values="{y:.1f};{y-travel_y:.1f};{y:.1f}" '
            f'dur="{duration:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
            '</line>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{size:.2f}" fill="#ffffff">'
            f'<animate attributeName="cx" values="{x:.1f};{x+travel_x:.1f};{x:.1f}" '
            f'dur="{duration:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="cy" values="{y:.1f};{y-travel_y:.1f};{y:.1f}" '
            f'dur="{duration:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="r" values="{size:.2f};{size*1.5:.2f};{size:.2f}" '
            f'dur="{duration:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
            '</circle>'
            f'<title>{safe_count} contribution(s)</title>'
            '</g>'
        )

    # A few independent long meteors add a subtle cinematic shooting-star layer.
    for meteor in range(7):
        sx = 110 + meteor * 125
        sy = 70 + (meteor * 37) % 150
        length = 28 + (meteor % 3) * 12
        duration = 5.5 + meteor * 0.35
        delay = -(meteor * 1.7)
        svg.append(
            f'<g opacity=".5" filter="url(#glow)">'
            f'<line x1="{sx}" y1="{sy}" x2="{sx+length}" y2="{sy-length*.55}" stroke="url(#meteorTrail)" stroke-width="1.2" stroke-linecap="round">'
            f'<animate attributeName="x1" values="{sx};{sx+length*2};{sx}" dur="{duration:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="x2" values="{sx+length};{sx+length*2+length};{sx+length}" dur="{duration:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
            '</line></g>'
        )

    svg.append('<text x="490" y="282" text-anchor="middle" fill="#71717a" font-family="Inter,Segoe UI,sans-serif" font-size="10" letter-spacing="1.5">EACH METEOR REPRESENTS A DAY OF ACTIVITY</text>')
    svg.append('</svg>')

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as file:
        file.write("\n".join(svg))


if __name__ == "__main__":
    main()
