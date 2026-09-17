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
    lc0_backend: str = "blas"
    """Backend de cómputo de Lc0. Sin especificarlo, Lc0 elige uno por su
    cuenta y puede ser ~20x más lento (medido: 74 s contra ~4 s la misma
    búsqueda). "blas" va bien en CPU; con GPU NVIDIA, "cuda"."""
    analysis_depth: int = 18
    analysis_multipv: int = 3
    lichess_token: str = ""
    """Token de Lichess para el Opening Explorer (RF-3.6). Es obligatorio: el
    explorador responde 401 a cualquier petición anónima. Es gratuito y no
    necesita permisos: https://lichess.org/account/oauth/token"""
    lichess_user_agent: str = ""
    """Con qué se identifica LUCIA ante el Opening Explorer de Lichess
    (RF-3.6). Vacío usa el mismo que chess.com, que ya lleva contacto real: son
    dos servicios ajenos y la cortesía es la misma (RNF-10)."""
    explorer_min_interval_seconds: float = 1.0
    """Espera mínima entre consultas al explorador. La base de maestros es un
    servicio gratuito y aquí se le pregunta por muchas posiciones seguidas."""

    @model_validator(mode="after")
    def _anchor_relative_paths_to_repo_root(self) -> "Settings":
        """Una ruta relativa apunta a un sitio distinto según el directorio
        desde el que arranque el proceso (`make up`, `alembic`, `pytest`, un
        servicio de systemd...). Se anclan todas a la raíz del repo para que
        API, Alembic, worker y tests coincidan siempre."""
        if self.database_url.startswith(_SQLITE_PREFIX):
            raw_path = self.database_url.removeprefix(_SQLITE_PREFIX)
            if raw_path not in (":memory:", "") and not Path(raw_path).is_absolute():
                absolute = (_PROJECT_ROOT / raw_path).resolve()
                self.database_url = f"{_SQLITE_PREFIX}{absolute}"

        self.stockfish_path = _absolute_path(self.stockfish_path)
        self.lc0_path = _absolute_path(self.lc0_path)
        self.lc0_weights = _absolute_path(self.lc0_weights)
        return self


def _absolute_path(path: Path) -> Path:
    return path if path.is_absolute() else (_PROJECT_ROOT / path).resolve()


settings = Settings()
