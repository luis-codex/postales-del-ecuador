#!/usr/bin/env bash
# Muestra la evidencia de que el agente corre solo: cada vez que ha despertado
# y quien lo desperto.
set -euo pipefail
REGION="${REGION:-us-east-1}"
aws logs filter-log-events \
  --log-group-name /aws/lambda/postales-del-ecuador --region "$REGION" \
  --filter-pattern '"[agente] despierta"' \
  --query 'events[].message' --output text | tr '\t' '\n' | grep -v '^$'
