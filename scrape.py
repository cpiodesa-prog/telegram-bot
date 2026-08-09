# -*- coding: utf-8 -*-
"""Scrape Odesa City Council executive-committee listings (2026):
   - draft decisions  (проєкти рішень виконкому)  /ua/acts/projects/committee/
   - decisions        (рішення виконкому)         /ua/acts/committee/
Saves raw HTML pages to cache/ and a parsed JSON per listing."""
import os, re, sys, json, time, html
sys.stdout.reconfigure(encoding="utf-8")
import fetch

BASE = "https://omr.gov.ua"
CACHE = "cache"
os.makedirs(CACHE, exist_ok=True)

LISTINGS = {
    "projects": "/ua/acts/projects/committee/",   # draft decisions (виконком)
    "decisions": "/ua/acts/committee/",            # adopted decisions (виконком)
    "mayor": "/ua/acts/mayor/",                    # розпорядження міського голови (в т.ч. скликання сесій)
    "council": "/ua/acts/council/",                # рішення міської ради
    "omva": "/ua/acts/omva/",                      # розпорядження ОМВА
}

ROW_RE = re.compile(
    r'<td class="col-1">\s*(?P<num>[^<]*?)\s*</td>\s*'
    r'<td class="col-2">\s*(?:<time[^>]*>)?\s*(?P<date>[\d.]+)\s*(?:</time>)?\s*</td>\s*'
    r'<td class="col-3">\s*<a href="(?P<link>[^"]+)"[^>]*>\s*(?:<p>)?(?P<desc>.*?)(?:</p>)?\s*</a>',
    re.S)

LASTPAGE_RE = re.compile(r'\?page=(\d+)')

def clean(s):
    s = re.sub(r'<[^>]+>', '', s)
    s = html.unescape(s)
    s = s.replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', s).strip()

def fetch_page(slug, path, page):
    fn = os.path.join(CACHE, f"{slug}_p{page}.html")
    if os.path.exists(fn):
        return open(fn, encoding="utf-8").read()
    url = BASE + path + (f"?page={page}" if page > 1 else "")
    print(f"  fetching {url}")
    h = fetch.get(url)
    open(fn, "w", encoding="utf-8").write(h)
    time.sleep(1)
    return h

def last_page(htmltext):
    nums = [int(x) for x in LASTPAGE_RE.findall(htmltext)]
    return max(nums) if nums else 1

def parse_rows(htmltext):
    out = []
    for m in ROW_RE.finditer(htmltext):
        link = m.group("link")
        if link.startswith("/"):
            link = BASE + link
        out.append({
            "number": clean(m.group("num")),
            "date": m.group("date").strip(),
            "description": clean(m.group("desc")),
            "url": link,
        })
    return out

def scrape(slug, path):
    print(f"[{slug}] {path}")
    first = fetch_page(slug, path, 1)
    lp = last_page(first)
    print(f"  last page = {lp}")
    rows = parse_rows(first)
    for p in range(2, lp + 1):
        h = fetch_page(slug, path, p)
        rows += parse_rows(h)
    print(f"  parsed rows: {len(rows)}")
    json.dump(rows, open(f"{slug}.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    return rows

if __name__ == "__main__":
    for slug, path in LISTINGS.items():
        scrape(slug, path)
