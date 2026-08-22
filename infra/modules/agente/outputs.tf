output "arn" {
  description = "ARN de la funcion, para que el scheduler la invoque."
  value       = aws_lambda_function.agente.arn
}

output "nombre" {
  description = "Nombre de la funcion."
  value       = aws_lambda_function.agente.function_name
}

output "tema_alertas" {
  description = "Tema SNS donde avisa si el agente falla."
  value       = aws_sns_topic.alertas.arn
}

output "log_group" {
  description = "Donde mirar la evidencia de que el agente corre solo."
  value       = aws_cloudwatch_log_group.agente.name
}
