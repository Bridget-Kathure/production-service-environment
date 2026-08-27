# Reliability Target

## Critical User Journey
User accesses the application via ALB → Service A → Service B → Service C → returns response.

## SLIs
| SLI | Definition | Measurement |
|-----|------------|-------------|
| **Availability** | % of successful HTTP requests (status 2xx) | ALB `RequestCount` / `HTTPCode_Target_2XX_Count` |
| **Latency** | p95 response time (ms) | ALB `TargetResponseTime` p95 |
| **Correctness** | % of requests returning expected JSON structure | Custom metric from application logs |

## SLOs
| SLI | SLO | Window |
|-----|-----|--------|
| Availability | ≥ 99.9% | 30 days |
| Latency | p95 < 500ms | 30 days |
| Correctness | ≥ 99.5% | 30 days |

## Error Budget
- Availability error budget: 0.1% (≈ 43 minutes per month)
- Latency error budget: p95 exceeding 500ms for ≤ 0.5% of requests

## Engineering Behaviour
| Budget State | Action |
|--------------|--------|
| **Healthy** (> 50% remaining) | Continue normal development; monitor trends |
| **Consuming quickly** (20–50% remaining) | Prioritize reliability work; pause non-critical features |
| **Exhausted** (< 20% remaining) | Stop all feature work; focus on remediation; rollback risky changes |
