import requests
from .base import ScanWorker

def run_scan(target: str, **kwargs) -> dict:
    result = ScanWorker.empty_result(target)
    found  = []

    # -- psbdmp.ws: indexes Pastebin public pastes --
    try:
        r = requests.get(
            f"https://psbdmp.ws/api/v3/search/{target}",
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            for item in data.get("data", [])[:20]:
                found.append({
                    "source":  "Pastebin",
                    "id":      item.get("id", ""),
                    "url":     f"https://pastebin.com/{item.get('id','')}",
                    "time":    item.get("time", ""),
                    "tags":    item.get("tags", ""),
                    "size":    item.get("length", 0),
                })
    except Exception:
        pass

    # -- GitHub Gist (public gists mentioning target) --
    try:
        r2 = requests.get(
            "https://api.github.com/search/code",
            params={"q": f'"{target}" filename:.txt', "per_page": 5},
            timeout=10,
        )
        if r2.status_code == 200:
            for item in r2.json().get("items", []):
                if "gist" in item.get("html_url", ""):
                    found.append({
                        "source": "GitHub Gist",
                        "id":     item.get("sha", ""),
                        "url":    item.get("html_url", ""),
                        "time":   "",
                        "tags":   "",
                        "size":   0,
                    })
    except Exception:
        pass

    result["data"]["pastes"] = found
    result["data"]["total"]  = len(found)

    for p in found:
        result["findings"].append(
            f"[PASTE] {p['source']} – {p['url']} ({p['time'][:10] if p['time'] else 'N/A'})"
        )

    if found:
        result["risk_score"] = min(len(found) * 12, 100)
        result["findings"].insert(0, f"[!] {len(found)} paste mentions found for target")
    else:
        result["findings"].append("No paste site mentions found.")

    return result


class Worker(ScanWorker):
    def run(self):
        self.log(f"Paste Monitor: {self.target}", "INFO")
        self.progress.emit(20)
        result = run_scan(self.target, **self.kwargs)
        self.progress.emit(100)
        self.log(f"Paste scan done – {result['data'].get('total', 0)} pastes found",
                 "WARNING" if result["data"].get("total", 0) > 0 else "SUCCESS")
        self.result_ready.emit(result)
