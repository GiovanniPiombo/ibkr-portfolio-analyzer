from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPen, QPainter
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import Qt, QPointF, QTimer

class MonteCarloChartView(QChartView):
    """Custom QChartView for displaying Monte Carlo simulations."""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.chart = QChart()
        self.setChart(self.chart)
        
        # Apply dark theme
        self.chart.setBackgroundBrush(QColor('#0D1117'))
        self.chart.setTitleBrush(QColor('#E8EDF5'))
        self.chart.legend().setLabelColor(QColor('#C8D0DC'))
        self.chart.legend().setAlignment(Qt.AlignBottom)
        
        # Remove unnecessary chart margins
        self.chart.layout().setContentsMargins(0, 0, 0, 0)
        self.chart.setBackgroundRoundness(0)
        
        # Antialiasing for smoother lines
        self.setRenderHint(QPainter.Antialiasing)

        # Enable click-and-drag selection to zoom
        self.setRubberBand(QChartView.RectangleRubberBand)
        
        # Variables to store our axes and hard limits safely
        self.axis_x = None
        self.axis_y = None
        self.orig_x_min = 0.0
        self.orig_x_max = 0.0
        self.orig_y_min = 0.0
        self.orig_y_max = 0.0

    def update_graph(self, time_steps, worst, median, best, background_lines):
        """Updates the graph with the newly calculated data."""
        self.chart.removeAllSeries()
        
        # Remove old axes
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)

        # Save boundaries securely inside the class instance
        self.orig_x_min = 0.0
        self.orig_x_max = float(time_steps[-1])
        
        min_val = float(background_lines.min()) * 0.95
        max_val = float(background_lines.max()) * 1.05
        
        self.orig_y_min = 0.0 if min_val < 0 else min_val 
        self.orig_y_max = max_val

        # --- Background Lines ---
        num_bg_lines = min(100, background_lines.shape[0] if len(background_lines.shape) > 1 else 0)
        
        bg_pen = QPen(QColor(128, 128, 128, 20))
        bg_pen.setWidth(1)

        for i in range(num_bg_lines):
            series = QLineSeries()
            series.setPen(bg_pen)
            points = [QPointF(float(x), float(y)) for x, y in zip(time_steps, background_lines[i])]
            series.append(points)
            self.chart.addSeries(series)

        # --- Main Lines (Worst, Median, Best) ---
        self._add_main_series(time_steps, worst, "Worst (5%)", "#E05252")
        self._add_main_series(time_steps, median, "Median (50%)", "#4A90E2")
        self._add_main_series(time_steps, best, "Best (95%)", "#2ECC8A")

        # --- Axes Configuration ---
        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Trading Days")
        self.axis_x.setLabelFormat("%i")
        self.axis_x.setRange(self.orig_x_min, self.orig_x_max)
        self.axis_x.setLabelsColor(QColor('#C8D0DC'))
        self.axis_x.setTitleBrush(QColor('#C8D0DC'))
        self.axis_x.setGridLineColor(QColor(200, 208, 220, 25))

        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("Portfolio Value (€)")
        self.axis_y.setLabelFormat("%.0f")
        self.axis_y.setRange(self.orig_y_min, self.orig_y_max)
        self.axis_y.setLabelsColor(QColor('#C8D0DC'))
        self.axis_y.setTitleBrush(QColor('#C8D0DC'))
        self.axis_y.setGridLineColor(QColor(200, 208, 220, 25))

        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)

        for series in self.chart.series():
            series.attachAxis(self.axis_x)
            series.attachAxis(self.axis_y)

        simulated_years = int(self.orig_x_max // 252)
        self.chart.setTitle(f"Portfolio Value Projection ({simulated_years} Years)")

    def _add_main_series(self, x_data, y_data, name, hex_color):
        """Helper to add main series."""
        series = QLineSeries()
        series.setName(name)
        
        pen = QPen(QColor(hex_color))
        pen.setWidth(2)
        series.setPen(pen)
        
        points = [QPointF(float(x), float(y)) for x, y in zip(x_data, y_data)]
        series.append(points)
        self.chart.addSeries(series)

    def _clamp_axes(self):
        """Forces the current view to stay within original data boundaries."""
        if not self.axis_x or not self.axis_y:
            return

        # Force X-Axis Limits
        if self.axis_x.min() < self.orig_x_min:
            self.axis_x.setMin(self.orig_x_min)
        if self.axis_x.max() > self.orig_x_max:
            self.axis_x.setMax(self.orig_x_max)

        # Force Y-Axis Limits
        if self.axis_y.min() < self.orig_y_min:
            self.axis_y.setMin(self.orig_y_min)
        if self.axis_y.max() > self.orig_y_max:
            self.axis_y.setMax(self.orig_y_max)

    def wheelEvent(self, event):
        """Zoom in/out with the scroll wheel and enforce limits using a delay."""
        if event.angleDelta().y() > 0:
            self.chart.zoomIn()
        else:
            self.chart.zoomOut()
            
        # This ensures Qt is completely finished with its internal zoom logic first.
        QTimer.singleShot(10, self._clamp_axes)
        event.accept() 

    def mousePressEvent(self, event):
        """Record the start position to differentiate between a click and a drag."""
        self._click_pos = event.pos()
        
        # Shield base Qt from right-click cursed behavior, but let left-click through
        if event.button() == Qt.RightButton:
            event.accept() 
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Decide whether to reset the zoom (click) or clamp the zoom (drag)."""
        if event.button() == Qt.LeftButton:
            super().mouseReleaseEvent(event)

        is_click = False
        if hasattr(self, '_click_pos') and self._click_pos is not None:
            # Calculate pixel distance between press and release
            delta = event.pos() - self._click_pos
            if delta.manhattanLength() < 5:  # Less than 5 pixels = a click
                is_click = True

        if is_click:
            self.reset_zoom()
            event.accept()
        else:
            if event.button() == Qt.LeftButton:
                # Left drag = Apply the delayed clamp after the zoom
                QTimer.singleShot(10, self._clamp_axes)
            elif event.button() == Qt.RightButton:
                # Right drag = Ignore entirely
                event.accept()
    
    def reset_zoom(self):
        """Manually resets the chart to the exact original boundaries."""
        if self.axis_x and self.axis_y:
            self.axis_x.setRange(self.orig_x_min, self.orig_x_max)
            self.axis_y.setRange(self.orig_y_min, self.orig_y_max)