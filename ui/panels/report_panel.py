from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import os, threading


class ReportPanel(QWidget):
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
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("Report Generator")
        title.setObjectName("mod_title")
        root.addWidget(title)

        desc = QLabel("Generate a professional PDF report from all collected scan results.")
        desc.setObjectName("mod_desc")
        root.addWidget(desc)

        # Output path
        path_row = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Output path (leave blank for Desktop) …")
        path_row.addWidget(self.path_input)

        browse = QPushButton("Browse …")
        browse.setObjectName("clear_btn")
        browse.clicked.connect(self._browse)
        path_row.addWidget(browse)
        root.addLayout(path_row)

        # Generate button
        self.gen_btn = QPushButton("▶  GENERATE PDF REPORT")
        self.gen_btn.setObjectName("scan_btn")
        self.gen_btn.setStyleSheet(
            "QPushButton#scan_btn { font-size:13px; padding:10px 24px; max-height:40px; }"
        )
        self.gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.gen_btn.clicked.connect(self._generate)
        root.addWidget(self.gen_btn)

        # Status / result
        self.status_lbl = QLabel("Ready. Run module scans first to populate the report.")
        self.status_lbl.setStyleSheet("color:#8899aa; font-size:12px; font-family:Consolas;")
        self.status_lbl.setWordWrap(True)
        root.addWidget(self.status_lbl)

        self.open_btn = QPushButton("Open Report")
        self.open_btn.setObjectName("clear_btn")
        self.open_btn.setVisible(False)
        self.open_btn.clicked.connect(self._open_report)
        root.addWidget(self.open_btn)
        self._report_path = None

        root.addStretch()

    def _browse(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Report As", "NEXUS_Report.pdf", "PDF (*.pdf)"
        )
        if path:
            self.path_input.setText(path)

    def _generate(self):
        target = self.main_window.search_input.text().strip()
        if not target:
            QMessageBox.warning(self, "No Target", "Enter a target and run some scans first.")
            return

        all_results = self.main_window.all_results
        if not all_results:
            QMessageBox.warning(self, "No Data",
                "No scan results available. Run modules before generating a report.")
            return

        self.gen_btn.setEnabled(False)
        self.status_lbl.setText("Generating report…")
        self.status_lbl.setStyleSheet("color:#fdcb6e; font-size:12px; font-family:Consolas;")

        output = self.path_input.text().strip() or None

        def _run():
            try:
                from modules.report_generator import generate_report
                path = generate_report(target, all_results, output)
                self._report_path = path
                QMetaObject.invokeMethod(self, "_on_done",
                    Qt.ConnectionType.QueuedConnection, Q_ARG(str, path))
            except Exception as e:
                QMetaObject.invokeMethod(self, "_on_error",
                    Qt.ConnectionType.QueuedConnection, Q_ARG(str, str(e)))

        threading.Thread(target=_run, daemon=True).start()

    @pyqtSlot(str)
    def _on_done(self, path: str):
        self.gen_btn.setEnabled(True)
        self.status_lbl.setText(f"✓  Report saved:\n{path}")
        self.status_lbl.setStyleSheet("color:#00dd88; font-size:12px; font-family:Consolas;")
        self.open_btn.setVisible(True)
        self.log_signal.emit(f"Report generated: {path}", "SUCCESS")

    @pyqtSlot(str)
    def _on_error(self, err: str):
        self.gen_btn.setEnabled(True)
        self.status_lbl.setText(f"⚠  Error: {err}")
        self.status_lbl.setStyleSheet("color:#e94560; font-size:12px; font-family:Consolas;")
        self.log_signal.emit(f"Report generation failed: {err}", "ERROR")

    def _open_report(self):
        if self._report_path and os.path.exists(self._report_path):
            import subprocess, sys
            if sys.platform == "win32":
                os.startfile(self._report_path)
            else:
                subprocess.run(["xdg-open", self._report_path])

    def set_target(self, _): pass
    def clear(self):
        self.status_lbl.setText("Ready.")
        self.open_btn.setVisible(False)
        self._report_path = None
