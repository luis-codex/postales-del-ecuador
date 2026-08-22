#!/usr/bin/env bash
# Desmonta todo, en orden inverso al despliegue.
#
# Este archivo es el precio de hacer la infraestructura con scripts: una
# herramienta declarativa sabe sola que creo y en que orden deshacerlo. Aqui
# el orden lo mantenemos a mano, y hay que actualizarlo cada vez que se
# anade un recurso.
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$RAIZ/infra/config.sh"
source "$RAIZ/infra/lib.sh"
source "$RAIZ/infra/10-almacenamiento.sh"
source "$RAIZ/infra/20-agente.sh"
source "$RAIZ/infra/30-programacion.sh"

if [[ "${1:-}" != "--si" ]]; then
  cat <<AVISO
Esto borra la infraestructura completa de $PROYECTO en la cuenta $CUENTA:

  · schedule $SCHEDULE y su rol
  · funcion $FUNCION, su rol, su log group, su alarma y su tema SNS
  · bucket $BUCKET CON TODAS LAS POSTALES PUBLICADAS
  · tabla $TABLA CON LA MEMORIA DEL AGENTE

Respalda antes:  aws dynamodb scan --table-name $TABLA > respaldo.json

Si estas seguro:  bash infra/destroy.sh --si
AVISO
  exit 1
fi

# inverso al despliegue: primero lo que depende, al final lo que guarda datos
programacion::destruir
agente::destruir
almacenamiento::destruir

paso "Desmontado"
