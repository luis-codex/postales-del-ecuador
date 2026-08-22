# El cerebro: rol, logs, funcion y la alarma que avisa si se rompe.

data "aws_iam_policy_document" "confianza" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "permisos" {
  # Acotado al modelo concreto, nunca a "*".
  statement {
    sid       = "InvocarElModelo"
    effect    = "Allow"
    actions   = ["bedrock:InvokeModel"]
    resources = ["arn:aws:bedrock:${var.region}::foundation-model/${var.modelo_bedrock}"]
  }

  statement {
    sid    = "LeerYEscribirLaMemoria"
    effect = "Allow"
    actions = [
      "dynamodb:PutItem",
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:Scan",
    ]
    resources = [var.tabla_arn]
  }

  statement {
    sid       = "PublicarElArchivo"
    effect    = "Allow"
    actions   = ["s3:PutObject"]
    resources = ["${var.bucket_arn}/*"]
  }
}

resource "aws_iam_role" "agente" {
  name               = "${var.nombre}-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.confianza.json
}

resource "aws_iam_role_policy" "agente" {
  name   = "postales-permisos"
  role   = aws_iam_role.agente.id
  policy = data.aws_iam_policy_document.permisos.json
}

# Ojo con los ARN: AWSLambdaBasicExecutionRole vive bajo service-role/ y
# AWSXRayDaemonWriteAccess no. Se escriben completos para no adivinar.
resource "aws_iam_role_policy_attachment" "gestionadas" {
  for_each = toset([
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess",
  ])

  role       = aws_iam_role.agente.name
  policy_arn = each.value
}

# Declarado a proposito: si lo crea la Lambda sola, los logs se guardan para
# siempre y se pagan para siempre.
resource "aws_cloudwatch_log_group" "agente" {
  name              = "/aws/lambda/${var.nombre}"
  retention_in_days = var.retencion_logs
}

# El zip lo hace Terraform: nada de scripts externos.
data "archive_file" "agente" {
  type        = "zip"
  source_dir  = var.ruta_src
  output_path = var.ruta_zip
  excludes    = ["__pycache__", "*.pyc"]
}

resource "aws_lambda_function" "agente" {
  function_name = var.nombre
  description   = "Escribe una postal desde un lugar del Ecuador segun su clima real."

  role             = aws_iam_role.agente.arn
  runtime          = "python3.12"
  handler          = "handler.lambda_handler"
  architectures    = ["arm64"] # Graviton: ~20% mas barato
  memory_size      = var.memoria_mb
  timeout          = var.timeout_s
  filename         = data.archive_file.agente.output_path
  source_code_hash = data.archive_file.agente.output_base64sha256

  tracing_config {
    mode = "Active"
  }

  environment {
    variables = {
      TABLE_NAME  = var.tabla_nombre
      BUCKET_NAME = var.bucket_id
      MODEL_ID    = var.modelo_bedrock
    }
  }

  # Sin esto, la Lambda crea el log group ella misma sin retencion.
  depends_on = [aws_cloudwatch_log_group.agente]
}

resource "aws_sns_topic" "alertas" {
  name         = "${var.nombre}-alertas"
  display_name = "Postales del Ecuador - alertas"
}

resource "aws_cloudwatch_metric_alarm" "falla" {
  alarm_name        = "${var.nombre}-fallos"
  alarm_description = "El agente fallo al escribir. Nadie mira los logs a las seis de la manana."

  namespace   = "AWS/Lambda"
  metric_name = "Errors"
  dimensions  = { FunctionName = aws_lambda_function.agente.function_name }

  statistic           = "Sum"
  period              = 3600
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alertas.arn]
}
