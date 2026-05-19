import whois
from datetime import datetime
from .base import ScanWorker

def run_scan(target: str, **kwargs) -> dict:
    result = ScanWorker.empty_result(target)
    try:
        w = whois.whois(target)
        if not w:
            raise ValueError("No WHOIS data returned")

        def fmt_date(d):
            if isinstance(d, list):
                d = d[0]
            if isinstance(d, datetime):
                return d.strftime("%Y-%m-%d")
            return str(d) if d else "N/A"

        def clean(v):
            if isinstance(v, list):
                return ", ".join(str(x) for x in v if x)
            return str(v) if v else "N/A"

        data = {
            "domain":       clean(w.domain_name),
            "registrar":    clean(w.registrar),
            "created":      fmt_date(w.creation_date),
            "expires":      fmt_date(w.expiration_date),
            "updated":      fmt_date(w.updated_date),
            "status":       clean(w.status),
            "nameservers":  clean(w.name_servers),
            "emails":       clean(w.emails),
            "org":          clean(w.org),
            "country":      clean(w.country),
            "registrant":   clean(w.registrant_postal_code),
        }
        result["data"]["whois"] = data

        result["findings"].append(f"Registrar: {data['registrar']}")
        result["findings"].append(f"Created: {data['created']} | Expires: {data['expires']}")
        if data["org"] != "N/A":
            result["findings"].append(f"Organization: {data['org']}")
        if data["emails"] != "N/A":
            result["findings"].append(f"Contact email(s): {data['emails']}")

        # Risk: recently created domain = suspicious
        try:
            created = datetime.strptime(data["created"], "%Y-%m-%d")
            age_days = (datetime.now() - created).days
            if age_days < 30:
                result["risk_score"] = 70
                result["findings"].append("[HIGH RISK] Domain created less than 30 days ago")
            elif age_days < 180:
                result["risk_score"] = 30
                result["findings"].append("[MEDIUM RISK] Domain is less than 6 months old")
        except Exception:
            pass

    except Exception as e:
        result = ScanWorker.error_result(target, str(e))
    return result


class Worker(ScanWorker):
    def run(self):
        self.log(f"WHOIS lookup: {self.target}", "INFO")
        self.progress.emit(30)
        result = run_scan(self.target, **self.kwargs)
        self.progress.emit(100)
        self.log(f"WHOIS finished ({result['status']})",
                 "SUCCESS" if result["status"] == "success" else "ERROR")
        self.result_ready.emit(result)
