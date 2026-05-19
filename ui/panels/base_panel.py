from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


class BasePanel(QWidget):
    log_signal     = pyqtSignal(str, str)   # message, level
    results_signal = pyqtSignal(str, dict)  # module_key, data

    # Override in subclasses
    module_name: str   = "Module"
    description: str   = ""
    module_key:  str   = "key"
    Worker             = None               # reference to modules.xxx.Worker

    def __init__(self, main_window):
        super().__init__()
        self.main_window     = main_window
        self.current_worker  = None
        self.last_data: dict = {}
        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 8)
        root.setSpacing(8)

        # ── Module header
        title = QLabel(self.module_name)
        title.setObjectName("mod_title")
        root.addWidget(title)

        if self.description:
            desc = QLabel(self.description)
            desc.setObjectName("mod_desc")
            root.addWidget(desc)

        # ── Control bar
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)

        self.target_label = QLabel("Target:  —")
        self.target_label.setObjectName("mod_target")
        ctrl.addWidget(self.target_label)
        ctrl.addStretch()

        self.run_btn = QPushButton("▶  RUN MODULE")
        self.run_btn.setObjectName("run_btn")
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.clicked.connect(
            lambda: self.run_scan(self.main_window.search_input.text().strip())
        )
        ctrl.addWidget(self.run_btn)

        self.clear_btn = QPushButton("CLEAR")
        self.clear_btn.setObjectName("clear_btn")
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear)
        ctrl.addWidget(self.clear_btn)

        root.addLayout(ctrl)

        # ── Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        root.addWidget(self.progress_bar)

        # ── Results tabs
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        # Summary tab
        self.findings_list = QListWidget()
        self.findings_list.setAlternatingRowColors(True)
        self.findings_list.setStyleSheet(
            "QListWidget { background:#0d1117; color:#c9d1d9;"
            "font-family:Consolas; font-size:12px;"
            "border:1px solid #0f3460; }"
            "QListWidget::item { padding:3px 8px; }"
            "QListWidget::item:alternate { background:#111622; }"
        )
        self.tabs.addTab(self.findings_list, "Summary")

        # Details tab
        self.detail_table = QTableWidget(0, 2)
        self.detail_table.setHorizontalHeaderLabels(["Key", "Value"])
        self.detail_table.horizontalHeader().setStretchLastSection(True)
        self.detail_table.verticalHeader().setVisible(False)
        self.detail_table.setAlternatingRowColors(True)
        self.tabs.addTab(self.detail_table, "Details")

        # Module-specific extra UI
        self.setup_module_ui()

        # ── Status row
        status_row = QHBoxLayout()
        self.risk_label = QLabel("Risk:  —")
        self.risk_label.setStyleSheet("color:#556677; font-size:11px; font-family:Consolas;")
        status_row.addWidget(self.risk_label)
        status_row.addStretch()
        self.status_bar = QLabel("Ready.")
        self.status_bar.setStyleSheet("color:#556677; font-size:11px; font-family:Consolas;")
        status_row.addWidget(self.status_bar)
        root.addLayout(status_row)

    def setup_module_ui(self):
        """Override to add module-specific widgets before the status row."""
        pass

    # ------------------------------------------------------------------ API
    def set_target(self, target: str):
        self.target_label.setText(f"Target:  {target}")

    def run_scan(self, target: str):
        if not target:
            return
        if not self.Worker:
            self.log_signal.emit(f"[{self.module_name}] No worker available.", "WARNING")
            return
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.abort()

        self.set_target(target)
        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_bar.setText("Scanning…")
        self.status_bar.setStyleSheet("color:#8899aa; font-size:11px;")
        self.findings_list.clear()
        self.detail_table.setRowCount(0)

        self.current_worker = self.Worker(target)
        self.current_worker.result_ready.connect(self._on_results)
        self.current_worker.log_message.connect(self.log_signal)
        self.current_worker.progress.connect(self.progress_bar.setValue)
        self.current_worker.start()

    def _on_results(self, data: dict):
        self.last_data = data
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        # Populate findings
        for f in data.get("findings", []):
            item = QListWidgetItem(f)
            if any(x in f for x in ("[CRITICAL]", "[!]", "BREACH:", "DARK WEB]")):
                item.setForeground(QColor("#e94560"))
            elif any(x in f for x in ("[HIGH", "[RISK]", "WARNING")):
                item.setForeground(QColor("#fdcb6e"))
            elif any(x in f for x in ("FOUND:", "✓", "Done")):
                item.setForeground(QColor("#00dd88"))
            self.findings_list.addItem(item)

        # Populate detail table
        self._fill_details(data.get("data", {}))

        # Risk label
        score = data.get("risk_score", 0)
        col   = ("#e94560" if score >= 75 else
                 "#fdcb6e" if score >= 50 else
                 "#e17055" if score >= 25 else "#00dd88")
        label = ("CRITICAL" if score >= 75 else
                 "HIGH"     if score >= 50 else
                 "MEDIUM"   if score >= 25 else "LOW")
        self.risk_label.setText(f"Risk Score:  {score}/100  [{label}]")
        self.risk_label.setStyleSheet(
            f"color:{col}; font-size:11px; font-family:Consolas; font-weight:bold;"
        )

        if data.get("error"):
            self.status_bar.setText(f"⚠  {data['error'][:90]}")
            self.status_bar.setStyleSheet("color:#e94560; font-size:11px;")
        elif data.get("status") == "no_key":
            self.status_bar.setText(f"⚙  {data.get('error','API key required')}")
            self.status_bar.setStyleSheet("color:#fdcb6e; font-size:11px;")
        else:
            n = len(data.get("findings", []))
            self.status_bar.setText(f"✓  Done.  {n} finding{'s' if n!=1 else ''}.")
            self.status_bar.setStyleSheet("color:#00dd88; font-size:11px;")

        self.results_signal.emit(self.module_key, data)
        self.populate_results(data)

    def _fill_details(self, d, _rows=None):
        rows  = []

        def flatten(obj, prefix=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    key = f"{prefix}.{k}" if prefix else k
                    if isinstance(v, (dict, list)):
                        flatten(v, key)
                    else:
                        rows.append((key, str(v)[:200]))
            elif isinstance(obj, list):
                for i, item in enumerate(obj[:30]):
                    flatten(item, f"{prefix}[{i}]")

        flatten(d)
        self.detail_table.setRowCount(len(rows))
        for i, (k, v) in enumerate(rows):
            ki = QTableWidgetItem(k)
            vi = QTableWidgetItem(v)
            ki.setForeground(QColor("#8899aa"))
            self.detail_table.setItem(i, 0, ki)
            self.detail_table.setItem(i, 1, vi)

    def populate_results(self, data: dict):
        """Override for module-specific extra display."""
        pass

    def clear(self):
        self.findings_list.clear()
        self.detail_table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.risk_label.setText("Risk:  —")
        self.risk_label.setStyleSheet("color:#556677; font-size:11px; font-family:Consolas;")
        self.status_bar.setText("Ready.")
        self.status_bar.setStyleSheet("color:#556677; font-size:11px; font-family:Consolas;")
        self.last_data = {}
