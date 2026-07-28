# Phase 6.1 — Cost Sweep (Service B / C + shared pipeline infra)

Pulled directly from AWS via `describe`/`list` calls, us-east-2, 2026-07-25.

## Resources owned by Pearl (Service B + C)

| Resource | Bills while idle? | Current state | Cleanup required? |
|---|---|---|---|
| Fargate task — service-b | Yes (vCPU/memory while running) | 1 task, 0.25 vCPU / 512 MB | Yes |
| Fargate task — service-c | Yes (vCPU/memory while running) | 1 task, 0.25 vCPU / 512 MB | Yes |
| Security group — devops-g2-service-b-sg (`sg-06f7c2e3d2f6d6fe1`) | No | — | Yes |
| Security group — devops-g2-service-c-sg (`sg-03015100432db898f`) | No | — | Yes |
| ECR repo — devops-g2-service-b | Storage only | 7 images, ~530 MB total | As instructed |
| ECR repo — devops-g2-service-c | Storage only | 7 images, ~530 MB total | As instructed |
| CloudWatch log group — /ecs/devops-g2-service-b | Ingestion + storage | ~4.1 MB stored | As instructed |
| CloudWatch log group — /ecs/devops-g2-service-c | Ingestion + storage | ~4.1 MB stored | As instructed |
| CodeBuild — devops-g2-service-b-build | Per-build only, no idle cost | — | No persistent compute |
| CodeBuild — devops-g2-service-c-build | Per-build only, no idle cost | — | No persistent compute |
| CodePipeline — devops-g2-service-b-pipeline | Small per-pipeline monthly charge | — | Yes |
| CodePipeline — devops-g2-service-c-pipeline | Small per-pipeline monthly charge | — | Yes |
| S3 — devops-g2-pipeline-artifacts | Storage (small) | 18 objects, ~7.9 MB | Yes |
| IAM roles (codebuild, codepipeline, eventbridge-trigger) | No direct cost | 3 roles | Yes |
| EventBridge rule — devops-g2-main-push-trigger | No direct cost | Enabled, currently redundant (superseded by CodePipeline's own `DetectChanges`/webhook integration) | Yes — safe to remove now, was a debugging artifact from before the real fix was found |

## Most expensive forgotten-resource risk

**The two Fargate tasks (B + C) and, group-wide, the Application Load Balancer** (Patricia's resource, not itemized here) are the ones that keep costing money purely by existing, regardless of traffic. Everything else in this table is either free at rest or bills only for the tiny amount of storage/build-minutes actually used. If this environment is left running unattended, the ALB (hourly charge) is the single biggest line item across the whole group's setup — worth flagging to Patricia too, since it's her resource.

## Note on the EventBridge rule

`devops-g2-main-push-trigger` (and its `devops-g2-eventbridge-pipeline-trigger-role`) were built while diagnosing the auto-trigger issue, before discovering the real cause (GitHub App repo scope) and the real fix (`DetectChanges: true` on the Source action, which CodePipeline manages internally). This rule never actually fired and isn't part of the real trigering path — it's safe to delete as leftover debugging infrastructure, not production wiring.
