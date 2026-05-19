from .base_panel import BasePanel
from modules.darkweb_module import Worker


class DarkWebPanel(BasePanel):
    module_name = "Dark Web"
    description = "Dark web exposure via Tor + Ahmia – start Tor first"
    module_key  = "darkweb"
    Worker      = Worker
