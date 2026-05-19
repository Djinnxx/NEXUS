import requests
from .base import ScanWorker

def run_scan(target: str, **kwargs) -> dict:
    result = ScanWorker.empty_result(target)
    try:
        # Check if URL is archived
        avail  = requests.get(
            f"https://archive.org/wayback/available?url={target}", timeout=10
        ).json()
        snapshot = avail.get("archived_snapshots", {}).get("closest", {})

        result["data"]["latest_snapshot"] = snapshot
        if snapshot:
            result["findings"].append(f"Latest snapshot: {snapshot.get('timestamp','?')[:8]}")
            result["findings"].append(f"URL: {snapshot.get('url','')}")

        # Get last 50 captures
        cdx = requests.get(
            "https://web.archive.org/cdx/search/cdx",
            params={
                "url":      f"{target}/*",
                "output":   "json",
                "fl":       "timestamp,original,statuscode",
                "collapse": "urlkey",
                "limit":    "50",
            },
            timeout=15,
        )
        rows = cdx.json()
        if rows and len(rows) > 1:
            # rows[0] is header
            captures = [{"timestamp": r[0], "url": r[1], "status": r[2]}
                        for r in rows[1:]]
            result["data"]["captures"]       = captures
            result["data"]["capture_count"]  = len(captures)
            result["findings"].append(f"Found {len(captures)} archived URLs")

            # Find unique subpages
            pages = sorted(set(r["url"] for r in captures))
            result["data"]["unique_pages"] = pages[:50]

    except Exception as e:
        result = ScanWorker.error_result(target, str(e))
    return result


class Worker(ScanWorker):
    def run(self):
        self.log(f"Wayback Machine lookup: {self.target}", "INFO")
        self.progress.emit(20)
        result = run_scan(self.target, **self.kwargs)
        self.progress.emit(100)
        self.log(f"Wayback done – {result['data'].get('capture_count', 0)} captures",
                 "SUCCESS" if result["status"] == "success" else "ERROR")
        self.result_ready.emit(result)
