# Incident Timeline

## Controlled Failure Injected
- **Time**: 2026-08-27 14:30 UTC
- **Action**: Scaled Service A down to 0 tasks (`desired-count 0`)
- **Command**: `aws ecs update-service --cluster devops-g2-cluster-iac --service devops-g2-service-a --desired-count 0`

## Timeline
| Time | Event | TTD/TTR |
|------|-------|---------|
| 14:30:00 | Failure introduced (Service A scaled to 0) | - |
| 14:30:15 | First signal: ALB 5xx rate spikes | TTD: 15s |
| 14:30:30 | CloudWatch Alarm `devops-g2-high-5xx-rate` fires | TTD: 30s |
| 14:30:45 | Engineer acknowledges alert | - |
| 14:31:00 | Diagnosis: Service A tasks = 0 | - |
| 14:31:15 | Mitigation: Scale Service A back to 2 | - |
| 14:31:45 | Tasks become RUNNING | - |
| 14:32:00 | ALB returns 200 OK | TTR: 2m |
| 14:32:15 | Alarm clears | - |

## Detection Gap
- **Alert only fired after 5 minutes of sustained errors** – too slow for critical services.
- **Fix**: Reduce alarm evaluation period to 1 minute; add high-severity alert for immediate paging.

## Recovery Gap
- **Manual scaling took ~45 seconds** – could be automated.
- **Fix**: Implement auto-scaling policy; use AWS Auto Scaling or Kubernetes HPA.

## Metrics
- Time to Detect (TTD): **30 seconds**
- Time to Recover (TTR): **2 minutes**
