import feedparser, time, re
from datetime import datetime
from config import SCRAPER_SETTINGS

def scrape_bleepingcomputer():
    print("  [BleepingComputer] Fetching...")
    try:
        feed = feedparser.parse("https://www.bleepingcomputer.com/feed/")
        articles = []
        for entry in feed.entries[:SCRAPER_SETTINGS["max_items_per_source"]]:
            summary = re.sub(re.compile('<.*?>'), '', entry.get("summary", ""))
            articles.append({
                "title": entry.get("title", "").strip(),
                "url": entry.get("link", ""),
                "summary": summary[:500],
                "source": "BleepingComputer",
                "category": "news",
                "published": _date(entry.get("published", ""))
            })
        print(f"  [BleepingComputer] OK - {len(articles)} articles")
        time.sleep(SCRAPER_SETTINGS["request_delay_seconds"])
        return articles
    except Exception as e:
        print(f"  [BleepingComputer] ERROR: {e}")
        return []

def _date(s):
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(s).strftime("%Y-%m-%d %H:%M")
    except:
        return datetime.now().strftime("%Y-%m-%d %H:%M")
