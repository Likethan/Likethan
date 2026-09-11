import json
import math
import os
import random
import urllib.request
from PIL import Image, ImageDraw, ImageFilter

USERNAME = "Likethan"
OUTPUT = "dist/contribution-galaxy.gif"
WIDTH, HEIGHT = 980, 300
FRAMES = 32
FRAME_MS = 90

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


def lerp(a, b, t):
    return a + (b - a) * t


def main():
    calendar = fetch_calendar()
    total = calendar["totalContributions"]

    random.seed(20260911)
    left, top = 44, 58
    cell_x, cell_y = 17, 29

    contributions = []
    for wi, week in enumerate(calendar["weeks"]):
        for di, day in enumerate(week["contributionDays"]):
            level = level_value(day["contributionLevel"])
            count = int(day["contributionCount"])
            if level == 0:
                continue
            contributions.append({
                "x": left + wi * cell_x,
                "y": top + di * cell_y,
                "level": level,
                "count": count,
                "seed": wi * 7 + di,
            })

    stars = [
        (random.randint(18, WIDTH - 18), random.randint(45, HEIGHT - 22), random.choice([1, 1, 1, 2]))
        for _ in range(130)
    ]

    frames = []
    for frame_no in range(FRAMES):
        base = Image.new("RGB", (WIDTH, HEIGHT), (4, 4, 12))
        draw = ImageDraw.Draw(base)

        # Deep-space gradient.
        for y in range(HEIGHT):
            t = y / HEIGHT
            r = int(5 + 7 * (1 - abs(t - 0.5) * 2))
            g = int(4 + 4 * (1 - abs(t - 0.5) * 2))
            b = int(13 + 18 * (1 - abs(t - 0.5) * 2))
            draw.line((0, y, WIDTH, y), fill=(r, g, b))

        # Soft purple/blue nebula.
        glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse((80, 55, 900, 275), fill=(88, 52, 180, 45))
        gd.ellipse((250, 25, 760, 250), fill=(55, 65, 190, 30))
        glow = glow.filter(ImageFilter.GaussianBlur(38))
        base = Image.alpha_composite(base.convert("RGBA"), glow)
        draw = ImageDraw.Draw(base)

        for x, y, r in stars:
            alpha = random.choice([45, 60, 80, 105])
            draw.ellipse((x-r, y-r, x+r, y+r), fill=(205, 196, 255, alpha))

        # Header.
        draw.text((42, 15), "CONTRIBUTION GALAXY", fill=(245, 243, 255, 255))
        label = f"{total:,} contributions  ·  LAST 12 MONTHS"
        bbox = draw.textbbox((0, 0), label)
        draw.text((WIDTH - 42 - (bbox[2] - bbox[0]), 16), label, fill=(161, 161, 170, 255))

        # Real contribution days become moving meteors.
        for item in contributions:
            x, y = item["x"], item["y"]
            level, count, seed = item["level"], item["count"], item["seed"]
            phase = ((frame_no / FRAMES) + ((seed * 0.071) % 1.0)) % 1.0
            # Fade at the start/end so the meteor appears to shoot through the point.
            fade = math.sin(math.pi * phase)
            travel_x = 24 + level * 7
            travel_y = 13 + level * 5
            head_x = x + travel_x * phase
            head_y = y - travel_y * phase
            size = 2.0 + level * 0.9 + min(count, 25) * 0.055
            tail = 10 + level * 6 + min(count, 20) * 0.12

            # Layered tail for a cinematic glow.
            layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            tx = head_x - tail
            ty = head_y + tail * 0.52
            ld.line((tx, ty, head_x, head_y), fill=(167, 139, 250, int(80 * fade)), width=max(2, int(size)))
            layer = layer.filter(ImageFilter.GaussianBlur(3))
            base = Image.alpha_composite(base, layer)
            draw = ImageDraw.Draw(base)

            draw.line((tx, ty, head_x, head_y), fill=(221, 214, 254, int(165 * fade)), width=max(1, int(size * 0.65)))
            rr = max(1.2, size * (0.72 + 0.55 * fade))
            a = int(120 + 135 * fade)
            draw.ellipse((head_x-rr, head_y-rr, head_x+rr, head_y+rr), fill=(255, 255, 255, a))

        # A few independent long cinematic shooting stars.
        for meteor in range(8):
            sx = 80 + meteor * 120
            sy = 65 + (meteor * 41) % 145
            phase = ((frame_no / FRAMES) + meteor * 0.17) % 1.0
            mx = sx + 70 * phase
            my = sy - 38 * phase
            tail = 38
            draw.line((mx-tail, my+tail*0.55, mx, my), fill=(196, 181, 253, int(150 * math.sin(math.pi*phase))), width=2)
            draw.ellipse((mx-2, my-2, mx+2, my+2), fill=(255, 255, 255, 210))

        footer = "EACH METEOR REPRESENTS A DAY OF ACTIVITY"
        bbox = draw.textbbox((0, 0), footer)
        draw.text(((WIDTH - (bbox[2]-bbox[0]))/2, 282), footer, fill=(113, 113, 122, 255))

        frames.append(base.convert("RGB"))

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_MS,
        loop=0,
        optimize=True,
        disposal=2,
    )


if __name__ == "__main__":
    main()
