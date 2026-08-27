# Failure Map

## User Journey Path
Internet → ALB → Service A → Service B → Service C → Response

## Failure Modes
| Component | What Can Fail | Detection | Tolerance / Mitigation | User Experience |
|-----------|---------------|-----------|------------------------|-----------------|
| **ALB** | DNS resolution failure | CloudWatch `DNSUnavailable` | Multi-AZ; Route53 health checks | 503 Service Unavailable |
| **ALB** | Listener/port misconfiguration | ALB `HTTPCode_ELB_5XX_Count` | Infrastructure as Code (Terraform) | 502/503 errors |
| **Service A** | Container crash | ECS task failure; CloudWatch logs | ECS auto-restart; deployment circuit breaker | 503 from ALB |
| **Service A** | CPU/memory exhaustion | CloudWatch `CPUUtilization` > 90% | Horizontal scaling; increased resource limits | Increased latency or 5xx |
| **Service B** | Unreachable (Service Connect failure) | `UPSTREAM_SERVICE` timeout | Retries; circuit breaker | Partial response or 5xx |
| **Service C** | Unreachable | Same as above | Same as above | Partial response or 5xx |
| **Networking** | Subnet/NAT failure | VPC Flow Logs; CloudWatch | Multi-AZ deployment | Service unreachable |
| **Deployment** | Bad image version | ECS task fails health checks | Rollback via Terraform/CodePipeline | Brief downtime during rollback |
