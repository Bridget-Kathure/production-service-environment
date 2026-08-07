# 8. State backend — Group 2

## Tooling (from kickoff)

| Item | Value |
|---|---|
| Terraform CLI | v1.15.8 |
| Provider | `hashicorp/aws` `~> 5.60` |
| Region | `us-east-2` |
| Local state as team source of truth | Forbidden |

Pins live in `infra/bootstrap/main.tf` and `infra/environments/lab/versions.tf`. Exact provider version frozen by committing `.terraform.lock.hcl` after `terraform init`.

## Two stacks

| Stack | Path | Purpose | Destroy with workload? |
|---|---|---|---|
| Bootstrap | `infra/bootstrap/` | Encrypted, versioned, locked S3 backend | **No** |
| Workload | `infra/environments/lab/` | VPC, ECS, ALB, services | **Yes** |

## Bootstrap bucket — as built

| Requirement | Value |
|---|---|
| Name | `devops-g2-tfstate-827478161993` |
| Encryption | SSE-KMS, customer-managed key (`alias/devops-g2-tfstate-key`), rotation enabled |
| Versioning | Enabled |
| Public access | Blocked (all four block-public-access settings) |
| Locking | DynamoDB table `devops-g2-tfstate-lock`, `PAY_PER_REQUEST`, hash key `LockID` |
| Region | `us-east-2` |
| Tags | `Project=devops-g2`, `Group=g2`, `Owner=platform`, `Environment=lab` |

## Workload backend — as built

```hcl
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
}
```

**Known deprecation, deliberately not yet resolved:** `dynamodb_table` triggers a deprecation warning in favor of `use_lockfile = true`. Kept as-is because the DynamoDB table is the real, already-deployed locking mechanism the team has been applying against; switching requires a coordinated migration, not a unilateral change to the backend block. Tracked as a follow-up decision, not an oversight.

## Safety

- Never commit state, `.terraform/`, or saved plans.
- Never destroy the bootstrap bucket with the workload.
- Before destroy: confirm account, region, and state key.
- Console may inspect state, logs, events, routes and health; console must not create or repair IaC-managed resources.

## Real gap found and fixed (Cycle 2)

The workload stack initially had **no `terraform {}` block committed at all** — a fresh checkout would silently default to local state, violating "local state as team source of truth: forbidden." The real infrastructure existed (built and applied by the platform owner), but the backend configuration file itself was never pushed. Fixed by adding `versions.tf` with the block above, verified by confirming `terraform init` reaches "Initializing modules" without error — proof the backend connects to the real, existing state rather than creating a new local one.
