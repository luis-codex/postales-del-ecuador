#!/usr/bin/env bash
# Despliega "Postales del Ecuador" completo con AWS CLI. Idempotente.
set -euo pipefail

REGION="${REGION:-us-east-1}"
PROYECTO="postales-del-ecuador"
TABLA="postales-historial"
ROL_LAMBDA="postales-lambda-role"
ROL_SCHEDULER="postales-scheduler-role"
SCHEDULE="postales-diarias"
MODELO="${MODELO:-amazon.nova-pro-v1:0}"
FRECUENCIA="${FRECUENCIA:-rate(20 minutes)}"

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$RAIZ/infra/.env"
CUENTA="$(aws sts get-caller-identity --query Account --output text)"

# El nombre del bucket es global: se genera una vez y se reutiliza siempre
if [[ -f "$ENV_FILE" ]]; then source "$ENV_FILE"; fi
if [[ -z "${BUCKET:-}" ]]; then
  BUCKET="${PROYECTO}-$(head -c4 /dev/urandom | od -An -tx1 | tr -d ' \n')"
  echo "BUCKET=$BUCKET" > "$ENV_FILE"
fi

echo "== cuenta $CUENTA | region $REGION | bucket $BUCKET | modelo $MODELO"

espera() { python3 -c "import time,sys; time.sleep(float(sys.argv[1]))" "$1"; }

# ---------------------------------------------------------------- 1. rol IAM
echo "-- [1/6] rol IAM de la Lambda"
if ! aws iam get-role --role-name "$ROL_LAMBDA" >/dev/null 2>&1; then
  aws iam create-role --role-name "$ROL_LAMBDA" \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' \
    >/dev/null
  echo "   rol creado"
else
  echo "   ya existia"
fi

aws iam put-role-policy --role-name "$ROL_LAMBDA" --policy-name "postales-permisos" \
  --policy-document "$(cat <<JSON
{"Version":"2012-10-17","Statement":[
 {"Effect":"Allow","Action":["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],
  "Resource":"arn:aws:logs:${REGION}:${CUENTA}:*"},
 {"Effect":"Allow","Action":["bedrock:InvokeModel"],"Resource":"*"},
 {"Effect":"Allow","Action":["dynamodb:PutItem","dynamodb:Scan","dynamodb:GetItem","dynamodb:Query"],
  "Resource":"arn:aws:dynamodb:${REGION}:${CUENTA}:table/${TABLA}"},
 {"Effect":"Allow","Action":["s3:PutObject"],"Resource":"arn:aws:s3:::${BUCKET}/*"}
]}
JSON
)"
echo "   permisos aplicados"

# ------------------------------------------------------------- 2. dynamodb
echo "-- [2/6] tabla DynamoDB"
if ! aws dynamodb describe-table --table-name "$TABLA" --region "$REGION" >/dev/null 2>&1; then
  aws dynamodb create-table --table-name "$TABLA" --region "$REGION" \
    --attribute-definitions AttributeName=id,AttributeType=S \
    --key-schema AttributeName=id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST >/dev/null
  aws dynamodb wait table-exists --table-name "$TABLA" --region "$REGION"
  echo "   tabla creada"
else
  echo "   ya existia"
fi

# -------------------------------------------------------------------- 3. s3
echo "-- [3/6] bucket S3 + web estatica"
if ! aws s3api head-bucket --bucket "$BUCKET" >/dev/null 2>&1; then
  aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" >/dev/null
  echo "   bucket creado"
else
  echo "   ya existia"
fi

aws s3api put-public-access-block --bucket "$BUCKET" \
  --public-access-block-configuration \
  "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

aws s3api put-bucket-policy --bucket "$BUCKET" --policy "$(cat <<JSON
{"Version":"2012-10-17","Statement":[
 {"Sid":"LecturaPublica","Effect":"Allow","Principal":"*","Action":"s3:GetObject",
  "Resource":"arn:aws:s3:::${BUCKET}/*"}]}
JSON
)"

aws s3api put-bucket-website --bucket "$BUCKET" \
  --website-configuration '{"IndexDocument":{"Suffix":"index.html"},"ErrorDocument":{"Key":"index.html"}}'

aws s3 cp "$RAIZ/web/index.html" "s3://$BUCKET/index.html" \
  --content-type "text/html; charset=utf-8" --cache-control "no-cache, max-age=0" >/dev/null
echo "   web subida"

# ---------------------------------------------------------------- 4. lambda
echo "-- [4/6] Lambda"
TMP="$(mktemp -d)"
cp "$RAIZ/src/handler.py" "$RAIZ/src/lugares.py" "$TMP/"
(cd "$TMP" && zip -q -r funcion.zip handler.py lugares.py)

if aws lambda get-function --function-name "$PROYECTO" --region "$REGION" >/dev/null 2>&1; then
  aws lambda update-function-code --function-name "$PROYECTO" --region "$REGION" \
    --zip-file "fileb://$TMP/funcion.zip" >/dev/null
  aws lambda wait function-updated --function-name "$PROYECTO" --region "$REGION"
  aws lambda update-function-configuration --function-name "$PROYECTO" --region "$REGION" \
    --timeout 120 --memory-size 512 \
    --environment "Variables={TABLE_NAME=$TABLA,BUCKET_NAME=$BUCKET,MODEL_ID=$MODELO}" >/dev/null
  aws lambda wait function-updated --function-name "$PROYECTO" --region "$REGION"
  echo "   codigo actualizado"
else
  for intento in 1 2 3 4 5 6; do
    if aws lambda create-function --function-name "$PROYECTO" --region "$REGION" \
        --runtime python3.12 --handler handler.lambda_handler \
        --role "arn:aws:iam::${CUENTA}:role/${ROL_LAMBDA}" \
        --zip-file "fileb://$TMP/funcion.zip" \
        --timeout 120 --memory-size 512 \
        --environment "Variables={TABLE_NAME=$TABLA,BUCKET_NAME=$BUCKET,MODEL_ID=$MODELO}" \
        >/dev/null 2>&1; then
      echo "   funcion creada"; break
    fi
    echo "   esperando propagacion del rol IAM (intento $intento)..."
    espera 10
  done
  aws lambda wait function-active --function-name "$PROYECTO" --region "$REGION"
fi
rm -rf "$TMP"

# ------------------------------------------------- 5. rol para el scheduler
echo "-- [5/6] rol IAM del scheduler"
if ! aws iam get-role --role-name "$ROL_SCHEDULER" >/dev/null 2>&1; then
  aws iam create-role --role-name "$ROL_SCHEDULER" \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"scheduler.amazonaws.com"},"Action":"sts:AssumeRole"}]}' \
    >/dev/null
  echo "   rol creado"
else
  echo "   ya existia"
fi
aws iam put-role-policy --role-name "$ROL_SCHEDULER" --policy-name "invocar-postales" \
  --policy-document "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":\"lambda:InvokeFunction\",\"Resource\":\"arn:aws:lambda:${REGION}:${CUENTA}:function:${PROYECTO}\"}]}"

# ------------------------------------------------- 6. eventbridge scheduler
echo "-- [6/6] EventBridge Scheduler ($FRECUENCIA)"
COMUN=(--name "$SCHEDULE" --region "$REGION"
  --schedule-expression "$FRECUENCIA"
  --schedule-expression-timezone "America/Guayaquil"
  --flexible-time-window '{"Mode":"OFF"}'
  --description "Despierta al agente Postales del Ecuador"
  --target "{\"Arn\":\"arn:aws:lambda:${REGION}:${CUENTA}:function:${PROYECTO}\",\"RoleArn\":\"arn:aws:iam::${CUENTA}:role/${ROL_SCHEDULER}\",\"Input\":\"{\\\"origen\\\":\\\"scheduler\\\"}\"}")

if aws scheduler get-schedule --name "$SCHEDULE" --region "$REGION" >/dev/null 2>&1; then
  aws scheduler update-schedule "${COMUN[@]}" >/dev/null
  echo "   schedule actualizado"
else
  for intento in 1 2 3 4 5; do
    if aws scheduler create-schedule "${COMUN[@]}" >/dev/null 2>&1; then
      echo "   schedule creado"; break
    fi
    echo "   esperando propagacion del rol del scheduler (intento $intento)..."
    espera 10
  done
fi

WEB="http://${BUCKET}.s3-website-${REGION}.amazonaws.com"
echo "WEB=$WEB" >> "$ENV_FILE"
echo
echo "=============================================================="
echo " DESPLIEGUE COMPLETO"
echo " Web publica : $WEB"
echo " Lambda      : $PROYECTO"
echo " Tabla       : $TABLA"
echo " Schedule    : $SCHEDULE ($FRECUENCIA)"
echo "=============================================================="
