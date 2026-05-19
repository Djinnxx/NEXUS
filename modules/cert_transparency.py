import requests
from .base import ScanWorker

def run_scan(target: str, **kwargs) -> dict:
    result = ScanWorker.empty_result(target)
    try:
        r    = requests.get(f"https://crt.sh/?q={target}&output=json", timeout=15)
        certs = r.json()

        seen    = set()
        entries = []
        for c in certs:
            name = c.get("name_value", "").lower()
            for n in name.split("\n"):
                n = n.strip()
                if n and n not in seen:
                    seen.add(n)
                    entries.append({
                        "domain":    n,
                        "issuer":    c.get("issuer_name", "N/A"),
                        "logged_at": c.get("entry_timestamp", "N/A")[:10],
                        "not_before": c.get("not_before", "N/A")[:10],
                        "not_after":  c.get("not_after",  "N/A")[:10],
                    })

        result["data"]["certificates"] = entries
        result["data"]["total"]        = len(entries)

        unique_domains = sorted(set(e["domain"] for e in entries))
        result["data"]["unique_domains"] = unique_domains

        for d in unique_domains[:20]:
            result["findings"].append(f"Domain in CT logs: {d}")

        if len(unique_domains) > 20:
            result["findings"].append(f"...and {len(unique_domains)-20} more domains")

        result["findings"].append(
            f"Total certificate entries: {len(entries)}"
        )

        # Wildcard or suspicious patterns
        wildcards = [d for d in unique_domains if d.startswith("*")]
        if wildcards:
            result["findings"].append(f"Wildcard certs found: {', '.join(wildcards[:5])}")

    except Exception as e:
        result = ScanWorker.error_result(target, str(e))
    return result


class Worker(ScanWorker):
    def run(self):
        self.log(f"Certificate Transparency search: {self.target}", "INFO")
        self.progress.emit(20)
        result = run_scan(self.target, **self.kwargs)
        self.progress.emit(100)
        self.log(f"CT logs done – {result['data'].get('total', 0)} entries found",
                 "SUCCESS" if result["status"] == "success" else "ERROR")
        self.result_ready.emit(result)
