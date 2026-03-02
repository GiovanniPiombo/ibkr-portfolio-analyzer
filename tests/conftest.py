# root/tests/conftest.py
import sys
import os
import pytest

# 1. RISOLUZIONE DEL PATH
# Calcola il percorso assoluto della cartella 'core' e lo aggiunge a sys.path
core_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../core'))
if core_path not in sys.path:
    sys.path.insert(0, core_path)


# 2. FIXTURE CONDIVISE (Opzionale ma utilissimo)
# Importiamo il modulo DOPO aver sistemato il path
import portfolio

@pytest.fixture(autouse=True)
def reset_fx_cache():
    """
    Questa fixture pulisce la cache FX prima di OGNI test in tutta la suite.
    Essendo in conftest.py con autouse=True, non devi scriverla nei file di test.
    """
    portfolio.fx_cache.clear()