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
# Sin GPU: backend blas. Con CUDA instalado, quita -Dblas y deja que Meson detecte cuda.
./build.sh release -Dblas=true -Dopenblas=true
popd >/dev/null
cp "$ENGINES/lc0/build/release/lc0" "$BIN/lc0"

echo "== Red por defecto de Lc0 =="
if [[ ! -f "$NETS/default.pb.gz" ]]; then
  # Red pequeña apta para CPU. Cambia la URL por una red T1/T2 grande si tienes GPU.
  curl -L -o "$NETS/default.pb.gz" "https://training.lczero.org/get_network?sha=$(
    curl -s 'https://training.lczero.org/networks/?show_all=0' | grep -oE 'sha=[0-9a-f]{64}' | head -1 | cut -d= -f2)"
fi

echo
echo "Listo:"
ls -la "$BIN" "$NETS"
"$BIN/stockfish" --help >/dev/null 2>&1 || true
