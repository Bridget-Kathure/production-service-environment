# Platform Resources — Group 2

Reference for Pearl (Service B + C) — everything Patricia's platform build created. Use these exact IDs/ARNs when building your services so naming and networking stay consistent.

---

## Cluster

| Field | Value |
|---|---|
| Cluster name | `devops-g2-cluster` |
| Cluster ARN | `arn:aws:ecs:us-east-2:827478161993:cluster/devops-g2-cluster` |
| Region | us-east-2 |

## Service Connect namespace

| Field | Value |
|---|---|
| Namespace name | `group2.internal` |
| Namespace ID | `ns-n2h2kki3swg7oek4` |
| Type | HTTP |

Register your services as `service-b` and `service-c` in this namespace (matches what Service A already expects when it calls `http://service-b:3002/health`).

## Subnets (use these two, nowhere else)

| Subnet ID | AZ |
|---|---|
| `subnet-02db924128425a3f5` | us-east-2a |
| `subnet-0a728100c8a214340` | us-east-2b |

## IAM roles (shared — reuse these, don't create your own)

| Role | ARN |
|---|---|
| Execution role | `arn:aws:iam::827478161993:role/devops-g2-ecs-execution-role` |
| Task role | `arn:aws:iam::827478161993:role/devops-g2-ecs-task-role` |

**Important:** the task role already has the SSM messaging inline policy attached (`ecs-exec-ssm-messaging`) so ECS Exec works out of the box — see `06-scar-log.md` for why this was needed. You don't need to add it again; just reference the same role ARN in your task definitions.

## Service A reference (for your security-group rules later)

| Field | Value |
|---|---|
| Security group | `sg-088ce544a660d8348` (`devops-g2-service-a-sg`) |
| Port | 3001 |
| Service Connect name | `service-a` |

When we wire up traffic contracts (A→B, B→C), B's security group will need an inbound rule from `sg-088ce544a660d8348` on B's port, and C's security group will need one from B's SG on C's port — by SG reference, never by IP.

## CloudWatch log group naming convention

Pattern: `/ecs/devops-g2-service-<x>`
Service A's is `/ecs/devops-g2-service-a` — create matching ones for B and C.

## Target group name reserved (Platform will create this)

`devops-g2-tg` — registers Service A only, per the traffic contract. B and C are not registered to any target group.

---

*Last updated after Service A checkpoint verification (task RUNNING, HEALTHY, logs visible, SHA visible, ECS Exec working).*

## ALB (added post-wiring)

| Field | Value |
|---|---|
| ALB name | `devops-g2-alb` |
| ALB DNS | `devops-g2-alb-587868346.us-east-2.elb.amazonaws.com` |
| ALB security group | `sg-02f1f76b56f71897b` |
| Target group | `devops-g2-tg` (registers Service A only, port 3001) |
| Listener | HTTP :80 → forwards to `devops-g2-tg` |

Verified: `curl -i http://devops-g2-alb-587868346.us-east-2.elb.amazonaws.com/health` returns `200 OK` with Service A's health JSON.
