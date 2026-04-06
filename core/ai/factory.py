from core.ai.gemini import GeminiProvider
from core.utils import read_json
from core.path_manager import PathManager
from core.logger import app_logger

class AIFactory:
    @staticmethod
    def get_provider():
        config = read_json(PathManager.CONFIG_FILE) or {}
        provider_type = config.get("AI_PROVIDER", "Gemini")
        
        if provider_type == "Gemini":
            return GeminiProvider(
                api_key=config.get("GEMINI_API_KEY", ""),
                model_name=config.get("GEMINI_MODEL", "gemini-3-flash-preview")
            )
        else:
            app_logger.warning(f"Provider {provider_type} not implemented. Falling back to Gemini.")
            return GeminiProvider(
                api_key=config.get("GEMINI_API_KEY", ""),
                model_name=config.get("GEMINI_MODEL", "gemini-3-flash-preview")
            )

def get_portfolio_analysis(portfolio_data: dict) -> dict:
    """
    Entry point used by AIWorker. 
    Dynamically instantiates the correct provider and starts the analysis.
    """
    provider = AIFactory.get_provider()
    return provider.analyze_portfolio(portfolio_data)