locals {
  name_prefix = "devops-${var.group_number}"
}

# ── ECS Cluster ──────────────────────────────────────────────
resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster-iac"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name  = "${local.name_prefix}-cluster-iac"
    Owner = var.owner
  }
}

# ── Service Connect Namespace ────────────────────────────────
resource "aws_service_discovery_private_dns_namespace" "main" {
  name        = "group2.internal"
  description = "Service Connect namespace for group 2"
  vpc         = var.vpc_id

  tags = {
    Name  = "group2.internal"
    Owner = var.owner
  }
}

# ── CloudWatch Log Group for ECS ─────────────────────────────
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${local.name_prefix}"
  retention_in_days = 7

  tags = {
    Name  = "/ecs/${local.name_prefix}"
    Owner = var.owner
  }
}

# ── ECS Task Execution Role ──────────────────────────────────
resource "aws_iam_role" "ecs_execution" {
  name = "${local.name_prefix}-ecs-execution-role-iac"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name  = "${local.name_prefix}-ecs-execution-role-iac"
    Owner = var.owner
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution_managed" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Additional policy for ECR pull and CloudWatch
resource "aws_iam_role_policy" "ecs_execution_extra" {
  name = "${local.name_prefix}-ecs-execution-extra"
  role = aws_iam_role.ecs_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# ── ECS Task Role (skeleton) ─────────────────────────────────
resource "aws_iam_role" "ecs_task" {
  name = "${local.name_prefix}-ecs-task-role-iac"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name  = "${local.name_prefix}-ecs-task-role-iac"
    Owner = var.owner
  }
}

# Required for `aws ecs execute-command` (ECS Exec) to work against tasks
# using this role. Without this, exec sessions fail even when
# enable_execute_command = true is set on the service.
resource "aws_iam_role_policy" "ecs_task_exec" {
  name = "${local.name_prefix}-ecs-task-exec"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssmmessages:CreateControlChannel",
          "ssmmessages:CreateDataChannel",
          "ssmmessages:OpenControlChannel",
          "ssmmessages:OpenDataChannel"
        ]
        Resource = "*"
      }
    ]
  })
}
