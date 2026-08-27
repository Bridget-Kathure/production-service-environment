# Runbook: Service A Unhealthy

## Trigger
- CloudWatch Alarm `devops-g2-high-5xx-rate` fires
- OR manual detection: users report errors / ALB returns 5xx

## Verify Impact
1. Check ALB metrics: `aws cloudwatch get-metric-statistics ...`
2. Check ECS service status: `aws ecs describe-services --cluster devops-g2-cluster-iac --services devops-g2-service-a`
3. Check task logs: `aws logs get-log-events --log-group-name /ecs/devops-g2-service-a ...`

## Diagnose
- Is the task running? (`lastStatus == "RUNNING"`)
- Is the health check passing? (target group health status)
- Are there recent deployment events? (`events` in service description)
- Check container logs for errors (e.g., `Connection refused` to Service B)

## Mitigate
- If bad deployment: rollback to previous task definition
  ```bash
  aws ecs update-service --cluster devops-g2-cluster-iac --service devops-g2-service-a --task-definition devops-g2-service-a:1 --force-new-deployment
If resource exhaustion: increase CPU/memory or scale out
aws ecs update-service --cluster devops-g2-cluster-iac --service devops-g2-service-a --desired-count 3
If downstream failure: check Service B/C status and restart if needed

Recover
Wait for new tasks to become healthy (lastStatus == "RUNNING")

Confirm ALB target group health: aws elbv2 describe-target-health --target-group-arn <arn>

Validate
curl http://<alb-dns> – should return valid JSON

Check CloudWatch alarms – should be in OK state

Escalate
If issue persists > 15 minutes, escalate to platform team

If data loss or security issue, escalate immediately
