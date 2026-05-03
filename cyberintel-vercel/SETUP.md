# CyberIntel Brief — Vercel Deployment Guide

## Architecture
- GitHub Actions → runs scraper + Groq AI daily at 6AM UTC
- Supabase → stores digest results (free tier)
- Vercel → hosts the dashboard + API (free tier)

---

## STEP 1 — Set up Supabase

1. Go to https://supabase.com and create a free account
2. Create a new project (any name, e.g. "cyberintel")
3. Once created, go to: Project → SQL Editor
4. Run this SQL to create the digests table:

```sql
CREATE TABLE digests (
  id          BIGSERIAL PRIMARY KEY,
  date        TEXT NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  item_count  INTEGER,
  items       TEXT
);

-- Allow public read (dashboard fetches this)
ALTER TABLE digests ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow public read" ON digests FOR SELECT USING (true);
```

5. Go to: Project Settings → API
   - Copy "Project URL"         → this is your SUPABASE_URL
   - Copy "anon public" key     → this is your SUPABASE_ANON_KEY
   - Copy "service_role" key    → this is your SUPABASE_SERVICE_KEY

---

## STEP 2 — Push to GitHub

1. Create a new GitHub repo (e.g. "cyberintel-brief")
2. Push this entire folder:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/cyberintel-brief.git
git push -u origin main
```

3. Go to your repo → Settings → Secrets and variables → Actions
4. Add these repository secrets:

   GROQ_API_KEY         = your Groq key from console.groq.com
   SUPABASE_URL         = your Supabase project URL
   SUPABASE_SERVICE_KEY = your Supabase service_role key

---

## STEP 3 — Deploy to Vercel

1. Go to https://vercel.com and sign in with GitHub
2. Click "Add New Project" → Import your GitHub repo
3. In Environment Variables, add:

   SUPABASE_URL      = your Supabase project URL
   SUPABASE_ANON_KEY = your Supabase anon public key

4. Click Deploy — your dashboard will be live in ~30 seconds

---

## STEP 4 — First Manual Run

To test before the daily schedule kicks in:
1. Go to your GitHub repo → Actions tab
2. Click "CyberIntel Daily Digest" → "Run workflow"
3. Wait ~2 minutes for it to complete
4. Open your Vercel dashboard URL — data will appear!

---

## Daily Schedule
The agent runs automatically every day at 6:00 AM UTC.
To change the time, edit .github/workflows/daily.yml — cron line.

Timezone reference:
  "0 6 * * *"  = 6:00 AM UTC = 7:00 AM Lagos/WAT
  "0 5 * * *"  = 5:00 AM UTC = 6:00 AM Lagos/WAT

---

## File Structure
  api/digest.js                  Vercel API — fetches data from Supabase
  public/index.html              Dashboard UI
  .github/workflows/daily.yml    GitHub Actions — daily automation
  agent/processor.py             Groq AI agent
  scrapers/                      BleepingComputer, TheHackerNews, NVD
  run.py                         Entry point for GitHub Actions
  config.py                      Your profile — edit this!
  requirements.txt               Python dependencies
  vercel.json                    Vercel routing config
