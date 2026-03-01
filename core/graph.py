import matplotlib.pyplot as plt
import numpy as np

def plot_portfolio_montecarlo(simulation_prices, title="Monte Carlo Simulation of Portfolio Value Over Time"):
    """
    Plots the Monte Carlo simulation results for a financial portfolio.
    Shows the Worst (5th percentile), Median (50th percentile), and Best (95th percentile) scenarios over time
    """
    # transpose if simulations are in rows and time steps in columns
    if simulation_prices.shape[1] > simulation_prices.shape[0]:
        simulation_prices = simulation_prices.T
    
    # percentiles
    worst = np.percentile(simulation_prices, 5, axis=0)
    median = np.percentile(simulation_prices, 50, axis=0)
    best = np.percentile(simulation_prices, 95, axis=0)
    
    time_steps = np.arange(simulation_prices.shape[1])
    
    plt.figure(figsize=(12, 6))
    
    # first 100 simulations in grey for visual context
    plt.plot(time_steps, simulation_prices[:100, :].T, color='grey', alpha=0.1, linewidth=1)
    
    # plot percentiles with distinct colors and labels
    plt.plot(time_steps, worst, color='red', linestyle='-', linewidth=2, label='Worst Case (5° percentile)')
    plt.plot(time_steps, median, color='blue', linestyle='-', linewidth=2, label='Median Case (50° percentile)')
    plt.plot(time_steps, best, color='green', linestyle='-', linewidth=2, label='Best Case (95° percentile)')
    
    plt.title(title)
    plt.xlabel('Trading Days')
    plt.ylabel('Portfolio Value')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # format y-axis with commas for thousands
    ax = plt.gca()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
    
    plt.tight_layout()
    plt.show()