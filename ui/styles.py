NEXUS_STYLE = """
/* ── Base ───────────────────────────────────── */
QMainWindow, QWidget { background: #1a1a2e; color: #eaeaea; font-family: 'Segoe UI'; font-size: 13px; }
QDialog { background: #1a1a2e; }

/* ── Sidebar ────────────────────────────────── */
QFrame#sidebar { background: #16213e; border-right: 1px solid #0f3460; min-width: 195px; max-width: 195px; }
QLabel#logo    { color: #e94560; font-size: 15px; font-weight: bold; padding: 18px 14px 10px 14px; border-bottom: 1px solid #0f3460; }
QLabel#version { color: #555; font-size: 10px; padding: 0 14px 12px 14px; }

QPushButton#nav_btn {
    background: transparent; color: #8899aa;
    border: none; border-left: 3px solid transparent;
    padding: 9px 14px; text-align: left; font-size: 12px;
}
QPushButton#nav_btn:hover   { background: rgba(15,52,96,0.5); color: #cce0ff; border-left: 3px solid #0f3460; }
QPushButton#nav_btn:checked { background: #0f3460; color: #ffffff; border-left: 3px solid #e94560; font-weight: bold; }

QLabel#status_indicator { color: #00ff88; font-family: Consolas; font-size: 11px; padding: 10px 14px; border-top: 1px solid #0f3460; }

/* ── Header bar ─────────────────────────────── */
QFrame#header { background: #16213e; border-bottom: 1px solid #0f3460; min-height: 54px; max-height: 54px; }
QLabel#app_title { color: #e94560; font-size: 13px; font-weight: bold; padding: 0 8px; }

QLineEdit#search_input {
    background: #0d1117; color: #eaeaea;
    border: 1px solid #0f3460; border-radius: 4px;
    padding: 5px 12px; font-family: Consolas; font-size: 12px;
    min-width: 340px; max-height: 28px;
}
QLineEdit#search_input:focus { border: 1px solid #e94560; }
QLineEdit#search_input::placeholder { color: #444; }

QPushButton#scan_btn {
    background: #e94560; color: white; border: none;
    border-radius: 4px; padding: 5px 18px;
    font-size: 12px; font-weight: bold; max-height: 28px;
}
QPushButton#scan_btn:hover   { background: #c73652; }
QPushButton#scan_btn:pressed { background: #a52840; }
QPushButton#scan_btn:disabled { background: #4a1a28; color: #888; }

QPushButton#header_btn {
    background: #0f3460; color: #a0b0c0; border: 1px solid #1a4a80;
    border-radius: 4px; padding: 5px 12px;
    font-size: 12px; max-height: 28px;
}
QPushButton#header_btn:hover { background: #1a4a80; color: white; }

/* ── Module panel ───────────────────────────── */
QFrame#module_panel { background: #16213e; }
QLabel#mod_title  { color: #eaeaea; font-size: 17px; font-weight: bold; padding-bottom: 2px; }
QLabel#mod_desc   { color: #8899aa; font-size: 11px; }
QLabel#mod_target { color: #00ccff; font-family: Consolas; font-size: 12px; }

QPushButton#run_btn {
    background: #0f3460; color: white; border: 1px solid #1e4a80;
    border-radius: 4px; padding: 6px 18px; font-size: 12px; font-weight: bold;
}
QPushButton#run_btn:hover   { background: #1a4a80; }
QPushButton#run_btn:pressed { background: #0a2a50; }
QPushButton#run_btn:disabled { background: #0a1a2e; color: #555; border-color: #222; }

QPushButton#clear_btn {
    background: transparent; color: #667788; border: 1px solid #334466;
    border-radius: 4px; padding: 6px 14px; font-size: 12px;
}
QPushButton#clear_btn:hover { color: #aabbcc; border-color: #4466aa; }

QProgressBar {
    background: #0d1117; border: 1px solid #0f3460;
    border-radius: 3px; text-align: center; color: #667788;
    font-size: 10px; max-height: 10px;
}
QProgressBar::chunk { background: #e94560; border-radius: 3px; }

/* ── Tabs ───────────────────────────────────── */
QTabWidget::pane  { background: #16213e; border: 1px solid #0f3460; border-top: none; }
QTabBar::tab      { background: #1a1a2e; color: #8899aa; border: 1px solid #0f3460; border-bottom: none; padding: 6px 16px; font-size: 12px; }
QTabBar::tab:selected { background: #16213e; color: #ffffff; border-top: 2px solid #e94560; }
QTabBar::tab:hover    { background: #0f3460; color: #cce0ff; }

/* ── Tables ─────────────────────────────────── */
QTableWidget {
    background: #0d1117; color: #c9d1d9; alternate-background-color: #111622;
    gridline-color: #0f3460; border: 1px solid #0f3460;
    border-radius: 4px; font-family: Consolas; font-size: 12px;
    selection-background-color: #0f3460;
}
QTableWidget::item          { padding: 3px 8px; border: none; }
QTableWidget::item:selected { background: #0f3460; color: #ffffff; }
QHeaderView::section {
    background: #16213e; color: #8899aa; border: none;
    border-bottom: 1px solid #0f3460; padding: 6px 8px;
    font-size: 11px; font-weight: bold; letter-spacing: 0.5px;
}

/* ── Log terminal ───────────────────────────── */
QFrame#log_frame   { background: #0d1117; border-top: 1px solid #0f3460; }
QTextEdit#log_view {
    background: #0d1117; color: #00dd88; font-family: Consolas; font-size: 11px;
    border: none; padding: 6px;
    selection-background-color: #0f3460;
}
QLabel#log_label { color: #556677; font-family: Consolas; font-size: 10px; padding: 4px 8px; }

/* ── Scrollbars ─────────────────────────────── */
QScrollBar:vertical   { background: #0d1117; width: 7px; border: none; }
QScrollBar:horizontal { background: #0d1117; height: 7px; border: none; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #1e3a5f; border-radius: 3px; min-height: 20px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background: #0f3460; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }

/* ── Splitter ───────────────────────────────── */
QSplitter::handle { background: #0f3460; }
QSplitter::handle:horizontal { width: 2px; }
QSplitter::handle:vertical   { height: 2px; }

/* ── Misc inputs ────────────────────────────── */
QLineEdit, QTextEdit {
    background: #0d1117; color: #eaeaea; border: 1px solid #0f3460;
    border-radius: 4px; padding: 5px 8px; font-family: Consolas;
}
QLineEdit:focus, QTextEdit:focus { border: 1px solid #e94560; }

QComboBox {
    background: #0d1117; color: #eaeaea; border: 1px solid #0f3460;
    border-radius: 4px; padding: 4px 8px; font-size: 12px;
}
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView { background: #0d1117; color: #eaeaea; selection-background-color: #0f3460; }

QCheckBox { color: #8899aa; font-size: 12px; spacing: 6px; }
QCheckBox::indicator { width: 14px; height: 14px; border: 1px solid #0f3460; border-radius: 2px; background: #0d1117; }
QCheckBox::indicator:checked { background: #e94560; border-color: #e94560; }

/* ── Tooltips ───────────────────────────────── */
QToolTip { background: #16213e; color: #eaeaea; border: 1px solid #0f3460; padding: 4px 8px; font-size: 11px; }

/* ── Message boxes ──────────────────────────── */
QMessageBox { background: #1a1a2e; }
QMessageBox QPushButton { background: #0f3460; color: white; border: none; padding: 6px 16px; border-radius: 4px; }
QMessageBox QPushButton:hover { background: #1a4a80; }
"""
