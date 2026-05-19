from .base_panel import BasePanel
from modules.ip_lookup import Worker


class IPPanel(BasePanel):
    module_name = "IP Lookup"
    description = "Geolocation, ASN, ISP and hostname for any IP address"
    module_key  = "ip"
    Worker      = Worker
