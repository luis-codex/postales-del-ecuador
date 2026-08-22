variable "nombre" {
  description = "Nombre de la funcion y prefijo de sus recursos."
  type        = string
}

variable "ruta_src" {
  description = "Directorio con el codigo Python del agente."
  type        = string
}

variable "tabla_nombre" {
  description = "Tabla de memoria que lee y escribe el agente."
  type        = string
}

variable "tabla_arn" {
  description = "ARN de esa tabla, para acotar los permisos."
  type        = string
}

variable "bucket_id" {
  description = "Bucket donde el agente publica el archivo."
  type        = string
}

variable "bucket_arn" {
  description = "ARN de ese bucket, para acotar los permisos."
  type        = string
}

variable "modelo_bedrock" {
  description = "Modelo de Amazon Bedrock que escribe las postales."
  type        = string
}

variable "region" {
  description = "Region, necesaria para construir el ARN del modelo."
  type        = string
}

variable "retencion_logs" {
  description = "Dias que se conservan los logs del agente."
  type        = number

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 180, 365], var.retencion_logs)
    error_message = "CloudWatch solo admite ciertos valores de retencion."
  }
}

variable "memoria_mb" {
  description = "Memoria de la Lambda."
  type        = number
  default     = 512
}

variable "timeout_s" {
  description = "Tiempo maximo de una ejecucion del agente."
  type        = number
  default     = 120
}

variable "ruta_zip" {
  description = "Donde se deja el zip que se sube a Lambda."
  type        = string
}
