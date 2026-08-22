variable "nombre_bucket" {
  description = "Nombre del bucket que sirve la web. Es global en todo AWS."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.nombre_bucket))
    error_message = "Nombre de bucket invalido: minusculas, numeros, puntos y guiones."
  }
}

variable "nombre_tabla" {
  description = "Nombre de la tabla que guarda la memoria del agente."
  type        = string
}

variable "ruta_web" {
  description = "Ruta al index.html que se publica en el bucket."
  type        = string
}
