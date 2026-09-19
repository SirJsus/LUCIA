#!/usr/bin/env bash
# Añade los submódulos de Stockfish y Lc0 (si no existen), los compila a engines/bin/
# y descarga una red por defecto para Lc0.
#
# Requisitos en Fedora:
#   sudo dnf install git make gcc-c++ meson ninja-build openblas-devel zlib-devel
#   (GPU NVIDIA opcional para Lc0: cuda-toolkit)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENGINES="$ROOT/engines"
BIN="$ENGINES/bin"
NETS="$ENGINES/networks"

STOCKFISH_TAG="${STOCKFISH_TAG:-sf_17.1}"
LC0_TAG="${LC0_TAG:-v0.31.2}"
# Detecta arquitectura para Stockfish (avx512 > bmi2 > avx2 > modern)
SF_ARCH="${SF_ARCH:-}"
if [[ -z "$SF_ARCH" ]]; then
  if grep -q avx512 /proc/cpuinfo; then SF_ARCH=x86-64-avx512
  elif grep -q bmi2 /proc/cpuinfo; then SF_ARCH=x86-64-bmi2
  elif grep -q avx2 /proc/cpuinfo; then SF_ARCH=x86-64-avx2
  else SF_ARCH=x86-64; fi
fi

mkdir -p "$BIN" "$NETS"

add_submodule() {
  local path="$1" url="$2" tag="$3"
  if [[ ! -f "$path/.git" && ! -d "$path/.git" ]]; then
    echo ">> Añadiendo submódulo $url en $path"
    git -C "$ROOT" submodule add "$url" "${path#$ROOT/}"
  fi
  git -C "$ROOT" submodule update --init --recursive "${path#$ROOT/}"
  git -C "$path" fetch --tags --quiet
  git -C "$path" checkout --quiet "$tag"
}

echo "== Stockfish ($STOCKFISH_TAG, ARCH=$SF_ARCH) =="
add_submodule "$ENGINES/stockfish" https://github.com/official-stockfish/Stockfish.git "$STOCKFISH_TAG"
make -C "$ENGINES/stockfish/src" -j"$(nproc)" profile-build ARCH="$SF_ARCH"
cp "$ENGINES/stockfish/src/stockfish" "$BIN/stockfish"

echo "== Lc0 ($LC0_TAG) =="
add_submodule "$ENGINES/lc0" https://github.com/LeelaChessZero/lc0.git "$LC0_TAG"
pushd "$ENGINES/lc0" >/dev/null
LC0_BUILDDIR="build/release"

# El backend decide si Lc0 es utilizable o no: en CPU cada evaluación de la red
# es lentísima (medido: 200 nodos en 80 s con una red grande), y en GPU es de
# otro orden. Se compila con lo que haya disponible, de más rápido a menos.
LC0_OPTS=(-Dblas=true -Dopenblas=true)  # CPU: siempre, como respaldo
LC0_GPU="ninguna (solo CPU)"

if [[ -n "${LC0_FORCE_CPU:-}" ]]; then
  LC0_GPU="forzado a CPU por LC0_FORCE_CPU"
elif command -v nvcc >/dev/null 2>&1; then
  # CUDA es lo más rápido en tarjetas NVIDIA, pero necesita el toolkit entero.
  LC0_OPTS+=(-Dcudnn=true)
  LC0_GPU="CUDA (nvcc encontrado)"
elif [[ -e /etc/OpenCL/vendors/nvidia.icd || -n "$(ls /etc/OpenCL/vendors/*.icd 2>/dev/null)" ]] \
     && pkg-config --exists OpenCL 2>/dev/null; then
  # OpenCL: mucho más ligero de instalar que CUDA (en Fedora basta
  # `sudo dnf install ocl-icd-devel opencl-headers`) y ya aprovecha la GPU.
  LC0_OPTS+=(-Dopencl=true)
  LC0_GPU="OpenCL"
elif [[ -e /etc/OpenCL/vendors/nvidia.icd ]]; then
  echo ">> Hay una GPU con OpenCL, pero faltan las cabeceras para compilarlo."
  echo "   En Fedora: sudo dnf install ocl-icd-devel opencl-headers"
  echo "   Después vuelve a ejecutar este script para recompilar con GPU."
fi
echo ">> Backend de GPU para Lc0: $LC0_GPU"

if [[ -f "$LC0_BUILDDIR/build.ninja" ]]; then
  meson configure "$LC0_BUILDDIR" -Dbuildtype=release "${LC0_OPTS[@]}"
else
  meson setup "$LC0_BUILDDIR" --buildtype release "${LC0_OPTS[@]}"
fi
# Solo el binario `lc0`, no los tests empaquetados: traen un googletest 1.10.0
# (2020) que no compila con GCC recientes (falta <cstdint> para uintptr_t en
# gtest-death-test.cc) y no los necesitamos para tener el motor.
meson compile -C "$LC0_BUILDDIR" lc0
popd >/dev/null
cp "$ENGINES/lc0/$LC0_BUILDDIR/lc0" "$BIN/lc0"

echo "== Redes de Lc0 =="
# Se descargan tres, porque la red —su tamaño y su arquitectura— decide si Lc0
# es usable y para qué:
#
#   default.pb.gz  la última red publicada (~300 MB). Fuerte, pero en CPU cada
#                  evaluación es lentísima. Medido en un i7 con BLAS: 200 nodos
#                  en 80 s. Solo tiene sentido con GPU (LC0_BACKEND=cuda).
#   744706-conv.pb.gz  red convolucional de la serie T74 (~6 MB). Es la
#                  recomendada por defecto: fuerte de verdad y —a diferencia de
#                  la anterior— compatible con el backend OpenCL, que solo
#                  acepta redes convolucionales, no las transformer modernas.
#                  Medido en una GTX 1060 por OpenCL: ~4.000 nodos/s.
#   maia-1500.pb.gz  red de 6x64 (~1 MB), la más rápida (~12.500 nodos/s en esa
#                  misma GPU). Es de la familia Maia, entrenada para jugar como
#                  un humano de ~1500: evalúa distinto a un motor clásico, lo
#                  que la hace mala como "verdad absoluta" y buena para el
#                  sparring humano de la fase 3 (RF-4.3).
#
# Cuál usar se elige en .env con LC0_WEIGHTS.
if [[ ! -f "$NETS/default.pb.gz" ]]; then
  curl -L -o "$NETS/default.pb.gz" "https://training.lczero.org/get_network?sha=$(
    curl -s 'https://training.lczero.org/networks/?show_all=0' | grep -oE 'sha=[0-9a-f]{64}' | head -1 | cut -d= -f2)"
fi
if [[ ! -f "$NETS/744706-conv.pb.gz" ]]; then
  curl -L -o "$NETS/744706-conv.pb.gz" \
    "https://storage.lczero.org/files/networks-contrib/744706.pb.gz"
fi
if [[ ! -f "$NETS/maia-1500.pb.gz" ]]; then
  curl -L -o "$NETS/maia-1500.pb.gz" \
    "https://github.com/CSSLab/maia-chess/raw/master/maia_weights/maia-1500.pb.gz"
fi

echo
echo "Listo:"
ls -la "$BIN" "$NETS"
"$BIN/stockfish" --help >/dev/null 2>&1 || true
