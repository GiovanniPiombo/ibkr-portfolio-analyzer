from core.brokers.ibkr_broker import IBKRBroker
from core.utils import read_json
from core.path_manager import PathManager

class BrokerFactory:
    """
    Factory class responsible for instantiating the correct broker adapter
    based on user settings. 
    """
    
    @staticmethod
    def get_active_broker():
        """
        Reads the configuration and returns an initialized instance of a BaseBroker.
        In the future, this will check an "ACTIVE_BROKER" setting in config.json 
        to decide the broker to return.
        """
        
        # IBKR
        host = read_json(PathManager.CONFIG_FILE, "IBKR_HOST") or '127.0.0.1'
        port = read_json(PathManager.CONFIG_FILE, "IBKR_PORT") or 4001
        client_id = read_json(PathManager.CONFIG_FILE, "IBKR_CLIENT_ID") or 1
        
        return IBKRBroker(host=host, port=port, client_id=client_id)