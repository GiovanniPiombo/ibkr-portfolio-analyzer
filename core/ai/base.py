from abc import ABC, abstractmethod

class BaseAIProvider(ABC):
    """
    Base interface for all Artificial Intelligence providers in AlphaPaths.
    """
    
    @abstractmethod
    def analyze_portfolio(self, portfolio_data: dict) -> dict:
        """
        Processes portfolio data and returns the analysis.
        
        Args:
            portfolio_data (dict): Dictionary containing metrics and projections.
            
        Returns:
            dict: The analysis result as a parsed JSON format, 
                  or a dictionary with an {"error": "message"} key in case of failure.
        """
        pass