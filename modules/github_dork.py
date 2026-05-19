import requests
from .base import ScanWorker
from config.settings import get_api_key

DORK_QUERIES = [
    '"{target}" password',
    '"{target}" secret',
    '"{target}" api_key',
    '"{target}" token',
    '"{target}" credentials',
    '"{target}" .env',
    '"{target}" config',
    'site:{target}',
]

def run_scan(target: str, **kwargs) -> dict:
    result  = ScanWorker.empty_result(target)
    api_key = get_api_key("github")

    if not api_key:
        result["status"] = "no_key"
        result["error"]  = "GitHub API token not configured. Get a free token at github.com/settings/tokens"
        return result

    headers = {
        "Authorization": f"token {api_key}",
        "Accept":        "application/vnd.github.v3+json",
    }
    all_items = []

    for query_tmpl in DORK_QUERIES:
        query = query_tmpl.format(target=target)
        try:
            r = requests.get(
                "https://api.github.com/search/code",
                headers=headers,
                params={"q": query, "per_page": 5},
                timeout=10,
            )
            if r.status_code == 200:
                items = r.json().get("items", [])
                for item in items:
                    entry = {
                        "query":      query,
                        "repo":       item.get("repository", {}).get("full_name", "N/A"),
                        "file":       item.get("name", "N/A"),
                        "path":       item.get("path", "N/A"),
                        "url":        item.get("html_url", ""),
                        "repo_url":   item.get("repository", {}).get("html_url", ""),
                    }
                    all_items.append(entry)
                    result["findings"].append(
                        f"MATCH: {entry['repo']}/{entry['path']} (query: {query[:40]})"
                    )
            elif r.status_code == 403:
                result["findings"].append("GitHub rate limit reached – try again later")
                break
        except Exception:
            continue

    result["data"]["matches"] = all_items
    result["data"]["total"]   = len(all_items)

    if all_items:
        result["risk_score"] = min(len(all_items) * 10, 100)
        result["findings"].insert(0, f"[HIGH] {len(all_items)} potential secret/credential leaks found on GitHub!")
    else:
        result["findings"].append("No leaks found on GitHub.")

    return result


class Worker(ScanWorker):
    def run(self):
        self.log(f"GitHub dorking: {self.target}", "INFO")
        self.progress.emit(10)
        result = run_scan(self.target, **self.kwargs)
        self.progress.emit(100)
        self.log(f"GitHub dork done – {result['data'].get('total', 0)} matches",
                 "SUCCESS" if result["status"] == "success" else "WARNING")
        self.result_ready.emit(result)
