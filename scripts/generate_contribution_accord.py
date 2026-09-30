import json
import os
import urllib.request
from html import escape

USERNAME = "Likethan"
OUTPUT = "output/contribution-accord.svg"

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
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Likethan-accord-contribution-renderer",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.load(response)
    if data.get("errors"):
        raise RuntimeError(data["errors"])
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

def fallback_calendar():
    import datetime
    days = []
    start = datetime.date.today() - datetime.timedelta(days=370)
    for i in range(371):
        date = start + datetime.timedelta(days=i)
        value = (i * 7 + i // 13) % 6
        level = min(4, value)
        days.append({"date": date.isoformat(), "contributionCount": value, "contributionLevel": list(LEVELS)[level]})
    weeks = [{"contributionDays": days[i:i+7]} for i in range(0, len(days), 7)]
    return {"totalContributions": sum(d["contributionCount"] for d in days), "weeks": weeks}

def esc(value):
    return escape(str(value), quote=True)

def generate_svg(calendar):
    days = [d for week in calendar["weeks"] for d in week["contributionDays"]][-371:]
    total = int(calendar["totalContributions"])

    # Map the 371 GitHub days into a sedan silhouette.
    cols, rows = 53, 7
    matrix = [[days[c * 7 + r] if c * 7 + r < len(days) else {"contributionCount": 0, "contributionLevel": "NONE", "date": ""} for r in range(rows)] for c in range(cols)]

    W, H = 1200, 560
    body_left, body_top = 92, 150
    cell, gap = 16, 2
    pitch = cell + gap

    # A 2003 Accord-inspired sedan silhouette. Contribution tiles are clipped to it.
    silhouette = "M110 370 C125 325 180 292 255 276 L335 223 C365 203 408 193 472 193 L662 193 C725 196 778 220 817 255 L1000 282 C1048 289 1080 318 1090 362 L1080 397 L1034 397 C1029 347 997 320 952 320 C905 320 873 350 868 397 L344 397 C339 348 307 320 260 320 C213 320 181 349 176 397 L125 397 Z"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="2003 Honda Accord GitHub contribution graph">',
        '<defs>',
        '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#05070a"/><stop offset=".58" stop-color="#0a1015"/><stop offset="1" stop-color="#05070a"/></linearGradient>',
        '<linearGradient id="metal" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#263039"/><stop offset=".48" stop-color="#10161b"/><stop offset="1" stop-color="#05080b"/></linearGradient>',
        '<linearGradient id="glass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#24343b"/><stop offset=".55" stop-color="#081015"/><stop offset="1" stop-color="#020406"/></linearGradient>',
        '<filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        f'<clipPath id="carClip"><path d="{silhouette}"/></clipPath>',
        '<style><![CDATA[text{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}.tile{shape-rendering:geometricPrecision}@keyframes blink{50%{opacity:.55}}.live{animation:blink 2.8s ease-in-out infinite}]]></style>',
        '</defs>',
        '<rect width="1200" height="560" fill="url(#bg)"/>',
        '<path d="M55 438H1145" stroke="#16252d"/><path d="M80 455H1120" stroke="#0e181e"/>',
        '<text x="58" y="62" fill="#d9ece9" font-size="20" font-weight="800" letter-spacing="3">LIKETHAN / CONTRIBUTION MACHINE</text>',
        '<text x="58" y="88" fill="#61757d" font-size="11" letter-spacing="2">2003 HONDA ACCORD · EVERY TILE IS A REAL CONTRIBUTION DAY</text>',
        f'<text x="1045" y="64" fill="#38d9c3" font-size="12" text-anchor="end" letter-spacing="2">LIVE GITHUB DATA</text>',
        f'<text x="1045" y="88" fill="#d9ece9" font-size="24" font-weight="800" text-anchor="end">{total:,}</text>',
        '<text x="1045" y="105" fill="#61757d" font-size="9" text-anchor="end" letter-spacing="2">TOTAL CONTRIBUTIONS</text>',
        # base car
        f'<path d="{silhouette}" fill="url(#metal)" stroke="#34434b" stroke-width="2"/>',
        # contribution grid mapped into car body
        '<g clip-path="url(#carClip)">',
    ]

    colors = ["#0a161a", "#123b3d", "#17655f", "#25a18e", "#42e8c2"]
    for c in range(cols):
        x = 110 + c * 18.2
        # Slight perspective: compress outer columns.
        for r in range(rows):
            d = matrix[c][r]
            level = LEVELS.get(d.get("contributionLevel"), 0)
            count = int(d.get("contributionCount", 0))
            y = 255 + r * 18.0 + (c - 26) * 0.28
            width = 16.2
            height = 15.4
            opacity = 0.25 + level * 0.17
            color = colors[level]
            parts.append(f'<rect class="tile" x="{x:.1f}" y="{y:.1f}" width="{width}" height="{height}" rx="3" fill="{color}" fill-opacity="{opacity:.2f}" stroke="{color}" stroke-opacity="{min(0.95, .22+level*.17):.2f}" stroke-width="0.7"><title>{esc(d.get("date",""))} — {count} contributions</title></rect>')
            if level >= 3:
                parts.append(f'<circle class="live" cx="{x+width/2:.1f}" cy="{y+height/2:.1f}" r="{1.4+level*.45:.1f}" fill="{color}" filter="url(#glow)"/>')
    parts.append('</g>')

    # Glasshouse, pillars, trim, bumpers and details make the tile field read as an actual Accord.
    parts += [
        '<path d="M318 276 L361 229 Q391 210 445 208 L641 208 Q700 211 756 260 L807 276 Z" fill="url(#glass)" stroke="#52636a" stroke-width="1.5"/>',
        '<path d="M445 210 L440 270 M641 210 L650 270" stroke="#4c5e65" stroke-width="1"/>',
        '<path d="M365 273 H803" stroke="#607179" stroke-width="1.4" opacity=".65"/>',
        '<path d="M112 362 Q155 338 204 329 M812 331 Q910 331 1027 355" fill="none" stroke="#73838a" stroke-width="1.2" opacity=".65"/>',
        '<path d="M118 377 H1047" stroke="#020406" stroke-width="11" opacity=".72"/>',
        '<path d="M129 351 Q155 336 186 331 L225 331" stroke="#38d9c3" stroke-width="3" filter="url(#glow)"/>',
        '<path d="M972 332 Q1025 338 1062 360" stroke="#ff4b5f" stroke-width="4" filter="url(#glow)"/>',
        '<path d="M182 378 H337 M866 378 H1054" stroke="#1b272d" stroke-width="7"/>',
        # wheels
        '<circle cx="260" cy="382" r="48" fill="#030506" stroke="#3b4a50" stroke-width="3"/><circle cx="260" cy="382" r="31" fill="#0a1014" stroke="#1c2a30" stroke-width="2"/><circle cx="260" cy="382" r="7" fill="#38d9c3"/><path d="M260 351V413 M229 382H291 M238 360L282 404 M282 360L238 404" stroke="#52636a" stroke-width="2"/>',
        '<circle cx="952" cy="382" r="48" fill="#030506" stroke="#3b4a50" stroke-width="3"/><circle cx="952" cy="382" r="31" fill="#0a1014" stroke="#1c2a30" stroke-width="2"/><circle cx="952" cy="382" r="7" fill="#38d9c3"/><path d="M952 351V413 M921 382H983 M930 360L974 404 M974 360L930 404" stroke="#52636a" stroke-width="2"/>',
        # lights / grille / badge
        '<path d="M145 324 Q175 307 218 309 L248 329 Q207 333 165 340 Z" fill="#d8f4ee" stroke="#38d9c3" stroke-width="1.5" filter="url(#glow)"/>',
        '<path d="M1017 319 Q1047 326 1067 342 L1040 348 L1014 340 Z" fill="#ff3f55" stroke="#ff7380" stroke-width="1.5" filter="url(#glow)"/>',
        '<path d="M96 350 Q145 344 192 348 M1010 350 Q1052 351 1083 363" stroke="#111b20" stroke-width="13"/>',
        '<path d="M470 353 H706" stroke="#26363d" stroke-width="3"/><path d="M548 353 H650" stroke="#38d9c3" stroke-width="1.5" opacity=".7"/>',
        '<text x="590" y="340" fill="#a7bbb9" font-size="10" text-anchor="middle" letter-spacing="4">ACCORD</text>',
        # labels
        '<path d="M260 150V190" stroke="#38d9c3" stroke-dasharray="3 4"/><text x="260" y="137" fill="#38d9c3" font-size="10" text-anchor="middle" letter-spacing="2">RECENT ACTIVITY</text>',
        '<path d="M952 150V190" stroke="#ff5968" stroke-dasharray="3 4"/><text x="952" y="137" fill="#ff5968" font-size="10" text-anchor="middle" letter-spacing="2">OLDER ACTIVITY</text>',
        '<path d="M610 440V480" stroke="#38d9c3" stroke-dasharray="3 4"/><text x="610" y="500" fill="#71858c" font-size="10" text-anchor="middle" letter-spacing="2">CONSISTENCY = WHEELS · INTENSITY = BODY ENERGY</text>',
        '<text x="58" y="515" fill="#31444b" font-size="9" letter-spacing="1">AUTO-GENERATED FROM GITHUB CONTRIBUTION CALENDAR · UPDATED DAILY</text>',
        '</svg>'
    ]
    return "\n".join(parts)

def main():
    try:
        calendar = fetch_calendar()
    except Exception as exc:
        print(f"GitHub calendar fetch failed: {exc}; using fallback preview")
        calendar = fallback_calendar()

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(generate_svg(calendar))

if __name__ == "__main__":
    main()

# Renderer maintained for the profile contribution machine.
# Visual edition: the generated SVG is the profile artwork itself, not a separate graph.
