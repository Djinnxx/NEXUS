import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

DEFAULT_CONFIG = {
    "api_keys": {
        "hibp": "",
        "shodan": "",
        "virustotal": "",
        "github": "",
        "ipinfo": ""
    },
    "tor": {
        "enabled": False,
        "host": "127.0.0.1",
        "port": 9050
    },
    "scan": {
        "timeout": 10,
        "threads": 5
    }
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                # Merge with defaults to handle missing keys
                for section, values in DEFAULT_CONFIG.items():
                    if section not in data:
                        data[section] = values
                    elif isinstance(values, dict):
                        for k, v in values.items():
                            if k not in data[section]:
                                data[section][k] = v
                return data
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config: dict):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception:
        return False

def get_api_key(name: str) -> str:
    config = load_config()
    return config.get("api_keys", {}).get(name, "")

def get_tor_config() -> dict:
    return load_config().get("tor", DEFAULT_CONFIG["tor"])

def get_scan_config() -> dict:
    return load_config().get("scan", DEFAULT_CONFIG["scan"])
