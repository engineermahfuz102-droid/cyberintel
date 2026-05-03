import feedparser, time, re
from datetime import datetime
from config import SCRAPER_SETTINGS

def scrape_thehackernews():
    print("  [TheHackerNews] Fetching...")
    try:
        feed = feedparser.parse("https://feeds.feedburner.com/TheHackersNews")
        articles = []
        for entry in feed.entries[:SCRAPER_SETTINGS["max_items_per_source"]]:
            summary = re.sub(re.compile('<.*?>'), '', entry.get("summary", ""))
            articles.append({
                "title": entry.get("title", "").strip(),
                "url": entry.get("link", ""),
                "summary": summary[:500],
                "source": "The Hacker News",
                "category": "news",
                "published": _date(entry.get("published", ""))
            })
        print(f"  [TheHackerNews] OK - {len(articles)} articles")
        time.sleep(SCRAPER_SETTINGS["request_delay_seconds"])
        return articles
    except Exception as e:
        print(f"  [TheHackerNews] ERROR: {e}")
        return []

def _date(s):
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(s).strftime("%Y-%m-%d %H:%M")
    except:
        return datetime.now().strftime("%Y-%m-%d %H:%M")
