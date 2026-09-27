#!/usr/bin/env bash
# Levanta el entorno de desarrollo nativo con logs unificados, al estilo `docker compose up`.
#
# Uso:
#   ./scripts/dev.sh              # api + web
#   ./scripts/dev.sh api          # solo api
#   ./scripts/dev.sh web          # solo web
#   ./scripts/dev.sh --no-install # no ejecutar uv sync / pnpm install aunque falten
#
# API_PORT cambia el puerto de la API (8000 por defecto); el proxy del front lo
# lee de la misma variable, así que basta con exportarla una vez:
#   API_PORT=8001 ./scripts/dev.sh
#
# Ctrl+C apaga todos los servicios. Los logs también se guardan en data/logs/.
set -uo pipefail
source "$(dirname "$0")/lib.sh"
cd "$ROOT"

API_PORT="${API_PORT:-8000}"
export API_PORT  # lo lee también el proxy de vite (apps/web/vite.config.ts)

SERVICES=()
INSTALL=1
for arg in "$@"; do
  case "$arg" in
    api|web) SERVICES+=("$arg") ;;
    --no-install) INSTALL=0 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "argumento desconocido: $arg"; exit 2 ;;
  esac
done
[[ ${#SERVICES[@]} -eq 0 ]] && SERVICES=(api web)

printf "%sL.U.C.I.A. · dev%s  servicios: %s\n" "$C_BOLD" "$C_RESET" "${SERVICES[*]}"; hr

# 1. Prerrequisitos (solo los de los servicios pedidos; `make doctor` da el informe completo)
MISSING=0
require() { command -v "$1" >/dev/null 2>&1 || { fail "falta '$1' para el servicio $2. Ejecuta 'make doctor'."; MISSING=1; }; }
[[ " ${SERVICES[*]} " == *" api "* ]] && require uv api
[[ " ${SERVICES[*]} " == *" web "* ]] && { require node web; require pnpm web; }
[[ $MISSING -eq 1 ]] && exit 1

# El puerto ocupado daba un "Address already in use" de uvicorn sin decir por
# quién, y en una máquina con varios proyectos eso puede ser cualquier cosa.
if [[ " ${SERVICES[*]} " == *" api "* ]] && (ss -ltn 2>/dev/null || netstat -ltn 2>/dev/null) | grep -qE "[:.]${API_PORT}[[:space:]]"; then
  fail "el puerto ${API_PORT} ya está ocupado."
  culpable=$(docker ps --format '{{.Names}}\t{{.Ports}}' 2>/dev/null | grep ":${API_PORT}->" | cut -f1)
  [[ -n "$culpable" ]] && info "lo tiene el contenedor '${culpable}'; párralo o usa otro puerto."
  info "para levantar LUCIA en otro puerto: API_PORT=8001 make up"
  exit 1
fi

# 2. Configuración y dependencias
[[ -f .env ]] || { cp .env.example .env; info "creado .env desde .env.example (edítalo con tu usuario de chess.com)"; }
mkdir -p data/logs

if [[ $INSTALL -eq 1 ]]; then
  if [[ " ${SERVICES[*]} " == *" api "* && ! -d .venv ]]; then
    info "instalando dependencias Python (uv sync)"; uv sync --all-packages --all-extras 2>&1 | prefix "uv" "$C_MAGENTA"
  fi
  if [[ " ${SERVICES[*]} " == *" web "* && ! -d node_modules ]]; then
    info "instalando dependencias JS (pnpm install)"; pnpm install 2>&1 | prefix "pnpm" "$C_MAGENTA"
  fi
fi

# 3. Motores: aviso, no bloqueo
[[ -x engines/bin/stockfish ]] || warn "Stockfish no compilado: la API arranca pero no analizará. Ejecuta 'make engines'."

# 4. Arranque de servicios en grupos de proceso propios (para matarlos limpiamente)
declare -A PIDS
start() {
  local name="$1" color="$2" cmd="$3"
  local log="data/logs/$name.log"
  setsid bash -c "$cmd" > >(tee -a "$log" | prefix "$name" "$color") 2>&1 &
  PIDS[$name]=$!
  info "$name iniciado (pid ${PIDS[$name]}, log $log)"
}

shutdown() {
  echo; info "apagando..."
  for name in "${!PIDS[@]}"; do
    kill -TERM -- -"${PIDS[$name]}" 2>/dev/null && ok "$name detenido"
  done
  wait 2>/dev/null
  exit 0
}
trap shutdown INT TERM

for s in "${SERVICES[@]}"; do
  case "$s" in
    api) start api "$C_BLUE"  "uv run --package lucia-api uvicorn lucia_api.main:app --reload --port ${API_PORT}" ;;
    web) start web "$C_GREEN" "pnpm --filter @lucia/web dev" ;;
  esac
done

hr
[[ " ${SERVICES[*]} " == *" api "* ]] && printf "  API   → %shttp://localhost:${API_PORT}/docs%s\n" "$C_BOLD" "$C_RESET"
[[ " ${SERVICES[*]} " == *" web "* ]] && printf "  Web   → %shttp://localhost:5173%s\n" "$C_BOLD" "$C_RESET"
printf "  Ctrl+C para apagar todo\n"; hr

# 5. Si un servicio muere, avisar y apagar el resto
while true; do
  for name in "${!PIDS[@]}"; do
    if ! kill -0 "${PIDS[$name]}" 2>/dev/null; then
      fail "$name terminó inesperadamente (ver data/logs/$name.log)"
      unset "PIDS[$name]"
      shutdown
    fi
  done
  sleep 1
done
