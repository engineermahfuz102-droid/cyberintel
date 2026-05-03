"""Scrapes BleepingComputer, The Hacker News, and NVD CVEs."""
import re
import time
import requests
import feedparser
from datetime import datetime, timedelta
from config import SCRAPER_SETTINGS

HEADERS = {"User-Agent": SCRAPER_SETTINGS["user_agent"]}
TIMEOUT = SCRAPER_SETTINGS["request_timeout"]
MAX     = SCRAPER_SETTINGS["max_items_per_source"]


def scrape_all() -> list[dict]:
    items = []
    for fn in [_bleepingcomputer, _thehackernews, _nvd]:
        try:
            results = fn()
            items.extend(results)
            print(f"  Scraped {len(results)} from {fn.__name__}")
        except Exception as e:
            print(f"  Scraper {fn.__name__} failed: {e}")
    return items


def _bleepingcomputer() -> list[dict]:
    feed = feedparser.parse("https://www.bleepingcomputer.com/feed/")
    return [_entry(e, "BleepingComputer", "news") for e in feed.entries[:MAX]]


def _thehackernews() -> list[dict]:
    feed = feedparser.parse("https://feeds.feedburner.com/TheHackersNews")
    return [_entry(e, "The Hacker News", "news") for e in feed.entries[:MAX]]


def _nvd() -> list[dict]:
    end   = datetime.utcnow()
    start = end - timedelta(days=2)
    params = {
        "pubStartDate": start.strftime("%Y-%m-%dT00:00:00.000"),
        "pubEndDate":   end.strftime("%Y-%m-%dT23:59:59.000"),
        "resultsPerPage": 20
    }
    r = requests.get("https://services.nvd.nist.gov/rest/json/cves/2.0",
                     params=params, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    cves = []
    for item in r.json().get("vulnerabilities", []):
        cve = item.get("cve", {})
        cve_id = cve.get("id", "Unknown")
        desc = next((d["value"] for d in cve.get("descriptions", [])
                     if d.get("lang") == "en"), "No description.")
        severity, score = _cvss(cve)
        if severity not in ("HIGH", "CRITICAL"):
            continue
        cves.append({
            "title":     f"{cve_id} — {severity} Severity",
            "url":       f"https://nvd.nist.gov/vuln/detail/{cve_id}",
            "summary":   desc[:500],
            "source":    "NVD / NIST",
            "category":  "cve",
            "published": cve.get("published", "")[:16].replace("T", " "),
            "score":     score
        })
    cves.sort(key=lambda x: x.get("score", 0), reverse=True)
    return cves[:MAX]


def _entry(e, source, category) -> dict:
    return {
        "title":     e.get("title", "").strip(),
        "url":       e.get("link", ""),
        "summary":   _strip(e.get("summary", ""))[:500],
        "source":    source,
        "category":  category,
        "published": _date(e.get("published", ""))
    }


def _strip(text):
    return re.sub(re.compile("<.*?>"), "", text).strip()


def _date(s):
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(s).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d %H:%M")


def _cvss(cve):
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        metrics = cve.get("metrics", {}).get(key, [])
        if metrics:
            d = metrics[0].get("cvssData", {})
            return d.get("baseSeverity", "UNKNOWN").upper(), float(d.get("baseScore", 0))
    return "UNKNOWN", 0.0
