# Gate 0 / Kickoff decisions — Group 2

## Decision 1 — Tooling

| Item | Value |
|---|---|
| IaC tool | **Terraform** |
| Terraform CLI | **v1.15.8** installed by both engineers; code constraint `>= 1.9.0` |
| AWS provider source | `hashicorp/aws` |
| AWS provider version pin | `~> 5.60` |
| Lockfile | `.terraform.lock.hcl` committed after first `terraform init` |
| AWS Region | `us-east-2` only |

Live in code today — `infra/bootstrap/main.tf` and `infra/environments/lab/versions.tf`:

```hcl
terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }
}

provider "aws" {
  region = "us-east-2"
}
```

## Decision 2 — Network

| Item | Value |
|---|---|
| VPC CIDR | `10.2.0.0/16` |
| Public subnet AZ-1 (`us-east-2a`) | `10.2.0.0/20` |
| Public subnet AZ-2 (`us-east-2b`) | `10.2.16.0/20` |
| Private app subnet AZ-1 | `10.2.32.0/19` |
| Private app subnet AZ-2 | `10.2.64.0/19` |
| Egress for private Fargate | **NAT Gateway per AZ** (two NAT Gateways, one per public subnet) |
| Task public IPs | **false** (`assign_public_ip = false`, hardcoded in the `ecs-service` module, not a variable) |
| ALB | Internet-facing, spans both public subnets |

**Note on NAT choice:** two NAT Gateways (one per AZ) rather than a single shared one — a single-AZ NAT failure does not cut off outbound access for the whole environment. Documented cost trade-off: ~$90/month vs ~$45/month for a single NAT, accepted for the lab given the reliability goal (see Decision Card 1).
