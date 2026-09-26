# Circuit contribution visualizer — auto-generated from GitHub contribution data.\nimport json
import os
import urllib.request
from html import escape

USERNAME = "Likethan"
OUTPUT = "output/contribution-circuit.svg"
WIDTH = 1200
HEIGHT = 430

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

LEVELS = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}

def fetch_calendar():
    token = os.environ["GITHUB_TOKEN"]
    payload = json.dumps({"query": QUERY, "variables": {"login": USERNAME}}).encode()
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Likethan-contribution-circuit",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    if data.get("errors"):
        raise RuntimeError(data["errors"])
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

def main():
    calendar = fetch_calendar()
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]

    # Normalize to a 53-column x 7-row circuit board.
    cells = []
    for wi, week in enumerate(weeks[-53:]):
        days = week["contributionDays"]
        for di, day in enumerate(days):
            cells.append((wi, di, int(day["contributionCount"]), LEVELS.get(day["contributionLevel"], 0), day["date"]))

    board_x, board_y = 56, 126
    cell = 17
    gap = 3
    pitch = cell + gap

    nodes = []
    for wi, di, count, level, date in cells:
        x = board_x + wi * pitch + cell / 2
        y = board_y + di * pitch + cell / 2
        nodes.append((x, y, count, level, date))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Likethan GitHub contribution circuit">',
        '<defs>',
        '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#05070b"/><stop offset="1" stop-color="#0c1118"/></linearGradient>',
        '<filter id="glow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        '<pattern id="grid" width="34" height="34" patternUnits="userSpaceOnUse"><path d="M34 0H0V34" fill="none" stroke="#15202b" stroke-width="1"/></pattern>',
        '<style><![CDATA[.trace{stroke:#1c3942;stroke-width:2;fill:none;stroke-linecap:round}.hot{stroke:#38d9c3}.node{animation:pulse 2.8s ease-in-out infinite}.traceAnim{stroke-dasharray:8 14;animation:flow 2.4s linear infinite}@keyframes pulse{0%,100%{opacity:.72}50%{opacity:1}}@keyframes flow{to{stroke-dashoffset:-44}}]]></style>',
        '</defs>',
        '<rect width="1200" height="430" rx="18" fill="url(#bg)"/>',
        '<rect x="18" y="18" width="1164" height="394" rx="14" fill="url(#grid)" opacity=".55"/>',
        '<rect x="30" y="30" width="1140" height="370" rx="12" fill="none" stroke="#1b2a33"/>',
        '<text x="56" y="62" fill="#e7f7f4" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="19" font-weight="700">GITHUB CONTRIBUTION CIRCUIT</text>',
        f'<text x="56" y="88" fill="#6f858e" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12">LIKETHAN / LAST 12 MONTHS / {total:,} CONTRIBUTIONS</text>',
        '<circle cx="1115" cy="58" r="5" fill="#38d9c3" filter="url(#glow)"/><text x="1130" y="63" fill="#6f858e" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11">LIVE DATA</text>',
    ]

    # Horizontal and vertical bus traces.
    for row in range(7):
        y = board_y + row * pitch + cell / 2
        parts.append(f'<path class="trace" d="M42 {y:.1f}H{board_x-8}"/>')
    for col in range(min(53, len(weeks))):
        x = board_x + col * pitch + cell / 2
        parts.append(f'<path class="trace" d="M{x:.1f} {board_y-10}V{board_y-2}"/>')

    # Connect active cells to their nearest active neighbor to create circuit routes.
    active = {(round(x,1), round(y,1)): (count, level) for x,y,count,level,_ in nodes if level > 0}
    for x, y, count, level, date in nodes:
        if level <= 0:
            continue
        right = (round(x + pitch,1), round(y,1))
        down = (round(x,1), round(y + pitch,1))
        if right in active:
            parts.append(f'<path class="trace traceAnim" d="M{x:.1f} {y:.1f}H{right[0]:.1f}"/>')
        if down in active:
            parts.append(f'<path class="trace" d="M{x:.1f} {y:.1f}V{down[1]:.1f}"/>')

    for x, y, count, level, date in nodes:
        if level == 0:
            parts.append(f'<rect x="{x-cell/2:.1f}" y="{y-cell/2:.1f}" width="{cell}" height="{cell}" rx="3" fill="#0b1117" stroke="#111c23"/>')
            continue
        intensity = ["#163039", "#1e5c62", "#238f8a", "#2bb7a6", "#38d9c3"][level]
        radius = 3.2 + level * 1.2 + min(count, 12) * .12
        parts.append(f'<rect class="node" x="{x-cell/2:.1f}" y="{y-cell/2:.1f}" width="{cell}" height="{cell}" rx="3" fill="#0a171b" stroke="{intensity}" stroke-width="{1.2 + level*.35:.1f}" style="animation-delay:{(x+y)%19/10:.1f}s"><title>{escape(date)} — {count} contributions</title></rect>')
        parts.append(f'<circle class="node" cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="{intensity}" filter="url(#glow)" style="animation-delay:{(x+y)%17/9:.1f}s"/>')

    parts += [
        '<rect x="56" y="278" width="1088" height="1" fill="#17262e"/>',
        '<text x="56" y="314" fill="#6f858e" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11">SIGNAL STRENGTH</text>',
    ]

    for i, label in enumerate(["IDLE", "LOW", "MED", "HIGH", "PEAK"]):
        x = 155 + i * 42
        color = ["#111c23", "#1e5c62", "#238f8a", "#2bb7a6", "#38d9c3"][i]
        parts.append(f'<rect x="{x}" y="305" width="16" height="16" rx="3" fill="{color}"/>')
        parts.append(f'<text x="{x+23}" y="318" fill="#536a73" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10">{label}</text>')

    parts += [
        '<text x="56" y="362" fill="#32454d" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10">EACH NODE = CONTRIBUTION DAY  ·  TRACE = ACTIVE PATH  ·  BRIGHTNESS = ACTIVITY LEVEL</text>',
        '<text x="56" y="383" fill="#263840" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10">AUTO-GENERATED BY GITHUB ACTIONS</text>',
        '</svg>'
    ]

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))

if __name__ == "__main__":
    main()
