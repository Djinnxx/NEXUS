from .base_panel import BasePanel
from modules.dns_enum import Worker


class DNSPanel(BasePanel):
    module_name = "DNS Enumeration"
    description = "DNS records (A, MX, TXT, NS, SOA) and subdomain discovery"
    module_key  = "dns"
    Worker      = Worker
