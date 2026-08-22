#!/usr/bin/env bash
# Despliega el stack completo. Uso: bash infra/scripts/deploy.sh [entorno]
# El entorno por defecto es "prod" y corresponde a infra/params/prod.json
set -euo pipefail

ENTORNO="${1:-prod}"
REGION="${REGION:-us-east-1}"
STACK="${STACK:-postales-del-ecuador}"

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PARAMS="$RAIZ/infra/params/${ENTORNO}.json"
[[ -f "$PARAMS" ]] || { echo "no existe $PARAMS"; exit 1; }

CUENTA="$(aws sts get-caller-identity --query Account --output text)"
ARTEFACTOS="postales-artefactos-${CUENTA}"

echo "== stack $STACK | entorno $ENTORNO | region $REGION"

# CloudFormation necesita un bucket donde subir el codigo y las plantillas hijas
if ! aws s3api head-bucket --bucket "$ARTEFACTOS" >/dev/null 2>&1; then
  echo "-- creando bucket de artefactos $ARTEFACTOS"
  aws s3api create-bucket --bucket "$ARTEFACTOS" --region "$REGION" >/dev/null
  aws s3api put-bucket-versioning --bucket "$ARTEFACTOS" \
    --versioning-configuration Status=Enabled
fi

echo "-- empaquetando codigo y plantillas anidadas"
aws cloudformation package \
  --template-file "$RAIZ/infra/main.yaml" \
  --s3-bucket "$ARTEFACTOS" \
  --s3-prefix "$STACK" \
  --output-template-file "$RAIZ/infra/.empaquetado.yaml" \
  --region "$REGION" >/dev/null

echo "-- desplegando"
# un elemento por parametro: los valores con espacios, como la expresion cron,
# tienen que llegar al CLI como un solo argumento
mapfile -t OVERRIDES < <(python3 -c "
import json
for k, v in json.load(open('$PARAMS')).items():
    print(f'{k}={v}')
")

aws cloudformation deploy \
  --template-file "$RAIZ/infra/.empaquetado.yaml" \
  --stack-name "$STACK" \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides "${OVERRIDES[@]}" \
  --no-fail-on-empty-changeset \
  --region "$REGION"

BUCKET="$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='Bucket'].OutputValue" --output text)"

echo "-- subiendo la web"
aws s3 cp "$RAIZ/web/index.html" "s3://${BUCKET}/index.html" \
  --content-type "text/html; charset=utf-8" --cache-control "no-cache, max-age=0" >/dev/null

echo
aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[].[OutputKey,OutputValue]" --output table
