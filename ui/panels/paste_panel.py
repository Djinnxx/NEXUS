from .base_panel import BasePanel
from modules.paste_monitor import Worker


class PastePanel(BasePanel):
    module_name = "Paste Monitor"
    description = "Search Pastebin and public paste sites for target mentions"
    module_key  = "paste"
    Worker      = Worker
