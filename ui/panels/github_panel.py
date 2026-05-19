from .base_panel import BasePanel
from modules.github_dork import Worker


class GithubPanel(BasePanel):
    module_name = "GitHub Dorking"
    description = "Scan public repos for leaked credentials (GitHub token req.)"
    module_key  = "github"
    Worker      = Worker
