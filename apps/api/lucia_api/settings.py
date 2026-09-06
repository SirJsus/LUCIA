from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# apps/api/lucia_api/settings.py -> lucia_api -> api -> apps -> raíz del repo.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SQLITE_PREFIX = "sqlite+aiosqlite:///"


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

    @model_validator(mode="after")
    def _anclar_sqlite_a_la_raiz_del_repo(self) -> "Settings":
        """Una ruta sqlite relativa apunta a un archivo distinto según el
        directorio desde el que arranque el proceso (`make up`, `alembic`,
        `pytest`...). Se ancla siempre a la raíz del repo para que todos —
        API, Alembic y tests — usen el mismo archivo."""
        if self.database_url.startswith(_SQLITE_PREFIX):
            raw_path = self.database_url.removeprefix(_SQLITE_PREFIX)
            if raw_path not in (":memory:", "") and not Path(raw_path).is_absolute():
                absolute = (_PROJECT_ROOT / raw_path).resolve()
                self.database_url = f"{_SQLITE_PREFIX}{absolute}"
        return self


settings = Settings()
