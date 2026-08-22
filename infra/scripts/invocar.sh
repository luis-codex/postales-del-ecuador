#!/usr/bin/env bash
# Despierta al agente a mano y muestra sus logs. Util para probar cambios.
set -euo pipefail
REGION="${REGION:-us-east-1}"
SALIDA="$(mktemp)"
aws lambda invoke --function-name postales-del-ecuador --region "$REGION" \
  --cli-binary-format raw-in-base64-out --payload '{}' \
  --log-type Tail --query LogResult --output text "$SALIDA" | base64 -d
echo "--- respuesta ---"
cat "$SALIDA"; echo
rm -f "$SALIDA"
