import json
import urllib.request
from datetime import date, timedelta
from pathlib import Path

USERNAME = "Likethan"
API = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}?y=last"
OUT = Path("output/contribution-wave.svg")

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
    '<title id="title">Likethan — Morphing GitHub Contribution Heatmap</title>',
    '<desc id="desc">A real GitHub contribution calendar generated from the latest public contribution data. Active cells breathe and morph between rounded shapes according to contribution intensity.</desc>',
    '<defs>',
    '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#030406"/><stop offset=".55" stop-color="#090b12"/><stop offset="1" stop-color="#11131b"/></linearGradient>',
    '<filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
    '</defs>',
    f'<rect width="{width}" height="{height}" rx="24" fill="url(#bg)"/>',
    f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="23" fill="none" stroke="#fff" stroke-opacity=".08"/>',
    '<text x="28" y="32" fill="#f8fafc" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="15" font-weight="800" letter-spacing="2.8">MORPHING HEATMAP</text>',
    f'<text x="{width-28}" y="32" text-anchor="end" fill="#737985" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="10" letter-spacing="1.7">GITHUB ACTIVITY • {end.isoformat()}</text>',
    f'<g transform="translate({left} {top})">'
]

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
    else:
        duration = max(1.8, 5.4 - level * 0.65)
        delay = -((col * 0.17 + row * 0.31) % duration)
        morph = 2.6 + level * 0.18
        svg.append(
            f'<g filter="url(#glow)">'
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="4" fill="{fill}">'
            f'<title>{d.isoformat()} — {count} contribution{"s" if count != 1 else ""}</title>'
            f'<animate attributeName="opacity" values=".70;1;.70" dur="{duration:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="x" values="{x};{x-2};{x+1};{x}" dur="{morph:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="y" values="{y};{y+1};{y-2};{y}" dur="{morph:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="width" values="{cell};{cell+4};{cell-2};{cell}" dur="{morph:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="height" values="{cell};{cell-2};{cell+4};{cell}" dur="{morph:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="rx" values="4;10;6;4" dur="{morph:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
            f'</rect>'
            f'<rect x="{x-2}" y="{y-2}" width="{cell+4}" height="{cell+4}" rx="6" fill="none" stroke="#b88cff" stroke-opacity="0">'
            f'<animate attributeName="stroke-opacity" values="0;.34;0" dur="{duration:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="rx" values="6;12;6" dur="{morph:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
            f'</rect></g>'
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
print(f"Generated {OUT} from {len(contributions)} GitHub contribution records with morphing cells.")
