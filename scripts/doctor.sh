#!/usr/bin/env bash
# Diagnóstico del entorno de desarrollo: qué hay, qué falta y cómo arreglarlo.
# Uso: ./scripts/doctor.sh   (o `make doctor`)
# Sale con 1 si falta algo imprescindible para `make up`.
set -uo pipefail
source "$(dirname "$0")/lib.sh"
cd "$ROOT"

MISSING=0
need() { # need <cmd> <cómo instalar> [opcional]
  if command -v "$1" >/dev/null 2>&1; then
    ok "$1 $(${1} --version 2>/dev/null | head -1 | sed 's/^/(/;s/$/)/')"
  elif [[ "${3:-}" == "opcional" ]]; then
    warn "$1 no encontrado (opcional). $2"
  else
    fail "$1 no encontrado. $2"; MISSING=1
  fi
}

printf "%sL.U.C.I.A. · doctor%s\n" "$C_BOLD" "$C_RESET"; hr
info "Toolchain"
need git    "sudo dnf install git"
need python3 "sudo dnf install python3"
need uv     "curl -LsSf https://astral.sh/uv/install.sh | sh   (luego reabre la terminal)"
need node   "sudo dnf install nodejs"
need pnpm   "npm install -g pnpm"
need g++    "sudo dnf install gcc-c++ make" 
need make   "sudo dnf install make"
need meson  "sudo dnf install meson ninja-build openblas-devel zlib-devel   (solo para compilar Lc0)" opcional
need docker "solo si quieres usar infra/docker" opcional

echo; info "Configuración"
if [[ -f .env ]]; then ok ".env presente"; else warn ".env no existe (make up lo crea desde .env.example)"; fi

echo; info "Dependencias"
if [[ -d .venv ]]; then ok "Python: .venv presente"; else warn "Python: falta .venv (make up ejecuta 'uv sync')"; fi
if [[ -d node_modules ]]; then ok "JS: node_modules presente"; else warn "JS: falta node_modules (make up ejecuta 'pnpm install')"; fi

echo; info "GPU para Lc0 (opcional, pero decide si Lc0 es usable)"
if [[ -x engines/bin/lc0 ]]; then
  backends=$(printf "uci\nquit\n" | ./engines/bin/lc0 2>/dev/null | grep -i "option name Backend " || true)
  if echo "$backends" | grep -qiE "cuda|opencl"; then
    ok "lc0 compilado con soporte de GPU"
  elif [[ -e /etc/OpenCL/vendors/nvidia.icd ]]; then
    if pkg-config --exists OpenCL 2>/dev/null; then
      warn "hay GPU y cabeceras OpenCL, pero lc0 se compiló sin ellas: re-ejecuta 'make engines'"
    else
      warn "hay GPU pero faltan cabeceras: sudo dnf install ocl-icd-devel opencl-headers && make engines"
    fi
  else
    warn "lc0 solo con backend de CPU; con la red grande será demasiado lento"
  fi
else
  warn "lc0 sin compilar; no se puede comprobar el soporte de GPU"
fi

echo; info "Motores (engines/bin)"
for e in stockfish lc0; do
  if [[ -x "engines/bin/$e" ]]; then
    ok "$e listo"
  else
    warn "$e no compilado. Ejecuta: make engines   (la API arranca sin motores, pero no podrá analizar)"
  fi
done
if [[ -f engines/networks/default.pb.gz ]]; then ok "red Lc0 presente"; else warn "sin red Lc0 (make engines la descarga)"; fi

echo; hr
if [[ $MISSING -eq 0 ]]; then
  printf "%sTodo lo imprescindible está listo. Ejecuta: make up%s\n" "$C_GREEN" "$C_RESET"
else
  printf "%sFaltan herramientas imprescindibles (ver ✘ arriba).%s\n" "$C_RED" "$C_RESET"
fi
exit $MISSING
