#!/usr/bin/env bash
# Despliega Postales del Ecuador. Idempotente: se puede repetir sin miedo.
#
#   bash infra/deploy.sh
#   FRECUENCIA="rate(5 minutes)" bash infra/deploy.sh
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$RAIZ/infra/config.sh"
source "$RAIZ/infra/lib.sh"
source "$RAIZ/infra/10-almacenamiento.sh"
source "$RAIZ/infra/20-agente.sh"
source "$RAIZ/infra/30-programacion.sh"

printf '\033[1mPostales del Ecuador\033[0m — cuenta %s · region %s\n' "$CUENTA" "$REGION"

almacenamiento::desplegar
agente::desplegar
programacion::desplegar

paso "Publicando la web"
aws s3 cp "$RAIZ/web/index.html" "s3://${BUCKET}/index.html" \
  --content-type "text/html; charset=utf-8" --cache-control "no-cache, max-age=0" >/dev/null
ok "index.html subido"

WEB="http://${BUCKET}.s3-website-${REGION}.amazonaws.com"
paso "Listo"
info "web       $WEB"
info "funcion   $FUNCION"
info "tabla     $TABLA"
info "schedule  $SCHEDULE — $FRECUENCIA"
info "alertas   $ARN_TEMA"
