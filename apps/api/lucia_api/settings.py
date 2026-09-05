from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    chesscom_username: str = ""
    chesscom_user_agent: str = "LUCIA/0.1"
    database_url: str = "sqlite+aiosqlite:///./data/lucia.db"
    stockfish_path: Path = Path("./engines/bin/stockfish")
    lc0_path: Path = Path("./engines/bin/lc0")
    lc0_weights: Path = Path("./engines/networks/default.pb.gz")
    analysis_depth: int = 18
    analysis_multipv: int = 3


settings = Settings()
