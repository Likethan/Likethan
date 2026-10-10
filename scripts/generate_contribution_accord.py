import json
import os
import urllib.request
from datetime import date, timedelta
from PIL import Image, ImageDraw, ImageFont

USERNAME = "Likethan"
SOURCE_IMAGE = "asset/ChatGPT Image Sep 10, 2026, 04_12_00 PM.png"
TARGET_SIZE = (3840, 2160)
OUTPUT_IMAGE = "output/contribution-accord.jpg"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
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
    last_error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.load(response)
            break
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt == 2:
                raise RuntimeError(f"GitHub GraphQL request failed after 3 attempts: {exc}") from exc
            import time
            time.sleep(2 ** attempt)
    if data.get("errors"):
        raise RuntimeError(data["errors"])
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

def streaks(days):
    ordered = sorted(days, key=lambda d: d["date"])
    longest = current = 0
    run = 0
    today = date.today().isoformat()
    for d in ordered:
        if int(d["contributionCount"]) > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    for d in reversed(ordered):
        if int(d["contributionCount"]) > 0:
            current += 1
        elif d["date"] < today:
            break
    return longest, current

def font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def render(calendar):
    if not os.path.isfile(SOURCE_IMAGE):
        raise FileNotFoundError(
            f"Base Accord artwork not found at {SOURCE_IMAGE}. "
            "Keep the source PNG in the repository before running this workflow."
        )
    os.makedirs(os.path.dirname(OUTPUT_IMAGE), exist_ok=True)
    im = Image.open(SOURCE_IMAGE).convert("RGB")
    # Always start from the untouched source artwork and render in 4K UHD.
    im = im.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(im, "RGBA")
    w, h = im.size
    days = [d for week in calendar["weeks"] for d in week["contributionDays"]][-371:]
    total = int(calendar["totalContributions"])
    longest, current = streaks(days)

    # The uploaded artwork is the base. Only contribution-dependent regions are refreshed.
    sx, sy = w / 1672, h / 941

    # Contribution calendar area from the supplied artwork.
    gx0, gy0, gx1, gy1 = [int(v * s) for v, s in [(75, sx), (180, sy), (552, sx), (272, sy)]]
    draw.rounded_rectangle((gx0, gy0, gx1, gy1), radius=max(2, int(6*sx)), fill=(3, 12, 14, 205))

    cols, rows = 53, 7
    cell_w = max(1, int((gx1-gx0) / cols))
    cell_h = max(1, int((gy1-gy0) / rows))
    colors = [(8, 40, 38), (12, 70, 58), (20, 115, 88), (35, 178, 126), (65, 235, 175)]

    for i in range(cols * rows):
        if i >= len(days):
            break
        d = days[i]
        level = LEVELS.get(d.get("contributionLevel"), 0)
        x = gx0 + (i // rows) * cell_w
        y = gy0 + (i % rows) * cell_h
        pad = max(1, int(1*sx))
        draw.rounded_rectangle(
            (x+pad, y+pad, x+cell_w-pad, y+cell_h-pad),
            radius=max(1, int(2*sx)),
            fill=colors[level],
        )

    # Refresh the live stats panel while preserving the supplied composition.
    px0, py0, px1, py1 = int(1390*sx), int(175*sy), int(1660*sx), int(455*sy)
    draw.rectangle((px0, py0, px1, py1), fill=(2, 8, 12, 190))

    white = (225, 239, 238, 255)
    muted = (151, 176, 180, 255)
    green = (58, 239, 177, 255)

    f_big = font(max(7, int(20*sx)), True)
    f_small = font(max(5, int(11*sx)))
    f_label = font(max(5, int(9*sx)))

    stats = [
        ("TOTAL DAYS", len(days), 214),
        ("TOTAL CONTRIBUTIONS", f"{total:,}", 284),
        ("LONGEST STREAK", longest, 354),
        ("CURRENT STREAK", current, 424),
    ]
    for label, value, y in stats:
        yy = int(y * sy)
        draw.text((int(1450*sx), yy), str(value), fill=white, font=f_big)
        draw.text((int(1450*sx), yy + int(25*sy)), label, fill=muted, font=f_label)
        draw.ellipse(
            (int(1410*sx), yy + int(5*sy), int(1422*sx), yy + int(17*sy)),
            fill=green,
        )

    # Real contribution intensity on the car body.
    body_x0, body_y0 = int(390*sx), int(315*sy)
    body_x1, body_y1 = int(1190*sx), int(570*sy)
    for i, d in enumerate(days):
        level = LEVELS.get(d.get("contributionLevel"), 0)
        if level < 2:
            continue
        col = i % 40
        row = (i // 40) % 9
        x = body_x0 + int((body_x1-body_x0) * col / 40)
        y = body_y0 + int((body_y1-body_y0) * row / 9)
        r = max(1, int((1.0 + level * .45) * sx))
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(52, 238, 171, min(220, 80 + level*35)))

    im.save(OUTPUT_IMAGE, format="JPEG", quality=97, subsampling=0, optimize=True, progressive=True)
    with Image.open(OUTPUT_IMAGE) as check:
        if check.size != TARGET_SIZE:
            raise RuntimeError(f"Expected 4K output {TARGET_SIZE}, got {check.size}")
    if not os.path.isfile(OUTPUT_IMAGE) or os.path.getsize(OUTPUT_IMAGE) == 0:
        raise RuntimeError(f"Renderer did not produce a valid output file: {OUTPUT_IMAGE}")

def main():
    calendar = fetch_calendar()
    render(calendar)

if __name__ == "__main__":
    main()
