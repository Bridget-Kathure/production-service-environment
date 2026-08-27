# Actionable Alerts

## 1. High Error Rate (Availability)
- **Signal**: ALB `HTTPCode_Target_5XX_Count` > 5% of requests over 5 minutes
- **Why it matters**: Users are experiencing failures
- **Investigate first**: Check Service A logs; verify downstream services are healthy
- **Alert**: CloudWatch Alarm `devops-g2-high-5xx-rate`

## 2. High Latency
- **Signal**: ALB `TargetResponseTime` p95 > 500ms over 5 minutes
- **Why it matters**: Users experience slow responses
- **Investigate first**: Check CPU/memory of Service A; check database/network latency
- **Alert**: CloudWatch Alarm `devops-g2-high-latency`

## 3. Resource Pressure (Saturation)
- **Signal**: ECS `CPUUtilization` > 85% or `MemoryUtilization` > 85% for any service
- **Why it matters**: Performance degradation or impending crashes
- **Investigate first**: Check if tasks need more resources; consider scaling up
- **Alert**: CloudWatch Alarm `devops-g2-cpu-pressure`
