import pytest
import numpy as np
from montecarlo import MonteCarloSimulator

# --- FIXTURE ---
# We use a fixture to create a baseline simulator to reuse across tests
@pytest.fixture
def default_simulator():
    return MonteCarloSimulator(capital=1000.0, mu=0.05, sigma=0.2, years=2, simulations=100)

# 1. INITIALIZATION TEST
def test_initialization(default_simulator):
    assert default_simulator.capital == 1000.0
    assert default_simulator.mu == 0.05
    assert default_simulator.sigma == 0.2
    assert default_simulator.years == 2
    assert default_simulator.simulations == 100

# 2. OUTPUT SHAPE TEST
def test_simulation_shape(default_simulator):
    prices = default_simulator.simulate()
    # Years * 252 days + 1 (Day 0)
    expected_days = int(2 * 252) + 1  
    assert prices.shape == (expected_days, 100)

# 3. INITIAL VALUE TEST (DAY 0)
def test_day_zero_capital(default_simulator):
    prices = default_simulator.simulate()
    # Verify that the entire first row (Day 0) is exactly equal to the initial capital
    assert np.all(prices[0, :] == 1000.0)

# 4. DETERMINISTIC BEHAVIOR TESTS
def test_zero_volatility():
    # If sigma is 0, the process loses randomness: P_T = P_0 * exp(mu * T)
    sim = MonteCarloSimulator(capital=1000.0, mu=0.05, sigma=0.0, years=1, simulations=10)
    prices = sim.simulate()
    
    expected_final_price = 1000.0 * np.exp(0.05 * 1)
    
    # np.allclose checks that values are almost identical (tolerating small float rounding errors)
    assert np.allclose(prices[-1, :], expected_final_price)

def test_zero_drift_and_volatility():
    # If mu = 0 and sigma = 0, the price must never deviate from the initial capital
    sim = MonteCarloSimulator(capital=1000.0, mu=0.0, sigma=0.0, years=1, simulations=10)
    prices = sim.simulate()
    
    assert np.all(prices == 1000.0)

# 5. SCENARIO CALCULATION TEST
def test_get_scenarios():
    sim = MonteCarloSimulator(capital=100.0, mu=0.05, sigma=0.2, years=1)
    
    # Create a fake price matrix (mock)
    # get_scenarios only cares about the last row, so we populate it with numbers from 1 to 100
    mock_prices = np.zeros((10, 100))
    mock_prices[-1, :] = np.arange(1, 101) 
    
    scenarios = sim.get_scenarios(mock_prices)
    
    # The exact mathematical percentiles of a series from 1 to 100
    assert np.isclose(scenarios["Worst (5%)"], 5.95)
    assert np.isclose(scenarios["Median (50%)"], 50.5)
    assert np.isclose(scenarios["Best (95%)"], 95.05)

# 6. REPRODUCIBILITY TEST (SEED)
def test_reproducibility():
    sim = MonteCarloSimulator(capital=1000.0, mu=0.05, sigma=0.2, years=1, simulations=10)
    
    # Set the seed and run the first simulation
    np.random.seed(42)
    prices_run_1 = sim.simulate()
    
    # Reset the same seed and run the second simulation
    np.random.seed(42)
    prices_run_2 = sim.simulate()
    
    # The two matrices must be perfectly identical
    assert np.array_equal(prices_run_1, prices_run_2)

    # --- 7. INVALID INPUTS TESTS (NEGATIVE EDGE CASES) ---

def test_negative_capital():
    # Expect a ValueError when capital is negative or zero
    with pytest.raises(ValueError):
        MonteCarloSimulator(capital=-1000.0, mu=0.05, sigma=0.2, years=1)

def test_negative_sigma():
    # Expect a ValueError when volatility is negative
    with pytest.raises(ValueError):
        MonteCarloSimulator(capital=1000.0, mu=0.05, sigma=-0.2, years=1)

def test_negative_years():
    # Expect a ValueError when years are negative
    with pytest.raises(ValueError):
        MonteCarloSimulator(capital=1000.0, mu=0.05, sigma=0.2, years=-1)

# --- 8. BOUNDARY / LIMIT PARAMETERS TESTS ---

def test_zero_simulations():
    # simulations = 0 should raise an error to prevent empty arrays
    with pytest.raises(ValueError):
        MonteCarloSimulator(capital=1000.0, mu=0.05, sigma=0.2, years=1, simulations=0)

def test_one_simulation():
    # simulations = 1 is valid and should compute successfully
    sim = MonteCarloSimulator(capital=1000.0, mu=0.05, sigma=0.2, years=1, simulations=1)
    prices = sim.simulate()
    # Expect 252 days + 1 (Day 0) and exactly 1 column
    assert prices.shape == (253, 1)

def test_zero_years():
    # years = 0 should only return Day 0 (the initial capital)
    sim = MonteCarloSimulator(capital=1000.0, mu=0.05, sigma=0.2, years=0, simulations=10)
    prices = sim.simulate()
    
    # Shape should be exactly 1 row (Day 0) and 10 columns
    assert prices.shape == (1, 10)
    assert np.all(prices == 1000.0)

# --- 9. EXTREME VALUES TESTS ---

def test_extreme_volatility():
    # Test with very high volatility (e.g., 80% or 0.8) and long period
    sim = MonteCarloSimulator(capital=1000.0, mu=0.05, sigma=0.8, years=10, simulations=100)
    prices = sim.simulate()
    
    # Check that there are no NaN (Not a Number) or Inf (Infinity) values generated
    assert not np.isnan(prices).any(), "Simulation contains NaN values."
    assert not np.isinf(prices).any(), "Simulation contains Infinite values."

# --- 10. STATISTICAL VALIDATION TEST ---

def test_statistical_expected_value():
    # The theoretical expected value of Geometric Brownian Motion is E[S_T] = S_0 * exp(mu * T)
    # We use a large number of simulations to satisfy the Law of Large Numbers
    sim = MonteCarloSimulator(capital=1000.0, mu=0.05, sigma=0.2, years=1, simulations=50000)
    
    np.random.seed(42)
    prices = sim.simulate()
    final_prices = prices[-1, :]
    
    theoretical_mean = 1000.0 * np.exp(0.05 * 1)
    empirical_mean = np.mean(final_prices)
    
    # Check if the empirical mean is close to the theoretical mean (within a 2% relative tolerance)
    assert np.isclose(empirical_mean, theoretical_mean, rtol=0.02)

# --- 11. PERCENTILE ORDERING TEST ---

def test_percentile_ordering(default_simulator):
    # Verify that Worst (5%) <= Median (50%) <= Best (95%)
    prices = default_simulator.simulate()
    scenarios = default_simulator.get_scenarios(prices)
    
    worst = scenarios["Worst (5%)"]
    median = scenarios["Median (50%)"]
    best = scenarios["Best (95%)"]
    
    assert worst <= median
    assert median <= best