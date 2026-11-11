import shutil
import datetime
from pathlib import Path
from xml.sax.saxutils import escape

import markdown
import yaml
from PIL import Image

SITE_TITLE = "Joe Machin"
SITE_URL = "https://joemachin.github.io"
SITE_DESC = "Product designer portfolio"

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
NAV = [("About", "/about/"), ("Work", "/work/"),
       ("Notes", "/notes/"), ("Contact", "/contact/")]


def load(path):
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    if text.startswith("---"):
        _, front, body = text.split("---", 2)
        meta = yaml.safe_load(front) or {}
    html = markdown.markdown(
        body, extensions=["fenced_code", "tables", "smarty"])
    return meta, html


def collect(folder):
    items = []
    for p in sorted((ROOT / folder).glob("*.md")):
        meta, html = load(p)
        if meta.get("draft"):
            continue
        meta["slug"] = p.stem
        meta.setdefault("title", p.stem.replace("-", " ").title())
        meta["date"] = str(meta.get("date", ""))
        meta["html"] = html
        items.append(meta)
    return items


def render(title, content, url, desc=""):
    tpl = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
        cur = "/about/" if url == "/" else url
    links = []
    for n, u in NAV:
        mark = ' aria-current="page"' if cur.startswith(u) else ""
        links.append(f'<a href="{u}"{mark}>{n}</a>')
    nav = "".join(links)
    full_title = SITE_TITLE if url == "/" else f"{title} - {SITE_TITLE}"
    values = {
        "title": full_title,
        "description": escape(desc or SITE_DESC),
        "site_title": SITE_TITLE,
        "nav": nav,
        "content": content,
    }
    for key, val in values.items():
        tpl = tpl.replace("{{" + key + "}}", val)
    out = DIST / url.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(tpl, encoding="utf-8")


def rfc822(date_str):
    try:
        d = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%a, %d %b %Y 00:00:00 +0000")
    except ValueError:
        return ""


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    if (ROOT / "static").exists():
        shutil.copytree(ROOT / "static", DIST / "static")

    img_out = DIST / "images"
    img_out.mkdir()
    img_in = ROOT / "images"
    if img_in.exists():
        for f in img_in.iterdir():
            if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                im = Image.open(f)
                if im.width > 1600:
                    h = int(im.height * 1600 / im.width)
                    im = im.resize((1600, h))
                im.save(img_out / f.name)
            elif f.is_file():
                shutil.copy(f, img_out / f.name)

    urls = ["/"]

    # Pages: About and Contact (About is also the home page)
    for p in collect("pages"):
        body = f'<h1>{p["title"]}</h1>{p["html"]}'
        render(p["title"], body, f'/{p["slug"]}/', p.get("summary", ""))
        urls.append(f'/{p["slug"]}/')
        if p["slug"] == "about":
            render(p["title"], body, "/", p.get("summary", ""))

    # Work
    work = collect("work")
    work.sort(key=lambda w: (w.get("order", 999), w["title"]))
    for w in work:
        role = f'<p class="meta">{w["role"]}</p>' if w.get("role") else ""
        cover = (f'<img src="/images/{w["cover"]}" alt="">'
                 if w.get("cover") else "")
        body = f'<h1>{w["title"]}</h1>{role}{cover}{w["html"]}'
        render(w["title"], body, f'/work/{w["slug"]}/', w.get("summary", ""))
        urls.append(f'/work/{w["slug"]}/')
    cards = "".join(
        f'<li><a href="/work/{w["slug"]}/"><h2>{w["title"]}</h2>'
        f'<p>{w.get("summary", "")}</p></a></li>' for w in work)
    render("Work", f'<h1>Work</h1><ul class="list">{cards}</ul>', "/work/")
    urls.append("/work/")

    # Notes
    notes = collect("notes")
    notes.sort(key=lambda n: n["date"], reverse=True)
    for n in notes:
        body = (f'<h1>{n["title"]}</h1><p class="meta">{n["date"]}</p>'
                f'{n["html"]}')
        render(n["title"], body, f'/notes/{n["slug"]}/', n.get("summary", ""))
        urls.append(f'/notes/{n["slug"]}/')
    rows = "".join(
        f'<li><a href="/notes/{n["slug"]}/"><h2>{n["title"]}</h2>'
        f'<p class="meta">{n["date"]}</p><p>{n.get("summary", "")}</p>'
        f'</a></li>' for n in notes)
    render("Notes", f'<h1>Notes</h1><ul class="list">{rows}</ul>', "/notes/")
    urls.append("/notes/")

    # RSS feed (Notes only)
    items = "".join(
        f'<item><title>{escape(n["title"])}</title>'
        f'<link>{SITE_URL}/notes/{n["slug"]}/</link>'
        f'<guid>{SITE_URL}/notes/{n["slug"]}/</guid>'
        f'<pubDate>{rfc822(n["date"])}</pubDate>'
        f'<description>{escape(n.get("summary", ""))}</description></item>'
        for n in notes)
    rss = ('<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
           f'<title>{escape(SITE_TITLE)}</title><link>{SITE_URL}</link>'
           f'<description>{escape(SITE_DESC)}</description>{items}'
           '</channel></rss>')
    (DIST / "rss.xml").write_text(rss, encoding="utf-8")

    # Sitemap
    locs = "".join(f"<url><loc>{SITE_URL}{u}</loc></url>" for u in urls)
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
               f'{locs}</urlset>')
    (DIST / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    print(f"Built {len(urls)} pages")


if __name__ == "__main__":
    build()
