output "bucket_id" {
  description = "Nombre del bucket que sirve la web."
  value       = aws_s3_bucket.sitio.id
}

output "bucket_arn" {
  description = "ARN del bucket, para acotar los permisos de escritura."
  value       = aws_s3_bucket.sitio.arn
}

output "tabla_nombre" {
  description = "Nombre de la tabla de memoria."
  value       = aws_dynamodb_table.historial.name
}

output "tabla_arn" {
  description = "ARN de la tabla, para acotar los permisos del agente."
  value       = aws_dynamodb_table.historial.arn
}

output "web_publica" {
  description = "URL de la galeria publica."
  value       = "http://${aws_s3_bucket_website_configuration.sitio.website_endpoint}"
}
