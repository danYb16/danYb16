"""
Builds the profile README artwork.

The rules this file lives by, learned the hard way:

1. 700px native width. The profile README column is about 700px, so panels
   drawn wider render scaled down and the type arrives too small.

2. Dark only. GitHub's sanitiser pulls the <img> out of a <picture> wrapped in
   an <a>, so a panel can be theme-aware OR clickable, never both. Clickable
   wins, and dark is the shipped design system anyway.

3. Every image in the README must be wrapped in a real <a>. GitHub auto-links
   a bare image to its own file, which lands the reader on an empty page
   showing the SVG.

4. Panels carry the content; markdown carries only what must be selectable
   (the email address) or searchable (headings). People do not read long text.

5. Nothing on the page describes how the products work inside. Facts stay at
   the level of the public marketing sites.

No <style>, no scripts, no external fetches: camo renders these as plain
<img>, so only presentation attributes plus SMIL survive everywhere. The one
animation is a slow opacity pulse on the hero's STATUS dot, matching the
"disciplined, decelerated" motion rule of the design system. No webfonts; the
stacks mirror GitHub's own. Text width is estimated, never measured, so `wrap`
runs pessimistic and boxes keep slack.

Brand icons are vendored Simple Icons paths (CC0) in tools/icons.py; they must
be inlined because camo blocks external references inside SVGs. Icons render
monochrome; Discord may use blurple, the design system's one sanctioned
recognition colour. Status greens/reds appear only as status, never decoration.

Palette is the shipped design system (AITB-Site src/styles/globals.css).

Run:  python tools/build_assets.py     (static panels only)
      python tools/build_live.py      (hero status, counters, activity)
"""

from pathlib import Path

from icons import ICONS

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

P = {
    "panel": "#15171b",
    "panel2": "#1b1e23",
    "line": "#23262c",
    "line_strong": "#2d3036",
    "brand": "#f39021",
    "brand_dim": "#6b4818",
    "ink0": "#f5f6f7",
    "ink1": "#c9ced4",
    "ink2": "#8b9098",
    "ink3": "#83878f",
    "ok": "#3dd68c",
    "err": "#ef5454",
    "blurple": "#5865f2",
}

W = 700

# --------------------------------------------------------------------------
# primitives
# --------------------------------------------------------------------------


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text_el(x, y, content, *, size, fill, family=SANS, weight=400,
            anchor="start", spacing=None):
    attrs = [f'x="{x}"', f'y="{y}"', f'font-family="{family}"',
             f'font-size="{size}"', f'fill="{fill}"']
    if weight != 400:
        attrs.append(f'font-weight="{weight}"')
    if anchor != "start":
        attrs.append(f'text-anchor="{anchor}"')
    if spacing is not None:
        attrs.append(f'letter-spacing="{spacing}"')
    return f"<text {' '.join(attrs)}>{esc(content)}</text>"


def rect(x, y, w, h, *, rx, fill, stroke=None, opacity=None):
    # Half-pixel inset keeps a 1px stroke on the pixel grid instead of blurring
    # across two.
    if stroke:
        x, y, w, h = x + 0.5, y + 0.5, w - 1, h - 1
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"'
    if stroke:
        out += f' stroke="{stroke}" stroke-width="1"'
    if opacity is not None:
        out += f' opacity="{opacity}"'
    return out + "/>"


def line(x1, y1, x2, y2, stroke):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{stroke}" stroke-width="1"/>')


def icon(x, y, key, size, fill):
    """A Simple Icons path (24x24 viewBox) placed at x,y and scaled to size."""
    d = ICONS[key][1]
    s = size / 24
    return (f'<path transform="translate({x},{y}) scale({s:.4f})" d="{d}" '
            f'fill="{fill}"/>')


def mono_w(text: str, size: float) -> float:
    """Monospace advance. 0.6em is the ratio every stack above holds to."""
    return len(text) * size * 0.6


def wrap(text: str, size: float, max_width: float):
    """Greedy wrap on a pessimistic 0.55em average advance, so a line that fits
    here fits in every font the stack can fall back to."""
    limit = max(1, int(max_width / (size * 0.55)))
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if len(candidate) <= limit:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def card(x, y, w, h, *, rail=False, uid=""):
    """A panel: hairline border, faint inner top highlight, optional amber
    leading-edge rail clipped to the radius."""
    out = rect(x, y, w, h, rx=12, fill=P["panel"], stroke=P["line"])
    out += rect(x + 12, y + 1, w - 24, 1, rx=0.5, fill="#ffffff", opacity="0.05")
    if rail:
        out = (
            f'<clipPath id="c{uid}"><rect x="{x}" y="{y}" width="{w}" '
            f'height="{h}" rx="12"/></clipPath>' + out
            + f'<g clip-path="url(#c{uid})"><rect x="{x}" y="{y}" width="3" '
              f'height="{h}" fill="{P["brand"]}"/></g>'
        )
    return out


def chip(x, y, label, *, key=None, mark=None, accent=False, size=9, h=20):
    """Rounded tag, optionally with a brand icon or a small amber mark. Width
    follows the content so a longer label cannot overflow."""
    pad, gap, isz = 8, 5, 11
    lead = (isz + gap) if (key or mark) else 0
    w = pad + lead + mono_w(label, size) + pad
    fill = "#221709" if accent else P["panel2"]
    stroke = P["brand_dim"] if accent else P["line"]
    ink = P["brand"] if accent else P["ink2"]
    parts = [rect(x, y, w, h, rx=4, fill=fill, stroke=stroke)]
    if key:
        icon_fill = P["blurple"] if key == "discord" else P["ink2"]
        parts.append(icon(x + pad, y + (h - isz) / 2, key, isz, icon_fill))
    elif mark:
        parts.append(rect(x + pad + 1.5, y + (h - 8) / 2, 8, 8, rx=2, fill=P["brand"]))
    parts.append(
        text_el(x + pad + lead, y + h / 2 + 3.1, label, size=size, fill=ink,
                family=MONO)
    )
    return "".join(parts), w


def chip_row(x, y, chips):
    """chips: list of (label, kwargs)."""
    out, cx = [], x
    for label, kwargs in chips:
        markup, w = chip(cx, y, label, **kwargs)
        out.append(markup)
        cx += w + 6
    return "".join(out)


def svg(width, height, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" role="img">'
        f"{body}</svg>\n"
    )


# --------------------------------------------------------------------------
# hero, with the live status board
# --------------------------------------------------------------------------

H_HERO = 176
DOMAINS = ["aiticketbot.com", "nexbrain.dev", "micoapp.io"]


def build_hero(status=None):
    """status: {domain: True|False|None}. None renders a neutral dash, so the
    committed hero is honest even before the first live check has run."""
    status = status or {}
    b = [card(0, 0, W, H_HERO, rail=True, uid="h")]

    b.append(text_el(42, 40, "SOLO DEVELOPER  ·  ROMANIA", size=9.5,
                     fill=P["ink3"], family=MONO, spacing=1.6))
    b.append(text_el(40, 78, "Dani", size=38, fill=P["ink0"], weight=700,
                     spacing=-1))
    b.append(text_el(40, 112, "I build AI support systems for Discord,",
                     size=15, fill=P["ink1"]))
    b.append(text_el(40, 133, "and built my own AI platform along the way.",
                     size=15, fill=P["ink1"]))

    # instrument ruler along the bottom
    ticks = []
    for i, x in enumerate(range(40, 661, 8)):
        tall = 5 if i % 5 == 0 else 3
        ticks.append(line(x, H_HERO - 12, x, H_HERO - 12 + tall, P["line_strong"]))
    b.append(f'<g opacity="0.55">{"".join(ticks)}</g>')

    # status board
    b.append(line(436, 30, 436, 140, P["line_strong"]))
    b.append(
        f'<circle cx="458" cy="37" r="3.5" fill="{P["brand"]}">'
        f'<animate attributeName="opacity" values="1;0.25;1" dur="3s" '
        f'repeatCount="indefinite"/></circle>'
    )
    b.append(text_el(468, 41, "STATUS", size=9, fill=P["ink3"], family=MONO,
                     spacing=1.6))
    y = 72
    for domain in DOMAINS:
        up = status.get(domain)
        dot = P["ok"] if up else P["err"] if up is False else P["ink3"]
        label = "UP" if up else "DOWN" if up is False else "--"
        b.append(f'<circle cx="458" cy="{y - 3.5}" r="3.5" fill="{dot}"/>')
        b.append(text_el(470, y, domain, size=10.5, fill=P["ink1"], family=MONO))
        b.append(text_el(664, y, label, size=9, fill=dot, family=MONO,
                         weight=700, anchor="end"))
        y += 27

    return svg(W, H_HERO, "".join(b))


# --------------------------------------------------------------------------
# counter strip: one panel, four readouts, hairline dividers
# --------------------------------------------------------------------------


def build_strip(cells, *, value_size=20):
    h = 84
    b = [card(0, 0, W, h)]
    cw = W / 4
    for i, (label, value) in enumerate(cells):
        x = i * cw
        if i:
            b.append(line(x, 18, x, h - 18, P["line"]))
        cx = x + cw / 2
        b.append(text_el(cx, 32, label, size=8.5, fill=P["ink3"], family=MONO,
                         anchor="middle", spacing=1.2))
        b.append(text_el(cx, 62, value, size=value_size, fill=P["brand"],
                         family=MONO, weight=700, anchor="middle"))
    return svg(W, h, "".join(b))


STATS_FALLBACK = [("SERVERS", "0"), ("TICKETS HANDLED", "0"),
                  ("RESOLVED BY AI", "0%"), ("AVG FIRST REPLY", "0s")]


def build_stats(cells=None):
    return build_strip(cells or STATS_FALLBACK)


# --------------------------------------------------------------------------
# product cards
# --------------------------------------------------------------------------


def product_card(w, h, title, kicker, body, chips, uid, *, tag=None):
    b = [card(0, 0, w, h, rail=True, uid=uid)]
    b.append(text_el(20, 34, title, size=15.5, fill=P["brand"], weight=700))
    if tag:
        tx = 20 + len(title) * 15.5 * 0.56 + 12
        markup, _ = chip(tx, 19, tag, accent=True, size=8, h=18)
        b.append(markup)
    b.append(text_el(20, 52, kicker, size=9.5, fill=P["ink3"], family=MONO))
    y = 74
    for row in wrap(body, 12, w - 40):
        b.append(text_el(20, y, row, size=12, fill=P["ink1"]))
        y += 15.5
    b.append(chip_row(20, h - 30, chips))
    return svg(w, h, "".join(b))


def build_card_aitb():
    return product_card(
        344, 144, "AI Ticket Bot", "aiticketbot.com",
        "AI support for Discord servers and sites. Members get answers, "
        "staff get the hard ones.",
        [("Discord", {"key": "discord"}),
         ("Web widget", {}),
         ("Nexus AI", {"mark": "amber"})],
        "a",
    )


def build_card_mico():
    return product_card(
        344, 144, "Mico", "micoapp.io",
        "AI screening for Discord applications. Scores every answer, flags "
        "the AI-written ones.",
        [("Discord", {"key": "discord"}),
         ("Next.js", {"key": "nextdotjs"}),
         ("OpenAI", {"key": "openai"})],
        "m",
    )


def build_card_nexus():
    return product_card(
        W, 118, "Nexus", "nexbrain.dev",
        "The AI platform behind AI Ticket Bot. Per-customer memory, training "
        "and usage metering.",
        [("Python", {"key": "python"}),
         ("FastAPI", {"key": "fastapi"}),
         ("Postgres", {"key": "postgresql"}),
         ("Claude", {"key": "claude"})],
        "n",
        tag="MY PLATFORM",
    )


def build_card_debox():
    """Slim client-work bar."""
    h = 54
    b = [card(0, 0, W, h)]
    b.append(text_el(20, 22, "CLIENT WORK", size=8.5, fill=P["ink3"],
                     family=MONO, spacing=1.4))
    b.append(text_el(20, 40, "Debox Performance", size=13, fill=P["ink0"],
                     weight=700))
    b.append(text_el(230, 33, "deboxperformance.ro", size=10, fill=P["ink3"],
                     family=MONO))
    chips = [("PHP", {"key": "php"}), ("MariaDB", {"key": "mariadb"})]
    widths = [8 + 11 + 5 + mono_w(label, 9) + 8 for label, _ in chips]
    x = W - 20 - sum(widths) - 6 * (len(chips) - 1)
    b.append(chip_row(x, (h - 20) / 2, chips))
    return svg(W, h, "".join(b))


# --------------------------------------------------------------------------
# in production: four short proofs, no methodology
# --------------------------------------------------------------------------

PROOFS = [
    ("Claude Code, daily",
     "Over a year on production code, not demos."),
    ("Two AI stacks",
     "Claude and OpenAI, both serving paying users."),
    ("37 languages",
     "Every user-facing surface localized."),
    ("Full-stack solo",
     "Bots, APIs, dashboards, billing and ops."),
]


def build_proof():
    cw, ch, gap = (W - 12) / 2, 70, 12
    b = []
    for i, (title, body) in enumerate(PROOFS):
        x = (i % 2) * (cw + gap)
        y = (i // 2) * (ch + gap)
        b.append(card(x, y, cw, ch))
        b.append(f'<circle cx="{x + 20}" cy="{y + 24}" r="3" fill="{P["brand"]}"/>')
        b.append(text_el(x + 32, y + 28, title, size=12.5, fill=P["ink0"],
                         weight=700))
        b.append(text_el(x + 20, y + 50, body, size=11, fill=P["ink2"]))
    return svg(W, 2 * ch + gap, "".join(b))


# --------------------------------------------------------------------------
# stack grid
# --------------------------------------------------------------------------

STACK = [
    "python", "typescript", "php", "fastapi", "nextdotjs", "tailwindcss",
    "mariadb", "postgresql", "stripe", "openai", "claude", "discord",
]


def build_stack():
    h = 148
    b = [card(0, 0, W, h)]
    cols, isz = 6, 22
    cw = (W - 40) / cols
    for i, key in enumerate(STACK):
        cx = 20 + (i % cols) * cw + cw / 2
        top = 24 if i < cols else 88
        fill = P["blurple"] if key == "discord" else P["ink1"]
        b.append(icon(cx - isz / 2, top, key, isz, fill))
        b.append(text_el(cx, top + isz + 16, ICONS[key][0], size=9,
                         fill=P["ink3"], family=MONO, anchor="middle"))
    return svg(W, h, "".join(b))


# --------------------------------------------------------------------------

# Static panels only. The live ones (hero status, stats, activity) are written
# by tools/build_live.py so a network failure can never blank them.
BUILDERS = {
    "card-aitb": build_card_aitb,
    "card-mico": build_card_mico,
    "card-nexus": build_card_nexus,
    "card-debox": build_card_debox,
    "proof": build_proof,
    "stack": build_stack,
}


def main():
    out = Path(__file__).resolve().parent.parent / "assets"
    out.mkdir(parents=True, exist_ok=True)
    for name, builder in BUILDERS.items():
        path = out / f"{name}.svg"
        path.write_text(builder(), encoding="utf-8")
        print(f"wrote {path.relative_to(out.parent)}")


if __name__ == "__main__":
    main()
