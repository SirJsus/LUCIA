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

## Lc0: el backend y la red deciden si sirve o no

Lc0 evalúa una red neuronal en cada nodo, así que su velocidad depende por
completo de dónde corre esa red y de cuánto pesa. Medido en un portátil con
i7 y GTX 1060 (200 nodos sobre la posición inicial):

| Configuración | Tiempo |
|---|---|
| CPU (BLAS) + red de 313 MB | 80,3 s |
| CPU (BLAS) + red de 1,2 MB | 0,5 s |

Con la red grande en CPU, analizar una partida entera pasa de media hora y no
es utilizable; solo sirve para consultar posiciones sueltas.

- **La red** se elige en `.env` con `LC0_WEIGHTS`. `setup-engines.sh` descarga
  las dos: `default.pb.gz` (la última publicada, fuerte, pesada) y
  `maia-1500.pb.gz` (pequeña; imita a un humano de ~1500, así que evalúa
  distinto a un motor clásico y además sirve para el sparring de RF-4.3).
- **El backend** se elige en `.env` con `LC0_BACKEND` (`blas` en CPU, `cuda` u
  `opencl` con GPU). Sin especificarlo, Lc0 elige por su cuenta y puede ser
  ~20 veces más lento.

`setup-engines.sh` detecta el soporte de GPU al compilar: usa CUDA si
encuentra `nvcc`, si no OpenCL si están sus cabeceras, y si no se queda en
CPU. En Fedora, para habilitar OpenCL basta con:

```bash
sudo dnf install ocl-icd-devel opencl-headers
make engines   # recompila lc0, ahora con backend de GPU
```

`make doctor` dice en qué situación estás.

Cualquier otro motor UCI puede apuntarse desde `.env` sin tocar el código.
