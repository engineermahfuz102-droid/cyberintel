"""Supabase database helpers."""
import os
import json
from datetime import datetime


def get_client():
    from supabase import create_client
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
    return create_client(url, key)


def save_digest(items: list[dict]) -> str:
    """Save a digest run to Supabase. Returns the digest ID."""
    client = get_client()
    now    = datetime.utcnow().isoformat()
    digest = {
        "generated_at": now,
        "item_count":   len(items),
        "items":        json.dumps(items)
    }
    result = client.table("digests").insert(digest).execute()
    return result.data[0]["id"] if result.data else None


def get_latest_digest() -> dict | None:
    """Fetch the most recent digest from Supabase."""
    client = get_client()
    result = (client.table("digests")
              .select("*")
              .order("generated_at", desc=True)
              .limit(1)
              .execute())
    if not result.data:
        return None
    row = result.data[0]
    row["items"] = json.loads(row["items"])
    return row


def get_all_digests() -> list[dict]:
    """Fetch last 30 digest summaries (no items) for history view."""
    client = get_client()
    result = (client.table("digests")
              .select("id, generated_at, item_count")
              .order("generated_at", desc=True)
              .limit(30)
              .execute())
    return result.data or []
