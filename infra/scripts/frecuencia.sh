#!/usr/bin/env bash
# Cambia cada cuanto despierta el agente sin volver a desplegar el codigo.
#   bash infra/scripts/frecuencia.sh "rate(5 minutes)"     -> acumular archivo
#   bash infra/scripts/frecuencia.sh "cron(0 6 * * ? *)"   -> ritmo diario
set -euo pipefail
[[ $# -eq 1 ]] || { echo 'uso: frecuencia.sh "<expresion>"'; exit 1; }

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PARAMS="$RAIZ/infra/params/prod.json"

python3 - "$1" <<'PY'
import json, sys
p = "infra/params/prod.json"
d = json.load(open(p))
d["Frecuencia"] = sys.argv[1]
json.dump(d, open(p, "w"), indent=2, ensure_ascii=False)
open(p, "a").write("\n")
print(f"frecuencia -> {sys.argv[1]}")
PY

bash "$RAIZ/infra/scripts/deploy.sh" prod
