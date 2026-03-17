# root/tests/conftest.py
import sys
import os
import pytest

#Path Resolving
core_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../core'))
if core_path not in sys.path:
    sys.path.insert(0, core_path)


# Necessary fixture to reset the FX cache before each test, ensuring that tests do not interfere with each other due to cached data.
import portfolio

@pytest.fixture(autouse=True)
def reset_fx_cache():
    """
    This fixture is automatically applied to all tests. It clears the FX cache before each test runs, ensuring that tests do not interfere with each other due to cached data.
    """
    portfolio.fx_cache.clear()