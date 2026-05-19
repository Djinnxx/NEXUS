from .base_panel import BasePanel
from modules.breach_check import Worker


class BreachPanel(BasePanel):
    module_name = "Breach Check"
    description = "Email breach lookup via HaveIBeenPwned (free API key required)"
    module_key  = "breach"
    Worker      = Worker
