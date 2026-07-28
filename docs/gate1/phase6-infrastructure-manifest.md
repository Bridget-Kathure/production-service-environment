# Phase 6.2 — Infrastructure Manifest (Service B / C + shared pipeline infra)

| Resource | Owner | Important settings | Depends on | Future IaC change |
|---|---|---|---|---|
| ECR repo — devops-g2-service-b | Pearl | Immutable tags | — | Terraform `aws_ecr_repository` |
| ECR repo — devops-g2-service-c | Pearl | Immutable tags | — | Terraform `aws_ecr_repository` |
| Task definition — devops-g2-service-b | Pearl | rev 7, Fargate, 256/512, named port `service-b`:3002, curl-based health check | Shared execution/task roles, ECR image | Terraform `aws_ecs_task_definition` |
| Task definition — devops-g2-service-c | Pearl | rev 7, Fargate, 256/512, named port `service-c`:3003, curl-based health check | Shared execution/task roles, ECR image | Terraform `aws_ecs_task_definition` |
| Security group — devops-g2-service-b-sg (`sg-06f7c2e3d2f6d6fe1`) | Pearl | Inbound: Service A's SG only, port 3002 | Service A's SG | Terraform `aws_security_group` |
| Security group — devops-g2-service-c-sg (`sg-03015100432db898f`) | Pearl | Inbound: Service B's SG only, port 3003 | Service B's SG | Terraform `aws_security_group` |
| ECS service — service-b | Pearl | Desired count 1, Service Connect alias `service-b`, no ALB registration | Cluster, task def, SG, Service Connect namespace | Autoscaling |
| ECS service — service-c | Pearl | Desired count 1, Service Connect alias `service-c`, no ALB registration | Cluster, task def, SG, Service Connect namespace | Autoscaling |
| CloudWatch log groups — /ecs/devops-g2-service-b, -c | Pearl | Manually pre-created (execution role lacks `logs:CreateLogGroup`) | — | Terraform `aws_cloudwatch_log_group` |
| CodeBuild — devops-g2-service-b-build, -c-build | Pearl | Privileged mode on, buildspec per service, LINUX_CONTAINER standard:7.0 | devops-g2-codebuild-role, ECR repos | Terraform `aws_codebuild_project` |
| CodePipeline — devops-g2-service-b-pipeline, -c-pipeline | Pearl | Source→Build→Deploy, `DetectChanges: true`, triggers via CodeConnections webhook | devops-g2-codepipeline-role, CodeBuild projects, S3 artifact bucket, CodeConnections | Terraform `aws_codepipeline` |
| IAM role — devops-g2-codebuild-role | Pearl | ECR push, logs, CodeConnections use, scoped to B/C repos | — | Terraform `aws_iam_role` |
| IAM role — devops-g2-codepipeline-role | Pearl | ECS deploy actions, CodeBuild invoke, S3 artifact access, `iam:PassRole` scoped to exec/task roles only | — | Terraform `aws_iam_role` |
| IAM role — devops-g2-eventbridge-pipeline-trigger-role | Pearl | `codepipeline:StartPipelineExecution`, unused now | — | Delete — superseded by `DetectChanges` |
| S3 — devops-g2-pipeline-artifacts | Pearl | Public access blocked, versioning off | CodePipeline artifact store | Terraform `aws_s3_bucket` |
| EventBridge rule — devops-g2-main-push-trigger | Pearl | Enabled, unused | — | Delete — debugging leftover, real trigger path is CodePipeline-managed |

## Shared platform dependencies (owned by Patricia, referenced here for context)

| Resource | Depends on |
|---|---|
| ECS cluster — devops-g2-cluster | VPC/subnets |
| Service Connect namespace — group2.internal | ECS cluster |
| Shared execution role — devops-g2-ecs-execution-role | Used by every task definition (A, B, C) |
| Shared task role — devops-g2-ecs-task-role | Used by every task definition (A, B, C); carries the SSM messaging inline policy for ECS Exec |
| CodeConnections — devops-g2-github | GitHub App installation, scoped to `production-service-environment` |

## Future production considerations (not built in this lab)

Custom VPC, private subnets, NAT Gateway/VPC endpoints, HTTPS + ACM, WAF, Secrets Manager, autoscaling for B/C, full Terraform coverage of everything above, separate accounts per environment.
