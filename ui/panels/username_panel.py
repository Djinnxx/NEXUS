from .base_panel import BasePanel
from modules.username_search import Worker


class UsernamePanel(BasePanel):
    module_name = "Username Search"
    description = "Check username across 30+ social and developer platforms"
    module_key  = "username"
    Worker      = Worker
