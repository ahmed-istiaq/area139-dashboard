#!/usr/bin/env python3
"""Area 139 link checker.

Checks every download/destination link on the site:
  * static cards  -> parsed from the live page (SITE_URL) or a local index.html
  * dynamic posts -> read from Supabase (posts + static_post_overrides)

Statuses:  OK | BROKEN | WARN (blocked / quota / timeout) | SKIP (can't be verified)
Exit code 1 if any BROKEN link is found (so GitHub Actions emails you).

Usage:
    python link_checker.py                       # live site + Supabase
    python link_checker.py --html index.html     # local file instead of live page
    python link_checker.py --no-db               # static links only
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag, urlparse

import requests

from common import DEFAULT_SITE_URL, UA, fetch_table, telegram_notify

TIMEOUT = 20
DEFAULT_OUT = Path(__file__).resolve().parent / "reports"
SKIP_HOSTS = {"schema.org", "fonts.googleapis.com", "fonts.gstatic.com"}
HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


# --------------------------------------------------------------------------
# 1. Collect links (and remember WHERE on the site each one lives)
# --------------------------------------------------------------------------
SECTION_KINDS = ("section", "nav", "header", "footer")
KIND_LABEL = {"nav": "Navigation menu", "header": "Page header", "footer": "Footer"}

# How the site (index.html) maps a post's category_slug to a section on the page.
STATIC_SECTION = {
    "books": ("section-mbbs-books", "MBBS Textbooks & Clinical Atlases"),
    "anatomy": ("section-anatomy", "Anatomy"),
    "physiology": ("section-physiology", "Physiology"),
    "biochemistry": ("section-biochemistry", "Biochemistry"),
    "histology": ("section-histo", "Histology & Radiology"),
    "others": ("section-QB", "Question Bank"),
}


ID_NAMES = {"about-site": "About this site"}


def clean(text) -> str:
    return " ".join((text or "").split())


class PageParser(HTMLParser):
    """Finds every <a href> together with its section, card (<article>) and button text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self._stack = []   # open section/nav/header/footer/article elements
        self._heading = False
        self._spans = []   # True for icon-font spans (their text is an icon name, not content)
        self._icon = 0
        self._a = None

    def _last(self, kinds):
        for kind, info in reversed(self._stack):
            if kind in kinds:
                return info
        return None

    def _heading_target(self):
        art = self._last(("article",))
        return art if art is not None else self._last(SECTION_KINDS)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in SECTION_KINDS:
            self._stack.append((tag, {"id": a.get("id"), "title": KIND_LABEL.get(tag, ""), "done": tag != "section"}))
        elif tag == "article":
            self._stack.append(("article", {"id": None, "title": "", "done": False}))
        elif tag in HEADINGS:
            self._heading = True
        elif tag == "span":
            is_icon = any(k in (a.get("class") or "") for k in ("material-symbols", "material-icons"))
            self._spans.append(is_icon)
            self._icon += int(is_icon)
        elif tag == "a" and a.get("href"):
            self._a = {"href": a["href"], "text": "", "aria": a.get("aria-label") or a.get("title") or "",
                       "sec": self._last(SECTION_KINDS), "art": self._last(("article",))}

    def handle_data(self, data):
        if self._icon:
            return
        if self._heading:
            target = self._heading_target()
            if target is not None and not target["done"]:
                target["title"] += data
        if self._a is not None:
            self._a["text"] += data

    def handle_endtag(self, tag):
        if tag in HEADINGS:
            if self._heading:
                target = self._heading_target()
                if target is not None and clean(target["title"]):
                    target["done"] = True
            self._heading = False
        elif tag == "span":
            if self._spans and self._spans.pop():
                self._icon -= 1
        elif tag == "a" and self._a is not None:
            self.links.append(self._a)
            self._a = None
        elif tag in SECTION_KINDS or tag == "article":
            for i in range(len(self._stack) - 1, -1, -1):
                if self._stack[i][0] == tag:
                    del self._stack[i:]
                    break


def normalize(href: str):
    href = (href or "").strip()
    if not href.lower().startswith(("http://", "https://")):
        return None
    url, _ = urldefrag(href)
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return None if host in SKIP_HOSTS else url


def make_loc(area, section_id, card, label, origin, site_url, field=None) -> dict:
    """One place on the website where a link appears."""
    base = (site_url or "").split("#")[0]
    return {
        "area": area,
        "section_id": section_id,
        "card": card,
        "label": label,
        "origin": origin,          # "Page" | "Database" | "Database override"
        "field": field,
        "path": " › ".join(p for p in (area, card, label) if p),
        "site_link": f"{base}#{section_id}" if (section_id and base) else base,
    }


def collect_static(html: str, site_url: str = "") -> dict:
    parser = PageParser()
    parser.feed(html)
    parser.close()
    items: dict = {}
    for l in parser.links:
        url = normalize(l["href"])
        if not url:
            continue
        sec, art = l["sec"], l["art"]
        area = (ID_NAMES.get(sec["id"]) or clean(sec["title"]) or sec["id"] or "Page section") if sec else "Top of page"
        card = clean(art["title"]) if art and clean(art["title"]) else None
        label = clean(l["text"]) or clean(l["aria"]) or "Link"
        items.setdefault(url, []).append(
            make_loc(area, sec["id"] if sec else None, card, label, "Page", site_url))
    return items


def _button_label(url: str) -> str:
    """The site labels a card button 'Open in Telegram' for t.me links, else 'Download Here'."""
    return "Open in Telegram" if urlparse(url).netloc.lower().removeprefix("www.") == "t.me" else "Download Here"


def collect_db(site_url: str = "") -> dict:
    items: dict = {}
    names: dict = {}
    try:
        names = {c.get("slug"): c.get("name") for c in fetch_table("post_categories")}
    except Exception:
        pass  # category names are only a nicety

    def location_for(slug):
        slug = (slug or "").strip().lower()
        if slug in STATIC_SECTION:
            return STATIC_SECTION[slug][1], STATIC_SECTION[slug][0]
        return (names.get(slug) or slug or "Uncategorised"), (f"section-{slug}" if slug else None)

    def add(rows, origin):
        for r in rows:
            if r.get("is_draft") or r.get("is_deleted"):
                continue
            title = r.get("title") or r.get("card_key") or "(untitled)"
            area, section_id = location_for(r.get("category_slug"))
            seen = set()
            for field in ("download_link", "destination_link"):
                url = normalize(r.get(field) or "")
                if not url or url in seen:
                    continue
                seen.add(url)
                label = _button_label(url) if field == "download_link" else "Destination link"
                items.setdefault(url, []).append(
                    make_loc(area, section_id, str(title), label, origin, site_url, field))

    add(fetch_table("posts"), "Database")
    try:
        add(fetch_table("static_post_overrides"), "Database override")
    except Exception:
        pass  # table may be hidden by RLS - not fatal
    return items


def merge(into: dict, other: dict):
    for url, locs in other.items():
        bucket = into.setdefault(url, [])
        keys = {(l["path"], l["origin"]) for l in bucket}
        for l in locs:
            if (l["path"], l["origin"]) not in keys:
                bucket.append(l)
                keys.add((l["path"], l["origin"]))


def load_html(html_path, site_url) -> str:
    if html_path:
        return Path(html_path).read_text(encoding="utf-8", errors="ignore")
    r = requests.get(site_url, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    return r.text


# --------------------------------------------------------------------------
# 2. Check links
# --------------------------------------------------------------------------
def _get(url, **kw):
    return requests.get(
        url, headers={"User-Agent": UA, "Accept-Language": "en"}, timeout=TIMEOUT, **kw
    )


def read_text(r, limit=200_000) -> str:
    buf = b""
    for chunk in r.iter_content(8192):
        buf += chunk
        if len(buf) >= limit:
            break
    r.close()
    return buf.decode(r.encoding or "utf-8", errors="ignore").lower()


def status_from_code(code: int):
    if code in (404, 410):
        return "BROKEN", f"HTTP {code} not found"
    if code in (401, 403, 429, 999):
        return "WARN", f"blocked / needs login (HTTP {code})"
    if code >= 500:
        return "WARN", f"server error (HTTP {code})"
    if code >= 400:
        return "BROKEN", f"HTTP {code}"
    return "OK", f"HTTP {code}"


def check_telegram(url):
    parts = [p for p in urlparse(url).path.split("/") if p]
    if not parts:
        return "OK", "t.me home"
    first = parts[0]
    if first in ("c", "joinchat") or first.startswith("+"):
        return "SKIP", "private / invite link - can't be verified automatically"
    if first == "s" and len(parts) > 1:  # t.me/s/<channel> web preview
        parts = parts[1:]
    if len(parts) >= 2 and parts[1].isdigit():  # a specific post
        r = _get(
            f"https://t.me/{parts[0]}/{parts[1]}",
            params={"embed": "1", "mode": "tme"},
            stream=True,
        )
        if r.status_code >= 400:
            r.close()
            return status_from_code(r.status_code)
        if "tgme_widget_message_error" in read_text(r):
            return "BROKEN", "post not found / deleted"
        return "OK", "post reachable"
    r = _get(f"https://t.me/{parts[0]}", stream=True)
    r.close()
    if r.status_code == 200:
        return "OK", "page reachable (channel existence can't be fully verified)"
    return status_from_code(r.status_code)


def check_drive(url):
    r = _get(url, stream=True, allow_redirects=True)
    code = r.status_code
    if code >= 400:
        r.close()
        if code in (401, 403):
            return "WARN", f"not public / access denied / quota (HTTP {code})"
        return status_from_code(code)
    if "text/html" not in r.headers.get("Content-Type", "").lower():
        r.close()
        return "OK", "file reachable"
    text = read_text(r)
    if "the file you have requested does not exist" in text:
        return "BROKEN", "file / folder deleted or not found"
    is_folder = "/folders/" in url
    if "too many users have viewed or downloaded" in text or "view or download this file at this time" in text:
        return "WARN", "download quota exceeded (temporary)"
    if not is_folder and ("you need access" in text or "request access" in text):
        return "WARN", "not shared publicly (needs access)"
    return "OK", "reachable"


def check_generic(url):
    r = requests.head(
        url, headers={"User-Agent": UA}, timeout=TIMEOUT, allow_redirects=True
    )
    if r.status_code >= 400:  # many servers reject HEAD
        r = _get(url, stream=True, allow_redirects=True)
        r.close()
    return status_from_code(r.status_code)


def check_url(url):
    host = urlparse(url).netloc.lower().removeprefix("www.")
    if host == "t.me":
        fn = check_telegram
    elif host in ("drive.google.com", "docs.google.com"):
        fn = check_drive
    else:
        fn = check_generic
    last = ("WARN", "unknown error")
    for _ in range(2):
        try:
            return fn(url)
        except requests.exceptions.Timeout:
            last = ("WARN", "timeout")
        except requests.exceptions.RequestException as e:
            last = ("WARN", f"request failed: {type(e).__name__}")
        time.sleep(1.5)
    return last


# --------------------------------------------------------------------------
# 3. Run + report
# --------------------------------------------------------------------------
def run_check(site_url=None, html_path=None, use_db=True, workers=6, out_dir=DEFAULT_OUT):
    site_url = site_url or os.getenv("SITE_URL", DEFAULT_SITE_URL)
    items: dict = {}
    notes = []

    try:
        merge(items, collect_static(load_html(html_path, site_url), site_url))
    except Exception as e:
        notes.append(f"static page load failed: {e}")
    if use_db:
        try:
            merge(items, collect_db(site_url))
        except Exception as e:
            notes.append(f"Supabase read failed: {e}")

    urls = sorted(items)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        outcomes = list(ex.map(check_url, urls))

    results = [
        {"url": u, "status": s, "detail": d, "locations": items[u],
         "sources": [l["path"] for l in items[u]]}
        for u, (s, d) in zip(urls, outcomes)
    ]
    order = {"BROKEN": 0, "WARN": 1, "SKIP": 2, "OK": 3}
    results.sort(key=lambda x: (order[x["status"]], x["url"]))
    summary = {k: sum(r["status"] == k for r in results) for k in order}
    summary["total"] = len(results)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "summary": summary,
        "notes": notes,
        "results": results,
    }

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "link_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "link_report.md").write_text(to_markdown(report), encoding="utf-8")
    return report


def to_markdown(rep) -> str:
    s = rep["summary"]
    lines = [
        f"# Area 139 link report - {rep['generated_at']}",
        "",
        f"Total {s['total']} | OK {s['OK']} | BROKEN {s['BROKEN']} | WARN {s['WARN']} | SKIP {s['SKIP']}",
        "",
    ]
    for n in rep["notes"]:
        lines.append(f"> note: {n}")
    for status, title in (("BROKEN", "Broken"), ("WARN", "Needs a look"), ("SKIP", "Not verifiable")):
        rows = [r for r in rep["results"] if r["status"] == status]
        if not rows:
            continue
        lines += ["", f"## {title} ({len(rows)})", ""]
        for r in rows:
            lines.append(f"- {r['url']} - {r['detail']}")
            for l in r.get("locations", [])[:5]:
                lines.append(f"  - found on: {l['path']} ({l['origin']}) -> {l['site_link']}")
    return "\n".join(lines) + "\n"


def alert_text(rep) -> str:
    broken = [r for r in rep["results"] if r["status"] == "BROKEN"]
    lines = [f"Area 139: {len(broken)} broken link(s) found"]
    for r in broken[:15]:
        where = r["locations"][0]["path"] if r.get("locations") else "unknown location"
        lines.append(f"- {r['url']} ({r['detail']})\n   Where: {where}")
    if len(broken) > 15:
        lines.append(f"...and {len(broken) - 15} more")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", help="live site URL (default: SITE_URL env / github.io)")
    ap.add_argument("--html", help="local index.html instead of fetching the live page")
    ap.add_argument("--no-db", action="store_true", help="skip Supabase links")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    a = ap.parse_args()

    rep = run_check(a.url, a.html, not a.no_db, a.workers, a.out)
    print((Path(a.out) / "link_report.md").read_text(encoding="utf-8"))

    if rep["summary"]["BROKEN"]:
        if telegram_notify(alert_text(rep)):
            print("Telegram alert sent.")
        sys.exit(1)


if __name__ == "__main__":
    main()
