import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    PROJECT_NAME: str = "StockAssure"
    VERSION: str = "0.5.0"
    DB_DIR: Path = BASE_DIR / "config"
    DATABASE_URL: str = f"sqlite:///{DB_DIR}/database.db"
    PLUGINS_DIR: Path = BASE_DIR / "plugins"
    Language: str = "Chinese Traditional"

settings = Settings()