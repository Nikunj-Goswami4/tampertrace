import json
import logging
from pathlib import Path
from typing import Dict, Any

from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the app directory (backend/app)
APP_DIR = Path(__file__).resolve().parent.parent
# Get the backend directory (backend)
BACKEND_DIR = APP_DIR.parent
# Get the project root directory (tampertrace)
PROJECT_ROOT = BACKEND_DIR.parent

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    DATABASE_URL: str = ""
    GEMINI_API_KEY: str = ""
    PINECONE_API_KEY: str = ""
    PORT: int = 8000

    # Look for .env in the project root, backend dir, or current dir
    model_config = SettingsConfigDict(
        env_file=(str(PROJECT_ROOT / ".env"), str(BACKEND_DIR / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def calibrated_config(self) -> Dict[str, Any]:
        """Safely load the calibrated_config.json file."""
        config_path = APP_DIR / "config" / "calibrated_config.json"
        
        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_path}")
            return {}
            
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing {config_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error reading {config_path}: {e}")
            return {}

settings = Settings()
