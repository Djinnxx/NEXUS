from .base_panel import BasePanel
from modules.wayback import Worker


class WaybackPanel(BasePanel):
    module_name = "Wayback Machine"
    description = "Historical URL snapshots and archived pages from archive.org"
    module_key  = "wayback"
    Worker      = Worker
