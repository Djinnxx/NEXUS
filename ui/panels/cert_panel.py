from .base_panel import BasePanel
from modules.cert_transparency import Worker


class CertPanel(BasePanel):
    module_name = "Cert Transparency"
    description = "Certificate Transparency logs via crt.sh – reveals subdomains"
    module_key  = "cert"
    Worker      = Worker
