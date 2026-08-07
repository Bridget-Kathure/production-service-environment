# 10. Five architecture decision cards — Group 2

Each card: risk reduced · trade-off · Well-Architected pillar · evidence.

## Card 1 — Two Availability Zones

1. **Risk reduced:** Single-AZ outage taking down the ALB, all Service A tasks, or the NAT path.
2. **Trade-off:** Doubled subnet/NAT infrastructure (~$90/month vs ~$45/month for one NAT); more Terraform resources to manage.
3. **Pillar:** Reliability.
4. **Evidence:** ALB spans two public subnets/AZs (`us-east-2a`, `us-east-2b`); Service A tasks placed across two AZs (desired count 2); two NAT Gateways, one per AZ.

## Card 2 — Private Fargate tasks

1. **Risk reduced:** Accidental Internet reachability of app ports 3000/3002/3003; forces all ingress through the ALB.
2. **Trade-off:** Needs NAT Gateways for egress (cost + a dependency that must stay healthy); image pulls and log writes fail if NAT/routes break.
3. **Pillar:** Security.
4. **Evidence:** `assign_public_ip = false` hardcoded in the `ecs-service` module (not a variable, so not configurable to `true`); enforced further by an explicit `postcondition` on the `aws_ecs_service` resource; Internet→ALB allowed, Internet→tasks denied by the security-group design; private route table shows `0.0.0.0/0 → nat-...`.

## Card 3 — Security-group references instead of IP allowlists

1. **Risk reduced:** Brittle task-IP allowlists that break the moment a task is replaced; wide-open `0.0.0.0/0` on application ports.
2. **Trade-off:** Security groups become coupled through Terraform outputs/inputs across modules; harder to "just open a port" for a quick debug session.
3. **Pillar:** Security.
4. **Evidence:** All inter-service rules use `source_security_group_id`, never `cidr_blocks`, on application ports; A→B and B→C allowed, A→C and Internet→tasks denied, enforced by a `check "traffic_contract"` block that fails the plan if any of these rules go missing or point at the wrong source.

## Card 4 — Immutable image SHA

1. **Risk reduced:** Mystery deploys, floating `latest` retags, no way to know which Git commit is actually running.
2. **Trade-off:** Every release needs an explicit build/push + IaC variable update; can't "just re-tag latest" to deploy.
3. **Pillar:** Operational Excellence.
4. **Evidence:** `image_tag` variable validation rejects `"latest"` outright; the deployed task definition and the app's own `/health` response both show the real Git SHA once a release lands through IaC.

## Card 5 — Remote, versioned and locked state

1. **Risk reduced:** Local state divergence between the two engineers, lost state, concurrent applies silently overwriting each other's changes.
2. **Trade-off:** A separate bootstrap stack must exist and stay protected before any workload work can begin; adds setup overhead up front.
3. **Pillar:** Operational Excellence / Reliability.
4. **Evidence:** S3 backend with versioning, SSE-KMS encryption and public access fully blocked; DynamoDB-backed locking on every apply; a real gap was found and fixed where the workload stack had no backend configuration committed at all (see `08-state-backend.md`) — the kind of failure this design is meant to catch.
