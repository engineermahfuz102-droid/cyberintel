"""Groq AI agent — filters, summarizes, and categorizes scraped items."""
import os
import json
import requests
from config import USER_PROFILE, AGENT_SETTINGS

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def process(raw_items: list[dict]) -> list[dict]:
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")

    batch_size = AGENT_SETTINGS["batch_size"]
    processed  = []

    for i in range(0, len(raw_items), batch_size):
        batch  = raw_items[i:i + batch_size]
        result = _batch(api_key, batch)
        processed.extend(result)
        print(f"  Agent batch {i//batch_size+1}: {len(result)} relevant items")

    processed.sort(key=lambda x: x.get("urgency", 1), reverse=True)
    return processed


def _batch(api_key: str, batch: list[dict]) -> list[dict]:
    items_text = ""
    for idx, item in enumerate(batch, 1):
        items_text += (f"\nItem {idx}:\n"
                       f"  Title: {item.get('title','')}\n"
                       f"  Source: {item.get('source','')}\n"
                       f"  URL: {item.get('url','')}\n"
                       f"  Summary: {item.get('summary','')}\n"
                       f"  Published: {item.get('published','')}\n")

    system = (
        "You are a cybersecurity intelligence analyst.\n\n"
        f"USER PROFILE:\n"
        f"- Skills: {', '.join(USER_PROFILE['skills'])}\n"
        f"- Interests: {', '.join(USER_PROFILE['interests'])}\n"
        f"- Priority keywords: {', '.join(USER_PROFILE['priority_keywords'])}\n\n"
        "For each item: if relevant, write a 2-3 sentence summary, assign category "
        "(news|cve|job|tool|opportunity|trend), and urgency 1-5 "
        "(5=critical active exploit, 4=high, 3=medium, 2=low, 1=minimal).\n"
        "Return ONLY a valid JSON array. No markdown. No explanation.\n"
        'Each object: {"title":"","url":"","source":"","summary":"","category":"","urgency":3,"published":""}\n'
        "Omit irrelevant items. If none relevant return: []"
    )

    try:
        r = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}",
                     "Content-Type": "application/json"},
            json={"model": AGENT_SETTINGS["model"],
                  "max_tokens": AGENT_SETTINGS["max_tokens"],
                  "temperature": AGENT_SETTINGS["temperature"],
                  "messages": [{"role": "system", "content": system},
                               {"role": "user",
                                "content": f"Analyze:\n{items_text}\nReturn JSON array:"}]},
            timeout=60
        )
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"].strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        parsed = json.loads(content.strip())
        return parsed if isinstance(parsed, list) else [parsed]
    except Exception as e:
        print(f"  Agent batch error: {e}")
        return []
