# Bootstrap: crea el bucket donde vive el state del despliegue principal.
#
# Es el huevo y la gallina de cualquier IaC: Terraform necesita un sitio donde
# guardar su state, pero ese sitio hay que crearlo con algo. Este modulo usa
# state LOCAL a proposito, se ejecuta una sola vez, y despues no se toca.
#
#   cd infra/bootstrap && terraform init && terraform apply

terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      proyecto       = "postales-del-ecuador"
      gestionado-por = "terraform"
      componente     = "bootstrap"
    }
  }
}

variable "region" {
  description = "Region de AWS."
  type        = string
  default     = "us-east-1"
}

data "aws_caller_identity" "actual" {}

resource "aws_s3_bucket" "state" {
  bucket = "postales-tfstate-${data.aws_caller_identity.actual.account_id}"
}

# Con versionado, un apply que corrompa el state se puede revertir.
resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# El state guarda en claro cosas que no deberian ser publicas.
resource "aws_s3_bucket_public_access_block" "state" {
  bucket                  = aws_s3_bucket.state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "bucket_state" {
  description = "Bucket del state. Va en backend.tf del despliegue principal."
  value       = aws_s3_bucket.state.id
}
