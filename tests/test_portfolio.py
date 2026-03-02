import pytest
import pandas as pd
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch

# Import the module to be tested (resolved via conftest.py or pytest.ini)
import portfolio

# ==========================================
# MATH FUNCTIONS TESTS
# ==========================================

def test_annualize():
    # Verify that the daily variance is correctly annualized
    assert portfolio.annualize(0.0001, 252) == 0.0252

def test_get_annual_volatility():
    # Verify the calculation of the square root of the annual variance
    assert portfolio.get_annual_volatility(0.04) == 0.2


# ==========================================
# FX RATE RETRIEVAL TESTS (get_fx_rate)
# ==========================================

@pytest.fixture(autouse=True)
def reset_fx_cache():
    """Fixture that clears the FX cache before each test to avoid false positives."""
    portfolio.fx_cache.clear()

@pytest.mark.asyncio
async def test_get_fx_rate_same_currency():
    mock_ib = AsyncMock()
    rate = await portfolio.get_fx_rate(mock_ib, 'EUR', 'EUR')
    
    assert rate == 1.0
    # Ensure no unnecessary API calls are made
    mock_ib.reqHistoricalDataAsync.assert_not_called()

@pytest.mark.asyncio
async def test_get_fx_rate_direct_pair():
    mock_ib = AsyncMock()
    mock_bar = MagicMock()
    mock_bar.close = 1.08
    mock_ib.reqHistoricalDataAsync.return_value = [mock_bar]

    rate = await portfolio.get_fx_rate(mock_ib, 'EUR', 'USD')
    
    assert rate == 1.08
    assert portfolio.fx_cache['EURUSD'] == 1.08

@pytest.mark.asyncio
async def test_get_fx_rate_inverse_pair():
    mock_ib = AsyncMock()
    mock_bar = MagicMock()
    mock_bar.close = 0.85
    
    # The first call (direct pair) returns empty, the second (inverse pair) finds the data
    mock_ib.reqHistoricalDataAsync.side_effect = [[], [mock_bar]]

    rate = await portfolio.get_fx_rate(mock_ib, 'EUR', 'GBP')
    
    assert rate == 1.0 / 0.85
    assert portfolio.fx_cache['EURGBP'] == 1.0 / 0.85

@pytest.mark.asyncio
async def test_get_fx_rate_not_found():
    mock_ib = AsyncMock()
    mock_ib.reqHistoricalDataAsync.return_value = [] # No data found

    with pytest.raises(ValueError, match="FX rate not found for EURJPY"):
        await portfolio.get_fx_rate(mock_ib, 'EUR', 'JPY')

@pytest.mark.asyncio
async def test_get_fx_rate_cache_hit():
    """Verify that consecutive calls for the same currency pair use the cache."""
    mock_ib = AsyncMock()
    mock_bar = MagicMock()
    mock_bar.close = 1.10
    mock_ib.reqHistoricalDataAsync.return_value = [mock_bar]

    # Ensure the cache is clean before starting
    portfolio.fx_cache.clear()

    # First call: Should trigger an API request and cache the result
    rate1 = await portfolio.get_fx_rate(mock_ib, 'GBP', 'USD')
    
    # Second call: Should instantly return the cached result
    rate2 = await portfolio.get_fx_rate(mock_ib, 'GBP', 'USD')

    assert rate1 == 1.10
    assert rate2 == 1.10
    
    # Assert the API was hit strictly once, confirming the cache worked
    mock_ib.reqHistoricalDataAsync.assert_called_once()


# ==========================================
# ORCHESTRATOR TESTS (check_portfolio)
# ==========================================

@pytest.mark.asyncio
@patch("portfolio.IB")
@patch("portfolio.get_fx_rate", new_callable=AsyncMock)
@patch("portfolio.util.df")
@patch("portfolio.read_json")
@patch("portfolio.MonteCarloSimulator")
@patch("portfolio.plot_portfolio_montecarlo")
@patch("portfolio.get_portfolio_analysis")
async def test_check_portfolio(
    mock_ai_analysis, mock_plot, mock_mc_simulator_class,
    mock_read_json, mock_util_df, mock_get_fx_rate, mock_ib_class
):
    """
    Isolated integration test for check_portfolio. 
    We completely mock IBKR, Pandas, and the AI/charting calls.
    """
    # --- IBKR MOCK SETUP ---
    mock_ib = AsyncMock()
    mock_ib_class.return_value = mock_ib
    
    # FORCE synchronous methods to be MagicMock (not AsyncMock) to prevent iterator/await errors
    mock_ib.isConnected = MagicMock(return_value=True)
    mock_ib.disconnect = MagicMock()

    # Dynamically create dummy objects for Account Summary
    Item = type('Item', (), {})
    nlv = Item(); nlv.tag = "NetLiquidation"; nlv.value = "100000.0"; nlv.currency = "EUR"
    cash = Item(); cash.tag = "TotalCashValue"; cash.value = "10000.0"
    mock_ib.accountSummaryAsync.return_value = [nlv, cash]

    # Dynamically create dummy objects for the Portfolio
    PortItem = type('PortItem', (), {})
    Contract = type('Contract', (), {})

    # Asset 1: Cash (will be skipped in risky assets calculations)
    cash_item = PortItem()
    cash_item.contract = Contract()
    cash_item.contract.secType = 'CASH'

    # Asset 2: US Stock
    stock_item = PortItem()
    stock_item.contract = Contract()
    stock_item.contract.secType = 'STK'
    stock_item.contract.symbol = 'AAPL'
    stock_item.contract.currency = 'USD'
    stock_item.marketValue = 90000.0 
    
    # FORCE portfolio to be a synchronous method returning a standard list
    mock_ib.portfolio = MagicMock(return_value=[cash_item, stock_item])

    # --- EXTERNAL MOCKS AND UTILS SETUP ---
    # Dummy exchange rate for AAPL (USD -> EUR)
    mock_get_fx_rate.return_value = 0.90 

    # Dummy historical data from IBKR
    mock_bar = MagicMock()
    mock_ib.reqHistoricalDataAsync.return_value = [mock_bar]

    # Dummy DataFrame to calculate covariance and returns (needs at least 3 rows for pct_change)
    df_mock = pd.DataFrame({
        'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
        'close': [150.0, 155.0, 152.0]
    })
    mock_util_df.return_value = df_mock

    # Dummy Risk-free rate
    mock_read_json.return_value = 0.02 

    # Monte Carlo simulator setup
    mock_simulator_instance = MagicMock()
    mock_simulator_instance.simulate.return_value = np.array([[100, 105], [105, 110]])
    mock_simulator_instance.get_scenarios.return_value = {
        "Worst (5%)": 90000, 
        "Median (50%)": 105000, 
        "Best (95%)": 120000
    }
    mock_mc_simulator_class.return_value = mock_simulator_instance

    # Dummy AI response
    mock_ai_analysis.return_value = {"status": "ok", "message": "Portfolio test passed"}

    # --- FUNCTION EXECUTION ---
    await portfolio.check_portfolio()

    # --- ASSERTIONS ---
    # Verify the main flow is called in the correct order
    mock_ib.connectAsync.assert_called_once_with('127.0.0.1', 4001, clientId=1)
    mock_ib.accountSummaryAsync.assert_called_once()
    mock_ib.portfolio.assert_called_once()
    
    # Verify contract qualification and data fetching are executed
    mock_ib.qualifyContractsAsync.assert_called_once_with(stock_item.contract)
    mock_ib.reqHistoricalDataAsync.assert_called_once()
    
    # Verify dependent modules are called (Charts, AI, MonteCarlo)
    mock_mc_simulator_class.assert_called_once()
    mock_plot.assert_called_once()
    mock_ai_analysis.assert_called_once()
    
    # Verify it always disconnects at the end (finally block)
    mock_ib.disconnect.assert_called_once()


@pytest.mark.asyncio
@patch("portfolio.IB")
async def test_check_portfolio_connection_error(mock_ib_class):
    """Verify that a failure to connect to IBKR halts execution properly."""
    mock_ib = AsyncMock()
    mock_ib_class.return_value = mock_ib
    
    # Simulate a network timeout or rejected connection
    mock_ib.connectAsync.side_effect = ConnectionError("Failed to connect to IBKR")

    # The function should raise the connection error immediately
    with pytest.raises(ConnectionError, match="Failed to connect to IBKR"):
        await portfolio.check_portfolio()
        
    # Ensure no subsequent API calls (like fetching account summary) were made
    mock_ib.accountSummaryAsync.assert_not_called()
    mock_ib.portfolio.assert_not_called()