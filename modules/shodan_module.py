import requests
from .base import ScanWorker
from config.settings import get_api_key

def run_scan(target: str, **kwargs) -> dict:
    result  = ScanWorker.empty_result(target)
    api_key = get_api_key("shodan")

    if not api_key:
        result["status"] = "no_key"
        result["error"]  = "Shodan API key not configured. Get a free key at account.shodan.io"
        return result

    try:
        # Host lookup
        r = requests.get(
            f"https://api.shodan.io/shodan/host/{target}",
            params={"key": api_key},
            timeout=10,
        )
        if r.status_code == 404:
            result["findings"].append("Host not found in Shodan index.")
            return result
        if r.status_code != 200:
            raise ValueError(f"Shodan API error: {r.status_code}")

        data = r.json()
        result["data"]["shodan"] = {
            "ip":           data.get("ip_str"),
            "org":          data.get("org", "N/A"),
            "isp":          data.get("isp", "N/A"),
            "os":           data.get("os", "N/A"),
            "country":      data.get("country_name", "N/A"),
            "city":         data.get("city", "N/A"),
            "ports":        data.get("ports", []),
            "hostnames":    data.get("hostnames", []),
            "tags":         data.get("tags", []),
            "last_update":  data.get("last_update", "N/A"),
        }

        ports   = data.get("ports", [])
        banners = data.get("data", [])

        result["findings"].append(f"Open ports: {', '.join(str(p) for p in ports)}")
        result["findings"].append(f"Organization: {data.get('org', 'N/A')}")
        result["findings"].append(f"Last seen: {data.get('last_update', 'N/A')[:10]}")

        # Service details
        services = []
        for b in banners:
            svc = {
                "port":      b.get("port"),
                "transport": b.get("transport", "tcp"),
                "product":   b.get("product", ""),
                "version":   b.get("version", ""),
                "cpe":       b.get("cpe", []),
                "banner":    b.get("data", "")[:200],
            }
            services.append(svc)
            if svc["product"]:
                result["findings"].append(
                    f"Port {svc['port']}/{svc['transport']}: {svc['product']} {svc['version']}"
                )

        result["data"]["services"] = services

        # Vulns
        vulns = data.get("vulns", {})
        if vulns:
            result["data"]["vulns"] = list(vulns.keys())
            result["risk_score"]    = min(len(vulns) * 20, 100)
            for cve in list(vulns.keys())[:10]:
                result["findings"].append(f"[CVE] {cve}")

    except Exception as e:
        result = ScanWorker.error_result(target, str(e))
    return result


class Worker(ScanWorker):
    def run(self):
        self.log(f"Shodan lookup: {self.target}", "INFO")
        self.progress.emit(20)
        result = run_scan(self.target, **self.kwargs)
        self.progress.emit(100)
        self.log(f"Shodan done ({result['status']})",
                 "SUCCESS" if result["status"] == "success" else "WARNING")
        self.result_ready.emit(result)
