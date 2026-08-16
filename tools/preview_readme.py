"""
Renders README.md through GitHub's own markdown API and wraps it in GitHub's
page styling at the real profile column width (~700px), so the preview shows
what the profile will actually look like rather than what a local markdown
library thinks it should.

Shown on both canvases, because the panels are dark only: the point of the light
pass is to confirm dark cards read as deliberate on a white page rather than
broken.

Image URLs are rewritten to the local assets/ copies, since the raw.github URLs
only resolve once a change is pushed.

Run:  python tools/preview_readme.py
Then: open tools/_readme.html
"""

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = "https://raw.githubusercontent.com/danYb16/danYb16/main/"

PAGE = """<!doctype html>
<meta charset="utf-8">
<title>README preview</title>
<style>
  body {{ margin: 0; }}
  .band {{ padding: 28px 0 48px; }}
  .wrap {{ width: 766px; margin: 0 auto; }}
  .sheet {{ border: 1px solid #d1d9e0; border-radius: 6px; padding: 32px;
            font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI",
            Helvetica, Arial, sans-serif; color: #1f2328; }}
  .sheet h2 {{ font-size: 24px; font-weight: 600; padding-bottom: .3em;
               border-bottom: 1px solid #d1d9e0; margin: 24px 0 16px; }}
  .sheet p {{ margin: 0 0 16px; }}
  .sheet a {{ color: #0969da; text-decoration: none; }}
  .sheet img {{ max-width: 100%; vertical-align: top; }}
  .sheet sub {{ font-size: 12px; color: #59636e; }}
  .dark {{ background: #0d1117; }}
  .dark .sheet {{ background: #0d1117; border-color: #3d444d; color: #f0f6fc; }}
  .dark .sheet h2 {{ border-color: #3d444d; }}
  .dark .sheet a {{ color: #4493f8; }}
  .dark .sheet sub {{ color: #9198a1; }}
  .tag {{ font: 600 11px ui-monospace, Consolas, monospace; letter-spacing: 1.5px;
          color: #59636e; padding-bottom: 10px; }}
  .dark .tag {{ color: #9198a1; }}
</style>
<div class="band {cls}"><div class="wrap">
  <div class="tag">{tag}</div>
  <div class="sheet">{html}</div>
</div></div>
"""


def render(markdown: str) -> str:
    request = urllib.request.Request(
        "https://api.github.com/markdown",
        data=json.dumps({"text": markdown, "mode": "markdown"}).encode(),
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

    out = ROOT / "tools" / "_readme.html"
    out.write_text(
        PAGE.format(cls="light", tag="GITHUB LIGHT", html=html)
        + PAGE.format(cls="dark", tag="GITHUB DARK", html=html),
        encoding="utf-8",
    )
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
