from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from datetime import datetime

from ui.styles import NEXUS_STYLE
from ui.panels.dashboard_panel   import DashboardPanel
from ui.panels.ip_panel          import IPPanel
from ui.panels.whois_panel       import WHOISPanel
from ui.panels.dns_panel         import DNSPanel
from ui.panels.cert_panel        import CertPanel
from ui.panels.wayback_panel     import WaybackPanel
from ui.panels.breach_panel      import BreachPanel
from ui.panels.username_panel    import UsernamePanel
from ui.panels.shodan_panel      import ShodanPanel
from ui.panels.virustotal_panel  import VirusTotalPanel
from ui.panels.github_panel      import GithubPanel
from ui.panels.exif_panel        import EXIFPanel
from ui.panels.darkweb_panel     import DarkWebPanel
from ui.panels.paste_panel       import PastePanel
from ui.panels.ioc_panel         import IOCPanel
from ui.panels.relationship_panel import RelationshipPanel
from ui.panels.report_panel      import ReportPanel
from ui.panels.settings_panel    import SettingsPanel

MODULES = [
    ("Dashboard",        "🏠", DashboardPanel),
    ("IP Lookup",        "⬡", IPPanel),
    ("WHOIS",            "📋", WHOISPanel),
    ("DNS Enumeration",  "🔍", DNSPanel),
    ("Cert Transparency","🔐", CertPanel),
    ("Wayback Machine",  "📅", WaybackPanel),
    ("Breach Check",     "💥", BreachPanel),
    ("Username Search",  "👤", UsernamePanel),
    ("Shodan",           "📡", ShodanPanel),
    ("VirusTotal",       "🦠", VirusTotalPanel),
    ("GitHub Dorking",   "💻", GithubPanel),
    ("EXIF Analysis",    "🖼", EXIFPanel),
    ("Dark Web",         "🕶", DarkWebPanel),
    ("Paste Monitor",    "📝", PastePanel),
    ("IOC Check",        "⚠", IOCPanel),
    ("Relationship Map", "🕸", RelationshipPanel),
    ("Report",           "📊", ReportPanel),
    ("Settings",         "⚙", SettingsPanel),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.all_results: dict = {}
        self._setup_ui()
        self.add_log("NEXUS OSINT v1.0 – Ready. Enter target and press SCAN.", "INFO")

    # ------------------------------------------------------------------ build
    def _setup_ui(self):
        self.setWindowTitle("NEXUS OSINT v1.0")
        self.setMinimumSize(1280, 800)
        self.resize(1440, 860)
        self.setStyleSheet(NEXUS_STYLE)

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        right = QWidget()
        rl    = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)
        rl.addWidget(self._build_header())

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self._build_stack())
        splitter.addWidget(self._build_log())
        splitter.setSizes([680, 150])
        rl.addWidget(splitter, 1)

        root.addWidget(right, 1)

        # Activate dashboard
        self.nav_buttons[0].setChecked(True)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(0)

        logo = QLabel("NEXUS OSINT")
        logo.setObjectName("logo")
        sl.addWidget(logo)

        ver = QLabel("v1.0  ·  OSINT Framework")
        ver.setObjectName("version")
        sl.addWidget(ver)

        self.nav_buttons: list[QPushButton] = []
        for i, (name, icon, _) in enumerate(MODULES):
            btn = QPushButton(f"  {name}")
            btn.setObjectName("nav_btn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, idx=i: self._switch_to(idx))
            sl.addWidget(btn)
            self.nav_buttons.append(btn)

        sl.addStretch()

        self.status_indicator = QLabel("● READY")
        self.status_indicator.setObjectName("status_indicator")
        sl.addWidget(self.status_indicator)
        return sidebar

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("header")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 0, 16, 0)
        hl.setSpacing(10)

        brand = QLabel("NEXUS")
        brand.setObjectName("app_title")
        hl.addWidget(brand)
        hl.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setObjectName("search_input")
        self.search_input.setPlaceholderText(
            "Enter target: IP / domain / email / username / file path …"
        )
        self.search_input.returnPressed.connect(self._scan_current)
        hl.addWidget(self.search_input)

        scan_btn = QPushButton("◉  SCAN")
        scan_btn.setObjectName("scan_btn")
        scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        scan_btn.clicked.connect(self._scan_current)
        hl.addWidget(scan_btn)
        self.scan_btn = scan_btn

        all_btn = QPushButton("SCAN ALL")
        all_btn.setObjectName("header_btn")
        all_btn.setToolTip("Run all applicable modules")
        all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        all_btn.clicked.connect(self._scan_all)
        hl.addWidget(all_btn)

        clear_btn = QPushButton("⬚  CLEAR")
        clear_btn.setObjectName("header_btn")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_all)
        hl.addWidget(clear_btn)
        return header

    def _build_stack(self) -> QStackedWidget:
        self.stack  = QStackedWidget()
        self.panels: dict[str, QWidget] = {}
        for name, _, PanelClass in MODULES:
            panel = PanelClass(self)
            if hasattr(panel, "log_signal"):
                panel.log_signal.connect(self.add_log)
            if hasattr(panel, "results_signal"):
                panel.results_signal.connect(self._on_module_result)
            self.panels[name] = panel
            self.stack.addWidget(panel)
        return self.stack

    def _build_log(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("log_frame")
        ll = QVBoxLayout(frame)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(0)

        label = QLabel("  ▸ TERMINAL LOG")
        label.setObjectName("log_label")
        ll.addWidget(label)

        self.log_view = QTextEdit()
        self.log_view.setObjectName("log_view")
        self.log_view.setReadOnly(True)
        ll.addWidget(self.log_view)
        return frame

    # ------------------------------------------------------------------ slots
    def _switch_to(self, index: int):
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        self.stack.setCurrentIndex(index)
        target = self.search_input.text().strip()
        if target:
            p = self.stack.currentWidget()
            if hasattr(p, "set_target"):
                p.set_target(target)

    def _scan_current(self):
        target = self.search_input.text().strip()
        if not target:
            return
        p = self.stack.currentWidget()
        if hasattr(p, "run_scan"):
            p.run_scan(target)

    def _scan_all(self):
        target = self.search_input.text().strip()
        if not target:
            QMessageBox.warning(self, "No Target", "Please enter a target first.")
            return
        skip = {"Dashboard", "Report", "Settings", "Relationship Map", "EXIF Analysis"}
        self.add_log(f"Full scan initiated: {target}", "INFO")
        for name, panel in self.panels.items():
            if name not in skip and hasattr(panel, "run_scan"):
                QTimer.singleShot(0, lambda p=panel, t=target: p.run_scan(t))

    def _clear_all(self):
        self.log_view.clear()
        self.all_results.clear()
        for p in self.panels.values():
            if hasattr(p, "clear"):
                p.clear()
        self.add_log("All results cleared.", "INFO")

    def _on_module_result(self, module_key: str, data: dict):
        self.all_results[module_key] = data
        rel = self.panels.get("Relationship Map")
        if rel and hasattr(rel, "update_results"):
            rel.update_results(self.all_results)
        dash = self.panels.get("Dashboard")
        if dash and hasattr(dash, "update_summary"):
            dash.update_summary(self.all_results)

    # ------------------------------------------------------------------ log
    def add_log(self, message: str, level: str = "INFO"):
        ts   = datetime.now().strftime("%H:%M:%S")
        col  = {"INFO": "#8899aa", "SUCCESS": "#00dd88",
                "WARNING": "#ffcc44", "ERROR": "#e94560"}.get(level, "#8899aa")
        self.log_view.append(
            f'<span style="color:#444;">[{ts}]</span> '
            f'<span style="color:{col};">[{level:7s}]</span> '
            f'<span style="color:#ccddee;">{message}</span>'
        )
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())
        self.status_indicator.setText(f"● {message[:55]}")
