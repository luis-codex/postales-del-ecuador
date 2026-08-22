output "web_publica" {
  description = "La galeria publica de postales."
  value       = module.almacenamiento.web_publica
}

output "funcion" {
  description = "La Lambda que contiene al agente."
  value       = module.agente.nombre
}

output "tabla" {
  description = "La memoria del agente."
  value       = module.almacenamiento.tabla_nombre
}

output "tema_alertas" {
  description = "Suscribe tu correo aqui para enterarte si el agente falla."
  value       = module.agente.tema_alertas
}

output "log_group" {
  description = "Donde mirar la evidencia de que el agente corre solo."
  value       = module.agente.log_group
}
