terraform {
  required_version = ">= 1.15.8, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }

  backend "s3" {
    bucket       = "devops-g2-tfstate-827478161993"
    key          = "lab/workload.tfstate"
    region       = "us-east-2"
    encrypt      = true
    kms_key_id   = "arn:aws:kms:us-east-2:827478161993:alias/devops-g2-tfstate-key"
    use_lockfile = true
    # Migrated from dynamodb_table (deprecated) to native S3 locking.
    # NOT YET APPLIED: this only takes effect after `terraform init
    # -reconfigure` against the real backend, which needs AWS
    # credentials we don't currently have. Until that's run, the
    # actually-deployed backend is still using the DynamoDB table
    # (devops-g2-tfstate-lock, created in bootstrap/main.tf). That
    # table is left in place on purpose - safe to remove in a future
    # cost sweep once the reconfigure is confirmed working, not before.
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
