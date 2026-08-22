#!/usr/bin/env bash
# Despliega Postales del Ecuador. Uso: bash infra/scripts/deploy.sh [entorno]
#
# No necesita SAM CLI: una plantilla SAM es CloudFormation con un transform,
# y el AWS CLI la expande en el servidor con CAPABILITY_AUTO_EXPAND.
set -euo pipefail

ENTORNO="${1:-prod}"
REGION="${REGION:-us-east-1}"
STACK="${STACK:-postales-del-ecuador}"

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PARAMS="$RAIZ/infra/params/${ENTORNO}.json"
[[ -f "$PARAMS" ]] || { echo "no existe $PARAMS"; exit 1; }

echo "== stack $STACK | entorno $ENTORNO | region $REGION"

# 1. El bucket de artefactos tambien es IaC: su propio stack, desplegado antes
#    que nada porque CloudFormation necesita donde subir el codigo.
echo "-- [1/4] bootstrap"
aws cloudformation deploy \
  --template-file "$RAIZ/infra/bootstrap.yaml" \
  --stack-name "${STACK}-bootstrap" \
  --no-fail-on-empty-changeset \
  --region "$REGION" >/dev/null

ARTEFACTOS="$(aws cloudformation describe-stacks --stack-name "${STACK}-bootstrap" \
  --region "$REGION" --query "Stacks[0].Outputs[?OutputKey=='Bucket'].OutputValue" --output text)"
echo "   artefactos en $ARTEFACTOS"

# 2. Sube el codigo de la Lambda y reescribe CodeUri con la ruta real en S3
echo "-- [2/4] empaquetando"
aws cloudformation package \
  --template-file "$RAIZ/infra/template.yaml" \
  --s3-bucket "$ARTEFACTOS" \
  --s3-prefix "$STACK" \
  --output-template-file "$RAIZ/infra/.empaquetado.yaml" \
  --region "$REGION" >/dev/null

# 3. Un elemento por parametro: los valores con espacios, como la expresion
#    cron, tienen que llegar al CLI como un solo argumento.
mapfile -t OVERRIDES < <(python3 -c "
import json
for k, v in json.load(open('$PARAMS')).items():
    print(f'{k}={v}')
")

echo "-- [3/4] desplegando"
aws cloudformation deploy \
  --template-file "$RAIZ/infra/.empaquetado.yaml" \
  --stack-name "$STACK" \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
  --parameter-overrides "${OVERRIDES[@]}" \
  --tags proyecto=postales-del-ecuador entorno="$ENTORNO" gestionado-por=cloudformation \
  --no-fail-on-empty-changeset \
  --region "$REGION"

BUCKET="$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='Bucket'].OutputValue" --output text)"

echo "-- [4/4] publicando la web"
aws s3 cp "$RAIZ/web/index.html" "s3://${BUCKET}/index.html" \
  --content-type "text/html; charset=utf-8" --cache-control "no-cache, max-age=0" >/dev/null

echo
aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[].[OutputKey,OutputValue]" --output table
