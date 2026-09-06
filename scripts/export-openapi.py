#!/usr/bin/env python3
"""Vuelca el esquema OpenAPI de la API a un archivo, sin arrancar el servidor.

Se usa para generar los tipos TypeScript de `packages/shared-types`
(`make types`), y así el front y la API no pueden desincronizarse en
silencio: si un endpoint cambia de forma, el `tsc` del front falla.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "apps" / "api"))

from lucia_api.main import app  # noqa: E402

destino = pathlib.Path(__file__).resolve().parents[1] / "openapi.json"
destino.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n")
print(f"OpenAPI escrito en {destino}")
