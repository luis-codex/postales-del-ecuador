terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.region

  # Etiqueta todos los recursos sin repetirlo en cada uno.
  default_tags {
    tags = {
      proyecto       = var.proyecto
      entorno        = "prod"
      gestionado-por = "terraform"
    }
  }
}

data "aws_caller_identity" "actual" {}
