from .base_panel import BasePanel
from modules.whois_module import Worker


class WHOISPanel(BasePanel):
    module_name = "WHOIS"
    description = "Domain registration, registrar, dates and contact details"
    module_key  = "whois"
    Worker      = Worker
