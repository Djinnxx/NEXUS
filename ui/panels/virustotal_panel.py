from .base_panel import BasePanel
from modules.virustotal_module import Worker


class VirusTotalPanel(BasePanel):
    module_name = "VirusTotal"
    description = "Scan IP, domain, URL or file hash (VT API key required)"
    module_key  = "virustotal"
    Worker      = Worker
