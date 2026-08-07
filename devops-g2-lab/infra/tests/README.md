# Architecture tests

Native `terraform test` files, run against a mocked AWS provider
(`mock_provider "aws" {}`) — no AWS credentials or account required.

## Run locally

```bash
cd devops-g2-lab/infra
terraform init
terraform test
```

## What's covered

- **ecs_service.tftest.hcl** — image tag validation (rejects `latest`
  and non-SHA values), service_name/owner validation, no public IP,
  ECS Exec enabled, ECR repository is IMMUTABLE.
- **alb.tftest.hcl** — rejects a single-AZ subnet list, target group
  type is `ip`, ALB is internet-facing on port 80.

## In CI

These run automatically on every PR touching `devops-g2-lab/infra/**`
via `.github/workflows/terraform-ci.yml`.
