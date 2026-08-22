variable "nombre" {
  description = "Prefijo de los recursos del scheduler."
  type        = string
}

variable "arn_funcion" {
  description = "Funcion que despierta el scheduler."
  type        = string
}

variable "cuenta_id" {
  description = "ID de la cuenta, para la condicion anti confused-deputy."
  type        = string
}

variable "frecuencia" {
  description = "Cada cuanto despierta el agente. Expresion cron() o rate()."
  type        = string

  validation {
    condition     = can(regex("^(cron|rate)\\(", var.frecuencia))
    error_message = "Debe ser una expresion cron(...) o rate(...)."
  }
}

variable "zona_horaria" {
  description = "Zona en la que se interpreta la frecuencia."
  type        = string
}
