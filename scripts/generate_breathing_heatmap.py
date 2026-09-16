import json
import math
import urllib.request
from datetime import date, timedelta
from pathlib import Path

USERNAME = "Likethan"
API = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}?y=last"
OUT = Path("output/contribution-wave.svg")

# REAL DATA + FLOW FIELD RENDERER: GitHub activity drives the visual intensity.
with urllib.request.urlopen(API, timeout=30) as response:
    payload = json.load(response)

contributions = payload.get("contributions", [])
by_date = {item["date"]: item for item in contributions}

end = date.today()
start = end - timedelta(days=364)
start -= timedelta(days=(start.weekday() + 1) % 7)

days = []
cur = start
while cur <= end:
    days.append(cur)
    cur += timedelta(days=1)

weeks = (len(days) + 6) // 7
cell = 18
gap = 6
left = 64
top = 74
width = left * 2 + weeks * (cell + gap) - gap
height = 360

palette = ["#11131a", "#24124d", "#47228a", "#7041cf", "#b88cff"]

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
    '<title id="title">Likethan — Flow Field GitHub Contribution Heatmap</title>',
    '<desc id="desc">A real GitHub contribution calendar rendered as a continuously moving flow field. Contribution intensity controls particle density, movement and glow.</desc>',
    '<defs>',
    '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#030406"/><stop offset=".55" stop-color="#090b12"/><stop offset="1" stop-color="#11131b"/></linearGradient>',
    '<filter id="softGlow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
    '<filter id="strongGlow" x="-200%" y="-200%" width="400%" height="400%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
    '</defs>',
    f'<rect width="{width}" height="{height}" rx="24" fill="url(#bg)"/>',
    f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="23" fill="none" stroke="#fff" stroke-opacity=".08"/>',
    '<text x="28" y="32" fill="#f8fafc" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="15" font-weight="800" letter-spacing="2.8">FLOW FIELD</text>',
    f'<text x="{width-28}" y="32" text-anchor="end" fill="#737985" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="10" letter-spacing="1.7">GITHUB ACTIVITY • {end.isoformat()}</text>',
    f'<g transform="translate({left} {top})">'
]

# Every cell is derived from the live contribution API. Active cells become
# local flow sources: stronger activity means brighter, faster currents.
for i, d in enumerate(days):
    item = by_date.get(d.isoformat(), {})
    count = int(item.get("count", 0))
    level = int(item.get("level", 0))
    col = i // 7
    row = i % 7
    x = col * (cell + gap)
    y = row * (cell + gap)
    fill = palette[max(0, min(4, level))]

    if level == 0:
        svg.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="4" fill="{fill}"/>')
        continue

    phase = (col * 0.42 + row * 0.71) % (math.pi * 2)
    duration = max(2.8, 7.0 - level * 0.7)
    delay = -((col * 0.23 + row * 0.37) % duration)
    travel = 5 + level * 1.8
    particle_r = 1.1 + level * 0.35
    opacity = 0.38 + level * 0.12

    c1x = x + cell * 0.15
    c1y = y + cell * (0.75 - 0.10 * math.sin(phase))
    c2x = x + cell * 0.72
    c2y = y + cell * (0.20 + 0.12 * math.cos(phase))
    path = f'M {x-3} {y+cell*0.62:.2f} C {c1x:.2f} {c1y:.2f}, {c2x:.2f} {c2y:.2f}, {x+cell+3} {y+cell*0.38:.2f}'

    svg.append('<g filter="url(#softGlow)">')
    svg.append(
        f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="4" fill="{fill}">'
        f'<title>{d.isoformat()} — {count} contribution{"s" if count != 1 else ""}</title>'
        f'<animate attributeName="opacity" values=".58;{min(1, opacity + 0.25):.2f};.58" dur="{duration:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
        f'<animate attributeName="rx" values="4;7;5;4" dur="{duration * 1.15:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
        f'</rect>'
    )
    svg.append(
        f'<path d="{path}" fill="none" stroke="#d5b8ff" stroke-opacity=".24" stroke-width="{0.7 + level*0.18:.2f}" stroke-linecap="round" stroke-dasharray="{travel:.1f} {travel*1.7:.1f}">'
        f'<animate attributeName="stroke-dashoffset" from="0" to="-{travel*2.7:.1f}" dur="{duration:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
        f'</path>'
    )
    svg.append(
        f'<circle cx="{x + cell*0.18:.2f}" cy="{y + cell*0.62:.2f}" r="{particle_r:.2f}" fill="#e9dcff" opacity="0">'
        f'<animate attributeName="cx" values="{x + cell*0.15:.2f};{x + cell*0.50:.2f};{x + cell*0.88:.2f};{x + cell*0.15:.2f}" dur="{duration:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
        f'<animate attributeName="cy" values="{y + cell*0.62:.2f};{y + cell*0.46:.2f};{y + cell*0.38:.2f};{y + cell*0.62:.2f}" dur="{duration:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="0;{min(1, 0.55 + level*0.1):.2f};0" dur="{duration:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
        f'</circle>'
    )
    svg.append('</g>')

# Global streamlines make the individual cell currents read as one field.
for lane in range(7):
    y0 = 40 + lane * 34
    amp = 8 + lane * 1.5
    path = f'M -24 {y0} C {width*0.22:.1f} {y0-amp:.1f}, {width*0.46:.1f} {y0+amp:.1f}, {width*0.70:.1f} {y0} S {width+8:.1f} {y0-amp:.1f}, {width+24:.1f} {y0+amp/2:.1f}'
    dur = 11 + lane * 1.4
    svg.append(
        f'<path d="{path}" fill="none" stroke="#9c6cff" stroke-opacity=".065" stroke-width="1.2" stroke-linecap="round" stroke-dasharray="2 18">'
        f'<animate attributeName="stroke-dashoffset" from="0" to="-220" dur="{dur:.1f}s" repeatCount="indefinite"/>'
        f'</path>'
    )

svg += [
    '</g>',
    f'<g transform="translate({left} {height-42})" font-family="Inter,Segoe UI,Arial,sans-serif">',
    '<text x="0" y="0" fill="#687080" font-size="9" letter-spacing="1.5">LESS</text>',
    '<rect x="40" y="-9" width="14" height="14" rx="3" fill="#11131a"/>',
    '<rect x="62" y="-9" width="14" height="14" rx="3" fill="#24124d"/>',
    '<rect x="84" y="-9" width="14" height="14" rx="3" fill="#47228a"/>',
    '<rect x="106" y="-9" width="14" height="14" rx="3" fill="#7041cf"/>',
    '<rect x="128" y="-9" width="14" height="14" rx="3" fill="#b88cff"/>',
    '<text x="154" y="0" fill="#687080" font-size="9" letter-spacing="1.5">MORE</text>',
    f'<text x="{width-left}" y="0" text-anchor="end" fill="#687080" font-size="9" letter-spacing="1.5">{sum(int(x.get("count", 0)) for x in contributions)} CONTRIBUTIONS • REAL GITHUB DATA</text>',
    '</g>',
    '</svg>'
]

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("".join(svg), encoding="utf-8")
print(f"Generated {OUT} from {len(contributions)} GitHub contribution records with flow-field animation.")
