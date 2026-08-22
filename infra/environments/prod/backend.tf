# State remoto en S3, con bloqueo nativo (use_lockfile).
#
# La configuracion va aparte, en backend.hcl, porque el nombre del bucket lleva
# el ID de la cuenta y eso no tiene por que estar en el repositorio:
#
#   terraform init -backend-config=backend.hcl
#
# Copia backend.hcl.ejemplo y rellenalo. El bucket lo crea infra/bootstrap.

terraform {
  backend "s3" {}
}
