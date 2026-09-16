from __future__ import annotations

import datetime as dt
import html
import json
import math
import os
import urllib.parse
import urllib.request
from pathlib import Path

DAYS = 90
WIDTH = 1100
HEIGHT = 300
LEFT = 52
RIGHT = 24
TOP = 52
BOTTOM = 48
GRAPH_W = WIDTH - LEFT - RIGHT
GRAPH_H = HEIGHT - TOP - BOTTOM


def github_commit_counts() -> list[int]:
    """Count Likethan-authored commits on main for the last 90 days."""
    repo = os.environ.get("GITHUB_REPOSITORY", "Likethan/Likethan")
    token = os.environ.get("GITHUB_TOKEN", "")
    start = dt.date.today() - dt.timedelta(days=DAYS - 1)
    since = f"{start.isoformat()}T00:00:00Z"
    until = f"{(dt.date.today() + dt.timedelta(days=1)).isoformat()}T00:00:00Z"
    counts = {start + dt.timedelta(days=i): 0 for i in range(DAYS)}

    for page in range(1, 6):
        query = urllib.parse.urlencode(
            {
                "sha": "main",
                "author": "Likethan",
                "since": since,
                "until": until,
                "per_page": 100,
                "page": page,
            }
        )
        request = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/commits?{query}",
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2026-03-10",
                **({"Authorization": f"Bearer {token}"} if token else {}),
                "User-Agent": "Likethan-contribution-wave",
            },
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            commits = json.load(response)

        if not commits:
            break

        for commit in commits:
            date_text = commit.get("commit", {}).get("author", {}).get("date", "")
            if not date_text:
                continue
            day = dt.date.fromisoformat(date_text[:10])
            if day in counts:
                counts[day] += 1

        if len(commits) < 100:
            break

    return [counts[start + dt.timedelta(days=i)] for i in range(DAYS)]


def smooth_points(values: list[int]) -> list[tuple[float, float]]:
    peak = max(max(values), 1)
    points = []
    for i, value in enumerate(values):
        x = LEFT + (GRAPH_W * i / (len(values) - 1))
        normalized = value / peak
        y = TOP + GRAPH_H * (0.88 - 0.70 * math.sqrt(normalized))
        points.append((x, y))
    return points


def path_d(points: list[tuple[float, float]]) -> str:
    if not points:
        return ""
    commands = [f"M {points[0][0]:.1f} {points[0][1]:.1f}"]
    for i in range(1, len(points)):
        x0, y0 = points[i - 1]
        x1, y1 = points[i]
        xm = (x0 + x1) / 2
        commands.append(f"C {xm:.1f} {y0:.1f}, {xm:.1f} {y1:.1f}, {x1:.1f} {y1:.1f}")
    return " ".join(commands)


def main() -> None:
    values = github_commit_counts()
    points = smooth_points(values)
    wave = path_d(points)
    max_value = max(values) if values else 0
    total = sum(values)
    today = dt.date.today()

    dots = []
    for i, ((x, y), value) in enumerate(zip(points, values)):
        radius = 2.6 + min(value, max_value) * 0.12 if max_value else 2.6
        opacity = 0.35 + (0.65 * value / max_value if max_value else 0)
        delay = i * 0.035
        dots.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="url(#dot)" opacity="{opacity:.2f}">'
            f'<animate attributeName="r" values="{radius:.1f};{radius + 2.8:.1f};{radius:.1f}" dur="2.4s" begin="-{delay:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="{opacity:.2f};1;{opacity:.2f}" dur="2.4s" begin="-{delay:.2f}s" repeatCount="indefinite"/>'
            f'</circle>'
        )

    labels = []
    for index in [0, 29, 59, 89]:
        date = today - dt.timedelta(days=DAYS - 1 - index)
        labels.append(
            f'<text x="{points[index][0]:.1f}" y="{HEIGHT - 16}" fill="#64748B" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="10" text-anchor="middle">{html.escape(date.strftime("%b %d"))}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">Likethan's animated GitHub contribution wave</title>
  <desc id="desc">An animated 90-day contribution wave showing {total} commits authored by Likethan.</desc>
  <defs>
    <linearGradient id="line" x1="0" x2="1" y1="0" y2="0">
      <stop offset="0%" stop-color="#6E56CF"/>
      <stop offset="52%" stop-color="#8B5CF6"/>
      <stop offset="100%" stop-color="#38BDF8"/>
    </linearGradient>
    <linearGradient id="fill" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0%" stop-color="#7C5CFF" stop-opacity="0.28"/>
      <stop offset="100%" stop-color="#7C5CFF" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="dot">
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="30%" stop-color="#8B5CF6"/>
      <stop offset="100%" stop-color="#38BDF8"/>
    </radialGradient>
    <filter id="glow" x="-30%" y="-100%" width="160%" height="300%">
      <feGaussianBlur stdDeviation="5" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <clipPath id="clip"><rect x="{LEFT}" y="{TOP}" width="{GRAPH_W}" height="{GRAPH_H}" rx="14"/></clipPath>
  </defs>
  <rect width="100%" height="100%" rx="22" fill="#0B0D12"/>
  <rect x="1" y="1" width="{WIDTH - 2}" height="{HEIGHT - 2}" rx="21" fill="none" stroke="#202532"/>
  <text x="28" y="30" fill="#F8FAFC" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="16" font-weight="700">CONTRIBUTION WAVE</text>
  <text x="{WIDTH - 28}" y="30" fill="#94A3B8" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="12" text-anchor="end">90 DAYS · {total} COMMITS</text>
  <g opacity="0.22" stroke="#64748B" stroke-width="1">
    <line x1="{LEFT}" y1="{TOP + GRAPH_H * .18:.1f}" x2="{WIDTH - RIGHT}" y2="{TOP + GRAPH_H * .18:.1f}"/>
    <line x1="{LEFT}" y1="{TOP + GRAPH_H * .50:.1f}" x2="{WIDTH - RIGHT}" y2="{TOP + GRAPH_H * .50:.1f}"/>
    <line x1="{LEFT}" y1="{TOP + GRAPH_H * .82:.1f}" x2="{WIDTH - RIGHT}" y2="{TOP + GRAPH_H * .82:.1f}"/>
  </g>
  <g clip-path="url(#clip)">
    <path d="{wave} L {points[-1][0]:.1f} {TOP + GRAPH_H:.1f} L {points[0][0]:.1f} {TOP + GRAPH_H:.1f} Z" fill="url(#fill)"/>
    <path d="{wave}" fill="none" stroke="#7C5CFF" stroke-width="8" opacity="0.18" filter="url(#glow)"/>
    <path d="{wave}" fill="none" stroke="url(#line)" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1400" stroke-dashoffset="1400">
      <animate attributeName="stroke-dashoffset" from="1400" to="0" dur="2.8s" fill="freeze"/>
    </path>
    {''.join(dots)}
  </g>
  {''.join(labels)}
  <text x="28" y="{HEIGHT - 16}" fill="#64748B" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="10">LOW</text>
  <text x="{WIDTH - 28}" y="{HEIGHT - 16}" fill="#64748B" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="10" text-anchor="end">HIGH ACTIVITY</text>
</svg>
'''

    output = Path("output/contribution-wave.svg")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")
    print(f"Generated {output} — {total} commits across {DAYS} days (peak day: {max_value}).")


if __name__ == "__main__":
    main()
