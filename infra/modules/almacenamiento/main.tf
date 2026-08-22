# La memoria del agente y el archivo publico.

resource "aws_dynamodb_table" "historial" {
  name         = var.nombre_tabla
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  # Si alguien vacia la memoria por error, se puede volver a cualquier
  # momento de los ultimos 35 dias.
  point_in_time_recovery {
    enabled = true
  }
}

resource "aws_s3_bucket" "sitio" {
  bucket = var.nombre_bucket
}

resource "aws_s3_bucket_ownership_controls" "sitio" {
  bucket = aws_s3_bucket.sitio.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

# La galeria tiene que ser publica, asi que se desactivan los bloqueos.
# Es deliberado y es el unico bucket del proyecto que lo hace.
resource "aws_s3_bucket_public_access_block" "sitio" {
  bucket                  = aws_s3_bucket.sitio.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

data "aws_iam_policy_document" "sitio_publico" {
  statement {
    sid       = "LecturaPublica"
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.sitio.arn}/*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }
  }
}

resource "aws_s3_bucket_policy" "sitio" {
  bucket = aws_s3_bucket.sitio.id
  policy = data.aws_iam_policy_document.sitio_publico.json

  # La politica publica se rechaza si el bloqueo sigue puesto.
  depends_on = [aws_s3_bucket_public_access_block.sitio]
}

resource "aws_s3_bucket_website_configuration" "sitio" {
  bucket = aws_s3_bucket.sitio.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

# La web tambien es infraestructura: si cambia el HTML, terraform lo detecta.
resource "aws_s3_object" "web" {
  bucket        = aws_s3_bucket.sitio.id
  key           = "index.html"
  source        = var.ruta_web
  etag          = filemd5(var.ruta_web)
  content_type  = "text/html; charset=utf-8"
  cache_control = "no-cache, max-age=0"
}
