# engines/

Motores de ajedrez como **sub-módulos git** (ver [ADR-0002](../docs/adr/0002-motores-como-submodulos.md)).

| Directorio | Upstream | Licencia | Build |
| ------------ | ---------- | ---------- | ------- |
| `stockfish/` | <https://github.com/official-stockfish/Stockfish> | GPL-3.0 | `make -C src -j build ARCH=x86-64-avx2` |
| `lc0/` | <https://github.com/LeelaChessZero/lc0> | GPL-3.0 | `./build.sh` (Meson + Ninja) |

Los sub-módulos se añaden y compilan con:

```bash
./scripts/setup-engines.sh
```

Salida (ignorada por git):

- `engines/bin/stockfish`, `engines/bin/lc0`
- `engines/networks/*.pb.gz` — redes de Lc0 (por defecto una red pequeña de lczero.org; opcionalmente Maia para sparring humano).

Cualquier otro motor UCI puede apuntarse desde `.env` sin tocar el código.
