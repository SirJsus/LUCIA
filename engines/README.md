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

| Configuración | Velocidad |
|---|---|
| CPU (BLAS) + red grande transformer (313 MB) | 2,5 nodos/s (200 nodos en 80,3 s) |
| OpenCL + red grande transformer | **no soportada**: OpenCL solo acepta redes convolucionales |
| OpenCL + red convolucional T74 (6 MB) | ~4.000 nodos/s |
| OpenCL + red Maia (1 MB) | ~12.500 nodos/s |

Con la red grande en CPU, analizar una partida entera pasa de media hora y no
es utilizable; solo sirve para consultar posiciones sueltas.

- **La red** se elige en `.env` con `LC0_WEIGHTS`. `setup-engines.sh` descarga
  **tres**: `744706-conv.pb.gz` (convolucional de la serie T74, **la
  recomendada**: fuerte y compatible con OpenCL, y la que trae `.env.example`),
  `default.pb.gz` (la última publicada, la más fuerte, pero transformer: solo
  sirve con CUDA) y `maia-1500.pb.gz` (imita a un humano de ~1500, así que
  evalúa distinto a un motor clásico; sirve para el sparring de RF-4.3, no
  como segunda opinión de RF-2.6).
- **El backend se deja vacío**, que es el defecto de `LC0_BACKEND`. Vacío no
  lo deja sin backend: hace que Lc0 elija entre los que `setup-engines.sh` le
  compiló en esta máquina, y elige bien. Medido con la red T74, 3.000 nodos
  desde la posición inicial en una GTX 1060: **vacío 1,23 s**, `opencl` 1,12 s,
  `blas` 14,88 s. Fijarlo a mano solo compensa si se sabe más que Lc0 sobre la
  máquina concreta, y tiene un riesgo: pedirle un backend que no compiló aborta
  el arranque (`invalid value for combo option 'Backend'`).

`setup-engines.sh` detecta el soporte de GPU al compilar: usa CUDA si
encuentra `nvcc`, si no OpenCL si están sus cabeceras, y si no se queda en
CPU. En Fedora, para habilitar OpenCL basta con:

```bash
sudo dnf install ocl-icd-devel opencl-headers
make engines   # recompila lc0, ahora con backend de GPU
```

`make doctor` dice en qué situación estás.

Cualquier otro motor UCI habla con el núcleo sin tocarlo (RNF-9,
[ADR-0015](../docs/adr/0015-cada-motor-con-su-unidad-de-esfuerzo-y-sus-opciones.md)):
`EngineBridge` le manda solo las opciones que el propio motor declara. Para que
además aparezca en la aplicación hacen falta dos líneas fuera del núcleo: su
ruta en `.env` y su nombre en `ENGINE_NAMES`
(`apps/api/lucia_api/services/engines.py`).
