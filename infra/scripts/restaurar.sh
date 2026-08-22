#!/usr/bin/env bash
# Restaura la memoria del agente desde un volcado de infra/backup/.
#   bash infra/scripts/restaurar.sh infra/backup/postales-YYYYMMDD-HHMM.json
set -euo pipefail
[[ $# -eq 1 ]] || { echo "uso: restaurar.sh <archivo-de-respaldo.json>"; exit 1; }
REGION="${REGION:-us-east-1}"
TABLA="${TABLA:-postales-del-ecuador-historial}"

python3 - "$1" "$TABLA" "$REGION" <<'PY'
import json, subprocess, sys

respaldo, tabla, region = sys.argv[1], sys.argv[2], sys.argv[3]
items = json.load(open(respaldo))["Items"]

# BatchWriteItem acepta como mucho 25 elementos por llamada
for i in range(0, len(items), 25):
    lote = {tabla: [{"PutRequest": {"Item": it}} for it in items[i:i + 25]]}
    subprocess.run(
        ["aws", "dynamodb", "batch-write-item", "--region", region,
         "--request-items", json.dumps(lote)],
        check=True, stdout=subprocess.DEVNULL)
    print(f"  restauradas {min(i + 25, len(items))}/{len(items)}")
PY
