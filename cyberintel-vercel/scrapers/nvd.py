import requests, time
from datetime import datetime, timedelta
from config import SCRAPER_SETTINGS

def scrape_nvd():
    print("  [NVD] Fetching CVEs...")
    end   = datetime.utcnow()
    start = end - timedelta(days=2)
    try:
        r = requests.get("https://services.nvd.nist.gov/rest/json/cves/2.0",
            params={"pubStartDate": start.strftime("%Y-%m-%dT00:00:00.000"),
                    "pubEndDate": end.strftime("%Y-%m-%dT23:59:59.000"),
                    "resultsPerPage": 20},
            headers={"User-Agent": SCRAPER_SETTINGS["user_agent"]},
            timeout=SCRAPER_SETTINGS["request_timeout"])
        r.raise_for_status()
        cves = []
        for item in r.json().get("vulnerabilities", []):
            cve  = item.get("cve", {})
            cid  = cve.get("id","Unknown")
            desc = next((d["value"] for d in cve.get("descriptions",[]) if d.get("lang")=="en"), "")
            sev, score = _severity(cve)
            if sev not in ("HIGH","CRITICAL"):
                continue
            cves.append({"title": f"{cid} - {sev} Severity","url": f"https://nvd.nist.gov/vuln/detail/{cid}",
                "summary": desc[:500],"source": "NVD / NIST","category": "cve",
                "published": cve.get("published","")[:16].replace("T"," "),
                "severity": sev,"score": score})
        cves.sort(key=lambda x: x.get("score",0), reverse=True)
        print(f"  [NVD] OK - {len(cves[:10])} CVEs")
        time.sleep(SCRAPER_SETTINGS["request_delay_seconds"])
        return cves[:10]
    except Exception as e:
        print(f"  [NVD] ERROR: {e}")
        return []

def _severity(cve):
    try:
        for key in ("cvssMetricV31","cvssMetricV30","cvssMetricV2"):
            m = cve.get("metrics",{}).get(key,[])
            if m:
                d = m[0].get("cvssData",{})
                return d.get("baseSeverity","UNKNOWN").upper(), float(d.get("baseScore",0))
    except: pass
    return "UNKNOWN", 0.0
