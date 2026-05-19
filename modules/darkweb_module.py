"""
Dark Web Monitoring Module
--------------------------
Searches for mentions of the target in publicly indexed dark web sources
using Ahmia.fi (a legitimate research search engine that blocks illegal content).
Requires Tor to be installed and running for full functionality.

AUTHORIZED USE ONLY – for pentests and bug bounties with written permission.
"""

import requests
from bs4 import BeautifulSoup
from .base import ScanWorker

AHMIA_CLEARNET = "https://ahmia.fi/search/"
AHMIA_ONION    = "http://juhanurmihxlp77nkivv77mrnwhsramyl2prjpheou2cpvat6loofpqd.onion/search/"

def _check_tor(host="127.0.0.1", port=9050) -> bool:
    """Return True if Tor SOCKS5 proxy is reachable."""
    try:
        proxies = {
            "http":  f"socks5h://{host}:{port}",
            "https": f"socks5h://{host}:{port}",
        }
        r = requests.get(
            "https://check.torproject.org/api/ip",
            proxies=proxies,
            timeout=10,
        )
        return r.json().get("IsTor", False)
    except Exception:
        return False


def _search_ahmia(query: str, proxies=None, timeout=20) -> list:
    """Query Ahmia.fi and parse result snippets. Returns list of result dicts."""
    url     = AHMIA_ONION if proxies else AHMIA_CLEARNET
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/109.0"}
    try:
        r = requests.get(
            url,
            params={"q": query},
            headers=headers,
            proxies=proxies,
            timeout=timeout,
        )
        soup    = BeautifulSoup(r.text, "html.parser")
        results = []
        for item in soup.select("li.result")[:20]:
            title_el = item.select_one("h4")
            url_el   = item.select_one("p.onion-site")
            desc_el  = item.select_one("p.description")
            if title_el:
                results.append({
                    "title":   title_el.get_text(strip=True),
                    "onion":   url_el.get_text(strip=True)  if url_el  else "N/A",
                    "snippet": desc_el.get_text(strip=True) if desc_el else "",
                })
        return results
    except Exception:
        return []


def run_scan(target: str, tor_host="127.0.0.1", tor_port=9050, **kwargs) -> dict:
    result = ScanWorker.empty_result(target)

    # Check Tor
    tor_up = _check_tor(tor_host, tor_port)
    result["data"]["tor_active"] = tor_up

    if tor_up:
        result["findings"].append("✓ Tor is active – searching via onion network")
        proxies = {
            "http":  f"socks5h://{tor_host}:{tor_port}",
            "https": f"socks5h://{tor_host}:{tor_port}",
        }
    else:
        result["findings"].append("⚠ Tor not detected – using Ahmia clearnet index")
        proxies = None

    # Run queries
    queries = [target, f'"{target}" leak', f'"{target}" password', f'"{target}" database']
    all_results = []

    for q in queries:
        hits = _search_ahmia(q, proxies=proxies)
        for h in hits:
            h["query"] = q
            all_results.append(h)

    # De-duplicate by onion URL
    seen     = set()
    unique   = []
    for r_ in all_results:
        key = r_.get("onion", r_.get("title", ""))
        if key not in seen:
            seen.add(key)
            unique.append(r_)

    result["data"]["results"] = unique
    result["data"]["total"]   = len(unique)

    for r_ in unique[:15]:
        result["findings"].append(
            f"[DARK WEB] {r_['title'][:60]} | {r_['onion'][:40]}"
        )
        if r_.get("snippet"):
            result["findings"].append(f"   └ {r_['snippet'][:100]}")

    if unique:
        result["risk_score"] = min(len(unique) * 8, 100)
        result["findings"].insert(0, f"[!] {len(unique)} dark web mentions found for target")
    else:
        result["findings"].append("No dark web mentions found.")

    return result


class Worker(ScanWorker):
    def run(self):
        self.log(f"Dark web monitoring: {self.target}", "INFO")
        self.progress.emit(10)
        result = run_scan(self.target, **self.kwargs)
        self.progress.emit(100)
        total = result["data"].get("total", 0)
        self.log(
            f"Dark web scan done – {total} mentions found",
            "WARNING" if total > 0 else "SUCCESS",
        )
        self.result_ready.emit(result)
