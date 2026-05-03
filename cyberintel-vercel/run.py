import os, json, sys
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from scrapers import scrape_bleepingcomputer, scrape_thehackernews, scrape_nvd
from agent import process_items

def run():
    print("\n=== CyberIntel Brief — Daily Run ===")
    print(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")

    # Step 1: Scrape
    print("[STEP 1] Scraping sources...")
    raw = []
    for name, fn in [("BleepingComputer", scrape_bleepingcomputer),
                     ("The Hacker News",  scrape_thehackernews),
                     ("NVD / NIST",       scrape_nvd)]:
        try:
            items = fn()
            raw.extend(items)
        except Exception as e:
            print(f"  [{name}] FAILED: {e}")

    print(f"\n  Total collected: {len(raw)} items")
    if not raw:
        print("Nothing scraped. Exiting.")
        return

    # Step 2: AI Agent
    print("\n[STEP 2] Running AI agent...")
    try:
        processed = process_items(raw)
    except Exception as e:
        print(f"Agent error: {e}")
        return

    if not processed:
        print("No relevant items returned.")
        return

    # Step 3: Save to Supabase
    print(f"\n[STEP 3] Saving {len(processed)} items to Supabase...")
    _save_to_supabase(processed)
    print("\n=== Run complete ===")

def _save_to_supabase(items):
    import requests as req
    url  = os.environ.get("SUPABASE_URL")
    key  = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        print("  ERROR: SUPABASE_URL or SUPABASE_SERVICE_KEY not set")
        return

    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "date":       now[:10],
        "created_at": now,
        "item_count": len(items),
        "items":      json.dumps(items)
    }

    r = req.post(
        f"{url}/rest/v1/digests",
        headers={
            "apikey":        key,
            "Authorization": f"Bearer {key}",
            "Content-Type":  "application/json",
            "Prefer":        "return=minimal"
        },
        json=payload,
        timeout=15
    )
    if r.status_code in (200, 201):
        print(f"  Saved digest for {now[:10]}")
    else:
        print(f"  Supabase error {r.status_code}: {r.text[:200]}")

if __name__ == "__main__":
    run()
