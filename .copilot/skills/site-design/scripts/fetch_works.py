#!/usr/bin/env python3
"""List recent works from Google Scholar, ORCID, and GitHub and mark which ones index.html already links.

Usage: python3 fetch_works.py [--orcid ID] [--json]
Stdlib only. Scholar user ID is read from the Scholar link in index.html.
Only works from the year of the newest work already linked on the page onward are listed;
older works are left alone because that part of the page is settled.
"""
import argparse, html, json, re, subprocess, sys, time, urllib.error, urllib.parse, urllib.request
from difflib import SequenceMatcher
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
DEFAULT_ORCID = "0000-0002-7971-5222"


def get(url, accept=None):
    hdr = dict(UA, **({"Accept": accept} if accept else {}))
    for wait in (2, 5, 10, None):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or wait is None:
                raise
            time.sleep(wait)


def norm_id(s):
    s = s.lower().strip()
    s = re.sub(r"^https?://(dx\.)?doi\.org/", "", s)
    s = re.sub(r"^https?://arxiv\.org/(abs|pdf)/", "arxiv:", s)
    return re.sub(r"v\d+$", "", s.removesuffix(".pdf"))


def norm_title(t):
    return re.sub(r"[^a-z0-9]+", " ", html.unescape(t).lower()).strip()


def scholar(user, since):
    url = f"https://scholar.google.com/citations?user={user}&hl=en&cstart=0&pagesize=100&sortby=pubdate"
    page = get(url)
    if "gsc_a_tr" not in page:
        sys.exit("Scholar returned no rows (likely a CAPTCHA); open the profile in a browser instead.")
    out = []
    for row in re.findall(r'<tr class="gsc_a_tr">(.*?)</tr>', page, re.S):
        title = re.search(r'class="gsc_a_at">(.*?)</a>', row, re.S)
        gray = re.findall(r'<div class="gs_gray">(.*?)</div>', row, re.S)
        year = re.search(r'gsc_a_h[^>]*>(\d{4})<', row)
        y = int(year.group(1)) if year else 0
        if y and y < since:
            continue
        venue = re.sub(r"<span class=\"gs_oph\">.*?</span>|<.*?>", "", gray[1]) if len(gray) > 1 else ""
        out.append({"source": "scholar", "year": y, "title": html.unescape(title.group(1)),
                    "authors": html.unescape(gray[0]) if gray else "",
                    "venue": html.unescape(venue).strip(), "id": ""})
    return out


def orcid(oid, since):
    data = json.loads(get(f"https://pub.orcid.org/v3.0/{oid}/works", "application/json"))
    out = []
    for g in data["group"]:
        s = g["work-summary"][0]
        y = int((((s.get("publication-date") or {}).get("year")) or {}).get("value") or 0)
        if y and y < since:
            continue
        ids = {i["external-id-type"]: i["external-id-value"] for i in (s.get("external-ids") or {}).get("external-id", [])}
        wid = ("doi:" + ids["doi"]) if "doi" in ids else ("arxiv:" + ids["arxiv"]) if "arxiv" in ids else ""
        out.append({"source": "orcid", "year": y, "title": s["title"]["title"]["value"], "authors": "",
                    "venue": ((s.get("journal-title") or {}).get("value")) or "", "id": wid})
    return out


def resolve(title, authors=""):
    """Best-effort DOI or arXiv ID for a title: Crossref first, then the arXiv API."""
    q = urllib.parse.quote(title)
    first = authors.split(",")[0].split()[-1] if authors.strip() else ""
    au = f"&query.author={urllib.parse.quote(first)}" if first else ""
    for extra in ([au, ""] if au else [""]):
        try:
            items = json.loads(get(f"https://api.crossref.org/works?rows=3&query.bibliographic={q}{extra}"))["message"]["items"]
        except Exception:
            continue
        for it in items:
            if it.get("type") == "component":
                continue
            if SequenceMatcher(None, norm_title((it.get("title") or [""])[0]), norm_title(title)).ratio() > 0.9:
                return "doi:" + it["DOI"].lower()
    try:
        feed = get(f"https://export.arxiv.org/api/query?max_results=3&search_query=ti:%22{q}%22")
        for aid, t in re.findall(r"<id>http://arxiv.org/abs/([^<]+)</id>.*?<title>(.*?)</title>", feed, re.S):
            if SequenceMatcher(None, norm_title(t), norm_title(title)).ratio() > 0.9:
                return "arxiv:" + re.sub(r"v\d+$", "", aid)
    except Exception:
        pass
    return ""


def github(user, since, linked):
    """Public repos the user owns or has public activity in, created from `since` on and not yet linked."""
    api = "https://api.github.com"
    names = {r["full_name"] for r in json.loads(get(f"{api}/users/{user}/repos?per_page=100&type=owner")) if not r["fork"]}
    names |= {e["repo"]["name"] for e in json.loads(get(f"{api}/users/{user}/events/public?per_page=100"))}
    prs = json.loads(get(f"{api}/search/issues?q=type:pr+author:{user}&per_page=100"))["items"]
    names |= {i["repository_url"].split("/repos/")[1] for i in prs}
    out = []
    for n in sorted(names):
        if n.lower() == f"{user}/{user}.github.io".lower():
            continue
        try:
            r = json.loads(get(f"{api}/repos/{n}"))
        except Exception:
            continue
        y = int(r["created_at"][:4])
        if r["private"] or r["fork"] or y < since or r["html_url"].lower().rstrip("/") in linked:
            continue
        out.append({"source": "github", "year": y, "title": r["full_name"], "authors": "",
                    "venue": r.get("description") or "", "id": "", "url": r["html_url"], "on_site": False})
    return out


def year_of(wid):
    """Publication year of a linked work: from the arXiv ID, or from Crossref for a DOI."""
    if wid.startswith("arxiv:"):
        m = re.match(r"arxiv:(\d{2})\d{2}\.", wid)
        return 2000 + int(m.group(1)) if m else 0
    if wid.startswith("doi:"):
        try:
            msg = json.loads(get("https://api.crossref.org/works/" + urllib.parse.quote(wid[4:])))["message"]
            return (msg.get("issued") or {}).get("date-parts", [[0]])[0][0] or 0
        except Exception:
            return 0
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--orcid", default=DEFAULT_ORCID)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    page = (root / "index.html").read_text()
    on_site = {norm_id(h).replace("10.", "doi:10.", 1) if h.lower().startswith(("https://doi.org", "http://doi.org", "https://dx.doi.org")) else norm_id(h)
               for h in re.findall(r'href="([^"]+)"', page)}
    years = {wid: year_of(wid) for wid in on_site if wid.startswith(("arxiv:", "doi:"))}
    newest_id = max(years, key=years.get)
    since = years[newest_id]
    print(f"Newest work on the page: {since} ({newest_id}); listing works from {since} on.", file=sys.stderr)
    user = re.search(r"scholar\.google\.com/citations\?user=([\w-]+)", page).group(1)

    orc = orcid(a.orcid, 0)
    newest = max((w["year"] for w in orc), default=0)
    print(f"ORCID {a.orcid}: {sum(w['year'] >= since for w in orc)} works since {since}; newest ORCID work is from {newest}.", file=sys.stderr)
    works = scholar(user, since) + [w for w in orc if not w["year"] or w["year"] >= since]
    merged = {}
    for w in works:
        arx = re.search(r"arXiv:(\d{4}\.\d{4,5})", w["venue"])
        if not w["id"]:
            w["id"] = ("arxiv:" + arx.group(1)) if arx else resolve(w["title"], w["authors"])
        key = w["id"] or norm_title(w["title"])
        if key in merged:
            merged[key]["source"] += "+" + w["source"]
            merged[key]["venue"] = merged[key]["venue"] or w["venue"]
            merged[key]["authors"] = merged[key]["authors"] or w["authors"]
        else:
            merged[key] = w
    for w in merged.values():
        w["on_site"] = w["id"] in on_site
        w["url"] = ("https://doi.org/" + w["id"][4:]) if w["id"].startswith("doi:") else \
                   ("https://arxiv.org/abs/" + w["id"][6:]) if w["id"].startswith("arxiv:") else ""
    for w in merged.values():
        w["year"] = w["year"] or year_of(w["id"])
    undated = [w for w in merged.values() if not w["year"]]
    if undated:
        print(f"Dropped {len(undated)} undated rows: " + "; ".join(w["title"][:60] for w in undated), file=sys.stderr)
    rows = [w for w in merged.values() if w["year"] >= since]
    # Scholar keeps year-less duplicate records of the same paper; drop them when any other row shares the title stem.
    stem = lambda w: " ".join(norm_title(w["title"]).split()[:5])
    rows = [w for i, w in enumerate(rows) if w["year"] or all(stem(w) != stem(v) for j, v in enumerate(rows) if j < i or v["year"])]
    # A preprint and its journal version get different IDs; count a row as on the page when a linked row has the same title.
    linked = [norm_title(w["title"]) for w in rows if w["on_site"]]
    # A follow-up of an artifact already named on the page (MatterSim -> MatterSim-MT) is not news; mark it so it is skipped.
    names = {t for t in re.findall(r'<a [^>]*>([^<]+)</a>', page) if re.fullmatch(r"[A-Z][\w-]{3,}", t)}
    for w in rows:
        hit = next((t for t in names if re.match(re.escape(t) + r"\b", w["title"], re.I)), None)
        if not w["on_site"] and hit:
            w["on_site"] = f"follow-up of {hit}"
    for w in rows:
        n = norm_title(w["title"])
        if not w["on_site"] and any(SequenceMatcher(None, n, t).ratio() > 0.85 or t.startswith(n) for t in linked):
            w["on_site"] = "other version"
    gh = re.search(r'href="https://github\.com/([\w-]+)"', page)
    if gh:
        linked = {h.lower().rstrip("/") for h in re.findall(r'href="([^"]+)"', page)}
        try:
            rows += github(gh.group(1), since, linked)
        except Exception as e:
            print(f"GitHub check failed ({e}); check public repos by hand.", file=sys.stderr)
    rows = sorted(rows, key=lambda w: (bool(w["on_site"]), -w["year"]))
    if a.json:
        print(json.dumps(rows, indent=1, ensure_ascii=False))
        return
    print(f"| on site | year | source | title | venue | authors | url |\n|---|---|---|---|---|---|---|")
    for w in rows:
        print(f"| {('yes' if w['on_site'] is True else w['on_site']) if w['on_site'] else '**no**'} | {w['year'] or '?'} | {w['source']} | {w['title']} | {w['venue']} | {w['authors']} | {w['url']} |")


if __name__ == "__main__":
    main()
