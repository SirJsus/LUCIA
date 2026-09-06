"""Fixtures compartidas de `lucia-core`: ruta al binario real de Stockfish
para los tests que necesitan un motor de verdad, no un doble."""

from __future__ import annotations

from pathlib import Path

import pytest

# packages/core/tests/conftest.py -> tests -> core -> packages -> raíz del repo.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
STOCKFISH_PATH = _PROJECT_ROOT / "engines" / "bin" / "stockfish"

requiere_stockfish = pytest.mark.skipif(
    not STOCKFISH_PATH.exists(),
    reason="Stockfish no está compilado; ejecuta 'make engines' para correr estos tests.",
)
