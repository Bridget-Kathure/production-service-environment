# Scar Log — Group 2

## Scar: ECS Exec TargetNotConnectedException

- **Symptom**: `aws ecs execute-command` failed with `TargetNotConnectedException`
- **First hypothesis**: Session Manager plugin not installed locally
- **Evidence**: Installing the plugin changed the error from "plugin not found" to `TargetNotConnected` — proved the plugin wasn't the only issue
- **Actual cause**: Task role (`devops-g2-ecs-task-role`) had no SSM messaging permissions
- **Repair**: Added inline policy granting `ssmmessages:CreateControlChannel`, `CreateDataChannel`, `OpenControlChannel`, `OpenDataChannel` to the task role; forced a new deployment so running tasks picked up the updated permissions
- **Prevention**: Bake the SSM messaging policy into the task role from the start, before first deployment, for every service (B and C will need this too)

## Scar: Service A missing from Service Connect

- **Symptom**: A→B request couldn't resolve `service-b`; Pearl's diagnostics showed her side (B→C) worked, isolating the problem to Service A's side
- **First hypothesis**: security group misconfiguration on A→B rule
- **Evidence**: Pearl confirmed the A→B security group rule was correct; found via `describe-services` that Service A's `serviceConnectConfiguration` was null — it had never been registered into `group2.internal` at all, no proxy sidecar attached
- **Actual cause**: original `create-service` command for Service A predated Service Connect wiring and was never updated with a `--service-connect-configuration` block
- **Repair**: ran `update-service` with an explicit Service Connect config (named port, explicit `dnsName` alias matching Pearl's own fix for B→C) and `--force-new-deployment`; confirmed via `describe-tasks` that the `ecs-service-connect` proxy container was now present, then verified A→B with a live `curl`-equivalent from inside the task via ECS Exec
- **Prevention**: Service Connect configuration must be part of every service's *initial* `create-service` call, not bolted on afterward — will apply this to any future services from the start
