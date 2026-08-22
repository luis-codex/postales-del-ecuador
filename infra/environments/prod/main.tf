# Entorno de produccion. Une los tres modulos conectando sus salidas.
#
# Las rutas al codigo y a la web se calculan aqui, desde path.root, para que
# los modulos no tengan que saber donde estan colocados en el repositorio.

locals {
  raiz = "${path.root}/../../.."
}

module "almacenamiento" {
  source = "../../modules/almacenamiento"

  nombre_bucket = var.nombre_bucket
  nombre_tabla  = "${var.proyecto}-historial"
  ruta_web      = "${local.raiz}/web/index.html"
}

module "agente" {
  source = "../../modules/agente"

  nombre   = var.proyecto
  ruta_src = "${local.raiz}/src"
  ruta_zip = "${path.root}/.terraform/agente.zip"

  tabla_nombre = module.almacenamiento.tabla_nombre
  tabla_arn    = module.almacenamiento.tabla_arn
  bucket_id    = module.almacenamiento.bucket_id
  bucket_arn   = module.almacenamiento.bucket_arn

  modelo_bedrock = var.modelo_bedrock
  region         = var.region
  retencion_logs = var.retencion_logs
}

module "programacion" {
  source = "../../modules/programacion"

  nombre       = var.proyecto
  arn_funcion  = module.agente.arn
  cuenta_id    = data.aws_caller_identity.actual.account_id
  frecuencia   = var.frecuencia
  zona_horaria = var.zona_horaria
}
