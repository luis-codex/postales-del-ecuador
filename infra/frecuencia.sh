#!/usr/bin/env bash
# Cambia cada cuanto despierta el agente sin tocar el codigo ni los datos.
#   bash infra/frecuencia.sh "rate(5 minutes)"
#   bash infra/frecuencia.sh "cron(0 6 * * ? *)"
set -euo pipefail
[[ $# -eq 1 ]] || { echo 'uso: frecuencia.sh "<expresion>"'; exit 1; }

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRECUENCIA="$1"
source "$RAIZ/infra/config.sh"
source "$RAIZ/infra/lib.sh"
source "$RAIZ/infra/30-programacion.sh"

programacion::desplegar
