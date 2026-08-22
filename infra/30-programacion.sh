#!/usr/bin/env bash
# Capa 3 - el reloj que despierta al agente.

programacion::desplegar() {
  paso "[3/3] Programacion"

  if existe aws iam get-role --role-name "$ROL_SCHEDULER"; then
    salta "rol $ROL_SCHEDULER ya existe"
  else
    aws iam create-role --role-name "$ROL_SCHEDULER" \
      --assume-role-policy-document "$(cat <<JSON
{"Version":"2012-10-17","Statement":[{"Effect":"Allow",
 "Principal":{"Service":"scheduler.amazonaws.com"},"Action":"sts:AssumeRole",
 "Condition":{"StringEquals":{"aws:SourceAccount":"${CUENTA}"}}}]}
JSON
)" >/dev/null
    ok "rol $ROL_SCHEDULER creado"
  fi

  aws iam put-role-policy --role-name "$ROL_SCHEDULER" --policy-name invocar-postales \
    --policy-document "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":\"lambda:InvokeFunction\",\"Resource\":\"${ARN_FUNCION}\"}]}"

  local comun=(--name "$SCHEDULE" --region "$REGION"
    --schedule-expression "$FRECUENCIA"
    --schedule-expression-timezone "$ZONA_HORARIA"
    --flexible-time-window '{"Mode":"OFF"}'
    --description "Despierta al agente Postales del Ecuador."
    --target "{\"Arn\":\"${ARN_FUNCION}\",\"RoleArn\":\"arn:aws:iam::${CUENTA}:role/${ROL_SCHEDULER}\",\"Input\":\"{\\\"origen\\\":\\\"scheduler\\\"}\"}")

  if existe aws scheduler get-schedule --name "$SCHEDULE" --region "$REGION"; then
    aws scheduler update-schedule "${comun[@]}" >/dev/null
    ok "schedule actualizado: $FRECUENCIA"
  else
    reintentar 5 10 aws scheduler create-schedule "${comun[@]}" \
      && ok "schedule creado: $FRECUENCIA" \
      || { malo "no se pudo crear el schedule"; return 1; }
  fi
}

programacion::destruir() {
  paso "[1/3] Programacion"
  if existe aws scheduler get-schedule --name "$SCHEDULE" --region "$REGION"; then
    aws scheduler delete-schedule --name "$SCHEDULE" --region "$REGION" && ok "schedule borrado"
  else
    salta "schedule ya no existe"
  fi
  if existe aws iam get-role --role-name "$ROL_SCHEDULER"; then
    for P in $(aws iam list-role-policies --role-name "$ROL_SCHEDULER" --query 'PolicyNames[]' --output text); do
      aws iam delete-role-policy --role-name "$ROL_SCHEDULER" --policy-name "$P"
    done
    aws iam delete-role --role-name "$ROL_SCHEDULER" && ok "rol $ROL_SCHEDULER borrado"
  else
    salta "rol ya no existe"
  fi
}
