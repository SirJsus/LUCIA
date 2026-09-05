#!/usr/bin/env bash
# Utilidades compartidas por los scripts de LUCIA.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -t 1 ]]; then
  C_RESET=$'\e[0m'; C_DIM=$'\e[2m'; C_BOLD=$'\e[1m'
  C_RED=$'\e[31m'; C_GREEN=$'\e[32m'; C_YELLOW=$'\e[33m'
  C_BLUE=$'\e[34m'; C_MAGENTA=$'\e[35m'; C_CYAN=$'\e[36m'
else
  C_RESET=""; C_DIM=""; C_BOLD=""; C_RED=""; C_GREEN=""; C_YELLOW=""; C_BLUE=""; C_MAGENTA=""; C_CYAN=""
fi

ok()   { printf "  %s✔%s %s\n" "$C_GREEN" "$C_RESET" "$*"; }
warn() { printf "  %s!%s %s\n" "$C_YELLOW" "$C_RESET" "$*"; }
fail() { printf "  %s✘%s %s\n" "$C_RED" "$C_RESET" "$*"; }
info() { printf "%s»%s %s\n" "$C_CYAN" "$C_RESET" "$*"; }
hr()   { printf "%s%s%s\n" "$C_DIM" "────────────────────────────────────────────────────────" "$C_RESET"; }

# Prefija cada línea de stdin con el nombre del servicio (estilo docker compose).
prefix() {
  local name="$1" color="$2"
  while IFS= read -r line; do
    printf "%s%-6s|%s %s\n" "$color" "$name" "$C_RESET" "$line"
  done
}
