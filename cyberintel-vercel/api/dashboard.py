"""Dashboard endpoint — serves the full HTML dashboard with live data from Supabase."""
from http.server import BaseHTTPRequestHandler
from datetime import datetime
from collections import Counter
import json
import os


CAT_COLOR = {
    "cve": "#FF4D6A", "news": "#3B8BEB", "tool": "#00DC82",
    "job": "#A78BFA", "opportunity": "#FF9D3D", "trend": "#60D9F0"
}
URG_COLOR = {5:"#FF4D6A", 4:"#FF9D3D", 3:"#EDD700", 2:"#3B8BEB", 1:"#4A5E4E"}
URG_LBL   = {5:"CRITICAL", 4:"HIGH", 3:"MEDIUM", 2:"LOW", 1:"MINIMAL"}


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            from db import get_latest_digest, get_all_digests
            digest  = get_latest_digest()
            history = get_all_digests()
        except Exception as e:
            digest  = None
            history = []
            print(f"DB error: {e}")

        html = _build_html(digest, history)
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


def _badge(text, color):
    return (f'<span style="font-family:monospace;font-size:9px;padding:2px 7px;'
            f'border:1px solid {color}55;background:{color}11;color:{color};'
            f'letter-spacing:.07em;white-space:nowrap">{text}</span>')


def _item_card(item):
    u      = item.get("urgency", 1)
    cat    = item.get("category", "news")
    color  = CAT_COLOR.get(cat, "#00DC82")
    uc     = URG_COLOR.get(u, "#4A5E4E")
    title  = item.get("title", "Untitled")
    summ   = item.get("summary", "")
    url    = item.get("url", "#")
    source = item.get("source", "")
    pub    = item.get("published", "")
    score  = f'&nbsp;|&nbsp;CVSS {item["score"]}' if item.get("score") else ""
    return f"""
<div class="card" style="border-left:3px solid {color}"
     data-cat="{cat}" data-urg="{u}">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:8px">
    <div style="font-size:13.5px;font-weight:500;color:#E8F0E4;line-height:1.45;flex:1">{title}</div>
    <div style="display:flex;gap:6px;flex-shrink:0;flex-wrap:wrap;justify-content:flex-end">
      {_badge("U"+str(u)+" "+URG_LBL.get(u,""), uc)}
      {_badge(cat.upper(), color)}
    </div>
  </div>
  <div style="font-size:12.5px;color:#8A9E8E;line-height:1.65;margin-bottom:10px">{summ}</div>
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px">
    <span style="font-family:monospace;font-size:9px;color:#4A5E4E">
      {source}&nbsp;|&nbsp;{pub}{score}
    </span>
    <a href="{url}" target="_blank" rel="noopener"
       style="font-family:monospace;font-size:9px;color:#00DC82;text-decoration:none;opacity:.7">
      VIEW SOURCE &#8599;
    </a>
  </div>
</div>"""


def _build_html(digest, history):
    now = datetime.utcnow()

    if digest:
        items      = digest.get("items", [])
        gen_at     = digest.get("generated_at", "")[:16].replace("T", " ")
        counts     = Counter(i.get("category","?") for i in items)
        critical_n = len([i for i in items if i.get("urgency",1) >= 5])
        high_n     = len([i for i in items if i.get("urgency",1) >= 4])
        src_counts = Counter(i.get("source","") for i in items)
        max_src    = max(src_counts.values(), default=1)
        items_json = json.dumps(items)
        no_data    = ""
    else:
        items = []; gen_at = "No data yet"; counts = Counter()
        critical_n = 0; high_n = 0; src_counts = Counter()
        max_src = 1; items_json = "[]"
        no_data = """
<div style="text-align:center;padding:60px 20px;border:1px dashed rgba(0,220,130,.2);
            background:#0D1219;margin-bottom:20px">
  <div style="font-family:monospace;font-size:11px;color:#4A5E4E;letter-spacing:.1em;margin-bottom:10px">
    NO DIGEST DATA YET
  </div>
  <div style="font-size:12px;color:#4A5E4E">
    The cron job runs daily at 6:00 AM UTC.<br>
    You can trigger it manually at <code style="color:#00DC82">/api/cron</code>
  </div>
</div>"""

    # stat cards
    stats_html = ""
    for lbl, val, ac in [
        ("Total Items",   len(items),              "#00DC82"),
        ("Critical",      critical_n,              "#FF4D6A"),
        ("CVEs Found",    counts.get("cve",0),     "#FF4D6A"),
        ("Sources",       len(src_counts),         "#3B8BEB"),
        ("Opportunities", counts.get("opportunity",0)+counts.get("job",0), "#FF9D3D"),
    ]:
        stats_html += f"""
<div style="background:#0D1219;border:1px solid #1a2a1a;border-bottom:2px solid {ac};padding:14px 16px">
  <div style="font-family:monospace;font-size:8px;letter-spacing:.12em;color:#4A5E4E;
              text-transform:uppercase;margin-bottom:8px">{lbl}</div>
  <div style="font-family:monospace;font-size:26px;font-weight:700;color:{ac};line-height:1">{val}</div>
</div>"""

    # category grid
    cat_html = ""
    for cat in ["cve","news","tool","job","opportunity","trend"]:
        c = CAT_COLOR.get(cat,"#00DC82")
        n = counts.get(cat,0)
        cat_html += f"""
<div class="cat-cell" onclick="filterCat('{cat}')"
     style="background:#0D1219;padding:11px 13px;cursor:pointer;border-bottom:2px solid {c}22">
  <div style="width:18px;height:18px;border:1px solid {c};display:flex;
              align-items:center;justify-content:center;margin-bottom:5px">
    <div style="width:6px;height:6px;background:{c}"></div>
  </div>
  <div style="font-family:monospace;font-size:17px;font-weight:700;color:{c};
              line-height:1;margin-bottom:2px">{n}</div>
  <div style="font-family:monospace;font-size:7px;letter-spacing:.1em;
              color:#4A5E4E;text-transform:uppercase">{cat}</div>
</div>"""

    # source list
    src_html = ""
    for src, cnt in sorted(src_counts.items(), key=lambda x:-x[1]):
        pct = int(cnt / max_src * 100)
        src_html += f"""
<div style="display:flex;align-items:center;padding:7px 14px;gap:8px">
  <div style="width:5px;height:5px;border-radius:50%;background:#00DC82;flex-shrink:0"></div>
  <div style="font-size:10px;color:#8A9E8E;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{src}</div>
  <div style="width:50px;height:2px;background:#161E28;flex-shrink:0">
    <div style="width:{pct}%;height:100%;background:#00DC82"></div>
  </div>
  <div style="font-family:monospace;font-size:8px;color:#4A5E4E;min-width:14px;text-align:right">{cnt}</div>
</div>"""

    # history list
    hist_html = ""
    for row in history[:10]:
        d = row.get("generated_at","")[:10]
        n = row.get("item_count", 0)
        hist_html += f"""
<div style="display:flex;align-items:center;justify-content:space-between;
            padding:7px 14px;border-bottom:1px solid #1a2a1a">
  <span style="font-family:monospace;font-size:9px;color:#8A9E8E">{d}</span>
  <span style="font-family:monospace;font-size:9px;color:#00DC82">{n} items</span>
</div>"""

    # all item cards
    cards_html = no_data + "".join(_item_card(i) for i in items)

    # threat arc
    score_val  = min(10, round((critical_n * 2.5 + high_n * 0.8), 1)) if items else 0
    arc_offset = round(251 - (251 * score_val / 10))
    threat_color = "#FF4D6A" if score_val >= 7 else "#FF9D3D" if score_val >= 4 else "#00DC82"
    threat_lbl   = "HIGH ALERT" if score_val >= 7 else "ELEVATED" if score_val >= 4 else "NOMINAL"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CyberIntel Brief</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#080C12;color:#E8F0E4;font-family:-apple-system,'Segoe UI',system-ui,sans-serif;
     font-size:14px;min-height:100vh}}
body::before{{content:'';position:fixed;inset:0;
  background-image:linear-gradient(rgba(0,220,130,.025) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(0,220,130,.025) 1px,transparent 1px);
  background-size:40px 40px;pointer-events:none;z-index:0}}
.shell{{position:relative;z-index:1;max-width:1300px;margin:0 auto;padding:0 24px 48px}}
.topbar{{display:flex;align-items:center;justify-content:space-between;
         padding:18px 0 20px;border-bottom:1px solid rgba(0,220,130,.12);
         margin-bottom:20px;flex-wrap:wrap;gap:10px}}
.stats{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:20px}}
.main{{display:grid;grid-template-columns:1fr 290px;gap:18px;align-items:start}}
.panel{{background:#0D1219;border:1px solid rgba(0,220,130,.12);margin-bottom:14px;overflow:hidden}}
.p-head{{display:flex;align-items:center;justify-content:space-between;
         padding:10px 14px;border-bottom:1px solid rgba(0,220,130,.12)}}
.p-title{{font-family:monospace;font-size:8px;letter-spacing:.14em;color:#00DC82;text-transform:uppercase}}
.p-sub{{font-family:monospace;font-size:8px;color:#4A5E4E}}
.cat-grid{{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:rgba(0,220,130,.1)}}
.cat-cell:hover{{background:#111820 !important}}
.filter-bar{{display:flex;align-items:center;gap:6px;margin-bottom:16px;flex-wrap:wrap}}
.fbtn{{font-family:monospace;font-size:9px;letter-spacing:.06em;padding:5px 11px;
       border:1px solid rgba(0,220,130,.15);background:transparent;color:#8A9E8E;
       cursor:pointer;text-transform:uppercase;transition:all .15s}}
.fbtn:hover,.fbtn.on{{border-color:#00DC82;color:#00DC82;background:rgba(0,220,130,.08)}}
.search{{margin-left:auto;display:flex;align-items:center;gap:8px;
         background:#0D1219;border:1px solid rgba(0,220,130,.15);padding:5px 12px}}
.search input{{background:transparent;border:none;outline:none;color:#E8F0E4;font-size:12px;width:170px}}
.search input::placeholder{{color:#4A5E4E}}
.card{{background:#0D1219;border:1px solid #1a2a1a;padding:16px 18px;
       margin-bottom:8px;transition:border-color .2s}}
.card:hover{{border-color:rgba(0,220,130,.2)}}
.dot{{width:5px;height:5px;background:#00DC82;border-radius:50%;
      animation:blink 1.2s ease-in-out infinite}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
.more-btn{{width:100%;padding:12px;border:1px solid rgba(0,220,130,.15);background:transparent;
           color:#4A5E4E;font-family:monospace;font-size:9px;letter-spacing:.1em;
           cursor:pointer;text-transform:uppercase;margin-top:4px;transition:all .15s}}
.more-btn:hover{{border-color:#00DC82;color:#00DC82;background:rgba(0,220,130,.06)}}
@media(max-width:900px){{.main{{grid-template-columns:1fr}}.stats{{grid-template-columns:repeat(3,1fr)}}}}
@media(max-width:560px){{.stats{{grid-template-columns:repeat(2,1fr)}}}}
</style>
</head>
<body>
<div class="shell">

  <!-- TOPBAR -->
  <div class="topbar">
    <div style="display:flex;align-items:center;gap:12px">
      <div style="width:32px;height:32px;border:1.5px solid #00DC82;display:flex;align-items:center;justify-content:center">
        <div class="dot"></div>
      </div>
      <div>
        <div style="font-family:monospace;font-size:12px;font-weight:700;letter-spacing:.14em;color:#00DC82">CYBERINTEL BRIEF</div>
        <div style="font-size:10px;color:#4A5E4E;font-family:monospace;letter-spacing:.06em;margin-top:2px">Daily Intelligence Dashboard</div>
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap">
      <span style="font-family:monospace;font-size:9px;color:#4A5E4E">Last updated: {gen_at} UTC</span>
      <a href="/api/cron" style="font-family:monospace;font-size:9px;color:#00DC82;text-decoration:none;
         padding:4px 10px;border:1px solid rgba(0,220,130,.3);background:rgba(0,220,130,.06)">
        RUN NOW &#8599;
      </a>
      <div style="display:flex;align-items:center;gap:6px;font-family:monospace;font-size:9px;
                  color:#00DC82;letter-spacing:.1em;padding:4px 10px;
                  border:1px solid rgba(0,220,130,.24);background:rgba(0,220,130,.08)">
        <div class="dot"></div>LIVE
      </div>
    </div>
  </div>

  <!-- STATS -->
  <div class="stats">{stats_html}</div>

  <!-- FILTER BAR -->
  <div class="filter-bar">
    <span style="font-family:monospace;font-size:8px;letter-spacing:.12em;color:#4A5E4E;text-transform:uppercase;margin-right:4px">Filter:</span>
    <button class="fbtn on" onclick="filterCat('all')">All</button>
    <button class="fbtn" onclick="filterCat('cve')">CVE</button>
    <button class="fbtn" onclick="filterCat('news')">News</button>
    <button class="fbtn" onclick="filterCat('tool')">Tools</button>
    <button class="fbtn" onclick="filterCat('job')">Jobs</button>
    <button class="fbtn" onclick="filterCat('opportunity')">Opportunities</button>
    <button class="fbtn" onclick="filterCat('trend')">Trends</button>
    <div class="search">
      <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
        <circle cx="4.5" cy="4.5" r="3.5" stroke="#4A5E4E" stroke-width="1.5"/>
        <line x1="7.5" y1="7.5" x2="10" y2="10" stroke="#4A5E4E" stroke-width="1.5"/>
      </svg>
      <input type="text" placeholder="Search items..." oninput="search(this.value)">
    </div>
  </div>

  <!-- MAIN GRID -->
  <div class="main">

    <!-- FEED -->
    <div>
      <div id="feed">{cards_html}</div>
      <button class="more-btn" id="moreBtn" onclick="loadMore()">Load More</button>
    </div>

    <!-- SIDEBAR -->
    <div>

      <!-- THREAT LEVEL -->
      <div class="panel">
        <div class="p-head">
          <span class="p-title">Threat Level</span>
          <span class="p-sub">{critical_n} critical</span>
        </div>
        <div style="padding:18px 14px;text-align:center">
          <div style="width:100px;height:100px;margin:0 auto 14px;position:relative">
            <svg width="100" height="100" viewBox="0 0 100 100" style="transform:rotate(-90deg)">
              <circle cx="50" cy="50" r="40" fill="none" stroke="{threat_color}22" stroke-width="7"/>
              <circle cx="50" cy="50" r="40" fill="none" stroke="{threat_color}" stroke-width="7"
                stroke-dasharray="251" stroke-dashoffset="{arc_offset}" stroke-linecap="square"/>
            </svg>
            <div style="position:absolute;inset:0;display:flex;flex-direction:column;
                        align-items:center;justify-content:center">
              <div style="font-family:monospace;font-size:20px;font-weight:700;color:{threat_color};line-height:1">{score_val}</div>
              <div style="font-family:monospace;font-size:8px;color:#4A5E4E;margin-top:1px">/ 10</div>
            </div>
          </div>
          <div style="font-family:monospace;font-size:10px;letter-spacing:.08em;color:{threat_color};margin-bottom:3px">{threat_lbl}</div>
          <div style="font-size:10px;color:#4A5E4E">{critical_n} critical, {high_n} high severity</div>
        </div>
      </div>

      <!-- SOURCES -->
      <div class="panel">
        <div class="p-head">
          <span class="p-title">Sources</span>
          <span class="p-sub">{len(src_counts)} active</span>
        </div>
        <div style="padding:4px 0">{src_html}</div>
      </div>

      <!-- CATEGORIES -->
      <div class="panel">
        <div class="p-head"><span class="p-title">Categories</span></div>
        <div class="cat-grid">{cat_html}</div>
      </div>

      <!-- HISTORY -->
      <div class="panel">
        <div class="p-head">
          <span class="p-title">Digest History</span>
          <span class="p-sub">{len(history)} runs</span>
        </div>
        <div>{hist_html if hist_html else '<div style="padding:14px;font-family:monospace;font-size:9px;color:#4A5E4E">No history yet</div>'}</div>
      </div>

    </div>
  </div>
</div>

<script>
const ALL_ITEMS = {items_json};
let currentCat = 'all';
let currentQ   = '';
let visible    = 10;

function filtered() {{
  return ALL_ITEMS.filter(i => {{
    const matchCat = currentCat === 'all' || i.category === currentCat;
    const matchQ   = !currentQ ||
      (i.title||'').toLowerCase().includes(currentQ) ||
      (i.summary||'').toLowerCase().includes(currentQ) ||
      (i.source||'').toLowerCase().includes(currentQ);
    return matchCat && matchQ;
  }});
}}

const CAT_COLOR = {json.dumps(CAT_COLOR)};
const URG_COLOR = {json.dumps({str(k):v for k,v in URG_COLOR.items()})};
const URG_LBL   = {json.dumps({str(k):v for k,v in URG_LBL.items()})};

function badge(text, color) {{
  return `<span style="font-family:monospace;font-size:9px;padding:2px 7px;
    border:1px solid ${{color}}55;background:${{color}}11;color:${{color}};
    letter-spacing:.07em;white-space:nowrap">${{text}}</span>`;
}}

function renderCard(item) {{
  const u     = item.urgency || 1;
  const cat   = item.category || 'news';
  const color = CAT_COLOR[cat] || '#00DC82';
  const uc    = URG_COLOR[String(u)] || '#4A5E4E';
  const score = item.score ? `&nbsp;|&nbsp;CVSS ${{item.score}}` : '';
  return `
<div class="card" style="border-left:3px solid ${{color}}">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:8px">
    <div style="font-size:13.5px;font-weight:500;color:#E8F0E4;line-height:1.45;flex:1">${{item.title||''}}</div>
    <div style="display:flex;gap:6px;flex-shrink:0;flex-wrap:wrap;justify-content:flex-end">
      ${{badge('U'+u+' '+(URG_LBL[String(u)]||''), uc)}}
      ${{badge(cat.toUpperCase(), color)}}
    </div>
  </div>
  <div style="font-size:12.5px;color:#8A9E8E;line-height:1.65;margin-bottom:10px">${{item.summary||''}}</div>
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px">
    <span style="font-family:monospace;font-size:9px;color:#4A5E4E">
      ${{item.source||''}}&nbsp;|&nbsp;${{item.published||''}}${{score}}
    </span>
    <a href="${{item.url||'#'}}" target="_blank" rel="noopener"
       style="font-family:monospace;font-size:9px;color:#00DC82;text-decoration:none;opacity:.7">
      VIEW SOURCE &#8599;
    </a>
  </div>
</div>`;
}}

function render() {{
  const f    = filtered();
  const show = f.slice(0, visible);
  const feed = document.getElementById('feed');
  const btn  = document.getElementById('moreBtn');
  if (show.length === 0) {{
    feed.innerHTML = '<div style="text-align:center;padding:40px;border:1px dashed rgba(0,220,130,.2);background:#0D1219;font-family:monospace;font-size:9px;color:#4A5E4E;letter-spacing:.1em">NO ITEMS MATCH</div>';
  }} else {{
    feed.innerHTML = show.map(renderCard).join('');
  }}
  btn.style.display = f.length > visible ? 'block' : 'none';
  btn.textContent   = `Load More  (${{f.length - visible}} remaining)`;
}}

function filterCat(cat) {{
  currentCat = cat;
  visible    = 10;
  document.querySelectorAll('.fbtn').forEach(b => b.classList.remove('on'));
  event.target.classList.add('on');
  render();
}}

function search(q) {{
  currentQ = q.toLowerCase();
  visible  = 10;
  render();
}}

function loadMore() {{
  visible += 10;
  render();
}}

render();
</script>
</body>
</html>"""

