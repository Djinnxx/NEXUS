import requests
from .base import ScanWorker
from config.settings import get_api_key, get_scan_config

HIGH_RISK_COUNTRIES = {"CN", "RU", "KP", "IR", "SY", "CU"}

def run_scan(target: str, **kwargs) -> dict:
    result = ScanWorker.empty_result(target)
    cfg    = get_scan_config()
    timeout = cfg.get("timeout", 10)

    try:
        r    = requests.get(f"https://ipapi.co/{target}/json/", timeout=timeout)
        data = r.json()

        if data.get("error"):
            raise ValueError(data.get("reason", "Invalid IP"))

        geo = {
            "ip":           data.get("ip", target),
            "city":         data.get("city", "Unknown"),
            "region":       data.get("region", ""),
            "country":      data.get("country_name", "Unknown"),
            "country_code": data.get("country_code", ""),
            "postal":       data.get("postal", ""),
            "latitude":     data.get("latitude", 0),
            "longitude":    data.get("longitude", 0),
            "timezone":     data.get("timezone", ""),
            "isp":          data.get("org", "Unknown"),
            "asn":          data.get("asn", ""),
            "hostname":     data.get("hostname", ""),
        }
        result["data"]["geo"] = geo

        # Findings
        result["findings"].append(
            f"Located in {geo['city']}, {geo['region']}, {geo['country']}"
        )
        result["findings"].append(f"ISP/ASN: {geo['isp']} ({geo['asn']})")
        if geo["hostname"]:
            result["findings"].append(f"Reverse DNS: {geo['hostname']}")

        # Risk scoring
        score = 0
        if geo["country_code"] in HIGH_RISK_COUNTRIES:
            score += 35
            result["findings"].append(f"[HIGH RISK] Origin country: {geo['country']}")
        if "hosting" in geo["isp"].lower() or "vps" in geo["isp"].lower():
            score += 15
            result["findings"].append("IP belongs to hosting/VPS provider")
        if "tor" in geo["isp"].lower():
            score += 50
            result["findings"].append("[CRITICAL] Possible Tor exit node detected")

        result["risk_score"] = min(score, 100)

    except requests.RequestException as e:
        result = ScanWorker.error_result(target, f"Network error: {e}")
    except Exception as e:
        result = ScanWorker.error_result(target, str(e))

    return result


class Worker(ScanWorker):
    def run(self):
        self.log(f"Starting IP lookup: {self.target}", "INFO")
        self.progress.emit(20)
        result = run_scan(self.target, **self.kwargs)
        self.progress.emit(100)
        level  = "SUCCESS" if result["status"] == "success" else "ERROR"
        self.log(f"IP lookup finished ({result['status']})", level)
        self.result_ready.emit(result)
