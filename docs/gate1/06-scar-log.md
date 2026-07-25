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

## Scar: Service C's /greet-c callback to Service A fails by design (not a bug)

- **Symptom**: /greet-service-b → /greet → /greet-c full trace succeeds (200/200/200) with matching trace_id across all three services, but service-c logs a callback_failed error trying to reach service-a:3001/greeting-rcvd
- **First hypothesis**: Service Connect DNS misconfiguration, same pattern as the earlier Service A registration gap
- **Evidence**: read the actual code — service-c's greet_c() intentionally fires a background callback to service-a's /greeting-rcvd, with full OTel trace context propagation. This is deliberate application-level design, not a leftover bug
- **Actual cause**: no security-group rule permits service-c to reach service-a (port 3001) — correctly so, since our Gate 1 traffic contract explicitly denies any C-to-A path (and A-to-C)
- **Decision**: left as-is. Adding a C-to-A security-group rule would violate our documented, Gate-1-approved traffic contract. The callback failure is an accepted limitation of a demo endpoint not required by this assignment's traffic contract
- **Prevention**: if this callback pattern is ever required by a future assignment phase, it needs an explicit Gate-reviewed traffic-contract update first, not a silent SG change

## Phase 4: Kill-a-task drill results

- **Setup**: continuous curl loop (1 req/sec) against ALB /health, desiredCount=2 for Service A
- **Action**: stopped one Service A task manually (task 42c7469a...) via aws ecs stop-task
- **Observed**: zero failed requests (all status=200); two latency spikes — 0.96s and 0.82s during draining, one 5.56s spike likely from a request landing on the task mid-shutdown; recovered to baseline (~0.45-0.5s) within seconds, well before the replacement task finished
- **ECS timeline**: deregistered from target group (20:28:58.600) -> began draining connections (20:28:58.606) -> new task started (20:28:59.510) -> new task registered healthy in target group (20:29:46.750) = ~48s total recovery window
- **Why ECS replaced the task**: desiredCount=2 is continuously reconciled against actual running count; ECS scheduled a replacement the moment the stopped task was detected
- **Why the ALB avoided serving an unhealthy target**: target deregistration + connection draining removed the dying task from rotation immediately, routing all new requests to the surviving healthy target
- **Service Connect impact**: none required — services are addressed by name (service-a in group2.internal), not by IP, so the replacement task registered automatically under the same identity
- **What changes at desiredCount=1**: with only one task, there would be zero healthy targets during the ~48s replacement window, producing real failed requests (502/504) instead of latency wobble — this is exactly why Service A specifically runs desiredCount=2

## Sabotage round: Service C nonexistent image tag (diagnosed by Patricia)

- **Symptom**: service-c stuck at running=1, desired=1, pending=1 indefinitely
- **First hypothesis**: task placement or capacity issue
- **Evidence**: describe-services events showed repeated CannotPullContainerError referencing image tag 9f8e7d6c; diffed task-definition revision 2 vs 3 and found the image tag was the only change (43fe4bc -> 9f8e7d6c)
- **Actual cause**: Pearl's sabotage round injection — task definition revision 3 pointed at a nonexistent ECR image tag
- **Repair**: rolled service-c back to task-definition revision 2 (known-good image 43fe4bc) via update-service + force-new-deployment; confirmed via service events that new task started and sabotaged task was stopped
- **Prevention**: this is exactly why image tags should always be verified against `aws ecr describe-images` before registering a new task-definition revision

## Scar: CodeBuild access denied to CodeConnections despite correct IAM policy

- **Symptom**: CodeBuild failed immediately at DOWNLOAD_SOURCE with "Access denied to connection ...", despite the CodeBuild role having codeconnections:GetConnection and codeconnections:UseConnection explicitly granted
- **First hypothesis**: missing resource-based policy on the CodeConnections connection itself
- **Evidence**: `aws codeconnections help` showed no get-resource-policy/put-resource-policy commands exist at all for this service — ruling out a resource-policy-based fix
- **Actual cause**: CodeBuild's underlying integration still checks the legacy `codestar-connections` IAM namespace (the service was renamed to CodeConnections, but permission checks for some actions haven't fully migrated) — the codeconnections:* actions alone were insufficient
- **Repair**: added the equivalent codestar-connections:GetConnection, codestar-connections:UseConnection, codestar-connections:GetConnectionToken actions to the CodeBuild role's policy, alongside the codeconnections:* ones
- **Prevention**: when granting CodeBuild/CodePipeline access to a CodeConnections connection, include both codeconnections:* and codestar-connections:* actions on the role — this will apply to Pearl's Service B/C CodeBuild roles too

## Scar: CodePipeline V2 Git triggers not firing automatically on merge (shared issue with Pearl)

- **Symptom**: merges to main never automatically started a pipeline execution on either Service A (Patricia) or Service B (Pearl) pipelines. Every execution in history was triggerType StartPipelineExecution (manual) or CreatePipeline (initial), never an automatic push-based trigger
- **First hypothesis**: missing trigger configuration on the pipeline
- **Evidence**: confirmed via `get-pipeline` that a correctly-formed `triggers` block (CodeStarSourceConnection provider, gitConfiguration watching pushes to main) was present and persisted on Service A's pipeline. Also tried changing executionMode from SUPERSEDED to QUEUED (per AWS docs suggesting QUEUED is required for reliable trigger-based execution) -- still no automatic trigger fired after two separate real merges (PR #20, PR #21)
- **Cross-check**: independently verified the same failure on Pearl's Service B pipeline (her branch pearl/verify-detectchanges-fix shows she attempted the same fix independently) -- ruling out an individual configuration mistake
- **Actual cause**: unresolved -- likely an account-level or environment-level limitation on this lab account's CodeConnections-to-CodePipeline event delivery, not a mistake in either team member's pipeline JSON
- **Workaround in use**: manual `aws codepipeline start-pipeline-execution` after each merge, until/unless the trigger issue is resolved
- **Prevention/next step**: flagged to instructor as a potential platform-level constraint; both team members have independently confirmed correct trigger configuration per AWS documentation

## Resolution: CodePipeline auto-trigger root cause found

- **Root cause identified**: the AWS Connector for GitHub app (installed under Bridget's GitHub account) was scoped to "Only select repositories" -> Bridget-Kathure/Final-Stand-Admin-Dashboard, an unrelated repo. It was never granted access to production-service-environment, so GitHub never sent push-event notifications to AWS for this repo -- despite the CodeConnections connection itself showing "Available" and working fine for manual/Source-stage pulls
- **How found**: checked github.com/{repo}/settings/webhooks (empty -- expected for App-based integrations, not the actual gap) then github.com/settings/installations (account-level view) -> found AWS Connector for GitHub installed but scoped to the wrong repository entirely
- **Fix**: added production-service-environment to the app's repository access list via Configure -> Select repositories -> Save
- **Verified**: next merge to main produced a new pipeline execution with triggerType "WebhookV2" (vs previous manual "StartPipelineExecution"), confirming genuine automatic hands-off deployment
- **Prevention**: when setting up CodeConnections/GitHub App integration, explicitly verify the GitHub App's repository access includes the target repo at github.com/settings/installations -- the AWS-side connection can show "Available" and work for manual actions even when the underlying GitHub App has never been granted access to send push events for that specific repo
