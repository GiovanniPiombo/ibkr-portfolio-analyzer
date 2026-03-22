from PySide6.QtCore import QThread, Signal
from core.markowitz_model import MarkowitzOptimizer

class OptimizationWorker(QThread):
    """
    A dedicated background thread for running Modern Portfolio Theory optimizations.

    This worker prevents the PySide6 UI from freezing while SciPy performs 
    complex matrix minimizations to find the Efficient Frontier and the 
    Tangency Portfolio.

    Signals:
        optimization_finished (dict): Emitted upon successful calculation. Contains 
            current stats, optimal stats, frontier points, and asset symbols.
        error_occurred (str): Emitted if an exception is raised during optimization.
        progress_update (str): Emitted at various stages to update UI loading states.
    """
    optimization_finished = Signal(dict)
    error_occurred = Signal(str)
    progress_update = Signal(str)

    def __init__(self, metrics: dict, positions: list):
        """
        Initializes the optimization worker.

        Args:
            metrics (dict): The pre-calculated risk metrics exported by PortfolioManager.
                Must contain 'asset_returns', 'cov_matrix', 'symbols', and 'risk_free_rate'.
            positions (list): The list of current holdings formatted for the UI.
                Expected format per item: [Ticker, Quantity, Current Price, Market Value]
        """
        super().__init__()
        self.metrics = metrics
        self.positions = positions

    def run(self):
        """
        Executes the optimization pipeline in a background thread.
        """
        try:
            self.progress_update.emit("Initializing Markowitz engine...")
            
            asset_returns = self.metrics.get("asset_returns", {})
            cov_matrix = self.metrics.get("cov_matrix", {})
            symbols = self.metrics.get("symbols", [])
            risk_free = self.metrics.get("risk_free_rate", 0.0)

            if not symbols:
                raise ValueError("No risky assets available for optimization.")

            total_risky_value = sum([pos[3] for pos in self.positions if pos[0] in symbols])
            current_weights = {}
            
            if total_risky_value > 0:
                for pos in self.positions:
                    ticker = pos[0]
                    market_value = pos[3]
                    if ticker in symbols:
                        current_weights[ticker] = market_value / total_risky_value

            optimizer = MarkowitzOptimizer(
                asset_returns=asset_returns, 
                cov_matrix=cov_matrix, 
                symbols=symbols, 
                risk_free_rate=risk_free
            )

            self.progress_update.emit("Evaluating current allocation...")
            current_stats = optimizer.evaluate_current_portfolio(current_weights)
            self.progress_update.emit("Finding optimal Max Sharpe portfolio...")
            optimal_stats = optimizer.optimize_max_sharpe()
            self.progress_update.emit("Calculating the Efficient Frontier...")
            frontier_points = optimizer.generate_efficient_frontier(points=40)

            payload = {
                "current": current_stats,
                "optimal": optimal_stats,
                "frontier": frontier_points,
                "symbols": symbols,
                "current_weights": current_weights
            }

            self.progress_update.emit("Optimization complete!")
            self.optimization_finished.emit(payload)

        except Exception as e:
            self.error_occurred.emit(f"Optimization Worker Error: {str(e)}")