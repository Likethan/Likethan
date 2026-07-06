#!/usr/bin/env python3
"""
generate_readme.py
Simple GitHub profile README generator.
Saves README.md in current directory.
"""

import os
import json
import textwrap
from datetime import datetime
try:
    # Python 3 standard lib
    from urllib.request import urlopen, Request
except Exception:
    urlopen = None

def input_default(prompt, default=""):
    val = input(f"{prompt} [{'Enter' if default=='' else default}]: ").strip()
    return val if val else default

def fetch_github_user(username):
    if not username or urlopen is None:
        return None
    url = f"https://api.github.com/users/{username}"
    req = Request(url, headers={"User-Agent": "readme-generator"})
    try:
        with urlopen(req, timeout=10) as resp:
            return json.load(resp)
    except Exception:
        return None

def generate_badges(username, languages=None):
    badges = []
    if username:
        badges.append(f"[![GitHub followers](https://img.shields.io/github/followers/{username}?label=Follow&style=social)](https://github.com/{username})")
        badges.append(f"[![Top Langs](https://github-readme-stats.vercel.app/api/top-langs/?username={username}&layout=compact)](https://github.com/{username})")
        badges.append(f"[![Stats](https://github-readme-stats.vercel.app/api?username={username}&show_icons=true&count_private=true&theme=default)](https://github.com/{username})")
    if languages:
        # languages is a list; show as simple badges
        for lang in languages[:5]:
            badges.append(f"![{lang}](https://img.shields.io/badge/-{lang}-blue?style=flat-square)")
    return " ".join(badges)

def make_projects_section(projects):
    if not projects:
        return ""
    lines = ["## Projects\n"]
    for p in projects:
        title = p.get("name","Untitled")
        desc = p.get("desc","No description.")
        url = p.get("url","")
        if url:
            lines.append(f"- [{title}]({url}) — {desc}")
        else:
            lines.append(f"- **{title}** — {desc}")
    return "\n".join(lines) + "\n"

def main():
    print("GitHub README.md generator\n")
    username = input_default("GitHub username", "")
    name = input_default("Display name (Full name)", username)
    short_bio = input_default("One-line bio (what you do)", "Software developer | Open-source enthusiast")
    long_bio = input_default("Longer bio (2-3 sentences)", "")
    highlights = input_default("Top achievements / one-line bullets (comma-separated)", "")
    languages = input_default("Top languages/tech (comma-separated)", "")
    projects_raw = input_default("Add projects? (format: name|desc|url ; semicolon-separated)", "")
    contact = input_default("Email or contact line", "")
    linkedin = input_default("LinkedIn URL (optional)", "")
    twitter = input_default("Twitter handle (optional, without @)", "")

    gh_data = fetch_github_user(username) if username else None
    public_repos = gh_data.get("public_repos") if gh_data else None
    followers = gh_data.get("followers") if gh_data else None

    # Transform inputs
    top_langs = [s.strip() for s in languages.split(",") if s.strip()]
    projects = []
    if projects_raw.strip():
        for item in projects_raw.split(";"):
            parts = [p.strip() for p in item.split("|")]
            if len(parts) >= 3:
                projects.append({"name":parts[0],"desc":parts[1],"url":parts[2]})
            elif len(parts) == 2:
                projects.append({"name":parts[0],"desc":parts[1],"url":""})
            elif parts[0]:
                projects.append({"name":parts[0],"desc":"","url":""})

    badges_md = generate_badges(username, top_langs)

    # Build README content
    created = datetime.utcnow().strftime("%Y-%m-%d")
    lines = []
    lines.append(f"# Hi, I'm {name} 👋")
    lines.append("")
    lines.append(badges_md)
    lines.append("")
    lines.append(short_bio)
    lines.append("")
    if long_bio:
        lines.append(long_bio)
        lines.append("")
    if highlights:
        lines.append("## Highlights")
        for h in [x.strip() for x in highlights.split(",") if x.strip()]:
            lines.append(f"- {h}")
        lines.append("")
    if top_langs:
        lines.append("## Skills")
        lines.append(", ".join(top_langs))
        lines.append("")

    if public_repos is not None or followers is not None:
        lines.append("## GitHub")
        if public_repos is not None:
            lines.append(f"- Public repos: **{public_repos}**")
        if followers is not None:
            lines.append(f"- Followers: **{followers}**")
        lines.append("")

    lines.append(make_projects_section(projects))
    contact_lines = []
    if contact:
        contact_lines.append(f"- Email: {contact}")
    if linkedin:
        contact_lines.append(f"- LinkedIn: [{linkedin}]({linkedin})")
    if twitter:
        contact_lines.append(f"- Twitter: [@{twitter}](https://twitter.com/{twitter})")
    if contact_lines:
        lines.append("## Contact")
        lines.extend(contact_lines)
        lines.append("")

    lines.append("---")
    lines.append(f"_README generated on {created}_")
    content = "\n".join(lines).strip() + "\n"

    out = "README.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"README.md written to ./{out}")
    print("Open it, tweak, and commit to your profile repository (create a repo named the same as your GitHub username)")

if __name__ == "__main__":
    main()
