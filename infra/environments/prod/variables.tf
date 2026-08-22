variable "region" {
  description = "Region de AWS donde vive el agente."
  type        = string
  default     = "us-east-1"
}

variable "proyecto" {
  description = "Nombre del proyecto. Prefija los recursos."
  type        = string
  default     = "postales-del-ecuador"
}

variable "nombre_bucket" {
  description = "Nombre del bucket que sirve la web. Es global en todo AWS."
  type        = string
}

variable "modelo_bedrock" {
  description = "Modelo de Amazon Bedrock que escribe las postales."
  type        = string
  default     = "amazon.nova-pro-v1:0"
}

variable "frecuencia" {
  description = "Cada cuanto despierta el agente."
  type        = string
  default     = "cron(0 6 * * ? *)"
}

variable "zona_horaria" {
  description = "Zona en la que se interpreta la frecuencia."
  type        = string
  default     = "America/Guayaquil"
}

variable "retencion_logs" {
  description = "Dias que se conservan los logs del agente."
  type        = number
  default     = 30
}
