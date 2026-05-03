"""
Vercel Cron Job — runs daily at 6:00 AM UTC (configured in vercel.json).
Scrapes sources, processes with AI, saves to Supabase.
"""
from http.server import BaseHTTPRequestHandler
import json
import os


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # Verify this is called by Vercel cron (not a random visitor)
        auth = self.headers.get("authorization", "")
        cron_secret = os.environ.get("CRON_SECRET", "")
        if cron_secret and auth != f"Bearer {cron_secret}":
            self._respond(401, {"error": "Unauthorized"})
            return

        try:
            print("=== CyberIntel Cron Job Starting ===")

            # Step 1: Scrape
            from scraper import scrape_all
            raw_items = scrape_all()
            print(f"Scraped {len(raw_items)} raw items")

            if not raw_items:
                self._respond(200, {"status": "no_items", "message": "No items scraped"})
                return

            # Step 2: AI Agent
            from agent import process
            processed = process(raw_items)
            print(f"Agent returned {len(processed)} relevant items")

            if not processed:
                self._respond(200, {"status": "no_relevant", "message": "No relevant items"})
                return

            # Step 3: Save to Supabase
            from db import save_digest
            digest_id = save_digest(processed)
            print(f"Saved digest ID: {digest_id}")

            self._respond(200, {
                "status":    "success",
                "digest_id": digest_id,
                "raw":       len(raw_items),
                "processed": len(processed)
            })

        except Exception as e:
            print(f"Cron error: {e}")
            self._respond(500, {"status": "error", "message": str(e)})

    def _respond(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # suppress default logging
