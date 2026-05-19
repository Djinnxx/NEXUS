import requests
import re
from .base import ScanWorker

def _detect_type(target: str) -> str:
    if re.match(r"^[a-fA-F0-9]{32}$",  target): return "md5"
    if re.match(r"^[a-fA-F0-9]{40}$",  target): return "sha1"
    if re.match(r"^[a-fA-F0-9]{64}$",  target): return "sha256"
    if re.match(r"^(\d{1,3}\.){3}\d{1,3}$", target): return "ip"
    if re.match(r"^https?://", target):          return "url"
    return "domain"

def run_scan(target: str, **kwargs) -> dict:
    result  = ScanWorker.empty_result(target)
    ioc_type = _detect_type(target)
    result["data"]["ioc_type"] = ioc_type
    found_threats = []

    # --- URLhaus (URLs / domains / IPs) ---------------------------------
    if ioc_type in ("url", "domain", "ip"):
        try:
            endpoint = "url" if ioc_type == "url" else "host"
            r = requests.post(
                f"https://urlhaus-api.abuse.ch/v1/{endpoint}/",
                data={"url" if ioc_type == "url" else "host": target},
                timeout=10,
            )
            data = r.json()
            if data.get("query_status") not in ("no_results", "not_found"):
                entry = {
                    "source":  "URLhaus",
                    "status":  data.get("url_status", data.get("blacklists", "N/A")),
                    "threat":  data.get("threat", "malware"),
                    "tags":    data.get("tags", []),
                    "added":   data.get("date_added", "")[:10],
                }
                found_threats.append(entry)
                result["findings"].append(
                    f"[URLhaus] Malicious: {entry['threat']} | Status: {entry['status']}"
                )
        except Exception:
            pass

    # --- ThreatFox (all IOC types) --------------------------------------
    try:
        r = requests.post(
            "https://threatfox-api.abuse.ch/api/v1/",
            json={"query": "search_ioc", "search_term": target},
            timeout=10,
        )
        data = r.json()
        if data.get("query_status") == "ok":
            for entry in data.get("data", [])[:5]:
                threat = {
                    "source":    "ThreatFox",
                    "malware":   entry.get("malware_printable", "N/A"),
                    "ioc_type":  entry.get("ioc_type", "N/A"),
                    "confidence":entry.get("confidence_level", 0),
                    "tags":      entry.get("tags", []),
                    "first_seen":entry.get("first_seen", "")[:10],
                }
                found_threats.append(threat)
                result["findings"].append(
                    f"[ThreatFox] {threat['malware']} | Confidence: {threat['confidence']}% | {threat['first_seen']}"
                )
    except Exception:
        pass

    # --- MalwareBazaar (file hashes) ------------------------------------
    if ioc_type in ("md5", "sha1", "sha256"):
        try:
            r = requests.post(
                "https://mb-api.abuse.ch/api/v1/",
                data={"query": "get_info", "hash": target},
                timeout=10,
            )
            data = r.json()
            if data.get("query_status") == "ok":
                for item in data.get("data", [])[:3]:
                    threat = {
                        "source":    "MalwareBazaar",
                        "malware":   item.get("signature", "N/A"),
                        "file_type": item.get("file_type", "N/A"),
                        "first_seen":item.get("first_seen", "")[:10],
                        "tags":      item.get("tags", []),
                    }
                    found_threats.append(threat)
                    result["findings"].append(
                        f"[MalwareBazaar] {threat['malware']} | {threat['file_type']} | {threat['first_seen']}"
                    )
        except Exception:
            pass

    result["data"]["threats"] = found_threats
    result["data"]["total"]   = len(found_threats)

    if found_threats:
        result["risk_score"] = min(len(found_threats) * 25, 100)
        result["findings"].insert(0, f"[CRITICAL] IOC matched {len(found_threats)} threat intelligence entries!")
    else:
        result["findings"].append("IOC not found in threat intelligence databases.")

    return result


class Worker(ScanWorker):
    def run(self):
        self.log(f"IOC check: {self.target}", "INFO")
        self.progress.emit(10)
        result = run_scan(self.target, **self.kwargs)
        self.progress.emit(100)
        self.log(f"IOC check done – {result['data'].get('total', 0)} threats",
                 "WARNING" if result["data"].get("total", 0) > 0 else "SUCCESS")
        self.result_ready.emit(result)
