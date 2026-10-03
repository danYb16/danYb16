"""
Builds everything on the profile that carries live numbers.

  assets/figure-wide.svg     the ticket figure, drawn for a desktop column
  assets/figure-narrow.svg   the same figure, drawn for a phone
  README.md                  the values between <!--live:key--> markers

The rules this file lives by:

1. Text is markdown. GitHub reflows it on a phone and themes it for free, so
   anything that is a sentence stays out of the artwork.

2. The one figure is drawn twice. A 700px drawing scaled onto a phone arrives
   at half size, so the README swaps in a 360px drawing through
   <picture media>. Both are rebuilt from the same numbers.

3. No background and no near-black or near-white ink. The figure sits on
   GitHub's light and dark canvases alike, so every colour has to hold on
   both. <picture> could switch on theme as well, but GitHub rewrites those
   media queries itself and combining them with a width query is untested.

4. Nothing describes how the products work inside. Facts stay at the level of
   the public marketing sites.

Fail closed: a source that is down or has changed shape raises before anything
is written, so CI keeps the last good commit. The two sources are independent;
one dead source does not block the other, and the run still exits non-zero.

Run:  python tools/build.py [--user danYb16]
"""

import argparse
import json
import re
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
README = ROOT / "README.md"

STATS_URL = "https://api.aiticketbot.com/stats/global"
CONTRIB_URL = "https://github.com/users/{user}/contributions"
UA = "danYb16-profile"

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

# Each holds at least 3:1 on both #ffffff and #0d1117.
AMBER = "#d9730d"
INK = "#767d86"
REST = "#8b949e"  # drawn at 30% opacity


def get(url: str, headers: dict | None = None) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "replace")


# --------------------------------------------------------------------------
# figure
# --------------------------------------------------------------------------


def text(x, y, content, *, size, fill=INK, weight=400, anchor="start"):
    attrs = f'x="{x}" y="{y}" font-size="{size}" fill="{fill}"'
    if weight != 400:
        attrs += f' font-weight="{weight}"'
    if anchor != "start":
        attrs += f' text-anchor="{anchor}"'
    return f"<text {attrs}>{content}</text>"


def waffle(y, width, cols, rows, share, *, gap, by_column):
    """100 cells, `share` of them amber. Filled along the short axis so the
    amber cells form one block instead of a scatter."""
    cell = (width - gap * (cols - 1)) / cols
    out = []
    for i in range(cols * rows):
        col, row = (i // rows, i % rows) if by_column else (i % cols, i // cols)
        on = i < share
        out.append(
            f'<rect x="{col * (cell + gap):.1f}" y="{y + row * (cell + gap):.1f}" '
            f'width="{cell:.1f}" height="{cell:.1f}" rx="{cell * 0.18:.1f}" '
            f'fill="{AMBER if on else REST}"'
            + ("" if on else ' opacity="0.3"') + "/>"
        )
    return "".join(out), rows * cell + (rows - 1) * gap


def svg(width, height, label, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height:.0f}" viewBox="0 0 {width} {height:.0f}" role="img" '
        f'aria-label="{label}" font-family="{SANS}">{body}</svg>\n'
    )


def figure_wide(s):
    grid, grid_h = waffle(104, 700, 25, 4, s["share"], gap=6, by_column=True)
    foot = 104 + grid_h + 28
    body = (
        text(0, 52, s["tickets"], size=56, fill=AMBER, weight=700)
        + text(0, 80, f'tickets handled across {s["servers"]} Discord servers', size=15)
        + text(700, 52, s["reply"], size=56, weight=700, anchor="end")
        + text(700, 80, "average first reply", size=15, anchor="end")
        + grid
        + f'<rect x="0" y="{foot - 10:.1f}" width="10" height="10" rx="2" fill="{AMBER}"/>'
        + text(18, foot, f'{s["share"]} of every 100 tickets resolved by AI', size=13)
        + text(700, foot, f'Updated {s["stamp"]}', size=12, anchor="end")
    )
    return svg(700, foot + 8, s["label"], body)


def figure_narrow(s):
    grid, grid_h = waffle(128, 360, 20, 5, s["share"], gap=4, by_column=True)
    foot = 128 + grid_h + 30
    body = (
        text(0, 54, s["tickets"], size=60, fill=AMBER, weight=700)
        + text(0, 82, "tickets handled across", size=16)
        + text(0, 104, f'{s["servers"]} Discord servers', size=16)
        + grid
        + f'<rect x="0" y="{foot - 11:.1f}" width="11" height="11" rx="2" fill="{AMBER}"/>'
        + text(20, foot, f'{s["share"]} of every 100 resolved by AI', size=15)
        + f'<text x="0" y="{foot + 44:.1f}" fill="{INK}">'
          f'<tspan font-size="30" font-weight="700">{s["reply"]}</tspan>'
          f'<tspan font-size="15" dx="8">average first reply</tspan></text>'
        + text(0, foot + 72, f'Updated {s["stamp"]}', size=12)
    )
    return svg(360, foot + 80, s["label"], body)


def stats():
    data = json.loads(get(STATS_URL, {"Accept": "application/json"}))
    servers = int(data["servers"])
    tickets = int(data["tickets_total"])
    resolved = int(data["ai_resolved"])
    seconds = float(data["ai_response_seconds"])
    if not (servers and tickets):
        raise SystemExit("stats endpoint returned zeroes; refusing to write")

    share = round(resolved / tickets * 100)
    today = datetime.now(timezone.utc)
    s = {
        "tickets": f"{tickets:,}",
        "servers": f"{servers:,}",
        "share": share,
        "reply": f"{seconds:.1f}s",
        "stamp": f"{today.day} {today:%b %Y}",
    }
    s["label"] = (
        f'AI Ticket Bot: {s["tickets"]} tickets handled across {s["servers"]} '
        f'Discord servers, {share} of every 100 resolved by AI, '
        f'{s["reply"]} average first reply.'
    )
    return s


# --------------------------------------------------------------------------
# activity
# --------------------------------------------------------------------------

DAY_RE = re.compile(
    r'<td[^>]*?data-date="(\d{4}-\d{2}-\d{2})"'
    r'[^>]*?id="contribution-day-component-(\d+)-(\d+)"',
    re.S,
)
TIP_RE = re.compile(
    r'<tool-tip[^>]*?for="contribution-day-component-(\d+)-(\d+)"[^>]*?>'
    r"([^<]*)</tool-tip>",
    re.S,
)
COUNT_RE = re.compile(r"^([\d,]+)\s+contribution")


def activity(user: str):
    """The public contribution feed, which already honours the "include
    private contributions" profile setting."""
    html = get(
        CONTRIB_URL.format(user=user),
        {"Accept": "text/html", "X-Requested-With": "XMLHttpRequest"},
    )
    counts = {}
    for row, col, label in TIP_RE.findall(html):
        match = COUNT_RE.match(label.strip())
        counts[(int(row), int(col))] = (
            int(match.group(1).replace(",", "")) if match else 0
        )
    days = [
        (date.fromisoformat(iso), counts.get((int(row), int(col)), 0))
        for iso, row, col in DAY_RE.findall(html)
    ]
    if len(days) < 300:
        raise SystemExit(
            f"parsed only {len(days)} days; GitHub's markup probably changed"
        )
    return {
        "contributions": f"{sum(c for _, c in days):,}",
        "active_days": str(sum(1 for _, c in days if c)),
    }


# --------------------------------------------------------------------------


def patch_readme(values: dict) -> None:
    """Replaces the text between <!--live:key--> and <!--/live--> markers."""
    source = README.read_text(encoding="utf-8")
    patched = re.sub(
        r"(<!--live:(\w+)-->)(.*?)(<!--/live-->)",
        lambda m: m.group(1) + values.get(m.group(2), m.group(3)) + m.group(4),
        source,
        flags=re.S,
    )
    if patched != source:
        README.write_text(patched, encoding="utf-8", newline="\n")
        print("  patched README.md")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", default="danYb16")
    args = parser.parse_args()

    values, failures = {}, []

    try:
        s = stats()
        ASSETS.mkdir(parents=True, exist_ok=True)
        for name, build in (("figure-wide", figure_wide), ("figure-narrow", figure_narrow)):
            (ASSETS / f"{name}.svg").write_text(build(s), encoding="utf-8", newline="\n")
            print(f"  wrote assets/{name}.svg")
        values.update(servers=s["servers"], tickets=s["tickets"])
    except Exception as error:
        print(f"stats: FAILED, keeping the committed figure ({error})")
        failures.append("stats")

    try:
        values.update(activity(args.user))
    except Exception as error:
        print(f"activity: FAILED, keeping the committed numbers ({error})")
        failures.append("activity")

    patch_readme(values)

    if failures:
        raise SystemExit(f"failed: {', '.join(failures)}")


if __name__ == "__main__":
    main()
