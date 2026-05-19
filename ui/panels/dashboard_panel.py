from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


class DashboardPanel(QWidget):
    log_signal     = pyqtSignal(str, str)
    results_signal = pyqtSignal(str, dict)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 12)
        root.setSpacing(12)

        title = QLabel("NEXUS OSINT — Dashboard")
        title.setObjectName("mod_title")
        root.addWidget(title)

        sub = QLabel("Overview of all collected intelligence for the current target.")
        sub.setObjectName("mod_desc")
        root.addWidget(sub)

        # ── Risk score widget
        self.risk_frame = QFrame()
        self.risk_frame.setStyleSheet(
            "background:#0d1117; border:1px solid #0f3460; border-radius:6px; padding:12px;"
        )
        rf = QHBoxLayout(self.risk_frame)

        self.risk_number = QLabel("—")
        self.risk_number.setStyleSheet(
            "color:#e94560; font-size:52px; font-weight:bold; font-family:Consolas;"
        )
        rf.addWidget(self.risk_number)

        risk_info = QVBoxLayout()
        risk_info.setSpacing(2)
        self.risk_badge = QLabel("NO DATA")
        self.risk_badge.setStyleSheet(
            "color:#556677; font-size:18px; font-weight:bold;"
        )
        risk_info.addWidget(self.risk_badge)

        self.risk_target = QLabel("Target: —")
        self.risk_target.setStyleSheet("color:#8899aa; font-size:12px; font-family:Consolas;")
        risk_info.addWidget(self.risk_target)

        self.modules_ran = QLabel("Modules run: 0")
        self.modules_ran.setStyleSheet("color:#8899aa; font-size:12px; font-family:Consolas;")
        risk_info.addWidget(self.modules_ran)

        rf.addLayout(risk_info)
        rf.addStretch()
        root.addWidget(self.risk_frame)

        # ── Module cards grid
        self.cards_widget = QWidget()
        self.cards_grid   = QGridLayout(self.cards_widget)
        self.cards_grid.setSpacing(8)
        root.addWidget(self.cards_widget)

        self._module_cards: dict[str, dict] = {}
        module_keys = [
            ("ip",       "IP Lookup"),  ("whois",    "WHOIS"),
            ("dns",      "DNS Enum"),   ("cert",     "Certs"),
            ("wayback",  "Wayback"),    ("breach",   "Breach"),
            ("username", "Username"),   ("shodan",   "Shodan"),
            ("virustotal","VirusTotal"),("github",   "GitHub"),
            ("darkweb",  "Dark Web"),   ("paste",    "Paste"),
            ("ioc",      "IOC"),
        ]
        for idx, (key, label) in enumerate(module_keys):
            card = self._make_card(key, label)
            self._module_cards[key] = card
            row, col = divmod(idx, 4)
            self.cards_grid.addWidget(card["frame"], row, col)

        root.addStretch()

    def _make_card(self, key, label) -> dict:
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame { background:#0d1117; border:1px solid #0f3460;"
            "border-radius:6px; }"
        )
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(10, 8, 10, 8)
        fl.setSpacing(2)

        name_lbl = QLabel(label)
        name_lbl.setStyleSheet("color:#8899aa; font-size:11px; letter-spacing:0.5px;")
        fl.addWidget(name_lbl)

        score_lbl = QLabel("—")
        score_lbl.setStyleSheet("color:#334455; font-size:22px; font-weight:bold; font-family:Consolas;")
        fl.addWidget(score_lbl)

        status_lbl = QLabel("pending")
        status_lbl.setStyleSheet("color:#334455; font-size:10px; font-family:Consolas;")
        fl.addWidget(status_lbl)

        return {"frame": frame, "score": score_lbl, "status": status_lbl}

    # ------------------------------------------------------------------ API
    def update_summary(self, all_results: dict):
        target = self.main_window.search_input.text().strip()
        self.risk_target.setText(f"Target: {target}")

        ran   = len(all_results)
        total = max(v.get("risk_score", 0) for v in all_results.values()) if all_results else 0
        self.modules_ran.setText(f"Modules run: {ran}")
        self.risk_number.setText(str(total))

        col  = ("#e94560" if total >= 75 else "#fdcb6e" if total >= 50
                else "#e17055" if total >= 25 else "#00dd88")
        label = ("CRITICAL" if total >= 75 else "HIGH" if total >= 50
                 else "MEDIUM" if total >= 25 else "LOW")
        self.risk_number.setStyleSheet(
            f"color:{col}; font-size:52px; font-weight:bold; font-family:Consolas;"
        )
        self.risk_badge.setText(label)
        self.risk_badge.setStyleSheet(f"color:{col}; font-size:18px; font-weight:bold;")

        for key, card in self._module_cards.items():
            res = all_results.get(key)
            if res:
                sc  = res.get("risk_score", 0)
                c   = ("#e94560" if sc >= 75 else "#fdcb6e" if sc >= 50
                       else "#00dd88" if sc < 25 else "#e17055")
                card["score"].setText(str(sc))
                card["score"].setStyleSheet(
                    f"color:{c}; font-size:22px; font-weight:bold; font-family:Consolas;"
                )
                st = res.get("status", "done")
                card["status"].setText(st)
                card["status"].setStyleSheet(f"color:{c}; font-size:10px; font-family:Consolas;")

    def set_target(self, target):
        self.risk_target.setText(f"Target: {target}")

    def clear(self):
        self.risk_number.setText("—")
        self.risk_badge.setText("NO DATA")
        for card in self._module_cards.values():
            card["score"].setText("—")
            card["status"].setText("pending")
