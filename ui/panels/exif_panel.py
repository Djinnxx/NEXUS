from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from .base_panel import BasePanel
from modules.exif_module import Worker


class EXIFPanel(BasePanel):
    module_name = "EXIF / Metadata Analysis"
    description = "Extract GPS, device info and author metadata from images and documents"
    module_key  = "exif"
    Worker      = Worker

    def setup_module_ui(self):
        # Insert file picker row above the tabs
        file_row = QHBoxLayout()
        file_row.setSpacing(8)

        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Select or drag a file (JPG, PDF, DOCX) …")
        self.file_input.textChanged.connect(lambda t: self.target_label.setText(f"Target:  {t}"))
        file_row.addWidget(self.file_input)

        browse_btn = QPushButton("Browse …")
        browse_btn.setObjectName("action_btn")
        browse_btn.setStyleSheet(
            "QPushButton { background:#0f3460; color:white; border:1px solid #1e4a80;"
            "border-radius:4px; padding:5px 14px; font-size:12px; }"
            "QPushButton:hover { background:#1a4a80; }"
        )
        browse_btn.clicked.connect(self._browse)
        file_row.addWidget(browse_btn)

        # Insert at position 3 (after progress bar, before tabs)
        layout = self.layout()
        layout.insertLayout(layout.count() - 2, file_row)

        # Map tab
        self.map_label = QLabel("No GPS data found yet.")
        self.map_label.setStyleSheet(
            "color:#8899aa; font-family:Consolas; font-size:12px;"
            "background:#0d1117; border:1px solid #0f3460; padding:12px;"
        )
        self.map_label.setWordWrap(True)
        self.tabs.addTab(self.map_label, "GPS")

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select File",
            "",
            "Supported Files (*.jpg *.jpeg *.png *.tiff *.pdf *.docx *.docm);;All Files (*)"
        )
        if path:
            self.file_input.setText(path)

    def run_scan(self, target: str = None):
        path = self.file_input.text().strip() or target or ""
        if not path:
            QMessageBox.warning(self, "No File", "Please select a file first.")
            return
        super().run_scan(path)

    def populate_results(self, data: dict):
        gps = data.get("data", {}).get("gps")
        if gps:
            lat, lon = gps["latitude"], gps["longitude"]
            self.map_label.setText(
                f"<b style='color:#e94560;'>GPS COORDINATES FOUND</b><br><br>"
                f"Latitude:   {lat}<br>"
                f"Longitude:  {lon}<br><br>"
                f"<a style='color:#00ccff;' href='https://maps.google.com/?q={lat},{lon}'>"
                f"Open in Google Maps</a>"
            )
            self.map_label.setTextFormat(Qt.TextFormat.RichText)
            self.map_label.setOpenExternalLinks(True)
            self.tabs.setCurrentIndex(self.tabs.count() - 1)
        else:
            self.map_label.setText("No GPS data found in this file.")
