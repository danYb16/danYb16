"""
Renders README.md through GitHub's own markdown API and wraps it in GitHub's
page styling, so the preview shows what the profile will actually look like
rather than what a local markdown library thinks it should.

Writes one page per theme. The sheet is fluid, so opening a page in a narrow
window (or a phone emulator) exercises the <picture> swap the same way GitHub
does. Check both themes at both widths: the figure has no background and must
hold on either canvas.

The API runs in "gfm" mode. Its "markdown" mode is not the pipeline READMEs go
through: it wraps the <img> inside a <picture> in a link, which stops the
browser picking a <source> and makes a linked <picture> look broken.

Image URLs are rewritten to the local assets/ copies, since the raw.github URLs
only resolve once a change is pushed.

Run:  python tools/preview_readme.py
Then: open tools/_readme-light.html and tools/_readme-dark.html
"""

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = "https://raw.githubusercontent.com/danYb16/danYb16/main/"

PAGE = """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>README preview, {theme}</title>
<style>
  body {{ margin: 0; padding: 16px; background: {bg}; }}
  .sheet {{ max-width: 846px; margin: 0 auto; box-sizing: border-box;
            border: 1px solid {line}; border-radius: 6px; padding: 24px;
            font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI",
            Helvetica, Arial, sans-serif; color: {ink}; }}
  @media (max-width: 540px) {{ body {{ padding: 0; }}
            .sheet {{ border: 0; padding: 16px; }} }}
  .sheet h1, .sheet h2 {{ font-weight: 600; padding-bottom: .3em;
            border-bottom: 1px solid {line}; margin: 24px 0 16px; }}
  .sheet h1 {{ font-size: 2em; margin-top: 0; }}
  .sheet h2 {{ font-size: 1.5em; }}
  .sheet h3 {{ font-size: 1.25em; font-weight: 600; margin: 24px 0 16px; }}
  .sheet p, .sheet ul {{ margin: 0 0 16px; }}
  .sheet ul {{ padding-left: 2em; }}
  .sheet li + li {{ margin-top: .25em; }}
  .sheet a {{ color: {link}; text-decoration: none; }}
  .sheet img {{ max-width: 100%; }}
  .sheet sub {{ font-size: 12px; color: {muted}; }}
  .anchor {{ display: none; }}
</style>
<div class="sheet">{html}</div>
"""

THEMES = {
    "light": dict(bg="#ffffff", line="#d1d9e0", ink="#1f2328", link="#0969da",
                  muted="#59636e"),
    "dark": dict(bg="#0d1117", line="#3d444d", ink="#f0f6fc", link="#4493f8",
                 muted="#9198a1"),
}


def render(markdown: str) -> str:
    request = urllib.request.Request(
        "https://api.github.com/markdown",
        data=json.dumps({"text": markdown, "mode": "gfm"}).encode(),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "User-Agent": "profile-preview",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode()


def main():
    markdown = (ROOT / "README.md").read_text(encoding="utf-8").replace(RAW, "../")
    html = render(markdown)
    for theme, colours in THEMES.items():
        out = ROOT / "tools" / f"_readme-{theme}.html"
        out.write_text(PAGE.format(theme=theme, html=html, **colours),
                       encoding="utf-8")
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
