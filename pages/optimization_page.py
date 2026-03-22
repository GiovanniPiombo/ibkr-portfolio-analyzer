from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from workers.optimization_thread import OptimizationWorker
from components.markowitz_chart import MarkowitzChartView

class OptimizationPage(QWidget):
    """
    Page component for Modern Portfolio Theory optimization.
    
    Displays the Efficient Frontier chart and a table detailing the exact 
    weight reallocations required to achieve the Max Sharpe portfolio.
    """
    def __init__(self):
        super().__init__()
        self.metrics = None
        self.positions = None
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(28, 24, 28, 24)

        # ── HEADER & CONTROLS ───────────────────────────────────────────
        header_layout = QHBoxLayout()
        header_label = QLabel("Portfolio Optimization (Markowitz)")
        header_label.setObjectName("page_header")
        
        self.run_btn = QPushButton("Run Optimization")
        self.run_btn.setObjectName("primary_btn")
        self.run_btn.setMinimumHeight(38)
        self.run_btn.clicked.connect(self.on_run_clicked)
        
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        header_layout.addWidget(self.run_btn)
        main_layout.addLayout(header_layout)

        # ── SUMMARY CARDS ────────────────────────────────────
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)

        curr_card, self.curr_label = self.create_summary_card("CURRENT SHARPE", "0.00", "#E05252")
        opt_card, self.opt_label = self.create_summary_card("OPTIMAL SHARPE", "0.00", "#2ECC8A")
        
        cards_layout.addWidget(curr_card)
        cards_layout.addWidget(opt_card)
        main_layout.addLayout(cards_layout)

        # ── CHART & TABLE LAYOUT ────────────────────────────────────
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        self.chart_view = MarkowitzChartView(self)
        self.chart_view.setMinimumHeight(400)
        content_layout.addWidget(self.chart_view, stretch=2)

        self.delta_table = QTableWidget(0, 4)
        self.delta_table.setHorizontalHeaderLabels(["Asset", "Current %", "Optimal %", "Action"])
        header = self.delta_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.delta_table.setAlternatingRowColors(True)
        self.delta_table.setShowGrid(False)
        self.delta_table.verticalHeader().setVisible(False)
        self.delta_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.delta_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        content_layout.addWidget(self.delta_table, stretch=1)
        main_layout.addLayout(content_layout)

    def create_summary_card(self, title: str, initial_value: str, color: str):
        card = QFrame()
        card.setObjectName("summary_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        
        title_label = QLabel(title)
        title_label.setObjectName("card_title")
        
        value_label = QLabel(initial_value)
        value_label.setStyleSheet(
            f"color: {color}; font-family: 'Consolas', monospace; font-size: 24px; font-weight: 700;"
        )
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        return card, value_label

    def set_data(self, metrics: dict, positions: list):
        """Called by MainWindow to inject the shared portfolio data."""
        self.metrics = metrics
        self.positions = positions

    def on_run_clicked(self):
        if not self.metrics or not self.positions:
            QMessageBox.warning(self, "Data Missing", "Please wait for IBKR data to finish loading in the Dashboard.")
            return

        self.run_btn.setEnabled(False)
        self.run_btn.setText("Optimizing...")

        self.worker = OptimizationWorker(self.metrics, self.positions)
        self.worker.progress_update.connect(lambda msg: self.run_btn.setText(msg))
        self.worker.optimization_finished.connect(self.on_optimization_complete)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()

    def on_optimization_complete(self, payload: dict):
        self.run_btn.setEnabled(True)
        self.run_btn.setText("Run Optimization")

        current = payload["current"]
        optimal = payload["optimal"]
        
        self.curr_label.setText(f"{current['sharpe']:.2f}")
        self.opt_label.setText(f"{optimal['sharpe']:.2f}")

        self.chart_view.update_graph(payload["frontier"], current, optimal)

        symbols = payload["symbols"]
        curr_weights = payload["current_weights"]
        opt_weights = optimal["weights"]

        self.delta_table.setRowCount(len(symbols))
        for row, sym in enumerate(symbols):
            c_weight = curr_weights.get(sym, 0.0) * 100
            o_weight = opt_weights[row] * 100
            diff = o_weight - c_weight
            
            action = "Hold"
            if diff > 1.0: action = f"Buy +{diff:.1f}%"
            elif diff < -1.0: action = f"Sell {diff:.1f}%"

            self.delta_table.setItem(row, 0, QTableWidgetItem(sym))
            self.delta_table.setItem(row, 1, QTableWidgetItem(f"{c_weight:.1f}%"))
            self.delta_table.setItem(row, 2, QTableWidgetItem(f"{o_weight:.1f}%"))
            
            action_item = QTableWidgetItem(action)
            if "Buy" in action: action_item.setForeground(QColor("#2ECC8A"))
            elif "Sell" in action: action_item.setForeground(QColor("#E05252"))
            self.delta_table.setItem(row, 3, action_item)

    def on_error(self, error_msg):
        self.run_btn.setEnabled(True)
        self.run_btn.setText("Run Optimization")
        QMessageBox.critical(self, "Optimization Error", str(error_msg))