"""
Redraws the three panels that carry live state:

  assets/hero.svg      status lights from a real request to each product domain
  assets/stats.svg     the product's public stats endpoint
  assets/activity.svg  GitHub's public contribution feed

No tokens anywhere. The contribution feed already honours the "include private
contributions" profile setting, which matters because nearly all the work is in
private repositories.

Fail-closed rules:
  - A source that is down, rate limited or has changed shape raises, and
    nothing is written, so CI commits the previous panel instead of an empty
    one. The three tasks are independent; one dead source does not block the
    others, and the run still exits non-zero so the failure is visible.
  - A domain only shows DOWN after three attempts. If EVERY domain is
    unreachable the run assumes the runner's network is at fault and keeps the
    committed hero, because a false all-red board on a public profile is worse
    than a stale green one.

Run:  python tools/build_live.py [--user danYb16]
"""

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

from build_assets import DOMAINS, build_hero, build_stats, build_strip

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

STATS_URL = "https://api.aiticketbot.com/stats/global"
CONTRIB_URL = "https://github.com/users/{user}/contributions"
UA = "danYb16-profile-panels"


def get(url: str, headers: dict | None = None) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "replace")


def write(name: str, markup: str) -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    path = ASSETS / f"{name}.svg"
    path.write_text(markup, encoding="utf-8")
    print(f"  wrote {path.relative_to(ROOT)}")


# --------------------------------------------------------------------------
# hero status board
# --------------------------------------------------------------------------


def probe(domain: str) -> bool:
    """True if the site answered at all. Any HTTP status below 500 counts as
    up: a 403 from a bot shield is still a living site."""
    for attempt in range(3):
        try:
            request = urllib.request.Request(
                f"https://{domain}", headers={"User-Agent": UA}
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status < 500
        except urllib.error.HTTPError as error:
            return error.code < 500
        except Exception:
            time.sleep(2 * (attempt + 1))
    return False


def hero_panel():
    status = {domain: probe(domain) for domain in DOMAINS}
    print("status: " + ", ".join(
        f"{d} {'UP' if up else 'DOWN'}" for d, up in status.items()))
    if not any(status.values()):
        raise SystemExit(
            "every domain unreachable; assuming the runner's network is at "
            "fault and keeping the committed hero"
        )
    write("hero", build_hero(status))


# --------------------------------------------------------------------------
# product counters
# --------------------------------------------------------------------------


def compact(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def stats_strip():
    data = json.loads(get(STATS_URL, {"Accept": "application/json"}))
    servers = int(data["servers"])
    tickets = int(data["tickets_total"])
    resolved = int(data["ai_resolved"])
    seconds = float(data["ai_response_seconds"])

    if not (servers and tickets):
        raise SystemExit("stats endpoint returned zeroes; refusing to write")

    cells = [
        ("SERVERS", f"{servers:,}"),
        ("TICKETS HANDLED", compact(tickets)),
        ("RESOLVED BY AI", f"{round(resolved / tickets * 100)}%"),
        ("AVG FIRST REPLY", f"{seconds:.1f}s"),
    ]
    print("stats: " + ", ".join(f"{k.lower()} {v}" for k, v in cells))
    write("stats", build_stats(cells))


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


def parse_days(html: str):
    """-> list of (date, count), oldest first."""
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
            f"parsed only {len(days)} days; GitHub's markup probably changed. "
            "Refusing to write a broken strip."
        )
    days.sort(key=lambda d: d[0])
    return days


def activity_strip(user: str):
    days = parse_days(get(
        CONTRIB_URL.format(user=user),
        {"Accept": "text/html", "X-Requested-With": "XMLHttpRequest"},
    ))

    longest = run = 0
    for _, count in days:
        run = run + 1 if count else 0
        longest = max(longest, run)

    # Today counts only once it has something on it, so a streak is not
    # reported broken at breakfast.
    current = 0
    today = days[-1][0]
    for day, count in reversed(days):
        if count:
            current += 1
        elif day == today:
            continue
        else:
            break

    cells = [
        ("CONTRIBUTIONS", f"{sum(c for _, c in days):,}"),
        ("ACTIVE DAYS", f"{sum(1 for _, c in days if c)} / {len(days)}"),
        ("CURRENT STREAK", f"{current} days"),
        ("LONGEST STREAK", f"{longest} days"),
    ]
    print("activity: " + ", ".join(f"{k.lower()} {v}" for k, v in cells))
    # A smaller value size: "229 / 365" is the widest reading either strip holds.
    write("activity", build_strip(cells, value_size=18))


# --------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", default="danYb16")
    args = parser.parse_args()

    failures = []
    for name, run in (
        ("hero", hero_panel),
        ("stats", stats_strip),
        ("activity", lambda: activity_strip(args.user)),
    ):
        try:
            run()
        except Exception as error:  # one dead source must not block the others
            print(f"{name}: FAILED, keeping the committed panel ({error})")
            failures.append(name)

    if failures:
        raise SystemExit(f"failed: {', '.join(failures)}")


if __name__ == "__main__":
    main()
