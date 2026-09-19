"""lucia-lichess: cliente del Opening Explorer de Lichess.

Necesita un token de Lichess (gratuito, sin permisos especiales): el explorador
dejó de admitir peticiones anónimas.
"""

from .client import LichessExplorerAuthError, LichessExplorerClient, LichessExplorerError
from .models import ExplorerMove, ExplorerPosition

__all__ = [
    "LichessExplorerClient",
    "LichessExplorerError",
    "LichessExplorerAuthError",
    "ExplorerMove",
    "ExplorerPosition",
]
