from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

try:
    import matplotlib
    matplotlib.use("QtAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
    import networkx as nx
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


class RelationshipPanel(QWidget):
    log_signal     = pyqtSignal(str, str)
    results_signal = pyqtSignal(str, dict)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._graph      = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 8)
        root.setSpacing(8)

        title = QLabel("Relationship Map")
        title.setObjectName("mod_title")
        root.addWidget(title)

        desc = QLabel("Visual entity-relationship graph built from all module results.")
        desc.setObjectName("mod_desc")
        root.addWidget(desc)

        ctrl = QHBoxLayout()
        build_btn = QPushButton("▶  BUILD MAP")
        build_btn.setObjectName("run_btn")
        build_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        build_btn.clicked.connect(self._build_map)
        ctrl.addWidget(build_btn)

        save_btn = QPushButton("SAVE IMAGE")
        save_btn.setObjectName("clear_btn")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_image)
        ctrl.addWidget(save_btn)
        ctrl.addStretch()

        self.node_count = QLabel("Nodes: —  |  Edges: —")
        self.node_count.setStyleSheet("color:#556677; font-size:11px; font-family:Consolas;")
        ctrl.addWidget(self.node_count)
        root.addLayout(ctrl)

        if not HAS_MPL:
            warn = QLabel(
                "⚠  matplotlib or networkx not installed.\n"
                "Run:  pip install matplotlib networkx"
            )
            warn.setStyleSheet("color:#fdcb6e; font-family:Consolas; font-size:12px; padding:20px;")
            root.addWidget(warn)
            return

        # Matplotlib canvas
        plt.style.use("dark_background")
        self.fig, self.ax = plt.subplots(figsize=(10, 7))
        self.fig.patch.set_facecolor("#0d1117")
        self.ax.set_facecolor("#0d1117")
        self.canvas = FigureCanvasQTAgg(self.fig)
        root.addWidget(self.canvas, 1)

        toolbar = NavigationToolbar2QT(self.canvas, self)
        toolbar.setStyleSheet("background:#16213e; color:#eaeaea;")
        root.addWidget(toolbar)

    def update_results(self, all_results: dict):
        self._all_results = all_results

    def _build_map(self):
        if not HAS_MPL:
            return
        from modules.relationship_map import build_graph
        target = self.main_window.search_input.text().strip()
        if not target:
            QMessageBox.warning(self, "No Target", "Enter a target and run some scans first.")
            return

        all_results = getattr(self, "_all_results",
                              self.main_window.all_results)
        G = build_graph(target, all_results)
        self._graph = G

        self.ax.clear()
        self.ax.set_facecolor("#0d1117")

        if G.number_of_nodes() == 0:
            self.ax.text(0.5, 0.5, "No data yet – run some modules first.",
                         ha="center", va="center", color="#8899aa", fontsize=12,
                         transform=self.ax.transAxes)
            self.canvas.draw()
            return

        # Layout
        pos = nx.spring_layout(G, k=2.5, seed=42)

        # Node colours
        node_colors = [d.get("color", "#636e72") for _, d in G.nodes(data=True)]
        node_sizes  = [800 if n == target else 400 for n in G.nodes()]

        nx.draw_networkx_edges(G, pos, ax=self.ax,
                               edge_color="#1e3a5f", arrows=True,
                               arrowsize=12, width=0.8)
        nx.draw_networkx_nodes(G, pos, ax=self.ax,
                               node_color=node_colors, node_size=node_sizes,
                               alpha=0.9)
        nx.draw_networkx_labels(G, pos, ax=self.ax,
                                font_size=7, font_color="#c9d1d9",
                                labels={n: (n[:20] + "…" if len(n) > 20 else n)
                                        for n in G.nodes()})

        self.ax.set_title(f"Entity Map – {target}",
                          color="#8899aa", fontsize=11, pad=10)
        self.ax.axis("off")
        self.fig.tight_layout()
        self.canvas.draw()

        n, e = G.number_of_nodes(), G.number_of_edges()
        self.node_count.setText(f"Nodes: {n}  |  Edges: {e}")
        self.log_signal.emit(f"Relationship map built: {n} nodes, {e} edges", "SUCCESS")

    def _save_image(self):
        if not HAS_MPL or not self._graph:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Map", "nexus_map.png", "PNG (*.png);;PDF (*.pdf)"
        )
        if path:
            self.fig.savefig(path, dpi=150, facecolor="#0d1117")
            self.log_signal.emit(f"Map saved: {path}", "SUCCESS")

    def set_target(self, _):
        pass

    def clear(self):
        if HAS_MPL:
            self.ax.clear()
            self.ax.set_facecolor("#0d1117")
            self.canvas.draw()
        self.node_count.setText("Nodes: —  |  Edges: —")
        self._graph = None
