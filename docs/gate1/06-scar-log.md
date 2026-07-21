# Scar Log — Group 2

## Scar: ECS Exec TargetNotConnectedException

- **Symptom**: `aws ecs execute-command` failed with `TargetNotConnectedException`
- **First hypothesis**: Session Manager plugin not installed locally
- **Evidence**: Installing the plugin changed the error from "plugin not found" to `TargetNotConnected` — proved the plugin wasn't the only issue
- **Actual cause**: Task role (`devops-g2-ecs-task-role`) had no SSM messaging permissions
- **Repair**: Added inline policy granting `ssmmessages:CreateControlChannel`, `CreateDataChannel`, `OpenControlChannel`, `OpenDataChannel` to the task role; forced a new deployment so running tasks picked up the updated permissions
- **Prevention**: Bake the SSM messaging policy into the task role from the start, before first deployment, for every service (B and C will need this too)
