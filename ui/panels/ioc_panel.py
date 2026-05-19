from .base_panel import BasePanel
from modules.ioc_check import Worker


class IOCPanel(BasePanel):
    module_name = "IOC Check"
    description = "Check IP/domain/hash/URL against abuse.ch threat intel feeds"
    module_key  = "ioc"
    Worker      = Worker
