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
    lc0_weights: Path = Path("./engines/networks/744706-conv.pb.gz")
    """Red neuronal de Lc0. La T74 convolucional que descarga
    `scripts/setup-engines.sh`, que es la recomendada del proyecto: fuerte y
    aceptada por OpenCL. El defecto era `default.pb.gz` —la red grande, de
    arquitectura transformer—, que OpenCL rechaza y en CPU da 2,5 nodos/s, así
    que quien clonara el repo sin copiar `.env` tenía un Lc0 inservible."""

    lc0_backend: str = ""
    """Backend de cómputo de Lc0. **Vacío a propósito: es el mejor defecto.**

    Vacío no significa "sin backend": significa no mandarle la opción, y
    entonces Lc0 elige entre los que tenga compilados —que son los que el
    instalador detectó en la máquina: CUDA si había `nvcc`, si no OpenCL, si no
    CPU—. Elige bien, y forzar uno por nombre solo puede empeorarlo: pedirle
    uno que no compiló es un error duro (`invalid value for combo option
    'Backend'`), que es lo que le pasaría a `cuda` en una máquina sin CUDA.

    Medido con la red T74, 3.000 nodos desde la posición inicial, en una GTX
    1060: sin especificar 1,23 s; `opencl` 1,12 s; `blas` 14,88 s. O sea que el
    defecto anterior, `blas`, era **doce veces más lento** que dejar elegir a
    Lc0, y la advertencia que este comentario traía —"sin especificarlo puede
    ser ~20x más lento"— atribuía al backend lo que en realidad costaba la red
    transformer.

    Se sigue pudiendo forzar desde `.env` (`LC0_BACKEND`) cuando se sepa más
    que Lc0 sobre la máquina concreta."""

    maia_weights: Path = Path("./engines/networks/maia-1500.pb.gz")
    """Red de Lc0 para el sparring (RF-4.3), aparte de la de análisis.

    Maia está entrenada para **predecir la jugada de un humano** de cierto
    nivel, no para buscar la mejor: eso la hace un rival de estilo humano y
    una mala fuente de verdad, así que no puede ser la misma red con la que se
    analiza. `scripts/setup-engines.sh` descarga la de ~1500, que es la que
    trae este valor por defecto; cambiarla por otra de la familia (1100 a
    1900) es cambiar la fuerza del rival de Lc0."""

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
        self.maia_weights = _absolute_path(self.maia_weights)
        return self


def _absolute_path(path: Path) -> Path:
    return path if path.is_absolute() else (_PROJECT_ROOT / path).resolve()


settings = Settings()
