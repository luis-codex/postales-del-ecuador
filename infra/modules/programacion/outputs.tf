output "nombre_schedule" {
  description = "Nombre de la programacion creada."
  value       = aws_scheduler_schedule.despertador.name
}
