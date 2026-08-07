terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }

  backend "s3" {
    bucket         = "devops-g2-tfstate-827478161993"
    key            = "lab/workload.tfstate"
    region         = "us-east-2"
    encrypt        = true
    kms_key_id     = "arn:aws:kms:us-east-2:827478161993:alias/devops-g2-tfstate-key"
    dynamodb_table = "devops-g2-tfstate-lock"
  }
}

provider "aws" {
  region = "us-east-2"

  # Applies to every resource created through this provider, including
  # child modules (none of which declare their own provider block).
  # Resource-level `tags = { ... }` blocks still set Name/Owner per
  # resource; explicit tags win over default_tags on key collisions.
  default_tags {
    tags = {
      Project     = "devops-g2"
      Group       = "g2"
      Environment = "lab"
    }
  }
}
