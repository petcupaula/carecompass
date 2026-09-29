from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Interhuman AI
    interhuman_api_key: str = ""
    interhuman_base_url: str = "https://api.interhuman.ai"
    
    # Plaud Transcription API
    plaud_client_id: str = ""
    plaud_api_key: str = ""
    plaud_base_url: str = "https://platform-us.plaud.ai/developer/api"
    
    # Crusoe Inference API
    crusoe_api_key: str = ""
    crusoe_base_url: str = "https://api.inference.crusoecloud.com/v1"
    crusoe_model: str = "zai-org/GLM-5.3-Flash"
    
    # App settings
    upload_dir: str = "./uploads"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
