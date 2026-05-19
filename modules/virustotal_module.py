import requests
from .base import ScanWorker
from config.settings import get_api_key

VT_BASE = "https://www.virustotal.com/api/v3"

def _headers(key):
    return {"x-apikey": key, "Accept": "application/json"}

def run_scan(target: str, scan_type: str = "auto", **kwargs) -> dict:
    result  = ScanWorker.empty_result(target)
    api_key = get_api_key("virustotal")

    if not api_key:
        result["status"] = "no_key"
        result["error"]  = "VirusTotal API key not configured. Get a free key at virustotal.com"
        return result

    # Auto-detect type
    import re
    if scan_type == "auto":
        if re.match(r"^(\d{1,3}\.){3}\d{1,3}$", target):
            scan_type = "ip"
        elif re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", target):
            scan_type = "domain"
            target    = target.split("@")[1]
        elif re.match(r"^[a-fA-F0-9]{32,64}$", target):
            scan_type = "hash"
        else:
            scan_type = "domain"

    try:
        if scan_type == "ip":
            r = requests.get(f"{VT_BASE}/ip_addresses/{target}", headers=_headers(api_key), timeout=10)
        elif scan_type == "domain":
            r = requests.get(f"{VT_BASE}/domains/{target}", headers=_headers(api_key), timeout=10)
        elif scan_type == "hash":
            r = requests.get(f"{VT_BASE}/files/{target}", headers=_headers(api_key), timeout=10)
        elif scan_type == "url":
            import base64
            url_id = base64.urlsafe_b64encode(target.encode()).decode().rstrip("=")
            r = requests.get(f"{VT_BASE}/urls/{url_id}", headers=_headers(api_key), timeout=10)
        else:
            raise ValueError("Unknown scan type")

        if r.status_code == 404:
            result["findings"].append("Not found in VirusTotal database.")
            return result
        if r.status_code != 200:
            raise ValueError(f"VT API error {r.status_code}: {r.text[:200]}")

        data  = r.json().get("data", {})
        attrs = data.get("attributes", {})
        stats = attrs.get("last_analysis_stats", {})

        malicious  = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)
        total      = sum(stats.values()) or 1

        result["data"]["vt"] = {
            "scan_type":  scan_type,
            "malicious":  malicious,
            "suspicious": suspicious,
            "harmless":   stats.get("harmless", 0),
            "undetected": stats.get("undetected", 0),
            "total":      total,
            "reputation": attrs.get("reputation", 0),
            "categories": attrs.get("categories", {}),
            "tags":       attrs.get("tags", []),
        }

        result["findings"].append(
            f"Detection: {malicious}/{total} engines flagged as malicious"
        )
        if suspicious:
            result["findings"].append(f"{suspicious} engines flagged as suspicious")

        cats = attrs.get("categories", {})
        if cats:
            unique_cats = list(set(cats.values()))[:5]
            result["findings"].append(f"Categories: {', '.join(unique_cats)}")

        # Risk score
        result["risk_score"] = min(int((malicious / total) * 100 + (suspicious / total) * 50), 100)

    except Exception as e:
        result = ScanWorker.error_result(target, str(e))
    return result


class Worker(ScanWorker):
    def run(self):
        self.log(f"VirusTotal lookup: {self.target}", "INFO")
        self.progress.emit(20)
        result = run_scan(self.target, **self.kwargs)
        self.progress.emit(100)
        self.log(f"VT done ({result['status']})",
                 "SUCCESS" if result["status"] == "success" else "WARNING")
        self.result_ready.emit(result)
