#!/usr/bin/env bash
# Capa 1 - la memoria del agente y el archivo publico.
# No se ejecuta suelto: lo carga deploy.sh con source.

almacenamiento::desplegar() {
  paso "[1/3] Almacenamiento"

  # ---- la tabla: la memoria ----
  if existe aws dynamodb describe-table --table-name "$TABLA" --region "$REGION"; then
    salta "tabla $TABLA ya existe"
  else
    aws dynamodb create-table --table-name "$TABLA" --region "$REGION" \
      --attribute-definitions AttributeName=id,AttributeType=S \
      --key-schema AttributeName=id,KeyType=HASH \
      --billing-mode PAY_PER_REQUEST \
      --tags "${ETIQUETAS_LISTA[@]}" >/dev/null
    aws dynamodb wait table-exists --table-name "$TABLA" --region "$REGION"
    ok "tabla $TABLA creada"
  fi

  # recuperacion puntual: si alguien borra la memoria, se puede volver atras
  if [[ "$(aws dynamodb describe-continuous-backups --table-name "$TABLA" --region "$REGION" \
       --query 'ContinuousBackupsDescription.PointInTimeRecoveryDescription.PointInTimeRecoveryStatus' \
       --output text 2>/dev/null)" == "ENABLED" ]]; then
    salta "point-in-time recovery ya activo"
  else
    aws dynamodb update-continuous-backups --table-name "$TABLA" --region "$REGION" \
      --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true >/dev/null
    ok "point-in-time recovery activado"
  fi

  # ---- el bucket: el archivo publico ----
  if existe aws s3api head-bucket --bucket "$BUCKET"; then
    salta "bucket $BUCKET ya existe"
  else
    aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" >/dev/null
    ok "bucket $BUCKET creado"
  fi

  # estas cuatro se aplican siempre: son idempotentes y baratas
  # S3 pide las etiquetas en JSON completo, no en la forma abreviada
  aws s3api put-bucket-tagging --bucket "$BUCKET" \
    --tagging "{\"TagSet\": $ETIQUETAS_JSON}" >/dev/null

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
  ok "bucket configurado como sitio publico"
}

almacenamiento::destruir() {
  paso "[3/3] Almacenamiento"
  if existe aws s3api head-bucket --bucket "$BUCKET"; then
    aws s3 rm "s3://$BUCKET" --recursive >/dev/null 2>&1 || true
    aws s3api delete-bucket --bucket "$BUCKET" --region "$REGION" && ok "bucket $BUCKET borrado"
  else
    salta "bucket ya no existe"
  fi
  if existe aws dynamodb describe-table --table-name "$TABLA" --region "$REGION"; then
    aws dynamodb delete-table --table-name "$TABLA" --region "$REGION" >/dev/null
    aws dynamodb wait table-not-exists --table-name "$TABLA" --region "$REGION"
    ok "tabla $TABLA borrada"
  else
    salta "tabla ya no existe"
  fi
}
