import numpy as np
import pandas as pd
import scipy.optimize as sco

class MarkowitzOptimizer:
    """
    Mathematical engine for Modern Portfolio Theory (MPT) optimization.
    
    This class takes annualized expected returns and a covariance matrix 
    to calculate the Efficient Frontier and identify the Maximum Sharpe 
    Ratio portfolio (Tangency Portfolio). It enforces long-only constraints 
    (no short selling) and requires the weights to sum to 100%.
    """
    
    def __init__(self, asset_returns: dict, cov_matrix: dict, symbols: list, risk_free_rate: float = 0.0):
        """
        Initializes the optimizer with the pre-calculated metrics.
        
        Args:
            asset_returns (dict): Annualized expected returns per ticker.
            cov_matrix (dict): Annualized covariance matrix (nested dictionary).
            symbols (list): The strict order of tickers to maintain matrix alignment.
            risk_free_rate (float, optional): The risk-free rate for Sharpe calculations.
        """
        self.symbols = symbols
        self.num_assets = len(symbols)
        self.risk_free_rate = risk_free_rate
        
        self.returns = np.array([asset_returns[sym] for sym in symbols])
        
        cov_df = pd.DataFrame(cov_matrix)
        self.cov_matrix = cov_df.loc[symbols, symbols].values

    def portfolio_performance(self, weights: np.ndarray) -> tuple:
        """
        Calculates the expected return and volatility for a given set of weights.
        """
        p_return = np.sum(self.returns * weights)
        p_volatility = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
        return p_return, p_volatility

    def negative_sharpe_ratio(self, weights: np.ndarray) -> float:
        """
        The objective function to minimize. 
        Minimizing the negative Sharpe ratio is mathematically equivalent 
        to maximizing the actual Sharpe ratio.
        """
        p_ret, p_vol = self.portfolio_performance(weights)
        if p_vol == 0:
            return 0.0
        return -(p_ret - self.risk_free_rate) / p_vol

    def minimize_volatility(self, weights: np.ndarray) -> float:
        """Objective function to find the absolute minimum variance portfolio."""
        _, p_vol = self.portfolio_performance(weights)
        return p_vol

    def optimize_max_sharpe(self) -> dict:
        """
        Uses Sequential Least Squares Programming (SLSQP) to find the weights 
        that maximize the Sharpe Ratio.
        """
        initial_guess = self.num_assets * [1. / self.num_assets]
        
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        
        bounds = tuple((0.0, 1.0) for _ in range(self.num_assets))
        
        result = sco.minimize(
            self.negative_sharpe_ratio, 
            initial_guess, 
            method='SLSQP', 
            bounds=bounds, 
            constraints=constraints
        )
        
        opt_return, opt_vol = self.portfolio_performance(result.x)
        
        return {
            "weights": np.round(result.x, 4).tolist(),
            "return": opt_return,
            "volatility": opt_vol,
            "sharpe": (opt_return - self.risk_free_rate) / opt_vol if opt_vol > 0 else 0
        }

    def generate_efficient_frontier(self, points: int = 50) -> list:
        """
        Generates coordinates (Volatility, Return) to plot the Efficient Frontier curve.
        
        It sweeps through a range of target returns, from the minimum possible 
        variance to the maximum possible individual asset return, calculating 
        the minimum volatility for each target return.
        """
        initial_guess = self.num_assets * [1. / self.num_assets]
        bounds = tuple((0.0, 1.0) for _ in range(self.num_assets))
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        
        min_var_result = sco.minimize(self.minimize_volatility, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        min_ret, min_vol = self.portfolio_performance(min_var_result.x)
        
        max_ret = self.returns.max()
        
        target_returns = np.linspace(min_ret, max_ret, points)
        frontier_vols = []
        
        for tr in target_returns:
            loop_constraints = (
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': lambda x: self.portfolio_performance(x)[0] - tr}
            )
            res = sco.minimize(self.minimize_volatility, initial_guess, method='SLSQP', bounds=bounds, constraints=loop_constraints)
            frontier_vols.append(res.fun)
            
        return [{"volatility": v, "return": r} for v, r in zip(frontier_vols, target_returns)]

    def evaluate_current_portfolio(self, current_weights: dict) -> dict:
        """
        Evaluates the performance of the user's current allocation.
        """
        weights_array = np.array([current_weights.get(sym, 0.0) for sym in self.symbols])
        if np.sum(weights_array) > 0:
            weights_array = weights_array / np.sum(weights_array)
            
        p_ret, p_vol = self.portfolio_performance(weights_array)
        
        return {
            "weights": np.round(weights_array, 4).tolist(),
            "return": p_ret,
            "volatility": p_vol,
            "sharpe": (p_ret - self.risk_free_rate) / p_vol if p_vol > 0 else 0
        }