from .base_panel import BasePanel
from modules.shodan_module import Worker


class ShodanPanel(BasePanel):
    module_name = "Shodan"
    description = "Open ports, services, banners and CVEs (Shodan API key req.)"
    module_key  = "shodan"
    Worker      = Worker
