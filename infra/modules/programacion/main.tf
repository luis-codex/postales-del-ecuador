# El reloj que despierta al agente.

data "aws_iam_policy_document" "confianza" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }

    # Evita el problema del "confused deputy": solo esta cuenta.
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [var.cuenta_id]
    }
  }
}

data "aws_iam_policy_document" "permisos" {
  statement {
    effect    = "Allow"
    actions   = ["lambda:InvokeFunction"]
    resources = [var.arn_funcion]
  }
}

resource "aws_iam_role" "despertador" {
  name               = "${var.nombre}-scheduler-role"
  assume_role_policy = data.aws_iam_policy_document.confianza.json
}

resource "aws_iam_role_policy" "despertador" {
  name   = "invocar-postales"
  role   = aws_iam_role.despertador.id
  policy = data.aws_iam_policy_document.permisos.json
}

resource "aws_scheduler_schedule" "despertador" {
  name        = "${var.nombre}-despertador"
  description = "Despierta al agente Postales del Ecuador."
  state       = "ENABLED"

  schedule_expression          = var.frecuencia
  schedule_expression_timezone = var.zona_horaria

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = var.arn_funcion
    role_arn = aws_iam_role.despertador.arn
    input    = jsonencode({ origen = "scheduler" })
  }
}
