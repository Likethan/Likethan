import json
import os
import random
import urllib.request
from PIL import Image, ImageDraw

USERNAME = "Likethan"
OUTPUT = "dist/contribution-city.gif"
WIDTH, HEIGHT = 980, 360
FRAMES = 24
FRAME_MS = 120

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
            "User-Agent": "Likethan-contribution-city",
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
    total = calendar["totalContributions"]
    random.seed(20260912)

    # Convert the real 52-week contribution calendar into a skyline.
    buildings = []
    left = 34
    base_y = 305
    cell_w = 17

    for wi, week in enumerate(calendar["weeks"]):
        for di, day in enumerate(week["contributionDays"]):
            count = int(day["contributionCount"])
            level = level_value(day["contributionLevel"])
            if level == 0:
                continue
            x = left + wi * cell_w
            # Contribution intensity controls building height.
            height = 22 + level * 26 + min(count, 35) * 2.4
            height = min(height, 210)
            buildings.append({
                "x": x,
                "y": base_y - height,
                "w": 12,
                "h": height,
                "level": level,
                "count": count,
                "seed": wi * 7 + di,
            })

    # Background skyline silhouettes make the active contribution buildings stand out.
    silhouettes = []
    x = 0
    while x < WIDTH:
        w = random.choice([18, 24, 30, 36])
        h = random.randint(35, 110)
        silhouettes.append((x, base_y - h, w, h))
        x += w + random.randint(3, 9)

    # Flying pixel cars / drones provide subtle motion between frames.
    vehicles = [
        {"x": random.randint(0, WIDTH), "y": random.choice([220, 245, 270]), "speed": random.choice([2, 3, 4])}
        for _ in range(7)
    ]

    frames = []
    for frame_no in range(FRAMES):
        img = Image.new("RGB", (WIDTH, HEIGHT), (6, 8, 18))
        draw = ImageDraw.Draw(img)

        # Pixel-art dusk gradient.
        for y in range(HEIGHT):
            t = y / HEIGHT
            r = int(7 + 9 * t)
            g = int(9 + 7 * t)
            b = int(22 + 20 * t)
            draw.line((0, y, WIDTH, y), fill=(r, g, b))

        # Moon and tiny pixel stars.
        draw.ellipse((790, 42, 842, 94), fill=(220, 224, 245))
        draw.rectangle((807, 49, 820, 58), fill=(195, 199, 222))
        draw.rectangle((796, 70, 809, 80), fill=(198, 201, 222))

        random.seed(7000)
        for _ in range(95):
            sx = random.randint(12, WIDTH - 12)
            sy = random.randint(35, 175)
            size = random.choice([1, 1, 1, 2])
            draw.rectangle((sx, sy, sx + size, sy + size), fill=(185, 193, 225))

        # Distant city.
        for x, y, w, h in silhouettes:
            draw.rectangle((x, y, x + w, base_y), fill=(13, 17, 33))
            for wy in range(int(y) + 10, base_y - 8, 13):
                for wx in range(x + 5, x + w - 4, 10):
                    if (wx + wy + frame_no) % 5 == 0:
                        draw.rectangle((wx, wy, wx + 3, wy + 4), fill=(108, 92, 150))

        # Ground / street grid.
        draw.rectangle((0, base_y, WIDTH, HEIGHT), fill=(9, 11, 22))
        draw.line((0, base_y, WIDTH, base_y), fill=(71, 61, 103), width=2)
        for y in range(base_y + 18, HEIGHT, 18):
            draw.line((0, y, WIDTH, y), fill=(18, 21, 38))
        for x in range(0, WIDTH, 34):
            draw.line((x, base_y, x - 20, HEIGHT), fill=(16, 19, 34))

        # Real contribution days become pixel buildings.
        for building in buildings:
            x, y, w, h = building["x"], building["y"], building["w"], building["h"]
            level, count, seed = building["level"], building["count"], building["seed"]

            # Building body and roof.
            body = [(20, 25), (31, 38), (45, 58), (61, 76)][level]
            roof = [(30, 34), (47, 43), (72, 62), (104, 85)][level]
            highlight = [(56, 58), (83, 82), (125, 110), (174, 151)][level]
            draw.rectangle((x, y, x + w, base_y), fill=body)
            draw.rectangle((x, y, x + w, y + 3), fill=roof)
            draw.rectangle((x + 2, y + 4, x + 3, base_y - 1), fill=highlight)

            # Windows pulse based on frame, with more activity on stronger days.
            window_gap = 11
            for wy in range(int(y) + 10, base_y - 5, window_gap):
                for wx in range(x + 3, x + w - 1, 5):
                    lit = ((seed * 13 + wy + wx + frame_no * (level + 1)) % 17) < (3 + level)
                    if lit:
                        draw.rectangle((wx, wy, wx + 2, wy + 3), fill=(218, 196, 126))

            # Antenna on high-contribution buildings.
            if level >= 3:
                draw.rectangle((x + w // 2, y - 10, x + w // 2 + 1, y), fill=(139, 123, 190))
                if (frame_no + seed) % 8 < 4:
                    draw.rectangle((x + w // 2, y - 13, x + w // 2 + 1, y - 12), fill=(220, 205, 255))

        # Animated pixel traffic.
        for vehicle in vehicles:
            vx = (vehicle["x"] + frame_no * vehicle["speed"]) % (WIDTH + 30) - 15
            vy = vehicle["y"]
            draw.rectangle((vx, vy, vx + 10, vy + 3), fill=(184, 151, 238))
            draw.rectangle((vx + 2, vy - 2, vx + 6, vy), fill=(111, 96, 150))
            draw.point((vx + 11, vy + 2), fill=(245, 220, 145))

        # Header and legend.
        draw.text((34, 17), "PIXEL CONTRIBUTION CITY", fill=(241, 238, 252))
        label = f"{total:,} contributions  ·  LAST 12 MONTHS"
        bbox = draw.textbbox((0, 0), label)
        draw.text((WIDTH - 34 - (bbox[2] - bbox[0]), 18), label, fill=(156, 157, 175))
        draw.text((34, 325), "EACH BUILDING = AN ACTIVE CONTRIBUTION DAY", fill=(112, 113, 130))
        draw.text((WIDTH - 230, 325), "LOW  ▪  ▪  ▪  ▪  HIGH", fill=(112, 113, 130))

        frames.append(img)

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
