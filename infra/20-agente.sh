#!/usr/bin/env bash
# Capa 2 - el cerebro: rol, logs, funcion y la alarma que avisa si se rompe.

agente::_politica() {
  cat <<JSON
{"Version":"2012-10-17","Statement":[
 {"Effect":"Allow","Action":"bedrock:InvokeModel","Resource":"${ARN_MODELO}"},
 {"Effect":"Allow",
  "Action":["dynamodb:PutItem","dynamodb:GetItem","dynamodb:Query","dynamodb:Scan"],
  "Resource":"${ARN_TABLA}"},
 {"Effect":"Allow","Action":"s3:PutObject","Resource":"arn:aws:s3:::${BUCKET}/*"}
]}
JSON
}

agente::desplegar() {
  paso "[2/3] Agente"

  # ---- rol de ejecucion ----
  if existe aws iam get-role --role-name "$ROL_LAMBDA"; then
    salta "rol $ROL_LAMBDA ya existe"
  else
    aws iam create-role --role-name "$ROL_LAMBDA" \
      --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' \
      --tags "${ETIQUETAS_LISTA[@]}" >/dev/null
    ok "rol $ROL_LAMBDA creado"
  fi

  # permisos acotados al modelo, la tabla y el bucket concretos - nunca "*"
  aws iam put-role-policy --role-name "$ROL_LAMBDA" \
    --policy-name postales-permisos --policy-document "$(agente::_politica)"
  for P in AWSLambdaBasicExecutionRole AWSXRayDaemonWriteAccess; do
    aws iam attach-role-policy --role-name "$ROL_LAMBDA" \
      --policy-arn "arn:aws:iam::aws:policy/service-role/$P" 2>/dev/null || true
  done
  ok "permisos aplicados"

  # ---- log group con retencion ----
  # Si lo crea la Lambda sola, los logs se guardan para siempre y se pagan
  # para siempre. Creandolo aqui podemos fijarle caducidad.
  if existe aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP" \
       --region "$REGION" --query 'logGroups[0].logGroupName' --output text; then
    if [[ "$(aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP" --region "$REGION" \
          --query 'logGroups[0].logGroupName' --output text)" == "$LOG_GROUP" ]]; then
      salta "log group ya existe"
    else
      aws logs create-log-group --log-group-name "$LOG_GROUP" --region "$REGION" \
        --tags "$ETIQUETAS_MAPA" && ok "log group creado"
    fi
  fi
  aws logs put-retention-policy --log-group-name "$LOG_GROUP" \
    --retention-in-days "$RETENCION_LOGS" --region "$REGION"
  ok "retencion de logs: $RETENCION_LOGS dias"

  # ---- la funcion ----
  local tmp; tmp="$(mktemp -d)"
  cp "$RAIZ/src/handler.py" "$RAIZ/src/lugares.py" "$tmp/"
  (cd "$tmp" && zip -q funcion.zip handler.py lugares.py)

  if existe aws lambda get-function --function-name "$FUNCION" --region "$REGION"; then
    aws lambda update-function-code --function-name "$FUNCION" --region "$REGION" \
      --zip-file "fileb://$tmp/funcion.zip" >/dev/null
    aws lambda wait function-updated --function-name "$FUNCION" --region "$REGION"
    aws lambda update-function-configuration --function-name "$FUNCION" --region "$REGION" \
      --timeout "$TIMEOUT" --memory-size "$MEMORIA" \
      --tracing-config Mode=Active \
      --environment "Variables={TABLE_NAME=$TABLA,BUCKET_NAME=$BUCKET,MODEL_ID=$MODELO}" >/dev/null
    aws lambda wait function-updated --function-name "$FUNCION" --region "$REGION"
    ok "codigo actualizado"
  else
    # el rol recien creado tarda unos segundos en propagar
    reintentar 6 10 aws lambda create-function --function-name "$FUNCION" --region "$REGION" \
      --runtime "$RUNTIME" --handler handler.lambda_handler \
      --architectures "$ARQUITECTURA" \
      --role "arn:aws:iam::${CUENTA}:role/${ROL_LAMBDA}" \
      --zip-file "fileb://$tmp/funcion.zip" \
      --timeout "$TIMEOUT" --memory-size "$MEMORIA" \
      --tracing-config Mode=Active \
      --tags "$ETIQUETAS_MAPA" \
      --environment "Variables={TABLE_NAME=$TABLA,BUCKET_NAME=$BUCKET,MODEL_ID=$MODELO}" \
      || { malo "no se pudo crear la funcion"; rm -rf "$tmp"; return 1; }
    aws lambda wait function-active --function-name "$FUNCION" --region "$REGION"
    ok "funcion $FUNCION creada ($ARQUITECTURA, X-Ray activo)"
  fi
  rm -rf "$tmp"

  # ---- avisar si se rompe ----
  aws sns create-topic --name "$TEMA_ALERTAS" --region "$REGION" \
    --tags "${ETIQUETAS_LISTA[@]}" >/dev/null
  aws cloudwatch put-metric-alarm --region "$REGION" \
    --alarm-name "$ALARMA" \
    --alarm-description "El agente fallo al escribir. Nadie mira los logs a las seis de la manana." \
    --namespace AWS/Lambda --metric-name Errors \
    --dimensions "Name=FunctionName,Value=${FUNCION}" \
    --statistic Sum --period 3600 --evaluation-periods 1 \
    --threshold 1 --comparison-operator GreaterThanOrEqualToThreshold \
    --treat-missing-data notBreaching \
    --alarm-actions "$ARN_TEMA" \
    --tags "${ETIQUETAS_LISTA[@]}"
  ok "alarma de fallos conectada a SNS"
}

agente::destruir() {
  paso "[2/3] Agente"
  existe aws cloudwatch describe-alarms --alarm-names "$ALARMA" --region "$REGION" \
    && aws cloudwatch delete-alarms --alarm-names "$ALARMA" --region "$REGION" && ok "alarma borrada"
  aws sns delete-topic --topic-arn "$ARN_TEMA" --region "$REGION" 2>/dev/null && ok "tema SNS borrado" || salta "tema SNS ya no existe"
  if existe aws lambda get-function --function-name "$FUNCION" --region "$REGION"; then
    aws lambda delete-function --function-name "$FUNCION" --region "$REGION" && ok "funcion borrada"
  else
    salta "funcion ya no existe"
  fi
  aws logs delete-log-group --log-group-name "$LOG_GROUP" --region "$REGION" 2>/dev/null \
    && ok "log group borrado" || salta "log group ya no existe"
  # un rol no se puede borrar mientras tenga politicas colgando
  if existe aws iam get-role --role-name "$ROL_LAMBDA"; then
    for P in $(aws iam list-role-policies --role-name "$ROL_LAMBDA" --query 'PolicyNames[]' --output text); do
      aws iam delete-role-policy --role-name "$ROL_LAMBDA" --policy-name "$P"
    done
    for A in $(aws iam list-attached-role-policies --role-name "$ROL_LAMBDA" --query 'AttachedPolicies[].PolicyArn' --output text); do
      aws iam detach-role-policy --role-name "$ROL_LAMBDA" --policy-arn "$A"
    done
    aws iam delete-role --role-name "$ROL_LAMBDA" && ok "rol $ROL_LAMBDA borrado"
  else
    salta "rol ya no existe"
  fi
}
