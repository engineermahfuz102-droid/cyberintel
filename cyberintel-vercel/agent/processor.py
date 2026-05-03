import os, json, requests
from config import USER_PROFILE, AGENT_SETTINGS

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def process_items(raw_items):
    if not raw_items:
        return []
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set")
    batch_size = AGENT_SETTINGS["batch_size"]
    processed = []
    total = (len(raw_items) + batch_size - 1) // batch_size
    print(f"  [Agent] Processing {len(raw_items)} items in {total} batches...")
    for i in range(0, len(raw_items), batch_size):
        batch = raw_items[i:i+batch_size]
        print(f"  [Agent] Batch {i//batch_size+1}/{total}...")
        processed.extend(_batch(api_key, batch))
    processed.sort(key=lambda x: x.get("urgency",1), reverse=True)
    print(f"  [Agent] Done - {len(processed)} relevant items")
    return processed

def _batch(api_key, batch):
    items_text = ""
    for idx, item in enumerate(batch, 1):
        items_text += (f"\nItem {idx}:\n  Title: {item.get('title','')}\n"
            f"  Source: {item.get('source','')}\n  URL: {item.get('url','')}\n"
            f"  Summary: {item.get('summary','')}\n  Published: {item.get('published','')}\n")
    system = (
        "You are a cybersecurity intelligence analyst.\n\n"
        f"USER SKILLS: {', '.join(USER_PROFILE['skills'])}\n"
        f"USER INTERESTS: {', '.join(USER_PROFILE['interests'])}\n"
        f"PRIORITY KEYWORDS: {', '.join(USER_PROFILE['priority_keywords'])}\n\n"
        "For each item: filter by relevance, write 2-3 sentence summary, assign category "
        "(news|cve|job|tool|opportunity|trend), assign urgency 1-5 (5=critical).\n"
        "Return ONLY a valid JSON array. No markdown. No explanation.\n"
        'Each: {"title":"","url":"","source":"","summary":"","category":"","urgency":3,"published":""}\n'
        "Omit irrelevant items. If none: []"
    )
    try:
        r = requests.post(GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": AGENT_SETTINGS["model"], "max_tokens": AGENT_SETTINGS["max_tokens"],
                  "temperature": AGENT_SETTINGS["temperature"],
                  "messages": [{"role":"system","content":system},
                                {"role":"user","content":f"Analyze:\n{items_text}\nReturn JSON:"}]},
            timeout=60)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"].strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"): content = content[4:]
        parsed = json.loads(content.strip())
        return parsed if isinstance(parsed, list) else [parsed]
    except Exception as e:
        print(f"  [Agent] Batch error: {e}")
        return []
