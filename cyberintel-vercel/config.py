USER_PROFILE = {
    "name": "CyberIntel User",
    "skills": [
        "cybersecurity", "penetration testing", "threat intelligence",
        "network security", "vulnerability assessment", "SIEM",
        "incident response", "python", "linux"
    ],
    "interests": [
        "cyber threats", "data breaches", "ransomware", "zero-day vulnerabilities",
        "bug bounty", "CTF", "security tools", "AI security", "cloud security",
        "malware analysis", "OSINT", "threat hunting"
    ],
    "goals": [
        "find cybersecurity job opportunities",
        "discover new security tools",
        "stay updated on latest CVEs and threats",
        "find bug bounty programs",
        "learn about certifications"
    ],
    "priority_keywords": [
        "critical", "zero-day", "0-day", "RCE", "remote code execution",
        "active exploitation", "ransomware", "data breach", "urgent"
    ]
}

SCRAPER_SETTINGS = {
    "max_items_per_source": 10,
    "request_delay_seconds": 2,
    "request_timeout": 15,
    "user_agent": "Mozilla/5.0 (compatible; CyberIntelBot/1.0)"
}

AGENT_SETTINGS = {
    "model": "llama-3.3-70b-versatile",
    "max_tokens": 2048,
    "temperature": 0.2,
    "batch_size": 5
}
