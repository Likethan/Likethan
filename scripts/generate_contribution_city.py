# 3D contribution city — auto-generated from GitHub contribution data.
import json
import os
import urllib.request
from html import escape

USERNAME = "Likethan"
OUTPUT = "output/contribution-city.svg"
WIDTH, HEIGHT = 1200, 520

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
            "User-Agent": "Likethan-contribution-city",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    if data.get("errors"):
        raise RuntimeError(data["errors"])
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

def esc(value):
    return escape(str(value), quote=True)

def main():
    calendar = fetch_calendar()
    weeks = calendar["weeks"][-53:]
    total = calendar["totalContributions"]

    days = []
    for col, week in enumerate(weeks):
        for row, day in enumerate(week["contributionDays"]):
            days.append((
                col, row,
                int(day["contributionCount"]),
                LEVELS.get(day["contributionLevel"], 0),
                day["date"],
            ))

    # Isometric city projection.
    ox, oy = 610, 105
    dx, dy = 19, 9
    row_dx, row_dy = -19, 9
    building_w = 13
    max_h = 118

    def project(col, row):
        return ox + col * dx + row * row_dx, oy + col * dy + row * row_dy

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Likethan 3D GitHub contribution city">',
        "<defs>",
        '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#05070b"/><stop offset="1" stop-color="#101820"/></linearGradient>',
        '<linearGradient id="ground" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#111b20"/><stop offset="1" stop-color="#071015"/></linearGradient>',
        '<linearGradient id="glass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#38d9c3"/><stop offset="1" stop-color="#0d6769"/></linearGradient>',
        '<filter id="softGlow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        '<filter id="shadow" x="-40%" y="-40%" width="180%" height="220%"><feGaussianBlur in="SourceAlpha" stdDeviation="3"/><feOffset dx="0" dy="5" result="o"/><feComponentTransfer><feFuncA type="linear" slope=".45"/></feComponentTransfer><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        '<pattern id="stars" width="90" height="70" patternUnits="userSpaceOnUse"><circle cx="11" cy="17" r="1" fill="#29434a"/><circle cx="63" cy="42" r=".8" fill="#20363e"/><circle cx="39" cy="8" r=".6" fill="#35535a"/></pattern>',
        '<style><![CDATA[
        .pulse{animation:pulse 3.2s ease-in-out infinite}.traffic{stroke-dasharray:5 15;animation:traffic 2.5s linear infinite}
        .window{animation:window 4.5s ease-in-out infinite}
        @keyframes pulse{0%,100%{opacity:.62}50%{opacity:1}}
        @keyframes traffic{to{stroke-dashoffset:-40}}
        @keyframes window{0%,78%,100%{opacity:.18}84%{opacity:1}90%{opacity:.28}}
        ]]></style>',
        "</defs>",
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#sky)"/>',
        '<rect width="1200" height="310" fill="url(#stars)" opacity=".45"/>',
        '<ellipse cx="610" cy="250" rx="560" ry="175" fill="#071217" opacity=".9"/>',
        '<path d="M35 318 L600 82 L1165 318 L600 485 Z" fill="url(#ground)" stroke="#20343b" stroke-width="1.5"/>',
        '<text x="50" y="54" fill="#e9fbf7" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="21" font-weight="800" letter-spacing="1.5">CONTRIBUTION CITY</text>',
        f'<text x="50" y="78" fill="#71858c" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="11">LIKETHAN / 3D GITHUB ACTIVITY / {total:,} CONTRIBUTIONS / LIVE DATA</text>',
        '<circle cx="1110" cy="52" r="5" fill="#38d9c3" filter="url(#softGlow)"/><text x="1125" y="57" fill="#71858c" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="10">ONLINE</text>',
    ]

    # Isometric road network and lane markings.
    for col in range(0, 54, 3):
        x1, y1 = project(col, 0)
        x2, y2 = project(col, 6)
        parts.append(f'<path d="M{x1:.1f},{y1+8:.1f} L{x2:.1f},{y2+8:.1f}" stroke="#1b3138" stroke-width="2" fill="none"/>')
        parts.append(f'<path class="traffic" d="M{x1:.1f},{y1+8:.1f} L{x2:.1f},{y2+8:.1f}" stroke="#29464c" stroke-width="1" fill="none"/>')
    for row in range(0, 8):
        x1, y1 = project(0, row)
        x2, y2 = project(52, row)
        parts.append(f'<path d="M{x1:.1f},{y1+8:.1f} L{x2:.1f},{y2+8:.1f}" stroke="#1b3138" stroke-width="2" fill="none"/>')

    # Draw buildings back-to-front so the city reads as a real isometric scene.
    for col, row, count, level, date in sorted(days, key=lambda item: item[0] + item[1]):
        cx, base_y = project(col, row)
        if count <= 0:
            # Empty lots still form the city blocks.
            parts.append(f'<polygon points="{cx},{base_y} {cx+building_w},{base_y+6} {cx},{base_y+12} {cx-building_w},{base_y+6}" fill="#0b1419" stroke="#14252b"/>')
            continue

        h = min(max_h, 15 + count * 3.1)
        top_y = base_y - h
        left = cx - building_w
        right = cx + building_w
        top = f"{cx},{top_y}"
        # 3D extruded prism: roof + left/right faces.
        roof = f"{left},{top_y+7} {cx},{top_y} {right},{top_y+7} {cx},{top_y+14}"
        left_face = f"{left},{top_y+7} {cx},{top_y+14} {cx},{base_y+8} {left},{base_y+1}"
        right_face = f"{cx},{top_y+14} {right},{top_y+7} {right},{base_y+1} {cx},{base_y+8}"

        if level == 1:
            roof_fill, left_fill, right_fill, edge = "#174047", "#0e2b31", "#12363c", "#27656a"
        elif level == 2:
            roof_fill, left_fill, right_fill, edge = "#1e7776", "#124d52", "#155c60", "#2b9690"
        elif level == 3:
            roof_fill, left_fill, right_fill, edge = "#2aa69b", "#176b69", "#1b7b76", "#35c1b0"
        else:
            roof_fill, left_fill, right_fill, edge = "#38d9c3", "#19867e", "#21a196", "#7affeb"

        parts.append(f'<g class="pulse" style="animation-delay:{((col*7+row)%23)/10:.1f}s" filter="url(#shadow)">')
        parts.append(f'<polygon points="{roof}" fill="{roof_fill}" stroke="{edge}" stroke-width="1.1"><title>{esc(date)} — {count} contributions</title></polygon>')
        parts.append(f'<polygon points="{left_face}" fill="{left_fill}" stroke="#122a30" stroke-width=".7"/>')
        parts.append(f'<polygon points="{right_face}" fill="{right_fill}" stroke="#153238" stroke-width=".7"/>')

        # Vertical window bands encode contribution density.
        bands = min(5, max(1, 1 + count // 7))
        for b in range(bands):
            wx = left + 3 + b * 2.0
            wy = top_y + 11 + (b % 2) * 3
            parts.append(f'<rect class="window" x="{wx:.1f}" y="{wy:.1f}" width="1.4" height="{max(8,h-18):.1f}" rx=".5" fill="#8dfff2" opacity=".32" style="animation-delay:{((b+col)%9)/7:.1f}s"/>')
        parts.append("</g>")

    # Central beacon makes the most active period visually dominant.
    peak = max(days, key=lambda d: d[2])
    px, py = project(peak[0], peak[1])
    ph = min(max_h, 15 + peak[2] * 3.1)
    parts += [
        f'<path class="pulse" d="M{px},{py-ph-18} L{px},{py-ph-48}" stroke="#7affeb" stroke-width="1" opacity=".65"/>',
        f'<circle class="pulse" cx="{px}" cy="{py-ph-52}" r="4" fill="#7affeb" filter="url(#softGlow)"/>',
        f'<text x="{px+10}" y="{py-ph-46}" fill="#8dfff2" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="9">PEAK {esc(peak[2])}</text>',
        '<rect x="48" y="425" width="1104" height="1" fill="#1b3037"/>',
        '<text x="50" y="452" fill="#71858c" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="10">CITY LEGEND</text>',
    ]

    legend = [("QUIET","#0b1419"),("LOW","#174047"),("MED","#1e7776"),("HIGH","#2aa69b"),("PEAK","#38d9c3")]
    for i, (label, color) in enumerate(legend):
        x = 140 + i * 105
        parts.append(f'<polygon points="{x},{440} {x+9},{444} {x},{448} {x-9},{444}" fill="{color}" stroke="#31545a"/>')
        parts.append(f'<text x="{x+15}" y="448" fill="#71858c" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="9">{label}</text>')

    parts += [
        '<text x="650" y="452" fill="#40575e" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="9">HEIGHT = CONTRIBUTION VOLUME</text>',
        '<text x="650" y="469" fill="#40575e" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="9">WINDOWS = ACTIVITY SIGNAL  ·  ROADS = TIME/CITY GRID</text>',
        '<text x="650" y="486" fill="#2d434a" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="9">AUTO-GENERATED BY GITHUB ACTIONS</text>',
        "</svg>",
    ]

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as file:
        file.write("\n".join(parts))

if __name__ == "__main__":
    main()

# renderer revision 2
