import requests
from .base import ScanWorker
from config.settings import get_api_key

HIBP_URL = "https://haveibeenpwned.com/api/v3"

def run_scan(target: str, **kwargs) -> dict:
    result  = ScanWorker.empty_result(target)
    api_key = get_api_key("hibp")

    if not api_key:
        result["status"] = "no_key"
        result["error"]  = "HIBP API key not configured. Get a free key at haveibeenpwned.com/API/Key"
        return result

    headers = {
        "hibp-api-key": api_key,
        "User-Agent":   "NEXUS-OSINT/1.0",
    }

    try:
        # Check breaches
        r = requests.get(
            f"{HIBP_URL}/breachedaccount/{target}",
            headers=headers,
            params={"truncateResponse": "false"},
            timeout=10,
        )

        if r.status_code == 200:
            breaches = r.json()
            result["data"]["breaches"]      = breaches
            result["data"]["breach_count"]  = len(breaches)

            for b in breaches:
                result["findings"].append(
                    f"BREACH: {b.get('Name')} ({b.get('BreachDate','?')}) – "
                    f"Data: {', '.join(b.get('DataClasses', [])[:5])}"
                )

            score = min(len(breaches) * 15, 100)
            result["risk_score"] = score

        elif r.status_code == 404:
            result["findings"].append("No breaches found for this account.")
        else:
            result["status"] = "error"
            result["error"]  = f"HIBP API returned {r.status_code}"

        # Check pastes
        r2 = requests.get(
            f"{HIBP_URL}/pasteaccount/{target}",
            headers=headers,
            timeout=10,
        )
        if r2.status_code == 200:
            pastes = r2.json()
            result["data"]["pastes"]      = pastes
            result["data"]["paste_count"] = len(pastes)
            for p in pastes:
                result["findings"].append(
                    f"PASTE: {p.get('Source','?')} – {p.get('Title','untitled')} ({p.get('Date','?')[:10]})"
                )

    except Exception as e:
        result = ScanWorker.error_result(target, str(e))

    return result


class Worker(ScanWorker):
    def run(self):
        self.log(f"Breach check: {self.target}", "INFO")
        self.progress.emit(20)
        result = run_scan(self.target, **self.kwargs)
        self.progress.emit(100)
        level = "SUCCESS" if result["status"] == "success" else "WARNING"
        self.log(f"Breach check done – {result['data'].get('breach_count', 0)} breaches found", level)
        self.result_ready.emit(result)
