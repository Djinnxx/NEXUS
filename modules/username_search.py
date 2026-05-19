import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from .base import ScanWorker

PLATFORMS = {
    "GitHub":       ("https://github.com/{}",                  200, None),
    "GitLab":       ("https://gitlab.com/{}",                  200, None),
    "Twitter/X":    ("https://twitter.com/{}",                 200, "This account doesn"),
    "Instagram":    ("https://www.instagram.com/{}/",          200, "Sorry, this page"),
    "Reddit":       ("https://www.reddit.com/user/{}",         200, "page not found"),
    "TikTok":       ("https://www.tiktok.com/@{}",             200, "Couldn"),
    "YouTube":      ("https://www.youtube.com/@{}",            200, "doesn"),
    "Twitch":       ("https://www.twitch.tv/{}",               200, None),
    "Pinterest":    ("https://www.pinterest.com/{}/",          200, None),
    "Medium":       ("https://medium.com/@{}",                 200, "page not found"),
    "Dev.to":       ("https://dev.to/{}",                      200, None),
    "Keybase":      ("https://keybase.io/{}",                  200, "Not a Keybase user"),
    "Steam":        ("https://steamcommunity.com/id/{}",       200, "The specified profile"),
    "SoundCloud":   ("https://soundcloud.com/{}",              200, None),
    "HackerRank":   ("https://www.hackerrank.com/{}",          200, "404"),
    "LeetCode":     ("https://leetcode.com/{}",                200, "does not exist"),
    "Pastebin":     ("https://pastebin.com/u/{}",              200, "Not Found"),
    "Gravatar":     ("https://en.gravatar.com/{}",             200, "isn"),
    "Fiverr":       ("https://www.fiverr.com/{}",              200, None),
    "Replit":       ("https://replit.com/@{}",                 200, "doesn"),
    "Kaggle":       ("https://www.kaggle.com/{}",              200, None),
    "HackTheBox":   ("https://app.hackthebox.com/users/{}",    200, None),
    "TryHackMe":    ("https://tryhackme.com/p/{}",             200, "404"),
    "DockerHub":    ("https://hub.docker.com/u/{}",            200, None),
    "Snapchat":     ("https://www.snapchat.com/add/{}",        200, "Sorry"),
    "Tumblr":       ("https://{}.tumblr.com",                  200, "There"),
    "WordPress":    ("https://{}.wordpress.com",               200, "doesn"),
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

def check_platform(name, url_tmpl, ok_status, not_found_str, username):
    url = url_tmpl.format(username)
    try:
        r = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True)
        if r.status_code == ok_status:
            if not_found_str and not_found_str.lower() in r.text.lower():
                return name, False, url
            return name, True, url
        return name, False, url
    except Exception:
        return name, None, url   # None = error / timeout

def run_scan(target: str, **kwargs) -> dict:
    result   = ScanWorker.empty_result(target)
    found    = []
    notfound = []
    errors   = []

    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {
            ex.submit(check_platform, name, tmpl, ok, nf, target): name
            for name, (tmpl, ok, nf) in PLATFORMS.items()
        }
        for future in as_completed(futures):
            name, status, url = future.result()
            if status is True:
                found.append({"platform": name, "url": url})
            elif status is False:
                notfound.append(name)
            else:
                errors.append(name)

    result["data"]["found"]    = found
    result["data"]["notfound"] = notfound
    result["data"]["errors"]   = errors

    for f in found:
        result["findings"].append(f"FOUND: {f['platform']} – {f['url']}")

    result["findings"].append(f"Checked {len(PLATFORMS)} platforms – {len(found)} hits")
    result["risk_score"] = min(len(found) * 5, 60)
    return result


class Worker(ScanWorker):
    def run(self):
        self.log(f"Username search: {self.target} across {len(PLATFORMS)} platforms", "INFO")
        self.progress.emit(5)
        result = run_scan(self.target, **self.kwargs)
        self.progress.emit(100)
        self.log(f"Username search done – {len(result['data'].get('found', []))} profiles found", "SUCCESS")
        self.result_ready.emit(result)
