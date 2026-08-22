#!/usr/bin/env bash
# Variables del despliegue. Todo lo configurable vive aqui y en ningun otro sitio.
# Se carga con "source" desde los demas scripts.

REGION="${REGION:-us-east-1}"
PROYECTO="postales-del-ecuador"

# --- lo que el agente usa ---
BUCKET="${BUCKET:-postales-del-ecuador-ec}"          # nombre global, unico en todo AWS
TABLA="${TABLA:-postales-del-ecuador-historial}"
FUNCION="$PROYECTO"
LOG_GROUP="/aws/lambda/${FUNCION}"

# --- identidades ---
ROL_LAMBDA="postales-lambda-role"
ROL_SCHEDULER="postales-scheduler-role"

# --- cuando despierta ---
SCHEDULE="${SCHEDULE:-postales-del-ecuador-despertador}"
FRECUENCIA="${FRECUENCIA:-cron(0 6 * * ? *)}"
ZONA_HORARIA="${ZONA_HORARIA:-America/Guayaquil}"

# --- que modelo escribe ---
MODELO="${MODELO:-amazon.nova-pro-v1:0}"

# --- observabilidad ---
RETENCION_LOGS="${RETENCION_LOGS:-30}"               # dias
TEMA_ALERTAS="${PROYECTO}-alertas"
ALARMA="${PROYECTO}-fallos"

# --- runtime ---
RUNTIME="python3.12"
ARQUITECTURA="arm64"                                  # Graviton: ~20% mas barato
MEMORIA=512
TIMEOUT=120

# --- etiquetas ---
# El AWS CLI pide las etiquetas en tres formatos distintos segun el servicio.
# No hay forma de evitarlo, asi que se declaran los tres juntos para que se vea
# que son lo mismo:
#   mapa   -> lambda, logs
#   lista  -> iam, dynamodb, sns, cloudwatch  (argumentos separados, no una cadena)
#   json   -> s3
ETIQUETAS_MAPA="proyecto=${PROYECTO},entorno=prod,gestionado-por=bash"
ETIQUETAS_LISTA=(Key=proyecto,Value="${PROYECTO}" Key=entorno,Value=prod Key=gestionado-por,Value=bash)
ETIQUETAS_JSON='[{"Key":"proyecto","Value":"postales-del-ecuador"},{"Key":"entorno","Value":"prod"},{"Key":"gestionado-por","Value":"bash"}]'

CUENTA="$(aws sts get-caller-identity --query Account --output text)"
ARN_FUNCION="arn:aws:lambda:${REGION}:${CUENTA}:function:${FUNCION}"
ARN_TABLA="arn:aws:dynamodb:${REGION}:${CUENTA}:table/${TABLA}"
ARN_MODELO="arn:aws:bedrock:${REGION}::foundation-model/${MODELO}"
ARN_TEMA="arn:aws:sns:${REGION}:${CUENTA}:${TEMA_ALERTAS}"
