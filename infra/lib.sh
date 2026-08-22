#!/usr/bin/env bash
# Utilidades compartidas. Se carga con "source".
#
# La diferencia grande entre bash y una herramienta declarativa es que la
# idempotencia hay que escribirla. Estos helpers son justamente eso: la
# respuesta a "¿esto ya existe?" repetida para cada tipo de recurso.

paso()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
info()  { printf '   %s\n' "$*"; }
ok()    { printf '   \033[32m✓\033[0m %s\n' "$*"; }
salta() { printf '   \033[90m·\033[0m %s\n' "$*"; }
malo()  { printf '   \033[31m✗\033[0m %s\n' "$*" >&2; }

# existe <comando aws...>  ->  0 si el recurso ya esta
existe() { "$@" >/dev/null 2>&1; }

# dormir <segundos>  (sin depender de sleep)
dormir() { python3 -c "import time,sys; time.sleep(float(sys.argv[1]))" "$1"; }

# reintentar <intentos> <segundos> <comando...>
# IAM tarda unos segundos en propagar; sin esto, la Lambda falla al crearse.
reintentar() {
  local intentos=$1 espera=$2; shift 2
  local i
  for ((i = 1; i <= intentos; i++)); do
    if "$@" >/dev/null 2>&1; then return 0; fi
    [[ $i -lt $intentos ]] && { info "reintento $i/$intentos…"; dormir "$espera"; }
  done
  return 1
}
