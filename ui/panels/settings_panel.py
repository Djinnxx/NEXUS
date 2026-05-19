from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from config.settings import load_config, save_config


class SettingsPanel(QWidget):
    log_signal     = pyqtSignal(str, str)
    results_signal = pyqtSignal(str, dict)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._build_ui()
        self._load()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(20, 16, 20, 20)
        root.setSpacing(16)

        title = QLabel("Settings")
        title.setObjectName("mod_title")
        root.addWidget(title)

        # ── API Keys section
        root.addWidget(self._section_label("API Keys"))

        api_keys = [
            ("hibp",        "HaveIBeenPwned",    "https://haveibeenpwned.com/API/Key",        False),
            ("shodan",      "Shodan",             "https://account.shodan.io",                  False),
            ("virustotal",  "VirusTotal",         "https://www.virustotal.com/gui/my-apikey",   False),
            ("github",      "GitHub Token",       "https://github.com/settings/tokens",         False),
            ("ipinfo",      "IPInfo (optional)",  "https://ipinfo.io/account",                  False),
        ]
        self._key_inputs: dict[str, QLineEdit] = {}
        for key, label, hint, _ in api_keys:
            row = self._make_key_row(key, label, hint)
            root.addLayout(row)

        # ── Tor section
        root.addWidget(self._section_label("Tor Proxy (Dark Web module)"))

        tor_row = QHBoxLayout()
        self.tor_enable = QCheckBox("Enable Tor proxy")
        self.tor_enable.setStyleSheet("color:#eaeaea; font-size:12px;")
        tor_row.addWidget(self.tor_enable)
        tor_row.addStretch()
        root.addLayout(tor_row)

        host_row = QHBoxLayout()
        host_row.addWidget(QLabel("Host:"))
        self.tor_host = QLineEdit("127.0.0.1")
        self.tor_host.setMaximumWidth(180)
        host_row.addWidget(self.tor_host)
        host_row.addWidget(QLabel("Port:"))
        self.tor_port = QLineEdit("9050")
        self.tor_port.setMaximumWidth(80)
        host_row.addWidget(self.tor_port)
        host_row.addStretch()
        root.addLayout(host_row)

        # ── Scan section
        root.addWidget(self._section_label("Scan Settings"))

        timeout_row = QHBoxLayout()
        timeout_row.addWidget(QLabel("Request timeout (seconds):"))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(3, 60)
        self.timeout_spin.setValue(10)
        self.timeout_spin.setMaximumWidth(80)
        self.timeout_spin.setStyleSheet("background:#0d1117; color:#eaeaea; border:1px solid #0f3460; padding:4px;")
        timeout_row.addWidget(self.timeout_spin)
        timeout_row.addStretch()
        root.addLayout(timeout_row)

        threads_row = QHBoxLayout()
        threads_row.addWidget(QLabel("Max concurrent threads:"))
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 20)
        self.threads_spin.setValue(5)
        self.threads_spin.setMaximumWidth(80)
        self.threads_spin.setStyleSheet("background:#0d1117; color:#eaeaea; border:1px solid #0f3460; padding:4px;")
        threads_row.addWidget(self.threads_spin)
        threads_row.addStretch()
        root.addLayout(threads_row)

        # ── Buttons
        btn_row = QHBoxLayout()
        save_btn = QPushButton("💾  SAVE SETTINGS")
        save_btn.setObjectName("run_btn")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        test_btn = QPushButton("Test Tor Connection")
        test_btn.setObjectName("clear_btn")
        test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_btn.clicked.connect(self._test_tor)
        btn_row.addWidget(test_btn)
        btn_row.addStretch()
        root.addLayout(btn_row)

        self.save_status = QLabel("")
        self.save_status.setStyleSheet("color:#00dd88; font-size:11px; font-family:Consolas;")
        root.addWidget(self.save_status)

        root.addStretch()
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------ helpers
    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "color:#e94560; font-size:12px; font-weight:bold; letter-spacing:1px;"
            "border-bottom:1px solid #0f3460; padding-bottom:4px;"
        )
        return lbl

    def _make_key_row(self, key: str, label: str, hint: str) -> QHBoxLayout:
        row = QHBoxLayout()
        lbl = QLabel(f"{label}:")
        lbl.setFixedWidth(160)
        lbl.setStyleSheet("color:#8899aa; font-size:12px;")
        row.addWidget(lbl)

        inp = QLineEdit()
        inp.setPlaceholderText(f"Paste {label} key here …")
        inp.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_inputs[key] = inp
        row.addWidget(inp)

        show_btn = QPushButton("👁")
        show_btn.setFixedWidth(32)
        show_btn.setStyleSheet("background:transparent; color:#556677; border:none; font-size:14px;")
        show_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        show_btn.setCheckable(True)
        show_btn.toggled.connect(
            lambda checked, i=inp: i.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        row.addWidget(show_btn)

        link = QLabel(f'<a href="{hint}" style="color:#0099cc;">Get key</a>')
        link.setOpenExternalLinks(True)
        link.setFixedWidth(60)
        row.addWidget(link)
        return row

    # ------------------------------------------------------------------ load/save
    def _load(self):
        cfg = load_config()
        for key, inp in self._key_inputs.items():
            inp.setText(cfg.get("api_keys", {}).get(key, ""))
        tor = cfg.get("tor", {})
        self.tor_enable.setChecked(tor.get("enabled", False))
        self.tor_host.setText(tor.get("host", "127.0.0.1"))
        self.tor_port.setText(str(tor.get("port", 9050)))
        scan = cfg.get("scan", {})
        self.timeout_spin.setValue(scan.get("timeout", 10))
        self.threads_spin.setValue(scan.get("threads", 5))

    def _save(self):
        cfg = load_config()
        for key, inp in self._key_inputs.items():
            cfg.setdefault("api_keys", {})[key] = inp.text().strip()
        cfg["tor"] = {
            "enabled": self.tor_enable.isChecked(),
            "host":    self.tor_host.text().strip(),
            "port":    int(self.tor_port.text().strip() or 9050),
        }
        cfg["scan"] = {
            "timeout": self.timeout_spin.value(),
            "threads": self.threads_spin.value(),
        }
        if save_config(cfg):
            self.save_status.setText("✓  Settings saved.")
            self.log_signal.emit("Settings saved to config.json", "SUCCESS")
        else:
            self.save_status.setText("⚠  Could not save settings.")
            self.save_status.setStyleSheet("color:#e94560; font-size:11px;")

    def _test_tor(self):
        import threading, requests
        host = self.tor_host.text().strip()
        port = int(self.tor_port.text().strip() or 9050)

        def _check():
            try:
                r = requests.get(
                    "https://check.torproject.org/api/ip",
                    proxies={"https": f"socks5h://{host}:{port}"},
                    timeout=12,
                )
                is_tor = r.json().get("IsTor", False)
                msg = "✓  Tor is running and connected!" if is_tor else "⚠  Connected but not via Tor exit node."
                level = "SUCCESS" if is_tor else "WARNING"
            except Exception as e:
                msg   = f"✗  Tor not reachable: {e}"
                level = "ERROR"
            self.log_signal.emit(msg, level)
            QMetaObject.invokeMethod(
                self.save_status, "setText",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, msg)
            )

        threading.Thread(target=_check, daemon=True).start()
        self.save_status.setText("Testing Tor connection…")

    def set_target(self, _): pass
    def clear(self): pass
