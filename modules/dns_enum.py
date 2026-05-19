import dns.resolver
import dns.rdatatype
import requests
from .base import ScanWorker

RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME"]
COMMON_SUBS  = [
    "www","mail","ftp","smtp","pop","imap","vpn","remote","dev","staging",
    "api","cdn","admin","portal","test","shop","blog","login","secure",
    "webmail","autodiscover","ns1","ns2","mx","mx1","mx2","gateway",
]

def resolve(domain, rtype):
    try:
        answers = dns.resolver.resolve(domain, rtype, lifetime=5)
        return [str(r) for r in answers]
    except Exception:
        return []

def run_scan(target: str, **kwargs) -> dict:
    result  = ScanWorker.empty_result(target)
    records = {}

    for rtype in RECORD_TYPES:
        vals = resolve(target, rtype)
        if vals:
            records[rtype] = vals

    result["data"]["records"] = records

    for rtype, vals in records.items():
        for v in vals:
            result["findings"].append(f"{rtype}: {v}")

    # Subdomain bruteforce via DNS
    found_subs = []
    for sub in COMMON_SUBS:
        fqdn = f"{sub}.{target}"
        a = resolve(fqdn, "A")
        if a:
            found_subs.append({"subdomain": fqdn, "ips": a})

    result["data"]["subdomains"] = found_subs
    for s in found_subs:
        result["findings"].append(f"Subdomain: {s['subdomain']} -> {', '.join(s['ips'])}")

    # Basic risk scoring
    score = 0
    if "TXT" in records:
        for txt in records["TXT"]:
            if "spf" not in txt.lower() and "dmarc" not in txt.lower():
                pass
        has_spf   = any("v=spf1" in t for t in records.get("TXT", []))
        has_dmarc = any("v=dmarc1" in t.lower() for t in records.get("TXT", []))
        if not has_spf:
            score += 20
            result["findings"].append("[RISK] No SPF record – email spoofing possible")
        if not has_dmarc:
            score += 20
            result["findings"].append("[RISK] No DMARC record found")

    result["risk_score"] = min(score, 100)
    return result


class Worker(ScanWorker):
    def run(self):
        self.log(f"DNS enumeration: {self.target}", "INFO")
        self.progress.emit(10)
        result = run_scan(self.target, **self.kwargs)
        self.progress.emit(100)
        self.log(f"DNS done – {len(result['data'].get('subdomains', []))} subdomains found",
                 "SUCCESS" if result["status"] == "success" else "ERROR")
        self.result_ready.emit(result)
